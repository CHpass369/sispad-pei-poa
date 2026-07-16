import uuid
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


class GestionFiscal(models.Model):
    class Estado(models.TextChoices):
        PREPARACION = 'preparacion', 'Preparación'
        ABIERTA = 'abierta', 'Abierta'
        FORMULACION = 'formulacion', 'Formulación'
        REVISION = 'revision', 'Revisión'
        CONSOLIDACION = 'consolidacion', 'Consolidación'
        APROBACION = 'aprobacion', 'Aprobación'
        CERRADA = 'cerrada', 'Cerrada'
        ARCHIVADA = 'archivada', 'Archivada'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    anio = models.PositiveIntegerField(unique=True, verbose_name='Gestión fiscal')
    estado = models.CharField(max_length=20, choices=Estado, default=Estado.PREPARACION)
    descripcion = models.TextField(blank=True)
    anio_inicio_plurianual = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='Año inicial del horizonte plurianual'
    )
    anio_fin_plurianual = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='Año final del horizonte plurianual'
    )
    fecha_apertura = models.DateTimeField(null=True, blank=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    activa = models.BooleanField(default=True)

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='gestiones_creadas'
    )

    class Meta:
        verbose_name = 'Gestión fiscal'
        verbose_name_plural = 'Gestiones fiscales'
        ordering = ['-anio']

    def __str__(self):
        return f'Gestión {self.anio}'

    def clean(self):
        if self.anio_fin_plurianual and self.anio_inicio_plurianual:
            if self.anio_fin_plurianual <= self.anio_inicio_plurianual:
                raise ValidationError(
                    'El año final del horizonte plurianual debe ser posterior al inicial'
                )
            if self.anio < self.anio_inicio_plurianual or self.anio > self.anio_fin_plurianual:
                raise ValidationError(
                    'El año de gestión debe estar dentro del horizonte plurianual'
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class CicloFormulacion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    gestion = models.ForeignKey(
        GestionFiscal, on_delete=models.CASCADE,
        related_name='ciclos_formulacion'
    )
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    fecha_inicio = models.DateTimeField()
    fecha_cierre = models.DateTimeField()
    fecha_cierre_prorroga = models.DateTimeField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    orden = models.PositiveIntegerField(default=0)

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Ciclo de formulación'
        verbose_name_plural = 'Ciclos de formulación'
        ordering = ['gestion', 'orden']

    def __str__(self):
        return f'{self.nombre} - {self.gestion.anio}'


class EtapaFormulacion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ciclo = models.ForeignKey(
        CicloFormulacion, on_delete=models.CASCADE,
        related_name='etapas'
    )
    codigo = models.CharField(max_length=50)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    fecha_inicio = models.DateTimeField()
    fecha_cierre = models.DateTimeField()
    completada = models.BooleanField(default=False)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Etapa de formulación'
        verbose_name_plural = 'Etapas de formulación'
        ordering = ['ciclo', 'orden']
        unique_together = [('ciclo', 'codigo')]

    def __str__(self):
        return f'{self.ciclo.nombre} / {self.nombre}'
