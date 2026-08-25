"""Tests F3b2a: administración V2 de roles y capacidades."""

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import Capacidad, Rol, Usuario


PASSWORD = 'Clave-Roles.Segura.2026'
CAPACIDADES_ADMIN = [
    'accounts.rol.view',
    'accounts.rol.create',
    'accounts.rol.edit',
    'accounts.capacidad.view',
    'accounts.capacidad.assign',
]


class F3b2aTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        def capacidad(codigo, *, activo=True, sistema=None):
            obj, _ = Capacidad.objects.get_or_create(
                codigo=codigo,
                defaults={
                    'nombre': codigo,
                    'descripcion': f'Descripción {codigo}',
                    'sistema': sistema or codigo.split('.')[0],
                    'activo': activo,
                },
            )
            obj.nombre = codigo
            obj.descripcion = f'Descripción {codigo}'
            obj.sistema = sistema or codigo.split('.')[0]
            obj.activo = activo
            obj.save(update_fields=['nombre', 'descripcion', 'sistema', 'activo'])
            return obj

        cls.capacidades_admin = {
            codigo: capacidad(codigo) for codigo in CAPACIDADES_ADMIN
        }
        cls.cap_pe = capacidad(
            'sis_pe.f3b2a.view', sistema='sis_poa',
        )
        cls.cap_pe_edit = capacidad('sis_pe.f3b2a.edit')
        cls.cap_poa = capacidad('sis_poa.f3b2a.view')
        cls.cap_poa_edit = capacidad('sis_poa.f3b2a.edit')
        cls.cap_accounts_owned = capacidad('accounts.f3b2a.owned')
        cls.cap_accounts_unowned = capacidad('accounts.f3b2a.unowned')
        cls.cap_inactiva = capacidad('sis_pe.f3b2a.inactive', activo=False)
        cls.cap_pro = capacidad('sis_pro.f3b2a.view')
        cls.cap_pro_legacy = capacidad('sis-pro.f3b2a.legacy')
        cls.cap_platform = capacidad('platform.f3b2a.view')

        def rol(
            codigo, capacidades=(), *, es_sistema=False, deprecated=False,
            activo=True,
        ):
            obj, _ = Rol.objects.get_or_create(
                codigo=codigo,
                defaults={'nombre': codigo},
            )
            obj.nombre = codigo
            obj.descripcion = f'Descripción {codigo}'
            obj.es_sistema = es_sistema
            obj.deprecated = deprecated
            obj.activo = activo
            obj.save(update_fields=[
                'nombre', 'descripcion', 'es_sistema', 'deprecated', 'activo',
            ])
            obj.capacidades.set(capacidades)
            return obj

        admin = list(cls.capacidades_admin.values())
        cls.rol_super_admin = rol(
            'SUPER_ADMIN', [cls.cap_pe, cls.cap_poa, *admin], es_sistema=True,
        )
        cls.rol_secretario = rol(
            'SECRETARIO_MUNICIPAL', [cls.cap_poa], es_sistema=True,
        )
        cls.rol_director = rol(
            'DIRECTOR', [cls.cap_poa], es_sistema=True,
        )
        cls.rol_jefe_poa = rol(
            'JEFE_POA',
            [cls.cap_poa, cls.cap_accounts_owned, *admin],
            es_sistema=True,
        )
        cls.rol_jefe_pe = rol(
            'JEFE_PE',
            [cls.cap_pe, cls.cap_accounts_owned, *admin],
            es_sistema=True,
        )
        cls.rol_formulador = rol(
            'FORMULADOR_POAU', [cls.cap_poa], es_sistema=True,
        )
        cls.rol_pe = rol('CUSTOM_PE', [cls.cap_pe])
        cls.rol_poa = rol('CUSTOM_POA', [cls.cap_poa])
        cls.rol_mixto = rol('CUSTOM_MIXED', [cls.cap_pe, cls.cap_poa])
        cls.rol_deprecated = rol(
            'DEPRECATED_ROLE', [cls.cap_pe], deprecated=True,
        )
        cls.rol_sin_permisos = rol('NO_ADMIN_ROLE')

        def usuario(email, *roles, **kwargs):
            obj = Usuario.objects.create_user(
                email=email, password=PASSWORD, **kwargs,
            )
            obj.roles.set(roles)
            return obj

        cls.superuser = usuario(
            'f3b2a-superuser@test.gob.bo',
            is_staff=True,
            is_superuser=True,
        )
        cls.jefe_pe = usuario(
            'f3b2a-jefe-pe@test.gob.bo', cls.rol_jefe_pe,
        )
        cls.jefe_poa = usuario(
            'f3b2a-jefe-poa@test.gob.bo', cls.rol_jefe_poa,
        )
        cls.sin_capacidad = usuario(
            'f3b2a-sin-capacidad@test.gob.bo', cls.rol_sin_permisos,
        )

    @staticmethod
    def cliente(usuario=None):
        client = APIClient()
        if usuario is not None:
            client.force_authenticate(user=usuario)
        return client

    @staticmethod
    def resultados(response):
        return response.data.get('results', response.data)

    @staticmethod
    def codigos(response):
        return {
            item['codigo'] for item in F3b2aTestBase.resultados(response)
        }

    @staticmethod
    def url_rol(rol):
        return reverse('v2-admin-role-detail', kwargs={'pk': rol.pk})

    @staticmethod
    def url_capacidades_rol(rol):
        return reverse(
            'v2-admin-role-capabilities', kwargs={'pk': rol.pk},
        )


