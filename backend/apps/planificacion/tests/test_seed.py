import datetime
from django.test import TestCase
from apps.planificacion.models import Plan, NodoPlanificacion, ArticulacionPlanificacion


def _create_seed_data():
    """Reproduce the seed script logic for testing."""
    # 1. Planes
    plan_pgdesa, _ = Plan.objects.get_or_create(
        codigo='PGDESA-2026-2050', tipo='pgdesa',
        defaults={
            'nombre': 'Plan General de Desarrollo Sostenible del Estado 2026-2050',
            'gestion_inicio': 2026, 'gestion_fin': 2050,
            'fecha_vigencia_desde': datetime.date(2026, 1, 1),
        }
    )
    plan_pdesa, _ = Plan.objects.get_or_create(
        codigo='PDESA-2026-2030', tipo='pdesa',
        defaults={
            'nombre': 'Plan de Desarrollo Económico y Social 2026-2030',
            'gestion_inicio': 2026, 'gestion_fin': 2030,
            'fecha_vigencia_desde': datetime.date(2026, 1, 1),
        }
    )

    # 2. Ejes PGDESA
    ejes_data = [
        'Erradicación de la pobreza',
        'Desarrollo social universal',
        'Desarrollo económico y productivo',
        'Desarrollo integral del hábitat',
        'Desarrollo de las capacidades productivas',
        'Gestión de riesgos y cambio climático',
        'Gestión institucional y participación social',
    ]
    ejes = []
    for i, nombre in enumerate(ejes_data, 1):
        codigo = f'{i:02d}'
        eje, _ = NodoPlanificacion.objects.get_or_create(
            plan=plan_pgdesa, codigo=codigo, nivel='eje',
            defaults={'nombre': nombre, 'gestion': 2026, 'orden': i},
        )
        ejes.append(eje)

    metas_count = 0
    resultados_pgdesa = []
    for eje in ejes:
        # 3 metas por eje
        for j in range(1, 4):
            metas_count += 1
            codigo_meta = f'{eje.codigo}.{j:02d}'
            meta, _ = NodoPlanificacion.objects.get_or_create(
                plan=plan_pgdesa, codigo=codigo_meta, nivel='meta',
                defaults={
                    'nombre': f'Meta {eje.codigo}.{j:02d} - {eje.nombre[:30]}',
                    'gestion': 2026, 'padre': eje, 'orden': j,
                },
            )
            # 2 resultados por meta
            for k in range(1, 3):
                codigo_res = f'{codigo_meta}.{k:02d}'
                resultado, _ = NodoPlanificacion.objects.get_or_create(
                    plan=plan_pgdesa, codigo=codigo_res, nivel='resultado',
                    defaults={
                        'nombre': f'Resultado {codigo_res}',
                        'gestion': 2026, 'padre': meta, 'orden': k,
                    },
                )
                resultados_pgdesa.append(resultado)

    # 4. Componentes PDESA (~24)
    componentes_data = [
        'Desarrollo normativo institucional',
        'Fortalecimiento de capacidades institucionales',
        'Planificación y gestión territorial',
        'Infraestructura productiva',
        'Desarrollo agropecuario',
        'Seguridad alimentaria',
        'Promoción del empleo digno',
        'Fomento a la micro y pequeña empresa',
        'Turismo sostenible',
        'Desarrollo industrial',
        'Energías renovables',
        'Conectividad vial',
        'Agua potable y saneamiento',
        'Vivienda social',
        'Gestión de residuos sólidos',
        'Protección de cuencas y recursos hídricos',
        'Conservación de la biodiversidad',
        'Educación y capacitación técnica',
        'Salud preventiva',
        'Cultura y deporte',
        'Participación ciudadana',
        'Transparencia y lucha contra la corrupción',
        'Gestión de riesgos',
        'Desarrollo urbano sostenible',
    ]
    componentes = []
    for i, nombre in enumerate(componentes_data, 1):
        codigo = f'{i:02d}'
        componente, _ = NodoPlanificacion.objects.get_or_create(
            plan=plan_pdesa, codigo=codigo, nivel='componente',
            defaults={'nombre': nombre, 'gestion': 2026, 'orden': i},
        )
        componentes.append(componente)

    # 2-3 acciones por componente
    for comp in componentes:
        for j in range(1, 4 if componentes.index(comp) % 2 == 0 else 3):
            codigo_acc = f'{comp.codigo}.{j:02d}'
            NodoPlanificacion.objects.get_or_create(
                plan=plan_pdesa, codigo=codigo_acc, nivel='accion',
                defaults={
                    'nombre': f'Acción {comp.codigo}.{j:02d} - {comp.nombre[:30]}',
                    'gestion': 2026, 'padre': comp, 'orden': j,
                },
            )

    # 5. Articulaciones PGDESA resultado → PDESA componente
    # Link each resultado to a componente (round-robin)
    for i, resultado in enumerate(resultados_pgdesa):
        componente = componentes[i % len(componentes)]
        ArticulacionPlanificacion.objects.get_or_create(
            nodo_origen=resultado,
            nodo_destino=componente,
            gestion=2026,
            defaults={'es_principal': True},
        )

    return {
        'plan_pgdesa': plan_pgdesa,
        'plan_pdesa': plan_pdesa,
        'ejes': ejes,
        'componentes': componentes,
    }


