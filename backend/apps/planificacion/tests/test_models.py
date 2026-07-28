import datetime
from django.test import TestCase
from django.db import IntegrityError
from apps.planificacion.models import Plan, NodoPlanificacion


def _plan_defaults(**kwargs):
    defaults = dict(
        codigo='TEST-PLAN',
        nombre='Test Plan',
        tipo='pgdesa',
        gestion_inicio=2026,
        gestion_fin=2030,
        fecha_vigencia_desde=datetime.date(2026, 1, 1),
    )
    defaults.update(kwargs)
    return defaults


def _nodo_defaults(**kwargs):
    defaults = dict(
        codigo='TEST-NODO',
        nombre='Test Nodo',
        nivel='eje',
        gestion=2026,
        orden=0,
    )
    defaults.update(kwargs)
    return defaults


class PlanTipoChoicesTest(TestCase):
    def test_create_plan_with_pgdesa_tipo(self):
        """PGDESA debe ser un tipo válido de Plan"""
        plan = Plan.objects.create(**_plan_defaults(
            codigo='PGDESA-2026-2050',
            nombre='Plan General de Desarrollo Sostenible del Estado 2026-2050',
            tipo='pgdesa',
            gestion_inicio=2026,
            gestion_fin=2050,
        ))
        self.assertEqual(plan.tipo, 'pgdesa')
        self.assertEqual(plan.get_tipo_display(), 'PGDESA')

    def test_create_plan_with_pdesa_tipo(self):
        """PDESA debe ser un tipo válido de Plan"""
        plan = Plan.objects.create(**_plan_defaults(
            codigo='PDESA-2026-2030',
            nombre='Plan de Desarrollo Económico y Social 2026-2030',
            tipo='pdesa',
            gestion_inicio=2026,
            gestion_fin=2030,
        ))
        self.assertEqual(plan.tipo, 'pdesa')
        self.assertEqual(plan.get_tipo_display(), 'PDESA')

    def test_pgdesa_and_pdesa_not_returned_for_pdes_query(self):
        """Planes pgdesa/pdesa no deben aparecer en query por tipo='pdes'"""
        Plan.objects.create(**_plan_defaults(
            codigo='PGDESA-2026-2050', nombre='PGDESA',
            tipo='pgdesa', gestion_inicio=2026, gestion_fin=2050,
        ))
        Plan.objects.create(**_plan_defaults(
            codigo='PDESA-2026-2030', nombre='PDESA',
            tipo='pdesa', gestion_inicio=2026, gestion_fin=2030,
        ))
        Plan.objects.create(**_plan_defaults(
            codigo='PDES-2026', nombre='PDES existente',
            tipo='pdes', gestion_inicio=2026, gestion_fin=2030,
        ))
        pdes_plans = Plan.objects.filter(tipo='pdes')
        self.assertEqual(pdes_plans.count(), 1)
        self.assertEqual(pdes_plans.first().tipo, 'pdes')

    def test_unique_together_codigo_tipo_pgdesa(self):
        """unique_together (codigo, tipo) debe aplicarse a pgdesa"""
        Plan.objects.create(**_plan_defaults(
            codigo='PGDESA-2026-2050', nombre='Original',
            tipo='pgdesa',
        ))
        with self.assertRaises(IntegrityError):
            Plan.objects.create(**_plan_defaults(
                codigo='PGDESA-2026-2050', nombre='Duplicado',
                tipo='pgdesa',
            ))


class NodoPlanificacionNivelChoicesTest(TestCase):
    def test_create_nodo_with_componente_nivel(self):
        """'componente' debe ser un nivel válido de NodoPlanificacion"""
        plan = Plan.objects.create(**_plan_defaults(tipo='pdesa'))
        nodo = NodoPlanificacion.objects.create(
            plan=plan,
            **_nodo_defaults(nivel='componente', codigo='COMP-01')
        )
        self.assertEqual(nodo.nivel, 'componente')
        self.assertEqual(nodo.get_nivel_display(), 'Componente')

    def test_create_nodo_with_accion_nivel(self):
        """'accion' debe ser un nivel válido de NodoPlanificacion"""
        plan = Plan.objects.create(**_plan_defaults(tipo='pdesa'))
        nodo = NodoPlanificacion.objects.create(
            plan=plan,
            **_nodo_defaults(nivel='accion', codigo='ACC-01')
        )
        self.assertEqual(nodo.nivel, 'accion')
        self.assertEqual(nodo.get_nivel_display(), 'Acción')

    def test_existing_niveles_still_valid(self):
        """Los niveles existentes deben seguir funcionando"""
        plan = Plan.objects.create(**_plan_defaults(tipo='pdes'))
        for nivel, label in [
            ('pilar', 'Pilar'),
            ('eje', 'Eje Estratégico'),
            ('meta', 'Meta'),
            ('resultado', 'Resultado'),
        ]:
            nodo = NodoPlanificacion.objects.create(
                plan=plan,
                **_nodo_defaults(nivel=nivel, codigo=f'{nivel}-01')
            )
            self.assertEqual(nodo.get_nivel_display(), label)


