"""Single entry point for institutional PAD-PEI-POA-POAU coding."""
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.gestion.models import GestionFiscal
from apps.codificacion.models import (
    NIVEL_ARTICULACION_CHOICES,
    CodigoSegmentadoModel,
    EntidadCodificadora,
    EntidadTerritorialCGEO,
    HomologacionCodigo,
    SecuenciaCodigo,
    VersionCatalogoPlan,
)


class CodificadorService:
    """Generate, validate, and promote backend-owned institutional codes."""

    ENTIDAD_CODIFICADORA = '1312'
    NIVELES = {valor for valor, _ in NIVEL_ARTICULACION_CHOICES}
    ORDEN_SEGMENTOS = (
        'EE', 'CC', 'SS', 'RS', 'CGEO', 'LL', 'RT', 'PT',
        'ENTI', 'OE', 'RI', 'PI', 'ACP', 'OP', 'ACT', 'TAR',
    )
    ANCHOS = {
        'EE': 2, 'CC': 2, 'SS': 2, 'RS': 2, 'CGEO': 6,
        'LL': 2, 'RT': 2, 'PT': 2, 'ENTI': 4, 'OE': 2,
        'RI': 2, 'PI': 2, 'ACP': 3, 'OP': 3, 'ACT': 3, 'TAR': 3,
    }
    ANCHO_POR_NIVEL = {
        'resultado_pad': 2,
        'producto_pad': 2,
        'resultado_pei': 2,
        'producto_pei': 2,
        'accion_poa': 3,
        'operacion_poau': 3,
        'actividad_poau': 3,
        'tarea_poau': 3,
    }
    NIVEL_POR_MODELO = {
        'ResultadoPAD': 'resultado_pad',
        'ProductoPAD': 'producto_pad',
        'ResultadoPEI': 'resultado_pei',
        'ProductoPEI': 'producto_pei',
        'AccionPOA': 'accion_poa',
        'OperacionPOAU': 'operacion_poau',
        'ActividadPOAU': 'actividad_poau',
        'TareaPOAU': 'tarea_poau',
    }
    CAMPO_LEGACY_POR_MODELO = {
        'ResultadoPAD': 'codigo_resultado',
        'ProductoPAD': 'codigo_producto',
        'ResultadoPEI': 'codigo_resultado',
        'ProductoPEI': 'codigo_producto',
        'AccionPOA': 'codigo_accion',
        'OperacionPOAU': 'codigo_operacion',
        'ActividadPOAU': 'codigo_actividad',
        'TareaPOAU': 'codigo_tarea',
    }

    @classmethod
    @transaction.atomic
    def siguiente_correlativo(cls, nivel, padre_id, gestion, entidad):
        """Atomically emit the next value, including first-row races."""
        if nivel not in cls.NIVELES:
            raise ValidationError({'nivel': 'Nivel de articulación inválido.'})
        if not isinstance(entidad, EntidadCodificadora):
            raise ValidationError({'entidad': 'Entidad codificadora inválida.'})
        if entidad.codigo != cls.ENTIDAD_CODIFICADORA or not entidad.activo:
            raise ValidationError({'entidad': 'Solo se admite la entidad activa 1312.'})

        # PIP-DB-003: gestion es FK a GestionFiscal (año → instancia).
        if isinstance(gestion, GestionFiscal):
            gestion_fiscal = gestion
        else:
            if not isinstance(gestion, int) or isinstance(gestion, bool) or gestion < 1:
                raise ValidationError({'gestion': 'La gestión debe ser un entero positivo.'})
            gestion_fiscal = GestionFiscal.objects.filter(anio=gestion).first()
            if gestion_fiscal is None:
                raise ValidationError({
                    'gestion': (
                        f'La gestión {gestion} no existe en GestionFiscal '
                        '(PIP-DB-003: no se inventan gestiones).'
                    ),
                })

        clave = {
            'nivel': nivel,
            'padre_id': padre_id,
            'gestion': gestion_fiscal,
            'entidad': entidad,
        }
        try:
            secuencia = SecuenciaCodigo.objects.select_for_update().get(**clave)
        except SecuenciaCodigo.DoesNotExist:
            try:
                with transaction.atomic():
                    SecuenciaCodigo.objects.create(**clave)
            except IntegrityError:
                # A concurrent transaction created the unique key first.
                pass
            secuencia = SecuenciaCodigo.objects.select_for_update().get(**clave)

        maximo = (10 ** cls.ANCHO_POR_NIVEL[nivel]) - 1
        if secuencia.ultimo_valor >= maximo:
            raise ValidationError({
                'secuencia': (
                    f'El nivel {nivel} agotó su máximo correlativo {maximo}.'
                ),
            })
        secuencia.ultimo_valor += 1
        secuencia.save(update_fields=['ultimo_valor', 'updated_at'])
        return secuencia.ultimo_valor

    @classmethod
    def normalizar(cls, nivel, valor):
        """Strip and left-pad one numeric segment to its contractual width."""
        nombre = str(nivel).upper()
        ancho = cls.ANCHOS.get(nombre)
        texto = str(valor).strip()
        if ancho is None:
            raise ValidationError({'nivel': 'Segmento de código desconocido.'})
        if not texto.isdigit() or len(texto) > ancho:
            raise ValidationError({
                'valor': f'El segmento {nombre} debe contener hasta {ancho} dígitos.',
            })
        return texto.zfill(ancho)

    @classmethod
    def validar_codigo(cls, codigo, para_oficial=False):
        """Validate exact count, numeric content, widths, and official non-zero."""
        segmentos = str(codigo).split('.')
        if len(segmentos) != len(cls.ORDEN_SEGMENTOS):
            raise ValidationError({
                'codigo': 'El código completo debe contener exactamente 16 segmentos.',
            })

        errores = {}
        for nombre, segmento in zip(cls.ORDEN_SEGMENTOS, segmentos, strict=True):
            ancho = cls.ANCHOS[nombre]
            if not segmento.isdigit() or len(segmento) != ancho:
                errores[nombre] = f'Debe contener exactamente {ancho} dígitos.'
            elif para_oficial and int(segmento) == 0:
                errores[nombre] = 'Un código OFICIAL no admite segmentos cero.'
        if errores:
            raise ValidationError(errores)
        return True

    @classmethod
    def _contexto(cls, instancia):
        """Resolve canonical ancestors without inventing ambiguous relations."""
        from apps.articulacion.models import (
            AccionPOA,
            ActividadPOAU,
            ArticulacionPADPEI,
            OperacionPOAU,
            ProductoPAD,
            ProductoPEI,
            ResultadoPAD,
            ResultadoPEI,
            TareaPOAU,
        )

        modelos = (
            ResultadoPAD, ProductoPAD, ResultadoPEI, ProductoPEI,
            AccionPOA, OperacionPOAU, ActividadPOAU, TareaPOAU,
        )
        if not isinstance(instancia, modelos):
            raise ValidationError('El modelo no pertenece a la cadena codificable.')

        contexto = {
            'resultado_pad': None,
            'producto_pad': None,
            'resultado_pei': None,
            'producto_pei': None,
            'accion': None,
            'operacion': None,
            'actividad': None,
            'tarea': None,
            'articulacion_ambigua': False,
        }

        if isinstance(instancia, TareaPOAU):
            contexto['tarea'] = instancia
            contexto['actividad'] = instancia.actividad
        elif isinstance(instancia, ActividadPOAU):
            contexto['actividad'] = instancia
        if contexto['actividad'] is not None:
            contexto['operacion'] = contexto['actividad'].operacion
        elif isinstance(instancia, OperacionPOAU):
            contexto['operacion'] = instancia
        if contexto['operacion'] is not None:
            contexto['accion'] = contexto['operacion'].accion_poa
        elif isinstance(instancia, AccionPOA):
            contexto['accion'] = instancia
        if contexto['accion'] is not None:
            contexto['producto_pei'] = contexto['accion'].producto_pei
        elif isinstance(instancia, ProductoPEI):
            contexto['producto_pei'] = instancia
        if contexto['producto_pei'] is not None:
            contexto['resultado_pei'] = contexto['producto_pei'].resultado_pei
        elif isinstance(instancia, ResultadoPEI):
            contexto['resultado_pei'] = instancia

        if contexto['producto_pei'] is not None:
            enlaces = list(ArticulacionPADPEI.objects.filter(
                producto_pei=contexto['producto_pei'],
            ).select_related('producto_pad__resultado_pad')[:2])
            if len(enlaces) == 1:
                contexto['producto_pad'] = enlaces[0].producto_pad
            elif len(enlaces) > 1:
                contexto['articulacion_ambigua'] = True
        elif isinstance(instancia, ProductoPAD):
            contexto['producto_pad'] = instancia
        if contexto['producto_pad'] is not None:
            contexto['resultado_pad'] = contexto['producto_pad'].resultado_pad
        elif isinstance(instancia, ResultadoPAD):
            contexto['resultado_pad'] = instancia

        return contexto

    @staticmethod
    def _segmento_instancia(instancia):
        if instancia is None:
            return None
        if instancia.correlativo is None:
            if instancia.segmento:
                raise ValidationError({
                    'segmento': 'No puede existir sin correlativo.',
                })
            return None
        derivado = instancia.generar_segmento(instancia.correlativo)
        if instancia.segmento and instancia.segmento != derivado:
            raise ValidationError({
                'segmento': 'Debe coincidir con el correlativo normalizado.',
            })
        return derivado

    @classmethod
    def _segmentos(cls, instancia):
        contexto = cls._contexto(instancia)
        resultado_pad = contexto['resultado_pad']
        producto_pad = contexto['producto_pad']
        resultado_pei = contexto['resultado_pei']
        producto_pei = contexto['producto_pei']

        resultado_sectorial = (
            resultado_pad.resultado_sectorial_catalogo if resultado_pad else None
        )
        sector = resultado_sectorial.sector if resultado_sectorial else None
        componente = sector.componente if sector else None
        eje = componente.eje if componente else None

        valores = {
            'EE': eje.codigo if eje else None,
            'CC': componente.codigo if componente else None,
            'SS': sector.codigo if sector else None,
            'RS': resultado_sectorial.codigo if resultado_sectorial else None,
            'CGEO': (
                resultado_pad.entidad_territorial_cgeo.codigo
                if resultado_pad and resultado_pad.entidad_territorial_cgeo else None
            ),
            'LL': (
                resultado_pad.lineamiento_pad_catalogo.codigo
                if resultado_pad and resultado_pad.lineamiento_pad_catalogo else None
            ),
            'RT': cls._segmento_instancia(resultado_pad),
            'PT': cls._segmento_instancia(producto_pad),
            'ENTI': (
                resultado_pei.entidad_codificadora.codigo
                if resultado_pei and resultado_pei.entidad_codificadora else None
            ),
            'OE': (resultado_pei.cod_oei or None) if resultado_pei else None,
            'RI': cls._segmento_instancia(resultado_pei),
            'PI': cls._segmento_instancia(producto_pei),
            'ACP': cls._segmento_instancia(contexto['accion']),
            'OP': cls._segmento_instancia(contexto['operacion']),
            'ACT': cls._segmento_instancia(contexto['actividad']),
            'TAR': cls._segmento_instancia(contexto['tarea']),
        }
        return contexto, valores

    @classmethod
    def generar_codigo_completo(cls, instancia):
        """Build 16 normalized positions; omit missing FKs and flag the record."""
        contexto, valores = cls._segmentos(instancia)
        normalizados = {
            nombre: cls.normalizar(nombre, valor) if valor is not None else None
            for nombre, valor in valores.items()
        }
        instancia.articulacion_incompleta = (
            contexto['articulacion_ambigua']
            or any(valor is None for valor in normalizados.values())
        )
        codigo = '.'.join(
            normalizados[nombre]
            for nombre in cls.ORDEN_SEGMENTOS
            if normalizados[nombre] is not None
        )
        instancia.codigo_completo_articulacion = codigo
        return codigo

    @classmethod
    def _gestion(cls, contexto):
        if contexto['accion'] is not None:
            return contexto['accion'].gestion
        if contexto['resultado_pei'] is not None:
            return contexto['resultado_pei'].vigencia_desde
        if contexto['resultado_pad'] is not None:
            return contexto['resultado_pad'].vigencia_desde
        return None

    @classmethod
    def validar(cls, instancia, para_oficial=False):
        """Validate format, hierarchy, catalogs, management, entity, and uniqueness."""
        if not isinstance(instancia, CodigoSegmentadoModel):
            raise ValidationError('El registro no implementa codificación segmentada.')

        contexto, _ = cls._segmentos(instancia)
        codigo = cls.generar_codigo_completo(instancia)
        if contexto['articulacion_ambigua']:
            raise ValidationError({
                'articulacion': 'La relación PAD-PEI debe ser única para codificar.',
            })
        if para_oficial and instancia.articulacion_incompleta:
            raise ValidationError({
                'articulacion': 'La articulación debe contener los 16 segmentos.',
            })
        if not instancia.articulacion_incompleta:
            cls.validar_codigo(codigo, para_oficial=para_oficial)

        resultado_pad = contexto['resultado_pad']
        resultado_pei = contexto['resultado_pei']
        gestion = cls._gestion(contexto)
        if resultado_pad is not None and resultado_pad.resultado_sectorial_catalogo:
            resultado = resultado_pad.resultado_sectorial_catalogo
            sector = resultado.sector
            componente = sector.componente
            eje = componente.eje
            versiones = {
                resultado.version_catalogo_id,
                sector.version_catalogo_id,
                componente.version_catalogo_id,
                eje.version_catalogo_id,
            }
            if len(versiones) != 1:
                raise ValidationError({'jerarquia': 'La cadena nacional mezcla versiones.'})
            version_nacional = resultado.version_catalogo
            if (
                version_nacional.estado != VersionCatalogoPlan.ESTADO_VIGENTE
                or version_nacional.gestion != gestion
                or not all(item.activo for item in (eje, componente, sector, resultado))
            ):
                raise ValidationError({
                    'catalogo_nacional': 'El catálogo nacional debe estar activo y vigente para la gestión.',
                })
            if para_oficial:
                cls._validar_respaldo_oficial(
                    version_nacional, 'catalogo_nacional',
                )

        if resultado_pad is not None and resultado_pad.lineamiento_pad_catalogo:
            lineamiento = resultado_pad.lineamiento_pad_catalogo
            cgeo = resultado_pad.entidad_territorial_cgeo
            if (
                lineamiento.version_catalogo.estado
                != VersionCatalogoPlan.ESTADO_VIGENTE
                or lineamiento.version_catalogo.gestion != gestion
                or not lineamiento.activo
            ):
                raise ValidationError({
                    'lineamiento_pad': 'El lineamiento debe estar activo y vigente para la gestión.',
                })
            if para_oficial:
                cls._validar_respaldo_oficial(
                    lineamiento.version_catalogo, 'lineamiento_pad',
                )
            if cgeo and lineamiento.entidad_territorial_id != cgeo.pk:
                raise ValidationError({
                    'lineamiento_pad': 'El lineamiento no corresponde al CGEO seleccionado.',
                })

        if resultado_pad is not None and resultado_pad.entidad_territorial_cgeo:
            cgeo = resultado_pad.entidad_territorial_cgeo
            if cgeo.nivel != EntidadTerritorialCGEO.NIVEL_MUNICIPIO:
                raise ValidationError({'cgeo': 'El segmento CGEO debe ser municipal.'})
            if para_oficial and cgeo.estado != EntidadTerritorialCGEO.ESTADO_OFICIAL:
                raise ValidationError({'cgeo': 'El CGEO debe estar en estado OFICIAL.'})

        if resultado_pei is not None and resultado_pei.entidad_codificadora:
            entidad = resultado_pei.entidad_codificadora
            if entidad.codigo != cls.ENTIDAD_CODIFICADORA or not entidad.activo:
                raise ValidationError({'entidad': 'Solo se admite la entidad activa 1312.'})
            if resultado_pei.cod_entidad.strip() != entidad.codigo:
                raise ValidationError({'entidad': 'La entidad PEI no coincide con ENTI.'})

        if codigo and type(instancia).objects.exclude(pk=instancia.pk).filter(
            codigo_completo_articulacion=codigo,
        ).exists():
            raise ValidationError({'codigo': 'El código completo ya está asignado.'})
        return True

    @staticmethod
    def _validar_respaldo_oficial(version, campo):
        if version.clasificacion_fuente != VersionCatalogoPlan.FUENTE_OFICIAL:
            raise ValidationError({
                campo: 'La versión debe provenir de una fuente OFICIAL.',
            })
        if not version.norma_aprobacion.strip():
            raise ValidationError({
                campo: 'La versión OFICIAL requiere norma de aprobación.',
            })

    @classmethod
    def _ruta_operativa(cls, instancia):
        contexto = cls._contexto(instancia)
        return [
            contexto[nombre]
            for nombre in ('accion', 'operacion', 'actividad', 'tarea')
            if contexto[nombre] is not None
        ]

    @classmethod
    def generar_codigo_operativo(cls, instancia):
        """Build GESTION.ENTIDAD.ACP[.OP.ACT.TAR] for operational records."""
        contexto = cls._contexto(instancia)
        ruta = cls._ruta_operativa(instancia)
        if not ruta or contexto['accion'] is None:
            raise ValidationError('El registro no pertenece a la cadena POA operativa.')
        resultado_pei = contexto['resultado_pei']
        entidad = resultado_pei.entidad_codificadora if resultado_pei else None
        if entidad is None:
            raise ValidationError({'entidad_codificadora': 'La entidad es obligatoria.'})
        segmentos = [str(contexto['accion'].gestion), entidad.codigo]
        segmentos.extend(cls._segmento_instancia(item) for item in ruta)
        if any(segmento is None for segmento in segmentos):
            raise ValidationError('La cadena operativa aún no tiene correlativos completos.')
        return '.'.join(segmentos)

    @classmethod
    @transaction.atomic
    def promover_a_oficial(
        cls, instancia, *, usuario, motivo, documento_respaldo='',
    ):
        """Validate, persist, audit, and freeze one complete official code."""
        if not isinstance(instancia, CodigoSegmentadoModel) or not instancia.pk:
            raise ValidationError('El registro codificable debe existir antes de promoverse.')
        if usuario is None or not getattr(usuario, 'pk', None):
            raise ValidationError({'usuario': 'El usuario responsable es obligatorio.'})
        if not str(motivo).strip():
            raise ValidationError({'motivo': 'El motivo de homologación es obligatorio.'})

        bloqueada = type(instancia).objects.select_for_update().get(pk=instancia.pk)
        if bloqueada.estado_codigo == bloqueada.ESTADO_CODIGO_OFICIAL:
            raise ValidationError({'estado_codigo': 'El código ya es OFICIAL.'})

        cls.generar_codigo_completo(bloqueada)
        cls.validar(bloqueada, para_oficial=True)
        segmento = bloqueada.generar_segmento(bloqueada.correlativo)
        bloqueada.segmento = segmento
        bloqueada.codigo_normalizado = segmento
        bloqueada.estado_codigo = bloqueada.ESTADO_CODIGO_OFICIAL
        bloqueada._permitir_promocion_oficial = True
        try:
            bloqueada.save(update_fields=[
                'segmento',
                'codigo_normalizado',
                'codigo_completo_articulacion',
                'articulacion_incompleta',
                'estado_codigo',
                'updated_at',
            ])
        finally:
            delattr(bloqueada, '_permitir_promocion_oficial')

        nombre_modelo = type(bloqueada).__name__
        codigo_anterior = bloqueada.codigo_fuente or getattr(
            bloqueada, cls.CAMPO_LEGACY_POR_MODELO[nombre_modelo],
        )
        contexto = cls._contexto(bloqueada)
        # PIP-DB-003: gestion es FK; se resuelve el año a GestionFiscal sin
        # inventar gestiones (no se cambia _gestion, usado contra años int).
        gestion_anio = cls._gestion(contexto)
        gestion_fiscal = (
            gestion_anio
            if isinstance(gestion_anio, GestionFiscal)
            else GestionFiscal.objects.filter(anio=gestion_anio).first()
            if gestion_anio is not None
            else None
        )
        if gestion_fiscal is None:
            raise ValidationError({
                'gestion': (
                    'La gestión del registro no existe en GestionFiscal '
                    '(PIP-DB-003: no se inventan gestiones).'
                ),
            })
        HomologacionCodigo.objects.create(
            tipo_entidad=cls.NIVEL_POR_MODELO[nombre_modelo],
            entidad_id=bloqueada.pk,
            codigo_anterior=codigo_anterior,
            codigo_nuevo=bloqueada.codigo_completo_articulacion,
            motivo=str(motivo).strip(),
            gestion=gestion_fiscal,
            usuario=usuario,
            documento_respaldo=str(documento_respaldo).strip(),
        )
        return bloqueada
