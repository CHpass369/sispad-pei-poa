"""Emisión del acta de priorización en PDF, tamaño oficio.

El PDF lo arma el servidor y no el navegador: `window.print()` deja la medida en
manos del diálogo de impresión y basta con que el usuario tenga carta o A4 por
defecto para que el acta salga escalada.
"""
import hashlib
import io
import json
import re
from datetime import datetime

import segno
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
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
            fontSize=13.5, leading=17, alignment=TA_CENTER, spaceAfter=2),
        'subtitulo': ParagraphStyle(
            'subtitulo', parent=base['Normal'], fontName='Helvetica-Bold',
            fontSize=11.8, leading=15, alignment=TA_CENTER),
        'cuerpo': ParagraphStyle(
            'cuerpo', parent=base['Normal'], fontName='Helvetica',
            fontSize=10.7, leading=14.5, alignment=TA_JUSTIFY),
        'cuerpo_peq': ParagraphStyle(
            'cuerpo_peq', parent=base['Normal'], fontName='Helvetica',
            fontSize=9.2, leading=12, alignment=TA_JUSTIFY),
        'celda': ParagraphStyle(
            'celda', parent=base['Normal'], fontName='Helvetica',
            fontSize=10.0, leading=12.5),
        'celda_cab': ParagraphStyle(
            'celda_cab', parent=base['Normal'], fontName='Helvetica-Bold',
            fontSize=10.0, leading=12.5, alignment=TA_CENTER),
        'seccion_titulo': ParagraphStyle(
            'seccion_titulo', parent=base['Normal'], fontName='Helvetica-Bold',
            fontSize=9.8, leading=12, alignment=TA_CENTER, spaceAfter=2),
        'principio': ParagraphStyle(
            'principio', parent=base['Normal'], fontName='Helvetica',
            fontSize=8.3, leading=10.2, alignment=TA_JUSTIFY),
        'firma': ParagraphStyle(
            'firma', parent=base['Normal'], fontName='Helvetica-Bold',
            fontSize=10.2, leading=13, alignment=TA_CENTER),
        'firma_rol': ParagraphStyle(
            'firma_rol', parent=base['Normal'], fontName='Helvetica',
            fontSize=9.2, leading=11, alignment=TA_CENTER),
        'qr': ParagraphStyle(
            'qr', parent=base['Normal'], fontName='Helvetica',
            fontSize=7.0, leading=9, alignment=TA_CENTER,
            textColor=colors.HexColor('#555555')),
    }


def _qr(texto, lado=26 * mm):
    """El QR se dibuja en memoria: no se escribe ningún archivo temporal."""
    buffer = io.BytesIO()
    segno.make(texto, error='m').save(buffer, kind='png', scale=6, border=1)
    buffer.seek(0)
    return Image(buffer, width=lado, height=lado)



def _monto_bs(valor):
    """Formatea 1234567.8 como 1.234.567,80."""
    numero = float(valor or 0)
    return (
        f"{numero:,.2f}"
        .replace(",", "_")
        .replace(".", ",")
        .replace("_", ".")
    )

def _items_numerados(texto):
    """Convierte el bloque de principios en una lista.

    Funciona tanto si vienen:

        1. Principio uno.
        2. Principio dos.

    como si todo está en una sola línea:

        1. Principio uno. 2. Principio dos. 3. Principio tres.
    """
    texto = str(texto or '')

    texto = texto.replace('\r', ' ')
    texto = texto.replace('\n', ' ')
    texto = re.sub(r'\s+', ' ', texto).strip()

    if not texto:
        return []

    partes = re.split(
        r'(?=\b\d+\.\s+)',
        texto
    )

    resultado = []

    for parte in partes:
        parte = parte.strip()

        if re.match(r'^\d+\.\s+', parte):
            resultado.append(parte)

    return resultado or [texto]