class SeedPGDESAPDESATest(TestCase):
    def test_seed_creates_two_plans(self):
        """Seed debe crear Plan PGDESA y Plan PDESA"""
        result = _create_seed_data()
        self.assertEqual(result['plan_pgdesa'].tipo, 'pgdesa')
        self.assertEqual(result['plan_pdesa'].tipo, 'pdesa')

    def test_seed_creates_7_ejes(self):
        """Seed debe crear 7 ejes PGDESA"""
        result = _create_seed_data()
        self.assertEqual(len(result['ejes']), 7)

    def test_seed_creates_metas_and_resultados(self):
        """Seed debe crear 3 metas x 7 ejes = 21 metas, 2 resultados x 21 metas = 42 resultados"""
        _create_seed_data()
        plan_pgdesa = Plan.objects.get(codigo='PGDESA-2026-2050', tipo='pgdesa')
        metas = NodoPlanificacion.objects.filter(plan=plan_pgdesa, nivel='meta')
        resultados = NodoPlanificacion.objects.filter(plan=plan_pgdesa, nivel='resultado')
        self.assertEqual(metas.count(), 21)
        self.assertEqual(resultados.count(), 42)

    def test_seed_creates_24_componentes(self):
        """Seed debe crear ~24 componentes PDESA"""
        result = _create_seed_data()
        self.assertEqual(len(result['componentes']), 24)

    def test_seed_creates_acciones_for_componentes(self):
        """Seed debe crear acciones para cada componente"""
        _create_seed_data()
        plan_pdesa = Plan.objects.get(codigo='PDESA-2026-2030', tipo='pdesa')
        acciones = NodoPlanificacion.objects.filter(plan=plan_pdesa, nivel='accion')
        # 12 componentes with 3 acciones + 12 with 2 acciones = 60
        self.assertEqual(acciones.count(), 60)

    def test_seed_creates_articulaciones(self):
        """Seed debe crear ArticulacionPlanificacion entre resultados y componentes"""
        result = _create_seed_data()
        plan_pgdesa = result['plan_pgdesa']
        resultados = NodoPlanificacion.objects.filter(plan=plan_pgdesa, nivel='resultado')
        arts = ArticulacionPlanificacion.objects.filter(
            nodo_origen__in=resultados, gestion=2026
        )
        self.assertEqual(arts.count(), 42)

    def test_seed_idempotent_second_run(self):
        """Segunda ejecución del seed no debe duplicar datos"""
        _create_seed_data()
        # Counts after first run
        planes_count = Plan.objects.count()
        pgdesa_nodes = NodoPlanificacion.objects.filter(
            plan__tipo='pgdesa'
        ).count()
        pdesa_nodes = NodoPlanificacion.objects.filter(
            plan__tipo='pdesa'
        ).count()
        arts_count = ArticulacionPlanificacion.objects.count()

        # Second run
        _create_seed_data()

        self.assertEqual(Plan.objects.count(), planes_count)
        self.assertEqual(
            NodoPlanificacion.objects.filter(plan__tipo='pgdesa').count(),
            pgdesa_nodes
        )
        self.assertEqual(
            NodoPlanificacion.objects.filter(plan__tipo='pdesa').count(),
            pdesa_nodes
        )
        self.assertEqual(ArticulacionPlanificacion.objects.count(), arts_count)
