"""V2 ETL contract for POAU physical programming."""

import io
from datetime import date
from unittest.mock import patch

import openpyxl
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import AlcanceOrganizacional, Capacidad, Rol, Usuario
from apps.articulacion.models import (
    AccionPOA,
    ActividadPOAU,
    ImportacionProgramacionFisica,
    OperacionPOAU,
    ProductoPEI,
    ResultadoPEI,
    TareaPOAU,
)
from apps.articulacion.poau_importer import (
    ImportacionError,
    apply_preview,
    create_preview,
    download_google_sheet,
)
from apps.catalogos.models import TipoOperacion, UnidadMedida
from apps.gestion.testing import habilitar_gestion_para_tests
from apps.organizacion.models import TipoUnidad, UnidadOrganizacional


HEADERS = [
    'NIVEL', 'CÓDIGO UNIDAD', 'CÓDIGO ACCIÓN',
    'CÓDIGO OPERACIÓN', 'OPERACIÓN', 'CÓDIGO ACTIVIDAD', 'ACTIVIDAD',
    'CÓDIGO TAREA', 'TAREA', 'TIPO OPERACIÓN', 'INDICADOR', 'FÓRMULA',
    'UNIDAD DE MEDIDA', 'META', 'FECHA INICIO', 'FECHA FINAL', 'RESPONSABLE',
    'ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO',
    'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE',
    'TOTAL ANUAL',
]

REAL_LIKE_HEADERS = [
    'UNIDADES', 'Código codificación unidades',
    'ACCIÓN INSTITUCIONAL ESPECÍFICA (PEI)',
    'Acción de corto plazo gestión 2027 / Producto institucional anual',
    'OPERACIONES (PRODUCTO INTERMEDIO)', 'ACTIVIDADES', 'TAREAS ESPECÍFICAS',
    'TIPO DE OPERACIÓN', 'INDICADOR', 'FÓRMULA', 'UNIDAD DE MEDIDA', 'META',
    'FECHA INICIO', 'FECHA FINAL', 'RESPONSABLE',
    'ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO',
    'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE',
    'TOTAL ANUAL',
]


def workbook_bytes(rows, headers=HEADERS, sheet='POAU', header_row=1):
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = sheet
    for _ in range(header_row - 1):
        worksheet.append(['PROGRAMACIÓN FÍSICA POAU'])
    worksheet.append(headers)
    for row in rows:
        worksheet.append([row.get(header) for header in headers])
    output = io.BytesIO()
    workbook.save(output)
    workbook.close()
    return output.getvalue()


def physical_row(level, **values):
    row = {
        'NIVEL': level,
        'META': 1,
        'FECHA INICIO': '2027-01-01',
        'FECHA FINAL': '2027-12-31',
        'ENERO': 1,
        'TOTAL ANUAL': 1,
    }
    for month in HEADERS[18:29]:
        row[month] = 0
    row.update(values)
    return row


class PoauImportBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.gestion = habilitar_gestion_para_tests(2027)
        unit_type = TipoUnidad.objects.create(
            codigo='ETL', nombre='Unidad ETL', nivel=1,
        )
        cls.unit = UnidadOrganizacional.objects.create(
            codigo='UO-ETL', nombre='Unidad importadora', tipo=unit_type,
            gestion=cls.gestion, fecha_vigencia_desde=date(2027, 1, 1),
        )
        result = ResultadoPEI.objects.create(
            codigo_resultado='ETL.01', denominacion='Resultado ETL',
            cod_entidad='01', entidad='GAMS', vigencia_desde=2026,
            vigencia_hasta=2030,
        )
        product = ProductoPEI.objects.create(
            codigo_producto='ETL.01.01', denominacion='Producto ETL',
            resultado_pei=result,
        )
        cls.action = AccionPOA.objects.create(
            codigo_accion='ACP-ETL', denominacion='Acción ETL',
            producto_pei=product, gestion=2027, unidad_responsable=cls.unit,
        )
        cls.operation = OperacionPOAU.objects.create(
            codigo_operacion='ACP-ETL.1', correlativo=1, segmento='001',
            denominacion='Operación anterior', tipo_operacion='Funcionamiento',
            unidad_medida='Porcentaje', accion_poa=cls.action,
            meta_anual=1, programacion_mensual={'enero': '1'},
        )
        cls.activity = ActividadPOAU.objects.create(
            codigo_actividad='ACP-ETL.1.1', correlativo=1, segmento='001',
            denominacion='Actividad anterior', unidad_medida='Porcentaje',
            operacion=cls.operation, meta_anual=1,
            programacion_mensual={'enero': '1'},
        )
        cls.task = TareaPOAU.objects.create(
            codigo_tarea='ACP-ETL.1.1.1', correlativo=1, segmento='001',
            denominacion='Tarea anterior', actividad=cls.activity, metas=1,
            programacion_mensual={'enero': '1'},
        )
        UnidadMedida.objects.create(
            codigo='PORC', denominacion='Porcentaje', gestion=cls.gestion,
            fecha_vigencia_desde=date(2027, 1, 1),
        )
        TipoOperacion.objects.create(
            codigo='FUNC', denominacion='Funcionamiento', gestion=cls.gestion,
            fecha_vigencia_desde=date(2027, 1, 1),
        )
        capability, _ = Capacidad.objects.get_or_create(
            codigo='sis_poa.poau.edit',
            defaults={'nombre': 'Editar POAU', 'sistema': 'sis-poa'},
        )
        role = Rol.objects.create(codigo='ETL-POAU', nombre='Importador POAU')
        role.capacidades.add(capability)
        cls.user = Usuario.objects.create_user(
            email='etl-poau@test.gob.bo', password='Clave.ETL.2027',
        )
        cls.user.roles.add(role)
        AlcanceOrganizacional.objects.create(
            usuario=cls.user, unidad=cls.unit, rol=role,
            scope_type=AlcanceOrganizacional.SCOPE_SELF,
            fiscal_year=cls.gestion,
        )

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.query = f'?gestion_id={self.gestion.id}'

    def rows(self, duplicate=False, include_new=False):
        rows = [
            physical_row(
                'operacion', **{
                    'CÓDIGO UNIDAD': 'UO-ETL', 'CÓDIGO ACCIÓN': 'ACP-ETL',
                    'CÓDIGO OPERACIÓN': 'ACP-ETL.1', 'OPERACIÓN': 'Operación nueva',
                    'TIPO OPERACIÓN': 'FUNC', 'INDICADOR': 'Avance',
                    'UNIDAD DE MEDIDA': 'PORC',
                },
            ),
            physical_row(
                'actividad', **{
                    'CÓDIGO ACTIVIDAD': 'ACP-ETL.1.1', 'ACTIVIDAD': 'Actividad nueva',
                    'UNIDAD DE MEDIDA': 'PORC',
                },
            ),
            physical_row(
                'tarea', **{
                    'CÓDIGO TAREA': 'ACP-ETL.1.1.1', 'TAREA': 'Tarea nueva',
                    'RESPONSABLE': 'Responsable ETL',
                },
            ),
        ]
        if duplicate:
            rows.append(dict(rows[-1]))
        if include_new:
            rows.append(physical_row(
                'tarea', **{
                    'CÓDIGO TAREA': 'ACP-ETL.1.1.2', 'TAREA': 'Tarea adicional',
                    'RESPONSABLE': 'Responsable ETL',
                },
            ))
        return rows

    def preview_excel(self, rows=None, content=None, action_code=''):
        content = content or workbook_bytes(rows or self.rows())
        data = {
            'source_type': 'excel', 'unidad_codigo': self.unit.codigo,
            'sheet_name': 'POAU',
            'file': SimpleUploadedFile(
                'poau.xlsx', content,
                content_type=(
                    'application/vnd.openxmlformats-officedocument.'
                    'spreadsheetml.sheet'
                ),
            ),
        }
        if action_code:
            data['accion_codigo'] = action_code
        return self.client.post(
            reverse('v2-poau-imports-preview') + self.query,
            data,
            format='multipart',
        )


