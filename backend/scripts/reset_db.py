"""
Reset completo de la base de datos para pruebas.
Borra todos los datos y corre migraciones + seeds.

Uso:
    python manage.py shell < scripts/reset_db.py
"""
from django.db import connection
from django.apps import apps
from django.conf import settings

print('Reset de base de datos de prueba...')

# Eliminar todas las tablas (excepto las de Django)
with connection.schema_editor() as schema_editor:
    models = apps.get_models()
    for model in models:
        app_label = model._meta.app_label
        if app_label.startswith('django_') or app_label == 'auth' or app_label == 'contenttypes':
            continue
        try:
            schema_editor.delete_model(model)
            print(f'  Eliminado: {model._meta.db_table}')
        except Exception as e:
            print(f'  Error eliminando {model._meta.db_table}: {e}')

print('Tablas eliminadas. Corra: python manage.py migrate && python manage.py shell < scripts/seed_catalogos.py && python manage.py shell < scripts/seed_reglas.py')
