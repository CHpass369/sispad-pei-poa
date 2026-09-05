"""V2 ETL contract for POAU physical programming."""

import io
from datetime import date
from decimal import Decimal
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
    VersionImportacionPOAU,
)
from apps.articulacion.poau_importer import (
    ImportacionError,
    apply_preview,
    create_preview,
    download_google_sheet,
)
from apps.catalogos.models import (
    ClasificadorInstitucional,
    FuenteFinanciamiento,
    ObjetoGasto,
    OrganismoFinanciador,
    TipoOperacion,
    UnidadMedida,
    VersionClasificador,
)
from apps.gestion.testing import habilitar_gestion_para_tests
from apps.organizacion.models import (
    DireccionAdministrativa,
    TipoUnidad,
    UnidadEjecutora,
    UnidadOrganizacional,
)
from apps.presupuesto.models import (
    ActividadPresupuestaria,
    AsignacionPresupuestariaUnidad,
    CategoriaProgramatica,
    ProgramaPresupuestario,
    ProyectoPresupuestario,
)
from apps.presupuesto.test_t4_asignaciones import crear_version


HEADERS = [
    'NIVEL', 'CÓDIGO UNIDAD',
    'ACCIÓN INSTITUCIONAL ESPECÍFICA (PEI)', 'ACCIÓN DE CORTO PLAZO',
    'CÓDIGO ACCIÓN',
    'CÓDIGO OPERACIÓN', 'OPERACIÓN', 'CÓDIGO ACTIVIDAD', 'ACTIVIDAD',
    'CÓDIGO TAREA', 'TAREA', 'TIPO OPERACIÓN', 'INDICADOR', 'FÓRMULA',
    'UNIDAD DE MEDIDA', 'LÍNEA BASE (2026)', 'META', 'META ACTUAL',
    '% PONDERACIÓN', 'CATEGORÍA PROGRAMÁTICA',
    'FECHA INICIO', 'FECHA FINAL', 'RESPONSABLE',
    'ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO',
    'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE',
    'TOTAL ANUAL',
]

MONTH_HEADERS = [
    'ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO',
    'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE',
]

