"""Quién administra los techos por unidad y categoría, y qué impide duplicarlos.

El monto que el asistente de recursos ofrece para programar vivía en un arreglo
estático del bundle de Angular. Moverlo a la base abre dos riesgos nuevos que
estos casos fijan:

- **la escritura tiene que ser de administrador y solo de administrador.** Leer
  el techo lo necesita cualquiera que programe; decidirlo, no. Un usuario con
  las capacidades `sis_poa.poau.*` completas y alcance global sigue recibiendo
  403 al escribir;
- **el par (unidad, categoría, fuente, organismo) no puede repetirse.** Dos
  filas para el mismo par duplican el techo declarado del municipio, que es
  exactamente el error que se evitó a mano siete veces en el catálogo estático.
  Con fuente y organismo nulos —el estado de las 175 filas heredadas— PostgreSQL
  trata cada NULL como distinto y la restricción deja de morder: por eso va con
  `nulls_distinct=False`, y por eso hay un caso que lo prueba con nulos.
"""
from decimal import Decimal

from django.db import IntegrityError, transaction
from rest_framework import status

from apps.accounts.models import Usuario
from apps.articulacion.models import SaldoUnidadCategoria

from .test_scope_poau_unidad import ScopePOAUUnidadBase

SALDOS = '/api/v1/articulacion/saldos-unidad-categoria/'


