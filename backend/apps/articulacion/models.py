import uuid
from django.db import models

from .revision_poau import EstadosPOAU
from django.conf import settings
from django.core.exceptions import ValidationError
from apps.core.models import TimeStampedModel
from apps.codificacion.models import CodigoSegmentadoModel


class CodigoNivel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nivel = models.CharField(max_length=100, unique=True, verbose_name='Nivel')
    codigo_nivel = models.CharField(max_length=10, verbose_name='Código nivel')
    segmentos = models.CharField(max_length=100, verbose_name='Segmentos')
    longitud = models.CharField(max_length=50, verbose_name='Longitud')
    codigo_padre = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='hijos', verbose_name='Código padre'
    )
    ejemplo = models.CharField(max_length=300, verbose_name='Ejemplo')
    regla_generacion = models.TextField(verbose_name='Regla de generación')
    editable = models.BooleanField(default=False, verbose_name='Editable')
    vigencia = models.CharField(max_length=50, verbose_name='Vigencia')

    class Meta:
        verbose_name = 'Código de nivel'
        verbose_name_plural = 'Códigos de nivel'
        ordering = ['codigo_nivel']

    def __str__(self):
        return f'[{self.codigo_nivel}] {self.nivel}'


class AcuerdoInternacional(models.Model):
    TIPO_ACUERDO_CHOICES = [
        ('ODS', 'ODS'),
        ('NDC', 'NDC'),
        ('NDT', 'NDT'),
        ('COMPROMISO_3030', 'Compromiso 30/30'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tipo_acuerdo = models.CharField(
        max_length=30, choices=TIPO_ACUERDO_CHOICES,
        verbose_name='Tipo de acuerdo'
    )
    codigo = models.CharField(max_length=10, verbose_name='Código')
    denominacion = models.TextField(verbose_name='Denominación')
    rango_valido = models.CharField(max_length=100, blank=True, verbose_name='Rango válido')
    es_codigo_oficial = models.BooleanField(default=True, verbose_name='Es código oficial')
    activo = models.BooleanField(default=True, verbose_name='Activo')

    class Meta:
        verbose_name = 'Acuerdo internacional'
        verbose_name_plural = 'Acuerdos internacionales'
        ordering = ['tipo_acuerdo', 'codigo']

    def __str__(self):
        return f'[{self.get_tipo_acuerdo_display()}] {self.codigo} - {self.denominacion[:80]}'


class CompatibilidadAcuerdoInternacional(TimeStampedModel):
    """Classified compatibility between two international agreements."""

    class TiposRelacion(models.TextChoices):
        OFICIAL_EXPLICITA = 'OFICIAL_EXPLICITA', 'Oficial explícita'
        DERIVADA_DOCUMENTAL = 'DERIVADA_DOCUMENTAL', 'Derivada documental'
        SUGERENCIA_SEMANTICA = 'SUGERENCIA_SEMANTICA', 'Sugerencia IA'

    class Estados(models.TextChoices):
        VALIDADA = 'VALIDADA', 'Validada'
        CANDIDATA = 'CANDIDATA', 'Candidata'
        RECHAZADA = 'RECHAZADA', 'Rechazada'

    class Confianzas(models.TextChoices):
        ALTA = 'ALTA', 'Alta'
        MEDIA = 'MEDIA', 'Media'
        BAJA = 'BAJA', 'Baja'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    origen = models.ForeignKey(
        AcuerdoInternacional,
        on_delete=models.CASCADE,
        related_name='compatibilidades_origen',
        verbose_name='Acuerdo origen',
    )
    destino = models.ForeignKey(
        AcuerdoInternacional,
        on_delete=models.CASCADE,
        related_name='compatibilidades_destino',
        verbose_name='Acuerdo destino',
    )
    tipo_relacion = models.CharField(
        max_length=30,
        choices=TiposRelacion.choices,
        verbose_name='Tipo de relación',
    )
    estado = models.CharField(
        max_length=20,
        choices=Estados.choices,
        default=Estados.CANDIDATA,
        verbose_name='Estado',
    )
    confianza = models.CharField(
        max_length=10,
        choices=Confianzas.choices,
        default=Confianzas.BAJA,
        verbose_name='Confianza',
    )
    fuente_url = models.URLField(max_length=500, blank=True, default='', verbose_name='URL fuente')
    fuente_titulo = models.CharField(max_length=300, blank=True, default='', verbose_name='Título fuente')
    fuente_version = models.CharField(max_length=150, blank=True, default='', verbose_name='Versión fuente')
    localizador = models.CharField(max_length=200, blank=True, default='', verbose_name='Localizador')
    evidencia = models.TextField(blank=True, default='', verbose_name='Evidencia')
    justificacion = models.TextField(blank=True, default='', verbose_name='Justificación')
    activo = models.BooleanField(default=True, verbose_name='Activo')
    revisado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='compatibilidades_acuerdos_revisadas',
        verbose_name='Usuario revisor',
    )
    revisado_en = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de revisión')

    class Meta:
        verbose_name = 'Compatibilidad de acuerdo internacional'
        verbose_name_plural = 'Compatibilidades de acuerdos internacionales'
        ordering = ['origen__codigo', 'destino__codigo', 'tipo_relacion', 'fuente_url']
        constraints = [
            models.UniqueConstraint(
                fields=['origen', 'destino', 'tipo_relacion', 'fuente_url'],
                name='uniq_compat_acuerdo_origen_destino_tipo_fuente',
            ),
            models.CheckConstraint(
                condition=~models.Q(origen=models.F('destino')),
                name='compat_acuerdo_origen_destino_distintos',
            ),
        ]
        indexes = [
            models.Index(
                fields=['origen', 'destino', 'activo'],
                name='articulacio_origen_1c85f8_idx',
            ),
            models.Index(
                fields=['destino', 'estado', 'tipo_relacion'],
                name='articulacio_destino_1d4388_idx',
            ),
        ]

    def clean(self):
        super().clean()
        errores = {}
        if self.origen_id and self.destino_id and self.origen_id == self.destino_id:
            errores['destino'] = 'El origen y el destino deben ser acuerdos distintos.'
        if (
            self.origen_id
            and self.destino_id
            and self.origen_id != self.destino_id
            and self.origen.tipo_acuerdo == self.destino.tipo_acuerdo
        ):
            errores['destino'] = 'La cascada no permite relaciones entre tipos iguales.'
        if errores:
            raise ValidationError(errores)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class Normativa(TimeStampedModel):
    NIVEL_CHOICES = [
        ('Nacional', 'Nacional'),
        ('Departamental', 'Departamental'),
        ('Municipal', 'Municipal'),
        ('Institucional', 'Institucional'),
        ('Internacional', 'Internacional'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo_norma = models.CharField(max_length=50, unique=True, verbose_name='Código norma')
    nivel = models.CharField(max_length=30, choices=NIVEL_CHOICES, verbose_name='Nivel')
    tipo_norma = models.CharField(max_length=100, verbose_name='Tipo de norma')
    numero_identificador = models.CharField(max_length=100, verbose_name='Número identificador')
    denominacion = models.TextField(verbose_name='Denominación')
    ambito_aplicacion = models.TextField(blank=True, verbose_name='Ámbito de aplicación')
    vigencia = models.CharField(max_length=50, blank=True, verbose_name='Vigencia')
    estado = models.CharField(max_length=50, default='VALIDAR', verbose_name='Estado')
    fuente = models.CharField(max_length=200, blank=True, verbose_name='Fuente')
    observacion = models.TextField(blank=True, verbose_name='Observación')
    fecha_emision = models.DateField(null=True, blank=True, verbose_name='Fecha de emisión')
    archivo_adjunto = models.FileField(
        upload_to='normativa/', null=True, blank=True,
        verbose_name='Archivo adjunto'
    )
    reemplazada_por = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reemplazos', verbose_name='Reemplazada por'
    )

    class Meta:
        verbose_name = 'Normativa'
        verbose_name_plural = 'Normativas'
        ordering = ['codigo_norma']

    def __str__(self):
        return f'[{self.codigo_norma}] {self.denominacion[:80]}'


class LineamientoPAD(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=20, verbose_name='Código')
    denominacion = models.TextField(verbose_name='Denominación')
    codigo_padre = models.CharField(max_length=20, blank=True, verbose_name='Código padre')
    gestion_desde = models.IntegerField(verbose_name='Gestión desde')
    gestion_hasta = models.IntegerField(verbose_name='Gestión hasta')
    activo = models.BooleanField(default=True, verbose_name='Activo')

    class Meta:
        verbose_name = 'Lineamiento PAD'
        verbose_name_plural = 'Lineamientos PAD'
        ordering = ['codigo']

    def __str__(self):
        return f'[{self.codigo}] {self.denominacion[:80]}'


class ResultadoPAD(CodigoSegmentadoModel):
    ANCHO_SEGMENTO = 2  # segmento RT
    CAMPOS_CODIFICACION_ADICIONALES = (
        'vigencia_desde', 'resultado_sectorial_catalogo',
        'entidad_territorial_cgeo', 'lineamiento_pad_catalogo',
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_cadena = models.CharField(max_length=20, unique=True, verbose_name='ID cadena')
    codigo_resultado = models.CharField(max_length=50, verbose_name='Código resultado')
    denominacion = models.TextField(verbose_name='Denominación')
    lineamiento_pad = models.CharField(max_length=20, verbose_name='Lineamiento PAD')
    territorializacion = models.TextField(blank=True, verbose_name='Territorialización')
    responsable_pad = models.CharField(max_length=200, blank=True, verbose_name='Responsable PAD')
    vigencia_desde = models.IntegerField(verbose_name='Vigencia desde')
    vigencia_hasta = models.IntegerField(verbose_name='Vigencia hasta')
    cod_geografico = models.CharField(max_length=20, verbose_name='Código geográfico')
    eta = models.CharField(max_length=300, verbose_name='ETA')
    resultado_sectorial_catalogo = models.ForeignKey(
        'codificacion.ResultadoSectorial', on_delete=models.PROTECT,
        null=True, blank=True, related_name='resultados_pad',
        verbose_name='Resultado sectorial de catálogo',
    )
    entidad_territorial_cgeo = models.ForeignKey(
        'codificacion.EntidadTerritorialCGEO', on_delete=models.PROTECT,
        null=True, blank=True, related_name='resultados_pad',
        verbose_name='Entidad territorial CGEO',
    )
    lineamiento_pad_catalogo = models.ForeignKey(
        'codificacion.LineamientoPAD', on_delete=models.PROTECT,
        null=True, blank=True, related_name='resultados_pad',
        verbose_name='Lineamiento PAD de catálogo',
    )
    acuerdo_ods = models.ManyToManyField(
        AcuerdoInternacional, blank=True,
        limit_choices_to={'tipo_acuerdo': 'ODS'},
        related_name='resultados_pad_ods', verbose_name='Acuerdo ODS'
    )
    acuerdo_ndc = models.ManyToManyField(
        AcuerdoInternacional, blank=True,
        limit_choices_to={'tipo_acuerdo': 'NDC'},
        related_name='resultados_pad_ndc', verbose_name='Acuerdo NDC'
    )
    acuerdo_ndt = models.ManyToManyField(
        AcuerdoInternacional, blank=True,
        limit_choices_to={'tipo_acuerdo': 'NDT'},
        related_name='resultados_pad_ndt', verbose_name='Acuerdo NDT'
    )
    acuerdo_3030 = models.ManyToManyField(
        AcuerdoInternacional, blank=True,
        limit_choices_to={'tipo_acuerdo': 'COMPROMISO_3030'},
        related_name='resultados_pad_3030', verbose_name='Acuerdo 30/30'
    )
    cod_eje_pgdesa = models.CharField(max_length=10, blank=True, verbose_name='Código eje PGDESA')
    objetivo_impacto = models.TextField(blank=True, verbose_name='Objetivo de impacto')
    cod_componente_pdesa = models.CharField(max_length=10, blank=True, verbose_name='Código componente PDESA')
    nodo_pdesa = models.ForeignKey(
        'planificacion.NodoPlanificacion', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='resultados_pad',
        limit_choices_to={'plan__tipo': 'pdesa', 'nivel': 'accion'},
        verbose_name='Nodo PDESA'
    )
    objetivo_efecto = models.TextField(blank=True, verbose_name='Objetivo de efecto')
    cod_sector = models.CharField(max_length=10, blank=True, verbose_name='Código sector')
    sector = models.CharField(max_length=200, blank=True, verbose_name='Sector')
    cod_resultado_pds = models.CharField(max_length=20, blank=True, verbose_name='Código resultado PDS')
    resultado_pds = models.TextField(blank=True, verbose_name='Resultado PDS')
    estado = models.CharField(max_length=20, default='REFERENCIAL', verbose_name='Estado')

    class Meta:
        verbose_name = 'Resultado PAD'
        verbose_name_plural = 'Resultados PAD'
        ordering = ['codigo_resultado']
        unique_together = [('codigo_resultado', 'vigencia_desde')]
        constraints = [
            models.UniqueConstraint(
                fields=['vigencia_desde', 'correlativo'],
                name='uniq_resultado_pad_gestion_correlativo',
            ),
        ]
        indexes = [
            models.Index(fields=['vigencia_desde', 'estado']),
        ]

    def save(self, *args, **kwargs):
        old_estado = None
        if self.pk:
            try:
                old_estado = ResultadoPAD.objects.get(pk=self.pk).estado
            except ResultadoPAD.DoesNotExist:
                pass
        super().save(*args, **kwargs)
        if old_estado is not None and old_estado != self.estado:
            from .services import registrar_auditoria
            try:
                registrar_auditoria(
                    usuario=None, accion='modificar', entidad='ResultadoPAD',
                    entidad_id=self.id,
                    detalle=f'Estado cambió de {old_estado} a {self.estado}'
                )
            except Exception:
                pass

    def __str__(self):
        return f'[{self.codigo_resultado}] {self.denominacion[:80]}'


class ProductoPAD(CodigoSegmentadoModel):
    ANCHO_SEGMENTO = 2  # segmento PT
    CAMPOS_CODIFICACION_ADICIONALES = ('resultado_pad',)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo_producto = models.CharField(max_length=50, verbose_name='Código producto')
    denominacion = models.TextField(verbose_name='Denominación')
    resultado_pad = models.ForeignKey(
        ResultadoPAD, on_delete=models.CASCADE,
        related_name='productos', verbose_name='Resultado PAD'
    )
    territorializacion = models.TextField(blank=True, verbose_name='Territorialización')
    responsable = models.CharField(max_length=200, blank=True, verbose_name='Responsable')

    class Meta:
        verbose_name = 'Producto PAD'
        verbose_name_plural = 'Productos PAD'
        ordering = ['codigo_producto']
        unique_together = [('codigo_producto', 'resultado_pad')]
        constraints = [
            models.UniqueConstraint(
                fields=['resultado_pad', 'correlativo'],
                name='uniq_producto_pad_padre_correlativo',
            ),
        ]

    def __str__(self):
        return f'[{self.codigo_producto}] {self.denominacion[:80]}'


class ResultadoPEI(CodigoSegmentadoModel):
    ANCHO_SEGMENTO = 2  # segmento RI
    CAMPOS_CODIFICACION_ADICIONALES = (
        'cod_entidad', 'cod_oei', 'vigencia_desde', 'entidad_codificadora',
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo_resultado = models.CharField(max_length=50, verbose_name='Código resultado')
    denominacion = models.TextField(verbose_name='Denominación')
    cod_entidad = models.CharField(max_length=10, verbose_name='Código entidad')
    entidad = models.CharField(max_length=300, verbose_name='Entidad')
    entidad_codificadora = models.ForeignKey(
        'codificacion.EntidadCodificadora', on_delete=models.PROTECT,
        null=True, blank=True, related_name='resultados_pei',
        verbose_name='Entidad codificadora',
    )
    cod_oei = models.CharField(max_length=10, blank=True, verbose_name='Código OEI')
    objetivo_estrategico = models.TextField(blank=True, verbose_name='Objetivo estratégico institucional')
    vigencia_desde = models.IntegerField(verbose_name='Vigencia desde')
    vigencia_hasta = models.IntegerField(verbose_name='Vigencia hasta')

    # Matriz de planificación PEI — Sección I: planificación nacional.
    cod_eje_pgdesa = models.CharField(max_length=10, blank=True, verbose_name='Código eje PGDESA')
    objetivo_impacto = models.TextField(blank=True, verbose_name='Objetivo de impacto')
    cod_componente_pdesa = models.CharField(
        max_length=10, blank=True, verbose_name='Código componente PDESA'
    )
    objetivo_efecto = models.TextField(blank=True, verbose_name='Objetivo de efecto')

    # Sección II: acuerdos internacionales (opcionales según la guía).
    cod_ods = models.CharField(max_length=10, blank=True, verbose_name='Código ODS')
    cod_ndc = models.CharField(max_length=20, blank=True, verbose_name='Código NDC')
    cod_ndt = models.CharField(max_length=20, blank=True, verbose_name='Código NDT')
    cod_meta_3030 = models.CharField(max_length=20, blank=True, verbose_name='Código meta 30x30')

    # Sección III: identificación del sector.
    cod_sector = models.CharField(max_length=10, blank=True, verbose_name='Código sector')
    sector = models.CharField(max_length=200, blank=True, verbose_name='Sector')

    # Sección IV: articulación sectorial.
    cod_resultado_sectorial = models.CharField(
        max_length=20, blank=True, verbose_name='Código resultado sectorial PES'
    )
    resultado_sectorial = models.TextField(blank=True, verbose_name='Resultado sectorial')

    # Articulación territorial: resultado del PAD al que contribuye el resultado PEI.
    cod_resultado_territorial = models.CharField(
        max_length=20, blank=True, verbose_name='Código resultado territorial'
    )
    resultado_pad = models.ForeignKey(
        'ResultadoPAD', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='resultados_pei', verbose_name='Resultado PAD',
    )

    class Meta:
        verbose_name = 'Resultado PEI'
        verbose_name_plural = 'Resultados PEI'
        ordering = ['codigo_resultado']
        unique_together = [('codigo_resultado', 'vigencia_desde')]
        constraints = [
            models.UniqueConstraint(
                fields=['vigencia_desde', 'correlativo'],
                name='uniq_resultado_pei_gestion_correlativo',
            ),
        ]
        indexes = [
            models.Index(fields=['vigencia_desde']),
        ]

    def __str__(self):
        return f'[{self.codigo_resultado}] {self.denominacion[:80]}'


class ProductoPEI(CodigoSegmentadoModel):
    ANCHO_SEGMENTO = 2  # segmento PI
    CAMPOS_CODIFICACION_ADICIONALES = ('resultado_pei',)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    TIPO_PRODUCTO_CHOICES = [
        ('INTERMEDIO', 'Intermedio'),
        ('FINAL', 'Final'),
        ('TERMINAL', 'Terminal'),
    ]

    codigo_producto = models.CharField(max_length=50, verbose_name='Código producto')
    denominacion = models.TextField(verbose_name='Denominación')
    resultado_pei = models.ForeignKey(
        ResultadoPEI, on_delete=models.CASCADE,
        related_name='productos', verbose_name='Resultado PEI'
    )
    tipo_producto = models.CharField(
        max_length=20, blank=True, choices=TIPO_PRODUCTO_CHOICES,
        verbose_name='Tipo de producto',
    )
    cod_programa_presup = models.CharField(
        max_length=20, blank=True, verbose_name='Código programa presupuestario'
    )
    programa_presup = models.CharField(
        max_length=300, blank=True, verbose_name='Programa presupuestario'
    )

    class Meta:
        verbose_name = 'Producto PEI'
        verbose_name_plural = 'Productos PEI'
        ordering = ['codigo_producto']
        unique_together = [('codigo_producto', 'resultado_pei')]
        constraints = [
            models.UniqueConstraint(
                fields=['resultado_pei', 'correlativo'],
                name='uniq_producto_pei_padre_correlativo',
            ),
        ]

    def __str__(self):
        return f'[{self.codigo_producto}] {self.denominacion[:80]}'


class ArticulacionPADPEI(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    producto_pad = models.ForeignKey(
        ProductoPAD, on_delete=models.CASCADE,
        related_name='articulaciones_pei', verbose_name='Producto PAD'
    )
    producto_pei = models.ForeignKey(
        ProductoPEI, on_delete=models.CASCADE,
        related_name='articulaciones_pad', verbose_name='Producto PEI'
    )
    tipo_contribucion = models.CharField(
        max_length=50, blank=True, verbose_name='Tipo de contribución'
    )
    ponderacion = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name='Ponderación'
    )
    justificacion = models.TextField(blank=True, verbose_name='Justificación')
    estado = models.CharField(max_length=20, default='REFERENCIAL', verbose_name='Estado')

    class Meta:
        verbose_name = 'Articulación PAD-PEI'
        verbose_name_plural = 'Articulaciones PAD-PEI'
        unique_together = [('producto_pad', 'producto_pei')]

    def save(self, *args, **kwargs):
        old_estado = None
        if self.pk:
            try:
                old_estado = ArticulacionPADPEI.objects.get(pk=self.pk).estado
            except ArticulacionPADPEI.DoesNotExist:
                pass
        super().save(*args, **kwargs)
        if old_estado is not None and old_estado != self.estado:
            from .services import registrar_auditoria
            try:
                registrar_auditoria(
                    usuario=None, accion='modificar', entidad='ArticulacionPADPEI',
                    entidad_id=self.id,
                    detalle=f'Estado cambió de {old_estado} a {self.estado}'
                )
            except Exception:
                pass

    def __str__(self):
        return f'{self.producto_pad.codigo_producto} ↔ {self.producto_pei.codigo_producto}'


class IndicadorCadena(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nivel_indicador = models.CharField(max_length=50, verbose_name='Nivel del indicador')
    indicador = models.TextField(verbose_name='Indicador')
    tipo_indicador = models.CharField(max_length=50, blank=True, verbose_name='Tipo de indicador')
    unidad_medida = models.CharField(max_length=100, verbose_name='Unidad de medida')
    formula = models.TextField(blank=True, verbose_name='Fórmula')
    linea_base = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True,
        verbose_name='Línea base'
    )
    meta_2030 = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True,
        verbose_name='Meta 2030'
    )
    producto_pad = models.ForeignKey(
        ProductoPAD, on_delete=models.CASCADE, null=True, blank=True,
        related_name='indicadores', verbose_name='Producto PAD'
    )
    producto_pei = models.ForeignKey(
        ProductoPEI, on_delete=models.CASCADE, null=True, blank=True,
        related_name='indicadores', verbose_name='Producto PEI'
    )
    resultado_pei = models.ForeignKey(
        ResultadoPEI, on_delete=models.CASCADE, null=True, blank=True,
        related_name='indicadores', verbose_name='Resultado PEI'
    )
    programacion_fisica = models.JSONField(null=True, blank=True, verbose_name='Programación física')
    presupuesto_inversion_total = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True,
        verbose_name='Presupuesto inversión total'
    )
    inversion_2026 = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    inversion_2027 = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    inversion_2028 = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    inversion_2029 = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    inversion_2030 = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    presupuesto_corriente_total = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True,
        verbose_name='Presupuesto corriente total'
    )
    corriente_2026 = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    corriente_2027 = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    corriente_2028 = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    corriente_2029 = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    corriente_2030 = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    fuente_dato = models.TextField(blank=True, verbose_name='Fuente de dato')

    class Meta:
        verbose_name = 'Indicador de cadena'
        verbose_name_plural = 'Indicadores de cadena'
        ordering = ['nivel_indicador', 'indicador']

    def __str__(self):
        return f'[{self.nivel_indicador}] {self.indicador[:80]}'


class AccionPOA(CodigoSegmentadoModel):
    ANCHO_SEGMENTO = 3  # segmento ACP
    CAMPOS_CODIFICACION_ADICIONALES = ('producto_pei', 'gestion')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo_accion = models.CharField(max_length=50, unique=True, verbose_name='Código acción')
    denominacion = models.TextField(verbose_name='Denominación')
    resultado_esperado = models.TextField(blank=True, verbose_name='Resultado esperado')
    producto_pei = models.ForeignKey(
        ProductoPEI, on_delete=models.CASCADE,
        related_name='acciones_poa', verbose_name='Producto PEI'
    )
    indicador = models.TextField(blank=True, verbose_name='Indicador')
    formula = models.TextField(blank=True, verbose_name='Fórmula')
    unidad_medida = models.CharField(max_length=100, blank=True, verbose_name='Unidad de medida')
    linea_base = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True,
        verbose_name='Línea base'
    )
    meta_gestion = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True,
        verbose_name='Meta de gestión'
    )
    codigo_rea = models.CharField(max_length=20, blank=True, verbose_name='Código REA')
    cargo_responsable = models.CharField(max_length=200, blank=True, verbose_name='Cargo responsable')
    fecha_inicio = models.DateField(null=True, blank=True, verbose_name='Fecha inicio')
    fecha_fin = models.DateField(null=True, blank=True, verbose_name='Fecha fin')
    tipo_operacion = models.CharField(max_length=50, blank=True, verbose_name='Tipo de operación')
    categoria_programatica = models.CharField(
        max_length=50, blank=True, verbose_name='Categoría programática'
    )
    programa = models.CharField(max_length=200, blank=True, verbose_name='Programa')
    proyecto_sisin = models.CharField(max_length=100, blank=True, verbose_name='Proyecto SISIN')
    actividad_presupuestaria = models.CharField(
        max_length=100, blank=True, verbose_name='Actividad presupuestaria'
    )
    presupuesto_programado = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True,
        verbose_name='Presupuesto programado'
    )
    fuente_financiamiento = models.CharField(
        max_length=20, blank=True, verbose_name='Fuente de financiamiento'
    )
    organismo_financiador = models.CharField(
        max_length=20, blank=True, verbose_name='Organismo financiador'
    )
    medio_verificacion = models.TextField(blank=True, verbose_name='Medio de verificación')
    riesgo = models.TextField(blank=True, verbose_name='Riesgo')
    estado = models.CharField(max_length=20, default='REFERENCIAL', verbose_name='Estado')
    gestion = models.IntegerField(verbose_name='Gestión')
    unidad_responsable = models.ForeignKey(
        'organizacion.UnidadOrganizacional', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='acciones_poa',
        verbose_name='Unidad responsable'
    )

    class Meta:
        verbose_name = 'Acción POA'
        verbose_name_plural = 'Acciones POA'
        ordering = ['codigo_accion']
        constraints = [
            models.UniqueConstraint(
                fields=['producto_pei', 'gestion', 'correlativo'],
                name='uniq_accion_poa_padre_gestion_correlativo',
            ),
        ]
        indexes = [
            models.Index(fields=['gestion', 'estado']),
        ]

    def save(self, *args, **kwargs):
        old_estado = None
        if self.pk:
            try:
                old_estado = AccionPOA.objects.get(pk=self.pk).estado
            except AccionPOA.DoesNotExist:
                pass
        super().save(*args, **kwargs)
        if old_estado is not None and old_estado != self.estado:
            from .services import registrar_auditoria
            try:
                registrar_auditoria(
                    usuario=None, accion='modificar', entidad='AccionPOA',
                    entidad_id=self.id,
                    detalle=f'Estado cambió de {old_estado} a {self.estado}'
                )
            except Exception:
                pass

    def __str__(self):
        return f'[{self.codigo_accion}] {self.denominacion[:80]}'


