"""Utilidades de auditoría de migración legacy→V2 (WP-05 / ADR-004)."""
import hashlib
import json
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


def serializar_registro(obj):
    """Serializa los campos concretos de una instancia a JSON estable.

    Orden alfabético por nombre de campo para que el checksum no dependa del
    orden de definición del modelo.
    """
    payload = {}
    for field in obj._meta.concrete_fields:
        name = field.name
        if name in ('created_at', 'updated_at', 'fecha'):
            continue  # campos de auditoría no forman parte del contenido
        value = getattr(obj, name, None)
        payload[name] = value

    def _default(v):
        if isinstance(v, UUID):
            return str(v)
        if isinstance(v, (date, datetime)):
            return v.isoformat()
        if isinstance(v, Decimal):
            return str(v)
        return str(v)

    return json.dumps(payload, sort_keys=True, default=_default, ensure_ascii=False)


def checksum_registro(obj):
    """SHA-256 del contenido canónico de un registro legacy."""
    return hashlib.sha256(
        serializar_registro(obj).encode('utf-8')
    ).hexdigest()


def modelos_de_aplicacion(apps=None, excluir=None):
    """Itera modelos de las apps del proyecto (módulo bajo 'apps.')."""
    from django.apps import apps as django_apps

    excluir = set(excluir or [])
    for model in django_apps.get_models():
        if not model._meta.app_config.name.startswith('apps.'):
            continue
        if model._meta.label in excluir:
            continue
        yield model
