import uuid
from django.db import models
from django.contrib.gis.db import models as gis_models
from apps.core.models import TimeStampedModel
from apps.core.texto import normalizar
from apps.gestion.models import GestionFiscal


class Distrito(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=10)
    nombre = models.CharField(max_length=200)
    geometria = gis_models.MultiPolygonField(srid=4326, null=True, blank=True)

    class Meta:
        verbose_name = 'Distrito'
        verbose_name_plural = 'Distritos'

    def __str__(self):
        return f'{self.codigo} - {self.nombre}'


def clave_organizacion(nombre):
    """Clave de unicidad del padrón, más dura que `normalizar`.

    `normalizar` deja `O.T.B. VILLA` como `O T B VILLA` y `OTB VILLA` como
    `OTB VILLA`: dos claves para la misma organización. En las planillas de los
    doce distritos conviven las dos grafías, así que las siglas punteadas se
    vuelven a pegar. Solo se junta una corrida de DOS O MÁS letras sueltas, que
    es lo que deja una sigla; una letra suelta al final —`OTB SAN JOSE B`— es
    parte del nombre y se respeta.

    Lo que NO hace es traducir abreviaturas: `J.V.` y `JUNTA VECINAL` siguen
    siendo claves distintas. Equipararlas sería adivinar, y el nombre completo
    es el que se imprime en el acta.
    """
    palabras, salida, sigla = normalizar(nombre).split(), [], []

    def cerrar():
        if len(sigla) > 1:
            salida.append(''.join(sigla))
        else:
            salida.extend(sigla)
        sigla.clear()

    for palabra in palabras:
        if len(palabra) == 1 and palabra.isalpha():
            sigla.append(palabra)
            continue
        cerrar()
        salida.append(palabra)
    cerrar()
    return ' '.join(salida)


class TipoUnidadTerritorial(models.TextChoices):
    """Cómo se llama a sí misma la organización.

    Sale del propio nombre que trae la planilla —`OTB ...`, `JUNTA VECINAL
    ...`, `SINDICATO AGRARIO ...`—. Es una etiqueta para filtrar y agrupar: el
    nombre completo se guarda tal cual vino y es el que sale impreso en el acta.
    """
    OTB = 'otb', 'OTB'
    JUNTA_VECINAL = 'junta_vecinal', 'Junta vecinal'
    COMUNIDAD = 'comunidad', 'Comunidad'
    SINDICATO = 'sindicato', 'Sindicato agrario'
    SUBCENTRAL = 'subcentral', 'Subcentral'
    ZONA = 'zona', 'Zona'
    ESTABLECIMIENTO = 'establecimiento', 'Establecimiento'
    OTRO = 'otro', 'Otro'