class OperacionPOAU(CodigoSegmentadoModel):
    ANCHO_SEGMENTO = 3  # segmento OP
    CAMPOS_CODIFICACION_ADICIONALES = ('accion_poa',)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo_operacion = models.CharField(max_length=50, unique=True, verbose_name='Código operación')
    denominacion = models.TextField(verbose_name='Denominación')
    tipo_operacion = models.CharField(max_length=50, verbose_name='Tipo de operación')
    producto_entregable = models.TextField(blank=True, verbose_name='Producto/Entregable')
    accion_poa = models.ForeignKey(
        AccionPOA, on_delete=models.CASCADE,
        related_name='operaciones', verbose_name='Acción POA'
    )
    unidad_ejecutora = models.CharField(max_length=200, blank=True, verbose_name='Unidad ejecutora')
    codigo_unidad_ejecutora = models.CharField(
        max_length=20, blank=True, verbose_name='Código unidad ejecutora'
    )
    responsable = models.CharField(max_length=200, blank=True, verbose_name='Responsable')
    codigo_responsable = models.CharField(
        max_length=20, blank=True, verbose_name='Código responsable'
    )
    meta_anual = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True,
        verbose_name='Meta anual'
    )
    indicador = models.TextField(blank=True, verbose_name='Indicador')
    formula = models.TextField(blank=True, verbose_name='Fórmula')
    unidad_medida = models.CharField(max_length=100, blank=True, verbose_name='Unidad de medida')
    fecha_inicio = models.DateField(null=True, blank=True, verbose_name='Fecha inicio')
    fecha_fin = models.DateField(null=True, blank=True, verbose_name='Fecha fin')
    programacion_mensual = models.JSONField(null=True, blank=True, verbose_name='Programación mensual')
    total_programado = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True,
        verbose_name='Total programado'
    )
    medio_verificacion = models.TextField(blank=True, verbose_name='Medio de verificación')
    requerimientos = models.TextField(blank=True, verbose_name='Requerimientos')
    riesgo = models.TextField(blank=True, verbose_name='Riesgo')
    accion_correctiva = models.TextField(blank=True, verbose_name='Acción correctiva')
    estado = models.CharField(
        max_length=20, choices=EstadosPOAU.choices,
        default=EstadosPOAU.BORRADOR, verbose_name='Estado'
    )
    observacion = models.TextField(blank=True, verbose_name='Observación')

    class Meta:
        verbose_name = 'Operación POAU'
        verbose_name_plural = 'Operaciones POAU'
        ordering = ['codigo_operacion']
        constraints = [
            models.UniqueConstraint(
                fields=['accion_poa', 'correlativo'],
                name='uniq_operacion_poau_padre_correlativo',
            ),
        ]

    def save(self, *args, **kwargs):
        old_estado = None
        if self.pk:
            try:
                old_estado = OperacionPOAU.objects.get(pk=self.pk).estado
            except OperacionPOAU.DoesNotExist:
                pass
        super().save(*args, **kwargs)
        if old_estado is not None and old_estado != self.estado:
            from .services import registrar_auditoria
            try:
                registrar_auditoria(
                    usuario=None, accion='modificar', entidad='OperacionPOAU',
                    entidad_id=self.id,
                    detalle=f'Estado cambió de {old_estado} a {self.estado}'
                )
            except Exception:
                pass

    def __str__(self):
        return f'[{self.codigo_operacion}] {self.denominacion[:80]}'


