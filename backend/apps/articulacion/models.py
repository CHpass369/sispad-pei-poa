import uuid
from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel


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


class ResultadoPAD(TimeStampedModel):
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


class ProductoPAD(TimeStampedModel):
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
        indexes = [
            models.Index(fields=['resultado_pad']),
        ]

    def __str__(self):
        return f'[{self.codigo_producto}] {self.denominacion[:80]}'


class ResultadoPEI(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo_resultado = models.CharField(max_length=50, verbose_name='Código resultado')
    denominacion = models.TextField(verbose_name='Denominación')
    cod_entidad = models.CharField(max_length=10, verbose_name='Código entidad')
    entidad = models.CharField(max_length=300, verbose_name='Entidad')
    cod_oei = models.CharField(max_length=10, blank=True, verbose_name='Código OEI')
    vigencia_desde = models.IntegerField(verbose_name='Vigencia desde')
    vigencia_hasta = models.IntegerField(verbose_name='Vigencia hasta')

    class Meta:
        verbose_name = 'Resultado PEI'
        verbose_name_plural = 'Resultados PEI'
        ordering = ['codigo_resultado']
        unique_together = [('codigo_resultado', 'vigencia_desde')]
        indexes = [
            models.Index(fields=['vigencia_desde']),
        ]

    def __str__(self):
        return f'[{self.codigo_resultado}] {self.denominacion[:80]}'


class ProductoPEI(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo_producto = models.CharField(max_length=50, verbose_name='Código producto')
    denominacion = models.TextField(verbose_name='Denominación')
    resultado_pei = models.ForeignKey(
        ResultadoPEI, on_delete=models.CASCADE,
        related_name='productos', verbose_name='Resultado PEI'
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
        indexes = [
            models.Index(fields=['resultado_pei']),
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


class AccionPOA(TimeStampedModel):
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
        indexes = [
            models.Index(fields=['gestion', 'estado']),
            models.Index(fields=['producto_pei']),
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


class OperacionPOAU(TimeStampedModel):
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
    estado = models.CharField(max_length=20, default='REFERENCIAL', verbose_name='Estado')

    class Meta:
        verbose_name = 'Operación POAU'
        verbose_name_plural = 'Operaciones POAU'
        ordering = ['codigo_operacion']
        indexes = [
            models.Index(fields=['accion_poa']),
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


class ActividadPOAU(TimeStampedModel):
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
    estado = models.CharField(max_length=20, default='REFERENCIAL', verbose_name='Estado')

    class Meta:
        verbose_name = 'Actividad POAU'
        verbose_name_plural = 'Actividades POAU'
        ordering = ['codigo_actividad']
        indexes = [
            models.Index(fields=['operacion']),
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


class TareaPOAU(TimeStampedModel):
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
    estado = models.CharField(max_length=20, default='REFERENCIAL', verbose_name='Estado')

    class Meta:
        verbose_name = 'Tarea POAU'
        verbose_name_plural = 'Tareas POAU'
        ordering = ['codigo_tarea']
        indexes = [
            models.Index(fields=['actividad']),
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
            models.Index(fields=['accion_poa']),
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
