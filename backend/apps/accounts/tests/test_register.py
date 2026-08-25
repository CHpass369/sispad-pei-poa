"""Tests de F3a: registro público + aprobación administrativa (spec #17/#18).

Sin `__init__.py` en este directorio a propósito (convención F2a:
`apps/accounts/tests.py` ya existe como módulo y un paquete `tests/` lo
sombrearía en la colección de pytest).

Jerarquía de UOs compartida (setUpTestData, read-only en los tests)::

    GAMS (root)
    └── Secretaría Municipal
        └── Dirección de Catastro

Roles sembrados acá (get_or_create, patrón de test_scope_integration):

- FORMULADOR_POAU / DIRECTOR: capacidades sis_poa.* (aprobaciables SIS-POA).
- JEFE_POA: sis_poa.* + accounts.solicitud.view/approve.
- JEFE_PE: sis_pe.* + accounts.solicitud.view/approve.
- SUPER_ADMIN: capacidades de ambos sistemas.

Las capacidades de solicitud se asignan explícitamente para verificar que las
restricciones cruzadas son del backend y no falsos positivos por falta del
permiso general.
"""
from datetime import date

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.throttling import SimpleRateThrottle

from apps.accounts.models import (
    AlcanceOrganizacional, Capacidad, Rol, Usuario,
)
from apps.gestion.models import GestionFiscal
from apps.organizacion.models import TipoUnidad, UnidadOrganizacional

PASSWORD = 'Clave-Registro.Segura.2026'


class UsuarioEstadoTests(TestCase):
    """Compatibilidad bidireccional entre estado y el booleano legacy."""

    def test_estado_por_defecto_es_activo(self):
        usuario = Usuario.objects.create_user(
            email='f3a-estado-default@test.gob.bo', password=PASSWORD,
        )
        self.assertEqual(usuario.estado, Usuario.ESTADO_ACTIVO)
        self.assertTrue(usuario.activo)

    def test_alta_legacy_inactiva_sincroniza_estado(self):
        usuario = Usuario.objects.create_user(
            email='f3a-estado-legacy@test.gob.bo',
            password=PASSWORD,
            activo=False,
        )
        self.assertEqual(usuario.estado, Usuario.ESTADO_INACTIVO)
        self.assertFalse(usuario.activo)

    def test_alta_pendiente_activo_false_es_valida(self):
        usuario = Usuario.objects.create_user(
            email='f3a-estado-pendiente@test.gob.bo',
            password=PASSWORD,
            estado=Usuario.ESTADO_PENDIENTE,
            activo=False,
        )
        self.assertEqual(usuario.estado, Usuario.ESTADO_PENDIENTE)
        self.assertFalse(usuario.activo)

    def test_transiciones_sincronizan_ambos_campos(self):
        usuario = Usuario.objects.create_user(
            email='f3a-estado-transicion@test.gob.bo', password=PASSWORD,
        )
        usuario.activo = False
        usuario.save(update_fields=['activo'])
        self.assertEqual(usuario.estado, Usuario.ESTADO_INACTIVO)

        usuario.estado = Usuario.ESTADO_ACTIVO
        usuario.save(update_fields=['estado'])
        self.assertTrue(usuario.activo)


