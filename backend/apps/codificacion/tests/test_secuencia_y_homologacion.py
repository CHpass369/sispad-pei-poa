"""Tests de SecuenciaCodigo y HomologacionCodigo (T2.2).

SecuenciaCodigo guarda el último correlativo emitido por clave
(nivel, padre_id, gestion, entidad) y está pensada para
``select_for_update()``: el CodificadorService (T3) la usa para emitir
correlativos sin duplicar bajo concurrencia.

HomologacionCodigo es el registro append-only de cambios de código
(ej. SIM-2027-OP-01 -> código oficial): ni update ni delete.
"""
import threading
import uuid
from queue import Empty, Queue

import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import (
    DatabaseError,
    IntegrityError,
    OperationalError,
    connection,
    transaction,
)
from django.db.models import ProtectedError

from apps.codificacion.models import (
    EntidadCodificadora,
    HomologacionCodigo,
    NIVEL_ARTICULACION_CHOICES,
    SecuenciaCodigo,
)

NIVELES_ESPERADOS = {
    'resultado_pad',
    'producto_pad',
    'resultado_pei',
    'producto_pei',
    'accion_poa',
    'operacion_poau',
    'actividad_poau',
    'tarea_poau',
}


@pytest.fixture
def entidad(db):
    """Entidad codificadora de prueba (la 1312 real la siembra la migración)."""
    return EntidadCodificadora.objects.create(
        codigo='9999', denominacion='Entidad de prueba',
    )


@pytest.fixture
def usuario(db):
    return get_user_model().objects.create_user(
        email='codificador@test.gob.bo', password='test123',
    )


class TestNivelesArticulacion:
    def test_choices_cubren_los_8_niveles(self):
        valores = {valor for valor, _ in NIVEL_ARTICULACION_CHOICES}
        assert valores == NIVELES_ESPERADOS


@pytest.mark.django_db
class TestSecuenciaCodigo:
    def test_ultimo_valor_default_cero(self, entidad):
        secuencia = SecuenciaCodigo.objects.create(
            nivel='operacion_poau', padre_id=uuid.uuid4(),
            gestion=2027, entidad=entidad,
        )
        assert secuencia.ultimo_valor == 0

    def test_clave_duplicada_rechazada(self, entidad):
        padre_id = uuid.uuid4()
        SecuenciaCodigo.objects.create(
            nivel='operacion_poau', padre_id=padre_id,
            gestion=2027, entidad=entidad,
        )
        with pytest.raises(IntegrityError):
            SecuenciaCodigo.objects.create(
                nivel='operacion_poau', padre_id=padre_id,
                gestion=2027, entidad=entidad,
            )

    def test_padre_null_tambien_es_unico(self, entidad):
        """Niveles raíz (sin padre): NULL no debe permitir duplicados."""
        SecuenciaCodigo.objects.create(
            nivel='resultado_pei', padre_id=None,
            gestion=2027, entidad=entidad,
        )
        with pytest.raises(IntegrityError):
            SecuenciaCodigo.objects.create(
                nivel='resultado_pei', padre_id=None,
                gestion=2027, entidad=entidad,
            )

    def test_misma_clave_en_distinta_gestion_es_valida(self, entidad):
        padre_id = uuid.uuid4()
        SecuenciaCodigo.objects.create(
            nivel='tarea_poau', padre_id=padre_id,
            gestion=2027, entidad=entidad,
        )
        otra = SecuenciaCodigo.objects.create(
            nivel='tarea_poau', padre_id=padre_id,
            gestion=2028, entidad=entidad,
        )
        assert otra.pk is not None

    def test_misma_clave_en_distinto_nivel_es_valida(self, entidad):
        padre_id = uuid.uuid4()
        SecuenciaCodigo.objects.create(
            nivel='actividad_poau', padre_id=padre_id,
            gestion=2027, entidad=entidad,
        )
        otra = SecuenciaCodigo.objects.create(
            nivel='operacion_poau', padre_id=padre_id,
            gestion=2027, entidad=entidad,
        )
        assert otra.pk is not None

    def test_admin_es_solo_lectura_y_no_permite_borrado(self):
        model_admin = admin.site._registry[SecuenciaCodigo]

        assert 'ultimo_valor' in model_admin.get_readonly_fields(request=None)
        assert model_admin.has_add_permission(request=None) is False
        assert model_admin.has_change_permission(request=None) is False
        assert model_admin.has_delete_permission(request=None) is False