REAL_LIKE_HEADERS = [
    'UNIDADES', 'Código codificación unidades',
    'ACCIÓN INSTITUCIONAL ESPECÍFICA (PEI)',
    'Acción de corto plazo gestión 2027 / Producto institucional anual',
    'OPERACIONES (PRODUCTO INTERMEDIO)', 'ACTIVIDADES', 'TAREAS ESPECÍFICAS',
    'TIPO DE OPERACIÓN', 'INDICADOR', 'FÓRMULA', 'UNIDAD DE MEDIDA',
    'LÍNEA BASE (2026)', 'META', 'META ACTUAL', '% PONDERACIÓN',
    'CATEGORÍA PROGRAMÁTICA',
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


def official_workbook_bytes(
    aie='Producto ETL', trailing_legacy_section=False, extra_categories=(),
):
    """Matriz con el layout oficial.

    `extra_categories` agrega una operación más por cada categoría, con la
    categoría escrita en la fila de la operación —que es donde la trae la
    matriz real: una acción de corto plazo agrupa operaciones financiadas
    desde categorías programáticas distintas.
    """
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = 'PROPUESTA POAU FINAL'
    row_one = [None] * 51
    row_one[0] = 'CODIFICACION DE UNIDADES'
    row_one[18] = 'FECHA'
    row_one[23] = 'CRONOGRAMA DE EJECUCIÓN'
    worksheet.append(row_one)
    worksheet.append([
        'PRO', 'SECRETARIA', 'DIRECCION', 'UNIDADES', 'CODIGO UNIDAD',
        'ACCIÓN INSTITUCIONAL ESPECIFICA (PEI) 2026-2030',
        'ACCIÓN DE CORTO PLAZO GESTIÓN 2027 (PRODUCTO INSTITUCIONAL ANUAL)',
        'CATEGORIA PROGRAMATICA', 'DENOMINACIÓN (CATEGORIA PROGRAMATICA)',
        'OPERACIONES', 'ACTIVIDADES', 'TAREAS ESPECIFICAS', 'INDICADOR',
        'FORMULA', 'UNIDAD DE MEDIDA', 'LINEA BASE (2026)',
        'ESTIMACION LINEA BASE (2027)', 'META 2027', 'INICIO', 'FINAL',
        '% PONDERACIÓN', 'UNIDAD ORGANIZACIONAL EJECUTORA',
        'RESPONSABLE REACP',
        'ENERO', None, 'FEBRERO', None, 'MARZO', None, 'ABRIL', None,
        'MAYO', None, 'JUNIO', None, 'JULIO', None, 'AGOSTO', None,
        'SEPTIEMBRE', None, 'OCTUBRE', None, 'NOVIEMBRE', None,
        'DICIEMBRE', None, 'TOTAL ANUAL', None, None,
        'MEDIO DE VERIFICACIÓN',
    ])
    subheaders = [None] * 51
    for column in range(23, 49, 2):
        subheaders[column] = 'PROGRAMADO'
        subheaders[column + 1] = 'EJECUTADO'
    subheaders[49] = '% AVANCE'
    worksheet.append(subheaders)

    unit = [None] * 51
    unit[3:6] = ['Unidad importadora', 'UO-ETL', aie]
    worksheet.append(unit)
    action = [None] * 51
    action[6:8] = ['Acción ETL importada', '000 0 001']
    worksheet.append(action)
    for level_column, name in (
        (9, 'Operación oficial'),
        (10, 'Actividad oficial'),
        (11, 'Tarea oficial'),
    ):
        row = [None] * 51
        row[level_column] = name
        row[12:15] = ['Avance físico', 'Ejecutado / programado', 'PORC']
        row[15:21] = [0.25, 0.50, 1, '2027-01-01', '2027-12-31', 25]
        row[22] = 'Responsable ETL'
        row[23] = 1
        for column in range(25, 47, 2):
            row[column] = 0
        row[47] = 1
        worksheet.append(row)
    for index, categoria in enumerate(extra_categories, start=2):
        row = [None] * 51
        row[7] = categoria
        row[9] = f'Operación oficial {index}'
        row[12:15] = ['Avance físico', 'Ejecutado / programado', 'PORC']
        row[15:21] = [0.25, 0.50, 1, '2027-01-01', '2027-12-31', 25]
        row[22] = 'Responsable ETL'
        row[23] = 1
        for column in range(25, 47, 2):
            row[column] = 0
        row[47] = 1
        worksheet.append(row)
    if trailing_legacy_section:
        legacy_header = [None] * 51
        legacy_header[5] = 'INDICADORES EXISTENTE'
        worksheet.append(legacy_header)
        legacy_row = [None] * 51
        legacy_row[9] = 'Operación legado'
        legacy_row[12:15] = ['Avance físico', 'Ejecutado / programado', 'PORC']
        legacy_row[15:21] = [0.25, 0.50, 1, '2027-01-01', '2027-12-31', 25]
        legacy_row[22] = 'Responsable ETL'
        worksheet.append(legacy_row)
    output = io.BytesIO()
    workbook.save(output)
    workbook.close()
    return output.getvalue()


def physical_row(level, **values):
    row = {
        'NIVEL': level,
        'CÓDIGO UNIDAD': 'UO-ETL',
        'ACCIÓN INSTITUCIONAL ESPECÍFICA (PEI)': 'Producto ETL',
        'ACCIÓN DE CORTO PLAZO': 'Acción ETL importada',
        'INDICADOR': 'Avance físico',
        'FÓRMULA': 'Ejecutado / programado',
        'UNIDAD DE MEDIDA': 'PORC',
        'LÍNEA BASE (2026)': 0.25,
        'META': 1,
        'META ACTUAL': 0.50,
        '% PONDERACIÓN': 25,
        'CATEGORÍA PROGRAMÁTICA': '000 0 001',
        'FECHA INICIO': '2027-01-01',
        'FECHA FINAL': '2027-12-31',
        'ENERO': 1,
        'TOTAL ANUAL': 1,
    }
    for month in MONTH_HEADERS[1:]:
        row[month] = 0
    row.update(values)
    return row


def crear_asignacion_presupuestaria(gestion, unidad, operacion):
    """Cadena mínima real para una `AsignacionPresupuestariaUnidad` de prueba.

    Reusa `crear_version` de `test_t4_asignaciones` en vez de reinventarla;
    el resto de la cadena de catálogos es exclusiva de este test porque
    `CategoriaProgramatica` exige entidad/da/ue/programa/proyecto/actividad
    reales y `full_clean()`-validados.
    """
    inicio = date(gestion.anio, 1, 1)
    entidad = ClasificadorInstitucional.objects.create(
        # CategoriaProgramatica.clean() exige entidad.codigo == '1312'.
        codigo='1312', denominacion='Entidad ETL', gestion=gestion,
        fecha_vigencia_desde=inicio,
    )
    da = DireccionAdministrativa.objects.create(
        codigo='DA-ETL', nombre='DA ETL', gestion=gestion,
        fecha_vigencia_desde=inicio,
    )
    ue = UnidadEjecutora.objects.create(
        codigo='UE-ETL', nombre='UE ETL', da=da, gestion=gestion,
        fecha_vigencia_desde=inicio,
    )
    programa = ProgramaPresupuestario.objects.create(
        codigo='ETL-PRG', nombre='Programa ETL', gestion=gestion.anio,
    )
    proyecto = ProyectoPresupuestario.objects.create(
        codigo='ETL-PRY', nombre='Proyecto ETL', programa=programa,
        gestion=gestion.anio,
    )
    actividad_presupuestaria = ActividadPresupuestaria.objects.create(
        codigo='ETL-ACT', nombre='Actividad presupuestaria ETL',
        proyecto=proyecto, gestion=gestion.anio,
    )
    categoria_version = crear_version(
        VersionClasificador.TIPO_CATEGORIA_PROGRAMATICA, gestion=gestion.anio,
    )
    categoria = CategoriaProgramatica.objects.create(
        version_clasificador=categoria_version, entidad=entidad, da=da, ue=ue,
        programa=programa, proyecto=proyecto, actividad=actividad_presupuestaria,
        codigo_fuente='1312-ETL|DA-ETL|UE-ETL|ETL-PRG|ETL-PRY|ETL-ACT',
        procedencia_normativa='Prueba ETL',
    )
    fuente = FuenteFinanciamiento.objects.create(
        # ANCHO_CODIGO_OFICIAL exige 2/3/5 dígitos exactos en fuente/organismo/objeto.
        codigo='20', denominacion='Fuente ETL', gestion=gestion,
        fecha_vigencia_desde=inicio,
        version_clasificador=crear_version(
            VersionClasificador.TIPO_FUENTE_FINANCIAMIENTO, gestion=gestion.anio,
        ),
    )
    organismo = OrganismoFinanciador.objects.create(
        codigo='210', denominacion='Organismo ETL', gestion=gestion,
        fecha_vigencia_desde=inicio,
        version_clasificador=crear_version(
            VersionClasificador.TIPO_ORGANISMO_FINANCIADOR, gestion=gestion.anio,
        ),
    )
    objeto = ObjetoGasto.objects.create(
        codigo='11210', denominacion='Objeto de gasto ETL', gestion=gestion,
        fecha_vigencia_desde=inicio, nivel=ObjetoGasto.NIVEL_DETALLE,
        version_clasificador=crear_version(
            VersionClasificador.TIPO_OBJETO_GASTO, gestion=gestion.anio,
        ),
    )
    return AsignacionPresupuestariaUnidad.objects.create(
        categoria_programatica=categoria, fuente=fuente, organismo=organismo,
        objeto_gasto=objeto, unidad=unidad, operacion=operacion,
        gestion=gestion.anio, monto_formulado=Decimal('1000.00'),
        monto_vigente=Decimal('900.00'), monto_ejecutado=Decimal('0'),
    )


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

    def preview_excel(self, rows=None, content=None, action_code='', sheet='POAU'):
        content = content or workbook_bytes(rows or self.rows())
        data = {
            'source_type': 'excel', 'unidad_codigo': self.unit.codigo,
            'sheet_name': sheet,
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
    def test_official_three_row_header_builds_complete_preview(self):
        response = self.preview_excel(
            content=official_workbook_bytes(), sheet='PROPUESTA POAU FINAL',
        )

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['estado'], 'VALIDO')
        self.assertEqual(response.data['resumen']['filas_validas'], 4)
        self.assertEqual(
            [row['nivel'] for row in response.data['filas']],
            ['accion', 'operacion', 'actividad', 'tarea'],
        )
        self.assertEqual(
            response.data['filas'][0]['producto_pei_codigo'],
            self.action.producto_pei.codigo_producto,
        )
        self.assertEqual(
            response.data['filas'][0]['categoria_programatica'], '000 0 001',
        )
        operation = response.data['filas'][1]
        self.assertEqual(operation['linea_base'], '0.25')
        self.assertEqual(operation['meta_actual'], '0.5')
        self.assertEqual(operation['ponderacion'], '25')

    def test_indicadores_existente_section_is_ignored(self):
        response = self.preview_excel(
            content=official_workbook_bytes(trailing_legacy_section=True),
            sheet='PROPUESTA POAU FINAL',
        )

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['estado'], 'VALIDO')
        self.assertEqual(response.data['resumen']['filas_validas'], 4)
        denominaciones = {
            row.get('operacion') or row.get('actividad') or row.get('tarea')
            for row in response.data['filas']
        }
        self.assertNotIn('Operación legado', denominaciones)

    def test_preview_returns_every_row_including_operations_past_row_100(self):
        """La vista previa no se recorta: el asistente pide el tipo de cada
        operación en su propia fila, así que una operación que no se serializa
        es una operación que nadie puede tipar."""
        rows = self.rows()
        for index in range(100):
            rows.append(physical_row(
                'tarea', **{
                    'CÓDIGO TAREA': f'ACP-ETL.1.1.R{index}',
                    'TAREA': f'Tarea de relleno {index}',
                    'RESPONSABLE': 'Responsable ETL',
                },
            ))
        rows.append(physical_row(
            'operacion', **{
                'CÓDIGO OPERACIÓN': 'ACP-ETL.2', 'OPERACIÓN': 'Operación tardía',
                'TIPO OPERACIÓN': 'FUNC', 'INDICADOR': 'Avance',
                'UNIDAD DE MEDIDA': 'PORC',
            },
        ))

        response = self.preview_excel(rows)

        self.assertEqual(response.status_code, 201, response.data)
        filas = response.data['filas']
        self.assertGreater(len(filas), 100)
        self.assertEqual(len(filas), response.data['resumen']['registros_preview'])
        operaciones = [row['operacion'] for row in filas if row['nivel'] == 'operacion']
        self.assertIn('Operación tardía', operaciones)

    def test_missing_unit_of_measure_is_a_warning_not_a_blocking_error(self):
        rows = self.rows()
        rows[0] = {**rows[0], 'UNIDAD DE MEDIDA': ''}
        response = self.preview_excel(rows)

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['estado'], 'VALIDO')
        warning = next(
            error for error in response.data['errores']
            if error['campo'] == 'unidad_medida'
        )
        self.assertEqual(warning['severidad'], 'advertencia')

    def test_ponderacion_over_100_is_a_warning_not_a_blocking_error(self):
        rows = self.rows()
        rows[0] = {**rows[0], '% PONDERACIÓN': 150}
        response = self.preview_excel(rows)

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['estado'], 'VALIDO')
        warning = next(
            error for error in response.data['errores']
            if error['campo'] == 'ponderacion'
        )
        self.assertEqual(warning['severidad'], 'advertencia')

    def test_fecha_fin_before_inicio_is_a_warning_not_a_blocking_error(self):
        rows = self.rows()
        rows[0] = {
            **rows[0], 'FECHA INICIO': '2027-12-31', 'FECHA FINAL': '2027-01-01',
        }
        response = self.preview_excel(rows)

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['estado'], 'VALIDO')
        warning = next(
            error for error in response.data['errores']
            if error['campo'] == 'fecha_fin'
        )
        self.assertEqual(warning['severidad'], 'advertencia')

    def test_excel_preview_is_read_only_and_does_not_store_bytes(self):
        response = self.preview_excel()
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['estado'], 'VALIDO')
        self.assertEqual(response.data['resumen']['filas_validas'], 4)
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

    def test_real_sheet_headers_on_row_two_build_complete_action_tree(self):
        rows = [
            {
                'Código codificación unidades': 'UO-ETL',
                'ACCIÓN INSTITUCIONAL ESPECÍFICA (PEI)': 'Producto ETL',
                'Acción de corto plazo gestión 2027 / Producto institucional anual': (
                    'Acción ETL importada'
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
                'RESPONSABLE': 'Responsable ETL',
                'UNIDAD DE MEDIDA': 'PORC', 'META': 1,
                'FECHA INICIO': '2027-01-01', 'FECHA FINAL': '2027-12-31',
                'ENERO': 1, 'TOTAL ANUAL': 1,
            },
        ]
        content = workbook_bytes(
            rows, headers=REAL_LIKE_HEADERS, header_row=2,
        )

        response = self.preview_excel(content=content)

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['estado'], 'VALIDO')
        self.assertEqual(response.data['resumen']['filas_validas'], 4)
        self.assertEqual(response.data['filas'][0]['fila'], 3)
        self.assertEqual(
            [row['nivel'] for row in response.data['filas']],
            ['accion', 'operacion', 'actividad', 'tarea'],
        )

    def test_real_sheet_without_unit_code_header_uses_selected_unit(self):
        headers = [
            header for header in REAL_LIKE_HEADERS
            if header != 'Código codificación unidades'
        ]
        row = {
            'ACCIÓN INSTITUCIONAL ESPECÍFICA (PEI)': 'Producto ETL',
            'Acción de corto plazo gestión 2027 / Producto institucional anual': (
                'Acción ETL importada'
            ),
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
            'ACCIÓN INSTITUCIONAL ESPECÍFICA (PEI)': 'Producto ETL',
            'Acción de corto plazo gestión 2027 / Producto institucional anual': (
                'Acción ETL importada'
            ),
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
            'ACCIÓN INSTITUCIONAL ESPECÍFICA (PEI)': 'Producto ETL',
            'Acción de corto plazo gestión 2027 / Producto institucional anual': (
                'Acción ETL importada'
            ),
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
        operation = next(
            row for row in response.data['filas'] if row['nivel'] == 'operacion'
        )
        self.assertEqual(operation['meta'], '100')
        self.assertEqual(operation['fecha_fin'], '2027-12-31')

    def test_real_sheet_with_empty_months_remains_invalid(self):
        row = {
            'Código codificación unidades': 'UO-ETL',
            'ACCIÓN INSTITUCIONAL ESPECÍFICA (PEI)': 'Producto ETL',
            'Acción de corto plazo gestión 2027 / Producto institucional anual': (
                'Acción ETL importada'
            ),
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
        self.assertEqual(response.data['estado'], 'VALIDO')
        self.assertTrue(any(
            error['campo'] == 'programacion_mensual'
            for error in response.data['errores']
        ))
        self.assertTrue(all(
            value == '0'
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

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['estado'], 'INVALIDO')
        self.assertTrue(any(
            error['campo'] == 'accion'
            for error in response.data['errores']
        ))

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
    def test_apply_creates_provisional_pei_reference_for_unknown_aie(self):
        aie = 'AIE ficticia pendiente de la matriz PEI'
        response = self.preview_excel(
            content=official_workbook_bytes(aie),
            sheet='PROPUESTA POAU FINAL',
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['estado'], 'VALIDO')

        applied = self.client.post(
            reverse('v2-poau-imports-apply', args=[response.data['id']]) + self.query,
            {
                'confirmation_code': self.unit.codigo,
                'operation_types': {'6': 'FUNC'},
            },
            format='json',
        )

        self.assertEqual(applied.status_code, 200, applied.data)
        product = ProductoPEI.objects.get(denominacion=aie)
        self.assertEqual(product.estado_codigo, 'provisional')
        self.assertTrue(
            AccionPOA.objects.filter(
                producto_pei=product,
                unidad_responsable=self.unit,
                estado='BORRADOR',
            ).exists()
        )

    def test_preview_keeps_one_category_per_operation(self):
        """La matriz real trae una categoría por operación, no una por acción.

        Antes se guardaba sólo en la acción y cada fila con categoría pisaba a
        la anterior: con ocho operaciones la acción terminaba con la última y
        las otras siete desaparecían sin ningún error.
        """
        response = self.preview_excel(
            content=official_workbook_bytes(
                extra_categories=('252 0 028', '252 0 009'),
            ),
            sheet='PROPUESTA POAU FINAL',
        )
        self.assertEqual(response.status_code, 201, response.data)

        filas = response.data['filas']
        operaciones = [f for f in filas if f['nivel'] == 'operacion']
        self.assertEqual(
            [f['categoria_programatica'] for f in operaciones],
            ['000 0 001', '252 0 028', '252 0 009'],
        )
        accion = next(f for f in filas if f['nivel'] == 'accion')
        self.assertEqual(accion['categoria_programatica'], '000 0 001')

    def test_apply_persists_the_category_of_each_operation(self):
        response = self.preview_excel(
            content=official_workbook_bytes(
                extra_categories=('252 0 028', '252 0 009'),
            ),
            sheet='PROPUESTA POAU FINAL',
        )
        applied = self.client.post(
            reverse('v2-poau-imports-apply', args=[response.data['id']]) + self.query,
            {
                'confirmation_code': self.unit.codigo,
                'operation_types': {'6': 'FUNC', '9': 'FUNC', '10': 'FUNC'},
            },
            format='json',
        )

        self.assertEqual(applied.status_code, 200, applied.data)
        categorias = dict(
            OperacionPOAU.objects.filter(
                accion_poa__unidad_responsable=self.unit,
            ).values_list('denominacion', 'categoria_programatica')
        )
        self.assertEqual(categorias, {
            'Operación oficial': '000 0 001',
            'Operación oficial 2': '252 0 028',
            'Operación oficial 3': '252 0 009',
        })

    def test_apply_replaces_complete_unit_tree(self):
        response = self.preview_excel(self.rows(include_new=True))
        operation_id = self.operation.id
        task_id = self.task.id
        applied = self.client.post(
            reverse('v2-poau-imports-apply', args=[response.data['id']]) + self.query,
            {'confirmation_code': self.unit.codigo}, format='json',
        )
        self.assertEqual(applied.status_code, 200, applied.data)
        self.assertFalse(OperacionPOAU.objects.filter(pk=operation_id).exists())
        self.assertFalse(TareaPOAU.objects.filter(pk=task_id).exists())
        self.assertTrue(OperacionPOAU.objects.filter(denominacion='Operación nueva').exists())
        self.assertTrue(TareaPOAU.objects.filter(denominacion='Tarea adicional').exists())
        action = AccionPOA.objects.get(denominacion='Acción ETL importada')
        operation = OperacionPOAU.objects.get(denominacion='Operación nueva')
        self.assertEqual(action.categoria_programatica, '000 0 001')
        self.assertEqual(operation.linea_base, 0.25)
        self.assertEqual(operation.meta_actual, 0.50)
        self.assertEqual(operation.ponderacion, 25)
        self.assertEqual(applied.data['resultado']['eliminados'], 4)
        self.assertEqual(applied.data['resultado']['creados'], 5)

    def test_apply_replaces_operation_with_existing_budget_assignment(self):
        """Reproduce el 400 real de producción: la operación que el nuevo

        árbol reemplaza ya tiene una `AsignacionPresupuestariaUnidad`
        (on_delete=PROTECT). Antes del fix esto bloqueaba todo el `apply`;
        ahora debe reemplazar igual, dejando la asignación en el historial
        auditado en vez de simplemente borrarla sin dejar rastro.
        """
        asignacion = crear_asignacion_presupuestaria(
            self.gestion, self.unit, self.operation,
        )
        response = self.preview_excel(self.rows(include_new=True))
        operation_id = self.operation.id

        applied = self.client.post(
            reverse('v2-poau-imports-apply', args=[response.data['id']]) + self.query,
            {'confirmation_code': self.unit.codigo}, format='json',
        )

        self.assertEqual(applied.status_code, 200, applied.data)
        self.assertFalse(OperacionPOAU.objects.filter(pk=operation_id).exists())
        self.assertFalse(
            AsignacionPresupuestariaUnidad.objects.filter(pk=asignacion.pk).exists(),
        )
        version = VersionImportacionPOAU.objects.get(
            unidad=self.unit, tipo_evento=VersionImportacionPOAU.TipoEvento.REEMPLAZO,
        )
        self.assertIn(
            str(operation_id),
            [row['id'] for row in version.snapshot['operaciones']],
        )
        # El monto asignado no se pierde: queda en el snapshot aunque la fila
        # viva ya no exista, para reconciliar a mano si hace falta.
        asignaciones_snapshot = version.snapshot['asignaciones_presupuestarias']
        self.assertEqual(len(asignaciones_snapshot), 1)
        self.assertEqual(asignaciones_snapshot[0]['id'], str(asignacion.pk))
        self.assertEqual(
            Decimal(asignaciones_snapshot[0]['monto_vigente']), Decimal('900.00'),
        )
        self.assertEqual(version.resumen['asignaciones_presupuestarias'], 1)

    def test_write_failure_rolls_back_all_changes(self):
        content = workbook_bytes(self.rows())
        request = type('Request', (), {'user': self.user, 'query_params': {}})()
        preview = create_preview(
            request=request, origin='excel', unit_code=self.unit.codigo,
            content=content, source_name='rollback.xlsx', sheet_name='POAU',
        )
        with patch.object(
            TareaPOAU.objects, 'create', side_effect=RuntimeError('injected failure'),
        ):
            with self.assertRaises(RuntimeError):
                apply_preview(
                    preview.id, self.user,
                    confirmation_code=self.unit.codigo,
                )
        self.operation.refresh_from_db()
        preview.refresh_from_db()
        self.assertEqual(self.operation.denominacion, 'Operación anterior')
        self.assertEqual(preview.estado, 'VALIDO')

    def test_approved_record_is_replaced_and_new_tree_returns_to_draft(self):
        self.task.estado = 'APROBADO'
        self.task.save(update_fields=['estado'])
        response = self.preview_excel()
        applied = self.client.post(
            reverse('v2-poau-imports-apply', args=[response.data['id']]) + self.query,
            {'confirmation_code': self.unit.codigo}, format='json',
        )
        self.assertEqual(applied.status_code, 200, applied.data)
        self.assertFalse(TareaPOAU.objects.filter(pk=self.task.pk).exists())
        self.assertTrue(TareaPOAU.objects.filter(estado='BORRADOR').exists())
