"""Emisión del acta de priorización en PDF, tamaño oficio.

El PDF lo arma el servidor y no el navegador: `window.print()` deja la medida en
manos del diálogo de impresión y basta con que el usuario tenga carta o A4 por
defecto para que el acta salga escalada.
"""
import hashlib
import io
import json
from datetime import datetime

import segno
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

# Oficio: 21,6 x 33 cm. No es el Legal norteamericano, que mide 21,6 x 35,6.
OFICIO = (216 * mm, 330 * mm)


def hash_acta(datos):
    """Huella del CONTENIDO del acta, no de los bytes del archivo.

    El QR va impreso dentro del PDF, así que no puede contener el hash del PDF
    terminado: incrustarlo cambiaría el archivo y con él su hash. Lo que se
    firma es el contenido —quién priorizó, qué y por cuánto—, que es lo que
    hay que poder verificar, y se mantiene estable aunque cambie la plantilla.
    """
    canonico = {
        'acta': str(datos['acta_id']),
        'gestion': datos['gestion'],
        'distrito': datos['distrito'],
        'otb': datos['otb'],
        'presidente': datos['presidente'],
        'fecha': datos['fecha'],
        'proyectos': [
            {'nro': p['nro'], 'descripcion': p['descripcion'],
             'monto': f"{p['monto']:.2f}"}
            for p in datos['proyectos']
        ],
        'total': f"{datos['total']:.2f}",
    }
    crudo = json.dumps(canonico, ensure_ascii=False, sort_keys=True,
                       separators=(',', ':'))
    return hashlib.sha256(crudo.encode('utf-8')).hexdigest()


ENTIDAD = 'Gobierno Autonomo Municipal de Sacaba'


def contenido_qr(datos, huella, generado_en):
    """Lo que se lee al escanear el QR.

    Va en texto plano y sin tildes: los lectores de codigo de barras baratos
    que usan en ventanilla no manejan UTF-8 y devuelven simbolos rotos.
    """
    firmantes = ', '.join(
        f['nombre'] for f in (datos.get('firmas') or []) if f.get('nombre'))
    return '\n'.join([
        f"ACTA DE PRIORIZACION POA {datos['gestion']}",
        f"{datos['otb']} - {datos['distrito']}",
        f"Firmantes: {firmantes or 'sin registrar'}",
        f"Generada: {generado_en.strftime('%d/%m/%Y %H:%M')}",
        f"SHA-256: {huella}",
        f"{ENTIDAD} - POA {datos['gestion']}",
    ])


def _estilos():
    base = getSampleStyleSheet()
    return {
        'titulo': ParagraphStyle(
            'titulo', parent=base['Normal'], fontName='Helvetica-Bold',
            fontSize=14, leading=18, alignment=TA_CENTER, spaceAfter=2),
        'subtitulo': ParagraphStyle(
            'subtitulo', parent=base['Normal'], fontName='Helvetica-Bold',
            fontSize=12.5, leading=16, alignment=TA_CENTER),
        'cuerpo': ParagraphStyle(
            'cuerpo', parent=base['Normal'], fontName='Helvetica',
            fontSize=11.5, leading=17, alignment=TA_JUSTIFY),
        'celda': ParagraphStyle(
            'celda', parent=base['Normal'], fontName='Helvetica',
            fontSize=10.5, leading=14),
        'celda_cab': ParagraphStyle(
            'celda_cab', parent=base['Normal'], fontName='Helvetica-Bold',
            fontSize=10.5, leading=14, alignment=TA_CENTER),
        'nota': ParagraphStyle(
            'nota', parent=base['Normal'], fontName='Helvetica-Oblique',
            fontSize=10, leading=14, alignment=TA_JUSTIFY),
        'firma': ParagraphStyle(
            'firma', parent=base['Normal'], fontName='Helvetica-Bold',
            fontSize=10.5, leading=14, alignment=TA_CENTER),
        'firma_rol': ParagraphStyle(
            'firma_rol', parent=base['Normal'], fontName='Helvetica',
            fontSize=9.5, leading=12, alignment=TA_CENTER),
        'qr': ParagraphStyle(
            'qr', parent=base['Normal'], fontName='Helvetica',
            fontSize=7.5, leading=10, alignment=TA_CENTER,
            textColor=colors.HexColor('#555555')),
    }


