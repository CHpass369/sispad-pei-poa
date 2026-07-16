"""
Script para migrar archivos existentes de media/ local a MinIO.

Uso:
    python manage.py shell < scripts/migrar_archivos_a_minio.py

Requiere USE_S3=True y configuración de MinIO en el entorno.
"""
import os
from django.conf import settings
from django.core.files.storage import default_storage
from apps.documentos.models import DocumentoAdjunto

USE_S3 = getattr(settings, 'USE_S3', False)
if not USE_S3:
    print("USE_S3=False. Activar MinIO primero con USE_S3=True")
    exit(1)

migrados = 0
errores = 0
for doc in DocumentoAdjunto.objects.filter(archivo__isnull=False):
    try:
        ruta_local = doc.archivo.path
        if os.path.exists(ruta_local):
            with open(ruta_local, 'rb') as f:
                nombre_guardado = default_storage.save(doc.archivo.name, f)
            doc.archivo.name = nombre_guardado
            doc.save(update_fields=['archivo'])
            migrados += 1
            print(f"✅ {doc.nombre} → {nombre_guardado}")
        else:
            print(f"⚠️  {doc.nombre} — archivo local no encontrado en {ruta_local}")
    except Exception as e:
        errores += 1
        print(f"❌ {doc.nombre}: {e}")

print(f"\nMigrados: {migrados}, Errores: {errores}")