class NodoPlanificacionSaveAutoCodigoTest(TestCase):
    def setUp(self):
        self.pgdesa_plan = Plan.objects.create(**_plan_defaults(
            codigo='PGDESA-2026-2050', tipo='pgdesa',
        ))
        self.pdesa_plan = Plan.objects.create(**_plan_defaults(
            codigo='PDESA-2026-2030', tipo='pdesa',
        ))
        self.pdes_plan = Plan.objects.create(**_plan_defaults(
            codigo='PDES-2026', tipo='pdes',
        ))

    def test_auto_code_root_pgdesa_eje_first(self):
        """Primer root nodo PGDESA sin codigo → codigo = '01'"""
        nodo = NodoPlanificacion.objects.create(
            plan=self.pgdesa_plan, nivel='eje',
            nombre='Erradicación de la pobreza',
            gestion=2026,
        )
        self.assertEqual(nodo.codigo, '01')

    def test_auto_code_root_pgdesa_eje_second(self):
        """Segundo root nodo PGDESA → codigo = '02'"""
        NodoPlanificacion.objects.create(
            plan=self.pgdesa_plan, nivel='eje',
            nombre='Primer eje', gestion=2026, codigo='01',
        )
        nodo = NodoPlanificacion.objects.create(
            plan=self.pgdesa_plan, nivel='eje',
            nombre='Segundo eje', gestion=2026,
        )
        self.assertEqual(nodo.codigo, '02')

    def test_auto_code_nested_child(self):
        """Nodo hijo con padre → codigo = '{padre.codigo}.{secuencia:02d}'"""
        padre = NodoPlanificacion.objects.create(
            plan=self.pgdesa_plan, nivel='eje',
            nombre='Eje 1', gestion=2026, codigo='01',
        )
        hijo = NodoPlanificacion.objects.create(
            plan=self.pgdesa_plan, nivel='meta',
            nombre='Meta 1.1', gestion=2026, padre=padre,
        )
        self.assertEqual(hijo.codigo, '01.01')

    def test_auto_code_nested_second_child(self):
        """Segundo hijo → codigo = '{padre.codigo}.02'"""
        padre = NodoPlanificacion.objects.create(
            plan=self.pgdesa_plan, nivel='eje',
            nombre='Eje 1', gestion=2026, codigo='01',
        )
        NodoPlanificacion.objects.create(
            plan=self.pgdesa_plan, nivel='meta',
            nombre='Meta 1.1', gestion=2026, padre=padre, codigo='01.01',
        )
        hijo = NodoPlanificacion.objects.create(
            plan=self.pgdesa_plan, nivel='meta',
            nombre='Meta 1.2', gestion=2026, padre=padre,
        )
        self.assertEqual(hijo.codigo, '01.02')

    def test_auto_code_pdesa_root_componente(self):
        """Root nodo PDESA sin codigo → codigo = '01'"""
        nodo = NodoPlanificacion.objects.create(
            plan=self.pdesa_plan, nivel='componente',
            nombre='Componente 1', gestion=2026,
        )
        self.assertEqual(nodo.codigo, '01')

    def test_auto_code_pdesa_nested_accion(self):
        """Nodo PDESA accion hijo → codigo = '{padre.codigo}.{secuencia}'"""
        padre = NodoPlanificacion.objects.create(
            plan=self.pdesa_plan, nivel='componente',
            nombre='Comp 1', gestion=2026, codigo='01',
        )
        hijo = NodoPlanificacion.objects.create(
            plan=self.pdesa_plan, nivel='accion',
            nombre='Acción 1.1', gestion=2026, padre=padre,
        )
        self.assertEqual(hijo.codigo, '01.01')

    def test_existing_codigo_not_overwritten(self):
        """Si ya tiene codigo, no se sobreescribe"""
        nodo = NodoPlanificacion.objects.create(
            plan=self.pgdesa_plan, nivel='eje',
            nombre='Eje personalizado', gestion=2026,
            codigo='CUSTOM-01',
        )
        self.assertEqual(nodo.codigo, 'CUSTOM-01')

    def test_no_auto_code_for_pdes_plan(self):
        """Plan tipo pdes NO debe auto-generar codigo"""
        nodo = NodoPlanificacion.objects.create(
            plan=self.pdes_plan, nivel='eje',
            nombre='Eje PDES', gestion=2026,
        )
        # When no codigo provided and not pgdesa/pdesa, Django saves empty string
        self.assertEqual(nodo.codigo, '')
