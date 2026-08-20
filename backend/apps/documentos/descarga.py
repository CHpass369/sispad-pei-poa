"""Descarga de documentos cifrados.

Los bytes solo salen por acá: no hay una URL de archivo que un servidor web mal
configurado pueda servir por su cuenta.
"""
from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .almacen import leer
from .cifrado import DocumentoAlterado
from .models import DocumentoAdjunto


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def descargar_documento(request, documento_id):
    documento = DocumentoAdjunto.objects.filter(
        id=documento_id, activo=True).first()
    if documento is None:
        return Response({'error': 'El documento no existe.'},
                        status=status.HTTP_404_NOT_FOUND)
    try:
        contenido = leer(documento)
    except FileNotFoundError:
        return Response({'error': 'El documento no tiene contenido guardado.'},
                        status=status.HTTP_404_NOT_FOUND)
    except DocumentoAlterado as error:
        # No se devuelve el contenido dudoso: se avisa.
        return Response({'error': str(error)},
                        status=status.HTTP_409_CONFLICT)

    respuesta = HttpResponse(contenido, content_type=documento.content_type)
    respuesta['Content-Disposition'] = f'attachment; filename="{documento.nombre}"'
    respuesta['X-Documento-Huella'] = documento.hash_sha256
    return respuesta
