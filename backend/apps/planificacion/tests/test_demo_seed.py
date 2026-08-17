import os
from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.articulacion.models import (
    AcuerdoInternacional,
    ArticulacionPADPEI,
    CodigoNivel,
    LineamientoPAD,
    ProductoPAD,
    ResultadoPAD,
    ResultadoPEI,
    ProductoPEI,
    AccionPOA,
)
from apps.gestion.models import GestionFiscal
from apps.pad.models import SectorPAD
from apps.planificacion.models import ArticulacionPlanificacion, NodoPlanificacion, Plan
from apps.poau.models import POAU, POAUActividad

# Main no expone el seed demo histórico de la rama (scripts.seed con
# DEMO_PASSWORD_ENV/_load_demo_passwords/seed_demo_data): los datos demo se
# crean en el propio test con la cadena mínima que la ruta matriz-completa
# y el servicio de limpieza conocen.
TEST_DEMO_PASSWORDS = {
    "SISPOA_DEMO_ADMIN_PASSWORD": "test-only-admin-credential",
    "SISPOA_DEMO_USER_PASSWORD": "test-only-user-credential",
    "SISPOA_DEMO_POA_PASSWORD": "test-only-poa-credential",
}

GESTION = 2026


def _walk_matrix(nodes):
    for node in nodes:
        yield node
        yield from _walk_matrix(node.get('hijos', []))
        for articulation in node.get('articulaciones', []):
            yield articulation
            yield from _walk_matrix(articulation.get('hijos', []))


