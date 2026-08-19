"""Priorización POA: lo que cada OTB elige para la gestión siguiente.

Un acta por OTB, con hasta siete proyectos priorizados y su monto. De ahí salen
dos cosas: el acta oficial que firma el presidente, y las matrices acumulativas
que consolidan por distrito lo priorizado.
"""
import re
import uuid

from django.db import models

from apps.core.models import TimeStampedModel
from apps.territorio.models import Distrito, UnidadTerritorial


def normalizar(texto):
    """Clave de búsqueda: sin tildes, sin puntuación y en mayúsculas.

    El buscador del nombre de proyecto compara por palabras sueltas, y los
    nombres llegan escritos de mil formas —`ADQ.`, `ADQ`, `Adquisición`—.
    """
    texto = str(texto or '').upper()
    for original, plano in zip('ÁÉÍÓÚÜÑ', 'AEIOUUN'):
        texto = texto.replace(original, plano)
    return re.sub(r'\s+', ' ', re.sub(r'[^A-Z0-9 ]', ' ', texto)).strip()


class OrigenProyecto(models.TextChoices):
    SIGEP = 'SIGEP', 'Reporte SIGEP'
    HISTORICO = 'HISTORICO', 'Acta de gestiones anteriores'
    MANUAL = 'MANUAL', 'Cargado a mano'


class ProyectoCatalogo(TimeStampedModel):
    """Catálogo maestro que alimenta el buscador del nombre de proyecto.

    Convive lo que ya tiene código SISIN con lo que solo existe como nombre en
    actas anteriores: en las OTB se prioriza mayormente por tipo de obra, y esos
    nombres no están en el SIGEP.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.TextField(verbose_name='Nombre del proyecto')
    nombre_busqueda = models.TextField(
        db_index=True, verbose_name='Nombre normalizado')
    sisin = models.CharField(max_length=30, blank=True, db_index=True,
                             verbose_name='Código SISIN')
    categoria_programatica = models.CharField(
        max_length=60, blank=True, verbose_name='Categoría programática')
    denominacion_categoria = models.TextField(
        blank=True, verbose_name='Denominación de la categoría')
    origen = models.CharField(
        max_length=12, choices=OrigenProyecto.choices,
        default=OrigenProyecto.MANUAL, verbose_name='Origen')
    veces_priorizado = models.PositiveIntegerField(
        default=0, verbose_name='Veces priorizado')

    class Meta:
        verbose_name = 'Proyecto del catálogo'
        verbose_name_plural = 'Proyectos del catálogo'
        ordering = ['-veces_priorizado', 'nombre']
        constraints = [
            models.UniqueConstraint(fields=['nombre_busqueda', 'sisin'],
                                    name='proyecto_catalogo_unico'),
        ]

    def save(self, *args, **kwargs):
        self.nombre_busqueda = normalizar(self.nombre)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.sisin} · {self.nombre}' if self.sisin else self.nombre


class EstadosActa(models.TextChoices):
    BORRADOR = 'BORRADOR', 'Borrador'
    VALIDADO = 'VALIDADO', 'Validado'
    OBSERVADO = 'OBSERVADO', 'Observado'
    APROBADO = 'APROBADO', 'Aprobado'


class ActaPriorizacion(TimeStampedModel):
    """Acta de priorización de una OTB para una gestión."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    gestion = models.PositiveIntegerField(db_index=True, verbose_name='Gestión POA')
    numero = models.PositiveIntegerField(null=True, blank=True,
                                         verbose_name='Número de acta')
    distrito = models.ForeignKey(
        Distrito, on_delete=models.PROTECT, related_name='actas_priorizacion',
        verbose_name='Distrito')
    otb = models.CharField(max_length=300, verbose_name='OTB / Junta vecinal')
    unidad_territorial = models.ForeignKey(
        UnidadTerritorial, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='actas_priorizacion', verbose_name='Unidad territorial')
    presidente = models.CharField(max_length=200, verbose_name='Presidente')
    responsable_registro = models.CharField(
        max_length=200, blank=True, verbose_name='Responsable del registro')
    # Hay actas cargadas sin fecha en la planilla de origen: se importan
    # igual y se marcan como incompletas, porque descartarlas perdía 18 actas
    # con sus proyectos priorizados.
    fecha = models.DateField(null=True, blank=True,
                             verbose_name='Fecha de la priorización')
    estado = models.CharField(
        max_length=20, choices=EstadosActa.choices,
        default=EstadosActa.BORRADOR, verbose_name='Estado')
    observacion = models.TextField(blank=True, verbose_name='Observación')

    class Meta:
        verbose_name = 'Acta de priorización'
        verbose_name_plural = 'Actas de priorización'
        ordering = ['distrito__codigo', 'otb']
        constraints = [
            # Una OTB prioriza una sola vez por gestión.
            models.UniqueConstraint(fields=['gestion', 'distrito', 'otb'],
                                    name='acta_unica_por_otb_y_gestion'),
        ]

    @property
    def esta_completa(self):
        """El acta oficial no se puede emitir sin fecha ni sin proyectos."""
        return bool(self.fecha) and self.proyectos.exists()

    @property
    def monto_total(self):
        return sum((p.monto or 0) for p in self.proyectos.all())

    def __str__(self):
        return f'{self.otb} ({self.distrito.nombre}) POA {self.gestion}'


