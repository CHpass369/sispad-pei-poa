"""Quién puede registrar la programación presupuestaria del POAU.

`ArticulacionPermisos` autorizaba la escritura contra `ROLES_FORMULADORES`, una
lista de códigos de rol en minúsculas de la que solo existen cuatro
(`accounts.0007`). El catálogo vigente —`seed_roles_permisos`, `accounts.0015`
y `accounts.0016`— está en MAYÚSCULAS, así que `ENCARGADO_UO` y
`VALIDADOR_POAU` no figuraban en ninguna: tenían `sis_poa.poau.edit` sembrada y
aun así el paso 3 del asistente de recursos moría con 403.

Lo que estos casos fijan:

- quien tiene la capacidad registra recursos en SU unidad (el defecto que se
  reportó desde el servidor);
- y solo en la suya: `bulk` no pasa por `perform_create`, así que si el alcance
  no se aplica ahí, la capacidad alcanzaba para programar sobre cualquier
  unidad. Una tanda mixta no debe dejar ni la fila propia;
- sin `sis_poa.poau.edit` sigue cerrado: la capacidad autoriza, no el hecho de
  estar autenticado;
- la escritura de PAD/PEI NO se ensancha: esos viewsets no declaran capacidad
  de escritura y siguen gobernados solo por la lista histórica.
"""
from rest_framework import status

from apps.accounts.models import AlcanceOrganizacional, Capacidad, Rol, Usuario
from apps.articulacion.models import ActividadPOAU, AsignacionObjetoGasto
from apps.articulacion.revision_poau import EstadosPOAU

from .test_scope_poau_unidad import ScopePOAUUnidadBase

BULK = '/api/v1/articulacion/asignaciones-gasto/bulk/'
PRODUCTOS_PEI = '/api/v1/articulacion/productos-pei/'

# Las capacidades exactas que `accounts.0016` y `seed_roles_permisos` siembran
# para los tres perfiles POAU. Se replican acá para que el test falle si el
# catálogo cambia sin que nadie lo mire.
_BASE_UNIDAD = (
    'sis_poa.poau.view', 'sis_poa.poau.create', 'sis_poa.poau.edit',
    'sis_poa.poau.submit',
)
PERFILES_REALES = {
    'FORMULADOR_POAU': _BASE_UNIDAD + ('sis_poa.formulate',),
    'VALIDADOR_POAU': _BASE_UNIDAD + ('sis_poa.poau.review',),
    'ENCARGADO_UO': _BASE_UNIDAD + (
        'sis_poa.poau.review', 'sis_poa.poau.approve',
    ),
}


def crear_perfil(codigo, capacidades, unidad, gestion):
    """Usuario con un rol real de producción, acotado a una unidad."""
    rol, _ = Rol.objects.get_or_create(
        codigo=codigo, defaults={'nombre': codigo},
    )
    for codigo_capacidad in capacidades:
        capacidad, _ = Capacidad.objects.get_or_create(
            codigo=codigo_capacidad,
            defaults={
                'nombre': codigo_capacidad,
                'sistema': codigo_capacidad.split('.')[0],
            },
        )
        rol.capacidades.add(capacidad)
    usuario = Usuario.objects.create_user(
        email=f'{codigo.lower()}@test.gob.bo', password='Clave.Scope.2027',
    )
    usuario.roles.add(rol)
    AlcanceOrganizacional.objects.create(
        usuario=usuario, unidad=unidad, rol=rol,
        scope_type=AlcanceOrganizacional.SCOPE_SELF, fiscal_year=gestion,
    )
    return usuario


