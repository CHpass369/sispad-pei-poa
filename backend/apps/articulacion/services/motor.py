"""Motor de Articulación PIP (ADR-004): navegación de la cadena en ambos sentidos.

Servicio de dominio que implementa la trazabilidad estratégica y
presupuestaria de la cadena PAD → PEI → POA → POAU sobre los 8 modelos
codificables de ``apps.articulacion``, usando las FK reales de los modelos
(no polimorfismo ``tipo + id``, ver ADR-004) y reutilizando el contexto
canónico que ya resuelve :class:`CodificadorService`.

Es la base del Motor de Articulación PIP (plan maestro §28, §83-84):
las futuras herramientas visuales (wizards m1..m5, matrices) consumen
``cadena_descendente`` / ``cadena_ascendente`` en lugar de reconstruir
la navegación por su cuenta.

Reglas de diseño:

- NO se duplica la navegación ascendente: se consume
  ``CodificadorService._contexto`` (API interna estable de la app de
  codificación dentro del mismo monolith). El descenso es propio del motor
  porque no existe en CodificadorService.
- La cadena legacy PGDESA → PDESA → PDS → PAD → PEI → POA de
  ``apps.pad.views.ResultadoTerritorialViewSet.cadena_completa`` sigue
  siendo la fuente para el PAD legacy (enlace semántico por código +
  gestión); el motor generaliza la cadena codificable con FK reales y NO
  duplica ese endpoint.
- Robustez: tipo desconocido o entidad inexistente → se devuelve ``[]``
  (decisión documentada en la frontera PIP INTEGRACIÓN).
"""
from django.apps import apps as django_apps


