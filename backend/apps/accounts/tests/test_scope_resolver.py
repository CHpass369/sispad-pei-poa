"""Tests de F2a: ScopeResolver + CapacidadConScope (ADR-003).

Sin `__init__.py` en este directorio a propósito: `apps/accounts/tests.py`
ya existe como módulo y un paquete `tests/` lo sombrearía en la colección
de pytest.

Jerarquía de UOs compartida (setUpTestData, read-only en los tests)::

    GAMS (root)
    └── Secretaría Municipal
        ├── Dirección de Catastro
        │   ├── Unidad de Catastro
        │   └── Unidad de Topografía
        └── Dirección de Educación
            └── Unidad de Educación Inicial
"""
from datetime import date
from types import SimpleNamespace

from django.test import TestCase
from rest_framework.test import APIRequestFactory

from apps.accounts.models import (
    AlcanceOrganizacional, Capacidad, Rol, Usuario,
)
from apps.accounts.permissions import CapacidadConScope
from apps.accounts.services_scope import GLOBAL_SCOPE, ScopeResolver
from apps.gestion.models import GestionFiscal
from apps.organizacion.models import TipoUnidad, UnidadOrganizacional
from apps.poau.models_v2 import (
    AccionCortoPlazo, Actividad, Operacion, PoAInstitucional, Tarea,
)

CAPACIDAD_TEST = 'test.scope.f2a'


class ScopeTestBase(TestCase):
    """Jerarquía de UOs, capacidad/roles y helpers compartidos (F2a)."""

    @classmethod
    def setUpTestData(cls):
        cls.gestion, _ = GestionFiscal.objects.get_or_create(
            anio=2026, defaults={'estado': 'preparacion'},
        )
        cls.gestion_2025, _ = GestionFiscal.objects.get_or_create(
            anio=2025, defaults={'estado': 'cerrada'},
        )
        tipo, _ = TipoUnidad.objects.get_or_create(
            codigo='TEST-F2A', defaults={'nombre': 'Tipo test F2a', 'nivel': 1},
        )
        vig = date(2026, 1, 1)

        def uo(codigo, nombre, padre):
            return UnidadOrganizacional.objects.create(
                codigo=codigo, nombre=nombre, tipo=tipo, padre=padre,
                gestion=cls.gestion, fecha_vigencia_desde=vig,
            )

        cls.gams = uo('T-GAMS', 'Gobierno Autónomo Municipal de Sacaba', None)
        cls.secretaria = uo('T-SEC', 'Secretaría Municipal', cls.gams)
        cls.dir_catastro = uo(
            'T-DCAT', 'Dirección de Catastro', cls.secretaria,
        )
        cls.uo_catastro = uo('T-UCAT', 'Unidad de Catastro', cls.dir_catastro)
        cls.uo_topografia = uo(
            'T-UTOP', 'Unidad de Topografía', cls.dir_catastro,
        )
        cls.dir_educacion = uo(
            'T-DEDU', 'Dirección de Educación', cls.secretaria,
        )
        cls.uo_ed_inicial = uo(
            'T-UEI', 'Unidad de Educación Inicial', cls.dir_educacion,
        )

        cls.capacidad, _ = Capacidad.objects.get_or_create(
            codigo=CAPACIDAD_TEST,
            defaults={'nombre': 'Capacidad test F2a', 'sistema': 'test'},
        )
        cls.rol, _ = Rol.objects.get_or_create(
            codigo='TEST-F2A-A', defaults={'nombre': 'Rol test F2a A'},
        )
        cls.rol.capacidades.add(cls.capacidad)
        cls.rol_b, _ = Rol.objects.get_or_create(
            codigo='TEST-F2A-B', defaults={'nombre': 'Rol test F2a B'},
        )

    def crear_usuario(self, email, **kwargs):
        kwargs.setdefault('activo', True)
        return Usuario.objects.create_user(
            email=email, password='test-2026', **kwargs,
        )

    def crear_alcance(self, usuario, unidad, **kwargs):
        kwargs.setdefault('fiscal_year', unidad.gestion)
        return AlcanceOrganizacional.objects.create(
            usuario=usuario, unidad=unidad, **kwargs,
        )


