from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel


class SectorPAD(TimeStampedModel):
    """Catálogo de sectores del PAD (salud, educación, infraestructura, etc.)"""
    codigo = models.CharField(max_length=10, unique=True)
    nombre = models.CharField(max_length=200)

    class Meta:
        verbose_name = 'Sector PAD'
        verbose_name_plural = 'Sectores PAD'
        ordering = ['codigo']

    def __str__(self):
        return f'[{self.codigo}] {self.nombre}'


class PoliticaPAD(TimeStampedModel):
    """Política o directriz del PAD (nivel estratégico departamental)"""
    codigo = models.CharField(max_length=20)
    nombre = models.CharField(max_length=500)
    descripcion = models.TextField(blank=True)
    gestion = models.PositiveIntegerField(verbose_name='Gestión')

    class Meta:
        verbose_name = 'Política PAD'
        verbose_name_plural = 'Políticas PAD'
        unique_together = [('codigo', 'gestion')]
        ordering = ['gestion', 'codigo']

    def __str__(self):
        return f'[{self.codigo}] {self.nombre}'


class LineamientoEstrategico(TimeStampedModel):
    """Lineamiento estratégico del PAD, asociado a una política"""
    codigo = models.CharField(max_length=20)
    nombre = models.CharField(max_length=500)
    politica = models.ForeignKey(
        PoliticaPAD, on_delete=models.CASCADE,
        related_name='lineamientos'
    )
    gestion = models.PositiveIntegerField(verbose_name='Gestión')

    class Meta:
        verbose_name = 'Lineamiento estratégico'
        verbose_name_plural = 'Lineamientos estratégicos'
        unique_together = [('codigo', 'politica', 'gestion')]
        ordering = ['gestion', 'codigo']

    def __str__(self):
        return f'[{self.codigo}] {self.nombre}'


class ResultadoTerritorial(TimeStampedModel):
    """Resultado departamental/territorial del PAD (Matriz A - Cuadro No 53)"""

    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('enviado', 'Enviado para aprobación'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado con observaciones'),
    ]

    codigo = models.CharField(max_length=50)
    nombre = models.TextField()
    lineamiento = models.ForeignKey(
        LineamientoEstrategico, on_delete=models.CASCADE,
        related_name='resultados'
    )
    sector = models.ForeignKey(
        SectorPAD, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='resultados'
    )
    indicador = models.TextField(blank=True)
    formula = models.TextField(blank=True)
    linea_base = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True
    )
    meta_2030 = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True
    )
    cod_geografico = models.CharField(
        max_length=20, blank=True, default='',
        verbose_name='Código geográfico'
    )
    # DEPRECATED: Se migrarán a ProgramacionAnualPAD en Futura versión
    programacion_fisica = models.JSONField(
        null=True, blank=True,
        help_text='[DEPRECATED] Usar programaciones en ProgramacionAnualPAD'
    )
    # DEPRECATED: Se migrarán a ProgramacionAnualPAD en Futura versión
    programacion_financiera = models.JSONField(
        null=True, blank=True,
        help_text='[DEPRECATED] Usar programaciones en ProgramacionAnualPAD'
    )
    gestion = models.PositiveIntegerField(verbose_name='Gestión')
    estado = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default='borrador',
        verbose_name='Estado',
    )

    class Meta:
        verbose_name = 'Resultado territorial'
        verbose_name_plural = 'Resultados territoriales'
        unique_together = [('codigo', 'lineamiento', 'gestion')]
        ordering = ['gestion', 'codigo']
        indexes = [
            models.Index(fields=['gestion', 'lineamiento']),
        ]

    def __str__(self):
        return f'[{self.codigo}] {self.nombre[:100]}'


class ArticulacionLog(models.Model):
    """Registro de cambios en el flujo de aprobación del PAD"""

    entidad = models.CharField(
        max_length=50,
        help_text="Nombre del modelo: 'resultado', 'producto'",
    )
    entidad_id = models.CharField(max_length=100)
    accion = models.CharField(
        max_length=50,
        help_text="Acción: 'crear', 'modificar', 'enviar', 'aprobar', 'rechazar'",
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    detalle = models.JSONField(null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Log de articulación'
        verbose_name_plural = 'Logs de articulación'
        ordering = ['-creado_en']

    def __str__(self):
        return f'{self.entidad}#{self.entidad_id} — {self.accion} ({self.creado_en})'


class ProductoTerritorial(TimeStampedModel):
    """Producto (bien o servicio) del PAD, asociado a un resultado territorial"""
    codigo = models.CharField(max_length=50)
    nombre = models.TextField()
    resultado = models.ForeignKey(
        ResultadoTerritorial, on_delete=models.CASCADE,
        related_name='productos'
    )
    territorializacion = models.TextField(
        blank=True,
        help_text='Ámbito territorial del producto'
    )
    responsable = models.CharField(
        max_length=300, blank=True,
        help_text='Unidad/instancia responsable'
    )
    indicador = models.TextField(blank=True)
    formula = models.TextField(blank=True)
    linea_base = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True
    )
    meta_2030 = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True
    )
    cuenta_con_financiamiento = models.CharField(
        max_length=2,
        choices=[('SI', 'SÍ'), ('NO', 'NO')],
        default='NO',
        verbose_name='Cuenta con financiamiento'
    )
    presupuesto_total_pad = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True,
        verbose_name='Presupuesto total PAD'
    )
    # DEPRECATED: Se migrarán a ProgramacionAnualPAD en Futura versión
    programacion_fisica = models.JSONField(
        null=True, blank=True,
        help_text='[DEPRECATED] Usar programaciones en ProgramacionAnualPAD'
    )
    # DEPRECATED: Se migrarán a ProgramacionAnualPAD en Futura versión
    programacion_financiera = models.JSONField(
        null=True, blank=True,
        help_text='[DEPRECATED] Usar programaciones en ProgramacionAnualPAD'
    )
    gestion = models.PositiveIntegerField(verbose_name='Gestión')

    class Meta:
        verbose_name = 'Producto territorial'
        verbose_name_plural = 'Productos territoriales'
        unique_together = [('codigo', 'resultado', 'gestion')]
        ordering = ['gestion', 'codigo']

    def __str__(self):
        return f'[{self.codigo}] {self.nombre[:100]}'


