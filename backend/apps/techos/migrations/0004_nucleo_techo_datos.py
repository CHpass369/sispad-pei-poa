"""
Data-migration 0004 del núcleo de techos (slice S2, design §5).

Ejecuta, dentro de transaction.atomic y en modo fail-loud:

1. **Pre-check 1:1 techo↔gestión (C2)**: COUNT(TechoPresupuestario)
   agrupado por gestion; si alguna gestión tiene más de un techo, aborta
   con RuntimeError + reporte ANTES del AlterField a no-null + unique.
2. **Backfill gestion_fiscal**: get(anio=gestion) o crear con estado
   'preparacion'; luego el AlterField final a OneToOneField no-null
   (unique) como operación separada de esta migración.
3. **monto_total = SUM(RecursoTecho.monto)** (Q1/DD6).
4. **Grupos**: TechoRecursoGrupo por (fuente, organismo) + un
   TechoRecursoDetalle por RecursoTecho; los RecursoTecho NO se borran
   (fuente legacy V1 read-only).
5. **Bolsas**: por (fuente, organismo); tipo_gasto = CORRIENTE (D10; la
   clasificación real llega por API en S4). monto_inicial = Σ del grupo
   (mapeo siempre 1:1: los recursos legacy no traen ObjetoGasto y el
   branch ambiguo era código muerto). En toda creación monto_vigente =
   monto_inicial + monto_ajustes (C8), nunca null ni 0 por omisión.
6. **Plano → jerárquico (DD4)**: categoría sintética 'MIGRACION LEGACY
   0004' (bolsa = única candidata si el techo tiene una sola bolsa, si no
   null) con monto = Σ legacy, marcador persistente en `concepto` (el
   identificador del árbol legacy vive en BD, sospechoso 4R), y una hoja
   por fila legacy (padre = categoría sintética).
7. **Validación post (fail-loud)**: Σ legacy pre == Σ hojas post;
   Σ recursos == Σ grupos; monto_total == total_recursos; Σ bolsas.vigente
   == Σ grupos. Cualquier diferencia → RuntimeError (nada se aplica
   parcialmente).

REVERSIBLE (K5 4R, opción "reverse real"): el forward toma una SNAPSHOT en
la tabla `techos_0004_backup` (monto_total original por techo + ids de las
filas legacy activas) ANTES de mutar cada techo. El reverse:
1. restaura monto_total original (Q1/DD6 se revierte);
2. borra las hojas sintéticas y la categoría sintética (marcador
   `concepto`);
3. reactiva EXACTAMENTE las filas legacy capturadas;
4. borra bolsas y grupos (los detalles van en cascada con el grupo); las
   GestionFiscal creadas por get_or_create se conservan (la reversión de
   0004_nucleo_techo revierte la columna; una gestión huérfana es un
   registro válido e inofensivo);
5. descarta la tabla de snapshot.
Así el estado 0003 queda exacto (sin datos 0004 residuales que lo
corrompan). Limitación documentada: si tras migrar se crearon
movimientos/ajustes (S3+) que referencien bolsas/distribuciones, el
reverse falla por FK PROTECT — el rollback debe hacerse ANTES de operar.
"""
from decimal import Decimal

import django.db.models.deletion
from django.db import migrations, models, transaction
from django.db.models import Count, Sum

NOMBRE_CATEGORIA_SINTETICA = 'MIGRACION LEGACY 0004'
TIPO_GASTO_LEGACY = 'CORRIENTE'  # D10: recursos legacy sin ObjetoGasto
TABLA_SNAPSHOT = 'techos_0004_backup'


def _resolver_constraints_diferidos():
    """Resuelve los eventos de triggers diferidos pendientes.

    Las FKs del proyecto son DEFERRABLE INITIALLY DEFERRED (PostgreSQL).
    Los INSERTs de la migración encolan eventos de RI que se mantienen
    pendientes hasta el commit; el AlterField a OneToOne no-null que
    cierra esta migración (misma transacción atómica) no puede correr
    con eventos pendientes ("cannot ALTER TABLE ... pending trigger
    events", PG15+). SET CONSTRAINTS ALL IMMEDIATE los dispara sin
    comprometer la transacción (se conserva el rollback total, §5).
    """
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute('SET CONSTRAINTS ALL IMMEDIATE')


def _suma(queryset, campo):
    """Suma Decimal segura (None → 0)."""
    total = queryset.aggregate(t=Sum(campo))['t']
    return total if total is not None else Decimal('0.00')


