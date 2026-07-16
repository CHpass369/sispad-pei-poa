"""
Servicios de generación de reportes del POA.
Soporta PDF (reportlab), XLSX (openpyxl), CSV y GeoJSON.
"""
import csv, io, json
from decimal import Decimal
from datetime import datetime
from django.db.models import Sum, Count, Q, DecimalField, IntegerField
from django.db.models.functions import Coalesce
from django.utils import timezone

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

from apps.presupuesto.models import ProgramaPresupuestario, LineaPresupuestaria
from apps.planificacion.models import AccionCortoPlazo
from apps.organizacion.models import UnidadOrganizacional
from apps.techos.models import TechoPresupuestario, DistribucionTecho
from apps.inversion.models import ProyectoInversion
from apps.workflow.models import Observacion, Aprobacion


HEADER_FILL = PatternFill(start_color='1B5E3B', end_color='1B5E3B', fill_type='solid')
HEADER_FONT = Font(color='FFFFFF', bold=True, size=10)
BORDER_THIN = Border(
    left=Side(style='thin'), right=Side(style='thin'),
    top=Side(style='thin'), bottom=Side(style='thin')
)


def _build_response_filename(tipo: str, formato: str, gestion: int) -> str:
    return f'poa_{tipo}_{gestion}_{datetime.now().strftime("%Y%m%d")}.{formato}'


# ===== REPORTE POA POR UNIDAD =====
def generar_poa_unidad_xlsx(gestion: int, unidad_id: str = None) -> tuple:
    """Genera XLSX del POA por unidad organizacional."""
    if not HAS_OPENPYXL:
        raise RuntimeError('openpyxl no está instalado')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f'POA Unidad {gestion}'

    # Encabezado
    ws.merge_cells('A1:H1')
    ws['A1'] = f'GOBIERNO AUTÓNOMO MUNICIPAL DE SACABA - POA {gestion}'
    ws['A1'].font = Font(bold=True, size=14, color='1B5E3B')

    # Headers
    headers = ['Código', 'Acción', 'Indicador', 'Meta', 'Unidad', 'Operaciones', 'Presupuesto (Bs)', 'Estado']
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col, value=h)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal='center')

    acciones = AccionCortoPlazo.objects.filter(gestion=gestion)
    if unidad_id:
        acciones = acciones.filter(unidad_responsable_id=unidad_id)

    row = 4
    for acp in acciones:
        datos = [
            acp.codigo, acp.nombre, '',
            '', '',
            acp.operaciones.count(),
            0,
            'Formulado' if acp.activo else 'Inactivo',
        ]
        for col, val in enumerate(datos, 1):
            cell = ws.cell(row=row, column=col, value=val)
            cell.border = BORDER_THIN
        row += 1

    for col in range(1, 9):
        ws.column_dimensions[chr(64 + col)].width = 20

    filename = _build_response_filename('unidad', 'xlsx', gestion)
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output, filename


# ===== REPORTE POA CONSOLIDADO =====
def generar_poa_consolidado_xlsx(gestion: int) -> tuple:
    """Genera XLSX del POA institucional consolidado."""
    if not HAS_OPENPYXL:
        raise RuntimeError('openpyxl no está instalado')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f'Consolidado {gestion}'

    ws.merge_cells('A1:G1')
    ws['A1'] = f'POA CONSOLIDADO {gestion} - GAM SACABA'
    ws['A1'].font = Font(bold=True, size=14, color='1B5E3B')

    headers = ['Programa', 'Acciones', 'Presupuesto (Bs)', 'Techo (Bs)', 'Saldo (Bs)', 'Avance %', 'Estado']
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col, value=h)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT

    programas = ProgramaPresupuestario.objects.filter(gestion=gestion).annotate(
        total_presupuesto=Coalesce(
            Sum('lineas__importe'), 0,
            output_field=DecimalField(max_digits=20, decimal_places=2)
        ),
        total_acciones=Coalesce(
            Count('proyectos_inversion'), 0,
            output_field=IntegerField()
        ),
    )

    row = 4
    for prog in programas:
        techo_total = DistribucionTecho.objects.filter(
            programa=prog, activo=True
        ).aggregate(t=Coalesce(
            Sum('monto_asignado'), 0,
            output_field=DecimalField(max_digits=20, decimal_places=2)
        ))['t']

        presupuesto = float(prog.total_presupuesto)
        techo = float(techo_total)
        saldo = techo - presupuesto
        avance = (presupuesto / techo * 100) if techo > 0 else 0

        datos = [prog.codigo, prog.total_acciones, round(presupuesto, 2),
                 round(techo, 2), round(saldo, 2), round(avance, 1),
                 'Completo' if saldo >= 0 else 'Sobregiro']
        for col, val in enumerate(datos, 1):
            ws.cell(row=row, column=col, value=val).border = BORDER_THIN
        row += 1

    filename = _build_response_filename('consolidado', 'xlsx', gestion)
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output, filename


