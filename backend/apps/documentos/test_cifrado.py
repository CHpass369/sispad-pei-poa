"""Cifrado y recuperación de documentos."""
import base64
import os

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings

from apps.documentos.cifrado import (
    DocumentoAlterado, cifrar, clave, descifrar, huella,
)

CLAVE = base64.b64encode(os.urandom(32)).decode()
OTRA = base64.b64encode(os.urandom(32)).decode()


@override_settings(DOCUMENTOS_CLAVE=CLAVE)
class CifradoTests(TestCase):
    def test_ida_y_vuelta(self):
        nonce, cifrado = cifrar(b'%PDF-1.4 acta')
        self.assertEqual(descifrar(nonce, cifrado), b'%PDF-1.4 acta')

    def test_el_cifrado_no_deja_ver_el_documento(self):
        _, cifrado = cifrar(b'%PDF-1.4 acta de priorizacion')
        self.assertNotIn(b'priorizacion', bytes(cifrado))
        self.assertNotIn(b'%PDF', bytes(cifrado))

    def test_dos_cifrados_del_mismo_documento_son_distintos(self):
        # Nonce aleatorio: si no, se vería que dos actas son idénticas.
        primero = cifrar(b'igual')[1]
        segundo = cifrar(b'igual')[1]
        self.assertNotEqual(bytes(primero), bytes(segundo))

    def test_tocar_un_byte_hace_fallar_el_descifrado(self):
        nonce, cifrado = cifrar(b'%PDF-1.4 acta')
        alterado = bytearray(cifrado)
        alterado[0] ^= 1
        # GCM autentica: no devuelve basura, falla.
        with self.assertRaises(DocumentoAlterado):
            descifrar(nonce, bytes(alterado))

    def test_el_contexto_impide_mover_el_documento_de_dueño(self):
        nonce, cifrado = cifrar(b'acta', b'acta:111')
        self.assertEqual(descifrar(nonce, cifrado, b'acta:111'), b'acta')
        with self.assertRaises(DocumentoAlterado):
            descifrar(nonce, cifrado, b'acta:222')

    def test_con_otra_clave_no_se_abre(self):
        nonce, cifrado = cifrar(b'acta')
        with override_settings(DOCUMENTOS_CLAVE=OTRA):
            with self.assertRaises(DocumentoAlterado):
                descifrar(nonce, cifrado)

    def test_la_huella_es_del_documento_en_claro(self):
        import hashlib
        self.assertEqual(huella(b'acta'), hashlib.sha256(b'acta').hexdigest())


class ClaveTests(TestCase):
    @override_settings(DOCUMENTOS_CLAVE='')
    def test_sin_clave_configurada_lo_dice(self):
        with self.assertRaises(ImproperlyConfigured) as e:
            clave()
        self.assertIn('DOCUMENTOS_CLAVE', str(e.exception))

    @override_settings(DOCUMENTOS_CLAVE='no-es-base64!!')
    def test_una_clave_ilegible_lo_dice(self):
        with self.assertRaises(ImproperlyConfigured):
            clave()

    @override_settings(DOCUMENTOS_CLAVE=base64.b64encode(b'corta').decode())
    def test_una_clave_de_largo_equivocado_lo_dice(self):
        with self.assertRaises(ImproperlyConfigured) as e:
            clave()
        self.assertIn('32 bytes', str(e.exception))