def migrar_nucleo_techo(apps, schema_editor):
    Techo = apps.get_model('techos', 'Techopresupuestario')
    Recurso = apps.get_model('techos', 'RecursoTecho')
    Grupo = apps.get_model('techos', 'TechoRecursoGrupo')
    Detalle = apps.get_model('techos', 'TechoRecursoDetalle')
    Bolsa = apps.get_model('techos', 'BolsaPresupuestaria')
    Distribucion = apps.get_model('techos', 'DistribucionTecho')
    Gestion = apps.get_model('gestion', 'GestionFiscal')

    reporte = []
    errores = []

    # Snapshot K5 4R: tabla que guarda el estado 0003 por techo
    # (monto_total original + ids legacy activos) para el reverse real.
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            f'CREATE TABLE IF NOT EXISTS {TABLA_SNAPSHOT} ('
            '  techo_id uuid PRIMARY KEY,'
            '  monto_total_legacy numeric(20,2) NOT NULL,'
            '  legacy_ids uuid[] NOT NULL'
            ')'
        )

    with transaction.atomic():
        # ------------------------------------------------------------------
        # 1) Pre-check 1:1 techo ↔ gestión (C2) — fail-loud con reporte
        # ------------------------------------------------------------------
        techos_por_gestion = (
            Techo.objects.values('gestion')
            .annotate(n=Count('id'))
            .filter(n__gt=1)
            .order_by('gestion')
        )
        if techos_por_gestion.exists():
            detalle = []
            for fila in techos_por_gestion:
                ids = list(
                    Techo.objects.filter(gestion=fila['gestion'])
                    .values_list('id', flat=True)
                )
                detalle.append(
                    f"gestion {fila['gestion']}: {fila['n']} techos ({ids})"
                )
            raise RuntimeError(
                'ABORTA migración 0004 (pre-check C2): la relación '
                'techo↔gestión debe ser 1:1 (V1 permitía varios techos por '
                'gestión). No se fusiona ni selecciona un techo '
                'silenciosamente. Reporte: ' + '; '.join(detalle)
            )

        # ------------------------------------------------------------------
        # 2) Backfill gestion_fiscal (get por anio o crear en preparacion)
        # ------------------------------------------------------------------
        for techo in Techo.objects.all().order_by('id'):
            gestion, _ = Gestion.objects.get_or_create(
                anio=techo.gestion,
                defaults={'estado': 'preparacion'},
            )
            if techo.gestion_fiscal_id != gestion.id:
                techo.gestion_fiscal = gestion
                techo.save(update_fields=['gestion_fiscal', 'updated_at'])

        # ------------------------------------------------------------------
        # 3)-5) monto_total, grupos+detalles y bolsas, por techo
        # ------------------------------------------------------------------
        totales_legacy_pre = {}   # techo_id -> Σ monto_asignado legacy activo

        for techo in Techo.objects.all().order_by('id'):
            tid = str(techo.id)

            # Estado 0003 ANTES de cualquier mutación de este techo: las
            # filas legacy activas y su Σ (para la validación post) y la
            # snapshot para el reverse (K5 4R).
            legacy = list(
                Distribucion.objects.filter(techo=techo, activo=True)
                .order_by('id')
            )
            totales_legacy_pre[tid] = _suma(
                Distribucion.objects.filter(techo=techo, activo=True),
                'monto_asignado',
            )
            with schema_editor.connection.cursor() as cursor:
                cursor.execute(
                    f'INSERT INTO {TABLA_SNAPSHOT} '
                    '(techo_id, monto_total_legacy, legacy_ids) '
                    'VALUES (%s, %s, %s::uuid[]) '
                    f'ON CONFLICT (techo_id) DO UPDATE SET '
                    'monto_total_legacy = EXCLUDED.monto_total_legacy, '
                    'legacy_ids = EXCLUDED.legacy_ids',
                    [techo.id, techo.monto_total, [str(f.id) for f in legacy]],
                )

            # 3) monto_total = SUM(RecursoTecho.monto) (Q1/DD6)
            total_recursos = _suma(Recurso.objects.filter(techo=techo), 'monto')
            if techo.monto_total != total_recursos:
                reporte.append(
                    f'techo {tid}: monto_total {techo.monto_total} normalizado '
                    f'→ {total_recursos} (= total_recursos, Q1/DD6)'
                )
                techo.monto_total = total_recursos
                techo.save(update_fields=['monto_total', 'updated_at'])

            # 4) Grupos por (fuente, organismo) + detalle por RecursoTecho
            recursos = list(
                Recurso.objects.filter(techo=techo).order_by('orden', 'id')
            )
            grupos = {}  # (fuente_id, organismo_id) -> grupo
            for recurso in recursos:
                clave = (str(recurso.fuente_id), str(recurso.organismo_id or ''))
                if clave not in grupos:
                    grupos[clave] = Grupo.objects.create(
                        techo=techo,
                        fuente_id=recurso.fuente_id,
                        organismo_id=recurso.organismo_id,
                        monto=Decimal('0.00'),
                    )
                grupos[clave].monto += recurso.monto
                Detalle.objects.create(
                    grupo=grupos[clave],
                    rubro=recurso.rubro,
                    concepto=recurso.concepto,
                    monto=recurso.monto,
                )
            for grupo in grupos.values():
                grupo.save(update_fields=['monto', 'updated_at'])

            # 5) Bolsas por (fuente, organismo) con C8; tipo de gasto
            # CORRIENTE (D10): los recursos legacy (0003) no traen
            # ObjetoGasto, el mapeo es SIEMPRE 1:1 y la clasificación real
            # llega por la API de clasificación (S4). El branch "ambiguo"
            # era código muerto (sospechoso 4R) y se eliminó.
            for clave, grupo in grupos.items():
                fuente_id, organismo_id = clave
                organismo_db = None if organismo_id == '' else organismo_id
                Bolsa.objects.create(
                    techo=techo,
                    fuente_id=fuente_id,
                    organismo_id=organismo_db,
                    tipo_gasto=TIPO_GASTO_LEGACY,
                    monto_inicial=grupo.monto,
                    monto_ajustes=Decimal('0.00'),
                    # C8: monto_vigente = monto_inicial + monto_ajustes
                    # SIEMPRE; nunca null ni 0 por omisión.
                    monto_vigente=grupo.monto + Decimal('0.00'),
                    monto_reservado=Decimal('0.00'),
                )

            # 6) Plano → jerárquico (DD4): categoría sintética + hojas
            if not legacy:
                continue
            bolsa_candidata = None
            bolsas_techo = Bolsa.objects.filter(techo=techo)
            if bolsas_techo.count() == 1:
                bolsa_candidata = bolsas_techo.first()
            categoria = Distribucion.objects.create(
                techo=techo,
                bolsa=bolsa_candidata,
                categoria_programatica=None,
                # Marcador persistente del árbol legacy (sospechoso 4R):
                # la identificación de la categoría sintética vive en BD,
                # no en un contrato implícito de la jerarquía.
                concepto=NOMBRE_CATEGORIA_SINTETICA,
                monto_asignado=_suma(
                    Distribucion.objects.filter(techo=techo, activo=True),
                    'monto_asignado',
                ),
                monto_reserva=_suma(
                    Distribucion.objects.filter(techo=techo, activo=True),
                    'monto_reserva',
                ),
                activo=True,
                version=1,
            )
            reporte.append(
                f'techo {tid}: categoría sintética "{NOMBRE_CATEGORIA_SINTETICA}" '
                f'Bs {categoria.monto_asignado} '
                f'({"bolsa " + str(bolsa_candidata.id) if bolsa_candidata else "sin bolsa"})'
            )
            for fila in legacy:
                Distribucion.objects.create(
                    techo=techo,
                    padre=categoria,
                    bolsa=bolsa_candidata,
                    da_id=fila.da_id,
                    ue_id=fila.ue_id,
                    unidad_id=fila.unidad_id,
                    programa_id=fila.programa_id,
                    monto_asignado=fila.monto_asignado,
                    monto_reserva=fila.monto_reserva,
                    activo=fila.activo,
                    version=fila.version,
                )
            # Las filas legacy planas pasan a inactivas: la jerarquía
            # sintética + hojas es la ÚNICA representación del saldo (DD4
            # "preserva saldos exactos"). Si quedaran activas, el guard C3
            # y los agregados del motor (Σ hojas activas) contarían el
            # mismo peso dos veces (una vía fila legacy y otra vía hoja).
            Distribucion.objects.filter(
                techo=techo, pk__in=[fila.pk for fila in legacy],
            ).update(activo=False)

        # ------------------------------------------------------------------
        # 7) Validación post (fail-loud)
        # ------------------------------------------------------------------
        for techo in Techo.objects.all().order_by('id'):
            tid = str(techo.id)

            recursos = _suma(Recurso.objects.filter(techo=techo), 'monto')
            grupos_total = _suma(Grupo.objects.filter(techo=techo), 'monto')
            if recursos != grupos_total:
                errores.append(
                    f'techo {tid}: Σ recursos {recursos} != Σ grupos '
                    f'{grupos_total}'
                )
            if techo.monto_total != recursos:
                errores.append(
                    f'techo {tid}: monto_total {techo.monto_total} != '
                    f'total_recursos {recursos}'
                )

            hojas = _suma(
                Distribucion.objects.filter(
                    techo=techo, activo=True, padre__isnull=False,
                ),
                'monto_asignado',
            )
            if hojas != totales_legacy_pre[tid]:
                errores.append(
                    f'techo {tid}: Σ hojas {hojas} != Σ legacy pre '
                    f'{totales_legacy_pre[tid]}'
                )

            bolsas = Bolsa.objects.filter(techo=techo)
            if bolsas.exists():
                suma_vigente = _suma(bolsas, 'monto_vigente')
                if suma_vigente != grupos_total:
                    errores.append(
                        f'techo {tid}: Σ bolsas.monto_vigente {suma_vigente} '
                        f'!= Σ grupos {grupos_total}'
                    )

        if errores:
            raise RuntimeError(
                'ABORTA validación post de la migración 0004: '
                + '; '.join(errores)
            )

        # Los INSERTs encolaron eventos de triggers diferidos (FKs
        # DEFERRABLE INITIALLY DEFERRED); el AlterField a OneToOne que
        # cierra la migración no puede correr con eventos pendientes.
        _resolver_constraints_diferidos()

        if reporte:
            print('[migración 0004 núcleo techo] reporte:')
            for linea in reporte:
                print(f'  - {linea}')


