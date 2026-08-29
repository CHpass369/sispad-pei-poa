import logging
from decimal import Decimal

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


logger = logging.getLogger(__name__)


SPREADSHEET_ID = "14v9Ln4ZabplMqMA0ZzOtbLRuycZZ7kgnocvjzW4AAcU"

# OJO: la pestaña tiene un espacio al principio.
SHEET_NAME = " BASE DE DATOS FICHAS 2026"

CREDENTIALS_FILE = "/srv/pip-gams/secrets/google-sheets.json"

START_ROW = 7

# Columna técnica para relacionar PIP con Google Sheets.
ID_COLUMN = "BB"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]


def _service():
    credentials = Credentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=SCOPES,
    )

    return build(
        "sheets",
        "v4",
        credentials=credentials,
        cache_discovery=False,
    )


def _clave_proyecto(proyecto):
    """
    Identificador estable.

    No usamos ProyectoPriorizado.id porque el serializer borra y recrea
    los proyectos cada vez que se modifica la lista del acta.
    """
    return f"{proyecto.acta_id}-{proyecto.orden:02d}"


def _separar_categoria(proyecto):
    """
    Ejemplo:
    180 08620281200000 000

    programa  = 180
    sisin     = 08620281200000
    actividad = 000
    """
    partes = (proyecto.categoria_programatica or "").strip().split()

    programa = partes[0] if len(partes) >= 1 else ""
    sisin_categoria = partes[1] if len(partes) >= 2 else ""
    actividad = partes[2] if len(partes) >= 3 else ""

    # Si el proyecto tiene SISIN explícito, tiene prioridad.
    sisin = (proyecto.sisin or "").strip() or sisin_categoria

    return programa, sisin, actividad


def _valor_decimal(valor):
    if valor is None:
        return ""

    if isinstance(valor, Decimal):
        return float(valor)

    return valor


def _buscar_filas_por_clave(service):
    resultado = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"'{SHEET_NAME}'!{ID_COLUMN}{START_ROW}:{ID_COLUMN}",
    ).execute()

    filas = {}

    for numero_fila, row in enumerate(
        resultado.get("values", []),
        start=START_ROW,
    ):
        if row and row[0]:
            filas[str(row[0]).strip()] = numero_fila

    return filas


def _buscar_primera_fila_libre(service):
    """
    Consideramos libre una fila cuando B, G y BB están vacías.
    """
    resultado = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"'{SHEET_NAME}'!B{START_ROW}:BB",
    ).execute()

    values = resultado.get("values", [])

    for offset, row in enumerate(values):
        fila = START_ROW + offset

        # B está en índice 0 dentro de B:BB
        b = row[0] if len(row) > 0 else ""

        # G está 5 columnas después de B.
        g = row[5] if len(row) > 5 else ""

        # BB dentro de B:BB es índice 52.
        bb = row[52] if len(row) > 52 else ""

        if not b and not g and not bb:
            return fila

    return START_ROW + len(values)


def _escribir_proyecto(service, proyecto, fila):
    programa, sisin, actividad = _separar_categoria(proyecto)

    clave = _clave_proyecto(proyecto)

    # Distrito asociado al acta.
    # Usamos el código; si no existe, usamos el nombre.
    distrito = ""

    if proyecto.acta.distrito:
        distrito = (
            getattr(proyecto.acta.distrito, "codigo", "")
            or getattr(proyecto.acta.distrito, "nombre", "")
            or ""
        )

    datos = [
        {
            "range": f"'{SHEET_NAME}'!B{fila}:E{fila}",
            "values": [[
                programa,
                sisin,
                actividad,
                proyecto.categoria_programatica or "",
            ]],
        },
        {
            "range": f"'{SHEET_NAME}'!G{fila}:H{fila}",
            "values": [[
                proyecto.nombre,
                _valor_decimal(proyecto.monto),
            ]],
        },
        {
            "range": f"'{SHEET_NAME}'!J{fila}",
            "values": [[
                distrito,
            ]],
        },
        {
            "range": f"'{SHEET_NAME}'!{ID_COLUMN}{fila}",
            "values": [[
                clave,
            ]],
        },
    ]

    service.spreadsheets().values().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body={
            "valueInputOption": "USER_ENTERED",
            "data": datos,
        },
    ).execute()


