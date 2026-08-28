"""Tests F3b2b: asignaciones atómicas de roles y alcances por usuario."""

from datetime import date

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import (
    AlcanceOrganizacional,
    Capacidad,
    Rol,
    Usuario,
)
from apps.gestion.models import GestionFiscal
from apps.organizacion.models import (
    AsignacionUsuarioUnidad,
    TipoUnidad,
    UnidadOrganizacional,
)


PASSWORD = 'Clave-Assignments.Segura.2026'
ADMIN_CAPABILITIES = [
    'accounts.alcance.view',
    'accounts.alcance.assign',
]


class F3b2bTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.gestion = GestionFiscal.objects.create(
            anio=2036, estado=GestionFiscal.Estado.PREPARACION,
        )
        cls.otra_gestion = GestionFiscal.objects.create(
            anio=2037, estado=GestionFiscal.Estado.PREPARACION,
        )
        tipo = TipoUnidad.objects.create(
            codigo='F3B2B', nombre='Tipo F3b2b', nivel=1,
        )

        def unidad(codigo, padre=None, gestion=None):
            return UnidadOrganizacional.objects.create(
                codigo=codigo,
                nombre=codigo,
                tipo=tipo,
                padre=padre,
                gestion=gestion or cls.gestion,
                fecha_vigencia_desde=date(2036, 1, 1),
            )

        cls.raiz = unidad('F3B2B-ROOT')
        cls.secretaria = unidad('F3B2B-SEC', cls.raiz)
        cls.unidad_pe = unidad('F3B2B-PE', cls.secretaria)
        cls.unidad_pe_2 = unidad('F3B2B-PE2', cls.secretaria)
        cls.unidad_poa = unidad('F3B2B-POA', cls.secretaria)
        cls.raiz_otra = unidad('F3B2B-ROOT2', gestion=cls.otra_gestion)

        def capacidad(codigo, *, activo=True):
            obj, _ = Capacidad.objects.get_or_create(
                codigo=codigo,
                defaults={
                    'nombre': codigo,
                    'sistema': codigo.split('.')[0],
                },
            )
            obj.activo = activo
            obj.save(update_fields=['activo'])
            return obj

        admin_caps = [capacidad(code) for code in ADMIN_CAPABILITIES]
        cap_pe = capacidad('sis_pe.f3b2b.manage')
        cap_poa = capacidad('sis_poa.f3b2b.manage')
        cap_pro = capacidad('sis_pro.f3b2b.manage')
        cap_accounts_elevated = capacidad('accounts.f3b2b.elevated')

        def rol(
            codigo,
            capacidades=(),
            *,
            es_sistema=False,
            activo=True,
            deprecated=False,
        ):
            obj, _ = Rol.objects.get_or_create(
                codigo=codigo,
                defaults={'nombre': codigo},
            )
            obj.nombre = codigo
            obj.es_sistema = es_sistema
            obj.activo = activo
            obj.deprecated = deprecated
            obj.save(update_fields=[
                'nombre', 'es_sistema', 'activo', 'deprecated',
            ])
            obj.capacidades.set(capacidades)
            return obj

        cls.rol_super_admin = rol(
            'SUPER_ADMIN', [cap_pe, cap_poa, *admin_caps], es_sistema=True,
        )
        cls.rol_jefe_pe = rol(
            'JEFE_PE', [cap_pe, *admin_caps], es_sistema=True,
        )
        cls.rol_jefe_poa = rol(
            'JEFE_POA', [cap_poa, *admin_caps], es_sistema=True,
        )
        cls.rol_secretario = rol(
            'SECRETARIO_MUNICIPAL', [cap_poa], es_sistema=True,
        )
        cls.rol_director = rol(
            'DIRECTOR', [cap_poa], es_sistema=True,
        )
        cls.rol_formulador = rol(
            'FORMULADOR_POAU', [cap_poa], es_sistema=True,
        )
        cls.rol_pe = rol('F3B2B_CUSTOM_PE', [cap_pe])
        cls.rol_pe_nuevo = rol('F3B2B_CUSTOM_PE_NEW', [cap_pe])
        cls.rol_poa = rol('F3B2B_CUSTOM_POA', [cap_poa])
        cls.rol_poa_nuevo = rol('F3B2B_CUSTOM_POA_NEW', [cap_poa])
        cls.rol_custom = rol('F3B2B_CUSTOM_SCOPES', [cap_pe])
        cls.rol_accounts = rol('F3B2B_CUSTOM_ACCOUNTS', [cap_accounts_elevated])
        cls.rol_pe_elevated = rol(
            'F3B2B_CUSTOM_PE_ELEVATED', [cap_pe, cap_accounts_elevated],
        )
        cls.rol_inactivo = rol(
            'F3B2B_INACTIVE', [cap_pe], activo=False,
        )
        cls.rol_deprecated = rol(
            'F3B2B_DEPRECATED', [cap_pe], deprecated=True,
        )
        cls.rol_pro = rol('F3B2B_SIS_PRO', [cap_pro])
        cls.rol_sin_capacidad = rol('F3B2B_NO_ADMIN', [cap_poa])

        def usuario(email, *roles, **kwargs):
            obj = Usuario.objects.create_user(
                email=email,
                password=PASSWORD,
                **kwargs,
            )
            obj.roles.set(roles)
            return obj

        cls.superuser = usuario(
            'f3b2b-superuser@test.gob.bo',
            is_staff=True,
            is_superuser=True,
        )
        cls.jefe_pe = usuario(
            'f3b2b-jefe-pe@test.gob.bo', cls.rol_jefe_pe,
        )
        cls.jefe_poa = usuario(
            'f3b2b-jefe-poa@test.gob.bo', cls.rol_jefe_poa,
        )
        cls.sin_capacidad = usuario(
            'f3b2b-sin-capacidad@test.gob.bo', cls.rol_sin_capacidad,
        )
        cls.usuario_mixto = usuario(
            'f3b2b-mixto@test.gob.bo', cls.rol_pe, cls.rol_poa,
            first_name='Usuario', last_name='Mixto',
        )
        cls.usuario_pe = usuario(
            'f3b2b-pe@test.gob.bo', cls.rol_pe,
        )
        cls.usuario_poa = usuario(
            'f3b2b-poa@test.gob.bo', cls.rol_poa,
        )
        cls.usuario_super_admin = usuario(
            'f3b2b-target-super@test.gob.bo', cls.rol_super_admin,
        )
        cls.usuario_pendiente = usuario(
            'f3b2b-pending@test.gob.bo',
            estado=Usuario.ESTADO_PENDIENTE,
            is_active=False,
        )

        cls.alcance_pe = AlcanceOrganizacional.objects.create(
            usuario=cls.usuario_mixto,
            rol=cls.rol_pe,
            unidad=cls.unidad_pe,
            scope_type=AlcanceOrganizacional.SCOPE_SELF,
            fiscal_year=cls.gestion,
        )
        cls.alcance_poa = AlcanceOrganizacional.objects.create(
            usuario=cls.usuario_mixto,
            rol=cls.rol_poa,
            unidad=cls.unidad_poa,
            scope_type=AlcanceOrganizacional.SCOPE_SELF,
            fiscal_year=cls.gestion,
        )
        AlcanceOrganizacional.objects.create(
            usuario=cls.usuario_pe,
            rol=cls.rol_pe,
            unidad=cls.unidad_pe,
            scope_type=AlcanceOrganizacional.SCOPE_SELF,
            fiscal_year=cls.gestion,
        )
        AlcanceOrganizacional.objects.create(
            usuario=cls.usuario_poa,
            rol=cls.rol_poa,
            unidad=cls.unidad_poa,
            scope_type=AlcanceOrganizacional.SCOPE_SELF,
            fiscal_year=cls.gestion,
        )

    @staticmethod
    def cliente(usuario=None):
        client = APIClient()
        if usuario is not None:
            client.force_authenticate(user=usuario)
        return client

    @staticmethod
    def url(usuario):
        return reverse(
            'v2-admin-user-assignments', kwargs={'pk': usuario.pk},
        )

    def assignment(
        self,
        role_code,
        unidad=None,
        scope_type=AlcanceOrganizacional.SCOPE_SELF,
        fiscal_year=True,
    ):
        return {
            'role_code': role_code,
            'organizational_unit_id': str((unidad or self.unidad_pe).pk),
            'scope_type': scope_type,
            'fiscal_year_id': (
                str(self.gestion.pk) if fiscal_year is True else fiscal_year
            ),
        }

    def put(self, actor, objetivo, assignments):
        return self.cliente(actor).put(
            self.url(objetivo), {'assignments': assignments}, format='json',
        )

    @staticmethod
    def active_scopes(usuario):
        return usuario.alcances_organizacionales.filter(
            activo=True,
        ).select_related('rol', 'unidad', 'fiscal_year')


