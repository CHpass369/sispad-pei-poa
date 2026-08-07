"""Tests de registro de la app codificacion (T1.1)."""
from django.apps import apps
from django.test import SimpleTestCase


class CodificacionAppTest(SimpleTestCase):
    def test_app_esta_instalada(self):
        """La app codificacion debe estar registrada en INSTALLED_APPS."""
        self.assertTrue(apps.is_installed('apps.codificacion'))

    def test_app_config(self):
        """El AppConfig expone nombre y verbose_name en español."""
        config = apps.get_app_config('codificacion')
        self.assertEqual(config.name, 'apps.codificacion')
        self.assertEqual(config.verbose_name, 'Codificación oficial PAD-PEI-POA-POAU')