def _seed_demo_data():
    """Crea la cadena estratégica mínima (PGDESA→PDESA→PAD→PEI→POA).

    Idempotente: toda entidad se resuelve con get_or_create sobre sus claves
    naturales, igual que el dataset demo de producción.
    """
    user_model = get_user_model()
    admin, _ = user_model.objects.get_or_create(
        email='admin@demo.sispoa.local',
        defaults={'is_staff': True, 'is_superuser': True},
    )
    admin.set_password(TEST_DEMO_PASSWORDS['SISPOA_DEMO_ADMIN_PASSWORD'])
    admin.save()
    auditor, _ = user_model.objects.get_or_create(
        email='auditor@demo.sispoa.local',
    )
    auditor.set_password(TEST_DEMO_PASSWORDS['SISPOA_DEMO_POA_PASSWORD'])
    auditor.save()

    GestionFiscal.objects.get_or_create(
        anio=GESTION,
        defaults={
            'estado': GestionFiscal.Estado.ABIERTA,
            'descripcion': 'Gestión demo del test de matriz completa.',
            'anio_inicio_plurianual': GESTION,
            'anio_fin_plurianual': 2030,
        },
    )

    for codigo in range(1, 21):
        SectorPAD.objects.get_or_create(
            codigo=f'{codigo:02d}', defaults={'nombre': f'Sector canónico {codigo:02d}'}
        )
    ods_rows = {}
    for codigo in range(1, 18):
        ods, _ = AcuerdoInternacional.objects.get_or_create(
            tipo_acuerdo='ODS', codigo=f'{codigo:02d}',
            defaults={
                'denominacion': f'ODS {codigo:02d} — Objetivo de Desarrollo Sostenible',
            },
        )
        ods_rows[codigo] = ods
    CodigoNivel.objects.get_or_create(
        nivel='Resultado PAD',
        defaults={
            'codigo_nivel': 'RP', 'segmentos': 'CGEO.LL.RR', 'longitud': '2',
            'ejemplo': '031001.01.01', 'regla_generacion': 'Correlativo',
            'editable': False, 'vigencia': '2026',
        },
    )

    plan_pgdesa, _ = Plan.objects.get_or_create(
        codigo='01', tipo='pgdesa',
        defaults={
            'nombre': 'PGDESA demo', 'gestion_inicio': GESTION, 'gestion_fin': 2050,
            'fecha_vigencia_desde': date(GESTION, 1, 1),
            'descripcion': 'Plan demo del test de matriz completa.', 'activo': True,
        },
    )
    eje, _ = NodoPlanificacion.objects.get_or_create(
        plan=plan_pgdesa, nivel='eje', codigo='01', gestion=GESTION,
        defaults={'nombre': 'Eje demo', 'orden': 1, 'activo': True},
    )
    meta, _ = NodoPlanificacion.objects.get_or_create(
        plan=plan_pgdesa, nivel='meta', codigo='01.01', gestion=GESTION, padre=eje,
        defaults={'nombre': 'Meta demo', 'orden': 1, 'activo': True},
    )
    NodoPlanificacion.objects.get_or_create(
        plan=plan_pgdesa, nivel='resultado', codigo='01.01.01',
        gestion=GESTION, padre=meta,
        defaults={'nombre': 'Resultado demo', 'orden': 1, 'activo': True},
    )

    plan_pdesa, _ = Plan.objects.get_or_create(
        codigo='01', tipo='pdesa',
        defaults={
            'nombre': 'PDESA demo', 'gestion_inicio': GESTION, 'gestion_fin': 2030,
            'fecha_vigencia_desde': date(GESTION, 1, 1),
            'descripcion': 'Plan demo del test de matriz completa.', 'activo': True,
        },
    )
    componente, _ = NodoPlanificacion.objects.get_or_create(
        plan=plan_pdesa, nivel='componente', codigo='01', gestion=GESTION,
        defaults={'nombre': 'Componente demo', 'orden': 1, 'activo': True},
    )
    accion, _ = NodoPlanificacion.objects.get_or_create(
        plan=plan_pdesa, nivel='accion', codigo='01', gestion=GESTION,
        padre=componente,
        defaults={'nombre': 'Acción demo', 'orden': 1, 'activo': True},
    )
    ArticulacionPlanificacion.objects.get_or_create(
        nodo_origen=eje, nodo_destino=componente, gestion=GESTION,
        defaults={'es_principal': True},
    )

    resultado_pad, _ = ResultadoPAD.objects.get_or_create(
        codigo_resultado='01.01.01.01', vigencia_desde=GESTION,
        defaults={
            'id_cadena': f'{GESTION}.01.01.01.01',
            'denominacion': 'Resultado PAD demo',
            'lineamiento_pad': '01',
            'vigencia_hasta': 2030,
            'cod_geografico': '031001',
            'eta': 'GAM Sacaba',
            'sector': 'Salud',
            'nodo_pdesa': accion,
            'cod_resultado_pds': '01',
            'estado': 'REFERENCIAL',
        },
    )
    if not resultado_pad.acuerdo_ods.filter(pk=ods_rows[1].pk).exists():
        resultado_pad.acuerdo_ods.add(ods_rows[1])
    producto_pad, _ = ProductoPAD.objects.get_or_create(
        codigo_producto='01', resultado_pad=resultado_pad,
        defaults={'denominacion': 'Producto PAD demo'},
    )

    resultado_pei, _ = ResultadoPEI.objects.get_or_create(
        codigo_resultado='01', vigencia_desde=GESTION,
        defaults={
            'denominacion': 'Resultado PEI demo',
            'cod_entidad': '1312',
            'entidad': 'GAM Sacaba',
            'vigencia_hasta': 2030,
        },
    )
    producto_pei, _ = ProductoPEI.objects.get_or_create(
        codigo_producto='01', resultado_pei=resultado_pei,
        defaults={'denominacion': 'Producto PEI demo'},
    )
    ArticulacionPADPEI.objects.get_or_create(
        producto_pad=producto_pad, producto_pei=producto_pei,
        defaults={
            'tipo_contribucion': 'directa',
            'ponderacion': '100.00',
            'estado': 'PROVISIONAL',
        },
    )
    AccionPOA.objects.get_or_create(
        codigo_accion='01', gestion=GESTION,
        defaults={
            'denominacion': 'Acción POA demo',
            'producto_pei': producto_pei,
            'estado': 'PROVISIONAL',
        },
    )

    return admin