class ActividadPOAU(CodigoSegmentadoModel):
    ANCHO_SEGMENTO = 3  # segmento ACT
    CAMPOS_CODIFICACION_ADICIONALES = ('operacion',)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo_actividad = models.CharField(max_length=50, unique=True, verbose_name='Código actividad')
    denominacion = models.TextField(verbose_name='Denominación')
    operacion = models.ForeignKey(
        OperacionPOAU, on_delete=models.CASCADE,
        related_name='actividades', verbose_name='Operación'
    )
    producto_entregable = models.TextField(blank=True, verbose_name='Producto/Entregable')
    meta_anual = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True,
        verbose_name='Meta anual'
    )
    indicador = models.TextField(blank=True, verbose_name='Indicador')
    formula = models.TextField(blank=True, verbose_name='Fórmula')
    unidad_medida = models.CharField(max_length=100, blank=True, verbose_name='Unidad de medida')
    fecha_inicio = models.DateField(null=True, blank=True, verbose_name='Fecha inicio')
    fecha_fin = models.DateField(null=True, blank=True, verbose_name='Fecha fin')
    programacion_mensual = models.JSONField(null=True, blank=True, verbose_name='Programación mensual')
    total_programado = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True,
        verbose_name='Total programado'
    )
    normativas = models.ManyToManyField(
        Normativa, through='ActividadNormativa', blank=True,
        verbose_name='Normativas'
    )
    medio_verificacion = models.TextField(blank=True, verbose_name='Medio de verificación')
    requerimientos = models.TextField(blank=True, verbose_name='Requerimientos')
    riesgo = models.TextField(blank=True, verbose_name='Riesgo')
    accion_correctiva = models.TextField(blank=True, verbose_name='Acción correctiva')
    estado = models.CharField(
        max_length=20, choices=EstadosPOAU.choices,
        default=EstadosPOAU.BORRADOR, verbose_name='Estado'
    )
    observacion = models.TextField(blank=True, verbose_name='Observación')

    class Meta:
        verbose_name = 'Actividad POAU'
        verbose_name_plural = 'Actividades POAU'
        ordering = ['codigo_actividad']
        constraints = [
            models.UniqueConstraint(
                fields=['operacion', 'correlativo'],
                name='uniq_actividad_poau_padre_correlativo',
            ),
        ]

    def save(self, *args, **kwargs):
        old_estado = None
        if self.pk:
            try:
                old_estado = ActividadPOAU.objects.get(pk=self.pk).estado
            except ActividadPOAU.DoesNotExist:
                pass
        super().save(*args, **kwargs)
        if old_estado is not None and old_estado != self.estado:
            from .services import registrar_auditoria
            try:
                registrar_auditoria(
                    usuario=None, accion='modificar', entidad='ActividadPOAU',
                    entidad_id=self.id,
                    detalle=f'Estado cambió de {old_estado} a {self.estado}'
                )
            except Exception:
                pass

    def __str__(self):
        return f'[{self.codigo_actividad}] {self.denominacion[:80]}'


