import uuid
from django.db import models
from django.conf import settings


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
    gestion = models.PositiveIntegerField()

    class Meta:
        abstract = True