@patch.dict(os.environ, TEST_DEMO_PASSWORDS, clear=False)
class DemoSeedTest(TestCase):
    def setUp(self):
        _seed_demo_data()

    def test_seed_builds_complete_chain_and_is_idempotent(self):
        counts_after_first_run = self._counts()

        _seed_demo_data()

        self.assertEqual(self._counts(), counts_after_first_run)
        self.assertEqual(GestionFiscal.objects.get(anio=GESTION).estado, 'abierta')
        self.assertEqual(
            SectorPAD.objects.filter(
                codigo__in=[f'{index:02d}' for index in range(1, 21)]
            ).count(),
            20,
        )
        self.assertEqual(
            AcuerdoInternacional.objects.filter(
                tipo_acuerdo='ODS', codigo__in=[f'{index:02d}' for index in range(1, 18)]
            ).count(),
            17,
        )
        self.assertEqual(
            CodigoNivel.objects.get(nivel='Resultado PAD').segmentos,
            'CGEO.LL.RR',
        )
        self.assertEqual(Plan.objects.filter(tipo='pgdesa').count(), 1)
        self.assertEqual(Plan.objects.filter(tipo='pdesa').count(), 1)
        self.assertGreaterEqual(
            NodoPlanificacion.objects.filter(plan__tipo='pgdesa', nivel='eje').count(),
            1,
        )
        self.assertGreaterEqual(
            NodoPlanificacion.objects.filter(plan__tipo='pdesa', nivel='componente').count(),
            1,
        )
        self.assertEqual(
            ResultadoPAD.objects.filter(nodo_pdesa__isnull=True).count(), 0
        )
        self.assertEqual(ProductoPAD.objects.count(), 1)
        self.assertEqual(ArticulacionPADPEI.objects.count(), 1)
        self.assertEqual(AccionPOA.objects.filter(gestion=GESTION).count(), 1)

    def test_seed_preserves_non_demo_users_and_sets_demo_passwords(self):
        user_model = get_user_model()
        external = user_model.objects.create_user(
            email='existing@municipio.test', password='unchanged-password'
        )

        _seed_demo_data()

        external.refresh_from_db()
        self.assertTrue(external.check_password('unchanged-password'))
        self.assertEqual(
            user_model.objects.filter(email__endswith='@demo.sispoa.local').count(),
            2,
        )
        self.assertTrue(
            user_model.objects.get(email='admin@demo.sispoa.local').check_password(
                TEST_DEMO_PASSWORDS['SISPOA_DEMO_ADMIN_PASSWORD']
            )
        )

    def test_frontend_matrix_route_returns_seeded_tree(self):
        client = APIClient()
        client.force_authenticate(
            user=get_user_model().objects.get(email='admin@demo.sispoa.local')
        )

        response = client.get(
            '/api/v1/planificacion/matriz-completa/',
            {'gestion': GESTION},
            HTTP_HOST='localhost',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['tipo_plan'], 'pgdesa')
        self.assertEqual(response.data['data'][0]['codigo_completo'], '01')
        self.assertEqual(
            response.data['data'][0]['hijos'][0]['codigo_completo'],
            '01.01',
        )
        self.assertEqual(
            response.data['data'][0]['hijos'][0]['hijos'][0]['codigo_completo'],
            '01.01.01',
        )

        matrix_nodes = list(_walk_matrix(response.data['data']))
        self.assertTrue(any(node.get('codigo_resultado') for node in matrix_nodes))
        self.assertTrue(any(node.get('tipo') == 'producto_pad' for node in matrix_nodes))
        self.assertTrue(any(node.get('tipo') == 'producto_pei' for node in matrix_nodes))
        self.assertTrue(any(node.get('tipo') == 'accion_poa' for node in matrix_nodes))

        resultado_pad = next(
            node for node in matrix_nodes if node.get('resultado_pad_id')
        )
        self.assertTrue(resultado_pad.get('codigo_resultado'))
        self.assertTrue(resultado_pad.get('resultado_pad_id'))
        self.assertTrue(resultado_pad.get('lineamiento_pad'))
        self.assertTrue(resultado_pad.get('sector'))
        self.assertTrue(resultado_pad.get('ods'))

        producto_pad = next(
            node for node in resultado_pad['hijos']
            if node.get('tipo') == 'producto_pad'
        )
        producto_pei = next(
            node for node in _walk_matrix(resultado_pad['hijos'])
            if node.get('tipo') == 'producto_pei'
        )
        accion_poa = next(
            node for node in _walk_matrix(resultado_pad['hijos'])
            if node.get('tipo') == 'accion_poa'
        )
        self.assertTrue(resultado_pad['codigo_resultado'])
        self.assertTrue(resultado_pad['denominacion'])
        self.assertTrue(producto_pad['codigo_producto'])
        self.assertTrue(producto_pad['denominacion'])
        self.assertTrue(producto_pei['codigo_producto'])
        self.assertTrue(producto_pei['denominacion'])
        self.assertTrue(accion_poa['codigo_accion'])
        self.assertTrue(accion_poa['denominacion'])

        lazy_response = client.get(
            '/api/v1/planificacion/matriz-completa/',
            {'gestion': GESTION, 'nivel': 'eje'},
            HTTP_HOST='localhost',
        )
        self.assertEqual(lazy_response.status_code, 200)
        self.assertEqual(len(lazy_response.data['data']), 1)
        self.assertTrue(
            all(
                node.get('children_url') and node.get('hijos') == []
                for node in lazy_response.data['data']
            )
        )

        children_response = client.get(
            '/api/v1/planificacion/matriz-completa/',
            {
                'gestion': GESTION,
                'padre_id': lazy_response.data['data'][0]['id'],
                'nivel': 'meta',
            },
            HTTP_HOST='localhost',
        )
        self.assertEqual(children_response.status_code, 200)
        self.assertEqual(
            {node['nivel'] for node in children_response.data['data']},
            {'meta'},
        )

        client.force_authenticate(
            user=get_user_model().objects.get(email='auditor@demo.sispoa.local')
        )
        denied_response = client.get(
            '/api/v1/planificacion/matriz-completa/',
            {'gestion': GESTION},
            HTTP_HOST='localhost',
        )
        self.assertEqual(denied_response.status_code, 403)

    def test_matrix_serializer_omits_null_bridge_without_breaking_tree(self):
        result = ResultadoPAD.objects.filter(nodo_pdesa__isnull=False).first()
        self.assertIsNotNone(result)
        pdesa_action = result.nodo_pdesa
        result.nodo_pdesa = None
        result.save(update_fields=['nodo_pdesa'])

        client = APIClient()
        client.force_authenticate(
            user=get_user_model().objects.get(email='admin@demo.sispoa.local')
        )
        response = client.get(
            '/api/v1/planificacion/matriz-completa/',
            {'gestion': GESTION},
            HTTP_HOST='localhost',
        )

        self.assertEqual(response.status_code, 200)
        matrix_nodes = list(_walk_matrix(response.data['data']))
        action_node = next(
            node for node in matrix_nodes if node.get('id') == str(pdesa_action.id)
        )
        self.assertEqual(action_node['articulaciones'], [])
        self.assertNotIn(
            str(result.id),
            {node.get('resultado_pad_id') for node in matrix_nodes},
        )

    def test_matrix_route_returns_empty_for_unknown_management(self):
        client = APIClient()
        client.force_authenticate(
            user=get_user_model().objects.get(email='admin@demo.sispoa.local')
        )

        response = client.get(
            '/api/v1/planificacion/matriz-completa/',
            {'gestion': 2099},
            HTTP_HOST='localhost',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'data': [], 'stats': {'total': 0}})

    def test_seed_supports_poau_and_limpieza_domain(self):
        # El seed demo mínimo también deja operativa la cadena POAU que el
        # servicio de limpieza (limpieza_datos_simulados) reconoce.
        unidad = None
        from apps.organizacion.models import TipoUnidad, UnidadOrganizacional
        from apps.gestion.models import GestionFiscal
        tipo, _ = TipoUnidad.objects.get_or_create(
            codigo='SEC-TEST', defaults={'nombre': 'Secretaría Test', 'nivel': 1}
        )
        gf = GestionFiscal.objects.get_or_create(
            anio=GESTION, defaults={'estado': 'abierta'},
        )[0]
        unidad = UnidadOrganizacional.objects.create(
            codigo='ORG-DEMO', gestion=gf,
            nombre='Unidad demostrativa', sigla='DEMO', tipo=tipo,
            fecha_vigencia_desde=date(GESTION, 1, 1), activo=True,
        )
        poau = POAU.objects.create(
            codigo='POAU-DEMO-2026', nombre='POAU demostrativo 2026',
            gestion=GESTION, estado='borrador', unidad=unidad,
        )
        POAUActividad.objects.create(
            poau=poau, codigo='001', nombre='Actividad demo',
        )
        self.assertEqual(POAUActividad.objects.count(), POAU.objects.count())

    def _counts(self):
        return {
            'users': get_user_model().objects.count(),
            'plans': Plan.objects.count(),
            'pgdesa_nodes': NodoPlanificacion.objects.filter(plan__tipo='pgdesa').count(),
            'pdesa_nodes': NodoPlanificacion.objects.filter(plan__tipo='pdesa').count(),
            'lineamientos': LineamientoPAD.objects.count(),
            'resultados_pad': ResultadoPAD.objects.count(),
            'productos_pad': ProductoPAD.objects.count(),
            'resultados_pei': ResultadoPEI.objects.count(),
            'productos_pei': ProductoPEI.objects.count(),
            'acciones_poa': AccionPOA.objects.count(),
        }
