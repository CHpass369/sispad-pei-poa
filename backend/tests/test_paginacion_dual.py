"""Tests de la paginación DUAL (Fase C del plan de optimización Postgres).

Verifican que:
- el modo página (por defecto) mantiene el contrato DRF del frontend
  (`{count, results, next, previous}` con `?page=N` y `next` como URL de
  página);
- el modo cursor (opt-in con `?cursor=`) devuelve el MISMO contrato, con
  `next/previous` como URLs de cursor completas;
- el orden por defecto de auditoría es `-creado_en`;
- las importaciones siguen paginadas en modo página (smoke) y soportan
  cursor.
"""
from urllib.parse import parse_qs, urlparse

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from datetime import timedelta

from apps.auditoria.models import EventoAuditoria
from apps.auditoria.services import registrar_evento
from apps.budget.models import BudgetImport

EVENTOS_URL = '/api/v1/eventos/'
IMPORTS_URL = '/api/v2/sis-poa/budget/imports/'


def _crear_eventos(cantidad):
    """Crea eventos y les fija `creado_en` distintos (el modelo lo auto-fija).

    `creado_en` es auto_now_add con resolución de milisegundos: crearlos en
    secuencia puede dejar timestamps idénticos, lo que volvería el orden
    ambiguo. Con `update` directo se garantiza un orden estricto y
    determinista: evento i más viejo que evento i+1.
    """
    eventos = [
        registrar_evento(
            None, EventoAuditoria.Accion.CREAR, 'Allocation', f'ev-{i}',
            resumen=f'Evento {i}', gestion=2026,
        )
        for i in range(cantidad)
    ]
    base = timezone.now() - timedelta(minutes=cantidad)
    for i, evento in enumerate(eventos):
        EventoAuditoria.objects.filter(pk=evento.pk).update(
            creado_en=base + timedelta(seconds=i),
        )
    return eventos


def _parametro_de(url, nombre):
    """Extrae un query param de una URL absoluta de la API."""
    return parse_qs(urlparse(url).query)[nombre][0]


def test_modo_page_por_defecto(auth_client):
    _crear_eventos(26)
    resp = auth_client.get(EVENTOS_URL)
    assert resp.status_code == 200
    data = resp.data
    assert data['count'] == 26
    assert len(data['results']) == 25
    assert data['next'] is not None
    assert 'page=2' in data['next']
    assert 'cursor=' not in data['next']
    assert data['previous'] is None

    # La navegación por número de página del frontend sigue intacta.
    resp2 = auth_client.get(EVENTOS_URL, {'page': 2})
    assert resp2.status_code == 200
    assert resp2.data['count'] == 26
    assert len(resp2.data['results']) == 1


def test_modo_cursor_disponible(auth_client):
    _crear_eventos(26)
    # `?cursor=` (vacío) opta por el modo cursor desde la primera página.
    resp = auth_client.get(EVENTOS_URL, {'cursor': ''})
    assert resp.status_code == 200
    data = resp.data
    assert data['count'] == 26
    assert len(data['results']) == 25
    assert data['next'] is not None
    assert 'cursor=' in data['next']
    assert 'page=' not in data['next']
    assert data['previous'] is None
    ids_primera = {fila['id'] for fila in data['results']}

    # Segunda página siguiendo el cursor devuelto.
    cursor = _parametro_de(data['next'], 'cursor')
    resp2 = auth_client.get(EVENTOS_URL, {'cursor': cursor})
    assert resp2.status_code == 200
    data2 = resp2.data
    assert data2['count'] == 26
    assert len(data2['results']) == 1
    assert data2['next'] is None
    assert data2['previous'] is not None
    assert 'cursor=' in data2['previous']

    # Sin solapamientos ni filas perdidas entre páginas.
    ids = ids_primera | {fila['id'] for fila in data2['results']}
    assert len(ids) == 26


def test_auditoria_orden_desc_por_creado(auth_client):
    _crear_eventos(3)
    resp = auth_client.get(EVENTOS_URL)
    assert resp.status_code == 200
    fechas = [fila['creado_en'] for fila in resp.data['results']]
    assert len(fechas) == 3
    assert fechas == sorted(fechas, reverse=True)

    # El modo cursor respeta el mismo orden.
    resp_cursor = auth_client.get(EVENTOS_URL, {'cursor': ''})
    fechas_cursor = [fila['creado_en'] for fila in resp_cursor.data['results']]
    assert fechas_cursor == fechas


def test_importaciones_paginadas(auth_client, gestion, admin_user):
    importacion = BudgetImport.objects.create(
        gestion=gestion,
        archivo=SimpleUploadedFile('planilla.xlsx', b'datos'),
        creado_por=admin_user,
    )
    resp = auth_client.get(IMPORTS_URL)
    assert resp.status_code == 200
    assert resp.data['count'] == 1
    assert len(resp.data['results']) == 1
    assert resp.data['results'][0]['id'] == importacion.id

    # El modo cursor también está disponible en importaciones (mismo contrato).
    resp_cursor = auth_client.get(IMPORTS_URL, {'cursor': ''})
    assert resp_cursor.status_code == 200
    assert resp_cursor.data['count'] == 1
    assert len(resp_cursor.data['results']) == 1
    assert resp_cursor.data['next'] is None
    assert resp_cursor.data['previous'] is None