def _revertir_nucleo_techo(apps, schema_editor):
    """Reverse REAL de la data-migration 0004 (K5 4R).

    Restaura el estado 0003 exacto usando la snapshot `techos_0004_backup`
    tomada en el forward (por eso el reverse NUNCA deja S1 corrupto):
    1. monto_total original (Q1/DD6 se revierte).
    2. Se borran las hojas sintéticas y la categoría sintética (marcador
       persistente `concepto`, sospechoso 4R).
    3. Se reactivan EXACTAMENTE las filas legacy capturadas.
    4. Se borran bolsas y grupos (detalles en cascada con el grupo); las
       distribuciones que referenciaban bolsas ya no existen. Las
       GestionFiscal creadas por get_or_create se conservan (la reversión
       de 0004_nucleo_techo revierte la columna; una gestión huérfana es
       un registro válido e inofensivo).
    5. Se descarta la tabla de snapshot.
    """
    Techo = apps.get_model('techos', 'Techopresupuestario')
    Distribucion = apps.get_model('techos', 'DistribucionTecho')
    Bolsa = apps.get_model('techos', 'BolsaPresupuestaria')
    Grupo = apps.get_model('techos', 'TechoRecursoGrupo')

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(f"SELECT to_regclass('public.{TABLA_SNAPSHOT}')")
        if cursor.fetchone()[0] is None:
            # El forward nunca corrió en esta BD (o ya se revirtió).
            return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            f'SELECT techo_id, monto_total_legacy, legacy_ids '
            f'FROM {TABLA_SNAPSHOT}'
        )
        snapshots = cursor.fetchall()

    for techo_id, monto_legacy, legacy_ids in snapshots:
        Techo.objects.filter(pk=techo_id).update(monto_total=monto_legacy)
        # Hojas sintéticas (hijos de la categoría sintética) y la
        # categoría sintética misma (concepto = marcador 0004).
        Distribucion.objects.filter(
            techo_id=techo_id, padre__concepto=NOMBRE_CATEGORIA_SINTETICA,
        ).delete()
        Distribucion.objects.filter(
            techo_id=techo_id, concepto=NOMBRE_CATEGORIA_SINTETICA,
        ).delete()
        # Filas legacy originales: reactivar exactamente las capturadas.
        Distribucion.objects.filter(pk__in=legacy_ids).update(activo=True)
        # Bolsas y grupos (detalles en cascada con el grupo). Las
        # distribuciones que los referenciaban ya no existen.
        Bolsa.objects.filter(techo_id=techo_id).delete()
        Grupo.objects.filter(techo_id=techo_id).delete()

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(f'DROP TABLE IF EXISTS {TABLA_SNAPSHOT}')


class Migration(migrations.Migration):

    dependencies = [
        ('techos', '0004_nucleo_techo'),
    ]

    operations = [
        # Reverse REAL (K5 4R): restaura el estado 0003 desde la snapshot.
        migrations.RunPython(migrar_nucleo_techo, _revertir_nucleo_techo),
        # Estado final R2.1: FK → OneToOne no-null (unique). Solo se llega
        # aquí si el pre-check C2 (1:1) pasó y el backfill completó.
        migrations.AlterField(
            model_name='techopresupuestario',
            name='gestion_fiscal',
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='techo',
                to='gestion.gestionfiscal',
                verbose_name='Gestión fiscal',
            ),
        ),
    ]
