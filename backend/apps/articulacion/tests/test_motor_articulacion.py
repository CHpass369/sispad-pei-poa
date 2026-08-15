"""Tests del MotorArticulacion (FASE 5 — PIP INTEGRACIÓN).

La cadena de prueba es la mínima codificable: ResultadoPAD → ProductoPAD →
(ArticulacionPADPEI) → ResultadoPEI → ProductoPEI → AccionPOA →
OperacionPOAU → ActividadPOAU → TareaPOAU (una fila por nivel).
"""
from uuid import uuid4

from django.test import TestCase

from apps.articulacion.models import (
    AccionPOA,
    ActividadPOAU,
    ArticulacionPADPEI,
    OperacionPOAU,
    ProductoPAD,
    ProductoPEI,
    ResultadoPAD,
    ResultadoPEI,
    TareaPOAU,
)
from apps.articulacion.services.motor import MotorArticulacion
from apps.planificacion.models_v2 import (
    InstrumentoPlanificacion,
    NodoEstrategico,
    TipoInstrumento,
    TipoNodoEstrategico,
    TipoVinculoEstrategico,
    VersionInstrumento,
    VersionMetodologia,
    VinculoEstrategico,
)

ORDEN_DESCENDENTE = [
    'ResultadoPAD', 'ProductoPAD', 'ResultadoPEI', 'ProductoPEI',
    'AccionPOA', 'OperacionPOAU', 'ActividadPOAU', 'TareaPOAU',
]