class UnidadTerritorial(models.Model):
    """Tabla maestra de organizaciones sociales territoriales (OST).

    Es el dominio que llena los campos «OTB / Junta vecinal» del acta de
    priorización. Una fila por organización y por distrito; quién la preside
    NO vive acá porque rota, va en `DirigenteTerritorial`.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=20)
    nombre = models.CharField(max_length=300)
    # Clave plana para buscar y para detectar la misma organización escrita de
    # otra forma: `O.T.B. SAN JOSÉ` y `OTB SAN JOSE` colapsan en la misma.
    # La arma `clave_organizacion`, no `normalizar` a secas.
    nombre_busqueda = models.TextField(blank=True, db_index=True,
                                       verbose_name='Nombre normalizado')
    tipo = models.CharField(max_length=50, choices=TipoUnidadTerritorial.choices)
    distrito = models.ForeignKey(Distrito, on_delete=models.SET_NULL, null=True, blank=True, related_name='unidades_territoriales')
    geometria = gis_models.MultiPolygonField(srid=4326, null=True, blank=True)
    centroide = gis_models.PointField(srid=4326, null=True, blank=True)
    poblacion = models.PositiveIntegerField(null=True, blank=True)
    superficie_ha = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    activa = models.BooleanField(
        default=True, verbose_name='Vigente',
        help_text='Se desmarca en vez de borrar: las actas ya emitidas la citan.')
    observacion = models.TextField(blank=True, verbose_name='Observación')

    class Meta:
        verbose_name = 'Unidad territorial'
        verbose_name_plural = 'Unidades territoriales'
        ordering = ['distrito', 'tipo', 'nombre']
        constraints = [
            # Una organización no se repite dentro de su distrito. Sin esto,
            # reimportar la planilla duplica todo el padrón.
            models.UniqueConstraint(fields=['distrito', 'nombre_busqueda'],
                                    name='unidad_territorial_unica_por_distrito'),
        ]

    def save(self, *args, **kwargs):
        self.nombre_busqueda = clave_organizacion(self.nombre)
        super().save(*args, **kwargs)

    @property
    def dirigente_vigente(self):
        """El dirigente marcado vigente más reciente, o nada."""
        return self.dirigentes.filter(vigente=True).order_by('-gestion').first()

    def __str__(self):
        return f'{self.nombre} ({self.get_tipo_display()})'


class DirigenteTerritorial(TimeStampedModel):
    """Quién representa a la organización en una gestión.

    Va aparte de la organización porque el cargo ROTA: cada gestión se carga
    una planilla nueva. Si el nombre viviera en `UnidadTerritorial`, importar
    el padrón del año siguiente pisaría en silencio quién firmó las actas
    anteriores.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    unidad = models.ForeignKey(
        UnidadTerritorial, on_delete=models.CASCADE, related_name='dirigentes',
        verbose_name='Organización territorial')
    gestion = models.PositiveIntegerField(
        db_index=True, verbose_name='Gestión',
        help_text='Gestión POA a la que sirve este padrón, no el año en que se '
                  'levantó: es la que busca el formulario del acta.')
    nombre = models.CharField(max_length=200, verbose_name='Nombre del dirigente')
    # La planilla trae presidentes y secretarios generales, y a veces la celda
    # viene vacía: el cargo es texto libre, no una lista cerrada.
    cargo = models.CharField(max_length=80, blank=True, verbose_name='Cargo')
    telefono = models.CharField(max_length=40, blank=True, verbose_name='Teléfono')
    vigente = models.BooleanField(default=True, verbose_name='Vigente')
    observacion = models.TextField(blank=True, verbose_name='Observación')

    class Meta:
        verbose_name = 'Dirigente territorial'
        verbose_name_plural = 'Dirigentes territoriales'
        ordering = ['unidad', '-gestion', 'cargo']
        constraints = [
            models.UniqueConstraint(fields=['unidad', 'gestion', 'cargo'],
                                    name='dirigente_unico_por_gestion_y_cargo'),
        ]

    def __str__(self):
        return f'{self.nombre} · {self.cargo or "sin cargo"} ({self.gestion})'


class LocalizacionTerritorial(TimeStampedModel):
    """Vincula acciones/proyectos con geometrías y unidades territoriales"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entidad = models.CharField(max_length=50, help_text='Nombre del modelo asociado')
    entidad_id = models.CharField(max_length=100, help_text='ID del registro')
    geometria = gis_models.GeometryField(srid=32719, null=True, blank=True, help_text='Geometría en EPSG:32719 (métrica)')
    geometria_4326 = gis_models.GeometryField(srid=4326, null=True, blank=True, help_text='Geometría en EPSG:4326 (web)')
    distrito = models.ForeignKey(Distrito, on_delete=models.SET_NULL, null=True, blank=True, related_name='localizaciones')
    unidad_territorial = models.ForeignKey(UnidadTerritorial, on_delete=models.SET_NULL, null=True, blank=True, related_name='localizaciones')
    direccion_referencia = models.CharField(max_length=500, blank=True)
    gestion = models.ForeignKey(
        GestionFiscal, on_delete=models.PROTECT, db_column='gestion',
        related_name='+', verbose_name='Gestión fiscal',
    )
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Localización territorial'
        verbose_name_plural = 'Localizaciones territoriales'
        indexes = [
            models.Index(fields=['entidad', 'entidad_id']),
            models.Index(fields=['gestion']),
        ]

    def __str__(self):
        return f'{self.entidad}#{self.entidad_id} en {self.distrito}'
