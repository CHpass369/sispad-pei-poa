"""Generación de documentos DOCX del expediente de preinversión (ITCP/EDTP).

Usa plantillas docxtpl versionadas. La conversión a PDF es opcional y no
bloquea la generación del DOCX (requiere LibreOffice headless).
"""
import json
from pathlib import Path

from django.conf import settings

from .models_preinversion import DocumentoGenerado

try:
    from docxtpl import DocxTemplate
except ImportError:  # pragma: no cover
    DocxTemplate = None


class ErrorGeneracionDocumento(RuntimeError):
    pass


def _dictar_condiciones(itcp):
    return list(
        itcp.condiciones.order_by('orden').values(
            'titulo', 'estado', 'hallazgo', 'plan_accion',
            'fuente', 'referencia_fuente',
        )
    )


def construir_contexto(proyecto, tipo_documento):
    """Contexto plano para la plantilla DOCX (docxtpl)."""
    contexto = {
        'project': {
            'code': proyecto.codigo_interno,
            'official_name': proyecto.nombre,
            'management_year': proyecto.gestion,
            'typology': (
                proyecto.get_tipologia_rm115_display()
                if proyecto.tipologia_rm115 else ''
            ),
            'district': proyecto.distrito,
            'community': proyecto.comunidad,
            'problem': proyecto.problema,
            'objective': proyecto.objetivo_general,
            'budget': str(proyecto.presupuesto_aprobado or proyecto.presupuesto_estimado or ''),
        },
        'components': list(
            proyecto.componentes.values(
                'codigo', 'nombre', 'descripcion', 'meta_fisica', 'unidad', 'presupuesto',
            )
        ),
        'beneficiaries': list(
            proyecto.grupos_beneficiarios.values(
                'tipo', 'descripcion', 'cantidad', 'unidad', 'fuente', 'fecha_fuente',
            )
        ),
    }
    if tipo_documento == 'ITCP':
        itcp = getattr(proyecto, 'itcp', None)
        if itcp is None:
            raise ErrorGeneracionDocumento('El proyecto no tiene ITCP')
        contexto['itcp'] = {
            'version': itcp.version,
            'justification': itcp.justificacion_iniciativa,
            'idea': itcp.idea_proyecto,
            'result': (
                itcp.get_resultado_preliminar_display()
                if itcp.resultado_preliminar else ''
            ),
            'conclusion': itcp.conclusiones,
            'recommendations': itcp.recomendaciones,
            'conditions': _dictar_condiciones(itcp),
        }
        tdr = getattr(proyecto, 'tdr', None)
        if tdr:
            contexto['tdr'] = {
                'objectives': tdr.objetivos,
                'scope': tdr.alcance,
                'methodology': tdr.metodologia,
                'duration_days': tdr.duracion_dias,
                'estimated_budget': str(tdr.presupuesto_referencial or ''),
            }
    else:
        edtp = getattr(proyecto, 'edtp', None)
        if edtp is None:
            raise ErrorGeneracionDocumento('El proyecto no tiene EDTP')
        contexto['edtp'] = {
            'version': edtp.version,
            'summary': edtp.resumen_ejecutivo,
            'evaluation_method': edtp.metodo_evaluacion,
            'viability_result': (
                edtp.get_resultado_viabilidad_display()
                if edtp.resultado_viabilidad else ''
            ),
            'conclusion': edtp.conclusiones,
            'recommendations': edtp.recomendaciones,
            'sections': list(
                edtp.secciones.order_by('orden').values(
                    'codigo', 'titulo', 'contenido',
                    'fuente', 'fecha_fuente', 'referencia_fuente',
                )
            ),
            'studies': list(
                edtp.estudios_tecnicos.values(
                    'tipo_estudio', 'titulo', 'estado', 'profesional',
                    'registro_profesional', 'fecha_estudio', 'conclusiones',
                )
            ),
            'cost_items': [
                {
                    'code': i.codigo, 'description': i.descripcion,
                    'unit': i.unidad, 'quantity': str(i.cantidad),
                    'unit_price': str(i.precio_unitario), 'subtotal': str(i.subtotal),
                }
                for i in edtp.items_costo.all()
            ],
            'financing': list(
                edtp.fuentes_financiamiento.values(
                    'codigo_fuente', 'nombre_fuente', 'monto', 'confirmada',
                )
            ),
        }
    return contexto


def seleccionar_plantilla(proyecto, tipo_documento):
    directorio = Path(settings.DOCUMENT_TEMPLATE_DIR)
    if tipo_documento == 'ITCP':
        return directorio / 'itcp_base.docx'
    if proyecto.tipologia_rm115 in {'IV', 'V'}:
        return directorio / 'edtp_institutional.docx'
    return directorio / 'edtp_base.docx'


def generar_documento(proyecto, tipo_documento, generado=None):
    """Genera DOCX (y PDF si hay LibreOffice). Actualiza `DocumentoGenerado`."""
    if DocxTemplate is None:  # pragma: no cover
        raise ErrorGeneracionDocumento(
            'docxtpl no está instalado; agregue la dependencia en requirements.txt'
        )
    import subprocess
    import tempfile
    from django.core.files import File

    plantilla = seleccionar_plantilla(proyecto, tipo_documento)
    if not plantilla.exists():
        raise ErrorGeneracionDocumento(f'No existe plantilla: {plantilla}')

    contexto = construir_contexto(proyecto, tipo_documento)
    generado = generado or DocumentoGenerado.objects.create(
        proyecto=proyecto, tipo_documento=tipo_documento,
    )
    generado.estado = 'procesando'
    generado.plantilla = plantilla.name
    generado.contexto = json.loads(json.dumps(contexto, default=str))
    generado.save()
    try:
        with tempfile.TemporaryDirectory() as tmp:
            salida = Path(tmp) / f'{proyecto.codigo_interno}_{tipo_documento}_v1.docx'
            tpl = DocxTemplate(plantilla)
            tpl.render(contexto)
            tpl.save(salida)
            with salida.open('rb') as fh:
                generado.archivo_docx.save(salida.name, File(fh), save=False)
            try:
                subprocess.run(
                    [
                        'libreoffice', '--headless', '--convert-to', 'pdf',
                        '--outdir', tmp, str(salida),
                    ],
                    check=True, capture_output=True, timeout=120,
                )
                pdf = salida.with_suffix('.pdf')
                if pdf.exists():
                    with pdf.open('rb') as fh:
                        generado.archivo_pdf.save(pdf.name, File(fh), save=False)
            except Exception as exc:  # noqa: BLE001
                generado.mensaje_error = f'DOCX generado; PDF pendiente: {exc}'
        generado.estado = 'completado'
        generado.save()
        return generado
    except Exception as exc:  # noqa: BLE001
        generado.estado = 'fallido'
        generado.mensaje_error = str(exc)
        generado.save()
        raise