class ProgramacionAnualPAD(TimeStampedModel):
    """Programación anual normalizada (física o financiera) para resultado o producto territorial

    Reemplaza los JSONFields programacion_fisica/programacion_financiera con una
    estructura relacional: una fila por año y tipo.
    """
    resultado = models.ForeignKey(
        'ResultadoTerritorial', on_delete=models.CASCADE,
        null=True, blank=True, related_name='programaciones'
    )
    producto = models.ForeignKey(
        'ProductoTerritorial', on_delete=models.CASCADE,
        null=True, blank=True, related_name='programaciones'
    )
    anio = models.PositiveIntegerField(verbose_name='Año')
    tipo = models.CharField(
        max_length=20,
        choices=[('fisica', 'Física'), ('financiera', 'Financiera')],
        verbose_name='Tipo'
    )
    valor = models.DecimalField(
        max_digits=20, decimal_places=4, verbose_name='Valor'
    )

    class Meta:
        verbose_name = 'Programación anual PAD'
        verbose_name_plural = 'Programaciones anuales PAD'
        ordering = ['anio', 'tipo']
        unique_together = [('resultado', 'producto', 'anio', 'tipo')]

    def clean(self):
        if not self.resultado and not self.producto:
            raise ValidationError(
                'Debe especificar al menos resultado o producto territorial'
            )
        if self.valor is not None and self.valor < 0:
            raise ValidationError({'valor': 'El valor no puede ser negativo'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.resultado:
            target = f'Resultado {self.resultado_id}'
        elif self.producto:
            target = f'Producto {self.producto_id}'
        else:
            target = 'Sin referencia'
        return f'{target} - {self.anio} ({self.get_tipo_display()}): {self.valor}'


class ArticulacionSIPEB(TimeStampedModel):
    """Vinculación del PAD con instrumentos nacionales y sectoriales (Matriz B)

    Articula: PGDESA → PDESA → PDS → PAD, incluyendo compromisos internacionales
    (ODS, NDC, NDT) y la iniciativa 30x30.
    """
    resultado = models.OneToOneField(
        ResultadoTerritorial, on_delete=models.CASCADE,
        related_name='articulacion_sipeb'
    )

    # PGDESA (Impacto) — nivel nacional de largo plazo
    cod_eje_pgdesa = models.CharField(
        max_length=20, blank=True,
        verbose_name='Código Eje PGDESA',
        help_text='7 ejes del PGDESA'
    )
    objetivo_impacto_pgdesa = models.TextField(
        blank=True,
        verbose_name='Objetivo de impacto PGDESA'
    )

    # PDESA (Efecto) — nivel nacional de mediano plazo
    cod_componente_pdesa = models.CharField(
        max_length=20, blank=True,
        verbose_name='Código Componente PDESA'
    )
    objetivo_efecto_pdesa = models.TextField(
        blank=True,
        verbose_name='Objetivo de efecto PDESA'
    )

    # Acuerdos internacionales
    cod_ods = models.CharField(
        max_length=10, blank=True,
        verbose_name='Código ODS',
        help_text='17 Objetivos de Desarrollo Sostenible'
    )
    cod_meta_ndc = models.CharField(
        max_length=10, blank=True,
        verbose_name='Código Meta NDC',
        help_text='35 metas de la Contribución Nacional Determinada'
    )
    cod_principio_ndt = models.CharField(
        max_length=10, blank=True,
        verbose_name='Código Principio NDT',
        help_text='19 principios del Nuevo Trato Departamental'
    )
    compromisos_3030 = models.TextField(
        blank=True,
        verbose_name='Compromisos 30x30',
        help_text='Iniciativa 30x30 (áreas protegidas)'
    )

    # PDS (Sectorial) — Plan de Desarrollo Sectorial
    cod_sector = models.CharField(
        max_length=10, blank=True,
        verbose_name='Código Sector'
    )
    sector_nombre = models.CharField(
        max_length=200, blank=True,
        verbose_name='Nombre del Sector'
    )
    cod_resultado_pds = models.CharField(
        max_length=20, blank=True,
        verbose_name='Código Resultado PDS'
    )
    resultado_pds = models.TextField(
        blank=True,
        verbose_name='Resultado PDS'
    )

    # PAD (Territorial) — datos que vienen de la Matriz A
    cod_geografico = models.CharField(
        max_length=20, blank=True,
        verbose_name='Código Geográfico'
    )
    denominacion_eta = models.CharField(
        max_length=300, blank=True,
        verbose_name='Denominación ETA',
        help_text='Entidad Territorial Autónoma (GAM Sacaba)'
    )

    gestion = models.PositiveIntegerField(verbose_name='Gestión')

    class Meta:
        verbose_name = 'Articulación SIPEB'
        verbose_name_plural = 'Articulaciones SIPEB'
        ordering = ['gestion', 'resultado']

    def __str__(self):
        return f'Articulación SIPEB - {self.resultado.codigo} ({self.gestion})'