class MotorArticulacion:
    """Navega la cadena PAD → PEI → POA → POAU en ambos sentidos.

    Entrada de ``cadena_descendente`` / ``cadena_ascendente``: nombre de la
    clase ('TareaPOAU', 'ResultadoPEI') + UUID de la entidad. Salida: lista
    de dicts ``{nivel, entidad_tipo, entidad_id, codigo, denominacion,
    gestion}`` en orden de cadena (de arriba hacia abajo para el descenso,
    de la entidad hacia arriba para el ascenso).
    """

    # Orden canónico de la cadena: coincide con el orden de los segmentos
    # RT → PT → RI → PI → ACP → OP → ACT → TAR de CodificadorService.
    ORDEN_CADENA = (
        'ResultadoPAD',
        'ProductoPAD',
        'ResultadoPEI',
        'ProductoPEI',
        'AccionPOA',
        'OperacionPOAU',
        'ActividadPOAU',
        'TareaPOAU',
    )

    # Clave de cada modelo dentro del contexto canónico de CodificadorService.
    _CLAVE_CONTEXTO = {
        'ResultadoPAD': 'resultado_pad',
        'ProductoPAD': 'producto_pad',
        'ResultadoPEI': 'resultado_pei',
        'ProductoPEI': 'producto_pei',
        'AccionPOA': 'accion',
        'OperacionPOAU': 'operacion',
        'ActividadPOAU': 'actividad',
        'TareaPOAU': 'tarea',
    }

    # ------------------------------------------------------------------
    # Resolución de tipos
    # ------------------------------------------------------------------
    @classmethod
    def _modelo_cadena(cls, entidad_tipo):
        """Devuelve la clase del modelo si es parte de la cadena, sino None."""
        if entidad_tipo not in cls.ORDEN_CADENA:
            return None
        return django_apps.get_model('articulacion', entidad_tipo)

    @staticmethod
    def _dedupe(objetos):
        """Elimina duplicados por (tipo, pk) preservando el orden."""
        vistos = set()
        unicos = []
        for obj in objetos:
            clave = (type(obj).__name__, str(obj.pk))
            if clave not in vistos:
                vistos.add(clave)
                unicos.append(obj)
        return unicos

    @classmethod
    def _ordenar_por_codigo(cls, objetos):
        if not objetos:
            return objetos
        from apps.codificacion.services.codificador import CodificadorService

        tipo = type(objetos[0]).__name__
        campo = CodificadorService.CAMPO_LEGACY_POR_MODELO[tipo]
        return sorted(
            objetos, key=lambda o: str(getattr(o, campo, '') or ''),
        )

    @classmethod
    def _a_dict(cls, instancia):
        """Convierte una entidad de la cadena al formato de salida del motor."""
        from apps.codificacion.services.codificador import CodificadorService

        tipo = type(instancia).__name__
        contexto = CodificadorService._contexto(instancia)
        codigo = getattr(
            instancia, CodificadorService.CAMPO_LEGACY_POR_MODELO[tipo], ''
        )
        return {
            'nivel': CodificadorService.NIVEL_POR_MODELO[tipo],
            'entidad_tipo': tipo,
            'entidad_id': str(instancia.pk),
            'codigo': codigo or '',
            'denominacion': instancia.denominacion,
            'gestion': CodificadorService._gestion(contexto),
        }

    # ------------------------------------------------------------------
    # Descenso (trazabilidad estratégica y presupuestaria hacia abajo)
    # ------------------------------------------------------------------
    @classmethod
    def cadena_descendente(cls, entidad_tipo, entidad_id):
        """Cadena desde ``entidad`` hacia abajo (p.ej. PAD → PEI → POA → POAU).

        El tramo PAD → PEI se resuelve por las FK reales de
        ``ArticulacionPADPEI`` (producto_pad → producto_pei); el tramo
        PEI → POA → POAU por las FK de cada nivel (producto_pei →
        acciones_poa → operaciones → actividades → tareas). Cuando el
        ResultadoPEI se alcanza desde el PAD, solo se emiten los productos
        PEI efectivamente vinculados (columna vertebral, no todos los
        hermanos); cuando el punto de partida es el propio ResultadoPEI se
        emiten todos sus productos.

        Tipo desconocido o entidad inexistente → ``[]``.
        """
        modelo = cls._modelo_cadena(entidad_tipo)
        if modelo is None:
            return []
        instancia = modelo.objects.filter(pk=entidad_id).first()
        if instancia is None:
            return []

        nivel_actual = cls.ORDEN_CADENA.index(entidad_tipo)
        pendientes = [instancia]
        resultado = [cls._a_dict(instancia)]
        pis_vinculados = []

        while nivel_actual < len(cls.ORDEN_CADENA) - 1:
            siguiente_tipo = cls.ORDEN_CADENA[nivel_actual + 1]
            siguiente, pis_vinculados = cls._nivel_siguiente(
                pendientes, entidad_tipo=siguiente_tipo,
                pis_vinculados=pis_vinculados,
            )
            if not siguiente:
                break
            resultado.extend(cls._a_dict(obj) for obj in siguiente)
            pendientes = siguiente
            nivel_actual += 1

        return resultado

    @classmethod
    def _nivel_siguiente(cls, registros, entidad_tipo, pis_vinculados):
        """Genera el nivel descendente ``entidad_tipo`` desde ``registros``."""
        tipo_actual = type(registros[0]).__name__ if registros else None
        if tipo_actual is None:
            return [], pis_vinculados

        if tipo_actual == 'ResultadoPAD':  # RT → PT
            hijos = [p for r in registros for p in r.productos.all()]
        elif tipo_actual == 'ProductoPAD':  # PT → RI vía articulación PAD-PEI
            productos_pei = cls._dedupe([
                enlace.producto_pei
                for pt in registros
                for enlace in pt.articulaciones_pei.select_related(
                    'producto_pei__resultado_pei',
                )
            ])
            pis_vinculados = cls._ordenar_por_codigo(productos_pei)
            hijos = cls._dedupe([
                p.resultado_pei for p in productos_pei if p.resultado_pei
            ])
        elif tipo_actual == 'ResultadoPEI':  # RI → PI
            if pis_vinculados:
                hijos = list(pis_vinculados)
            else:
                hijos = [p for r in registros for p in r.productos.all()]
        elif tipo_actual == 'ProductoPEI':  # PI → ACP
            hijos = [a for p in registros for a in p.acciones_poa.all()]
        elif tipo_actual == 'AccionPOA':  # ACP → OP
            hijos = [o for a in registros for o in a.operaciones.all()]
        elif tipo_actual == 'OperacionPOAU':  # OP → ACT
            hijos = [act for o in registros for act in o.actividades.all()]
        elif tipo_actual == 'ActividadPOAU':  # ACT → TAR
            hijos = [t for act in registros for t in act.tareas.all()]
        else:  # TareaPOAU: sin descendientes
            hijos = []

        return cls._ordenar_por_codigo(cls._dedupe(hijos)), pis_vinculados

    # ------------------------------------------------------------------
    # Ascenso (trazabilidad hacia el marco superior)
    # ------------------------------------------------------------------
    @classmethod
    def cadena_ascendente(cls, entidad_tipo, entidad_id):
        """Cadena desde ``entidad`` hacia arriba (p.ej. TAR → PAD).

        Reutiliza el contexto canónico de ``CodificadorService._contexto``
        (misma navegación por FK que usa el codificador, sin duplicarla):
        TareaPOAU → ActividadPOAU → OperacionPOAU → AccionPOA →
        ProductoPEI → ResultadoPEI → (ArticulacionPADPEI) → ProductoPAD →
        ResultadoPAD.

        Si la articulación PAD-PEI es ambigua (un producto PEI vinculado a
        varios productos PAD), la cadena asciende hasta PEI y se corta ahí:
        el motor no inventa un padre (ADR-004). Tipo desconocido o entidad
        inexistente → ``[]``.
        """
        from apps.codificacion.services.codificador import CodificadorService

        modelo = cls._modelo_cadena(entidad_tipo)
        if modelo is None:
            return []
        instancia = modelo.objects.filter(pk=entidad_id).first()
        if instancia is None:
            return []

        contexto = CodificadorService._contexto(instancia)
        nivel_entidad = cls.ORDEN_CADENA.index(entidad_tipo)
        tramo = [
            nombre
            for nombre in cls.ORDEN_CADENA[:nivel_entidad + 1]
            if contexto.get(cls._CLAVE_CONTEXTO[nombre]) is not None
        ]
        tramo.reverse()

        return [
            cls._a_dict(contexto[cls._CLAVE_CONTEXTO[nombre]])
            for nombre in tramo
        ]

    # ------------------------------------------------------------------
    # Kernel V2 (instrumentos versionados y vínculos estratégicos)
    # ------------------------------------------------------------------
    @classmethod
    def trazar_instrumento(cls, instancia):
        """Devuelve instrumento/versión y vínculos entrantes/salientes (V2).

        Acepta objetos del kernel estratégico SIS-PE
        (``planificacion.models_v2``): ``NodoEstrategico`` (sus vínculos
        salientes/entrantes sobre la versión) o ``VinculoEstrategico``
        (origen, destino y tipo sobre la versión del arco). La salida usa
        el formato V2 (ids + versión), distinto del formato de cadena:
        los vínculos pueden cruzar instrumentos (ADR-008).

        Cualquier otra instancia → ``[]``.
        """
        from apps.planificacion.models_v2 import NodoEstrategico, VinculoEstrategico

        if isinstance(instancia, NodoEstrategico):
            return cls._trazar_nodo(instancia)
        if isinstance(instancia, VinculoEstrategico):
            return cls._trazar_vinculo(instancia)
        return []

    @classmethod
    def _version_info(cls, version):
        return {
            'numero': version.numero,
            'etiqueta': version.etiqueta,
            'estado': version.estado,
            'inmutable': version.inmutable,
        }

    @classmethod
    def _nodo_info(cls, nodo):
        return {
            'id': str(nodo.pk),
            'codigo': nodo.codigo,
            'nombre': nodo.nombre,
            'tipo_nodo': nodo.tipo_nodo.codigo,
        }

    @classmethod
    def _trazar_nodo(cls, nodo):
        version = nodo.version
        salientes = [
            {
                'id': str(v.pk),
                'tipo': v.tipo.codigo,
                'destino': cls._nodo_info(v.destino),
                'ponderacion': str(v.ponderacion) if v.ponderacion is not None else None,
                'es_principal': v.es_principal,
            }
            for v in nodo.vinculos_origen.select_related('tipo', 'destino__tipo_nodo')
        ]
        entrantes = [
            {
                'id': str(v.pk),
                'tipo': v.tipo.codigo,
                'origen': cls._nodo_info(v.origen),
                'ponderacion': str(v.ponderacion) if v.ponderacion is not None else None,
                'es_principal': v.es_principal,
            }
            for v in nodo.vinculos_destino.select_related('tipo', 'origen__tipo_nodo')
        ]
        return {
            'entidad_tipo': 'NodoEstrategico',
            'entidad_id': str(nodo.pk),
            'codigo': nodo.codigo,
            'denominacion': nodo.nombre,
            'instrumento': {
                'id': str(version.instrumento.pk),
                'codigo': version.instrumento.codigo,
                'nombre': version.instrumento.nombre,
            },
            'version': cls._version_info(version),
            'vinculos_salientes': salientes,
            'vinculos_entrantes': entrantes,
        }

    @classmethod
    def _trazar_vinculo(cls, vinculo):
        version = vinculo.version
        return {
            'entidad_tipo': 'VinculoEstrategico',
            'entidad_id': str(vinculo.pk),
            'instrumento': {
                'id': str(version.instrumento.pk),
                'codigo': version.instrumento.codigo,
                'nombre': version.instrumento.nombre,
            },
            'version': cls._version_info(version),
            'tipo_vinculo': {
                'codigo': vinculo.tipo.codigo,
                'denominacion': vinculo.tipo.denominacion,
            },
            'origen': cls._nodo_info(vinculo.origen),
            'destino': cls._nodo_info(vinculo.destino),
            'ponderacion': (
                str(vinculo.ponderacion) if vinculo.ponderacion is not None else None
            ),
            'es_principal': vinculo.es_principal,
            'justificacion': vinculo.justificacion,
        }
