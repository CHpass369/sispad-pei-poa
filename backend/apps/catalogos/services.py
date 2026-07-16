"""
Servicios de importación masiva de catálogos desde XLSX/CSV.
"""
import csv, io, hashlib, openpyxl
from decimal import Decimal
from datetime import datetime
from django.db import transaction
from django.utils import timezone

from .models import (
    ClasificadorInstitucional, RubroRecurso, ObjetoGasto,
    FuenteFinanciamiento, OrganismoFinanciador, EntidadTransferencia,
    FinalidadFuncion, UnidadMedida, TipoOperacion, TipoProducto,
    TipoProyecto, TipoFinanciamiento, VersionCatalogo
)

MODEL_MAP = {
    'clasificador_institucional': ClasificadorInstitucional,
    'rubro_recurso': RubroRecurso,
    'objeto_gasto': ObjetoGasto,
    'fuente_financiamiento': FuenteFinanciamiento,
    'organismo_financiador': OrganismoFinanciador,
    'entidad_transferencia': EntidadTransferencia,
    'finalidad_funcion': FinalidadFuncion,
    'unidad_medida': UnidadMedida,
    'tipo_operacion': TipoOperacion,
    'tipo_producto': TipoProducto,
    'tipo_proyecto': TipoProyecto,
    'tipo_financiamiento': TipoFinanciamiento,
}

REQUIRED_FIELDS = ['codigo', 'denominacion', 'gestion']


class ImportResult:
    def __init__(self):
        self.creados = 0
        self.actualizados = 0
        self.errores = []
        self.hash_archivo = ''

    def to_dict(self):
        return {
            'creados': self.creados,
            'actualizados': self.actualizados,
            'errores': self.errores[:10],
            'total_errores': len(self.errores),
            'hash_archivo': self.hash_archivo,
        }


def importar_catalogo_desde_xlsx(file_obj, tipo_catalogo: str, gestion: int) -> ImportResult:
    """Importa registros de catálogo desde un archivo XLSX."""
    result = ImportResult()
    Model = MODEL_MAP.get(tipo_catalogo)
    if not Model:
        result.errores.append(f'Tipo de catálogo inválido: {tipo_catalogo}')
        return result

    # Hash del archivo
    content = file_obj.read()
    result.hash_archivo = hashlib.sha256(content).hexdigest()
    file_obj.seek(0)

    wb = openpyxl.load_workbook(file_obj, read_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        result.errores.append('El archivo está vacío')
        return result

    headers = [str(h).strip().lower() if h else '' for h in rows[0]]

    # Validar campos requeridos
    for req in REQUIRED_FIELDS:
        if req not in headers:
            result.errores.append(f'Falta columna requerida: {req}')
            return result

    with transaction.atomic():
        for row_idx, row in enumerate(rows[1:], start=2):
            try:
                data = {}
                for i, header in enumerate(headers):
                    val = row[i] if i < len(row) else None
                    if val is not None:
                        data[header] = str(val).strip() if not isinstance(val, (int, float, Decimal)) else val

                codigo = data.get('codigo', '')
                denominacion = data.get('denominacion', '')

                if not codigo or not denominacion:
                    result.errores.append(f'Fila {row_idx}: código o denominación vacíos')
                    continue

                extra = {}
                for field in ['descripcion', 'fuente_normativa']:
                    if field in data:
                        extra[field] = data[field]

                obj, created = Model.objects.update_or_create(
                    codigo=codigo,
                    gestion=gestion,
                    defaults={
                        'denominacion': denominacion,
                        **extra,
                        'fecha_vigencia_desde': data.get('fecha_vigencia_desde', timezone.now().date()),
                        'metadatos_importacion': {
                            'archivo_hash': result.hash_archivo,
                            'importado_en': timezone.now().isoformat(),
                            'fila_origen': row_idx,
                        },
                    }
                )
                if created:
                    result.creados += 1
                else:
                    result.actualizados += 1

            except Exception as e:
                result.errores.append(f'Fila {row_idx}: {str(e)}')

    return result


def importar_catalogo_desde_csv(file_obj, tipo_catalogo: str, gestion: int) -> ImportResult:
    """Importa registros de catálogo desde un archivo CSV."""
    result = ImportResult()
    Model = MODEL_MAP.get(tipo_catalogo)
    if not Model:
        result.errores.append(f'Tipo de catálogo inválido: {tipo_catalogo}')
        return result

    content = file_obj.read().decode('utf-8-sig')
    result.hash_archivo = hashlib.sha256(content.encode()).hexdigest()
    file_obj.seek(0)

    reader = csv.DictReader(io.StringIO(content))

    for req in REQUIRED_FIELDS:
        if req not in reader.fieldnames:
            result.errores.append(f'Falta columna requerida: {req}')
            return result

    with transaction.atomic():
        for row_idx, row in enumerate(reader, start=2):
            try:
                codigo = row.get('codigo', '').strip()
                denominacion = row.get('denominacion', '').strip()

                if not codigo or not denominacion:
                    result.errores.append(f'Fila {row_idx}: código o denominación vacíos')
                    continue

                obj, created = Model.objects.update_or_create(
                    codigo=codigo,
                    gestion=gestion,
                    defaults={
                        'denominacion': denominacion,
                        'descripcion': row.get('descripcion', ''),
                        'fuente_normativa': row.get('fuente_normativa', ''),
                        'fecha_vigencia_desde': row.get('fecha_vigencia_desde', timezone.now().date()),
                        'metadatos_importacion': {
                            'archivo_hash': result.hash_archivo,
                            'importado_en': timezone.now().isoformat(),
                            'fila_origen': row_idx,
                        },
                    }
                )
                if created:
                    result.creados += 1
                else:
                    result.actualizados += 1

            except Exception as e:
                result.errores.append(f'Fila {row_idx}: {str(e)}')

    return result
