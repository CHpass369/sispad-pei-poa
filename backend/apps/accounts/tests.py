from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import SimpleTestCase, TestCase
from django.urls import resolve, reverse

from rest_framework import status
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.test import APIRequestFactory

from .models import Usuario
from .views import LoginThrottle, LoginView


class LoginThrottleTests(SimpleTestCase):
    def setUp(self):
        # El cache compartido puede conservar intentos de otras pruebas.
        SimpleRateThrottle.cache.clear()
        self.factory = APIRequestFactory()
        self.login_url = reverse('login')

    def test_login_aplica_login_throttle_y_limita_el_sexto_intento(self):
        resolved = resolve(self.login_url)
        self.assertIs(resolved.func.view_class, LoginView)
        self.assertEqual(LoginView.throttle_classes, [LoginThrottle])
        self.assertEqual(LoginThrottle.scope, 'login')

        view = LoginView()
        throttle = view.get_throttles()[0]
        requests = [
            view.initialize_request(
                self.factory.post(self.login_url, {}, REMOTE_ADDR='192.0.2.10')
            )
            for _ in range(6)
        ]
        allowed = [throttle.allow_request(request, view) for request in requests]

        self.assertEqual(allowed[:5], [True] * 5)
        self.assertFalse(allowed[5])


class PasswordResetFlowTests(TestCase):
    """Flujo de restablecimiento de contraseña (PasswordResetRequest/Confirm).

    Regresiones cubiertas:
    - El request NO debe alterar la contraseña del usuario (bug: set_password
      con token aleatorio rompía la cuenta si el reset no se completaba).
    - El email no debe contener un bearer token de sesión (JWT), sino un
      token de un solo uso.
    - El token deja de ser válido una vez usada la nueva contraseña.
    """

    def setUp(self):
        # El throttle LoginThrottle define rate propio (5/min); se limpia el
        # cache entre tests para no bloquear por IP compartida (127.0.0.1).
        from rest_framework.throttling import SimpleRateThrottle
        SimpleRateThrottle.cache.clear()
        self.user = Usuario.objects.create_user(
            email='ana@sacaba.gob.bo',
            password='ClaveSegura-2026',
            first_name='Ana',
            activo=True,
        )
        self.request_url = reverse('password_reset')
        self.confirm_url = reverse('password_reset_confirm')

    def _request_reset(self, email):
        return self.client.post(self.request_url, {'email': email})

    def _extract_reset_token(self):
        """Saca el token del enlace del último email enviado."""
        self.assertEqual(len(mail.outbox), 1)
        body = mail.outbox[0].body
        line = next(l for l in body.splitlines() if 'auth/reset-password' in l)
        query = line.split('?', 1)[1]
        params = dict(p.split('=', 1) for p in query.split('&'))
        return params

    def test_request_requiere_email(self):
        resp = self.client.post(self.request_url, {})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_request_email_inexistente_responde_generico_sin_email(self):
        resp = self._request_reset('nadie@sacaba.gob.bo')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('Si el email existe', resp.data['detail'])
        self.assertEqual(len(mail.outbox), 0)

    def test_request_no_altera_la_contrasena_del_usuario(self):
        """Regresión del bug: set_password doble con token aleatorio."""
        resp = self._request_reset(self.user.email)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('ClaveSegura-2026'))
        self.assertFalse(self.user.check_password('s3crets-token-no-debe-activarse'))

    def test_request_envia_email_con_token_de_un_solo_uso(self):
        resp = self._request_reset(self.user.email)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        params = self._extract_reset_token()
        self.assertIn('token', params)
        self.assertIn('email', params)
        self.assertEqual(params['email'], self.user.email)
        # El token debe ser un token de reset válido, NO un JWT de sesión.
        self.assertNotIn('.', params['token'])
        self.assertTrue(default_token_generator.check_token(self.user, params['token']))

    def test_confirm_cambia_contrasena_con_token_valido(self):
        self._request_reset(self.user.email)
        token = self._extract_reset_token()['token']
        resp = self.client.post(self.confirm_url, {
            'email': self.user.email,
            'token': token,
            'new_password': 'NuevaClave-2026!',
            'confirm_password': 'NuevaClave-2026!',
        })
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NuevaClave-2026!'))
        self.assertFalse(self.user.debe_cambiar_password)

    def test_confirm_rechaza_token_invalido_sin_cambiar_contrasena(self):
        self._request_reset(self.user.email)
        resp = self.client.post(self.confirm_url, {
            'email': self.user.email,
            'token': 'token-falso',
            'new_password': 'NuevaClave-2026!',
            'confirm_password': 'NuevaClave-2026!',
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('ClaveSegura-2026'))

    def test_confirm_rechaza_contrasenas_distintas(self):
        self._request_reset(self.user.email)
        token = self._extract_reset_token()['token']
        resp = self.client.post(self.confirm_url, {
            'email': self.user.email,
            'token': token,
            'new_password': 'NuevaClave-2026!',
            'confirm_password': 'OtraClave-2026!',
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('ClaveSegura-2026'))

    def test_token_no_reutilizable_despues_del_reset(self):
        self._request_reset(self.user.email)
        token = self._extract_reset_token()['token']
        self.client.post(self.confirm_url, {
            'email': self.user.email,
            'token': token,
            'new_password': 'NuevaClave-2026!',
            'confirm_password': 'NuevaClave-2026!',
        })
        # El mismo token ya no debe funcionar (el hash incluye la contraseña).
        resp = self.client.post(self.confirm_url, {
            'email': self.user.email,
            'token': token,
            'new_password': 'OtraClave-2026!',
            'confirm_password': 'OtraClave-2026!',
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NuevaClave-2026!'))