class ActividadNormativa(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actividad = models.ForeignKey(
        ActividadPOAU, on_delete=models.CASCADE,
        related_name='normativas_through', verbose_name='Actividad'
    )
    normativa = models.ForeignKey(
        Normativa, on_delete=models.CASCADE,
        related_name='actividades_through', verbose_name='Normativa'
    )
    tipo_aplicacion = models.CharField(
        max_length=100, blank=True, verbose_name='Tipo de aplicación'
    )
    observacion = models.TextField(blank=True, verbose_name='Observación')
    obligatorio = models.BooleanField(default=False, verbose_name='Obligatorio')

    class Meta:
        verbose_name = 'Actividad - Normativa'
        verbose_name_plural = 'Actividades - Normativas'
        unique_together = [('actividad', 'normativa')]

    def __str__(self):
        return f'{self.actividad.codigo_actividad} - {self.normativa.codigo_norma}'


class TareaPOAU(CodigoSegmentadoModel):
    ANCHO_SEGMENTO = 3  # segmento TAR
    CAMPOS_CODIFICACION_ADICIONALES = ('actividad',)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo_tarea = models.CharField(max_length=50, unique=True, verbose_name='Código tarea')
    denominacion = models.TextField(verbose_name='Denominación')
    actividad = models.ForeignKey(
        ActividadPOAU, on_delete=models.CASCADE,
        related_name='tareas', verbose_name='Actividad'
    )
    responsable = models.CharField(max_length=200, blank=True, verbose_name='Responsable')
    fecha_inicio = models.DateField(null=True, blank=True, verbose_name='Fecha inicio')
    fecha_fin = models.DateField(null=True, blank=True, verbose_name='Fecha fin')
    metas = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True,
        verbose_name='Metas'
    )
    programacion_mensual = models.JSONField(null=True, blank=True, verbose_name='Programación mensual')
    requerimientos = models.TextField(blank=True, verbose_name='Requerimientos')
    normativas = models.ManyToManyField(
        Normativa, through='TareaNormativa', blank=True,
        verbose_name='Normativas'
    )
    evidencia = models.TextField(blank=True, verbose_name='Evidencia')
    estado = models.CharField(
        max_length=20, choices=EstadosPOAU.choices,
        default=EstadosPOAU.BORRADOR, verbose_name='Estado'
    )
    observacion = models.TextField(blank=True, verbose_name='Observación')

    class Meta:
        verbose_name = 'Tarea POAU'
        verbose_name_plural = 'Tareas POAU'
        ordering = ['codigo_tarea']
        constraints = [
            models.UniqueConstraint(
                fields=['actividad', 'correlativo'],
                name='uniq_tarea_poau_padre_correlativo',
            ),
        ]

    def save(self, *args, **kwargs):
        old_estado = None
        if self.pk:
            try:
                old_estado = TareaPOAU.objects.get(pk=self.pk).estado
            except TareaPOAU.DoesNotExist:
                pass
        super().save(*args, **kwargs)
        if old_estado is not None and old_estado != self.estado:
            from .services import registrar_auditoria
            try:
                registrar_auditoria(
                    usuario=None, accion='modificar', entidad='TareaPOAU',
                    entidad_id=self.id,
                    detalle=f'Estado cambió de {old_estado} a {self.estado}'
                )
            except Exception:
                pass

    def __str__(self):
        return f'[{self.codigo_tarea}] {self.denominacion[:80]}'


