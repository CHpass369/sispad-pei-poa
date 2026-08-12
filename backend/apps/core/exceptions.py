from rest_framework.views import exception_handler


class DomainError(Exception):
    """Error de dominio del núcleo presupuestario (S2+).

    Se usa para violaciones de invariantes que no deben expresarse como
    ValidationError de formulario: por ejemplo la inmutabilidad del
    ledger (MovimientoPresupuestario no admite update/delete, C7).
    """


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        response.data = {
            'error': response.data,
            'status_code': response.status_code,
        }
    return response