class F3aTestBase(TestCase):
    """Jerarquía de UOs, capacidades/roles F1 y usuarios compartidos."""

    @classmethod
    def setUpTestData(cls):
        cls.gestion, _ = GestionFiscal.objects.get_or_create(
            anio=2026, defaults={'estado': 'preparacion'},
        )
        tipo, _ = TipoUnidad.objects.get_or_create(
            codigo='F3A-TIPO', defaults={'nombre': 'Tipo test F3a', 'nivel': 1},
        )
        vig = date(2026, 1, 1)

        def uo(codigo, nombre, padre):
            return UnidadOrganizacional.objects.create(
                codigo=codigo, nombre=nombre, tipo=tipo, padre=padre,
                gestion=cls.gestion, fecha_vigencia_desde=vig,
            )

        cls.gams = uo('F3A-GAMS', 'Gobierno Autónomo Municipal de Sacaba', None)
        cls.secretaria = uo('F3A-SEC', 'Secretaría Municipal', cls.gams)
        cls.dir_catastro = uo('F3A-DCAT', 'Dirección de Catastro', cls.secretaria)

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

        cls.rol_formulador = rol(
            'FORMULADOR_POAU', ['sis_poa.poau.view', 'sis_poa.poau.create'],
        )
        cls.rol_director = rol('DIRECTOR', ['sis_poa.poau.view'])
        cls.rol_jefe_poa = rol(
            'JEFE_POA',
            [
                'sis_poa.poau.view',
                'accounts.solicitud.view',
                'accounts.solicitud.approve',
            ],
        )
        cls.rol_jefe_pe = rol(
            'JEFE_PE',
            [
                'sis_pe.pad.view',
                'accounts.solicitud.view',
                'accounts.solicitud.approve',
            ],
        )
        cls.rol_super_admin = rol(
            'SUPER_ADMIN',
            [
                'sis_pe.pad.view',
                'sis_poa.poau.view',
                'accounts.solicitud.view',
                'accounts.solicitud.approve',
            ],
        )
        cls.rol_sin_solicitud = rol('F3A-SIN-SOLICITUD', ['sis_poa.poau.view'])
        cls.rol_solo_accounts = rol(
            'F3A-SOLO-ACCOUNTS', ['accounts.solicitud.view'],
        )

        def usuario(email, rol_asignado=None, **kwargs):
            u = Usuario.objects.create_user(
                email=email, password=PASSWORD, **kwargs,
            )
            if rol_asignado is not None:
                u.roles.add(rol_asignado)
            return u

        cls.super_admin = usuario(
            'f3a-superadmin@test.gob.bo', is_staff=True, is_superuser=True,
        )
        cls.jefe_poa = usuario('f3a-jefe-poa@test.gob.bo', cls.rol_jefe_poa)
        cls.jefe_pe = usuario('f3a-jefe-pe@test.gob.bo', cls.rol_jefe_pe)
        cls.sin_capacidad = usuario(
            'f3a-sin-capacidad@test.gob.bo', cls.rol_sin_solicitud,
        )

    def setUp(self):
        # El registro público usa LoginThrottle (5/min): sin limpiar el cache
        # compartido, los tests se bloquean entre sí por IP (127.0.0.1).
        SimpleRateThrottle.cache.clear()

    def cliente(self, usuario=None):
        client = APIClient()
        if usuario is not None:
            client.force_authenticate(user=usuario)
        return client

    def payload_registro(self, email, **overrides):
        payload = {
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'email': email,
            'cargo': 'Analista',
            'unidad_organizacional_id': str(self.dir_catastro.id),
            'password': PASSWORD,
            'password_confirm': PASSWORD,
        }
        payload.update(overrides)
        return payload

    def registrar(self, email, client=None, **overrides):
        client = client or self.cliente()
        return client.post(
            reverse('v2-auth-register'),
            self.payload_registro(email, **overrides),
            format='json',
        )

    def payload_aprobacion(self, **overrides):
        payload = {
            'unidad_organizacional_id': str(self.dir_catastro.id),
            'rol_codigo': 'FORMULADOR_POAU',
            'sistema': 'sis_poa',
            'scope_type': AlcanceOrganizacional.SCOPE_SELF,
            'fiscal_year_id': None,
        }
        payload.update(overrides)
        return payload

    def aprobar(self, admin, objetivo, **overrides):
        return self.cliente(admin).post(
            reverse('v2-admin-user-approve', kwargs={'pk': objetivo.pk}),
            self.payload_aprobacion(**overrides),
            format='json',
        )