# ===== REPORTE DE PROYECTOS DE INVERSIÓN =====
def generar_proyectos_xlsx(gestion: int) -> tuple:
    """Genera XLSX de proyectos de inversión."""
    if not HAS_OPENPYXL:
        raise RuntimeError('openpyxl no está instalado')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f'Proyectos {gestion}'

    ws.merge_cells('A1:I1')
    ws['A1'] = f'PROYECTOS DE INVERSIÓN {gestion} - GAM SACABA'
    ws['A1'].font = Font(bold=True, size=14, color='1B5E3B')

    headers = ['Código', 'Nombre', 'SISIN', 'Prioridad', 'Etapa', 'Costo Total',
               'Ejecutado', 'Fuente', 'Organismo']
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col, value=h)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT

    proyectos = ProyectoInversion.objects.filter(gestion_inicio__lte=gestion) | \
                ProyectoInversion.objects.filter(gestion_fin__gte=gestion)
    proyectos = proyectos.filter(activo=True).distinct()

    row = 4
    for p in proyectos:
        datos = [p.codigo_interno, p.nombre, p.codigo_sisin or '—',
                 p.get_prioridad_display(), p.get_etapa_display(),
                 float(p.costo_total), float(p.ejecucion_acumulada),
                 p.fuente.denominacion if p.fuente else '—',
                 p.organismo.denominacion if p.organismo else '—']
        for col, val in enumerate(datos, 1):
            ws.cell(row=row, column=col, value=val).border = BORDER_THIN
        row += 1

    filename = _build_response_filename('proyectos', 'xlsx', gestion)
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output, filename


