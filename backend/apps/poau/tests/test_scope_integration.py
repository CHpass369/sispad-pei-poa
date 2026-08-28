"""Tests de integración F2b: filtro por UO efectiva + CapacidadConScope en
la API V2 del SIS-POA (ADR-003).

Sin `__init__.py` en este directorio a propósito: `apps/poau/tests.py` ya
existe como módulo y un paquete `tests/` lo sombrearía en la colección de
pytest (misma convención que `apps/accounts/tests/`, ver F2a).

Jerarquía de UOs compartida (setUpTestData, read-only en los tests)::

    GAMS (root)
    └── Secretaría Municipal
        ├── Dirección de Catastro
        │   └── Unidad de Catastro
        └── Dirección de Educación
            └── Unidad de Educación Inicial

Roles/alcances sembrados por caso:

- SUPER_ADMIN: `is_superuser`, sin alcances (bypass).
- JEFE_POA: GLOBAL en Secretaría (capacidades sis_poa.*).
- JEFE_PE: GLOBAL en Secretaría pero solo capacidades sis_pe.*.
- SECRETARIO_MUNICIPAL: DESCENDANTS en Secretaría.
- DIRECTOR: DESCENDANTS en Dirección de Catastro.
- FORMULADOR_POAU: SELF en Unidad de Catastro.
- SIN_ALCANCE: rol DIRECTOR sin alcances (fail-closed).
"""
from datetime import date
import uuid
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import (
    AlcanceOrganizacional, Capacidad, Rol, Usuario,
)
from apps.gestion.models import GestionFiscal
from apps.organizacion.models import TipoUnidad, UnidadOrganizacional
from apps.poau.models_v2 import (
    AccionCortoPlazo, Actividad, Operacion, PoAInstitucional,
    ProgramacionActividad, Tarea,
)
from apps.poau.models import (
    EjecucionFinanciera, EjecucionFisica, POAU, POAUActividad,
)

CAP_POAU_VIEW = 'sis_poa.poau.view'
CAP_POAU_EDIT = 'sis_poa.poau.edit'
CAP_POAU_CREATE = 'sis_poa.poau.create'
CAP_POAU_SUBMIT = 'sis_poa.poau.submit'
CAP_POAU_REVIEW = 'sis_poa.poau.review'
CAP_POAU_APPROVE = 'sis_poa.poau.approve'
CAP_POA_VIEW = 'sis_poa.poa.view'
CAP_POA_EDIT = 'sis_poa.poa.edit'
CAPS_SIS_POA = [
    CAP_POAU_VIEW, CAP_POAU_EDIT, CAP_POAU_CREATE, CAP_POAU_SUBMIT,
    CAP_POAU_REVIEW, CAP_POAU_APPROVE, CAP_POA_VIEW, CAP_POA_EDIT,
]


class FiscalAPIClient(APIClient):
    """API client that supplies the fiscal context expected by V2 requests."""

    def __init__(self, gestion_id):
        super().__init__()
        self.gestion_id = gestion_id

    def request(self, **kwargs):
        query = kwargs.get('QUERY_STRING', '')
        if self.gestion_id and 'gestion_id=' not in query:
            separator = '&' if query else ''
            kwargs['QUERY_STRING'] = (
                f'{query}{separator}gestion_id={self.gestion_id}'
            )
        return super().request(**kwargs)


