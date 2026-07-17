import io
import zipfile
import logging
from celery import shared_task
from django.db.models import Sum, Count, DecimalField
from django.db.models.functions import Coalesce

logger = logging.getLogger(__name__)


@shared_task(bind=True, soft_time_limit=300, time_limit=600)
def generar_reporte_presupuestario_async(self, params: dict):
    """Genera un reporte presupuestario de forma asíncrona"""
    from apps.reportes.services import (
        generar_poa_consolidado_xlsx,
        generar_poa_unidad_xlsx,
    )
    try:
        gestion = params.get('gestion')
        tipo = params.get('tipo', 'consolidado')

        if tipo == 'consolidado':
            output, filename = generar_poa_consolidado_xlsx(gestion)
        elif tipo == 'unidad':
            unidad_id = params.get('unidad_id')
            output, filename = generar_poa_unidad_xlsx(gestion, unidad_id)
        else:
            return {"status": "error", "error": f"Tipo de reporte no soportado: {tipo}"}

        logger.info(f"Reporte {tipo} generado: {filename}")
        return {
            "status": "ok",
            "filename": filename,
            "gestion": gestion,
            "tipo": tipo,
            "tamanio_bytes": output.tell(),
        }
    except Exception as e:
        logger.error(f"Error generando reporte: {e}")
        raise self.retry(exc=e, countdown=60)


def _generar_resumen_poau_xlsx(gestion):
    """Genera Excel resumen de POAUs de la gestión."""
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment

    from apps.poau.models import POAU

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f'Resumen POAU {gestion}'

    header_fill = PatternFill(start_color='1B5E3B', end_color='1B5E3B', fill_type='solid')
    header_font = Font(color='FFFFFF', bold=True, size=10)

    ws.merge_cells('A1:F1')
    ws['A1'] = f'RESUMEN POAU - GESTIÓN {gestion}'
    ws['A1'].font = Font(bold=True, size=14, color='1B5E3B')

    headers = ['Código', 'Nombre', 'Unidad', 'Estado', 'Actividades', 'Presupuesto Total']
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col, value=h)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')

    poaus = POAU.objects.filter(gestion=gestion).select_related('unidad')
    row = 4
    for poau in poaus:
        num_actividades = poau.actividades.count()
        presupuesto = poau.actividades.aggregate(
            total=Coalesce(
                Sum('presupuesto_anual'),
                0,
                output_field=DecimalField(max_digits=20, decimal_places=2),
            )
        )['total']
        datos = [
            poau.codigo,
            poau.nombre,
            str(poau.unidad),
            poau.get_estado_display(),
            num_actividades,
            float(presupuesto),
        ]
        for col, val in enumerate(datos, 1):
            ws.cell(row=row, column=col, value=val).border = (
                __import__('openpyxl', fromlist=['styles']).styles.Border(
                    left=__import__('openpyxl', fromlist=['styles']).styles.Side(style='thin'),
                    right=__import__('openpyxl', fromlist=['styles']).styles.Side(style='thin'),
                    top=__import__('openpyxl', fromlist=['styles']).styles.Side(style='thin'),
                    bottom=__import__('openpyxl', fromlist=['styles']).styles.Side(style='thin'),
                )
            )
        row += 1

    for col in range(1, 7):
        ws.column_dimensions[chr(64 + col)].width = 25

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output, f'resumen_poau_{gestion}.xlsx'


def _generar_actividades_xlsx(gestion):
    """Genera Excel con todas las actividades de la gestión."""
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment

    from apps.poau.models import POAUActividad

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f'Actividades {gestion}'

    header_fill = PatternFill(start_color='1B5E3B', end_color='1B5E3B', fill_type='solid')
    header_font = Font(color='FFFFFF', bold=True, size=10)

    ws.merge_cells('A1:J1')
    ws['A1'] = f'ACTIVIDADES POAU - GESTIÓN {gestion}'
    ws['A1'].font = Font(bold=True, size=14, color='1B5E3B')

    headers = [
        'POAU', 'Código', 'Nombre', 'Meta Anual', 'Presupuesto',
        'Q1', 'Q2', 'Q3', 'Q4', 'Acción CP',
    ]
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col, value=h)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')

    actividades = POAUActividad.objects.filter(
        poau__gestion=gestion
    ).select_related('poau', 'accion_corto_plazo')

    row = 4
    for act in actividades:
        datos = [
            act.poau.codigo,
            act.codigo,
            act.nombre,
            float(act.meta_fisica_anual) if act.meta_fisica_anual else '',
            float(act.presupuesto_anual) if act.presupuesto_anual else '',
            float(act.meta_q1) if act.meta_q1 else '',
            float(act.meta_q2) if act.meta_q2 else '',
            float(act.meta_q3) if act.meta_q3 else '',
            float(act.meta_q4) if act.meta_q4 else '',
            str(act.accion_corto_plazo) if act.accion_corto_plazo else '',
        ]
        for col, val in enumerate(datos, 1):
            cell = ws.cell(row=row, column=col, value=val)
        row += 1

    for col in range(1, 11):
        ws.column_dimensions[chr(64 + col)].width = 20

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output, f'actividades_{gestion}.xlsx'