def _qr(texto, lado=26 * mm):
    """El QR se dibuja en memoria: no se escribe ningún archivo temporal."""
    buffer = io.BytesIO()
    segno.make(texto, error='m').save(buffer, kind='png', scale=6, border=1)
    buffer.seek(0)
    return Image(buffer, width=lado, height=lado)


def generar_acta_pdf(datos, generado_en=None):
    """Devuelve (bytes del PDF, huella del contenido)."""
    huella = hash_acta(datos)
    generado_en = generado_en or datetime.now()
    est = _estilos()
    salida = io.BytesIO()
    # Márgenes amplios y parejos: el bloque queda centrado en la hoja.
    doc = SimpleDocTemplate(
        salida, pagesize=OFICIO,
        leftMargin=25 * mm, rightMargin=25 * mm,
        topMargin=24 * mm, bottomMargin=20 * mm,
        title=f"Acta de priorización {datos['otb']}",
        author='Gobierno Autónomo Municipal de Sacaba',
    )
    ancho = doc.width

    piezas = [
        Paragraph(datos['titulo'], est['titulo']),
        Paragraph(datos['subtitulo'], est['subtitulo']),
        Paragraph(datos['distrito'], est['subtitulo']),
        Spacer(1, 10 * mm),
        Paragraph(datos['encabezado'], est['cuerpo']),
        Spacer(1, 7 * mm),
    ]

    filas = [[Paragraph('N°', est['celda_cab']),
              Paragraph(datos['rotulo_descripcion'], est['celda_cab']),
              Paragraph(datos['rotulo_monto'], est['celda_cab'])]]
    for p in datos['proyectos']:
        filas.append([
            Paragraph(str(p['nro']), est['celda']),
            Paragraph(p['descripcion'], est['celda']),
            Paragraph(f"{p['monto']:,.0f}", est['celda']),
        ])
    filas.append([
        Paragraph('', est['celda']),
        Paragraph(f"<b>{datos['rotulo_total']}</b>", est['celda']),
        Paragraph(f"<b>{datos['total']:,.0f}</b>", est['celda']),
    ])

    tabla = Table(filas, colWidths=[12 * mm, ancho - 46 * mm, 34 * mm],
                  repeatRows=1)
    tabla.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.6, colors.HexColor('#444444')),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E8E8E8')),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#F3F3F3')),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    piezas.append(tabla)

    if datos.get('aclaracion'):
        piezas += [Spacer(1, 7 * mm),
                   Paragraph(datos['aclaracion'], est['cuerpo'])]
    if datos.get('nota'):
        piezas += [Spacer(1, 6 * mm), Paragraph(datos['nota'], est['nota'])]
    if datos.get('cierre'):
        piezas += [Spacer(1, 6 * mm), Paragraph(datos['cierre'], est['cuerpo'])]

    firmas = datos.get('firmas') or []
    if firmas:
        piezas.append(Spacer(1, 26 * mm))
        celdas = [[Paragraph('_' * 26, est['firma_rol']) for _ in firmas],
                  [Paragraph(f['nombre'] or ' ', est['firma']) for f in firmas],
                  [Paragraph(f['rol'], est['firma_rol']) for f in firmas]]
        tabla_firmas = Table(celdas, colWidths=[ancho / len(firmas)] * len(firmas))
        tabla_firmas.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ]))
        piezas.append(tabla_firmas)

    piezas += [
        Spacer(1, 12 * mm),
        # Mas grande que el minimo: el QR lleva seis lineas y con 26 mm los
        # modulos quedan demasiado finos para un lector de ventanilla.
        _qr(contenido_qr(datos, huella, generado_en), lado=32 * mm),
        Paragraph(huella, est['qr']),
        Paragraph(f'{ENTIDAD} · POA {datos["gestion"]} · '
                  f'generada el {generado_en.strftime("%d/%m/%Y %H:%M")}',
                  est['qr']),
    ]

    doc.build(piezas)
    return salida.getvalue(), huella