class AlcancesYUnidadesEfectivasTests(ScopeTestBase):
    """A. ScopeResolver.alcances_vigentes + unidades_efectivas."""

    def test_usuario_sin_alcances_retorna_set_vacio(self):
        u = self.crear_usuario('sin-alcances@test.gob.bo')
        self.assertEqual(list(ScopeResolver.alcances_vigentes(u)), [])
        self.assertEqual(ScopeResolver.unidades_efectivas(u), set())

    def test_scope_self_solo_la_unidad(self):
        u = self.crear_usuario('self@test.gob.bo')
        self.crear_alcance(u, self.uo_catastro)
        self.assertEqual(
            ScopeResolver.unidades_efectivas(u), {self.uo_catastro.id},
        )

    def test_scope_descendants_incluye_toda_la_rama(self):
        u = self.crear_usuario('desc@test.gob.bo')
        self.crear_alcance(
            u, self.dir_catastro,
            scope_type=AlcanceOrganizacional.SCOPE_DESCENDANTS,
        )
        self.assertEqual(
            ScopeResolver.unidades_efectivas(u),
            {self.dir_catastro.id, self.uo_catastro.id, self.uo_topografia.id},
        )

    def test_scope_global_retorna_sentinel(self):
        u = self.crear_usuario('global@test.gob.bo')
        self.crear_alcance(
            u, self.gams, scope_type=AlcanceOrganizacional.SCOPE_GLOBAL,
        )
        self.assertEqual(ScopeResolver.unidades_efectivas(u), {GLOBAL_SCOPE})

    def test_multiples_alcances_se_unen(self):
        u = self.crear_usuario('multi@test.gob.bo')
        self.crear_alcance(u, self.uo_catastro)
        self.crear_alcance(u, self.uo_ed_inicial)
        self.assertEqual(ScopeResolver.alcances_vigentes(u).count(), 2)
        self.assertEqual(
            ScopeResolver.unidades_efectivas(u),
            {self.uo_catastro.id, self.uo_ed_inicial.id},
        )

    def test_alcance_inactivo_se_ignora(self):
        u = self.crear_usuario('inactivo-alc@test.gob.bo')
        self.crear_alcance(u, self.uo_catastro, activo=False)
        self.assertEqual(ScopeResolver.unidades_efectivas(u), set())

    def test_filtro_por_gestion_excluye_otras_gestiones(self):
        u = self.crear_usuario('gestion@test.gob.bo')
        self.crear_alcance(u, self.uo_catastro, fiscal_year=self.gestion_2025)
        # Sin filtro: el alcance aplica.
        self.assertEqual(
            ScopeResolver.unidades_efectivas(u), {self.uo_catastro.id},
        )
        # Con filtro de otra gestión: no aplica.
        self.assertEqual(
            ScopeResolver.unidades_efectivas(u, gestion_id=self.gestion.id),
            set(),
        )
        # Con la gestión del alcance: aplica.
        self.assertEqual(
            ScopeResolver.unidades_efectivas(
                u, gestion_id=self.gestion_2025.id,
            ),
            {self.uo_catastro.id},
        )

    def test_alcance_sis_pe_sin_gestion_permanece_resoluble(self):
        u = self.crear_usuario('sis-pe-sin-gestion@test.gob.bo')
        capacidad_pe = Capacidad.objects.create(
            codigo='sis_pe.test.yearless',
            nombre='Capacidad SIS-PE sin gestión',
            sistema='sis_pe',
        )
        rol_pe = Rol.objects.create(
            codigo='TEST-F2A-PE-YEARLESS',
            nombre='Rol SIS-PE sin gestión',
        )
        rol_pe.capacidades.add(capacidad_pe)
        alcance = self.crear_alcance(
            u, self.uo_catastro, rol=rol_pe, fiscal_year=None,
        )

        alcance.refresh_from_db()
        self.assertIsNone(alcance.fiscal_year_id)
        self.assertEqual(
            ScopeResolver.alcances_vigentes(u).get(pk=alcance.pk), alcance,
        )
        self.assertEqual(
            ScopeResolver.unidades_efectivas(u), {self.uo_catastro.id},
        )

    def test_multi_rol_une_alcances(self):
        u = self.crear_usuario('multirol@test.gob.bo')
        u.roles.add(self.rol, self.rol_b)
        self.crear_alcance(u, self.uo_catastro, rol=self.rol)
        self.crear_alcance(u, self.uo_topografia, rol=self.rol_b)
        self.assertEqual(
            ScopeResolver.unidades_efectivas(u),
            {self.uo_catastro.id, self.uo_topografia.id},
        )


