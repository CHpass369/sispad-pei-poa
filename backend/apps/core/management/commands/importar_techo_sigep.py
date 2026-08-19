"""
Management command para importar el techo presupuestario SIGEP 2027 del GAM
Sacaba como techo directivo de la gestión 2027.

Fuente: reporte oficial SIGEP `RFprTechoPresup` (entidad 1312, PRODUCCIÓN,
10/08/2026).

Carga:
    - Rubros de recurso oficiales usados por el reporte (19211 y 19212).
    - Los 5 recursos del techo (origen SIGEP) con los montos reales del
      reporte (total 245.290.497,00 Bs).
    - Los 3 gastos obligatorios (renta dignidad, fondo de fomento cívico
      patriótico y ayuda económica a personas con discapacidad) que se
      descuentan del techo bruto (total 6.464.396,00 Bs).

El techo queda en BORRADOR para revisión humana: NO fija la versión.

Idempotente: puede ejecutarse varias veces sin duplicar registros.

Uso:
    python manage.py importar_techo_sigep --gestion=2027
    python manage.py importar_techo_sigep --gestion=2027 --dry-run
"""
from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.budget.models import (
    RecursoTecho,
    TechoDirectivo,
    TechoVersion,
    EstadosTecho,
    GastoObligatorio,
    OrigenRecurso,
)
from apps.budget.services import (
    ESTADOS_NO_HABILITABLES,
    gestion_habilitada,
    habilitar_gestion,
    validar_gestion_para_techo,
)
from apps.catalogos.models import (
    FuenteFinanciamiento,
    OrganismoFinanciador,
    RubroRecurso,
)
from apps.gestion.models import GestionFiscal
from apps.gestion.services import crear_gestion
from apps.organizacion.models import DireccionAdministrativa

REPORTE_SIGEP = (
    'SIGEP - Reporte oficial RFprTechoPresup '
    '(entidad 1312, PRODUCCIÓN, 10/08/2026)'
)

# Rubros de recurso usados por el reporte (denominaciones oficiales SIGEP).
RUBROS = [
    ('19211', 'Por Subsidios o Subvenciones'),
    ('19212', 'Por Coparticipación Tributaria'),
]

# Recursos del techo (origen SIGEP); total 245.290.497,00 Bs.
RECURSOS = [
    {
        'rubro': '19211', 'fuente': '41', 'organismo': '119',
        'concepto': 'Por Subsidios o Subvenciones',
        'monto': Decimal('6668964.00'),
    },
    {
        'rubro': '19211', 'fuente': '41', 'organismo': '119',
        'concepto': 'Nivelación',
        'monto': Decimal('19537553.00'),
    },
    {
        'rubro': '19211', 'fuente': '41', 'organismo': '111',
        'concepto': 'Por Subsidios o Subvenciones',
        'monto': Decimal('227539.00'),
    },
    {
        'rubro': '19212', 'fuente': '41', 'organismo': '113',
        'concepto': 'Por Coparticipación Tributaria',
        'monto': Decimal('217742150.00'),
    },
    {
        'rubro': '19212', 'fuente': '41', 'organismo': '119',
        'concepto': 'Por Coparticipación Tributaria',
        'monto': Decimal('1114291.00'),
    },
]

# Gastos obligatorios que se descuentan del techo bruto; total 6.464.396,00 Bs.
# Las UE del reporte (210/250) y los objetos de gasto (7.3.1 / 7.1.6.10, SISIN)
# no existen en los catálogos locales, por eso ue y objeto_gasto quedan None.
GASTOS_OBLIGATORIOS = [
    {
        'da': '1', 'ue': None, 'programa': '88',
        'denominacion': 'Fondo de Fomento a la Educación Cívico Patriótica',
        'fuente': '41', 'organismo': '119', 'objeto_gasto': None,
        'monto': Decimal('41304.00'),
    },
    {
        'da': '1', 'ue': None, 'programa': '89',
        'denominacion': 'Ayuda Económica para Personas con Discapacidad',
        'fuente': '41', 'organismo': '111', 'objeto_gasto': None,
        'monto': Decimal('227539.00'),
    },
    {
        'da': '1', 'ue': None, 'programa': '88',
        'denominacion': 'Renta Dignidad',
        'fuente': '41', 'organismo': '119', 'objeto_gasto': None,
        'monto': Decimal('6195553.00'),
    },
]

