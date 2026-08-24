"""Tests F3b1: administración V2 de usuarios y ciclo activo/inactivo."""

from datetime import date

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import (
    AlcanceOrganizacional,
    Capacidad,
    Rol,
    Usuario,
)
from apps.gestion.models import GestionFiscal
from apps.organizacion.models import TipoUnidad, UnidadOrganizacional

PASSWORD = 'Clave-Admin.Segura.2026'
CAPACIDADES_ADMIN = [
    'accounts.usuario.view',
    'accounts.usuario.edit',
    'accounts.usuario.activate',
]


class F3b1TestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.gestion, _ = GestionFiscal.objects.get_or_create(
            anio=2026, defaults={'estado': 'preparacion'},
        )
        tipo, _ = TipoUnidad.objects.get_or_create(
            codigo='F3B1-TIPO',
            defaults={'nombre': 'Tipo test F3b1', 'nivel': 1},
        )

        def unidad(codigo, nombre):
            return UnidadOrganizacional.objects.create(
                codigo=codigo,
                nombre=nombre,
                tipo=tipo,
                gestion=cls.gestion,
                fecha_vigencia_desde=date(2026, 1, 1),
            )

        cls.unidad_pe = unidad('F3B1-PE', 'Dirección de Planificación')
        cls.unidad_poa = unidad('F3B1-POA', 'Dirección POA')

        def capacidad(codigo):
            obj, _ = Capacidad.objects.get_or_create(
                codigo=codigo,
                defaults={
                    'nombre': codigo,
                    'sistema': codigo.split('.')[0],
                },
            )
            return obj

        def rol(codigo, capacidades):
            obj, _ = Rol.objects.get_or_create(
                codigo=codigo,
                defaults={'nombre': codigo, 'activo': True},
            )
            obj.capacidades.add(*[capacidad(codigo) for codigo in capacidades])
            return obj

        cls.rol_pe = rol('F3B1-ANALISTA-PE', ['sis_pe.pad.view'])
        cls.rol_poa = rol('F3B1-ANALISTA-POA', ['sis_poa.poau.view'])
        cls.rol_jefe_pe = rol(
            'JEFE_PE', ['sis_pe.pad.view', *CAPACIDADES_ADMIN],
        )
        cls.rol_jefe_poa = rol(
            'JEFE_POA', ['sis_poa.poau.view', *CAPACIDADES_ADMIN],
        )
        cls.rol_super_admin = rol(
            'SUPER_ADMIN',
            ['sis_pe.pad.view', 'sis_poa.poau.view', *CAPACIDADES_ADMIN],
        )
        cls.rol_sin_admin = rol(
            'F3B1-SIN-ADMIN', ['sis_poa.poau.view'],
        )

        def usuario(email, *roles, **kwargs):
            obj = Usuario.objects.create_user(
                email=email,
                password=PASSWORD,
                first_name=kwargs.pop('first_name', 'Nombre'),
                last_name=kwargs.pop('last_name', 'Apellido'),
                **kwargs,
            )
            obj.roles.add(*roles)
            return obj

        cls.superuser = usuario(
            'f3b1-superuser@test.gob.bo',
            first_name='Django',
            last_name='Superuser',
            is_staff=True,
            is_superuser=True,
        )
        cls.jefe_pe = usuario(
            'f3b1-jefe-pe@test.gob.bo', cls.rol_jefe_pe,
            first_name='Jefe', last_name='PE',
        )
        cls.jefe_poa = usuario(
            'f3b1-jefe-poa@test.gob.bo', cls.rol_jefe_poa,
            first_name='Jefe', last_name='POA',
        )
        cls.sin_capacidad = usuario(
            'f3b1-sin-capacidad@test.gob.bo', cls.rol_sin_admin,
        )

        cls.usuario_pe = usuario(
            'ana.pe@test.gob.bo', cls.rol_pe,
            first_name='Ana', last_name='Planificadora',
            cargo='Especialista Estratégica', telefono='4455667',
        )
        cls.usuario_pe.last_login = timezone.now()
        cls.usuario_pe.save(update_fields=['last_login'])
        cls.usuario_poa = usuario(
            'boris.poa@test.gob.bo', cls.rol_poa,
            first_name='Boris', last_name='Operativo',
            cargo='Analista POA',
        )
        cls.usuario_poa_inactivo = usuario(
            'carla.inactiva@test.gob.bo', cls.rol_poa,
            first_name='Carla', last_name='Inactiva',
            cargo='Técnica', estado=Usuario.ESTADO_INACTIVO,
            is_active=False,
        )
        cls.usuario_mixto = usuario(
            'dario.mixto@test.gob.bo', cls.rol_pe, cls.rol_poa,
            first_name='Darío', last_name='Mixto',
        )
        cls.usuario_super_admin = usuario(
            'elena.superadmin@test.gob.bo', cls.rol_super_admin,
            first_name='Elena', last_name='SuperAdmin',
        )
        cls.usuario_pendiente = usuario(
            'fabiola.pendiente@test.gob.bo',
            first_name='Fabiola', last_name='Pendiente',
            estado=Usuario.ESTADO_PENDIENTE, is_active=False,
        )

        cls.alcance_pe = AlcanceOrganizacional.objects.create(
            usuario=cls.usuario_pe,
            rol=cls.rol_pe,
            unidad=cls.unidad_pe,
            scope_type=AlcanceOrganizacional.SCOPE_DESCENDANTS,
            fiscal_year=cls.gestion,
        )
        AlcanceOrganizacional.objects.create(
            usuario=cls.usuario_poa,
            rol=cls.rol_poa,
            unidad=cls.unidad_poa,
            scope_type=AlcanceOrganizacional.SCOPE_SELF,
        )
        AlcanceOrganizacional.objects.create(
            usuario=cls.usuario_poa_inactivo,
            rol=cls.rol_poa,
            unidad=cls.unidad_poa,
            scope_type=AlcanceOrganizacional.SCOPE_SELF,
        )
        AlcanceOrganizacional.objects.create(
            usuario=cls.usuario_super_admin,
            rol=cls.rol_super_admin,
            unidad=cls.unidad_pe,
            scope_type=AlcanceOrganizacional.SCOPE_GLOBAL,
        )

    def cliente(self, usuario=None):
        client = APIClient()
        if usuario is not None:
            client.force_authenticate(user=usuario)
        return client

    @staticmethod
    def resultados(response):
        return response.data.get('results', response.data)

    @staticmethod
    def emails(response):
        return {item['email'] for item in F3b1TestBase.resultados(response)}

    @staticmethod
    def url_detalle(usuario):
        return reverse('v2-admin-user-detail', kwargs={'pk': usuario.pk})