class MotorArticulacionCadenaTest(TestCase):
    """Cadena completa PAD → PEI → POA → POAU con FK reales."""

    def setUp(self):
        self.resultado_pad = ResultadoPAD.objects.create(
            id_cadena='MOTOR-RP-001', codigo_resultado='MTR-01',
            denominacion='Resultado PAD Motor', lineamiento_pad='03',
            vigencia_desde=2027, vigencia_hasta=2030,
            cod_geografico='00', eta='ETA-MOTOR',
        )
        self.producto_pad = ProductoPAD.objects.create(
            codigo_producto='MTR-01.01', denominacion='Producto PAD Motor',
            resultado_pad=self.resultado_pad,
        )
        self.resultado_pei = ResultadoPEI.objects.create(
            codigo_resultado='MTR-02', denominacion='Resultado PEI Motor',
            cod_entidad='1312', entidad='GAM Sacaba',
            vigencia_desde=2027, vigencia_hasta=2030,
        )
        self.producto_pei = ProductoPEI.objects.create(
            codigo_producto='MTR-02.01', denominacion='Producto PEI Motor',
            resultado_pei=self.resultado_pei,
        )
        ArticulacionPADPEI.objects.create(
            producto_pad=self.producto_pad, producto_pei=self.producto_pei,
        )
        self.accion = AccionPOA.objects.create(
            codigo_accion='MTR-02.01.01', denominacion='Acción POA Motor',
            producto_pei=self.producto_pei, gestion=2027,
        )
        self.operacion = OperacionPOAU.objects.create(
            codigo_operacion='MTR-OP-001', denominacion='Operación Motor',
            tipo_operacion='Operación', accion_poa=self.accion,
        )
        self.actividad = ActividadPOAU.objects.create(
            codigo_actividad='MTR-ACT-001', denominacion='Actividad Motor',
            operacion=self.operacion,
        )
        self.tarea = TareaPOAU.objects.create(
            codigo_tarea='MTR-TAR-001', denominacion='Tarea Motor',
            actividad=self.actividad,
        )

    def test_cadena_descendente_desde_resultado_pad(self):
        """ResultadoPAD → ... → TareaPOAU en orden canónico completo."""
        cadena = MotorArticulacion.cadena_descendente(
            'ResultadoPAD', self.resultado_pad.pk,
        )
        self.assertEqual(
            [e['entidad_tipo'] for e in cadena], ORDEN_DESCENDENTE,
        )
        self.assertEqual(cadena[0]['codigo'], 'MTR-01')
        self.assertEqual(cadena[1]['nivel'], 'producto_pad')
        self.assertEqual(cadena[3]['nivel'], 'producto_pei')
        self.assertEqual(cadena[4]['gestion'], 2027)
        self.assertEqual(cadena[7]['codigo'], 'MTR-TAR-001')
        # Cada eslabón expone el contrato {nivel, entidad_tipo, entidad_id,
        # codigo, denominacion, gestion}
        claves = set(cadena[0])
        self.assertEqual(
            claves, {'nivel', 'entidad_tipo', 'entidad_id', 'codigo',
                     'denominacion', 'gestion'},
        )
        self.assertIsNotNone(cadena[0]['entidad_id'])

    def test_cadena_ascendente_desde_tarea(self):
        """TareaPOAU → ... → ResultadoPAD (camino inverso hasta PAD)."""
        cadena = MotorArticulacion.cadena_ascendente(
            'TareaPOAU', self.tarea.pk,
        )
        self.assertEqual(
            [e['entidad_tipo'] for e in cadena],
            list(reversed(ORDEN_DESCENDENTE)),
        )
        self.assertEqual(cadena[-1]['entidad_tipo'], 'ResultadoPAD')
        self.assertEqual(cadena[0]['codigo'], 'MTR-TAR-001')
        self.assertEqual(cadena[4]['nivel'], 'producto_pei')

    def test_cadena_ascendente_desde_accion(self):
        """AccionPOA asciende hasta PAD sin pasar por POAU."""
        cadena = MotorArticulacion.cadena_ascendente('AccionPOA', self.accion.pk)
        self.assertEqual(
            [e['entidad_tipo'] for e in cadena],
            ['AccionPOA', 'ProductoPEI', 'ResultadoPEI', 'ProductoPAD',
             'ResultadoPAD'],
        )

    def test_cadena_descendente_desde_resultado_pei(self):
        """ResultadoPEI desciende por sus propios productos (sin tramo PAD)."""
        cadena = MotorArticulacion.cadena_descendente(
            'ResultadoPEI', self.resultado_pei.pk,
        )
        self.assertEqual(
            [e['entidad_tipo'] for e in cadena],
            ['ResultadoPEI', 'ProductoPEI', 'AccionPOA', 'OperacionPOAU',
             'ActividadPOAU', 'TareaPOAU'],
        )

    def test_tipo_desconocido_devuelve_vacio(self):
        """Un tipo fuera de la cadena (o inexistente) no rompe el motor."""
        uuid_azar = uuid4()
        self.assertEqual(
            MotorArticulacion.cadena_descendente('Inexistente', uuid_azar), [],
        )
        self.assertEqual(
            MotorArticulacion.cadena_ascendente('Inexistente', uuid_azar), [],
        )
        # Tipos existentes en articulacion pero fuera de la cadena codificable
        self.assertEqual(
            MotorArticulacion.cadena_descendente(
                'ArticulacionPADPEI', uuid_azar,
            ),
            [],
        )

    def test_entidad_inexistente_devuelve_vacio(self):
        """UUID válido pero sin registro → lista vacía, sin excepción."""
        self.assertEqual(
            MotorArticulacion.cadena_descendente('TareaPOAU', uuid4()), [],
        )
        self.assertEqual(
            MotorArticulacion.cadena_ascendente('ResultadoPAD', uuid4()), [],
        )

    def test_cadena_con_registros_reales_demo(self):
        """Smoke contra la cadena demo de la BD si está sembrada.

        ``backend/tests/conftest.py`` NO siembra la cadena de articulacion
        (solo workflow e IAM para SQLite), así que en la BD de test este
        test se omite; en una BD real con la demo cargada por
        ``cargar_demo_v2`` sí ejecuta el smoke.
        """
        for modelo in (ResultadoPEI, ProductoPEI, AccionPOA,
                       OperacionPOAU, ActividadPOAU, TareaPOAU):
            if not modelo.objects.exists():
                self.skipTest(
                    'La BD de test no tiene la cadena demo sembrada '
                    '(tests/conftest.py no la siembra).'
                )
        tarea = TareaPOAU.objects.first()
        cadena = MotorArticulacion.cadena_ascendente('TareaPOAU', tarea.pk)
        self.assertTrue(cadena)
        self.assertEqual(cadena[0]['entidad_tipo'], 'TareaPOAU')
        self.assertEqual(
            MotorArticulacion.cadena_descendente(
                'TareaPOAU', tarea.pk,
            )[0]['entidad_id'],
            str(tarea.pk),
        )