class TareaNormativa(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tarea = models.ForeignKey(
        TareaPOAU, on_delete=models.CASCADE,
        related_name='normativas_through', verbose_name='Tarea'
    )
    normativa = models.ForeignKey(
        Normativa, on_delete=models.CASCADE,
        related_name='tareas_through', verbose_name='Normativa'
    )
    tipo_aplicacion = models.CharField(
        max_length=100, blank=True, verbose_name='Tipo de aplicación'
    )
    observacion = models.TextField(blank=True, verbose_name='Observación')
    obligatorio = models.BooleanField(default=False, verbose_name='Obligatorio')

    class Meta:
        verbose_name = 'Tarea - Normativa'
        verbose_name_plural = 'Tareas - Normativas'
        unique_together = [('tarea', 'normativa')]

    def __str__(self):
        return f'{self.tarea.codigo_tarea} - {self.normativa.codigo_norma}'


class SeguimientoPresupuesto(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_cadena = models.CharField(max_length=50, verbose_name='ID cadena')
    gestion = models.IntegerField(verbose_name='Gestión')
    accion_poa = models.ForeignKey(
        AccionPOA, on_delete=models.CASCADE,
        related_name='seguimientos', verbose_name='Acción POA'
    )
    operacion = models.ForeignKey(
        OperacionPOAU, on_delete=models.CASCADE,
        related_name='seguimientos', verbose_name='Operación'
    )
    actividad = models.ForeignKey(
        ActividadPOAU, on_delete=models.CASCADE,
        related_name='seguimientos', verbose_name='Actividad'
    )
    tarea = models.ForeignKey(
        TareaPOAU, on_delete=models.CASCADE, null=True, blank=True,
        related_name='seguimientos', verbose_name='Tarea'
    )
    categoria_programatica = models.CharField(
        max_length=50, verbose_name='Categoría programática'
    )
    da = models.CharField(max_length=20, verbose_name='DA')
    ue = models.CharField(max_length=20, verbose_name='UE')
    programa = models.CharField(max_length=100, verbose_name='Programa')
    proyecto_sisin = models.CharField(max_length=100, blank=True, verbose_name='Proyecto SISIN')
    actividad_presup = models.CharField(
        max_length=100, blank=True, verbose_name='Actividad presupuestaria'
    )
    tipo_gasto = models.CharField(max_length=50, verbose_name='Tipo de gasto')
    presupuesto_inicial = models.DecimalField(
        max_digits=20, decimal_places=2, verbose_name='Presupuesto inicial'
    )
    modificaciones = models.DecimalField(
        max_digits=20, decimal_places=2, default=0, verbose_name='Modificaciones'
    )
    presupuesto_vigente = models.DecimalField(
        max_digits=20, decimal_places=2, verbose_name='Presupuesto vigente'
    )
    ejecucion_mensual = models.JSONField(null=True, blank=True, verbose_name='Ejecución mensual')
    ejecutado_total = models.DecimalField(
        max_digits=20, decimal_places=2, default=0, verbose_name='Ejecutado total'
    )
    porcentaje_ejecucion_financiera = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True,
        verbose_name='% Ejecución financiera'
    )
    meta_fisica = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True,
        verbose_name='Meta física'
    )
    ejecucion_fisica = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True,
        verbose_name='Ejecución física'
    )
    porcentaje_ejecucion_fisica = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True,
        verbose_name='% Ejecución física'
    )
    eficacia = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True,
        verbose_name='Eficacia'
    )
    eficiencia = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True,
        verbose_name='Eficiencia'
    )
    desviacion = models.TextField(blank=True, verbose_name='Desviación')
    accion_correctiva = models.TextField(blank=True, verbose_name='Acción correctiva')
    evidencia = models.TextField(blank=True, verbose_name='Evidencia')
    fecha_actualizacion = models.DateField(null=True, blank=True, verbose_name='Fecha de actualización')
    estado = models.CharField(max_length=20, default='REFERENCIAL', verbose_name='Estado')

    class Meta:
        verbose_name = 'Seguimiento presupuestario'
        verbose_name_plural = 'Seguimientos presupuestarios'
        ordering = ['gestion', 'id_cadena']
        indexes = [
            models.Index(fields=['gestion', 'estado']),
        ]

    def save(self, *args, **kwargs):
        old_estado = None
        if self.pk:
            try:
                old_estado = SeguimientoPresupuesto.objects.get(pk=self.pk).estado
            except SeguimientoPresupuesto.DoesNotExist:
                pass
        super().save(*args, **kwargs)
        if old_estado is not None and old_estado != self.estado:
            from .services import registrar_auditoria
            try:
                registrar_auditoria(
                    usuario=None, accion='modificar', entidad='SeguimientoPresupuesto',
                    entidad_id=self.id,
                    detalle=f'Estado cambió de {old_estado} a {self.estado}'
                )
            except Exception:
                pass

    def __str__(self):
        return f'SP {self.id_cadena} - G{self.gestion}'


