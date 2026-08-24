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

CAP_POAU_VIEW = 'sis_poa.poau.view'
CAP_POAU_EDIT = 'sis_poa.poau.edit'
CAP_POA_VIEW = 'sis_poa.poa.view'
CAP_POA_EDIT = 'sis_poa.poa.edit'
CAPS_SIS_POA = [CAP_POAU_VIEW, CAP_POAU_EDIT, CAP_POA_VIEW, CAP_POA_EDIT]


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
            'FORMULADOR_POAU', [CAP_POAU_VIEW, CAP_POAU_EDIT],
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

    def cliente(self, usuario):
        client = APIClient()
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