class UsuarioAdminAutorizacionTests(F3b1TestBase):
    def test_listado_sin_autenticacion_devuelve_401(self):
        response = self.cliente().get(reverse('v2-admin-users'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_detalle_sin_autenticacion_devuelve_401(self):
        response = self.cliente().get(self.url_detalle(self.usuario_pe))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_usuario_sin_capacidad_recibe_403_segun_operacion(self):
        client = self.cliente(self.sin_capacidad)
        respuestas = [
            client.get(reverse('v2-admin-users')),
            client.get(self.url_detalle(self.usuario_poa)),
            client.patch(
                self.url_detalle(self.usuario_poa),
                {'cargo': 'Nuevo'}, format='json',
            ),
            client.post(reverse(
                'v2-admin-user-deactivate',
                kwargs={'pk': self.usuario_poa.pk},
            )),
        ]
        self.assertTrue(all(
            response.status_code == status.HTTP_403_FORBIDDEN
            for response in respuestas
        ))

    def test_superuser_ve_usuarios_de_ambos_sistemas(self):
        response = self.cliente(self.superuser).get(reverse('v2-admin-users'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        emails = self.emails(response)
        self.assertIn(self.usuario_pe.email, emails)
        self.assertIn(self.usuario_poa.email, emails)
        self.assertIn(self.usuario_mixto.email, emails)
        self.assertIn(self.usuario_super_admin.email, emails)

    def test_jefe_pe_solo_lista_usuarios_exclusivamente_pe(self):
        response = self.cliente(self.jefe_pe).get(reverse('v2-admin-users'))
        emails = self.emails(response)
        self.assertIn(self.usuario_pe.email, emails)
        self.assertNotIn(self.usuario_poa.email, emails)
        self.assertNotIn(self.usuario_mixto.email, emails)
        self.assertNotIn(self.usuario_super_admin.email, emails)
        self.assertNotIn(self.usuario_pendiente.email, emails)

    def test_jefe_poa_solo_lista_usuarios_exclusivamente_poa(self):
        response = self.cliente(self.jefe_poa).get(reverse('v2-admin-users'))
        emails = self.emails(response)
        self.assertIn(self.usuario_poa.email, emails)
        self.assertIn(self.usuario_poa_inactivo.email, emails)
        self.assertNotIn(self.usuario_pe.email, emails)
        self.assertNotIn(self.usuario_mixto.email, emails)
        self.assertNotIn(self.usuario_super_admin.email, emails)

    def test_jefe_pe_recibe_404_en_detalle_y_patch_poa_o_super_admin(self):
        client = self.cliente(self.jefe_pe)
        for objetivo in (self.usuario_poa, self.usuario_super_admin):
            self.assertEqual(
                client.get(self.url_detalle(objetivo)).status_code,
                status.HTTP_404_NOT_FOUND,
            )
            self.assertEqual(
                client.patch(
                    self.url_detalle(objetivo),
                    {'cargo': 'No permitido'}, format='json',
                ).status_code,
                status.HTTP_404_NOT_FOUND,
            )

    def test_jefe_poa_recibe_404_en_detalle_y_patch_pe_o_super_admin(self):
        client = self.cliente(self.jefe_poa)
        for objetivo in (self.usuario_pe, self.usuario_super_admin):
            self.assertEqual(
                client.get(self.url_detalle(objetivo)).status_code,
                status.HTTP_404_NOT_FOUND,
            )
            self.assertEqual(
                client.patch(
                    self.url_detalle(objetivo),
                    {'cargo': 'No permitido'}, format='json',
                ).status_code,
                status.HTTP_404_NOT_FOUND,
            )


class UsuarioAdminFiltrosTests(F3b1TestBase):
    def listar(self, **params):
        return self.cliente(self.superuser).get(
            reverse('v2-admin-users'), params,
        )

    def test_search_busca_nombre_apellido_email_y_cargo(self):
        casos = [
            ('Ana', self.usuario_pe.email),
            ('Operativo', self.usuario_poa.email),
            ('carla.inactiva', self.usuario_poa_inactivo.email),
            ('Estratégica', self.usuario_pe.email),
        ]
        for busqueda, esperado in casos:
            with self.subTest(search=busqueda):
                response = self.listar(search=busqueda)
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertIn(esperado, self.emails(response))

    def test_filtro_unidad_organizacional(self):
        response = self.listar(organizational_unit=str(self.unidad_pe.pk))
        self.assertEqual(
            self.emails(response),
            {self.usuario_pe.email, self.usuario_super_admin.email},
        )

    def test_filtro_rol_por_codigo_interno(self):
        response = self.listar(role=self.rol_pe.codigo)
        self.assertEqual(
            self.emails(response),
            {self.usuario_pe.email, self.usuario_mixto.email},
        )

    def test_filtro_sistema(self):
        response_pe = self.listar(system='sis_pe')
        response_poa = self.listar(system='sis_poa')
        self.assertIn(self.usuario_pe.email, self.emails(response_pe))
        self.assertNotIn(self.usuario_poa.email, self.emails(response_pe))
        self.assertIn(self.usuario_poa.email, self.emails(response_poa))
        self.assertNotIn(self.usuario_pe.email, self.emails(response_poa))
        self.assertIn(self.usuario_mixto.email, self.emails(response_pe))
        self.assertIn(self.usuario_mixto.email, self.emails(response_poa))

    def test_filtro_estado(self):
        response = self.listar(state=Usuario.ESTADO_INACTIVO)
        self.assertEqual(self.emails(response), {self.usuario_poa_inactivo.email})

    def test_filtros_invalidos_devuelven_400(self):
        for params in (
            {'system': 'sis_pro'},
            {'state': 'BORRADO'},
            {'organizational_unit': 'no-es-uuid'},
        ):
            with self.subTest(params=params):
                self.assertEqual(
                    self.listar(**params).status_code,
                    status.HTTP_400_BAD_REQUEST,
                )


class UsuarioAdminContratoTests(F3b1TestBase):
    def test_detalle_expone_campos_roles_alcances_y_sistemas_deduplicados(self):
        response = self.cliente(self.superuser).get(
            self.url_detalle(self.usuario_pe),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            set(response.data),
            {
                'id', 'first_name', 'last_name', 'email', 'cargo',
                'estado', 'activo', 'is_active', 'last_login',
                'roles', 'alcances', 'sistemas',
            },
        )
        self.assertEqual(response.data['sistemas'], ['sis_pe'])
        self.assertEqual(response.data['roles'], [{
            'codigo': self.rol_pe.codigo,
            'nombre': self.rol_pe.nombre,
            'sistemas': ['sis_pe'],
        }])
        self.assertEqual(len(response.data['alcances']), 1)
        alcance = response.data['alcances'][0]
        self.assertEqual(alcance['rol'], self.rol_pe.codigo)
        self.assertEqual(alcance['scope_type'], 'DESCENDANTS')
        self.assertEqual(alcance['fiscal_year'], str(self.gestion.pk))
        self.assertEqual(alcance['unidad'], {
            'id': str(self.unidad_pe.pk),
            'codigo': self.unidad_pe.codigo,
            'nombre': self.unidad_pe.nombre,
        })
        self.assertIsNotNone(response.data['last_login'])

    def test_usuario_mixto_deduplica_sistemas_de_roles_y_alcances(self):
        response = self.cliente(self.superuser).get(
            self.url_detalle(self.usuario_mixto),
        )
        self.assertEqual(response.data['sistemas'], ['sis_pe', 'sis_poa'])


class UsuarioAdminPatchTests(F3b1TestBase):
    def test_patch_actualiza_solo_los_cuatro_datos_personales(self):
        response = self.cliente(self.jefe_pe).patch(
            self.url_detalle(self.usuario_pe),
            {
                'first_name': 'Ana María',
                'last_name': 'Actualizada',
                'cargo': 'Jefa de Unidad',
                'telefono': '70000001',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.usuario_pe.refresh_from_db()
        self.assertEqual(self.usuario_pe.first_name, 'Ana María')
        self.assertEqual(self.usuario_pe.last_name, 'Actualizada')
        self.assertEqual(self.usuario_pe.cargo, 'Jefa de Unidad')
        self.assertEqual(self.usuario_pe.telefono, '70000001')

    def test_patch_rechaza_estado_roles_email_y_campos_desconocidos(self):
        originales = (
            self.usuario_pe.email,
            self.usuario_pe.estado,
            set(self.usuario_pe.roles.values_list('pk', flat=True)),
        )
        response = self.cliente(self.superuser).patch(
            self.url_detalle(self.usuario_pe),
            {
                'email': 'cambiado@test.gob.bo',
                'estado': Usuario.ESTADO_INACTIVO,
                'roles': [str(self.rol_poa.pk)],
                'is_active': False,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.usuario_pe.refresh_from_db()
        self.assertEqual(self.usuario_pe.email, originales[0])
        self.assertEqual(self.usuario_pe.estado, originales[1])
        self.assertEqual(
            set(self.usuario_pe.roles.values_list('pk', flat=True)),
            originales[2],
        )


class UsuarioAdminEstadoTests(F3b1TestBase):
    def url_estado(self, nombre, usuario):
        return reverse(nombre, kwargs={'pk': usuario.pk})

    def test_desactivar_sincroniza_estado_activo_e_is_active(self):
        response = self.cliente(self.superuser).post(self.url_estado(
            'v2-admin-user-deactivate', self.usuario_poa,
        ))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.usuario_poa.refresh_from_db()
        self.assertEqual(self.usuario_poa.estado, Usuario.ESTADO_INACTIVO)
        self.assertFalse(self.usuario_poa.activo)
        self.assertFalse(self.usuario_poa.is_active)

    def test_activar_sincroniza_estado_activo_e_is_active(self):
        response = self.cliente(self.superuser).post(self.url_estado(
            'v2-admin-user-activate', self.usuario_poa_inactivo,
        ))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.usuario_poa_inactivo.refresh_from_db()
        self.assertEqual(self.usuario_poa_inactivo.estado, Usuario.ESTADO_ACTIVO)
        self.assertTrue(self.usuario_poa_inactivo.activo)
        self.assertTrue(self.usuario_poa_inactivo.is_active)

    def test_auto_desactivacion_esta_prohibida(self):
        response = self.cliente(self.superuser).post(self.url_estado(
            'v2-admin-user-deactivate', self.superuser,
        ))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.superuser.refresh_from_db()
        self.assertTrue(self.superuser.is_active)
        self.assertEqual(self.superuser.estado, Usuario.ESTADO_ACTIVO)

    def test_jefe_no_puede_cambiar_estado_fuera_de_su_dominio(self):
        casos = [
            (self.jefe_pe, self.usuario_poa),
            (self.jefe_poa, self.usuario_pe),
            (self.jefe_pe, self.usuario_super_admin),
            (self.jefe_poa, self.usuario_super_admin),
        ]
        for administrador, objetivo in casos:
            with self.subTest(admin=administrador.email, target=objetivo.email):
                response = self.cliente(administrador).post(self.url_estado(
                    'v2-admin-user-deactivate', objetivo,
                ))
                self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