class ScopeIntegrationBase(TestCase):
    """Jerarquía de UOs, roles/alcances F1 y jerarquía POA compartidos."""

    @classmethod
    def setUpTestData(cls):
        cls.gestion, _ = GestionFiscal.objects.get_or_create(
            anio=2026, defaults={'estado': 'preparacion'},
        )
        tipo, _ = TipoUnidad.objects.get_or_create(
            codigo='S2-TIPO', defaults={'nombre': 'Tipo test F2b', 'nivel': 1},
        )
        vig = date(2026, 1, 1)

        def uo(codigo, nombre, padre):
            return UnidadOrganizacional.objects.create(
                codigo=codigo, nombre=nombre, tipo=tipo, padre=padre,
                gestion=cls.gestion, fecha_vigencia_desde=vig,
            )

        cls.gams = uo('S2-GAMS', 'Gobierno Autónomo Municipal de Sacaba', None)
        cls.secretaria = uo('S2-SEC', 'Secretaría Municipal', cls.gams)
        cls.dir_catastro = uo(
            'S2-DCAT', 'Dirección de Catastro', cls.secretaria,
        )
        cls.uo_catastro = uo('S2-UCAT', 'Unidad de Catastro', cls.dir_catastro)
        cls.dir_educacion = uo(
            'S2-DEDU', 'Dirección de Educación', cls.secretaria,
        )
        cls.uo_ed_inicial = uo(
            'S2-UEI', 'Unidad de Educación Inicial', cls.dir_educacion,
        )

        def cap(codigo):
            capacidad, _ = Capacidad.objects.get_or_create(
                codigo=codigo,
                defaults={
                    'nombre': codigo, 'sistema': codigo.split('.')[0],
                },
            )
            return capacidad

        def rol(codigo, capacidades):
            r, _ = Rol.objects.get_or_create(
                codigo=codigo, defaults={'nombre': codigo},
            )
            r.capacidades.add(*[cap(c) for c in capacidades])
            return r

        cls.rol_jefe_poa = rol('JEFE_POA', CAPS_SIS_POA)
        cls.rol_jefe_pe = rol('JEFE_PE', ['sis_pe.pad.view'])
        cls.rol_secretario = rol('SECRETARIO_MUNICIPAL', CAPS_SIS_POA)
        cls.rol_director = rol('DIRECTOR', CAPS_SIS_POA)
        cls.rol_formulador = rol(
            'FORMULADOR_POAU', [
                CAP_POAU_VIEW, CAP_POAU_EDIT, CAP_POAU_CREATE, CAP_POAU_SUBMIT,
            ],
        )

        def usuario(email, rol_asignado=None, **kwargs):
            u = Usuario.objects.create_user(
                email=email, password='test-2026', **kwargs,
            )
            if rol_asignado is not None:
                u.roles.add(rol_asignado)
            return u

        cls.super_admin = usuario(
            's2-superadmin@test.gob.bo', is_staff=True, is_superuser=True,
        )
        cls.jefe_poa = usuario('s2-jefe-poa@test.gob.bo', cls.rol_jefe_poa)
        cls.jefe_pe = usuario('s2-jefe-pe@test.gob.bo', cls.rol_jefe_pe)
        cls.secretario = usuario(
            's2-secretario@test.gob.bo', cls.rol_secretario,
        )
        cls.director = usuario('s2-director@test.gob.bo', cls.rol_director)
        cls.formulador = usuario(
            's2-formulador@test.gob.bo', cls.rol_formulador,
        )
        cls.sin_alcance = usuario(
            's2-sin-alcance@test.gob.bo', cls.rol_director,
        )

        def alcance(user, unidad, scope_type):
            return AlcanceOrganizacional.objects.create(
                usuario=user, unidad=unidad, scope_type=scope_type,
                fiscal_year=unidad.gestion,
            )

        alcance(cls.jefe_poa, cls.secretaria, AlcanceOrganizacional.SCOPE_GLOBAL)
        alcance(cls.jefe_pe, cls.secretaria, AlcanceOrganizacional.SCOPE_GLOBAL)
        alcance(
            cls.secretario, cls.secretaria,
            AlcanceOrganizacional.SCOPE_DESCENDANTS,
        )
        alcance(
            cls.director, cls.dir_catastro,
            AlcanceOrganizacional.SCOPE_DESCENDANTS,
        )
        alcance(
            cls.formulador, cls.uo_catastro,
            AlcanceOrganizacional.SCOPE_SELF,
        )
        # cls.sin_alcance queda sin alcances a propósito (fail-closed).

        # POA con dos acciones en ramas distintas y jerarquía completa.
        cls.poa = PoAInstitucional.objects.create(
            gestion=2026, codigo='POA-S2-1', nombre='POA test F2b',
        )
        cls.accion_catastro = AccionCortoPlazo.objects.create(
            poa=cls.poa, codigo='ACP-S2-CAT', nombre='Acción Catastro',
            unidad=cls.uo_catastro,
        )
        cls.accion_educacion = AccionCortoPlazo.objects.create(
            poa=cls.poa, codigo='ACP-S2-EDU', nombre='Acción Educación',
            unidad=cls.uo_ed_inicial,
        )
        cls.operacion_catastro = Operacion.objects.create(
            accion=cls.accion_catastro, codigo='OP-S2-CAT',
            nombre='Operación Catastro',  # sin UO propia: hereda de la acción
        )
        cls.actividad_catastro = Actividad.objects.create(
            operacion=cls.operacion_catastro, codigo='ACT-S2-CAT',
            nombre='Actividad Catastro',
        )
        cls.tarea_catastro = Tarea.objects.create(
            actividad=cls.actividad_catastro, codigo='TAR-S2-CAT',
            nombre='Tarea Catastro',
        )
        cls.programacion_catastro = ProgramacionActividad.objects.create(
            actividad=cls.actividad_catastro, anio=2026,
            tipo=ProgramacionActividad.TIPO_FISICA,
        )
        cls.operacion_educacion = Operacion.objects.create(
            accion=cls.accion_educacion, codigo='OP-S2-EDU',
            nombre='Operación Educación',
        )
        cls.actividad_educacion = Actividad.objects.create(
            operacion=cls.operacion_educacion, codigo='ACT-S2-EDU',
            nombre='Actividad Educación',
        )
        cls.tarea_educacion = Tarea.objects.create(
            actividad=cls.actividad_educacion, codigo='TAR-S2-EDU',
            nombre='Tarea Educación',
        )

    def cliente(self, usuario, gestion=None):
        client = FiscalAPIClient(str((gestion or self.gestion).pk))
        client.force_authenticate(user=usuario)
        return client

    @staticmethod
    def ids_de(response):
        data = response.data
        if isinstance(data, dict) and 'results' in data:
            data = data['results']
        return {str(item['id']) for item in data}

    def detalle_accion(self, usuario, accion):
        return self.cliente(usuario).get(
            reverse('v2-acciones-poa-detail', kwargs={'pk': accion.pk}),
        )

    def actualizar_accion(self, usuario, accion, **extra):
        payload = {
            'poa': str(accion.poa_id),
            'codigo': accion.codigo,
            'nombre': accion.nombre,
            'unidad': str(accion.unidad_id),
            **extra,
        }
        return self.cliente(usuario).put(
            reverse('v2-acciones-poa-detail', kwargs={'pk': accion.pk}),
            payload, format='json',
        )