class AsignacionObjetoGasto(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo_asignacion = models.CharField(max_length=20, verbose_name='Código asignación')
    gestion = models.IntegerField(verbose_name='Gestión')
    accion_poa = models.ForeignKey(
        AccionPOA, on_delete=models.CASCADE,
        related_name='asignaciones_og', verbose_name='Acción POA'
    )
    operacion = models.ForeignKey(
        OperacionPOAU, on_delete=models.CASCADE,
        related_name='asignaciones_og', verbose_name='Operación'
    )
    actividad = models.ForeignKey(
        ActividadPOAU, on_delete=models.CASCADE,
        related_name='asignaciones_og', verbose_name='Actividad'
    )
    tarea = models.ForeignKey(
        TareaPOAU, on_delete=models.CASCADE, null=True, blank=True,
        related_name='asignaciones_og', verbose_name='Tarea'
    )
    categoria_programatica = models.CharField(
        max_length=50, verbose_name='Categoría programática'
    )
    da = models.CharField(max_length=20, verbose_name='DA')
    ue = models.CharField(max_length=20, verbose_name='UE')
    programa = models.CharField(max_length=100, verbose_name='Programa')
    proyecto_sisin = models.CharField(max_length=100, blank=True, verbose_name='Proyecto SISIN')
    actividad_presup = models.CharField(
        max_length=100, blank=True, verbose_name='Actividad presupuestaria'
    )
    cod_objeto_gasto = models.CharField(max_length=20, verbose_name='Código objeto de gasto')
    descripcion_objeto = models.TextField(verbose_name='Descripción del objeto')
    grupo_gasto = models.CharField(max_length=20, verbose_name='Grupo de gasto')
    tipo_gasto = models.CharField(max_length=50, verbose_name='Tipo de gasto')
    fuente_financiamiento = models.CharField(
        max_length=20, verbose_name='Fuente de financiamiento'
    )
    organismo_financiador = models.CharField(
        max_length=20, verbose_name='Organismo financiador'
    )
    monto_programado = models.DecimalField(
        max_digits=20, decimal_places=2, verbose_name='Monto programado'
    )
    monto_modificado = models.DecimalField(
        max_digits=20, decimal_places=2, default=0, verbose_name='Monto modificado'
    )
    monto_vigente = models.DecimalField(
        max_digits=20, decimal_places=2, verbose_name='Monto vigente'
    )
    justificacion = models.TextField(blank=True, verbose_name='Justificación')
    memoria_calculo = models.TextField(blank=True, verbose_name='Memoria de cálculo')

    # Programación presupuestaria POAU (RE-SPO Cuadro 4: requerimientos).
    cargo_reacp = models.CharField(
        max_length=200, blank=True, verbose_name='Cargo del REACP',
    )
    fecha_requerimiento = models.CharField(
        max_length=30, blank=True,
        verbose_name='Fecha en la que se requiere el pago (mes estimado)',
    )
    programacion_mensual = models.JSONField(
        null=True, blank=True, verbose_name='Programación presupuestaria mensual',
    )
    medio_verificacion = models.TextField(
        blank=True, verbose_name='Medio de verificación',
    )
    estado = models.CharField(max_length=20, default='REFERENCIAL', verbose_name='Estado')

    class Meta:
        verbose_name = 'Asignación de objeto de gasto'
        verbose_name_plural = 'Asignaciones de objetos de gasto'
        ordering = ['gestion', 'codigo_asignacion']
        unique_together = [('codigo_asignacion', 'gestion')]
        indexes = [
            models.Index(fields=['gestion', 'estado']),
        ]

    def save(self, *args, **kwargs):
        old_estado = None
        if self.pk:
            try:
                old_estado = AsignacionObjetoGasto.objects.get(pk=self.pk).estado
            except AsignacionObjetoGasto.DoesNotExist:
                pass
        super().save(*args, **kwargs)
        if old_estado is not None and old_estado != self.estado:
            from .services import registrar_auditoria
            try:
                registrar_auditoria(
                    usuario=None, accion='modificar', entidad='AsignacionObjetoGasto',
                    entidad_id=self.id,
                    detalle=f'Estado cambió de {old_estado} a {self.estado}'
                )
            except Exception:
                pass

    def __str__(self):
        return f'[{self.codigo_asignacion}] G{self.gestion} - {self.descripcion_objeto[:60]}'


class BorradorMatrizPAD(TimeStampedModel):
    """Borrador del wizard de Matrices PAD (11 pasos, sin articulación PEI).

    Cada paso del wizard persiste su sección en ``datos`` mediante PATCH
    parcial (``seccion`` + ``valores``): los visualizadores Matriz A/B leen
    en vivo desde el borrador hasta que la action ``materializar`` crea los
    registros operativos (ResultadoPAD → ProductoPAD → IndicadorCadena) en
    una transacción atómica y deja el borrador en estado COMPLETO.
    """

    ESTADO_BORRADOR = 'BORRADOR'
    ESTADO_COMPLETO = 'COMPLETO'
    ESTADO_CHOICES = [
        (ESTADO_BORRADOR, 'Borrador'),
        (ESTADO_COMPLETO, 'Completo'),
    ]

    # Secciones del wizard por paso (claves del JSONField ``datos``)
    #
    # Estructura REAL de las matrices PAD: un borrador contiene VARIOS
    # resultados territoriales, cada uno con VARIOS productos, todos
    # conviviendo como filas de la misma Matriz A / Matriz B. La sección
    # ``resultados`` es una colección::
    #
    #   resultados: [
    #     {denominacion, territorializacion, responsable,
    #      cuenta_con_financiamiento,
    #      indicador: {indicador, formula, unidad_medida, linea_base,
    #                  meta_2030, programacion_fisica},
    #      presupuesto_total, presupuesto_anual,
    #      productos: [ {mismos campos que el resultado}, ... ]},
    #     ...
    #   ]
    #
    # Las secciones p1_nacional..p5_lineamiento son la cabecera de cadena
    # (nacional/acuerdos/sectorial/territorial/lineamiento) que la Matriz B
    # repite por fila. Las secciones p6..p10 se conservan SOLO para
    # retrocompatibilidad con borradores creados antes de la colección: la
    # lectura (materializar / matrices A-B) las transforma al formato nuevo.
    SECCIONES = (
        'p1_nacional',
        'p2_acuerdos',
        'p3_sectorial',
        'p4_territorial',
        'p5_lineamiento',
        'resultados',
        # Legacy (aceptado en PATCH, ignorado en lectura si existe resultados)
        'p6_resultado',
        'p7_producto',
        'p8_indicador_resultado',
        'p9_indicador_producto',
        'p10_financiera',
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    gestion = models.IntegerField(default=2026, verbose_name='Gestión')
    estado = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default=ESTADO_BORRADOR,
        verbose_name='Estado',
    )
    datos = models.JSONField(
        default=dict, verbose_name='Datos del wizard',
        help_text=(
            'Secciones de cabecera p1_nacional..p5_lineamiento + colección '
            'resultados[] (cada resultado con sus productos).'
        ),
    )
    id_resultado_pad = models.ForeignKey(
        ResultadoPAD, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='borradores_matriz_pad',
        verbose_name='Resultado PAD materializado',
        help_text='Se llena al materializar el borrador.',
    )

    # ------------------------------------------------------------------
    # Circuito de revisión
    #
    # El técnico que crea el registro lo VALIDA cuando verificó su contenido;
    # el jefe o administrador lo APRUEBA o lo OBSERVA. Un registro APROBADO
    # queda inmutable: no admite edición ni borrado.
    # ------------------------------------------------------------------
    REVISION_PENDIENTE = 'PENDIENTE'
    REVISION_VALIDADO = 'VALIDADO'
    REVISION_OBSERVADO = 'OBSERVADO'
    REVISION_APROBADO = 'APROBADO'
    REVISION_CHOICES = [
        (REVISION_PENDIENTE, 'Pendiente de validación'),
        (REVISION_VALIDADO, 'Validado por el técnico'),
        (REVISION_OBSERVADO, 'Observado'),
        (REVISION_APROBADO, 'Aprobado'),
    ]

    estado_revision = models.CharField(
        max_length=20, choices=REVISION_CHOICES, default=REVISION_PENDIENTE,
        verbose_name='Estado de revisión',
    )
    validado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='matrices_pad_validadas', verbose_name='Validado por',
    )
    validado_en = models.DateTimeField(null=True, blank=True, verbose_name='Validado en')
    aprobado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='matrices_pad_aprobadas', verbose_name='Aprobado por',
    )
    aprobado_en = models.DateTimeField(null=True, blank=True, verbose_name='Aprobado en')
    observacion = models.TextField(blank=True, verbose_name='Observación')
    observado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='matrices_pad_observadas', verbose_name='Observado por',
    )
    observado_en = models.DateTimeField(null=True, blank=True, verbose_name='Observado en')

    @property
    def esta_aprobado(self):
        return self.estado_revision == self.REVISION_APROBADO

    class Meta:
        verbose_name = 'Borrador de Matriz PAD'
        verbose_name_plural = 'Borradores de Matrices PAD'
        ordering = ['-created_at']

    def __str__(self):
        return (
            f'Borrador PAD G{self.gestion} '
            f'{self.get_estado_display()} '
            f'({self.created_at:%Y-%m-%d %H:%M})'
        )