METADATOS_IMPORTACION = {'fuente': 'clasificadores-mefp-2027'}


class Command(BaseCommand):
    help = (
        'Importa el techo presupuestario SIGEP 2027 del GAM Sacaba '
        '(reporte RFprTechoPresup, entidad 1312) como techo directivo'
    )

    def add_arguments(self, parser):
        parser.add_argument('--gestion', type=int, default=2027,
                            help='Gestión fiscal a importar (default: 2027)')
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Solo imprime lo que haría, sin escribir nada',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        gestion_anio = options['gestion']
        self.gestion_anio = gestion_anio
        self.dry_run = options['dry_run']
        self.techo_creado = False
        self.gestion_habilitada_en_run = False

        self.stdout.write(self.style.NOTICE(
            f'=== INICIO IMPORTACIÓN TECHO SIGEP (gestión {gestion_anio}) ==='
        ))
        self.stdout.write(f'    Fuente: {REPORTE_SIGEP}')
        if self.dry_run:
            self.stdout.write(self.style.WARNING(
                '    Modo dry-run: no se escribe nada en la base de datos.'
            ))

        # 1. Gestión fiscal (crear si no existe; habilitar si corresponde)
        gestion = self._obtener_gestion(gestion_anio)
        # PIP-DB-003: instancia GestionFiscal para modelos SHARED FK-izados
        # (RubroRecurso); None solo en dry-run sin gestión existente.
        self.gestion_fiscal = gestion

        # 2. Validación de gestión habilitada para techo
        self._validar_gestion(gestion)

        # 3. Techo directivo + versión actual (crear o reutilizar)
        ceiling, version = self._obtener_techo(gestion)

        # 4. Rubros de recurso oficiales del reporte
        rubros = self._importar_rubros()

        # 5. Recursos del techo (origen SIGEP)
        self._importar_recursos(version, rubros)

        # 6. Gastos obligatorios
        self._importar_obligatorios(version)

        self._resumen(gestion, version)

    # ============================================================
    # 1. GESTIÓN FISCAL
    # ============================================================
    def _obtener_gestion(self, gestion_anio):
        gestion = GestionFiscal.objects.filter(anio=gestion_anio).first()
        if gestion is not None:
            self.stdout.write(
                f'[1/6] Gestión fiscal {gestion_anio} ya existía '
                f'(estado {gestion.get_estado_display()}).'
            )
        elif self.dry_run:
            self.stdout.write(
                f'[1/6] Se crearía la gestión fiscal {gestion_anio}.'
            )
            return None
        else:
            gestion = crear_gestion(gestion_anio)
            self.gestion_habilitada_en_run = True
            self.stdout.write(self.style.SUCCESS(
                f'[1/6] Gestión fiscal {gestion_anio} creada.'
            ))

        if gestion is not None and not gestion_habilitada(gestion):
            if gestion.estado in ESTADOS_NO_HABILITABLES:
                raise CommandError(
                    f'La gestión {gestion_anio} está '
                    f'{gestion.get_estado_display()}; no se puede habilitar '
                    'para fijar techo.'
                )
            self.gestion_habilitada_en_run = True
            if self.dry_run:
                self.stdout.write(
                    f'[1/6] Se habilitaría la gestión {gestion_anio} '
                    '(estado HABILITADA).'
                )
            else:
                habilitar_gestion(gestion, None)
                self.stdout.write(self.style.SUCCESS(
                    f'[1/6] Gestión fiscal {gestion_anio} habilitada.'
                ))
        return gestion

    # ============================================================
    # 2. VALIDACIÓN DE GESTIÓN PARA TECHO
    # ============================================================
    def _validar_gestion(self, gestion):
        if gestion is None or self.gestion_habilitada_en_run:
            self.stdout.write(
                '[2/6] La gestión se habilitaría en esta ejecución; '
                'validación para techo OK.'
            )
            return
        try:
            validar_gestion_para_techo(gestion)
        except ValidationError as exc:
            raise CommandError(' '.join(exc.messages))
        self.stdout.write('[2/6] Gestión habilitada; validación para techo OK.')

    # ============================================================
    # 3. TECHO DIRECTIVO + VERSIÓN ACTUAL
    # ============================================================
    def _obtener_techo(self, gestion):
        if gestion is None:
            self.stdout.write(
                '[3/6] Se crearía el techo directivo (BORRADOR) con su '
                'versión 1.'
            )
            return None, None

        ceiling = TechoDirectivo.objects.filter(gestion=gestion).first()
        if ceiling is None:
            if self.dry_run:
                self.stdout.write(
                    '[3/6] Se crearía el techo directivo (BORRADOR) con su '
                    'versión 1.'
                )
                return None, None
            ceiling = TechoDirectivo.objects.create(
                gestion=gestion,
                estado=EstadosTecho.BORRADOR,
                version_actual=1,
            )
            TechoVersion.objects.create(
                ceiling=ceiling,
                numero=1,
                estado=EstadosTecho.BORRADOR,
            )
            self.techo_creado = True
            self.stdout.write(self.style.SUCCESS(
                '[3/6] Techo directivo creado (BORRADOR, versión 1).'
            ))
            return ceiling, ceiling.versiones.get(numero=1)

        version = TechoVersion.objects.filter(
            ceiling=ceiling, numero=ceiling.version_actual
        ).first()
        if version is None:
            raise CommandError(
                f'El techo de la gestión {self.gestion_anio} declara la '
                f'versión actual v{ceiling.version_actual}, pero esa versión '
                'no existe; revisá la consistencia del techo.'
            )
        if version.inmutable:
            raise CommandError(
                f'La versión actual del techo (v{version.numero}) está FIJADA '
                '(inmutable): no se puede editar. Usá el flujo de ajuste '
                '(nueva versión) para modificar el techo de la gestión '
                f'{self.gestion_anio}.'
            )
        self.stdout.write(
            f'[3/6] Techo existente: se actualiza la versión '
            f'v{version.numero} ({version.get_estado_display()}).'
        )
        return ceiling, version

    # ============================================================
    # 4. RUBROS DE RECURSO
    # ============================================================
    def _importar_rubros(self):
        rubros = {}
        creados = actualizados = 0
        for codigo, denominacion in RUBROS:
            if self.dry_run:
                self.stdout.write(
                    f'[4/6] Se crearía/actualizaría el rubro {codigo} '
                    f'({denominacion}).'
                )
                continue
            rubro, creado = RubroRecurso.objects.update_or_create(
                codigo=codigo, gestion=self.gestion_fiscal,
                defaults={
                    'denominacion': denominacion,
                    'fecha_vigencia_desde': date(self.gestion_anio, 1, 1),
                    'activo': True,
                    'metadatos_importacion': METADATOS_IMPORTACION,
                },
            )
            rubros[codigo] = rubro
            if creado:
                creados += 1
            else:
                actualizados += 1
        if not self.dry_run:
            self.stdout.write(
                f'[4/6] Rubros de recurso: {creados} creados, '
                f'{actualizados} actualizados (total {len(RUBROS)}).'
            )
        return rubros

    # ============================================================
    # 5. RECURSOS DEL TECHO (ORIGEN SIGEP)
    # ============================================================
    def _catalogo(self, modelo, codigo):
        from django.db.models import ForeignKey
        campo_gestion = modelo._meta.get_field('gestion')
        kwargs = {'codigo': codigo}
        if isinstance(campo_gestion, ForeignKey):
            # PIP-DB-002: organizacion.gestion es FK a GestionFiscal.
            kwargs['gestion__anio'] = self.gestion_anio
        else:
            kwargs['gestion'] = self.gestion_anio
        try:
            return modelo.objects.get(**kwargs)
        except modelo.DoesNotExist:
            raise CommandError(
                f'No se encontró {modelo._meta.verbose_name} "{codigo}" '
                f'para la gestión {self.gestion_anio}; ejecutá primero '
                'importar_catalogos_sacaba.'
            )

    def _importar_recursos(self, version, rubros):
        creados = actualizados = 0
        for dato in RECURSOS:
            rubro = rubros.get(dato['rubro'])
            fuente = self._catalogo(FuenteFinanciamiento, dato['fuente'])
            organismo = self._catalogo(
                OrganismoFinanciador, dato['organismo']
            )
            if self.dry_run:
                self.stdout.write(
                    f'[5/6] Se cargaría el recurso SIGEP rubro '
                    f'{dato["rubro"]} fuente {dato["fuente"]} organismo '
                    f'{dato["organismo"]}: {dato["concepto"]} '
                    f'({dato["monto"]:.2f} Bs).'
                )
                continue
            _, creado = RecursoTecho.objects.update_or_create(
                version=version,
                origen=OrigenRecurso.SIGEP,
                rubro=rubro,
                fuente=fuente,
                organismo=organismo,
                concepto=dato['concepto'],
                defaults={'monto': dato['monto']},
            )
            if creado:
                creados += 1
            else:
                actualizados += 1
        if not self.dry_run:
            self.stdout.write(
                f'[5/6] Recursos SIGEP: {creados} creados, '
                f'{actualizados} actualizados (total {len(RECURSOS)}).'
            )

    # ============================================================
    # 6. GASTOS OBLIGATORIOS
    # ============================================================
    def _importar_obligatorios(self, version):
        creados = actualizados = 0
        for dato in GASTOS_OBLIGATORIOS:
            da = self._catalogo(DireccionAdministrativa, dato['da'])
            fuente = self._catalogo(FuenteFinanciamiento, dato['fuente'])
            organismo = self._catalogo(
                OrganismoFinanciador, dato['organismo']
            )
            if self.dry_run:
                self.stdout.write(
                    f'[6/6] Se cargaría el gasto obligatorio programa '
                    f'{dato["programa"]}: {dato["denominacion"]} '
                    f'({dato["monto"]:.2f} Bs).'
                )
                continue
            _, creado = GastoObligatorio.objects.update_or_create(
                version=version,
                programa=dato['programa'],
                denominacion=dato['denominacion'],
                defaults={
                    'da': da,
                    'fuente': fuente,
                    'organismo': organismo,
                    'monto': dato['monto'],
                },
            )
            if creado:
                creados += 1
            else:
                actualizados += 1
        if not self.dry_run:
            self.stdout.write(
                f'[6/6] Gastos obligatorios: {creados} creados, '
                f'{actualizados} actualizados (total '
                f'{len(GASTOS_OBLIGATORIOS)}).'
            )

    # ============================================================
    # RESUMEN
    # ============================================================
    def _resumen(self, gestion, version):
        total_recursos = sum(
            (d['monto'] for d in RECURSOS), Decimal('0.00')
        )
        total_obligatorios = sum(
            (d['monto'] for d in GASTOS_OBLIGATORIOS), Decimal('0.00')
        )
        if self.dry_run:
            self.stdout.write(self.style.SUCCESS(
                '[Resumen dry-run] Gestión '
                f'{self.gestion_anio}: se cargarían {len(RECURSOS)} '
                f'recursos SIGEP ({total_recursos:.2f} Bs) y '
                f'{len(GASTOS_OBLIGATORIOS)} gastos obligatorios '
                f'({total_obligatorios:.2f} Bs). El techo quedaría en '
                'BORRADOR.'
            ))
            return
        self.stdout.write(self.style.SUCCESS(
            f'=== IMPORTACIÓN TECHO SIGEP COMPLETADA '
            f'(gestión {self.gestion_anio}) ==='
        ))
        self.stdout.write(
            f'    Techo directivo: '
            f'{"creado" if self.techo_creado else "existente"} '
            f'(versión v{version.numero}, estado '
            f'{version.get_estado_display()}).'
        )
        self.stdout.write(
            f'    Recursos SIGEP cargados: {len(RECURSOS)} '
            f'(total {total_recursos:.2f} Bs).'
        )
        self.stdout.write(
            f'    Gastos obligatorios cargados: {len(GASTOS_OBLIGATORIOS)} '
            f'(total {total_obligatorios:.2f} Bs).'
        )
        self.stdout.write(self.style.WARNING(
            '    El techo queda en BORRADOR para revisión; no se fijó la '
            'versión.'
        ))