@pytest.mark.django_db(transaction=True)
class TestSecuenciaCodigoConcurrencia:
    def test_select_for_update_bloquea_la_misma_fila_hasta_commit(self, entidad):
        """A holds the row lock, B times out, and a later transaction succeeds."""
        secuencia = SecuenciaCodigo.objects.create(
            nivel='operacion_poau', padre_id=uuid.uuid4(),
            gestion=2027, entidad=entidad,
        )

        inicio = threading.Barrier(2)
        lock_adquirido = threading.Event()
        liberar_lock = threading.Event()
        segundo_finalizo = threading.Event()
        errores_a = Queue()
        errores_b = Queue()

        def mantener_lock():
            try:
                inicio.wait(timeout=5)
                with transaction.atomic():
                    SecuenciaCodigo.objects.select_for_update().get(pk=secuencia.pk)
                    lock_adquirido.set()
                    if not liberar_lock.wait(timeout=5):
                        raise TimeoutError('No se liberó la transacción A.')
            except BaseException as exc:
                errores_a.put(exc)
            finally:
                connection.close()

        def intentar_mismo_lock():
            try:
                if not lock_adquirido.wait(timeout=5):
                    raise TimeoutError('La transacción A no obtuvo el lock.')
                with transaction.atomic():
                    with connection.cursor() as cursor:
                        cursor.execute("SET LOCAL lock_timeout = '250ms'")
                    SecuenciaCodigo.objects.select_for_update().get(pk=secuencia.pk)
            except BaseException as exc:
                errores_b.put(exc)
            finally:
                segundo_finalizo.set()
                connection.close()

        hilo_a = threading.Thread(target=mantener_lock)
        hilo_b = threading.Thread(target=intentar_mismo_lock)
        hilo_a.start()
        inicio.wait(timeout=5)
        assert lock_adquirido.wait(timeout=5)
        hilo_b.start()
        try:
            hilo_b.join(timeout=5)
            assert segundo_finalizo.is_set()
            assert not hilo_b.is_alive()
            try:
                error_b = errores_b.get_nowait()
            except Empty:
                error_b = None
            assert isinstance(error_b, OperationalError)
        finally:
            liberar_lock.set()
            hilo_a.join(timeout=5)

        assert not hilo_a.is_alive()
        assert errores_a.empty()

        with transaction.atomic():
            desbloqueada = SecuenciaCodigo.objects.select_for_update().get(
                pk=secuencia.pk,
            )
            desbloqueada.ultimo_valor = 1
            desbloqueada.save(update_fields=['ultimo_valor', 'updated_at'])

        secuencia.refresh_from_db()
        assert secuencia.ultimo_valor == 1

    def test_carrera_de_creacion_inicial_queda_para_t3(self):
        pytest.xfail(
            'La creación concurrente de SecuenciaCodigo pertenece a '
            'CodificadorService (T3); T2 solo garantiza filas preexistentes.'
        )