class RegistroPublicoTests(F3aTestBase):
    """A. POST /api/v2/auth/register/."""

    def test_registro_valido_devuelve_201_y_mensaje_generico(self):
        response = self.registrar('f3a-nuevo@test.gob.bo')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('administrador', response.data['detail'])

    def test_registro_no_requiere_autenticacion(self):
        # Sin force_authenticate ni header Authorization.
        response = self.registrar('f3a-anon@test.gob.bo', client=APIClient())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_usuario_creado_queda_pendiente_sin_roles(self):
        self.registrar('f3a-pendiente@test.gob.bo')
        u = Usuario.objects.get(email='f3a-pendiente@test.gob.bo')
        self.assertEqual(u.estado, Usuario.ESTADO_PENDIENTE)
        self.assertFalse(u.activo)
        self.assertFalse(u.is_active)
        self.assertFalse(u.is_staff)
        self.assertFalse(u.is_superuser)
        self.assertEqual(u.roles.count(), 0)
        self.assertEqual(u.cargo, 'Analista')

    def test_registro_no_devuelve_token(self):
        response = self.registrar('f3a-sin-token@test.gob.bo')
        self.assertNotIn('access', response.data)
        self.assertNotIn('refresh', response.data)
        self.assertNotIn('token', response.data)

    def test_usuario_pendiente_no_puede_obtener_token(self):
        self.registrar('f3a-sin-login@test.gob.bo')
        response = self.cliente().post(
            reverse('login'),
            {'email': 'f3a-sin-login@test.gob.bo', 'password': PASSWORD},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn('access', response.data)

    def test_email_duplicado_devuelve_400(self):
        Usuario.objects.create_user(
            email='f3a-existente@test.gob.bo', password=PASSWORD,
        )
        response = self.registrar('f3a-existente@test.gob.bo')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_passwords_no_coinciden_devuelve_400(self):
        response = self.registrar(
            'f3a-mismatch@test.gob.bo', password_confirm='Otra.Clave.2026',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(
            Usuario.objects.filter(email='f3a-mismatch@test.gob.bo').exists(),
        )

    def test_unidad_inexistente_devuelve_400(self):
        response = self.registrar(
            'f3a-sinuo@test.gob.bo',
            unidad_organizacional_id='00000000-0000-0000-0000-000000000000',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unidad_inactiva_no_puede_solicitarse(self):
        self.dir_catastro.activo = False
        self.dir_catastro.save(update_fields=['activo'])
        response = self.registrar('f3a-uo-inactiva@test.gob.bo')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_usuario_autenticado_no_puede_registrarse(self):
        response = self.registrar(
            'f3a-autenticado@test.gob.bo', client=self.cliente(self.jefe_poa),
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(
            Usuario.objects.filter(email='f3a-autenticado@test.gob.bo').exists(),
        )

    def test_registro_guarda_trazo_de_unidad_solicitada(self):
        """La UO pedida queda como alcance-trazo inactivo (nunca vigente)."""
        self.registrar('f3a-trazo@test.gob.bo')
        u = Usuario.objects.get(email='f3a-trazo@test.gob.bo')
        alcance = u.alcances_organizacionales.get()
        self.assertIsNone(alcance.rol_id)
        self.assertFalse(alcance.activo)
        self.assertEqual(alcance.unidad_id, self.dir_catastro.id)


class UnidadesOrganizacionalesPublicasTests(F3aTestBase):
    """GET /api/v2/auth/organizational-units/."""

    def setUp(self):
        super().setUp()
        self.url = reverse('v2-auth-organizational-units')

    def test_listado_no_requiere_autenticacion(self):
        response = APIClient().get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('F3A-DCAT', [unidad['codigo'] for unidad in response.data])

    def test_listado_devuelve_solo_activas_y_vigentes(self):
        self.secretaria.activo = False
        self.secretaria.save(update_fields=['activo'])
        self.dir_catastro.fecha_vigencia_hasta = date(2026, 1, 31)
        self.dir_catastro.save(update_fields=['fecha_vigencia_hasta'])

        response = APIClient().get(self.url)
        codigos = [unidad['codigo'] for unidad in response.data]

        self.assertNotIn('F3A-SEC', codigos)
        self.assertNotIn('F3A-DCAT', codigos)
        self.assertIn('F3A-GAMS', codigos)

    def test_listado_expone_solo_campos_publicos_minimos(self):
        response = APIClient().get(self.url)
        unidad = next(
            item for item in response.data if item['codigo'] == 'F3A-DCAT'
        )
        self.assertEqual(
            set(unidad), {'id', 'codigo', 'nombre', 'sigla', 'padre'},
        )
        self.assertEqual(unidad['padre'], str(self.secretaria.id))

    def test_busqueda_filtra_por_codigo_nombre_o_sigla(self):
        self.dir_catastro.sigla = 'DCAT'
        self.dir_catastro.save(update_fields=['sigla'])

        response = APIClient().get(self.url, {'search': 'dcat'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [unidad['codigo'] for unidad in response.data], ['F3A-DCAT'],
        )


class AprobacionSuperAdminTests(F3aTestBase):
    """B. POST /api/v2/admin/users/{id}/approve/ con SUPER_ADMIN."""

    def _pendiente(self, email):
        response = self.registrar(email)
        assert response.status_code == status.HTTP_201_CREATED
        return Usuario.objects.get(email=email)

    def test_aprobacion_formulador_self_activa_usuario(self):
        u = self._pendiente('f3a-ap-formulador@test.gob.bo')
        response = self.aprobar(self.super_admin, u)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        u.refresh_from_db()
        self.assertEqual(u.estado, Usuario.ESTADO_ACTIVO)
        self.assertTrue(u.activo)
        self.assertTrue(u.is_active)
        self.assertFalse(u.is_staff)
        self.assertTrue(u.debe_cambiar_password)
        self.assertIn(self.rol_formulador, u.roles.all())

        alcance = u.alcances_organizacionales.get(rol=self.rol_formulador)
        self.assertEqual(alcance.scope_type, AlcanceOrganizacional.SCOPE_SELF)
        self.assertEqual(alcance.unidad_id, self.dir_catastro.id)

    def test_aprobacion_jefe_poa_fuerza_alcance_global(self):
        u = self._pendiente('f3a-ap-jefepoa@test.gob.bo')
        response = self.aprobar(
            self.super_admin, u,
            rol_codigo='JEFE_POA',
            unidad_organizacional_id=str(self.secretaria.id),
            scope_type=AlcanceOrganizacional.SCOPE_SELF,  # se fuerza GLOBAL
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        alcance = u.alcances_organizacionales.get(rol=self.rol_jefe_poa)
        self.assertEqual(alcance.scope_type, AlcanceOrganizacional.SCOPE_GLOBAL)
        self.assertEqual(alcance.unidad_id, self.secretaria.id)

    def test_aprobacion_super_admin_fuerza_alcance_global(self):
        u = self._pendiente('f3a-ap-superadmin@test.gob.bo')
        response = self.aprobar(
            self.super_admin, u,
            rol_codigo='SUPER_ADMIN',
            sistema='sis_pe',
            scope_type=AlcanceOrganizacional.SCOPE_SELF,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        alcance = u.alcances_organizacionales.get(rol=self.rol_super_admin)
        self.assertEqual(alcance.scope_type, AlcanceOrganizacional.SCOPE_GLOBAL)

    def test_aprobacion_fuerza_scopes_normativos_de_roles_base(self):
        casos = [
            (
                'f3a-ap-scope-jefepe@test.gob.bo', self.rol_jefe_pe,
                'sis_pe', AlcanceOrganizacional.SCOPE_SELF,
                AlcanceOrganizacional.SCOPE_GLOBAL,
            ),
            (
                'f3a-ap-scope-director@test.gob.bo', self.rol_director,
                'sis_poa', AlcanceOrganizacional.SCOPE_GLOBAL,
                AlcanceOrganizacional.SCOPE_DESCENDANTS,
            ),
            (
                'f3a-ap-scope-formulador@test.gob.bo', self.rol_formulador,
                'sis_poa', AlcanceOrganizacional.SCOPE_GLOBAL,
                AlcanceOrganizacional.SCOPE_SELF,
            ),
        ]
        for email, rol, sistema, solicitado, esperado in casos:
            with self.subTest(rol=rol.codigo):
                usuario = self._pendiente(email)
                response = self.aprobar(
                    self.super_admin,
                    usuario,
                    rol_codigo=rol.codigo,
                    sistema=sistema,
                    scope_type=solicitado,
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                alcance = usuario.alcances_organizacionales.get(rol=rol)
                self.assertEqual(alcance.scope_type, esperado)

    def test_aprobacion_rol_inexistente_devuelve_400(self):
        u = self._pendiente('f3a-ap-rolno@test.gob.bo')
        response = self.aprobar(self.super_admin, u, rol_codigo='NO_EXISTE')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        u.refresh_from_db()
        self.assertEqual(u.estado, Usuario.ESTADO_PENDIENTE)

    def test_aprobacion_unidad_inexistente_devuelve_400(self):
        u = self._pendiente('f3a-ap-uono@test.gob.bo')
        response = self.aprobar(
            self.super_admin, u,
            unidad_organizacional_id='00000000-0000-0000-0000-000000000000',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_aprobacion_scope_type_invalido_devuelve_400(self):
        u = self._pendiente('f3a-ap-scopeno@test.gob.bo')
        response = self.aprobar(self.super_admin, u, scope_type='TODO')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_aprobacion_rol_de_otro_sistema_devuelve_400(self):
        """JEFE_PE no es asignable a SIS-POA aunque su configuración cambie."""
        u = self._pendiente('f3a-ap-sistemo@test.gob.bo')
        response = self.aprobar(
            self.super_admin, u, rol_codigo='JEFE_PE', sistema='sis_poa',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        u.refresh_from_db()
        self.assertEqual(u.estado, Usuario.ESTADO_PENDIENTE)

    def test_aprobacion_rol_sin_capacidades_del_sistema_devuelve_400(self):
        u = self._pendiente('f3a-ap-cap-sistema@test.gob.bo')
        response = self.aprobar(
            self.super_admin, u,
            rol_codigo='F3A-SOLO-ACCOUNTS',
            sistema='sis_poa',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_aprobacion_sistema_invalido_devuelve_400(self):
        u = self._pendiente('f3a-ap-sistema-invalido@test.gob.bo')
        response = self.aprobar(self.super_admin, u, sistema='sis_pro')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_no_auto_aprobacion(self):
        """Ni un superusuario puede aprobar su propia solicitud."""
        admin_pendiente = Usuario.objects.create_user(
            email='f3a-admin-pendiente@test.gob.bo', password=PASSWORD,
            is_staff=True, is_superuser=True,
            estado=Usuario.ESTADO_PENDIENTE,
        )
        response = self.aprobar(admin_pendiente, admin_pendiente)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        admin_pendiente.refresh_from_db()
        self.assertEqual(admin_pendiente.estado, Usuario.ESTADO_PENDIENTE)

    def test_aprobar_usuario_no_pendiente_devuelve_400(self):
        response = self.aprobar(self.super_admin, self.jefe_poa)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_fiscal_year_inexistente_devuelve_400(self):
        u = self._pendiente('f3a-ap-fyno@test.gob.bo')
        response = self.aprobar(
            self.super_admin, u,
            fiscal_year_id='00000000-0000-0000-0000-000000000000',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AprobacionPermisosTests(F3aTestBase):
    """C. Aprobación con permisos insuficientes → 403."""

    def _pendiente(self, email):
        self.registrar(email)
        return Usuario.objects.get(email=email)

    def test_usuario_sin_capacidad_no_puede_aprobar(self):
        u = self._pendiente('f3a-c-sincap@test.gob.bo')
        response = self.aprobar(self.sin_capacidad, u)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_jefe_pe_no_puede_aprobar_para_sis_poa(self):
        """La capacidad general no habilita a JEFE_PE en SIS-POA."""
        u = self._pendiente('f3a-c-jefepe@test.gob.bo')
        response = self.aprobar(
            self.jefe_pe, u, rol_codigo='DIRECTOR', sistema='sis_poa',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_jefe_pe_no_puede_asignar_super_admin(self):
        u = self._pendiente('f3a-c-jefepe-superadmin@test.gob.bo')
        response = self.aprobar(
            self.jefe_pe, u, rol_codigo='SUPER_ADMIN', sistema='sis_pe',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        u.refresh_from_db()
        self.assertEqual(u.estado, Usuario.ESTADO_PENDIENTE)

    def test_jefe_poa_no_puede_aprobar_para_sis_pe(self):
        u = self._pendiente('f3a-c-jefepoa@test.gob.bo')
        response = self.aprobar(
            self.jefe_poa, u, rol_codigo='JEFE_PE', sistema='sis_pe',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_jefe_poa_puede_aprobar_para_sis_poa(self):
        u = self._pendiente('f3a-c-jefepoa-valido@test.gob.bo')
        response = self.aprobar(self.jefe_poa, u)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_jefe_pe_puede_aprobar_para_sis_pe(self):
        u = self._pendiente('f3a-c-jefepe-valido@test.gob.bo')
        response = self.aprobar(
            self.jefe_pe, u, rol_codigo='JEFE_PE', sistema='sis_pe',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_aprobar_sin_autenticacion_devuelve_401(self):
        u = self._pendiente('f3a-c-anon@test.gob.bo')
        response = self.cliente().post(
            reverse('v2-admin-user-approve', kwargs={'pk': u.pk}),
            self.payload_aprobacion(),
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SolicitudesListTests(F3aTestBase):
    """D. GET /api/v2/admin/solicitudes/."""

    def setUp(self):
        super().setUp()
        # Un PENDIENTE visible y un ACTIVO que no debe aparecer.
        self.registrar('f3a-list-pendiente@test.gob.bo')
        self.url = reverse('v2-admin-solicitudes')

    @staticmethod
    def resultados(response):
        """Normaliza la respuesta con y sin paginación según los settings."""
        if isinstance(response.data, list):
            return response.data
        return response.data['results']

    def test_sin_autenticacion_devuelve_401(self):
        response = self.cliente().get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_sin_capacidad_devuelve_403(self):
        response = self.cliente(self.sin_capacidad).get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_super_admin_lista_solo_pendientes(self):
        response = self.cliente(self.super_admin).get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        emails = [s['email'] for s in self.resultados(response)]
        self.assertIn('f3a-list-pendiente@test.gob.bo', emails)
        # Ningún usuario ACTIVO del setUpTestData aparece.
        self.assertNotIn(self.super_admin.email, emails)
        self.assertNotIn(self.jefe_poa.email, emails)

    def test_jefe_poa_lista_solo_pendientes(self):
        response = self.cliente(self.jefe_poa).get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        emails = [s['email'] for s in self.resultados(response)]
        self.assertIn('f3a-list-pendiente@test.gob.bo', emails)
        self.assertNotIn(self.jefe_pe.email, emails)

    def test_listado_expone_unidad_solicitada(self):
        response = self.cliente(self.super_admin).get(self.url)
        solicitud = next(
            s for s in self.resultados(response)
            if s['email'] == 'f3a-list-pendiente@test.gob.bo'
        )
        self.assertEqual(
            solicitud['unidad_solicitada']['id'], str(self.dir_catastro.id),
        )

    def test_listado_no_expone_datos_sensibles(self):
        response = self.cliente(self.super_admin).get(self.url)
        for solicitud in self.resultados(response):
            for campo in ('roles', 'is_staff', 'is_superuser', 'password'):
                self.assertNotIn(campo, solicitud)