def _generar_lineas_presupuestarias_xlsx(gestion):
    """Genera Excel de líneas presupuestarias."""
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment

    from apps.presupuesto.models import LineaPresupuestaria

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f'Líneas {gestion}'

    header_fill = PatternFill(start_color='1B5E3B', end_color='1B5E3B', fill_type='solid')
    header_font = Font(color='FFFFFF', bold=True, size=10)

    ws.merge_cells('A1:H1')
    ws['A1'] = f'LÍNEAS PRESUPUESTARIAS - GESTIÓN {gestion}'
    ws['A1'].font = Font(bold=True, size=14, color='1B5E3B')

    headers = ['Programa', 'Proyecto', 'Actividad', 'Objeto Gasto',
               'Fuente', 'Importe', 'Importe G.Anterior', 'Plurianual']
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col, value=h)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')

    lineas = LineaPresupuestaria.objects.filter(
        gestion=gestion, activo=True
    ).select_related('programa', 'proyecto', 'actividad', 'objeto_gasto', 'fuente')

    row = 4
    for lp in lineas:
        datos = [
            str(lp.programa),
            str(lp.proyecto) if lp.proyecto else '',
            str(lp.actividad) if lp.actividad else '',
            str(lp.objeto_gasto),
            str(lp.fuente),
            float(lp.importe),
            float(lp.importe_gestion_anterior) if lp.importe_gestion_anterior else 0,
            float(lp.importe_plurianual) if lp.importe_plurianual else 0,
        ]
        for col, val in enumerate(datos, 1):
            ws.cell(row=row, column=col, value=val)
        row += 1

    for col in range(1, 9):
        ws.column_dimensions[chr(64 + col)].width = 20

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output, f'lineas_presupuestarias_{gestion}.xlsx'


def _generar_ejecucion_xlsx(gestion):
    """Genera Excel de datos de ejecución física y financiera."""
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment

    from apps.poau.models import EjecucionFisica, EjecucionFinanciera

    wb = openpyxl.Workbook()

    ws_fis = wb.active
    ws_fis.title = f'Ejecución Física {gestion}'

    header_fill = PatternFill(start_color='1B5E3B', end_color='1B5E3B', fill_type='solid')
    header_font = Font(color='FFFFFF', bold=True, size=10)

    ws_fis.merge_cells('A1:F1')
    ws_fis['A1'] = f'EJECUCIÓN FÍSICA - GESTIÓN {gestion}'
    ws_fis['A1'].font = Font(bold=True, size=14, color='1B5E3B')

    headers_fis = ['Actividad', 'Periodo', 'Tipo', 'Programado', 'Ejecutado', 'Observaciones']
    for col, h in enumerate(headers_fis, 1):
        cell = ws_fis.cell(row=3, column=col, value=h)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')

    ejec_fisicas = EjecucionFisica.objects.filter(
        actividad__poau__gestion=gestion
    ).select_related('actividad')

    row = 4
    for ef in ejec_fisicas:
        datos = [
            str(ef.actividad),
            ef.periodo,
            ef.get_tipo_periodo_display(),
            float(ef.programado),
            float(ef.ejecutado),
            ef.observaciones,
        ]
        for col, val in enumerate(datos, 1):
            ws_fis.cell(row=row, column=col, value=val)
        row += 1

    ws_fin = wb.create_sheet(title=f'Ejecución Financiera {gestion}')
    ws_fin.merge_cells('A1:F1')
    ws_fin['A1'] = f'EJECUCIÓN FINANCIERA - GESTIÓN {gestion}'
    ws_fin['A1'].font = Font(bold=True, size=14, color='1B5E3B')

    headers_fin = ['Actividad', 'Periodo', 'Tipo', 'Programado', 'Ejecutado', 'Observaciones']
    for col, h in enumerate(headers_fin, 1):
        cell = ws_fin.cell(row=3, column=col, value=h)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')

    ejec_financieras = EjecucionFinanciera.objects.filter(
        actividad__poau__gestion=gestion
    ).select_related('actividad')

    row = 4
    for ef in ejec_financieras:
        datos = [
            str(ef.actividad),
            ef.periodo,
            ef.get_tipo_periodo_display(),
            float(ef.programado),
            float(ef.ejecutado),
            ef.observaciones,
        ]
        for col, val in enumerate(datos, 1):
            ws_fin.cell(row=row, column=col, value=val)
        row += 1

    for ws in [ws_fis, ws_fin]:
        for col in range(1, 7):
            ws.column_dimensions[chr(64 + col)].width = 20

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output, f'ejecucion_{gestion}.xlsx'


@shared_task(bind=True, soft_time_limit=600, time_limit=900)
def exportar_poa_completo_async(self, gestion: int):
    """Exporta el POA completo de una gestión como ZIP con múltiples Excel."""
    logger.info(f"Exportando POA completo gestión {gestion}")

    zip_buffer = io.BytesIO()
    try:
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            resumen_io, resumen_name = _generar_resumen_poau_xlsx(gestion)
            zf.writestr(resumen_name, resumen_io.read())

            actividades_io, actividades_name = _generar_actividades_xlsx(gestion)
            zf.writestr(actividades_name, actividades_io.read())

            lineas_io, lineas_name = _generar_lineas_presupuestarias_xlsx(gestion)
            zf.writestr(lineas_name, lineas_io.read())

            ejecucion_io, ejecucion_name = _generar_ejecucion_xlsx(gestion)
            zf.writestr(ejecucion_name, ejecucion_io.read())

        zip_buffer.seek(0)
        zip_filename = f'poa_completo_{gestion}.zip'

        import tempfile
        import os
        from django.conf import settings

        export_dir = os.path.join(settings.MEDIA_ROOT, 'exportaciones')
        os.makedirs(export_dir, exist_ok=True)
        filepath = os.path.join(export_dir, zip_filename)

        with open(filepath, 'wb') as f:
            f.write(zip_buffer.read())

        logger.info(f"POA completo exportado: {filepath}")
        return {
            "status": "ok",
            "filename": zip_filename,
            "filepath": filepath,
            "gestion": gestion,
        }
    except Exception as e:
        logger.error(f"Error exportando POA completo: {e}")
        raise self.retry(exc=e, countdown=120)