class RegistroRecursosPorCapacidadTests(ScopePOAUUnidadBase):
    """El paso 3 del asistente de recursos, con perfiles de unidad."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # Cada operación necesita su actividad: el asistente cuelga de ahí.
        cls.actividades = {}
        for accion in (cls.accion_propia, cls.accion_ajena):
            operacion = accion.operaciones.get()
            cls.actividades[accion.pk] = ActividadPOAU.objects.create(
                operacion=operacion,
                codigo_actividad=f'{operacion.codigo_operacion}-AC1',
                denominacion=f'Actividad de {operacion.codigo_operacion}',
            )

        # Perfil que solo mira: tiene la capacidad de lectura pero no la de
        # edición, y su código de rol tampoco está en `ROLES_FORMULADORES`.
        rol_lector, _ = Rol.objects.get_or_create(
            codigo='SCOPE-LECTOR', defaults={'nombre': 'SCOPE-LECTOR'},
        )
        capacidad_view, _ = Capacidad.objects.get_or_create(
            codigo='sis_poa.poau.view',
            defaults={'nombre': 'sis_poa.poau.view', 'sistema': 'sis_poa'},
        )
        rol_lector.capacidades.add(capacidad_view)
        cls.lector = Usuario.objects.create_user(
            email='scope-lector@test.gob.bo', password='Clave.Scope.2027',
        )
        cls.lector.roles.add(rol_lector)
        AlcanceOrganizacional.objects.create(
            usuario=cls.lector, unidad=cls.propia, rol=rol_lector,
            scope_type=AlcanceOrganizacional.SCOPE_SELF,
            fiscal_year=cls.gestion,
        )

    def requerimiento(self, accion, codigo):
        """Un renglón del asistente, con la forma que manda el frontend."""
        actividad = self.actividades[accion.pk]
        return {
            'gestion': 2027,
            'codigo_asignacion': codigo,
            'accion_poa': str(accion.pk),
            'operacion': str(actividad.operacion.pk),
            'actividad': str(actividad.pk),
            'categoria_programatica': '170 0 001',
            'da': '1',
            'ue': '001',
            'programa': '170',
            'cod_objeto_gasto': '25200',
            'descripcion_objeto': 'Estudios e Investigaciones',
            'grupo_gasto': '20000',
            'tipo_gasto': 'Funcionamiento',
            'fuente_financiamiento': '20',
            'organismo_financiador': '230',
            'monto_programado': '1000.00',
            'monto_vigente': '1000.00',
            'programacion_mensual': {'enero': 1000},
        }

    def registrar(self, usuario, requerimientos):
        return self.cliente(usuario).post(
            BULK, requerimientos, format='json',
        )

    def test_el_perfil_de_unidad_registra_recursos_en_su_unidad(self):
        # El defecto reportado: capacidad sembrada, 403 igual.
        respuesta = self.registrar(
            self.acotado,
            [self.requerimiento(self.accion_propia, 'REQ-PROPIA-1')],
        )
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            AsignacionObjetoGasto.objects
            .filter(codigo_asignacion='REQ-PROPIA-1').exists(),
        )

    def test_el_perfil_de_unidad_no_registra_en_una_unidad_ajena(self):
        respuesta = self.registrar(
            self.acotado,
            [self.requerimiento(self.accion_ajena, 'REQ-AJENA-1')],
        )
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(
            AsignacionObjetoGasto.objects
            .filter(codigo_asignacion='REQ-AJENA-1').exists(),
        )

    def test_una_tanda_mixta_no_deja_ni_la_fila_propia(self):
        # La transacción es todo o nada: si la ajena se rechaza, la propia
        # tampoco queda. Con la fila propia primero, guardarla y recién
        # después rechazar la ajena sería el error a detectar.
        respuesta = self.registrar(self.acotado, [
            self.requerimiento(self.accion_propia, 'REQ-MIXTA-PROPIA'),
            self.requerimiento(self.accion_ajena, 'REQ-MIXTA-AJENA'),
        ])
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(
            AsignacionObjetoGasto.objects
            .filter(codigo_asignacion__startswith='REQ-MIXTA').exists(),
        )

    def test_sin_la_capacidad_de_edicion_sigue_bloqueado(self):
        respuesta = self.registrar(
            self.lector,
            [self.requerimiento(self.accion_propia, 'REQ-LECTOR-1')],
        )
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(
            AsignacionObjetoGasto.objects
            .filter(codigo_asignacion='REQ-LECTOR-1').exists(),
        )

    def test_los_tres_perfiles_poau_registran_recursos(self):
        # Los tres códigos reales de producción, con las capacidades que les
        # siembran `accounts.0016` y `seed_roles_permisos`.
        for indice, (codigo, capacidades) in enumerate(PERFILES_REALES.items()):
            with self.subTest(rol=codigo):
                usuario = crear_perfil(
                    codigo, capacidades, self.propia, self.gestion,
                )
                respuesta = self.registrar(
                    usuario,
                    [self.requerimiento(
                        self.accion_propia, f'REQ-{codigo}-{indice}')],
                )
                self.assertEqual(
                    respuesta.status_code, status.HTTP_201_CREATED,
                )

    def test_no_abre_la_escritura_de_pad_pei(self):
        # `ProductoPEIViewSet` no declara `capacidad_escritura`, así que un
        # perfil POAU de unidad sigue sin poder escribir instrumentos de
        # Planificación Estratégica.
        respuesta = self.cliente(self.acotado).post(
            PRODUCTOS_PEI,
            {
                'codigo_producto': 'SCP001.01.99',
                'denominacion': 'Producto intruso',
                'resultado_pei': str(self.producto_pei.resultado_pei_id),
            },
            format='json',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)


class CircuitoValidarAprobarTests(ScopePOAUUnidadBase):
    """Quién valida y quién aprueba un registro de la Matriz POAU.

    El reglamento reparte así: la unidad formula y valida, su encargado cierra.
    `aprobar` miraba `ROLES_APROBADORES` —códigos en minúsculas de SIS-PE— y
    `ENCARGADO_UO` no figura ahí, así que el encargado no podía aprobar nada de
    su propia unidad. Ahora `aprobar` y `observar` reconocen
    `sis_poa.poau.approve`, que es la capacidad que lo distingue de los otros
    dos perfiles.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        for atributo, codigo in (
            ('formulador', 'FORMULADOR_POAU'),
            ('validador', 'VALIDADOR_POAU'),
            ('encargado', 'ENCARGADO_UO'),
        ):
            setattr(cls, atributo, crear_perfil(
                codigo, PERFILES_REALES[codigo], cls.propia, cls.gestion,
            ))

    def setUp(self):
        super().setUp()
        # Cada caso arranca de un borrador limpio de la unidad propia.
        self.operacion = self.accion_propia.operaciones.get()
        self.operacion.estado = EstadosPOAU.BORRADOR
        self.operacion.save(update_fields=['estado'])
        self.url = (
            f'/api/v1/articulacion/operaciones/{self.operacion.pk}/'
        )

    def accion_sobre_la_operacion(self, usuario, verbo, cuerpo=None):
        return self.cliente(usuario).post(
            f'{self.url}{verbo}/', cuerpo or {}, format='json',
        )

    def _validado(self):
        self.operacion.estado = EstadosPOAU.VALIDADO
        self.operacion.save(update_fields=['estado'])

    def test_formulador_y_validador_pueden_validar(self):
        for usuario, codigo in (
            (self.formulador, 'FORMULADOR_POAU'),
            (self.validador, 'VALIDADOR_POAU'),
        ):
            with self.subTest(rol=codigo):
                self.operacion.estado = EstadosPOAU.BORRADOR
                self.operacion.save(update_fields=['estado'])
                respuesta = self.accion_sobre_la_operacion(usuario, 'validar')
                self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
                self.assertEqual(respuesta.data['estado'], EstadosPOAU.VALIDADO)

    def test_solo_el_encargado_aprueba(self):
        self._validado()
        respuesta = self.accion_sobre_la_operacion(self.encargado, 'aprobar')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['estado'], EstadosPOAU.APROBADO)

    def test_el_validador_no_aprueba(self):
        self._validado()
        respuesta = self.accion_sobre_la_operacion(self.validador, 'aprobar')
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)
        self.operacion.refresh_from_db()
        self.assertEqual(self.operacion.estado, EstadosPOAU.VALIDADO)

    def test_el_formulador_no_aprueba(self):
        self._validado()
        respuesta = self.accion_sobre_la_operacion(self.formulador, 'aprobar')
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)
        self.operacion.refresh_from_db()
        self.assertEqual(self.operacion.estado, EstadosPOAU.VALIDADO)

    def test_el_encargado_observa_y_el_validador_no(self):
        self._validado()
        rechazo = self.accion_sobre_la_operacion(
            self.validador, 'observar', {'comentario': 'Falta respaldo'},
        )
        self.assertEqual(rechazo.status_code, status.HTTP_403_FORBIDDEN)

        aceptado = self.accion_sobre_la_operacion(
            self.encargado, 'observar', {'comentario': 'Falta respaldo'},
        )
        self.assertEqual(aceptado.status_code, status.HTTP_200_OK)
        self.assertEqual(aceptado.data['estado'], EstadosPOAU.OBSERVADO)