class SaldosUnidadCategoriaBase(ScopePOAUUnidadBase):
    """Añade un administrador y un techo ya cargado sobre la unidad propia."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.admin = Usuario.objects.create_superuser(
            email='admin-saldos@test.gob.bo', password='Clave.Saldos.2027',
        )
        cls.saldo_propia = SaldoUnidadCategoria.objects.create(
            unidad=cls.propia, categoria_programatica='210 0 042',
            denominacion='SERVICIOS DE SISTEMAS INFORMATICOS',
            saldo=Decimal('2900000.00'), filas_origen=1,
        )
        cls.saldo_ajena = SaldoUnidadCategoria.objects.create(
            unidad=cls.ajena, categoria_programatica='331 0 022',
            denominacion='SEGURIDAD CIUDADANA',
            saldo=Decimal('150000.00'), filas_origen=1,
        )


class EscrituraSoloAdministradorTests(SaldosUnidadCategoriaBase):
    """A. El candado: leer con capacidad, escribir solo administrador."""

    def _cuerpo(self, **extra):
        cuerpo = {
            'unidad': str(self.propia.id),
            'categoria_programatica': '251 0 013',
            'denominacion': 'CENTRO DE ACOGIDA',
            'saldo': '60000.00',
            'filas_origen': 0,
        }
        cuerpo.update(extra)
        return cuerpo

    def test_usuario_con_capacidad_poau_puede_leer(self):
        respuesta = self.cliente(self.global_).get(SALDOS)
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)

    def test_usuario_con_capacidad_poau_no_puede_crear(self):
        """El defecto que se quiere evitar: capacidad de POAU ≠ decidir el techo."""
        respuesta = self.cliente(self.global_).post(
            SALDOS, self._cuerpo(), format='json',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(
            SaldoUnidadCategoria.objects
            .filter(categoria_programatica='251 0 013').exists()
        )

    def test_usuario_con_capacidad_poau_no_puede_editar_ni_borrar(self):
        detalle = f'{SALDOS}{self.saldo_propia.id}/'
        cliente = self.cliente(self.global_)
        self.assertEqual(
            cliente.patch(detalle, {'saldo': '1.00'}, format='json').status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            cliente.delete(detalle).status_code, status.HTTP_403_FORBIDDEN,
        )
        self.saldo_propia.refresh_from_db()
        self.assertEqual(self.saldo_propia.saldo, Decimal('2900000.00'))

    def test_administrador_crea_edita_y_borra(self):
        cliente = self.cliente(self.admin)

        creado = cliente.post(SALDOS, self._cuerpo(), format='json')
        self.assertEqual(creado.status_code, status.HTTP_201_CREATED)

        detalle = f'{SALDOS}{creado.data["id"]}/'
        editado = cliente.patch(detalle, {'saldo': '75000.00'}, format='json')
        self.assertEqual(editado.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(editado.data['saldo']), Decimal('75000.00'))

        self.assertEqual(
            cliente.delete(detalle).status_code, status.HTTP_204_NO_CONTENT,
        )
        self.assertFalse(
            SaldoUnidadCategoria.objects.filter(pk=creado.data['id']).exists()
        )

    def test_anonimo_no_lee(self):
        from rest_framework.test import APIClient
        respuesta = APIClient().get(SALDOS)
        self.assertIn(
            respuesta.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )


class AutorYNormalizacionTests(SaldosUnidadCategoriaBase):
    """B. Se guarda quién lo cargó, y la categoría entra normalizada."""

    def test_created_by_queda_estampado(self):
        """`AsignacionObjetoGasto` dejó trece filas sin autor; acá no se repite."""
        respuesta = self.cliente(self.admin).post(SALDOS, {
            'unidad': str(self.propia.id),
            'categoria_programatica': '344 0 024',
            'saldo': '500000.00',
        }, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)

        fila = SaldoUnidadCategoria.objects.get(pk=respuesta.data['id'])
        self.assertEqual(fila.created_by_id, self.admin.id)
        self.assertEqual(fila.updated_by_id, self.admin.id)

    def test_categoria_se_normaliza(self):
        """`340  0 099` con dos espacios tiene que entrar como `340 0 099`.

        Sin esto el techo no cruza con la operación del POAU y el selector sale
        vacío sin decir por qué.
        """
        respuesta = self.cliente(self.admin).post(SALDOS, {
            'unidad': str(self.propia.id),
            'categoria_programatica': '  340  0   099 ',
            'saldo': '1000.00',
        }, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(respuesta.data['categoria_programatica'], '340 0 099')

    def test_saldo_negativo_se_acepta(self):
        """`SD-000-55` tiene saldo negativo en la planilla y se traslada tal cual.

        Redondearlo a cero inventaría un margen que la unidad no tiene.
        """
        respuesta = self.cliente(self.admin).post(SALDOS, {
            'unidad': str(self.propia.id),
            'categoria_programatica': '280 0 004',
            'saldo': '-11521.00',
        }, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Decimal(respuesta.data['saldo']), Decimal('-11521.00'))


class DuplicadosTests(SaldosUnidadCategoriaBase):
    """C. El mismo par no entra dos veces, ni por API ni por ORM."""

    def test_api_rechaza_el_duplicado_con_400_y_no_con_500(self):
        respuesta = self.cliente(self.admin).post(SALDOS, {
            'unidad': str(self.propia.id),
            'categoria_programatica': '210 0 042',
            'saldo': '999.00',
        }, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        # `apps.core.exceptions.api_exception_handler` envuelve los errores en
        # `{'error': {...}, 'status_code': ...}`.
        detalle = respuesta.data.get('error', respuesta.data)
        self.assertIn('categoria_programatica', detalle)
        self.assertIn('Edite esa fila', str(detalle['categoria_programatica']))
        self.assertEqual(
            SaldoUnidadCategoria.objects
            .filter(unidad=self.propia, categoria_programatica='210 0 042')
            .count(),
            1,
        )

    def test_la_base_bloquea_el_duplicado_con_fuente_nula(self):
        """`nulls_distinct=False`: sin él, dos NULL cuentan como distintos.

        Es la trampa que dejó entrar organismos duplicados en los catálogos
        oficiales. Como las 175 filas heredadas tienen fuente y organismo nulos,
        sin esta cláusula la restricción no protegería a ninguna.
        """
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                SaldoUnidadCategoria.objects.create(
                    unidad=self.propia, categoria_programatica='210 0 042',
                    saldo=Decimal('1.00'),
                )

    def test_editar_la_propia_fila_no_choca_consigo_misma(self):
        detalle = f'{SALDOS}{self.saldo_propia.id}/'
        respuesta = self.cliente(self.admin).patch(
            detalle, {'saldo': '3000000.00'}, format='json',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)


class AlcanceDeLecturaTests(SaldosUnidadCategoriaBase):
    """D. La lectura respeta el alcance organizacional (ADR-003)."""

    @staticmethod
    def _categorias(data):
        filas = data.get('results', data) if isinstance(data, dict) else data
        return {f['categoria_programatica'] for f in filas}

    def test_alcance_acotado_solo_ve_su_unidad(self):
        respuesta = self.cliente(self.acotado).get(SALDOS)
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        categorias = self._categorias(respuesta.data)
        self.assertIn('210 0 042', categorias)
        self.assertNotIn('331 0 022', categorias)

    def test_alcance_global_ve_las_dos(self):
        respuesta = self.cliente(self.global_).get(SALDOS)
        categorias = self._categorias(respuesta.data)
        self.assertEqual(categorias, {'210 0 042', '331 0 022'})

    def test_filtro_por_unidad(self):
        respuesta = self.cliente(self.global_).get(
            f'{SALDOS}?unidad={self.ajena.codigo}',
        )
        self.assertEqual(self._categorias(respuesta.data), {'331 0 022'})