class PuedeOperarTests(ScopeTestBase):
    """B. ScopeResolver.puede_operar."""

    def test_sin_alcance_no_puede_operar(self):
        u = self.crear_usuario('po-sin@test.gob.bo')
        self.assertFalse(ScopeResolver.puede_operar(u, self.uo_catastro.id))

    def test_self_permite_la_misma_unidad(self):
        u = self.crear_usuario('po-self@test.gob.bo')
        self.crear_alcance(u, self.uo_catastro)
        self.assertTrue(ScopeResolver.puede_operar(u, self.uo_catastro.id))

    def test_self_no_permite_descendiente(self):
        u = self.crear_usuario('po-self-hijo@test.gob.bo')
        self.crear_alcance(u, self.dir_catastro)
        self.assertFalse(ScopeResolver.puede_operar(u, self.uo_catastro.id))

    def test_descendants_permite_hijos_y_nietos_no_ancestros(self):
        u = self.crear_usuario('po-desc@test.gob.bo')
        self.crear_alcance(
            u, self.secretaria,
            scope_type=AlcanceOrganizacional.SCOPE_DESCENDANTS,
        )
        self.assertTrue(ScopeResolver.puede_operar(u, self.dir_catastro.id))
        self.assertTrue(ScopeResolver.puede_operar(u, self.uo_catastro.id))
        self.assertTrue(ScopeResolver.puede_operar(u, self.uo_ed_inicial.id))
        # Fuera de la rama (el ancestro) no.
        self.assertFalse(ScopeResolver.puede_operar(u, self.gams.id))

    def test_global_puede_operar_en_cualquier_unidad(self):
        u = self.crear_usuario('po-global@test.gob.bo')
        self.crear_alcance(
            u, self.gams, scope_type=AlcanceOrganizacional.SCOPE_GLOBAL,
        )
        for unidad in (
            self.gams, self.secretaria, self.uo_topografia, self.uo_ed_inicial,
        ):
            self.assertTrue(ScopeResolver.puede_operar(u, unidad.id))

    def test_usuario_inactivo_no_puede_operar(self):
        u = self.crear_usuario('po-inactivo@test.gob.bo', activo=False)
        self.crear_alcance(
            u, self.gams, scope_type=AlcanceOrganizacional.SCOPE_GLOBAL,
        )
        self.assertFalse(ScopeResolver.puede_operar(u, self.gams.id))

    def test_unidad_id_como_string_se_normaliza(self):
        """Los kwargs de URL llegan como str (relevante para F2b)."""
        u = self.crear_usuario('po-str@test.gob.bo')
        self.crear_alcance(u, self.uo_catastro)
        self.assertTrue(ScopeResolver.puede_operar(u, str(self.uo_catastro.id)))


