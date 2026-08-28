"""Integration contract for the read-only V2 effective-access preview."""
import json
from datetime import date

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import AlcanceOrganizacional, Capacidad, Rol, Usuario
from apps.gestion.models import GestionFiscal
from apps.organizacion.models import TipoUnidad, UnidadOrganizacional

PASSWORD = 'Clave-Preview.Segura.2026'


class AccessPreviewV2Tests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.gestion = GestionFiscal.objects.create(
            anio=2042, estado=GestionFiscal.Estado.PREPARACION,
        )
        cls.otra_gestion = GestionFiscal.objects.create(
            anio=2043, estado=GestionFiscal.Estado.PREPARACION,
        )
        tipo = TipoUnidad.objects.create(codigo='PREVIEW', nombre='Preview', nivel=1)

        def unidad(codigo, padre=None, gestion=None):
            return UnidadOrganizacional.objects.create(
                codigo=codigo, nombre=f'Unidad {codigo}', tipo=tipo, padre=padre,
                gestion=gestion or cls.gestion,
                fecha_vigencia_desde=date(2042, 1, 1),
            )

        cls.raiz = unidad('PV-ROOT')
        cls.unidad = unidad('PV-UO', cls.raiz)
        cls.hija = unidad('PV-CHILD', cls.unidad)

        def capacidad(codigo, nombre):
            obj, _ = Capacidad.objects.get_or_create(
                codigo=codigo,
                defaults={'nombre': nombre, 'sistema': codigo.split('.')[0]},
            )
            obj.nombre, obj.activo = nombre, True
            obj.save(update_fields=['nombre', 'activo'])
            return obj

        cls.cap_view = capacidad('sis_poa.poau.view', 'Ver POAU')
        cls.cap_edit = capacidad('sis_poa.poau.edit', 'Editar POAU')
        cls.cap_pad = capacidad('sis_pe.pad.view', 'Ver PAD')
        cls.cap_pro = capacidad('sis_pro.project.view', 'Ver proyectos')

        def rol(codigo, capacidades):
            obj = Rol.objects.create(codigo=codigo, nombre=codigo)
            obj.capacidades.set(capacidades)
            return obj

        cls.rol_actual = rol('PREVIEW_CURRENT', [cls.cap_view])
        cls.rol_propuesto = rol('PREVIEW_PROPOSED', [cls.cap_edit, cls.cap_pad])
        cls.rol_pe = rol('PREVIEW_PE', [cls.cap_pad])
        cls.rol_pro = rol('PREVIEW_SIS_PRO', [cls.cap_pro])
        cls.admin = Usuario.objects.create_superuser(
            email='preview-admin@test.gob.bo', password=PASSWORD,
        )
        cls.sin_capacidad = Usuario.objects.create_user(
            email='preview-no-access@test.gob.bo', password=PASSWORD,
        )
        cls.objetivo = Usuario.objects.create_user(
            email='preview-target@test.gob.bo', password=PASSWORD,
        )
        cls.objetivo.roles.set([cls.rol_actual, cls.rol_pro])
        for role in (cls.rol_actual, cls.rol_pro):
            AlcanceOrganizacional.objects.create(
                usuario=cls.objetivo, rol=role, unidad=cls.unidad,
                scope_type=AlcanceOrganizacional.SCOPE_SELF,
                fiscal_year=cls.gestion,
            )

    @staticmethod
    def api_client(user=None):
        client = APIClient()
        if user is not None:
            client.force_authenticate(user=user)
        return client

    def assignment(self, role=None, year=None):
        return {
            'role_code': (role or self.rol_propuesto).codigo,
            'organizational_unit_id': str(self.unidad.pk),
            'scope_type': AlcanceOrganizacional.SCOPE_DESCENDANTS,
            'fiscal_year_id': str((year or self.gestion).pk),
        }

    def preview(self, user, assignments=None, extra=None):
        params = {'user_id': str(self.objetivo.pk)}
        if assignments is not None:
            params['assignments'] = json.dumps(assignments)
        params.update(extra or {})
        return self.api_client(user).get(reverse('v2-admin-preview-access'), params)

    def test_requires_authentication_and_assignment_admin_capability(self):
        params = {'user_id': str(self.objetivo.pk)}
        url = reverse('v2-admin-preview-access')
        self.assertEqual(self.api_client().get(url, params).status_code, 401)
        self.assertEqual(self.preview(self.sin_capacidad).status_code, 403)

    def test_rejects_malformed_missing_incompatible_and_forbidden_inputs(self):
        missing = '00000000-0000-0000-0000-000000000000'
        cases = [
            (None, {'user_id': 'not-a-uuid'}),
            ([{**self.assignment(), 'organizational_unit_id': 'bad-uuid'}], None),
            ([{**self.assignment(), 'organizational_unit_id': missing}], None),
            ([{**self.assignment(), 'fiscal_year_id': missing}], None),
            ([self.assignment(year=self.otra_gestion)], None),
            ([self.assignment(role=self.rol_pro)], None),
            ([], {'unexpected': 'value'}),
        ]
        for assignments, extra in cases:
            with self.subTest(assignments=assignments, extra=extra):
                response = self.preview(self.admin, assignments, extra)
                self.assertEqual(response.status_code, 400, response.data)

    def test_empty_proposal_returns_current_unpaginated_effective_access(self):
        response = self.preview(self.admin, [])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data), {'capabilities', 'effective_uos', 'modules'})
        self.assertFalse({'results', 'count'} & set(response.data))
        self.assertEqual(
            [item['codigo'] for item in response.data['capabilities']],
            [self.cap_view.codigo],
        )
        self.assertEqual(response.data['effective_uos'][0]['codigo'], self.unidad.codigo)
        capability = response.data['capabilities'][0]
        self.assertEqual(set(capability), {'codigo', 'nombre', 'sistema', 'modulo'})
        self.assertEqual(capability['modulo'], 'poau')
        self.assertEqual(response.data['modules'], [
            {'codigo': 'poau', 'sistema': 'sis_poa', 'visible': True},
        ])

    def test_preview_excludes_sis_pro_from_every_public_field(self):
        response = self.preview(self.admin)
        self.assertEqual(response.status_code, 200)
        serialized = json.dumps(response.data)
        self.assertNotIn('sis_pro', serialized)
        self.assertNotIn('sis-pro', serialized)
        self.assertNotIn(self.cap_pro.codigo, serialized)

    def test_hypothetical_preview_does_not_persist_assignments(self):
        role_ids = set(self.objetivo.roles.values_list('pk', flat=True))
        scope_rows = list(self.objetivo.alcances_organizacionales.values_list(
            'pk', 'rol_id', 'unidad_id', 'scope_type', 'fiscal_year_id',
        ))
        response = self.preview(self.admin, [self.assignment()])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(self.objetivo.roles.values_list('pk', flat=True)), role_ids)
        self.assertEqual(list(
            self.objetivo.alcances_organizacionales.values_list(
                'pk', 'rol_id', 'unidad_id', 'scope_type', 'fiscal_year_id',
            )
        ), scope_rows)

    def test_preview_matches_effective_access_after_production_assignment(self):
        assignments = [self.assignment()]
        preview = self.preview(self.admin, assignments)
        self.assertEqual(preview.status_code, 200)
        save = self.api_client(self.admin).put(
            reverse('v2-admin-user-assignments', kwargs={'pk': self.objetivo.pk}),
            {'assignments': assignments}, format='json',
        )
        self.assertEqual(save.status_code, 200)
        persisted = self.preview(self.admin, [])
        self.assertEqual(persisted.status_code, 200)
        self.assertEqual(preview.data, persisted.data)
        self.assertEqual(
            [item['codigo'] for item in preview.data['effective_uos']],
            [self.hija.codigo, self.unidad.codigo],
        )

    def test_yearless_sis_pe_preview_matches_saved_access(self):
        assignment = self.assignment(role=self.rol_pe)
        assignment['scope_type'] = AlcanceOrganizacional.SCOPE_SELF
        assignment['fiscal_year_id'] = None

        preview = self.preview(self.admin, [assignment])
        self.assertEqual(preview.status_code, status.HTTP_200_OK, preview.data)
        save = self.api_client(self.admin).put(
            reverse('v2-admin-user-assignments', kwargs={'pk': self.objetivo.pk}),
            {'assignments': [assignment]}, format='json',
        )
        self.assertEqual(save.status_code, status.HTTP_200_OK, save.data)
        persisted = self.preview(self.admin, [])

        self.assertEqual(persisted.status_code, status.HTTP_200_OK)
        self.assertEqual(preview.data, persisted.data)
        self.assertIsNone(
            self.objetivo.alcances_organizacionales.get(rol=self.rol_pe)
            .fiscal_year_id
        )