class PoauImportPreviewTests(PoauImportBase):
    def test_excel_preview_is_read_only_and_does_not_store_bytes(self):
        response = self.preview_excel()
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['estado'], 'VALIDO')
        self.assertEqual(response.data['resumen']['filas_validas'], 3)
        self.operation.refresh_from_db()
        self.assertEqual(self.operation.denominacion, 'Operación anterior')
        preview = ImportacionProgramacionFisica.objects.get(pk=response.data['id'])
        self.assertFalse(hasattr(preview, 'archivo'))
        self.assertEqual(len(preview.fuente_sha256), 64)

    @patch('apps.articulacion.views_poau_import.download_google_sheet')
    def test_google_sheets_uses_same_preview_pipeline(self, download):
        download.return_value = (workbook_bytes(self.rows()), 'Google test', '123')
        response = self.client.post(
            reverse('v2-poau-imports-preview') + self.query,
            {
                'source_type': 'google_sheets',
                'unidad_codigo': self.unit.codigo,
                'google_url': (
                    'https://docs.google.com/spreadsheets/d/'
                    '1e1G1bYXn2JOHKOpBfxncai5eUos9U-l88SdRvgLPEAI/edit?gid=123'
                ),
                'sheet_name': 'POAU',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['origen'], 'google_sheets')

    def test_google_sheets_rejects_non_google_hosts_before_network_access(self):
        with self.assertRaises(ImportacionError):
            download_google_sheet(
                'https://docs.google.com.attacker.example/spreadsheets/d/'
                '1e1G1bYXn2JOHKOpBfxncai5eUos9U-l88SdRvgLPEAI/edit?gid=123',
            )

    def test_duplicate_rows_make_preview_invalid_and_block_apply(self):
        response = self.preview_excel(self.rows(duplicate=True))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['estado'], 'INVALIDO')
        self.assertTrue(any(error['codigo'] == 'duplicate' for error in response.data['errores']))
        apply_response = self.client.post(
            reverse('v2-poau-imports-apply', args=[response.data['id']]) + self.query,
            {}, format='json',
        )
        self.assertEqual(apply_response.status_code, 400)

    def test_missing_month_column_is_a_structure_error(self):
        headers = [header for header in HEADERS if header != 'DICIEMBRE']
        response = self.preview_excel(content=workbook_bytes(self.rows(), headers=headers))
        self.assertEqual(response.status_code, 400)
        self.assertIn('Faltan columnas mensuales', str(response.data))

    def test_real_sheet_headers_on_row_two_use_explicit_action_fallback(self):
        rows = [
            {
                'Código codificación unidades': 'UO-ETL',
                'Acción de corto plazo gestión 2027 / Producto institucional anual': (
                    'Acción ETL'
                ),
                'OPERACIONES (PRODUCTO INTERMEDIO)': 'Operación nueva',
                'TIPO DE OPERACIÓN': 'FUNC', 'UNIDAD DE MEDIDA': 'PORC',
                'META': 1, 'FECHA INICIO': '2027-01-01',
                'FECHA FINAL': '2027-12-31', 'ENERO': 1,
                'TOTAL ANUAL': 1,
            },
            {
                'ACTIVIDADES': 'Actividad nueva', 'UNIDAD DE MEDIDA': 'PORC',
                'META': 1, 'FECHA INICIO': '2027-01-01',
                'FECHA FINAL': '2027-12-31', 'ENERO': 1,
                'TOTAL ANUAL': 1,
            },
            {
                'TAREAS ESPECÍFICAS': 'Tarea nueva',
                'RESPONSABLE': 'Responsable ETL', 'META': 1,
                'FECHA INICIO': '2027-01-01', 'FECHA FINAL': '2027-12-31',
                'ENERO': 1, 'TOTAL ANUAL': 1,
            },
        ]
        content = workbook_bytes(
            rows, headers=REAL_LIKE_HEADERS, header_row=2,
        )

        response = self.preview_excel(
            content=content, action_code=self.action.codigo_accion,
        )

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['estado'], 'VALIDO')
        self.assertEqual(response.data['resumen']['filas_validas'], 3)
        self.assertEqual(response.data['filas'][0]['fila'], 3)
        self.assertTrue(all(
            row['accion_codigo'] == self.action.codigo_accion
            for row in response.data['filas']
        ))

    def test_real_sheet_without_unit_code_header_uses_selected_unit(self):
        headers = [
            header for header in REAL_LIKE_HEADERS
            if header != 'Código codificación unidades'
        ]
        row = {
            'OPERACIONES (PRODUCTO INTERMEDIO)': 'Operación nueva',
            'TIPO DE OPERACIÓN': 'FUNC',
            'UNIDAD DE MEDIDA': 'PORC',
            'META': 1,
            'FECHA INICIO': '2027-01-01',
            'FECHA FINAL': '2027-12-31',
            'ENERO': 1,
            'TOTAL ANUAL': 1,
        }
        content = workbook_bytes([row], headers=headers, header_row=2)

        response = self.preview_excel(
            content=content, action_code=self.action.codigo_accion,
        )

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['estado'], 'VALIDO')
        self.assertEqual(response.data['filas'][0]['unidad_codigo'], self.unit.codigo)

    def test_explicit_conflicting_unit_code_remains_invalid(self):
        row = {
            'Código codificación unidades': 'UO-OTRA',
            'OPERACIONES (PRODUCTO INTERMEDIO)': 'Operación nueva',
            'TIPO DE OPERACIÓN': 'FUNC',
            'UNIDAD DE MEDIDA': 'PORC',
            'META': 1,
            'FECHA INICIO': '2027-01-01',
            'FECHA FINAL': '2027-12-31',
            'ENERO': 1,
            'TOTAL ANUAL': 1,
        }
        content = workbook_bytes(
            [row], headers=REAL_LIKE_HEADERS, header_row=2,
        )

        response = self.preview_excel(
            content=content, action_code=self.action.codigo_accion,
        )

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['estado'], 'INVALIDO')
        self.assertTrue(any(
            error['campo'] == 'unidad_codigo'
            and 'no a UO-ETL' in error['mensaje']
            for error in response.data['errores']
        ))

    def test_real_sheet_accepts_final_header_and_percentage_meta(self):
        headers = [
            'FINAL' if header == 'FECHA FINAL' else header
            for header in REAL_LIKE_HEADERS
        ]
        row = {
            'Código codificación unidades': 'UO-ETL',
            'OPERACIONES (PRODUCTO INTERMEDIO)': 'Operación porcentual',
            'TIPO DE OPERACIÓN': 'FUNC',
            'UNIDAD DE MEDIDA': 'PORC',
            'META': '100 %',
            'FECHA INICIO': '2027-01-01',
            'FINAL': '2027-12-31',
            'ENERO': 100,
            'TOTAL ANUAL': 100,
        }
        content = workbook_bytes(
            [row], headers=headers, header_row=2,
        )

        response = self.preview_excel(
            content=content, action_code=self.action.codigo_accion,
        )

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['estado'], 'VALIDO')
        self.assertEqual(response.data['filas'][0]['meta'], '100')
        self.assertEqual(response.data['filas'][0]['fecha_fin'], '2027-12-31')

    def test_real_sheet_with_empty_months_remains_invalid(self):
        row = {
            'Código codificación unidades': 'UO-ETL',
            'OPERACIONES (PRODUCTO INTERMEDIO)': 'Operación sin meses',
            'TIPO DE OPERACIÓN': 'FUNC',
            'UNIDAD DE MEDIDA': 'PORC',
        }
        content = workbook_bytes(
            [row], headers=REAL_LIKE_HEADERS, header_row=2,
        )

        response = self.preview_excel(
            content=content, action_code=self.action.codigo_accion,
        )

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['estado'], 'INVALIDO')
        self.assertTrue(any(
            error['campo'] == 'programacion_mensual'
            for error in response.data['errores']
        ))
        self.assertTrue(all(
            value is None
            for value in response.data['filas'][0]['programacion_mensual'].values()
        ))

    def test_real_sheet_without_explicit_action_fails_clearly(self):
        row = {
            'Código codificación unidades': 'UO-ETL',
            'OPERACIONES (PRODUCTO INTERMEDIO)': 'Operación nueva',
            'TIPO DE OPERACIÓN': 'FUNC', 'UNIDAD DE MEDIDA': 'PORC',
            'ENERO': 1, 'TOTAL ANUAL': 1,
        }
        content = workbook_bytes(
            [row], headers=REAL_LIKE_HEADERS, header_row=2,
        )

        response = self.preview_excel(content=content)

        self.assertEqual(response.status_code, 400)
        self.assertIn('Acción POA objetivo', str(response.data))

    def test_explicit_action_must_belong_to_unit_and_year(self):
        content = workbook_bytes(
            [{
                'Código codificación unidades': 'UO-ETL',
                'OPERACIONES (PRODUCTO INTERMEDIO)': 'Operación nueva',
                'ENERO': 1, 'TOTAL ANUAL': 1,
            }],
            headers=REAL_LIKE_HEADERS,
            header_row=2,
        )

        response = self.preview_excel(
            content=content, action_code='ACP-DE-OTRA-UNIDAD',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('no pertenece a la unidad y gestión', str(response.data))


class PoauImportApplyTests(PoauImportBase):
    def test_apply_updates_in_place_and_creates_missing_rows(self):
        response = self.preview_excel(self.rows(include_new=True))
        operation_id = self.operation.id
        task_id = self.task.id
        applied = self.client.post(
            reverse('v2-poau-imports-apply', args=[response.data['id']]) + self.query,
            {}, format='json',
        )
        self.assertEqual(applied.status_code, 200, applied.data)
        self.operation.refresh_from_db()
        self.task.refresh_from_db()
        self.assertEqual(self.operation.id, operation_id)
        self.assertEqual(self.task.id, task_id)
        self.assertEqual(self.operation.denominacion, 'Operación nueva')
        self.assertEqual(self.task.denominacion, 'Tarea nueva')
        self.assertTrue(TareaPOAU.objects.filter(codigo_tarea='ACP-ETL.1.1.2').exists())
        self.assertEqual(applied.data['resultado']['creados'], 1)

    def test_write_failure_rolls_back_all_changes(self):
        content = workbook_bytes(self.rows())
        request = type('Request', (), {'user': self.user, 'query_params': {}})()
        preview = create_preview(
            request=request, origin='excel', unit_code=self.unit.codigo,
            content=content, source_name='rollback.xlsx', sheet_name='POAU',
        )
        original_save = TareaPOAU.save

        def failing_save(instance, *args, **kwargs):
            if instance.pk == self.task.pk:
                raise RuntimeError('injected failure')
            return original_save(instance, *args, **kwargs)

        with patch.object(TareaPOAU, 'save', failing_save):
            with self.assertRaises(RuntimeError):
                apply_preview(preview.id, self.user)
        self.operation.refresh_from_db()
        preview.refresh_from_db()
        self.assertEqual(self.operation.denominacion, 'Operación anterior')
        self.assertEqual(preview.estado, 'VALIDO')

    def test_approved_record_blocks_replacement_without_mutation(self):
        self.task.estado = 'APROBADO'
        self.task.save(update_fields=['estado'])
        response = self.preview_excel()
        applied = self.client.post(
            reverse('v2-poau-imports-apply', args=[response.data['id']]) + self.query,
            {}, format='json',
        )
        self.assertEqual(applied.status_code, 400)
        self.operation.refresh_from_db()
        self.assertEqual(self.operation.denominacion, 'Operación anterior')