class BorradorMatrizPEI(TimeStampedModel):
    """Borrador del asistente de Matriz PEI (guardado por secciones).

    Espejo de :class:`BorradorMatrizPAD`. Cada sección del asistente persiste
    en ``datos`` mediante PATCH parcial (``seccion`` + ``valores``); la action
    ``materializar`` crea los registros operativos (ResultadoPEI → ProductoPEI
    → IndicadorCadena) en una transacción y deja el borrador en COMPLETO.

    Estructura de ``datos``::

        s1_nacional:      {eje: {codigo}, componente: {codigo},
                           objetivo_impacto, objetivo_efecto}
        s2_acuerdos:      {ods, ndc, ndt, kmgbf}          # código o 'N/A'
        s3_sector:        {sector: {codigo, denominacion},
                           resultado_sectorial: {codigo, denominacion}}
        s4_territorial:   {cod_resultado_territorial, resultado_pad}
        s5_institucional: {cod_entidad, entidad, cod_oei, objetivo_estrategico,
                           vigencia_desde, vigencia_hasta}
        resultados: [
          {correlativo, accion_cambio, variable_resultado, denominacion,
           indicador: {indicador, tipo_indicador, unidad_medida, formula,
                       linea_base, meta_2030},
           programacion_fisica: {'2026': ...},
           productos: [
             {denominacion, bien_servicio, condicion_estado, tipo_producto,
              cod_programa_presup, programa_presup,
              indicador: {...}, programacion_fisica: {...},
              inversion: {...}, corriente: {...}}
           ]}
        ]
    """

    ESTADO_BORRADOR = 'BORRADOR'
    ESTADO_COMPLETO = 'COMPLETO'
    ESTADO_CHOICES = [
        (ESTADO_BORRADOR, 'Borrador'),
        (ESTADO_COMPLETO, 'Completo'),
    ]

    SECCIONES = (
        's1_nacional',
        's2_acuerdos',
        's3_sector',
        's4_territorial',
        's5_institucional',
        'resultados',
    )

    # Circuito de revisión: idéntico al del PAD.
    REVISION_PENDIENTE = 'PENDIENTE'
    REVISION_VALIDADO = 'VALIDADO'
    REVISION_OBSERVADO = 'OBSERVADO'
    REVISION_APROBADO = 'APROBADO'
    REVISION_CHOICES = [
        (REVISION_PENDIENTE, 'Pendiente de validación'),
        (REVISION_VALIDADO, 'Validado por el técnico'),
        (REVISION_OBSERVADO, 'Observado'),
        (REVISION_APROBADO, 'Aprobado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    gestion = models.IntegerField(default=2026, verbose_name='Gestión inicial')
    estado = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default=ESTADO_BORRADOR,
        verbose_name='Estado',
    )
    datos = models.JSONField(default=dict, verbose_name='Datos del asistente')
    id_resultado_pei = models.ForeignKey(
        ResultadoPEI, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='borradores_matriz_pei',
        verbose_name='Resultado PEI materializado',
    )

    estado_revision = models.CharField(
        max_length=20, choices=REVISION_CHOICES, default=REVISION_PENDIENTE,
        verbose_name='Estado de revisión',
    )
    validado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='matrices_pei_validadas', verbose_name='Validado por',
    )
    validado_en = models.DateTimeField(null=True, blank=True, verbose_name='Validado en')
    aprobado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='matrices_pei_aprobadas', verbose_name='Aprobado por',
    )
    aprobado_en = models.DateTimeField(null=True, blank=True, verbose_name='Aprobado en')
    observacion = models.TextField(blank=True, verbose_name='Observación')
    observado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='matrices_pei_observadas', verbose_name='Observado por',
    )
    observado_en = models.DateTimeField(null=True, blank=True, verbose_name='Observado en')

    class Meta:
        verbose_name = 'Borrador de Matriz PEI'
        verbose_name_plural = 'Borradores de Matrices PEI'
        ordering = ['-created_at']

    def __str__(self):
        return (
            f'Borrador PEI G{self.gestion} {self.get_estado_display()} '
            f'({self.created_at:%Y-%m-%d %H:%M})'
        )


