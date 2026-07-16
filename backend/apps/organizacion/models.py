import uuid
from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel, ActivableModel, VigenciaModel


class TipoUnidad(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=200)
    nivel = models.PositiveIntegerField(help_text='Nivel jerárquico (1=superior)')
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Tipo de unidad'
        verbose_name_plural = 'Tipos de unidad'
        ordering = ['nivel', 'codigo']

    def __str__(self):
        return f'{self.nombre} ({self.codigo})'


class UnidadOrganizacional(TimeStampedModel, ActivableModel, VigenciaModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=20)
    nombre = models.CharField(max_length=300)
    sigla = models.CharField(max_length=30, blank=True)
    tipo = models.ForeignKey(TipoUnidad, on_delete=models.PROTECT, related_name='unidades')
    padre = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True,
        related_name='hijas'
    )
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='unidades_responsable'
    )
    gestion = models.PositiveIntegerField()
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Unidad organizacional'
        verbose_name_plural = 'Unidades organizacionales'
        ordering = ['gestion', 'tipo__nivel', 'orden']
        unique_together = [('codigo', 'gestion')]

    def __str__(self):
        return f'{self.nombre} ({self.codigo})'


class DireccionAdministrativa(TimeStampedModel, ActivableModel, VigenciaModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=10)
    nombre = models.CharField(max_length=200)
    gestion = models.PositiveIntegerField()
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='das_responsable'
    )

    class Meta:
        verbose_name = 'Dirección Administrativa'
        verbose_name_plural = 'Direcciones Administrativas'
        unique_together = [('codigo', 'gestion')]
        ordering = ['gestion', 'codigo']

    def __str__(self):
        return f'{self.codigo} - {self.nombre}'


class UnidadEjecutora(TimeStampedModel, ActivableModel, VigenciaModel):
    """
    Una UE solo puede depender de una DA para una gestión.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=10)
    nombre = models.CharField(max_length=200)
    da = models.ForeignKey(
        DireccionAdministrativa, on_delete=models.PROTECT,
        related_name='unidades_ejecutoras'
    )
    unidad_organizacional = models.ForeignKey(
        UnidadOrganizacional, on_delete=models.PROTECT,
        related_name='ues_asociadas', null=True, blank=True
    )
    gestion = models.PositiveIntegerField()
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='ues_responsable'
    )

    class Meta:
        verbose_name = 'Unidad Ejecutora'
        verbose_name_plural = 'Unidades Ejecutoras'
        unique_together = [('codigo', 'da', 'gestion')]
        ordering = ['gestion', 'da__codigo', 'codigo']

    def __str__(self):
        return f'UE {self.codigo} - {self.nombre} ({self.da.codigo})'


class AsignacionUsuarioUnidad(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='asignaciones_unidad'
    )
    unidad = models.ForeignKey(
        UnidadOrganizacional, on_delete=models.CASCADE,
        related_name='asignaciones_usuarios'
    )
    es_responsable_poa = models.BooleanField(default=False)
    gestion = models.PositiveIntegerField()
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Asignación usuario-unidad'
        verbose_name_plural = 'Asignaciones usuario-unidad'
        unique_together = [('usuario', 'unidad', 'gestion')]

    def __str__(self):
        return f'{self.usuario.email} -> {self.unidad.nombre} ({self.gestion})'
