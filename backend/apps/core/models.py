import uuid
from django.db import models
from django.conf import settings
from apps.gestion.models import GestionFiscal


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='+', editable=False
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='+', editable=False
    )

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class ActivableModel(models.Model):
    activo = models.BooleanField(default=True)

    class Meta:
        abstract = True


class VigenciaModel(models.Model):
    fecha_vigencia_desde = models.DateField()
    fecha_vigencia_hasta = models.DateField(null=True, blank=True)

    class Meta:
        abstract = True


class VersionableModel(models.Model):
    version = models.PositiveIntegerField(default=1)
    gestion = models.ForeignKey(
        GestionFiscal, on_delete=models.PROTECT, db_column='gestion',
        related_name='+', verbose_name='Gestión fiscal',
    )

    class Meta:
        abstract = True


class DemoDatasetManifest(models.Model):
    """Ownership manifest for an explicitly loaded demonstration dataset."""

    namespace = models.CharField(max_length=100, unique=True)
    gestion = models.ForeignKey(
        GestionFiscal, on_delete=models.PROTECT, db_column='gestion',
        related_name='+', verbose_name='Gestión fiscal',
    )
    payload = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'nucleo_manifesto_dataset_demo'
        ordering = ['namespace']

    def __str__(self):
        return self.namespace


class LegacyMigrationMap(models.Model):
    """Traza técnica legacy→V2 (ADR-004, WP-05).

    Registra cada registro legacy y su destino V2 durante la migración
    expand→backfill→reconciliar→cortar→retirar. Los checksums permiten
    reconciliación automática.
    """

    class Estados:
        PENDIENTE = 'pendiente'
        MIGRADO = 'migrado'
        RECONCILIADO = 'reconciliado'
        DISCREPANCIA = 'discrepancia'
        RETIRADO = 'retirado'

        CHOICES = [
            (PENDIENTE, 'Pendiente'),
            (MIGRADO, 'Migrado'),
            (RECONCILIADO, 'Reconciliado'),
            (DISCREPANCIA, 'Discrepancia'),
            (RETIRADO, 'Retirado'),
        ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    app_legacy = models.CharField(max_length=100)
    modelo_legacy = models.CharField(max_length=100)
    uuid_legacy = models.UUIDField()
    tipo_destino = models.CharField(max_length=100, blank=True, default='')
    uuid_destino = models.UUIDField(null=True, blank=True)
    lote = models.CharField(max_length=100, default='inicial')
    checksum = models.CharField(max_length=64, blank=True, default='')
    estado = models.CharField(
        max_length=20, choices=Estados.CHOICES, default=Estados.PENDIENTE,
    )
    observaciones = models.TextField(blank=True, default='')
    fecha = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'nucleo_mapa_migraciones_legacy'
        verbose_name = 'Mapa de migración legacy'
        verbose_name_plural = 'Mapas de migración legacy'
        ordering = ['app_legacy', 'modelo_legacy', 'uuid_legacy']
        constraints = [
            models.UniqueConstraint(
                fields=['app_legacy', 'modelo_legacy', 'uuid_legacy'],
                name='uniq_legacy_registro',
            ),
        ]

    def __str__(self):
        return f'{self.app_legacy}.{self.modelo_legacy}:{self.uuid_legacy}'