class BorradorMatrizPOA(TimeStampedModel):
    """Borrador del asistente de Matriz POA (guardado por secciones).

    Espejo de :class:`BorradorMatrizPEI` para el instrumento operativo anual.
    Cada sección del asistente persiste en ``datos`` mediante PATCH parcial
    (``seccion`` + ``valores``); la action ``materializar`` crea la cadena
    operativa (AccionPOA → OperacionPOAU → ActividadPOAU → TareaPOAU) en una
    transacción y deja el borrador en COMPLETO.

    Estructura de ``datos``::

        s1_articulacion: {producto_pei, cod_producto_pei,
                          accion_institucional_especifica, indicador_proceso,
                          cod_resultado_pei, resultado_pei}
        s2_responsable:  {unidad_responsable, area_responsable}
        acciones: [
          {codigo, denominacion, resultado_esperado,
           programa, proyecto, actividad, categoria_programatica,
           presupuesto_programado, cargo_reacp, fecha_inicio, fecha_fin,
           operaciones: [
             {denominacion, tipo_operacion, producto_entregable,
              unidad_ejecutora, responsable, meta_anual,
              fecha_inicio, fecha_fin,
              actividades: [
                {denominacion, producto_entregable, meta_anual,
                 fecha_inicio, fecha_fin,
                 tareas: [{denominacion, responsable, metas,
                           fecha_inicio, fecha_fin}]}
              ]}
           ]}
        ]
    """

    ESTADO_BORRADOR = 'BORRADOR'
    ESTADO_COMPLETO = 'COMPLETO'
    ESTADO_CHOICES = [
        (ESTADO_BORRADOR, 'Borrador'),
        (ESTADO_COMPLETO, 'Completo'),
    ]

    SECCIONES = (
        's1_articulacion',
        's2_responsable',
        'acciones',
    )

    # Circuito de revisión: idéntico al del PAD y al del PEI.
    REVISION_PENDIENTE = 'PENDIENTE'
    REVISION_VALIDADO = 'VALIDADO'
    REVISION_OBSERVADO = 'OBSERVADO'
    REVISION_APROBADO = 'APROBADO'
    REVISION_CHOICES = [
        (REVISION_PENDIENTE, 'Pendiente de validación'),
        (REVISION_VALIDADO, 'Validado por el técnico'),
        (REVISION_OBSERVADO, 'Observado'),
        (REVISION_APROBADO, 'Aprobado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    gestion = models.IntegerField(default=2026, verbose_name='Gestión fiscal')
    estado = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default=ESTADO_BORRADOR,
        verbose_name='Estado',
    )
    datos = models.JSONField(default=dict, verbose_name='Datos del asistente')
    id_accion_poa = models.ForeignKey(
        AccionPOA, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='borradores_matriz_poa',
        verbose_name='Acción POA materializada',
    )

    estado_revision = models.CharField(
        max_length=20, choices=REVISION_CHOICES, default=REVISION_PENDIENTE,
        verbose_name='Estado de revisión',
    )
    validado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='matrices_poa_validadas', verbose_name='Validado por',
    )
    validado_en = models.DateTimeField(null=True, blank=True, verbose_name='Validado en')
    aprobado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='matrices_poa_aprobadas', verbose_name='Aprobado por',
    )
    aprobado_en = models.DateTimeField(null=True, blank=True, verbose_name='Aprobado en')
    observacion = models.TextField(blank=True, verbose_name='Observación')
    observado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='matrices_poa_observadas', verbose_name='Observado por',
    )
    observado_en = models.DateTimeField(null=True, blank=True, verbose_name='Observado en')

    class Meta:
        verbose_name = 'Borrador de Matriz POA'
        verbose_name_plural = 'Borradores de Matrices POA'
        ordering = ['-created_at']

    def __str__(self):
        return (
            f'Borrador POA G{self.gestion} {self.get_estado_display()} '
            f'({self.created_at:%Y-%m-%d %H:%M})'
        )
