from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .models import Rol
from .serializers import UsuarioSerializer, RolSerializer

Usuario = get_user_model()


class RolViewSet(viewsets.ModelViewSet):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    search_fields = ['codigo', 'nombre']
    ordering_fields = ['orden', 'nombre']


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    search_fields = ['email', 'first_name', 'last_name', 'cargo']
    ordering_fields = ['email', 'last_name', 'first_name']

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cambiar_password(self, request, pk=None):
        user = self.get_object()
        password = request.data.get('password')
        if not password:
            return Response({'error': 'La contraseña es obligatoria'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(password)
        user.debe_cambiar_password = False
        user.save()
        return Response({'detail': 'Contraseña actualizada correctamente'})
