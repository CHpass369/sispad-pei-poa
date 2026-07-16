from rest_framework import serializers
from .models import DocumentoAdjunto


class DocumentoAdjuntoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentoAdjunto
        fields = '__all__'
        read_only_fields = ['hash_sha256', 'tamanio_bytes']