class ProyectoPriorizado(TimeStampedModel):
    """Un proyecto elegido en el acta, con su monto.

    La categoría programática se copia acá y no se lee del catálogo: el acta es
    un documento firmado, y lo que se priorizó no puede cambiar porque alguien
    edite el catálogo después.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    acta = models.ForeignKey(ActaPriorizacion, on_delete=models.CASCADE,
                             related_name='proyectos', verbose_name='Acta')
    orden = models.PositiveSmallIntegerField(default=1, verbose_name='Orden')
    nombre = models.TextField(verbose_name='Nombre del proyecto')
    catalogo = models.ForeignKey(
        ProyectoCatalogo, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='priorizaciones', verbose_name='Proyecto del catálogo')
    sisin = models.CharField(max_length=30, blank=True, verbose_name='Código SISIN')
    categoria_programatica = models.CharField(
        max_length=60, blank=True, verbose_name='Categoría programática')
    denominacion_categoria = models.TextField(
        blank=True, verbose_name='Denominación de la categoría')
    monto = models.DecimalField(max_digits=18, decimal_places=2, null=True,
                                blank=True, verbose_name='Monto Bs.')

    class Meta:
        verbose_name = 'Proyecto priorizado'
        verbose_name_plural = 'Proyectos priorizados'
        ordering = ['acta', 'orden']

    def __str__(self):
        return f'{self.orden}. {self.nombre[:60]}'


class PlantillaActa(TimeStampedModel):
    """Los textos del acta oficial, editables sin tocar código.

    La redacción del acta la fija la entidad y cambia entre gestiones. Vive en
    la base con marcadores entre llaves —{presidente}, {otb}, {distrito},
    {dia}, {mes}, {anio_letras}, {gestion}— que se reemplazan al emitir.
    """
    MARCADORES = ['presidente', 'otb', 'distrito', 'dia', 'mes', 'anio_letras',
                  'gestion', 'total']

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=120, verbose_name='Nombre de la plantilla')
    gestion = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name='Gestión',
        help_text='Vacío: sirve para cualquier gestión.')
    titulo = models.TextField(verbose_name='Título')
    subtitulo = models.TextField(blank=True, verbose_name='Subtítulo')
    encabezado = models.TextField(verbose_name='Párrafo de encabezado')
    rotulo_descripcion = models.CharField(
        max_length=80, default='DESCRIPCION', verbose_name='Rótulo de la columna')
    rotulo_monto = models.CharField(
        max_length=80, default='MONTO BS.-', verbose_name='Rótulo del monto')
    rotulo_total = models.CharField(
        max_length=80, default='TOTAL', verbose_name='Rótulo del total')
    aclaracion = models.TextField(
        blank=True, verbose_name='Aclaración sobre los recursos',
        help_text='Párrafo que va debajo de la tabla de proyectos.')
    nota = models.TextField(blank=True, verbose_name='Nota al pie')
    cierre = models.TextField(blank=True, verbose_name='Párrafo de cierre')
    firmas = models.JSONField(
        default=list, blank=True,
        verbose_name='Firmas',
        help_text='Lista de {"rol": "...", "campo": "presidente|responsable"}.')
    activa = models.BooleanField(default=True, verbose_name='Activa')

    class Meta:
        verbose_name = 'Plantilla de acta'
        verbose_name_plural = 'Plantillas de acta'
        ordering = ['-gestion', 'nombre']

    def render(self, valores):
        """Reemplaza los marcadores. No usa format(): un texto con llaves
        sueltas escrito por el usuario reventaría la emisión del acta."""
        def aplicar(texto):
            for clave in self.MARCADORES:
                texto = str(texto or '').replace(
                    '{' + clave + '}', str(valores.get(clave, '')))
            return texto
        return {
            'titulo': aplicar(self.titulo),
            'subtitulo': aplicar(self.subtitulo),
            'encabezado': aplicar(self.encabezado),
            'rotulo_descripcion': self.rotulo_descripcion,
            'rotulo_monto': self.rotulo_monto,
            'rotulo_total': self.rotulo_total,
            'aclaracion': aplicar(self.aclaracion),
            'nota': aplicar(self.nota),
            'cierre': aplicar(self.cierre),
        }

    def __str__(self):
        return f'{self.nombre} ({self.gestion or "todas las gestiones"})'