class CapacidadConScopeTests(ScopeTestBase):
    """C. Permission DRF CapacidadConScope."""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.permiso = CapacidadConScope(CAPACIDAD_TEST)

    def _request(self, usuario, data=None):
        request = self.factory.get('/fake/', data or {})
        request.user = usuario
        return request

    @staticmethod
    def _view(kwargs=None):
        return SimpleNamespace(kwargs=kwargs or {})

    def _usuario_con_capacidad(self, email):
        u = self.crear_usuario(email)
        u.roles.add(self.rol)
        return u

    def _cadena(self, unidad):
        """PoA → AccionCortoPlazo(unidad) → Operacion → Actividad → Tarea."""
        poa = PoAInstitucional.objects.create(
            gestion=2026, codigo=f'POA-T-{unidad.codigo}',
            nombre='POA test F2a',
        )
        accion = AccionCortoPlazo.objects.create(
            poa=poa, codigo='ACP-1', nombre='Acción test', unidad=unidad,
        )
        operacion = Operacion.objects.create(
            accion=accion, codigo='OP-1', nombre='Operación test',
        )
        actividad = Actividad.objects.create(
            operacion=operacion, codigo='ACT-1', nombre='Actividad test',
        )
        tarea = Tarea.objects.create(
            actividad=actividad, codigo='TAR-1', nombre='Tarea test',
        )
        return poa, accion, operacion, actividad, tarea

    def _puede_sobre(self, usuario, obj, permiso=None):
        permiso = permiso or self.permiso
        return permiso.has_object_permission(
            self._request(usuario), self._view(), obj,
        )

    # --- has_permission ---

    def test_has_permission_sin_capacidad_deniega(self):
        u = self.crear_usuario('hp-sincap@test.gob.bo')  # sin rol asignado
        self.crear_alcance(
            u, self.gams, scope_type=AlcanceOrganizacional.SCOPE_GLOBAL,
        )
        self.assertFalse(
            self.permiso.has_permission(self._request(u), self._view()),
        )

    def test_has_permission_con_capacidad_sin_alcances_deniega(self):
        u = self._usuario_con_capacidad('hp-sinalc@test.gob.bo')
        self.assertFalse(
            self.permiso.has_permission(self._request(u), self._view()),
        )

    def test_has_permission_con_capacidad_y_global_permite(self):
        u = self._usuario_con_capacidad('hp-global@test.gob.bo')
        self.crear_alcance(
            u, self.gams, scope_type=AlcanceOrganizacional.SCOPE_GLOBAL,
        )
        self.assertTrue(
            self.permiso.has_permission(self._request(u), self._view()),
        )

    def test_gestion_id_param_filtra_por_kwarg_de_url(self):
        u = self._usuario_con_capacidad('gp-kwarg@test.gob.bo')
        self.crear_alcance(u, self.uo_catastro, fiscal_year=self.gestion_2025)
        permiso = CapacidadConScope(CAPACIDAD_TEST, gestion_id_param='gestion_id')
        request = self._request(u)
        # Gestión 2026 en kwarg: el alcance de 2025 no aplica.
        view = self._view({'gestion_id': str(self.gestion.id)})
        self.assertFalse(permiso.has_permission(request, view))
        # Gestión 2025 en kwarg: aplica.
        view = self._view({'gestion_id': str(self.gestion_2025.id)})
        self.assertTrue(permiso.has_permission(request, view))

    def test_gestion_id_param_por_query_params(self):
        u = self._usuario_con_capacidad('gp-query@test.gob.bo')
        self.crear_alcance(u, self.uo_catastro, fiscal_year=self.gestion_2025)
        permiso = CapacidadConScope(CAPACIDAD_TEST, gestion_id_param='gestion_id')
        request = self._request(u, {'gestion_id': str(self.gestion_2025.id)})
        self.assertTrue(permiso.has_permission(request, self._view()))

    # --- has_object_permission ---

    def test_objeto_en_unidad_propia_permite(self):
        u = self._usuario_con_capacidad('op-self-ok@test.gob.bo')
        self.crear_alcance(u, self.uo_catastro)
        _, accion, *_ = self._cadena(self.uo_catastro)
        self.assertTrue(self._puede_sobre(u, accion))

    def test_objeto_en_unidad_ajena_deniega(self):
        u = self._usuario_con_capacidad('op-self-no@test.gob.bo')
        self.crear_alcance(u, self.uo_catastro)
        _, accion, *_ = self._cadena(self.uo_ed_inicial)
        self.assertFalse(self._puede_sobre(u, accion))

    def test_objeto_en_unidad_descendiente_permite(self):
        u = self._usuario_con_capacidad('op-desc-ok@test.gob.bo')
        self.crear_alcance(
            u, self.dir_catastro,
            scope_type=AlcanceOrganizacional.SCOPE_DESCENDANTS,
        )
        _, accion, *_ = self._cadena(self.uo_topografia)
        self.assertTrue(self._puede_sobre(u, accion))

    def test_tarea_dentro_de_scope_permite_por_jerarquia(self):
        """Tarea → Actividad → Operacion → AccionCortoPlazo → unidad."""
        u = self._usuario_con_capacidad('op-tarea-ok@test.gob.bo')
        self.crear_alcance(u, self.uo_catastro)
        *_, tarea = self._cadena(self.uo_catastro)
        self.assertTrue(self._puede_sobre(u, tarea))

    def test_tarea_fuera_de_scope_deniega_por_jerarquia(self):
        u = self._usuario_con_capacidad('op-tarea-no@test.gob.bo')
        self.crear_alcance(u, self.uo_ed_inicial)  # scope en otra rama
        *_, tarea = self._cadena(self.uo_catastro)
        self.assertFalse(self._puede_sobre(u, tarea))

    def test_poa_con_todas_las_acciones_en_scope_permite(self):
        u = self._usuario_con_capacidad('poa-ok@test.gob.bo')
        self.crear_alcance(
            u, self.dir_catastro,
            scope_type=AlcanceOrganizacional.SCOPE_DESCENDANTS,
        )
        poa, *_ = self._cadena(self.uo_catastro)
        AccionCortoPlazo.objects.create(
            poa=poa, codigo='ACP-2', nombre='Acción 2',
            unidad=self.uo_topografia,
        )
        self.assertTrue(self._puede_sobre(u, poa))

    def test_poa_con_alguna_accion_fuera_de_scope_deniega(self):
        u = self._usuario_con_capacidad('poa-no@test.gob.bo')
        self.crear_alcance(u, self.uo_catastro)
        poa, *_ = self._cadena(self.uo_catastro)
        AccionCortoPlazo.objects.create(
            poa=poa, codigo='ACP-2', nombre='Acción 2',
            unidad=self.uo_ed_inicial,
        )
        self.assertFalse(self._puede_sobre(u, poa))

    def test_poa_sin_acciones_permite(self):
        """Convención F2a: PoA sin acciones no restringe a nivel de objeto."""
        u = self._usuario_con_capacidad('poa-vacio@test.gob.bo')
        self.crear_alcance(u, self.uo_catastro)
        poa = PoAInstitucional.objects.create(
            gestion=2026, codigo='POA-T-VACIO', nombre='POA sin acciones',
        )
        self.assertTrue(self._puede_sobre(u, poa))
