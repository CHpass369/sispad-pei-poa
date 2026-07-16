"""
Configuración de almacenamiento S3 (MinIO).

Se activa cuando USE_S3=True en el entorno.
Si USE_S3=False (default), todo sigue usando FileSystemStorage local.

Importado desde settings.py al final del archivo.
"""
import os

USE_S3 = os.environ.get('USE_S3', 'False').lower() in ('true', '1', 'yes')

if USE_S3:
    AWS_ACCESS_KEY_ID = os.environ.get('MINIO_ROOT_USER', '')
    AWS_SECRET_ACCESS_KEY = os.environ.get('MINIO_ROOT_PASSWORD', '')
    AWS_STORAGE_BUCKET_NAME = os.environ.get('MINIO_BUCKET_NAME', 'sispoa-docs')
    AWS_S3_ENDPOINT_URL = os.environ.get('MINIO_ENDPOINT', 'http://sispoa-minio:9000')
    AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'us-east-1')
    AWS_S3_SIGNATURE_VERSION = 's3v4'
    AWS_DEFAULT_ACL = 'private'
    AWS_QUERYSTRING_AUTH = True
    AWS_QUERYSTRING_EXPIRE = 3600
    AWS_S3_FILE_OVERWRITE = False
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }

    # FileField → S3 automático
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

    # Media URL apunta a S3
    MEDIA_URL = f'{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/'
else:
    # Almacenamiento local (default)
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
