from decimal import Decimal


class UmbralesConfiguracion:
    VERDE = 80
    AMARILLO = 50
    ROJO = 0

    @classmethod
    def porcentaje_verde(cls):
        return cls.VERDE

    @classmethod
    def porcentaje_amarillo(cls):
        return cls.AMARILLO

    @classmethod
    def rango_verde(cls):
        return range(cls.VERDE, 101)

    @classmethod
    def rango_amarillo(cls):
        return range(cls.AMARILLO, cls.VERDE)

    @classmethod
    def rango_rojo(cls):
        return range(cls.ROJO, cls.AMARILLO)


def determinar_semaforo(porcentaje):
    porcentaje = Decimal(str(porcentaje))
    if porcentaje >= Decimal('80'):
        return 'verde'
    elif porcentaje >= Decimal('50'):
        return 'amarillo'
    else:
        return 'rojo'


def verificar_ejecucion_fisica_baja(entry):
    avance_fisico = getattr(entry, 'avance_fisico', None)
    if avance_fisico is None:
        return None
    porcentaje = Decimal(str(avance_fisico))
    semaforo = determinar_semaforo(porcentaje)
    if semaforo == 'rojo':
        return {
            'tipo': 'ejecucion_fisica_baja',
            'semaforo': semaforo,
            'mensaje': f'Ejecución física baja: {porcentaje}%',
            'valor': porcentaje,
            'entrada': entry,
        }
    return None


def verificar_ejecucion_financiera_baja(entry):
    avance_financiero = getattr(entry, 'avance_financiero', None)
    if avance_financiero is None:
        return None
    porcentaje = Decimal(str(avance_financiero))
    semaforo = determinar_semaforo(porcentaje)
    if semaforo == 'rojo':
        return {
            'tipo': 'ejecucion_financiera_baja',
            'semaforo': semaforo,
            'mensaje': f'Ejecución financiera baja: {porcentaje}%',
            'valor': porcentaje,
            'entrada': entry,
        }
    return None


def verificar_avance_sin_financiera(entry):
    avance_fisico = getattr(entry, 'avance_fisico', None)
    avance_financiero = getattr(entry, 'avance_financiero', None)
    if (avance_fisico is not None and avance_financiero is not None
            and Decimal(str(avance_fisico)) > Decimal('0')
            and Decimal(str(avance_financiero)) == Decimal('0')):
        return {
            'tipo': 'avance_sin_financiera',
            'semaforo': 'amarillo',
            'mensaje': f'Hay avance físico ({avance_fisico}%) pero sin ejecución financiera.',
            'valor': avance_fisico,
            'entrada': entry,
        }
    return None


def verificar_financiera_sin_avance(entry):
    avance_fisico = getattr(entry, 'avance_fisico', None)
    avance_financiero = getattr(entry, 'avance_financiero', None)
    if (avance_financiero is not None and avance_fisico is not None
            and Decimal(str(avance_financiero)) > Decimal('0')
            and Decimal(str(avance_fisico)) == Decimal('0')):
        return {
            'tipo': 'financiera_sin_avance',
            'semaforo': 'amarillo',
            'mensaje': f'Hay ejecución financiera ({avance_financiero}%) pero sin avance físico.',
            'valor': avance_financiero,
            'entrada': entry,
        }
    return None


def verificar_sobreejecucion(entry):
    avance_fisico = getattr(entry, 'avance_fisico', None)
    avance_financiero = getattr(entry, 'avance_financiero', None)
    alertas = []

    if avance_fisico is not None and Decimal(str(avance_fisico)) > Decimal('100'):
        alertas.append({
            'tipo': 'sobreejecucion_fisica',
            'semaforo': 'rojo',
            'mensaje': f'Sobreejecución física detectada: {avance_fisico}%',
            'valor': avance_fisico,
            'entrada': entry,
        })

    if avance_financiero is not None and Decimal(str(avance_financiero)) > Decimal('100'):
        alertas.append({
            'tipo': 'sobreejecucion_financiera',
            'semaforo': 'rojo',
            'mensaje': f'Sobreejecución financiera detectada: {avance_financiero}%',
            'valor': avance_financiero,
            'entrada': entry,
        })

    return alertas if alertas else None


def verificar_meta_vencida(entry):
    fecha_fin = getattr(entry, 'fecha_fin', None)
    if fecha_fin is None:
        return None
    from datetime import date
    hoy = date.today()
    if fecha_fin < hoy:
        avance = getattr(entry, 'avance_fisico', None)
        if avance is None or Decimal(str(avance)) < Decimal('100'):
            return {
                'tipo': 'meta_vencida',
                'semaforo': 'rojo',
                'mensaje': f'La meta venció el {fecha_fin} y no se cumplió al 100%.',
                'valor': avance,
                'entrada': entry,
            }
    return None


def verificar_sin_evidencia(entry):
    evidencias = getattr(entry, 'evidencias', None)
    if evidencias is not None and hasattr(evidencias, 'count'):
        if evidencias.count() == 0:
            return {
                'tipo': 'sin_evidencia',
                'semaforo': 'amarillo',
                'mensaje': 'No se ha registrado evidencia documental para esta entrada.',
                'valor': None,
                'entrada': entry,
            }
    return None


def generar_alertas_por_entrada(entry):
    alertas = []
    verificadores = [
        verificar_ejecucion_fisica_baja,
        verificar_ejecucion_financiera_baja,
        verificar_avance_sin_financiera,
        verificar_financiera_sin_avance,
        verificar_sobreejecucion,
        verificar_meta_vencida,
        verificar_sin_evidencia,
    ]

    for verificador in verificadores:
        resultado = verificador(entry)
        if resultado is None:
            continue
        if isinstance(resultado, list):
            alertas.extend(resultado)
        else:
            alertas.append(resultado)

    return alertas