# ===== REPORTE DE OBSERVACIONES =====
def generar_observaciones_csv(gestion: int) -> tuple:
    """Genera CSV de observaciones."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Código', 'Tipo', 'Severidad', 'Estado', 'Módulo',
                     'Texto', 'Creado', 'Responsable'])

    observaciones = Observacion.objects.filter(gestion=gestion)
    for obs in observaciones:
        writer.writerow([
            obs.codigo, obs.get_tipo_display(), obs.get_severidad_display(),
            obs.get_estado_display(), obs.modulo, obs.texto,
            obs.created_at.isoformat() if hasattr(obs, 'created_at') else '',
            str(obs.responsable_subsanacion) if obs.responsable_subsanacion else '',
        ])

    filename = _build_response_filename('observaciones', 'csv', gestion)
    return io.BytesIO(output.getvalue().encode('utf-8-sig')), filename


# ===== EXPORTACIÓN GEOJSON =====
def generar_territorio_geojson(gestion: int) -> dict:
    """Genera GeoJSON de localizaciones territoriales."""
    from apps.territorio.models import LocalizacionTerritorial

    localizaciones = LocalizacionTerritorial.objects.filter(gestion=gestion, activo=True)

    features = []
    for loc in localizaciones:
        if not loc.geometria_4326:
            continue
        try:
            geom_json = json.loads(loc.geometria_4326.geojson)
        except Exception:
            continue

        features.append({
            'type': 'Feature',
            'geometry': geom_json,
            'properties': {
                'entidad': loc.entidad,
                'entidad_id': loc.entidad_id,
                'distrito': str(loc.distrito) if loc.distrito else '',
                'unidad_territorial': str(loc.unidad_territorial) if loc.unidad_territorial else '',
                'gestion': loc.gestion,
            }
        })

    return {
        'type': 'FeatureCollection',
        'features': features,
        'metadata': {
            'gestion': gestion,
            'generado_en': timezone.now().isoformat(),
            'total_localizaciones': len(features),
        }
    }


# ===== ACTA DE APROBACIÓN =====
def generar_acta_aprobacion_pdf(gestion: int) -> tuple:
    """Genera PDF de acta de aprobación."""
    if not HAS_REPORTLAB:
        raise RuntimeError('reportlab no está instalado')

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        rightMargin=inch, leftMargin=inch,
        topMargin=inch, bottomMargin=inch
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='ActaTitle',
        parent=styles['Title'],
        fontSize=16,
        textColor=colors.HexColor('#1B5E3B'),
        spaceAfter=20,
    ))

    elements = []
    elements.append(Paragraph(f'ACTA DE APROBACIÓN POA {gestion}', styles['ActaTitle']))
    elements.append(Paragraph(
        f'GOBIERNO AUTÓNOMO MUNICIPAL DE SACABA<br/>'
        f'<br/>'
        f'<b>Gestión:</b> {gestion}<br/>'
        f'<b>Fecha de emisión:</b> {datetime.now().strftime("%d/%m/%Y %H:%M")}<br/>'
        f'<b>Tipo:</b> Acta de aprobación institucional del POA',
        styles['Normal']
    ))
    elements.append(Spacer(1, 20))

    # Tabla de aprobaciones
    aprobaciones = Aprobacion.objects.filter(gestion=gestion)
    if aprobaciones.exists():
        data = [['Tipo', 'Estado', 'Aprobado por', 'Fecha']]
        for ap in aprobaciones:
            data.append([
                ap.get_tipo_display(),
                ap.get_estado_display(),
                str(ap.aprobado_por) if ap.aprobado_por else '—',
                ap.created_at.strftime('%d/%m/%Y') if hasattr(ap, 'created_at') and ap.created_at else '—',
            ])

        table = Table(data, colWidths=[2*inch, 1*inch, 2*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1B5E3B')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(table)

    doc.build(elements)
    buffer.seek(0)
    filename = _build_response_filename('acta_aprobacion', 'pdf', gestion)
    return buffer, filename


# ===== AUXILIAR PLURI =====

GRUPOS_GASTO = {
    '1': 'SERVICIOS PERSONALES',
    '2': 'SERVICIOS NO PERSONALES',
    '3': 'MATERIALES Y SUMINISTROS',
    '4': 'ACTIVOS REALES',
    '5': 'FINANCIEROS',
    '6': 'TRANSFERENCIAS',
    '7': 'IMPUESTOS Y TASAS',
    '8': 'DEUDA PÚBLICA',
    '9': 'OTROS',
}


def _obtener_grupo_gasto(codigo_objeto: str) -> tuple:
    """Deriva el grupo de gasto del primer dígito del código."""
    if not codigo_objeto:
        return ('9', 'OTROS')
    primer_digito = codigo_objeto[0]
    nombre = GRUPOS_GASTO.get(primer_digito, 'OTROS')
    return (primer_digito, nombre)


def generar_auxiliar_pluri_xlsx(gestion: int) -> tuple:
    """Genera XLSX del Auxiliar Pluri (presupuesto plurianual por objeto de gasto y FF/OF)."""
    if not HAS_OPENPYXL:
        raise RuntimeError('openpyxl no está instalado')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f'Auxiliar Pluri {gestion}'

    # Encabezado institucional
    ws.merge_cells('A1:G1')
    ws['A1'] = f'GOBIERNO AUTÓNOMO MUNICIPAL DE SACABA'
    ws['A1'].font = Font(bold=True, size=14, color='1B5E3B')

    ws.merge_cells('A2:G2')
    ws['A2'] = f'AUXILIAR PLURI - Gestión {gestion} (Expresado en Bolivianos)'
    ws['A2'].font = Font(bold=True, size=11, color='1B5E3B')

    # Headers
    headers = ['GRUPO DE GASTO', 'OBJETO DE GASTO', 'DESCRIPCIÓN',
               'FF/OF', 'IMPORTE G. ANTERIOR', 'IMPORTE', 'IMPORTE PLURIANUAL']
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col, value=h)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal='center', wrap_text=True)

    # Consultar líneas presupuestarias
    lineas = LineaPresupuestaria.objects.filter(
        gestion=gestion, activo=True
    ).select_related(
        'objeto_gasto', 'fuente', 'organismo'
    ).order_by('objeto_gasto__codigo', 'fuente__codigo')

    row = 5
    grupo_actual = None
    subtotal_grupo_ant = 0
    subtotal_grupo_imp = 0
    subtotal_grupo_pluri = 0
    total_gral_ant = 0
    total_gral_imp = 0
    total_gral_pluri = 0

    for lp in lineas:
        grupo_cod, grupo_nom = _obtener_grupo_gasto(lp.objeto_gasto.codigo)

        # Subtotales al cambiar de grupo
        if grupo_actual and grupo_actual != grupo_cod:
            _write_subtotal(ws, row, grupo_actual, subtotal_grupo_ant, subtotal_grupo_imp, subtotal_grupo_pluri)
            row += 1
            subtotal_grupo_ant = 0
            subtotal_grupo_imp = 0
            subtotal_grupo_pluri = 0

        grupo_actual = grupo_cod

        ff_of = f'{lp.fuente.codigo}/{lp.organismo.codigo if lp.organismo else "—"}'
        imp_ant = float(lp.importe_gestion_anterior or 0)
        imp = float(lp.importe or 0)
        imp_pluri = float(lp.importe_plurianual or 0)

        ws.cell(row=row, column=1, value=grupo_nom)
        ws.cell(row=row, column=2, value=lp.objeto_gasto.codigo)
        ws.cell(row=row, column=3, value=lp.objeto_gasto.denominacion)
        ws.cell(row=row, column=4, value=ff_of)
        ws.cell(row=row, column=5, value=round(imp_ant, 2)).number_format = '#,##0.00'
        ws.cell(row=row, column=6, value=round(imp, 2)).number_format = '#,##0.00'
        ws.cell(row=row, column=7, value=round(imp_pluri, 2)).number_format = '#,##0.00'

        for c in range(1, 8):
            ws.cell(row=row, column=c).border = BORDER_THIN
            ws.cell(row=row, column=c).font = Font(size=9)

        subtotal_grupo_ant += imp_ant
        subtotal_grupo_imp += imp
        subtotal_grupo_pluri += imp_pluri
        total_gral_ant += imp_ant
        total_gral_imp += imp
        total_gral_pluri += imp_pluri
        row += 1

    # Último subtotal
    if grupo_actual:
        _write_subtotal(ws, row, grupo_actual, subtotal_grupo_ant, subtotal_grupo_imp, subtotal_grupo_pluri)
        row += 2

    # Total general
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=4)
    ws.cell(row=row, column=1, value='TOTAL GENERAL')
    ws.cell(row=row, column=1).font = Font(bold=True, size=11, color='1B5E3B')
    ws.cell(row=row, column=5, value=round(total_gral_ant, 2)).number_format = '#,##0.00'
    ws.cell(row=row, column=5).font = Font(bold=True)
    ws.cell(row=row, column=6, value=round(total_gral_imp, 2)).number_format = '#,##0.00'
    ws.cell(row=row, column=6).font = Font(bold=True)
    ws.cell(row=row, column=7, value=round(total_gral_pluri, 2)).number_format = '#,##0.00'
    ws.cell(row=row, column=7).font = Font(bold=True)
    for c in range(1, 8):
        ws.cell(row=row, column=c).border = Border(
            left=Side(style='thin'), right=Side(style='thin'),
            top=Side(style='double'), bottom=Side(style='double')
        )
        ws.cell(row=row, column=c).fill = PatternFill(start_color='E8F5E9', end_color='E8F5E9', fill_type='solid')

    # Ajustar ancho de columnas
    ws.column_dimensions['A'].width = 30
    ws.column_dimensions['B'].width = 15
    ws.column_dimensions['C'].width = 40
    ws.column_dimensions['D'].width = 12
    ws.column_dimensions['E'].width = 20
    ws.column_dimensions['F'].width = 20
    ws.column_dimensions['G'].width = 20

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    filename = _build_response_filename('auxiliar_pluri', 'xlsx', gestion)
    return buffer, filename


def _write_subtotal(ws, row, grupo_cod, sub_ant, sub_imp, sub_pluri):
    """Escribe fila de subtotal para un grupo de gasto."""
    grupo_nom = GRUPOS_GASTO.get(str(grupo_cod), 'OTROS')
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=4)
    ws.cell(row=row, column=1, value=f'Subtotal {grupo_cod} - {grupo_nom}')
    ws.cell(row=row, column=1).font = Font(bold=True, italic=True, size=9, color='1B5E3B')
    ws.cell(row=row, column=5, value=round(sub_ant, 2)).number_format = '#,##0.00'
    ws.cell(row=row, column=5).font = Font(bold=True)
    ws.cell(row=row, column=6, value=round(sub_imp, 2)).number_format = '#,##0.00'
    ws.cell(row=row, column=6).font = Font(bold=True)
    ws.cell(row=row, column=7, value=round(sub_pluri, 2)).number_format = '#,##0.00'
    ws.cell(row=row, column=7).font = Font(bold=True)
    for c in range(1, 8):
        ws.cell(row=row, column=c).border = BORDER_THIN
        ws.cell(row=row, column=c).fill = PatternFill(start_color='F5F5F5', end_color='F5F5F5', fill_type='solid')


# ===== EVALUACIÓN — CUADRO N°1 =====
def generar_evaluacion_cuadro1_xlsx(gestion: int) -> tuple:
    """Cuadro N°1: Comparación de programación presupuestaria PTDI vs PEI vs POA por fuente."""
    if not HAS_OPENPYXL:
        raise RuntimeError('openpyxl no está instalado')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f'Eval Cuadro1 {gestion}'

    ws.merge_cells('A1:F1')
    ws['A1'] = f'GOBIERNO AUTÓNOMO MUNICIPAL DE SACABA'
    ws['A1'].font = Font(bold=True, size=14, color='1B5E3B')

    ws.merge_cells('A2:F2')
    ws['A2'] = f'CUADRO N°1 — Evaluación de Programación de Recursos (Gestión {gestion})'
    ws['A2'].font = Font(bold=True, size=11, color='1B5E3B')

    headers = ['FUENTE DE INGRESOS', 'PTDI/PGTC (Bs)', 'PEI (Bs)',
               'POA (Bs)', 'DIFERENCIA (Bs)', 'DIFERENCIA (%)']
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col, value=h)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal='center', wrap_text=True)

    # Datos de LineaPresupuestaria agrupados por fuente
    from django.db.models import Sum
    lineas = LineaPresupuestaria.objects.filter(gestion=gestion, activo=True)
    fuentes_data = lineas.values('fuente__codigo', 'fuente__denominacion').annotate(
        total_poa=Sum('importe')
    ).order_by('fuente__codigo')

    row = 5
    total_poa = 0
    for f in fuentes_data:
        poa = float(f['total_poa'] or 0)
        # PTDI y PEI son estimativos sin datos en BD actual — se muestran como 0
        ws.cell(row=row, column=1, value=f'{f["fuente__codigo"]} — {f["fuente__denominacion"]}')
        ws.cell(row=row, column=2, value=0).number_format = '#,##0.00'
        ws.cell(row=row, column=3, value=0).number_format = '#,##0.00'
        ws.cell(row=row, column=4, value=round(poa, 2)).number_format = '#,##0.00'
        ws.cell(row=row, column=5, value=round(poa, 2)).number_format = '#,##0.00'  # dif = POA - PTDI
        ws.cell(row=row, column=6, value='100%' if poa > 0 else '0%')
        for c in range(1, 7):
            ws.cell(row=row, column=c).border = BORDER_THIN
            ws.cell(row=row, column=c).font = Font(size=9)
        total_poa += poa
        row += 1

    # Total
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=1)
    ws.cell(row=row, column=1, value='TOTAL').font = Font(bold=True, size=10, color='1B5E3B')
    ws.cell(row=row, column=4, value=round(total_poa, 2)).number_format = '#,##0.00'
    ws.cell(row=row, column=4).font = Font(bold=True)
    ws.cell(row=row, column=5, value=round(total_poa, 2)).number_format = '#,##0.00'
    ws.cell(row=row, column=5).font = Font(bold=True)
    for c in range(1, 7):
        ws.cell(row=row, column=c).border = Border(left=Side(style='thin'), right=Side(style='thin'),
                                                     top=Side(style='double'), bottom=Side(style='double'))

    for col_letter, width in [('A', 40), ('B', 18), ('C', 18), ('D', 18), ('E', 18), ('F', 18)]:
        ws.column_dimensions[col_letter].width = width

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer, _build_response_filename('evaluacion_cuadro1', 'xlsx', gestion)


# ===== EVALUACIÓN — CUADRO N°2 =====
def generar_evaluacion_cuadro2_xlsx(gestion: int) -> tuple:
    """Cuadro N°2: Vinculación de acciones PTDI/PGTC ↔ PEI ↔ POA."""
    if not HAS_OPENPYXL:
        raise RuntimeError('openpyxl no está instalado')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f'Eval Cuadro2 {gestion}'

    ws.merge_cells('A1:F1')
    ws['A1'] = f'GOBIERNO AUTÓNOMO MUNICIPAL DE SACABA'
    ws['A1'].font = Font(bold=True, size=14, color='1B5E3B')
    ws.merge_cells('A2:F2')
    ws['A2'] = f'CUADRO N°2 — Vinculación de Acciones PTDI/PGTC ↔ PEI ↔ POA (Gestión {gestion})'
    ws['A2'].font = Font(bold=True, size=11, color='1B5E3B')

    headers = ['PTDI/PGTC (Acción ETA)', 'PEI (AMP)', 'POA (ACP)',
               'CÓD. PROG.', '¿VINCULADO?', 'ARTICULACIÓN']
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col, value=h)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal='center', wrap_text=True)

    # Trazar relaciones reales: ACP → AMP → Nodo (vía ArticulacionPlanificacion)
    from apps.planificacion.models import AccionCortoPlazo, AccionMedianoPlazo, ArticulacionPlanificacion

    acps = AccionCortoPlazo.objects.filter(gestion=gestion).select_related(
        'accion_mediano_plazo'
    ).prefetch_related('accion_mediano_plazo__nodo_planificacion')

    row = 5
    for acp in acps:
        amp = acp.accion_mediano_plazo
        amp_nombre = amp.nombre[:100] if amp else '—'
        ptdi_accion = amp_nombre if amp else '—'

        # Verificar articulación
        articulado = 'SÍ' if amp and amp.nodo_planificacion else 'NO'
        nivel_art = amp.nodo_planificacion.nivel if amp and amp.nodo_planificacion else '—'

        ws.cell(row=row, column=1, value=ptdi_accion)
        ws.cell(row=row, column=2, value=amp_nombre)
        ws.cell(row=row, column=3, value=acp.nombre[:100])
        ws.cell(row=row, column=4, value=acp.codigo)
        ws.cell(row=row, column=5, value=articulado)
        ws.cell(row=row, column=6, value=nivel_art)

        fill_color = 'E8F5E9' if articulado == 'SÍ' else 'FFEBEE'
        for c in range(1, 7):
            ws.cell(row=row, column=c).border = BORDER_THIN
            ws.cell(row=row, column=c).font = Font(size=9)
            ws.cell(row=row, column=c).fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type='solid')
        row += 1

    for col_letter, width in [('A', 40), ('B', 40), ('C', 40), ('D', 15), ('E', 15), ('F', 20)]:
        ws.column_dimensions[col_letter].width = width

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer, _build_response_filename('evaluacion_cuadro2', 'xlsx', gestion)


# ===== EVALUACIÓN — CUADRO N°3 =====
def generar_evaluacion_cuadro3_xlsx(gestion: int) -> tuple:
    """Cuadro N°3: Seguimiento a la ejecución física y financiera."""
    if not HAS_OPENPYXL:
        raise RuntimeError('openpyxl no está instalado')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f'Eval Cuadro3 {gestion}'

    ws.merge_cells('A1:I1')
    ws['A1'] = f'GOBIERNO AUTÓNOMO MUNICIPAL DE SACABA'
    ws['A1'].font = Font(bold=True, size=14, color='1B5E3B')
    ws.merge_cells('A2:I2')
    ws['A2'] = f'CUADRO N°3 — Seguimiento a la Ejecución Física y Financiera (Gestión {gestion})'
    ws['A2'].font = Font(bold=True, size=11, color='1B5E3B')

    headers = ['ACTIVIDAD/ACP', 'PROG. FÍSICO', 'EJEC. FÍSICO', '% AVANCE FÍS.',
               'PROG. FINANCIERO', 'EJEC. FINANCIERO', '% EJEC. FIN.', 'CAUSA DESVIACIÓN', 'ESTADO']
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col, value=h)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal='center', wrap_text=True)

    from django.db.models import Sum
    from apps.poau.models import POAUActividad, EjecucionFisica, EjecucionFinanciera

    actividades = POAUActividad.objects.filter(poau__gestion=gestion).prefetch_related(
        'ejecucion_fisica', 'ejecucion_financiera'
    )

    row = 5
    for act in actividades:
        ef_fisica = act.ejecucion_fisica.all()
        ef_finan = act.ejecucion_financiera.all()

        prog_fis = sum(float(e.programado or 0) for e in ef_fisica)
        ejec_fis = sum(float(e.ejecutado or 0) for e in ef_fisica)
        prog_fin = sum(float(e.programado or 0) for e in ef_finan)
        ejec_fin = sum(float(e.ejecutado or 0) for e in ef_finan)

        avance_fis = (ejec_fis / prog_fis * 100) if prog_fis > 0 else 0
        avance_fin = (ejec_fin / prog_fin * 100) if prog_fin > 0 else 0

        # Determinar estado del semáforo
        if avance_fis >= 80:
            estado = '🟢 Verde'
            estado_fill = 'E8F5E9'
        elif avance_fis >= 50:
            estado = '🟡 Amarillo'
            estado_fill = 'FFF8E1'
        else:
            estado = '🔴 Rojo'
            estado_fill = 'FFEBEE'

        ws.cell(row=row, column=1, value=act.nombre[:80])
        ws.cell(row=row, column=2, value=round(prog_fis, 2)).number_format = '#,##0.00'
        ws.cell(row=row, column=3, value=round(ejec_fis, 2)).number_format = '#,##0.00'
        ws.cell(row=row, column=4, value=round(avance_fis, 1))
        ws.cell(row=row, column=5, value=round(prog_fin, 2)).number_format = '#,##0.00'
        ws.cell(row=row, column=6, value=round(ejec_fin, 2)).number_format = '#,##0.00'
        ws.cell(row=row, column=7, value=round(avance_fin, 1))
        ws.cell(row=row, column=8, value='')  # Causa — requiere input del usuario
        ws.cell(row=row, column=9, value=estado)

        for c in range(1, 10):
            ws.cell(row=row, column=c).border = BORDER_THIN
            ws.cell(row=row, column=c).font = Font(size=9)
            if c == 9:
                ws.cell(row=row, column=c).fill = PatternFill(
                    start_color=estado_fill, end_color=estado_fill, fill_type='solid')
        row += 1

    for col_letter, width in [('A', 35), ('B', 15), ('C', 15), ('D', 15),
                               ('E', 18), ('F', 18), ('G', 15), ('H', 30), ('I', 15)]:
        ws.column_dimensions[col_letter].width = width

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer, _build_response_filename('evaluacion_cuadro3', 'xlsx', gestion)