class MotorArticulacionV2Test(TestCase):
    """Trazado de instrumentos/versiones y vínculos del kernel V2 (SIS-PE)."""

    def setUp(self):
        tipo_pei = TipoInstrumento.objects.create(
            codigo='PEI-MOTOR', nombre='PEI Motor',
            nivel='institucional',
        )
        metodologia = VersionMetodologia.objects.create(
            codigo='MET-PEI-MOTOR', nombre='Metodología Motor',
            tipo_instrumento=tipo_pei, estado='vigente',
        )
        self.instrumento = InstrumentoPlanificacion.objects.create(
            tipo=tipo_pei, codigo='PEI-MOTOR-2027', nombre='PEI Motor 2027',
            periodo_inicio=2027, periodo_fin=2030, estado='borrador',
        )
        self.version = VersionInstrumento.objects.create(
            instrumento=self.instrumento, metodologia=metodologia,
        )
        tipo_oe = TipoNodoEstrategico.objects.create(
            codigo='OE', denominacion='Objetivo estratégico',
            metodologia=metodologia, nivel_orden=1,
        )
        tipo_ri = TipoNodoEstrategico.objects.create(
            codigo='RI', denominacion='Resultado intermedio',
            metodologia=metodologia, nivel_orden=2,
        )
        tipo_vinculo = TipoVinculoEstrategico.objects.create(
            codigo='ALCANZA', denominacion='Alcanza',
            metodologia=metodologia, origen_permitido=tipo_oe,
            destino_permitido=tipo_ri,
        )
        self.nodo_origen = NodoEstrategico.objects.create(
            version=self.version, tipo_nodo=tipo_oe, codigo='OE-01',
            nombre='Objetivo 1', orden=1,
        )
        self.nodo_destino = NodoEstrategico.objects.create(
            version=self.version, tipo_nodo=tipo_ri, codigo='RI-01',
            nombre='Resultado 1', orden=1,
        )
        self.vinculo = VinculoEstrategico.objects.create(
            version=self.version, origen=self.nodo_origen,
            destino=self.nodo_destino, tipo=tipo_vinculo,
            es_principal=True, ponderacion=50,
        )

    def test_trazar_instrumento_nodo(self):
        """Un NodoEstrategico expone instrumento, versión y vínculos."""
        trazado = MotorArticulacion.trazar_instrumento(self.nodo_origen)
        self.assertEqual(trazado['entidad_tipo'], 'NodoEstrategico')
        self.assertEqual(trazado['codigo'], 'OE-01')
        self.assertEqual(trazado['instrumento']['codigo'], 'PEI-MOTOR-2027')
        self.assertEqual(trazado['version']['numero'], 1)
        self.assertEqual(trazado['version']['inmutable'], False)
        self.assertEqual(len(trazado['vinculos_salientes']), 1)
        self.assertEqual(len(trazado['vinculos_entrantes']), 0)
        saliente = trazado['vinculos_salientes'][0]
        self.assertEqual(saliente['tipo'], 'ALCANZA')
        self.assertEqual(saliente['destino']['codigo'], 'RI-01')
        self.assertEqual(str(saliente['ponderacion']), '50.00')

    def test_trazar_instrumento_vinculo(self):
        """Un VinculoEstrategico expone origen/destino/tipo sobre la versión."""
        trazado = MotorArticulacion.trazar_instrumento(self.vinculo)
        self.assertEqual(trazado['entidad_tipo'], 'VinculoEstrategico')
        self.assertEqual(trazado['tipo_vinculo']['codigo'], 'ALCANZA')
        self.assertEqual(trazado['origen']['codigo'], 'OE-01')
        self.assertEqual(trazado['destino']['codigo'], 'RI-01')
        self.assertEqual(trazado['es_principal'], True)

    def test_trazar_instrumento_instancia_ajena_devuelve_vacio(self):
        """Instancias fuera del kernel V2 (o nulas) → []."""
        self.assertEqual(MotorArticulacion.trazar_instrumento(None), [])
        self.assertEqual(MotorArticulacion.trazar_instrumento('texto'), [])
