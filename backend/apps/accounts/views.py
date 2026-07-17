import logging
import secrets
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .models import Rol
from .serializers import UsuarioSerializer, RolSerializer

logger = logging.getLogger(__name__)
Usuario = get_user_model()


class LoginThrottle(AnonRateThrottle):
    rate = '5/minute'


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

        if not (request.user.is_superuser or request.user.pk == user.pk):
            return Response(
                {'error': 'No tiene permiso para cambiar la contraseña de este usuario'},
                status=status.HTTP_403_FORBIDDEN,
            )

        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not old_password:
            return Response(
                {'error': 'La contraseña actual es obligatoria'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not new_password:
            return Response(
                {'error': 'La nueva contraseña es obligatoria'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user.check_password(old_password):
            return Response(
                {'error': 'La contraseña actual es incorrecta'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_password(new_password, user=user)
        except DjangoValidationError as e:
            return Response(
                {'error': 'La nueva contraseña no cumple los requisitos de seguridad',
                 'detalles': e.messages},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.debe_cambiar_password = False
        user.save()
        logger.info(f'Contraseña cambiada para usuario {user.email}')
        return Response({'detail': 'Contraseña actualizada correctamente'})


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'error': 'El token de refresco es requerido'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response(
                {'error': 'Token inválido o ya expirado'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({'detail': 'Sesión cerrada correctamente'})


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [LoginThrottle]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response(
                {'error': 'El email es obligatorio'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = Usuario.objects.get(email=email, activo=True)
        except Usuario.DoesNotExist:
            return Response(
                {'detail': 'Si el email existe, recibirá instrucciones para restablecer su contraseña'},
                status=status.HTTP_200_OK,
            )

        token = secrets.token_urlsafe(48)
        user.set_password(token)
        user.save()

        token_for_reset = RefreshToken.for_user(user)
        reset_token = str(token_for_reset.access)

        user.set_password(token)
        user.save()

        try:
            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:4200')
            reset_url = f'{frontend_url}/auth/reset-password?token={reset_token}'
            send_mail(
                subject='Restablecimiento de contraseña - SISPOA',
                message=(
                    f'Estimado/a {user.get_full_name() or user.email}:\n\n'
                    f'Recibimos una solicitud para restablecer su contraseña.\n\n'
                    f'Su token de restablecimiento es: {reset_token}\n\n'
                    f'O puede usar el siguiente enlace:\n{reset_url}\n\n'
                    f'Si no solicitó este cambio, ignore este mensaje.\n\n'
                    f'El token expirará en 24 horas.'
                ),
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@sacaba.gob.bo'),
                recipient_list=[user.email],
                fail_silently=True,
            )
        except Exception as e:
            logger.error(f'Error enviando email de reset para {email}: {e}')

        return Response(
            {'detail': 'Si el email existe, recibirá instrucciones para restablecer su contraseña'},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [LoginThrottle]

    def post(self, request):
        token = request.data.get('token')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        if not token or not new_password or not confirm_password:
            return Response(
                {'error': 'Token, nueva contraseña y confirmación son requeridos'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if new_password != confirm_password:
            return Response(
                {'error': 'Las contraseñas no coinciden'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            from rest_framework_simplejwt.tokens import AccessToken
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            user = Usuario.objects.get(pk=user_id, activo=True)
        except Exception:
            return Response(
                {'error': 'Token inválido o expirado'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_password(new_password, user=user)
        except DjangoValidationError as e:
            return Response(
                {'error': 'La contraseña no cumple los requisitos de seguridad',
                 'detalles': e.messages},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.debe_cambiar_password = False
        user.save()
        logger.info(f'Contraseña restablecida para usuario {user.email}')
        return Response({'detail': 'Contraseña restablecida correctamente'})


class LoginAttemptViewSet(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        email = request.query_params.get('email', '')
        if not email:
            return Response(
                {'error': 'El parámetro email es requerido'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = Usuario.objects.get(email=email)
            locked_until = getattr(user, 'locked_until', None)
            failed_attempts = getattr(user, 'failed_login_attempts', 0)
            is_locked = False
            if locked_until and locked_until > timezone.now():
                is_locked = True
        except Usuario.DoesNotExist:
            failed_attempts = 0
            is_locked = False

        return Response({
            'is_locked': is_locked,
            'failed_attempts': failed_attempts,
        })