class UserAssignmentsAuthorizationTests(F3b2bTestBase):
    def test_unauthenticated_get_and_put_return_401(self):
        client = self.cliente()
        self.assertEqual(
            client.get(self.url(self.usuario_mixto)).status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
        self.assertEqual(
            client.put(
                self.url(self.usuario_mixto), {'assignments': []}, format='json',
            ).status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_missing_capabilities_return_403(self):
        client = self.cliente(self.sin_capacidad)
        self.assertEqual(
            client.get(self.url(self.usuario_poa)).status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            client.put(
                self.url(self.usuario_poa), {'assignments': []}, format='json',
            ).status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_chiefs_receive_404_outside_their_domain(self):
        cases = [
            (self.jefe_pe, self.usuario_poa),
            (self.jefe_poa, self.usuario_pe),
            (self.jefe_pe, self.usuario_super_admin),
            (self.jefe_poa, self.usuario_super_admin),
        ]
        for actor, target in cases:
            with self.subTest(actor=actor.email, target=target.email):
                self.assertEqual(
                    self.cliente(actor).get(self.url(target)).status_code,
                    status.HTTP_404_NOT_FOUND,
                )
                self.assertEqual(
                    self.put(actor, target, []).status_code,
                    status.HTTP_404_NOT_FOUND,
                )

    def test_chiefs_cannot_change_their_own_assignments(self):
        for actor, role, unit in (
            (self.jefe_pe, self.rol_jefe_pe, self.unidad_pe),
            (self.jefe_poa, self.rol_jefe_poa, self.unidad_poa),
        ):
            AlcanceOrganizacional.objects.create(
                usuario=actor,
                rol=role,
                unidad=self.raiz,
                scope_type=AlcanceOrganizacional.SCOPE_GLOBAL,
                fiscal_year=self.gestion,
            )
            with self.subTest(actor=actor.email):
                response = self.put(actor, actor, [self.assignment(
                    role.codigo,
                    unit,
                    AlcanceOrganizacional.SCOPE_GLOBAL,
                )])
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class UserAssignmentsReplacementTests(F3b2bTestBase):
    def test_get_returns_f3b1_roles_and_scopes(self):
        response = self.cliente(self.jefe_pe).get(self.url(self.usuario_mixto))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            {role['codigo'] for role in response.data['roles']},
            {self.rol_pe.codigo, self.rol_poa.codigo},
        )
        self.assertEqual(
            {scope['rol'] for scope in response.data['alcances']},
            {self.rol_pe.codigo, self.rol_poa.codigo},
        )

    def test_superuser_replaces_multiple_pe_and_poa_assignments(self):
        response = self.put(self.superuser, self.usuario_mixto, [
            self.assignment(self.rol_pe_nuevo.codigo, self.unidad_pe_2),
            self.assignment(
                self.rol_poa_nuevo.codigo,
                self.unidad_poa,
                AlcanceOrganizacional.SCOPE_DESCENDANTS,
            ),
            self.assignment(self.rol_accounts.codigo, self.unidad_pe),
        ])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            set(self.usuario_mixto.roles.values_list('codigo', flat=True)),
            {
                self.rol_pe_nuevo.codigo,
                self.rol_poa_nuevo.codigo,
                self.rol_accounts.codigo,
            },
        )
        self.assertEqual(
            {scope.rol.codigo for scope in self.active_scopes(self.usuario_mixto)},
            {
                self.rol_pe_nuevo.codigo,
                self.rol_poa_nuevo.codigo,
                self.rol_accounts.codigo,
            },
        )

    def test_jefe_pe_replaces_pe_and_preserves_poa(self):
        poa_scope_id = self.alcance_poa.pk
        response = self.put(self.jefe_pe, self.usuario_mixto, [
            self.assignment(self.rol_pe_nuevo.codigo, self.unidad_pe_2),
        ])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        scopes = self.active_scopes(self.usuario_mixto)
        self.assertFalse(scopes.filter(pk=self.alcance_pe.pk).exists())
        self.assertTrue(scopes.filter(pk=poa_scope_id).exists())
        self.assertEqual(
            set(self.usuario_mixto.roles.values_list('codigo', flat=True)),
            {self.rol_pe_nuevo.codigo, self.rol_poa.codigo},
        )

    def test_jefe_poa_replaces_poa_and_preserves_pe(self):
        pe_scope_id = self.alcance_pe.pk
        response = self.put(self.jefe_poa, self.usuario_mixto, [
            self.assignment(self.rol_poa_nuevo.codigo, self.unidad_poa),
        ])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        scopes = self.active_scopes(self.usuario_mixto)
        self.assertFalse(scopes.filter(pk=self.alcance_poa.pk).exists())
        self.assertTrue(scopes.filter(pk=pe_scope_id).exists())
        self.assertEqual(
            set(self.usuario_mixto.roles.values_list('codigo', flat=True)),
            {self.rol_pe.codigo, self.rol_poa_nuevo.codigo},
        )

    def test_put_does_not_change_user_lifecycle_fields(self):
        original = (
            self.usuario_mixto.estado,
            self.usuario_mixto.activo,
            self.usuario_mixto.is_active,
        )
        response = self.put(self.superuser, self.usuario_mixto, [
            self.assignment(self.rol_pe_nuevo.codigo),
        ])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.usuario_mixto.refresh_from_db()
        self.assertEqual(
            (
                self.usuario_mixto.estado,
                self.usuario_mixto.activo,
                self.usuario_mixto.is_active,
            ),
            original,
        )

    def test_formulator_create_update_delete_synchronizes_legacy_assignment(self):
        first = self.assignment(
            self.rol_formulador.codigo, self.unidad_pe,
        )
        response = self.put(self.superuser, self.usuario_mixto, [first])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(AsignacionUsuarioUnidad.objects.filter(
            usuario=self.usuario_mixto,
            unidad=self.unidad_pe,
            gestion=self.gestion,
            activo=True,
        ).exists())

        updated = self.assignment(
            self.rol_formulador.codigo, self.unidad_poa,
        )
        for _ in range(2):
            response = self.put(
                self.superuser, self.usuario_mixto, [updated],
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            AsignacionUsuarioUnidad.objects.filter(
                usuario=self.usuario_mixto,
                gestion=self.gestion,
                activo=True,
            ).count(),
            1,
        )
        self.assertTrue(AsignacionUsuarioUnidad.objects.filter(
            usuario=self.usuario_mixto,
            unidad=self.unidad_poa,
            gestion=self.gestion,
            activo=True,
        ).exists())

        response = self.put(self.superuser, self.usuario_mixto, [])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(AsignacionUsuarioUnidad.objects.filter(
            usuario=self.usuario_mixto,
            gestion=self.gestion,
            activo=True,
        ).exists())

    def test_formulator_delete_removes_migration_bridge_rows(self):
        self.usuario_mixto.roles.add(self.rol_formulador)
        AsignacionUsuarioUnidad.objects.create(
            usuario=self.usuario_mixto,
            unidad=self.unidad_pe,
            gestion=self.gestion,
        )
        AlcanceOrganizacional.objects.create(
            usuario=self.usuario_mixto,
            rol=None,
            unidad=self.unidad_pe,
            scope_type=AlcanceOrganizacional.SCOPE_SELF,
            fiscal_year=self.gestion,
        )

        response = self.put(self.superuser, self.usuario_mixto, [])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(AsignacionUsuarioUnidad.objects.filter(
            usuario=self.usuario_mixto, gestion=self.gestion,
        ).exists())
        self.assertFalse(AlcanceOrganizacional.objects.filter(
            usuario=self.usuario_mixto, rol__isnull=True,
            fiscal_year=self.gestion,
        ).exists())


class UserAssignmentsScopeTests(F3b2bTestBase):
    def test_all_six_system_roles_reject_a_contradictory_scope(self):
        cases = [
            (self.rol_super_admin, AlcanceOrganizacional.SCOPE_SELF),
            (self.rol_jefe_pe, AlcanceOrganizacional.SCOPE_SELF),
            (self.rol_jefe_poa, AlcanceOrganizacional.SCOPE_SELF),
            (self.rol_secretario, AlcanceOrganizacional.SCOPE_SELF),
            (self.rol_director, AlcanceOrganizacional.SCOPE_SELF),
            (self.rol_formulador, AlcanceOrganizacional.SCOPE_DESCENDANTS),
        ]
        for role, invalid_scope in cases:
            with self.subTest(role=role.codigo):
                response = self.put(self.superuser, self.usuario_mixto, [
                    self.assignment(role.codigo, scope_type=invalid_scope),
                ])
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_global_system_roles_are_normalized_to_root(self):
        for role in (
            self.rol_super_admin, self.rol_jefe_pe, self.rol_jefe_poa,
        ):
            with self.subTest(role=role.codigo):
                response = self.put(self.superuser, self.usuario_mixto, [
                    self.assignment(
                        role.codigo,
                        self.unidad_pe,
                        AlcanceOrganizacional.SCOPE_GLOBAL,
                    ),
                ])
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                scope = self.active_scopes(self.usuario_mixto).get(rol=role)
                self.assertEqual(scope.unidad_id, self.raiz.pk)

    def test_custom_role_accepts_each_scope_type(self):
        for scope_type in (
            AlcanceOrganizacional.SCOPE_SELF,
            AlcanceOrganizacional.SCOPE_DESCENDANTS,
            AlcanceOrganizacional.SCOPE_GLOBAL,
        ):
            with self.subTest(scope_type=scope_type):
                response = self.put(self.superuser, self.usuario_mixto, [
                    self.assignment(
                        self.rol_custom.codigo,
                        self.unidad_pe,
                        scope_type,
                    ),
                ])
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                scope = self.active_scopes(self.usuario_mixto).get(
                    rol=self.rol_custom,
                )
                self.assertEqual(scope.scope_type, scope_type)


class UserAssignmentsValidationTests(F3b2bTestBase):
    @staticmethod
    def assignment_state(usuario):
        return {
            'roles': tuple(usuario.roles.order_by('pk').values_list('pk', flat=True)),
            'scopes': tuple(
                usuario.alcances_organizacionales.order_by('pk').values_list(
                    'pk', 'rol_id', 'unidad_id', 'scope_type',
                    'fiscal_year_id', 'activo',
                )
            ),
            'legacy': tuple(
                usuario.asignaciones_unidad.order_by('pk').values_list(
                    'pk', 'unidad_id', 'gestion_id', 'activo',
                )
            ),
        }

    def assert_invalid_without_changes(self, assignment):
        original = self.assignment_state(self.usuario_mixto)
        response = self.put(self.superuser, self.usuario_mixto, [assignment])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.assignment_state(self.usuario_mixto), original)

    def test_rejects_missing_inactive_deprecated_and_sis_pro_roles(self):
        for role_code in (
            'F3B2B_MISSING',
            self.rol_inactivo.codigo,
            self.rol_deprecated.codigo,
            self.rol_pro.codigo,
        ):
            with self.subTest(role_code=role_code):
                self.assert_invalid_without_changes(self.assignment(role_code))

    def test_rejects_invalid_unit_and_fiscal_year(self):
        invalid_uuid = '00000000-0000-0000-0000-000000000000'
        invalid_unit = self.assignment(self.rol_pe.codigo)
        invalid_unit['organizational_unit_id'] = invalid_uuid
        invalid_year = self.assignment(self.rol_pe.codigo)
        invalid_year['fiscal_year_id'] = invalid_uuid
        mismatched_year = self.assignment(self.rol_pe.codigo)
        mismatched_year['fiscal_year_id'] = str(self.otra_gestion.pk)
        for assignment in (invalid_unit, invalid_year, mismatched_year):
            with self.subTest(assignment=assignment):
                self.assert_invalid_without_changes(assignment)

    def test_rejects_sis_poa_assignment_without_fiscal_year_before_writes(self):
        missing_year = self.assignment(self.rol_poa.codigo)
        missing_year.pop('fiscal_year_id')
        null_year = self.assignment(self.rol_poa.codigo, fiscal_year=None)

        for assignment in (missing_year, null_year):
            with self.subTest(assignment=assignment):
                self.assert_invalid_without_changes(assignment)

    def test_accepts_multiple_yearless_sis_pe_self_assignments(self):
        omitted = self.assignment(self.rol_pe_nuevo.codigo, self.unidad_pe)
        omitted.pop('fiscal_year_id')
        explicit_null = self.assignment(
            self.rol_pe_nuevo.codigo, self.unidad_poa, fiscal_year=None,
        )

        response = self.put(
            self.superuser, self.usuario_mixto, [omitted, explicit_null],
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        scopes = self.active_scopes(self.usuario_mixto).filter(
            rol=self.rol_pe_nuevo,
        )
        self.assertEqual(scopes.count(), 2)
        self.assertEqual(
            set(scopes.values_list('fiscal_year_id', flat=True)), {None},
        )

    def test_rejects_poau_unit_year_mismatch_without_any_write(self):
        assignment = self.assignment(
            self.rol_formulador.codigo,
            self.unidad_pe,
            fiscal_year=str(self.otra_gestion.pk),
        )
        self.assert_invalid_without_changes(assignment)

    def test_rejects_exact_and_semantically_overlapping_duplicates(self):
        exact = self.assignment(self.rol_custom.codigo)
        overlap_parent = self.assignment(
            self.rol_custom.codigo,
            self.secretaria,
            AlcanceOrganizacional.SCOPE_DESCENDANTS,
        )
        overlap_child = self.assignment(
            self.rol_custom.codigo,
            self.unidad_pe,
            AlcanceOrganizacional.SCOPE_SELF,
        )
        for assignments in ([exact, exact.copy()], [overlap_parent, overlap_child]):
            with self.subTest(assignments=assignments):
                response = self.put(
                    self.superuser, self.usuario_mixto, assignments,
                )
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_allows_same_role_and_year_on_distinct_nonoverlapping_units(self):
        response = self.put(self.superuser, self.usuario_mixto, [
            self.assignment(self.rol_custom.codigo, self.unidad_pe),
            self.assignment(self.rol_custom.codigo, self.unidad_poa),
        ])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.active_scopes(self.usuario_mixto).filter(
                rol=self.rol_custom,
            ).count(),
            2,
        )

    def test_rejects_second_formulator_self_unit_in_same_year(self):
        response = self.put(self.superuser, self.usuario_mixto, [
            self.assignment(self.rol_formulador.codigo, self.unidad_pe),
            self.assignment(self.rol_formulador.codigo, self.unidad_poa),
        ])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            self.active_scopes(self.usuario_mixto).count(),
            2,
        )

    def test_chief_cannot_assign_role_outside_authority(self):
        for role, unit in (
            (self.rol_poa_nuevo, self.unidad_poa),
            (self.rol_pe_elevated, self.unidad_pe),
        ):
            with self.subTest(role=role.codigo):
                response = self.put(self.jefe_pe, self.usuario_mixto, [
                    self.assignment(role.codigo, unit),
                ])
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_atomic_rollback_when_valid_item_accompanies_invalid_item(self):
        original_roles = set(
            self.usuario_mixto.roles.values_list('pk', flat=True),
        )
        original_scopes = set(
            self.active_scopes(self.usuario_mixto).values_list('pk', flat=True),
        )
        response = self.put(self.superuser, self.usuario_mixto, [
            self.assignment(self.rol_pe_nuevo.codigo, self.unidad_pe_2),
            self.assignment('F3B2B_MISSING', self.unidad_poa),
        ])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            set(self.usuario_mixto.roles.values_list('pk', flat=True)),
            original_roles,
        )
        self.assertEqual(
            set(self.active_scopes(self.usuario_mixto).values_list('pk', flat=True)),
            original_scopes,
        )

    def test_pending_user_is_rejected_by_get_and_put(self):
        client = self.cliente(self.superuser)
        self.assertEqual(
            client.get(self.url(self.usuario_pendiente)).status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        response = self.put(self.superuser, self.usuario_pendiente, [
            self.assignment(self.rol_pe.codigo),
        ])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.usuario_pendiente.refresh_from_db()
        self.assertEqual(self.usuario_pendiente.estado, Usuario.ESTADO_PENDIENTE)
        self.assertFalse(self.usuario_pendiente.activo)
        self.assertFalse(self.usuario_pendiente.is_active)