def _tabla_principios(items, estilo, ancho):
    """Un solo recuadro con los principios distribuidos en 2 columnas."""

    if not items:
        return Spacer(1, 0)

    filas = []

    for i in range(0, len(items), 2):

        izquierda = Paragraph(
            items[i],
            estilo
        )

        if i + 1 < len(items):
            derecha = Paragraph(
                items[i + 1],
                estilo
            )
        else:
            derecha = Paragraph('', estilo)

        filas.append([
            izquierda,
            derecha
        ])

    separacion = 4 * mm

    tabla = Table(
        filas,
        colWidths=[
            (ancho - separacion) / 2,
            (ancho - separacion) / 2,
        ],
        hAlign='LEFT'
    )

    tabla.setStyle(TableStyle([

        # Recuadro exterior
        (
            'BOX',
            (0, 0),
            (-1, -1),
            0.7,
            colors.HexColor('#555555')
        ),

        # Línea central entre ambas columnas
        (
            'LINEAFTER',
            (0, 0),
            (0, -1),
            0.35,
            colors.HexColor('#BBBBBB')
        ),

        (
            'VALIGN',
            (0, 0),
            (-1, -1),
            'TOP'
        ),

        (
            'LEFTPADDING',
            (0, 0),
            (-1, -1),
            4
        ),

        (
            'RIGHTPADDING',
            (0, 0),
            (-1, -1),
            4
        ),

        (
            'TOPPADDING',
            (0, 0),
            (-1, -1),
            3
        ),

        (
            'BOTTOMPADDING',
            (0, 0),
            (-1, -1),
            3
        ),

    ]))

    return tabla



def _dibujar_qr_fijo(canvas, doc, datos, huella, generado_en):
    """QR fijo en la esquina superior derecha de la primera página."""
    buffer = io.BytesIO()

    segno.make(
        contenido_qr(datos, huella, generado_en),
        error='m'
    ).save(
        buffer,
        kind='png',
        scale=6,
        border=1
    )

    buffer.seek(0)

    lado = 20 * mm

    # Dentro del margen superior de 40 mm.
    # 25 mm desde el borde derecho.
    x = OFICIO[0] - 25 * mm - lado

    # 10 mm desde el borde superior.
    y = OFICIO[1] - 10 * mm - lado

    canvas.saveState()

    canvas.drawImage(
        ImageReader(buffer),
        x,
        y,
        width=lado,
        height=lado,
        preserveAspectRatio=True,
        mask='auto'
    )

    canvas.setFont('Helvetica', 5.8)
    canvas.setFillColor(colors.HexColor('#555555'))

    canvas.drawCentredString(
        x + lado / 2,
        y - 3 * mm,
        'VERIFICACIÓN'
    )

    canvas.restoreState()


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
        topMargin=40 * mm, bottomMargin=20 * mm,
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
            Paragraph(_monto_bs(p['monto']), est['celda']),
        ])
    filas.append([
        Paragraph('', est['celda']),
        Paragraph(f"<b>{datos['rotulo_total']}</b>", est['celda']),
        Paragraph(f"<b>{_monto_bs(datos['total'])}</b>", est['celda']),
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


    if datos.get('es_pavimento'):

        texto_pavimento = (
            '<b>CONDICIÓN PARA PROYECTOS DE PAVIMENTO FLEXIBLE POR ADMINISTRACIÓN DIRECTA</b><br/>'
            'Se aclara que, para la ejecución de proyectos de pavimento '
            'flexible bajo la modalidad de administración directa, la '
            'composición del presupuesto priorizado se distribuirá de la '
            'siguiente manera: <b>75% destinado a materiales e insumos '
            'y 25% destinado a la ejecución del proyecto</b>, '
            'comprendiendo este último componente el uso de equipo pesado, '
            'planta de asfalto, logística, combustible y personal.'
        )

        cuadro_pavimento = Table(
            [[Paragraph(
                texto_pavimento,
                est['cuerpo_peq']
            )]],
            colWidths=[ancho],
            hAlign='LEFT'
        )

        cuadro_pavimento.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.7,
             colors.HexColor('#555555')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))

        piezas += [
            Spacer(1, 4 * mm),
            cuadro_pavimento,
        ]
    if datos.get('nota'):
        piezas += [
            Spacer(1, 5 * mm),
            Paragraph(
                datos['nota'],
                est['cuerpo_peq']
            ),
        ]
    if datos.get('cierre'):
        piezas += [
            Spacer(1, 5 * mm),
            Paragraph(
                datos['cierre'],
                est['cuerpo_peq']
            ),
        ]

    firmas = datos.get('firmas') or []
    if firmas:
        piezas.append(Spacer(1, 16 * mm))
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
        Paragraph(huella, est['qr']),
        Paragraph(f'{ENTIDAD} · POA {datos["gestion"]} · '
                  f'generada el {generado_en.strftime("%d/%m/%Y %H:%M")}',
                  est['qr']),
    ]

    def primera_pagina(canvas, documento):
        _dibujar_qr_fijo(
            canvas,
            documento,
            datos,
            huella,
            generado_en
        )

    doc.build(
        piezas,
        onFirstPage=primera_pagina
    )
    return salida.getvalue(), huella