@pytest.mark.django_db
class TestHomologacionCodigo:
    def _crear(self, usuario, **kwargs):
        datos = {
            'tipo_entidad': 'operacion_poau',
            'entidad_id': uuid.uuid4(),
            'codigo_anterior': 'SIM-2027-OP-01',
            'codigo_nuevo': '04.02.14.01.031001.02.01.01.1312.03.01.01.001.001',
            'motivo': 'Homologación inicial SIM-2027',
            'gestion': 2027,
            'usuario': usuario,
            'documento_respaldo': 'Resolución 001/2027',
        }
        datos.update(kwargs)
        return HomologacionCodigo.objects.create(**datos)

    def test_creacion_registra_fecha_automatica(self, usuario):
        homologacion = self._crear(usuario)
        assert homologacion.fecha is not None

    def test_documento_respaldo_opcional(self, usuario):
        homologacion = self._crear(usuario, documento_respaldo='')
        assert homologacion.pk is not None

    def test_append_only_bloquea_update(self, usuario):
        homologacion = self._crear(usuario)
        homologacion.motivo = 'Motivo alterado'
        with pytest.raises(ValidationError):
            homologacion.save()

    def test_append_only_bloquea_delete(self, usuario):
        homologacion = self._crear(usuario)
        with pytest.raises(ValidationError):
            homologacion.delete()
        assert HomologacionCodigo.objects.filter(pk=homologacion.pk).exists()

    def test_append_only_bloquea_queryset_update(self, usuario):
        homologacion = self._crear(usuario)

        with pytest.raises(ValidationError):
            HomologacionCodigo.objects.filter(pk=homologacion.pk).update(
                motivo='Alterado por QuerySet',
            )

        homologacion.refresh_from_db()
        assert homologacion.motivo == 'Homologación inicial SIM-2027'

    def test_append_only_bloquea_queryset_delete(self, usuario):
        homologacion = self._crear(usuario)

        with pytest.raises(ValidationError):
            HomologacionCodigo.objects.filter(pk=homologacion.pk).delete()

        assert HomologacionCodigo.objects.filter(pk=homologacion.pk).exists()

    def test_append_only_bloquea_bulk_update(self, usuario):
        homologacion = self._crear(usuario)
        homologacion.motivo = 'Alterado por bulk_update'

        with pytest.raises(ValidationError):
            HomologacionCodigo.objects.bulk_update([homologacion], ['motivo'])

        homologacion.refresh_from_db()
        assert homologacion.motivo == 'Homologación inicial SIM-2027'

    def test_append_only_permite_multiples_insert(self, usuario):
        primera = self._crear(usuario)
        segunda = self._crear(
            usuario,
            codigo_anterior='SIM-2027-OP-02',
            motivo='Otra homologación',
        )
        assert HomologacionCodigo.objects.count() == 2
        assert primera.pk != segunda.pk

    def test_usuario_protegido_contra_borrado(self, usuario):
        self._crear(usuario)
        with pytest.raises(ProtectedError):
            usuario.delete()

    def test_indices_requeridos(self):
        compuestos = {tuple(indice.fields) for indice in HomologacionCodigo._meta.indexes}
        assert ('tipo_entidad', 'codigo_anterior') in compuestos
        assert ('entidad_id',) in compuestos


@pytest.mark.django_db(transaction=True)
class TestHomologacionCodigoTriggerPostgreSQL:
    def test_sql_directo_bloquea_update_y_delete(self, usuario):
        homologacion = HomologacionCodigo.objects.create(
            tipo_entidad='operacion_poau',
            entidad_id=uuid.uuid4(),
            codigo_anterior='SIM-2027-OP-SQL',
            codigo_nuevo='04.02.14.01.031001.02.01.01.1312.03.01.01.001',
            motivo='Homologación protegida por trigger',
            gestion=2027,
            usuario=usuario,
        )

        with pytest.raises(DatabaseError):
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute(
                        'UPDATE codificacion_homologacioncodigo '
                        'SET motivo = %s WHERE id = %s',
                        ['Alteración SQL', homologacion.pk],
                    )

        with pytest.raises(DatabaseError):
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute(
                        'DELETE FROM codificacion_homologacioncodigo '
                        'WHERE id = %s',
                        [homologacion.pk],
                    )

        homologacion.refresh_from_db()
        assert homologacion.motivo == 'Homologación protegida por trigger'