class RolAdminAutorizacionTests(F3b2aTestBase):
    def test_sin_autenticacion_devuelve_401_en_cada_operacion(self):
        client = self.cliente()
        casos = [
            client.get(reverse('v2-admin-roles')),
            client.post(reverse('v2-admin-roles'), {}, format='json'),
            client.get(self.url_rol(self.rol_pe)),
            client.patch(self.url_rol(self.rol_pe), {}, format='json'),
            client.put(
                self.url_capacidades_rol(self.rol_pe),
                {'capability_codes': []},
                format='json',
            ),
            client.get(reverse('v2-admin-capabilities')),
        ]
        self.assertTrue(all(
            response.status_code == status.HTTP_401_UNAUTHORIZED
            for response in casos
        ))

    def test_sin_capacidad_devuelve_403_en_cada_operacion(self):
        client = self.cliente(self.sin_capacidad)
        casos = [
            client.get(reverse('v2-admin-roles')),
            client.post(reverse('v2-admin-roles'), {}, format='json'),
            client.get(self.url_rol(self.rol_pe)),
            client.patch(self.url_rol(self.rol_pe), {}, format='json'),
            client.put(
                self.url_capacidades_rol(self.rol_pe),
                {'capability_codes': []},
                format='json',
            ),
            client.get(reverse('v2-admin-capabilities')),
        ]
        self.assertTrue(all(
            response.status_code == status.HTTP_403_FORBIDDEN
            for response in casos
        ))

    def test_catalogo_capacidades_es_solo_lectura(self):
        client = self.cliente(self.superuser)
        url = reverse('v2-admin-capabilities')
        self.assertEqual(
            client.post(url, {}, format='json').status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
        self.assertEqual(
            client.patch(url, {}, format='json').status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )


class RolAdminSuperuserTests(F3b2aTestBase):
    def test_lista_roles_de_ambos_sistemas_y_expone_contrato(self):
        client = self.cliente(self.superuser)
        url = reverse('v2-admin-roles')
        pe_response = client.get(url, {'system': 'sis_pe'})
        poa_response = client.get(url, {'system': 'sis_poa'})
        self.assertIn('CUSTOM_PE', self.codigos(pe_response))
        self.assertIn('CUSTOM_POA', self.codigos(poa_response))
        response = client.get(url, {'search': 'CUSTOM_PE'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item = next(
            rol for rol in self.resultados(response)
            if rol['codigo'] == 'CUSTOM_PE'
        )
        self.assertEqual(set(item), {
            'id', 'codigo', 'nombre', 'descripcion', 'activo', 'es_sistema',
            'deprecated', 'orden', 'sistemas', 'capacidades',
        })
        self.assertEqual(item['sistemas'], ['sis_pe'])
        self.assertEqual(
            item['capacidades'][0]['sistema'], 'sis_pe',
        )

    def test_filtro_roles_accounts_usa_el_sistema_efectivo(self):
        response = self.cliente(self.superuser).get(
            reverse('v2-admin-roles'), {'system': 'accounts'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.rol_jefe_pe.codigo, self.codigos(response))
        self.assertNotIn(self.rol_poa.codigo, self.codigos(response))

    def test_crea_patch_y_asigna_capacidades_a_rol_personalizado(self):
        client = self.cliente(self.superuser)
        create_response = client.post(
            reverse('v2-admin-roles'),
            {
                'codigo': 'CUSTOM_CREATED',
                'nombre': 'Rol creado',
                'descripcion': 'Descripción inicial',
                'activo': True,
            },
            format='json',
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        rol = Rol.objects.get(codigo='CUSTOM_CREATED')
        self.assertFalse(rol.es_sistema)
        self.assertFalse(rol.deprecated)

        patch_response = client.patch(
            self.url_rol(rol),
            {
                'nombre': 'Rol actualizado',
                'descripcion': 'Nueva descripción',
                'activo': False,
                'orden': 44,
            },
            format='json',
        )
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        rol.refresh_from_db()
        self.assertEqual(rol.nombre, 'Rol actualizado')
        self.assertFalse(rol.activo)
        self.assertEqual(rol.orden, 44)

        assign_response = client.put(
            self.url_capacidades_rol(rol),
            {
                'capability_codes': [
                    self.cap_pe.codigo,
                    self.cap_poa.codigo,
                    self.cap_accounts_owned.codigo,
                ],
            },
            format='json',
        )
        self.assertEqual(assign_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            set(rol.capacidades.values_list('codigo', flat=True)),
            {
                self.cap_pe.codigo,
                self.cap_poa.codigo,
                self.cap_accounts_owned.codigo,
            },
        )
        self.assertEqual(
            assign_response.data['sistemas'],
            ['accounts', 'sis_pe', 'sis_poa'],
        )

    def test_roles_base_son_visibles_pero_inmutables(self):
        client = self.cliente(self.superuser)
        url = reverse('v2-admin-roles')
        codigos_base = {
            'SUPER_ADMIN', 'SECRETARIO_MUNICIPAL', 'DIRECTOR',
            'JEFE_POA', 'JEFE_PE', 'FORMULADOR_POAU',
        }
        for codigo in codigos_base:
            with self.subTest(codigo=codigo):
                self.assertIn(
                    codigo, self.codigos(client.get(url, {'search': codigo})),
                )
        self.assertEqual(
            client.get(self.url_rol(self.rol_jefe_pe)).status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            client.patch(
                self.url_rol(self.rol_jefe_pe),
                {'nombre': 'No permitido'},
                format='json',
            ).status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            client.put(
                self.url_capacidades_rol(self.rol_jefe_pe),
                {'capability_codes': [self.cap_pe.codigo]},
                format='json',
            ).status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_deprecated_ocultos_y_solo_superuser_puede_incluirlos(self):
        url = reverse('v2-admin-roles')
        client = self.cliente(self.superuser)
        self.assertNotIn(
            self.rol_deprecated.codigo,
            self.codigos(client.get(url, {'search': 'DEPRECATED_ROLE'})),
        )
        self.assertIn(
            self.rol_deprecated.codigo,
            self.codigos(client.get(url, {
                'search': 'DEPRECATED_ROLE',
                'include_deprecated': 'true',
            })),
        )
        response = self.cliente(self.jefe_pe).get(
            url, {'include_deprecated': 'true'},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class RolAdminJefaturasTests(F3b2aTestBase):
    def test_jefe_pe_no_ve_ni_modifica_roles_poa(self):
        client = self.cliente(self.jefe_pe)
        self.assertNotIn(
            self.rol_poa.codigo,
            self.codigos(client.get(reverse('v2-admin-roles'))),
        )
        self.assertEqual(
            client.get(self.url_rol(self.rol_poa)).status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            client.patch(
                self.url_rol(self.rol_poa), {'nombre': 'No'}, format='json',
            ).status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            client.put(
                self.url_capacidades_rol(self.rol_poa),
                {'capability_codes': [self.cap_pe.codigo]},
                format='json',
            ).status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_jefe_poa_no_ve_ni_modifica_roles_pe(self):
        client = self.cliente(self.jefe_poa)
        self.assertNotIn(
            self.rol_pe.codigo,
            self.codigos(client.get(reverse('v2-admin-roles'))),
        )
        self.assertEqual(
            client.get(self.url_rol(self.rol_pe)).status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            client.patch(
                self.url_rol(self.rol_pe), {'nombre': 'No'}, format='json',
            ).status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            client.put(
                self.url_capacidades_rol(self.rol_pe),
                {'capability_codes': [self.cap_poa.codigo]},
                format='json',
            ).status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_jefe_pe_solo_asigna_pe_y_accounts_que_posee(self):
        client = self.cliente(self.jefe_pe)
        response = client.put(
            self.url_capacidades_rol(self.rol_pe),
            {
                'capability_codes': [
                    self.cap_pe_edit.codigo,
                    self.cap_accounts_owned.codigo,
                ],
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for codigo in (self.cap_poa.codigo, self.cap_accounts_unowned.codigo):
            with self.subTest(codigo=codigo):
                response = client.put(
                    self.url_capacidades_rol(self.rol_pe),
                    {'capability_codes': [codigo]},
                    format='json',
                )
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_jefe_poa_solo_asigna_poa_y_accounts_que_posee(self):
        client = self.cliente(self.jefe_poa)
        response = client.put(
            self.url_capacidades_rol(self.rol_poa),
            {
                'capability_codes': [
                    self.cap_poa_edit.codigo,
                    self.cap_accounts_owned.codigo,
                ],
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = client.put(
            self.url_capacidades_rol(self.rol_poa),
            {'capability_codes': [self.cap_pe.codigo]},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_jefaturas_con_capacidad_no_crean_roles_personalizados(self):
        casos = [
            (self.jefe_pe, 'PE_CREATED'),
            (self.jefe_poa, 'POA_CREATED'),
        ]
        for jefe, codigo in casos:
            with self.subTest(jefe=jefe.email):
                response = self.cliente(jefe).post(
                    reverse('v2-admin-roles'),
                    {'codigo': codigo, 'nombre': 'No permitido'},
                    format='json',
                )
                self.assertEqual(
                    response.status_code, status.HTTP_403_FORBIDDEN,
                )
                self.assertFalse(Rol.objects.filter(codigo=codigo).exists())

    def test_jefatura_mantiene_patch_de_rol_personalizado_de_su_sistema(self):
        response = self.cliente(self.jefe_pe).patch(
            self.url_rol(self.rol_pe),
            {'nombre': 'Modificado por PE'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CapacidadAdminTests(F3b2aTestBase):
    def test_catalogo_excluye_sis_pro_y_deriva_sistema_del_codigo(self):
        response = self.cliente(self.superuser).get(
            reverse('v2-admin-capabilities'), {'search': 'f3b2a'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        codigos = self.codigos(response)
        self.assertNotIn(self.cap_pro.codigo, codigos)
        self.assertNotIn(self.cap_pro_legacy.codigo, codigos)
        item = next(
            capacidad for capacidad in self.resultados(response)
            if capacidad['codigo'] == self.cap_pe.codigo
        )
        self.assertEqual(item['sistema'], 'sis_pe')
        self.assertEqual(set(item), {
            'id', 'codigo', 'nombre', 'descripcion', 'sistema', 'activo',
            'orden',
        })

    def test_filtros_system_active_y_search(self):
        client = self.cliente(self.superuser)
        url = reverse('v2-admin-capabilities')
        pe = client.get(url, {'system': 'sis_pe'})
        self.assertIn(self.cap_pe.codigo, self.codigos(pe))
        self.assertNotIn(self.cap_poa.codigo, self.codigos(pe))

        inactivas = client.get(url, {'active': 'false'})
        self.assertIn(self.cap_inactiva.codigo, self.codigos(inactivas))
        self.assertTrue(all(
            not item['activo'] for item in self.resultados(inactivas)
        ))

        search = client.get(url, {'search': 'f3b2a.edit'})
        self.assertTrue({
            self.cap_pe_edit.codigo, self.cap_poa_edit.codigo,
        } <= self.codigos(search))

        accounts = client.get(url, {'system': 'accounts'})
        self.assertIn(self.cap_accounts_owned.codigo, self.codigos(accounts))
        self.assertNotIn(self.cap_pe.codigo, self.codigos(accounts))

    def test_system_sis_pro_es_invalido(self):
        response = self.cliente(self.superuser).get(
            reverse('v2-admin-capabilities'), {'system': 'sis_pro'},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class RolAdminValidacionTests(F3b2aTestBase):
    def test_codigos_invalidos_reservados_y_duplicados(self):
        client = self.cliente(self.superuser)
        url = reverse('v2-admin-roles')
        for codigo in (
            'ab', 'lowercase', 'INVALID-CODE', 'JEFE_PE', 'CUSTOM_PE',
            'deprecated_role',
        ):
            with self.subTest(codigo=codigo):
                response = client.post(
                    url, {'codigo': codigo, 'nombre': 'Inválido'}, format='json',
                )
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_rechaza_codigo_es_sistema_deprecated_y_campos_extra(self):
        response = self.cliente(self.superuser).patch(
            self.url_rol(self.rol_pe),
            {
                'codigo': 'OTHER_CODE',
                'es_sistema': True,
                'deprecated': True,
                'otro': 'valor',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.rol_pe.refresh_from_db()
        self.assertEqual(self.rol_pe.codigo, 'CUSTOM_PE')
        self.assertFalse(self.rol_pe.es_sistema)
        self.assertFalse(self.rol_pe.deprecated)

    def test_asignacion_rechaza_inexistentes_inactivas_duplicadas_y_no_soportadas(self):
        client = self.cliente(self.superuser)
        url = self.url_capacidades_rol(self.rol_pe)
        payloads = [
            ['accounts.no_existe'],
            [self.cap_inactiva.codigo],
            [self.cap_pe.codigo, self.cap_pe.codigo],
            [self.cap_pro.codigo],
            [self.cap_platform.codigo],
        ]
        for codigos in payloads:
            with self.subTest(codigos=codigos):
                response = client.put(
                    url, {'capability_codes': codigos}, format='json',
                )
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_asignacion_es_atomica_si_un_codigo_es_invalido(self):
        originales = set(
            self.rol_pe.capacidades.values_list('codigo', flat=True),
        )
        response = self.cliente(self.superuser).put(
            self.url_capacidades_rol(self.rol_pe),
            {
                'capability_codes': [
                    self.cap_poa.codigo,
                    'sis_poa.f3b2a.no_existe',
                ],
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            set(self.rol_pe.capacidades.values_list('codigo', flat=True)),
            originales,
        )