def _limpiar_proyecto(service, fila):
    """
    Limpia solamente las columnas administradas por PIP.

    No elimina físicamente la fila de Google Sheets.
    Tampoco toca otras columnas que puedan contener información
    manual, fórmulas u otros datos externos al PIP.

    Columnas controladas por PIP:
    B  -> PROG.
    C  -> CODIGO SISIN WEB
    D  -> ACT.
    E  -> CATEGORIA PROGRAMATICA
    G  -> NOMBRE DEL PROYECTO
    H  -> PRESUPUESTO
    J  -> DISTRITO
    BB -> IDENTIFICADOR TECNICO PIP
    """

    service.spreadsheets().values().batchClear(
        spreadsheetId=SPREADSHEET_ID,
        body={
            "ranges": [
                f"'{SHEET_NAME}'!B{fila}:E{fila}",
                f"'{SHEET_NAME}'!G{fila}:H{fila}",
                f"'{SHEET_NAME}'!J{fila}",
                f"'{SHEET_NAME}'!{ID_COLUMN}{fila}",
            ],
        },
    ).execute()


def sincronizar_acta_google(acta_id):
    """
    Sincroniza todos los proyectos actuales del acta.

    También elimina de Sheets aquellos proyectos que existían antes pero
    fueron quitados al editar el acta.
    """
    from apps.priorizacion.models import ActaPriorizacion

    try:
        acta = (
            ActaPriorizacion.objects
            .prefetch_related("proyectos")
            .get(pk=acta_id)
        )

        service = _service()

        filas_existentes = _buscar_filas_por_clave(service)

        prefijo = f"{acta.id}-"

        # Claves que actualmente pertenecen al acta en Google Sheets.
        claves_anteriores = {
            clave: fila
            for clave, fila in filas_existentes.items()
            if clave.startswith(prefijo)
        }

        claves_actuales = set()

        for proyecto in acta.proyectos.all().order_by("orden"):
            clave = _clave_proyecto(proyecto)
            claves_actuales.add(clave)

            fila = filas_existentes.get(clave)

            if fila is None:
                fila = _buscar_primera_fila_libre(service)

            _escribir_proyecto(service, proyecto, fila)

            # Para evitar reutilizar la misma fila dentro de esta ejecución.
            filas_existentes[clave] = fila

        # Si antes había proyecto 06 y ahora el acta solo tiene 5,
        # limpiamos únicamente las columnas gestionadas por PIP.
        eliminadas = set(claves_anteriores) - claves_actuales

        for clave in eliminadas:
            _limpiar_proyecto(
                service,
                claves_anteriores[clave],
            )

        logger.info(
            "Acta %s sincronizada con Google Sheets: %s proyectos",
            acta.id,
            len(claves_actuales),
        )

        return True

    except Exception:
        # Google jamás debe impedir que el usuario guarde en PIP.
        logger.exception(
            "Error sincronizando acta %s con Google Sheets",
            acta_id,
        )
        return False
def eliminar_acta_google(acta_id):
    """
    Limpia de Google Sheets todos los proyectos relacionados
    con un acta que fue eliminada del PIP.

    IMPORTANTE:
    - No elimina filas completas.
    - Solo limpia las columnas administradas por PIP.
    - Usa como referencia el identificador técnico guardado en BB.

    Ejemplo de BB:
        54b96cc8-aeaf-4af8-8c71-64eef5a34170-01
        54b96cc8-aeaf-4af8-8c71-64eef5a34170-02

    Si se elimina el acta:
        54b96cc8-aeaf-4af8-8c71-64eef5a34170

    se localizarán todas las filas cuyo BB comience con ese UUID.
    """

    try:
        service = _service()

        filas_existentes = _buscar_filas_por_clave(
            service
        )

        prefijo = f"{acta_id}-"

        filas_acta = []

        for clave, fila in filas_existentes.items():
            if clave.startswith(prefijo):
                filas_acta.append(fila)

        for fila in filas_acta:
            _limpiar_proyecto(
                service,
                fila,
            )

        logger.info(
            "Acta %s eliminada de Google Sheets. "
            "%s filas limpiadas.",
            acta_id,
            len(filas_acta),
        )

        return True

    except Exception:
        logger.exception(
            "Error eliminando el acta %s de Google Sheets",
            acta_id,
        )

        return False