class AccionListScopeTests(ScopeIntegrationBase):
    """B. GET /api/v2/sis-poa/acciones/ — visibilidad por rol y alcance."""

    def listar(self, usuario):
        return self.cliente(usuario).get(reverse('v2-acciones-poa-list'))

    def test_superadmin_ve_todas_las_acciones_por_bypass(self):
        response = self.listar(self.super_admin)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.ids_de(response),
            {str(self.accion_catastro.id), str(self.accion_educacion.id)},
        )

    def test_jefe_poa_global_ve_todas_las_acciones(self):
        response = self.listar(self.jefe_poa)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.ids_de(response),
            {str(self.accion_catastro.id), str(self.accion_educacion.id)},
        )

    def test_jefe_pe_sin_capacidad_sis_poa_recibe_403(self):
        response = self.listar(self.jefe_pe)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_secretario_descendants_ve_todas_las_acciones(self):
        response = self.listar(self.secretario)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.ids_de(response),
            {str(self.accion_catastro.id), str(self.accion_educacion.id)},
        )

    def test_director_ve_solo_la_accion_de_catastro(self):
        response = self.listar(self.director)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.ids_de(response), {str(self.accion_catastro.id)},
        )

    def test_formulador_ve_solo_la_accion_de_catastro(self):
        response = self.listar(self.formulador)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.ids_de(response), {str(self.accion_catastro.id)},
        )

    def test_formulador_no_ve_la_accion_de_educacion(self):
        response = self.listar(self.formulador)
        self.assertNotIn(str(self.accion_educacion.id), self.ids_de(response))

    def test_usuario_con_capacidad_sin_alcances_recibe_403(self):
        """Fail-closed: capacidad sin AlcanceOrganizacional no habilita nada."""
        response = self.listar(self.sin_alcance)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AccionDetailScopeTests(ScopeIntegrationBase):
    """C. GET /api/v2/sis-poa/acciones/{id}/ — 404 fail-closed fuera de scope."""

    def test_director_get_accion_propia_200(self):
        response = self.detalle_accion(self.director, self.accion_catastro)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_director_get_accion_ajena_404(self):
        """404 y no 403: no se expone la existencia del objeto (decisión F2b)."""
        response = self.detalle_accion(self.director, self.accion_educacion)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_formulador_get_accion_propia_200(self):
        response = self.detalle_accion(self.formulador, self.accion_catastro)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_formulador_get_accion_ajena_404(self):
        response = self.detalle_accion(self.formulador, self.accion_educacion)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AccionUpdateScopeTests(ScopeIntegrationBase):
    """D. PUT /api/v2/sis-poa/acciones/{id}/ — escritura acotada al alcance."""

    def test_director_put_accion_propia_200(self):
        response = self.actualizar_accion(
            self.director, self.accion_catastro, nombre='Acción Catastro v2',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_director_put_accion_ajena_404(self):
        response = self.actualizar_accion(self.director, self.accion_educacion)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_formulador_put_accion_propia_200(self):
        response = self.actualizar_accion(
            self.formulador, self.accion_catastro, nombre='Acción Formulador',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_formulador_put_accion_ajena_404(self):
        response = self.actualizar_accion(
            self.formulador, self.accion_educacion,
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_jefe_pe_put_cualquier_accion_403(self):
        """Sin capacidad sis_poa.poau.edit: 403 antes de tocar el queryset."""
        response = self.actualizar_accion(self.jefe_pe, self.accion_catastro)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_no_permite_mover_accion_a_unidad_ajena(self):
        """El permiso de objeto valida el estado actual; el destino lo valida
        `perform_update`: un PATCH de `unidad` a una UO ajena se rechaza."""
        response = self.actualizar_accion(
            self.formulador, self.accion_catastro,
            unidad=str(self.uo_ed_inicial.id),
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AccionCreateScopeTests(ScopeIntegrationBase):
    """E. POST /api/v2/sis-poa/acciones/ — el scope del destino se valida."""

    def crear_accion(self, usuario, unidad, codigo='ACP-S2-NEW'):
        return self.cliente(usuario).post(
            reverse('v2-acciones-poa-list'),
            {
                'poa': str(self.poa.id),
                'codigo': codigo,
                'nombre': 'Acción nueva',
                'unidad': str(unidad.id),
            },
            format='json',
        )

    def test_formulador_crea_accion_en_su_unidad_201(self):
        response = self.crear_accion(self.formulador, self.uo_catastro)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_formulador_crear_accion_en_unidad_ajena_403(self):
        response = self.crear_accion(self.formulador, self.uo_ed_inicial)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class JerarquiaScopeTests(ScopeIntegrationBase):
    """F. Objetos sin UO propia resuelven el scope por la jerarquía padre."""

    def test_director_get_tarea_de_su_rama_200(self):
        response = self.cliente(self.director).get(
            reverse('v2-tareas-detail', kwargs={'pk': self.tarea_catastro.pk}),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_formulador_get_tarea_de_su_rama_200(self):
        response = self.cliente(self.formulador).get(
            reverse('v2-tareas-detail', kwargs={'pk': self.tarea_catastro.pk}),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_director_get_tarea_de_otra_rama_404(self):
        response = self.cliente(self.director).get(
            reverse('v2-tareas-detail', kwargs={'pk': self.tarea_educacion.pk}),
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_operacion_sin_unidad_hereda_scope_de_su_accion(self):
        """Operacion.unidad es nullable: cae a `accion.unidad` (decisión F2a)."""
        response = self.cliente(self.director).get(
            reverse(
                'v2-operaciones-detail',
                kwargs={'pk': self.operacion_catastro.pk},
            ),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_operacion_sin_unidad_de_accion_ajena_404(self):
        response = self.cliente(self.director).get(
            reverse(
                'v2-operaciones-detail',
                kwargs={'pk': self.operacion_educacion.pk},
            ),
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_actividad_de_rama_ajena_404(self):
        response = self.cliente(self.director).get(
            reverse(
                'v2-actividades-detail',
                kwargs={'pk': self.actividad_educacion.pk},
            ),
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_programacion_list_filtra_por_jerarquia(self):
        response = self.cliente(self.director).get(
            reverse('v2-programaciones-list'),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.ids_de(response), {str(self.programacion_catastro.id)},
        )


class PoAScopeTests(ScopeIntegrationBase):
    """PoAInstitucional: list por EXISTS de acciones; retrieve exige ALL.

    La capacidad del contenedor (`sis_poa.poa.view`) es distinta de la del
    POAU (`sis_poa.poau.view`): el seed F1 no la otorga a FORMULADOR_POAU,
    que opera acciones/operaciones pero no el PoA consolidado.
    """

    def test_director_ve_en_lista_poa_con_accion_en_su_alcance(self):
        response = self.cliente(self.director).get(reverse('v2-poas-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.ids_de(response), {str(self.poa.id)})

    def test_poa_mixto_detail_requiere_todas_las_acciones_en_alcance(self):
        """Asimetría heredada de F2a: el list usa EXISTS, el objeto ALL."""
        response = self.cliente(self.director).get(
            reverse('v2-poas-detail', kwargs={'pk': self.poa.pk}),
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_formulador_sin_capacidad_poa_view_recibe_403_en_list(self):
        response = self.cliente(self.formulador).get(reverse('v2-poas-list'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_superadmin_poa_detail_200(self):
        response = self.cliente(self.super_admin).get(
            reverse('v2-poas-detail', kwargs={'pk': self.poa.pk}),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_usuario_sin_alcances_list_poas_403(self):
        response = self.cliente(self.sin_alcance).get(reverse('v2-poas-list'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class V2FiscalIsolationTests(ScopeIntegrationBase):
    """V2 records are isolated by the real year of their owning POA."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.gestion_2025 = GestionFiscal.objects.create(
            anio=2025, estado=GestionFiscal.Estado.CERRADA,
        )
        cls.uo_catastro_2025 = UnidadOrganizacional.objects.create(
            codigo=cls.uo_catastro.codigo,
            nombre=cls.uo_catastro.nombre,
            tipo=cls.uo_catastro.tipo,
            gestion=cls.gestion_2025,
            fecha_vigencia_desde=date(2025, 1, 1),
        )
        for user, role, scope_type in (
            (cls.formulador, cls.rol_formulador, AlcanceOrganizacional.SCOPE_SELF),
            (cls.jefe_poa, cls.rol_jefe_poa, AlcanceOrganizacional.SCOPE_GLOBAL),
        ):
            AlcanceOrganizacional.objects.create(
                usuario=user,
                rol=role,
                unidad=cls.uo_catastro_2025,
                scope_type=scope_type,
                fiscal_year=cls.gestion_2025,
            )

        cls.poa_2025 = PoAInstitucional.objects.create(
            gestion=2025, codigo='POA-S2-2025', nombre='POA test 2025',
        )
        cls.accion_2025 = AccionCortoPlazo.objects.create(
            poa=cls.poa_2025,
            codigo='ACP-S2-CAT',
            nombre='Acción Catastro 2025',
            unidad=cls.uo_catastro_2025,
        )
        cls.operacion_2025 = Operacion.objects.create(
            accion=cls.accion_2025,
            codigo='OP-S2-CAT',
            nombre='Operación Catastro 2025',
        )
        cls.actividad_2025 = Actividad.objects.create(
            operacion=cls.operacion_2025,
            codigo='ACT-S2-CAT',
            nombre='Actividad Catastro 2025',
        )
        cls.tarea_2025 = Tarea.objects.create(
            actividad=cls.actividad_2025,
            codigo='TAR-S2-CAT',
            nombre='Tarea Catastro 2025',
        )
        cls.programacion_2025 = ProgramacionActividad.objects.create(
            actividad=cls.actividad_2025,
            anio=2025,
            tipo=ProgramacionActividad.TIPO_FISICA,
        )

    def raw_client(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def test_missing_invalid_and_unknown_gestion_fail_before_superuser_bypass(self):
        client = self.raw_client(self.super_admin)
        url = reverse('v2-acciones-poa-list')

        for params in ({}, {'gestion_id': 'invalid'}, {'gestion_id': str(uuid.uuid4())}):
            with self.subTest(params=params):
                response = client.get(url, params)
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_lists_filter_every_resource_by_owning_poa_year(self):
        cases = (
            ('v2-poas-list', {self.poa.pk}, {self.poa_2025.pk}),
            (
                'v2-acciones-poa-list',
                {self.accion_catastro.pk, self.accion_educacion.pk},
                {self.accion_2025.pk},
            ),
            (
                'v2-operaciones-list',
                {self.operacion_catastro.pk, self.operacion_educacion.pk},
                {self.operacion_2025.pk},
            ),
            (
                'v2-actividades-list',
                {self.actividad_catastro.pk, self.actividad_educacion.pk},
                {self.actividad_2025.pk},
            ),
            (
                'v2-tareas-list',
                {self.tarea_catastro.pk, self.tarea_educacion.pk},
                {self.tarea_2025.pk},
            ),
            (
                'v2-programaciones-list',
                {self.programacion_catastro.pk},
                {self.programacion_2025.pk},
            ),
        )
        for route, current, previous in cases:
            with self.subTest(route=route, year=2026):
                response = self.cliente(self.jefe_poa).get(reverse(route))
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(self.ids_de(response), {str(pk) for pk in current})
            with self.subTest(route=route, year=2025):
                response = self.cliente(
                    self.jefe_poa, self.gestion_2025,
                ).get(reverse(route))
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(self.ids_de(response), {str(pk) for pk in previous})

    def test_retrieve_and_poa_actions_hide_records_owned_by_another_year(self):
        detail = reverse('v2-acciones-poa-detail', kwargs={'pk': self.accion_2025.pk})
        self.assertEqual(
            self.cliente(self.jefe_poa).get(detail).status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            self.cliente(self.jefe_poa, self.gestion_2025).get(detail).status_code,
            status.HTTP_200_OK,
        )

        for action_name in (
            'v2-poas-acciones',
            'v2-poas-resumen-presupuesto',
            'v2-poas-validar-techo',
            'v2-poas-programaciones',
        ):
            url = reverse(action_name, kwargs={'pk': self.poa_2025.pk})
            with self.subTest(action=action_name, year=2026):
                self.assertEqual(
                    self.cliente(self.jefe_poa).get(url).status_code,
                    status.HTTP_404_NOT_FOUND,
                )
            with self.subTest(action=action_name, year=2025):
                self.assertEqual(
                    self.cliente(self.jefe_poa, self.gestion_2025).get(url).status_code,
                    status.HTTP_200_OK,
                )


class V1ScopeHardeningTests(ScopeIntegrationBase):
    """V1 must enforce atomic capabilities, UO scope, and fiscal year."""
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        GestionFiscal.objects.exclude(pk=cls.gestion.pk).update(activa=False)
        cls.gestion.estado = GestionFiscal.Estado.ABIERTA
        cls.gestion.activa = True
        cls.gestion.save(update_fields=['estado', 'activa'])
        cls.gestion_2025 = GestionFiscal.objects.create(anio=2025, estado='cerrada')
        def poau(unidad, codigo):
            return POAU.objects.create(
                unidad=unidad, gestion=2026, codigo=codigo, nombre=codigo,
            )
        cls.poau_catastro = poau(cls.uo_catastro, 'POAU-V1-CAT')
        cls.poau_educacion = poau(cls.uo_ed_inicial, 'POAU-V1-EDU')
        cls.act_catastro = POAUActividad.objects.create(
            poau=cls.poau_catastro, codigo='V1-ACT-CAT', nombre='Catastro',
        )
        cls.act_educacion = POAUActividad.objects.create(
            poau=cls.poau_educacion, codigo='V1-ACT-EDU', nombre='Educación',
        )
        def execution(model, actividad):
            return model.objects.create(
                actividad=actividad, periodo='2026-Q1', tipo_periodo='trimestral',
            )
        cls.fisica_catastro = execution(EjecucionFisica, cls.act_catastro)
        cls.fisica_educacion = execution(EjecucionFisica, cls.act_educacion)
        cls.financiera_catastro = execution(EjecucionFinanciera, cls.act_catastro)
        cls.financiera_educacion = execution(EjecucionFinanciera, cls.act_educacion)

    def v1_url(self, resource, suffix=''):
        return f'/api/v1/poau/{resource}/{suffix}'

    def gestion_params(self, gestion=None):
        return {'gestion_id': str((gestion or self.gestion).pk)}

    def test_list_filters_uo_and_returns_empty_without_scope_or_year(self):
        response = self.cliente(self.formulador).get(
            self.v1_url('poaus'), self.gestion_params(),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.ids_de(response), {str(self.poau_catastro.pk)})
        no_scope = self.cliente(self.sin_alcance).get(
            self.v1_url('poaus'), self.gestion_params(),
        )
        self.assertEqual(no_scope.status_code, status.HTTP_200_OK)
        self.assertEqual(self.ids_de(no_scope), set())
        other_year = self.cliente(self.formulador).get(
            self.v1_url('poaus'), self.gestion_params(self.gestion_2025),
        )
        self.assertEqual(other_year.status_code, status.HTTP_200_OK)
        self.assertEqual(self.ids_de(other_year), set())

    def test_out_of_scope_retrieve_update_and_delete_are_hidden(self):
        detail = self.v1_url('poaus', f'{self.poau_educacion.pk}/')
        client = self.cliente(self.formulador)
        self.assertEqual(client.get(detail).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            client.patch(detail, {'nombre': 'No permitido'}, format='json').status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(client.delete(detail).status_code, status.HTTP_404_NOT_FOUND)

    def test_create_update_reparent_and_delete_validate_destination_scope(self):
        client = self.cliente(self.formulador)
        create_url = self.v1_url('poaus')
        allowed = client.post(create_url, {
            'unidad': str(self.uo_catastro.pk), 'gestion': 2026,
            'codigo': 'POAU-V1-NEW', 'nombre': 'Permitido',
        }, format='json')
        self.assertEqual(allowed.status_code, status.HTTP_201_CREATED)
        denied = client.post(create_url, {
            'unidad': str(self.uo_ed_inicial.pk), 'gestion': 2026,
            'codigo': 'POAU-V1-DENIED', 'nombre': 'Denegado',
        }, format='json')
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)
        detail = self.v1_url('poaus', f'{self.poau_catastro.pk}/')
        moved = client.patch(
            detail, {'unidad': str(self.uo_ed_inicial.pk)}, format='json',
        )
        self.assertEqual(moved.status_code, status.HTTP_403_FORBIDDEN)
        activity_detail = self.v1_url('actividades', f'{self.act_catastro.pk}/')
        reparented = client.patch(
            activity_detail, {'poau': self.poau_educacion.pk}, format='json',
        )
        self.assertEqual(reparented.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(client.delete(detail).status_code, status.HTTP_204_NO_CONTENT)

    def test_client_supplied_unidad_never_widens_por_unidad(self):
        client = self.cliente(self.formulador)
        url = self.v1_url('poaus', 'por_unidad/')
        own = client.get(url, {'unidad_id': str(self.uo_catastro.pk)})
        self.assertEqual(self.ids_de(own), {str(self.poau_catastro.pk)})
        foreign = client.get(url, {'unidad_id': str(self.uo_ed_inicial.pk)})
        self.assertEqual(foreign.status_code, status.HTTP_200_OK)
        self.assertEqual(self.ids_de(foreign), set())
    def test_workflow_actions_require_exact_capability_and_object_scope(self):
        client = self.cliente(self.formulador)
        enviar = self.v1_url('poaus', f'{self.poau_catastro.pk}/enviar/')
        self.assertEqual(client.post(enviar).status_code, status.HTTP_200_OK)
        self.poau_catastro.estado = 'borrador'
        self.poau_catastro.save(update_fields=['estado'])
        self.rol_formulador.capacidades.remove(
            Capacidad.objects.get(codigo=CAP_POAU_SUBMIT),
        )
        self.assertEqual(client.post(enviar).status_code, status.HTTP_403_FORBIDDEN)
        self.poau_educacion.estado = 'enviado'
        self.poau_educacion.save(update_fields=['estado'])
        aprobar_ajeno = self.v1_url(
            'poaus', f'{self.poau_educacion.pk}/aprobar/',
        )
        self.assertEqual(
            self.cliente(self.director).post(aprobar_ajeno).status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.poau_catastro.estado = 'enviado'
        self.poau_catastro.save(update_fields=['estado'])
        aprobar = self.v1_url('poaus', f'{self.poau_catastro.pk}/aprobar/')
        self.rol_director.capacidades.remove(
            Capacidad.objects.get(codigo=CAP_POAU_APPROVE),
        )
        self.assertEqual(
            self.cliente(self.director).post(aprobar).status_code,
            status.HTTP_403_FORBIDDEN,
        )
        rechazar = self.v1_url('poaus', f'{self.poau_catastro.pk}/rechazar/')
        self.rol_director.capacidades.remove(
            Capacidad.objects.get(codigo=CAP_POAU_REVIEW),
        )
        self.assertEqual(
            self.cliente(self.director).post(
                rechazar, {'observaciones': 'No'}, format='json',
            ).status_code,
            status.HTTP_403_FORBIDDEN,
        )
    def test_children_and_executions_hide_cross_uo_records(self):
        client = self.cliente(self.formulador)
        cases = [
            ('actividades', self.act_catastro),
            ('ejecucion-fisica', self.fisica_catastro),
            ('ejecucion-financiera', self.financiera_catastro),
        ]
        for resource, own in cases:
            with self.subTest(resource=resource):
                listed = client.get(
                    self.v1_url(resource), self.gestion_params(),
                )
                self.assertEqual(listed.status_code, status.HTTP_200_OK)
                self.assertEqual(self.ids_de(listed), {str(own.pk)})
    def test_v2_gestion_id_reaches_queryset_scope_resolution(self):
        with patch.object(
            __import__(
                'apps.accounts.services_scope', fromlist=['ScopeResolver'],
            ).ScopeResolver,
            'unidades_efectivas', return_value={self.uo_catastro.pk},
        ) as resolver:
            response = self.cliente(self.formulador).get(
                reverse('v2-acciones-poa-list'), self.gestion_params(),
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        gestion_args = {
            call.args[1] if len(call.args) > 1 else None
            for call in resolver.call_args_list
        }
        self.assertEqual(gestion_args, {self.gestion.pk})
