"""Flujo ESTRATÉGICO maestro: PAD → PEI → POA → POAU (prompt §74 y §84).

Test de integración de la cadena de trazabilidad estratégica completa:
ResultadoPAD → ProductoPAD → (ArticulacionPADPEI) → ResultadoPEI →
ProductoPEI → AccionPOA → OperacionPOAU → ActividadPOAU → TareaPOAU,
incluyendo la generación del código oficial de 16 segmentos (CodificadorService).

Verifica, de punta a punta (§84):
  (a) ``MotorArticulacion.cadena_descendente(ResultadoPAD)`` devuelve la
      cadena completa en orden canónico (8 eslabones);
  (b) ``cadena_ascendente(TareaPOAU)`` devuelve el camino inverso;
  (c) cada eslabón genera el mismo código completo de 16 segmentos, sin
      segmentos omitidos (articulacion_incompleta=False) y pasa la
      validación de dominio de CodificadorService;
  (d) la articulación PAD→PEI está registrada (ArticulacionPADPEI).

Estilo: TestCase Django (como ``FlujoCompletoE2ETests`` de budget) con un
test secuencial principal + verificaciones puntuales. El escenario replica
el de ``cadena_codificable`` de codificación (mismos catálogos) y el de
``test_motor_articulacion.py`` (mismos campos de la cadena).
"""
import datetime

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
from apps.codificacion.models import (
    ComponentePDESA,
    EjePGDESA,
    EntidadCodificadora,
    EntidadTerritorialCGEO,
    LineamientoPAD,
    ResultadoSectorial,
    SectorEconomico,
    VersionCatalogoPlan,
)
from apps.codificacion.services.codificador import CodificadorService
from apps.planificacion.models import Plan

GESTION = 2027
CODIGO_OFICIAL_16 = (
    '04.02.14.01.031001.02.01.01.1312.03.01.01.001.001.001.001'
)
ORDEN_DESCENDENTE = [
    'ResultadoPAD', 'ProductoPAD', 'ResultadoPEI', 'ProductoPEI',
    'AccionPOA', 'OperacionPOAU', 'ActividadPOAU', 'TareaPOAU',
]
CAMPO_LEGACY = CodificadorService.CAMPO_LEGACY_POR_MODELO


class FlujoEstrategicoIntegracionTest(TestCase):
    """Cadena estratégica completa con catálogos vigentes y códigos reales."""

    def setUp(self):
        # -- Catálogos nacionales y PAD vigentes (misma fuente que
        #    cadena_codificable de apps.codificacion) --------------------
        self.entidad, _ = EntidadCodificadora.objects.get_or_create(
            codigo='1312', defaults={'denominacion': 'GAM Sacaba'},
        )
        nacional = VersionCatalogoPlan.objects.create(
            plan=Plan.objects.create(
                codigo='PGDESA-FLUX', nombre='PGDESA Flujo', tipo='pgdesa',
                gestion_inicio=2026, gestion_fin=2030,
                fecha_vigencia_desde=datetime.date(2026, 1, 1),
            ),
            gestion=GESTION, estado=VersionCatalogoPlan.ESTADO_VIGENTE,
            norma_aprobacion='Norma institucional de prueba',
            clasificacion_fuente=VersionCatalogoPlan.FUENTE_OFICIAL,
            procedencia_fuente='Gaceta oficial de prueba',
        )
        pad_version = VersionCatalogoPlan.objects.create(
            plan=Plan.objects.create(
                codigo='PAD-FLUX', nombre='PAD Flujo', tipo='municipal',
                gestion_inicio=2026, gestion_fin=2030,
                fecha_vigencia_desde=datetime.date(2026, 1, 1),
            ),
            gestion=GESTION, estado=VersionCatalogoPlan.ESTADO_VIGENTE,
            norma_aprobacion='Norma municipal de prueba',
            clasificacion_fuente=VersionCatalogoPlan.FUENTE_OFICIAL,
            procedencia_fuente='Archivo municipal de prueba',
        )
        eje = EjePGDESA.objects.create(
            codigo='04', denominacion='Eje', version_catalogo=nacional,
        )
        componente = ComponentePDESA.objects.create(
            codigo='02', denominacion='Componente', eje=eje,
            version_catalogo=nacional,
        )
        sector = SectorEconomico.objects.create(
            codigo='14', denominacion='Sector', componente=componente,
            version_catalogo=nacional,
        )
        resultado_sectorial = ResultadoSectorial.objects.create(
            codigo='01', denominacion='Resultado sectorial', sector=sector,
            version_catalogo=nacional,
        )
        cgeo, _ = EntidadTerritorialCGEO.objects.get_or_create(
            codigo='031001',
            defaults={'nombre': 'Sacaba',
                      'nivel': EntidadTerritorialCGEO.NIVEL_MUNICIPIO},
        )
        cgeo.estado = EntidadTerritorialCGEO.ESTADO_OFICIAL
        cgeo.save(update_fields=['estado', 'updated_at'])
        lineamiento = LineamientoPAD.objects.create(
            codigo='02', denominacion='Lineamiento',
            entidad_territorial=cgeo, version_catalogo=pad_version,
        )

        # -- Cadena estratégica PAD → PEI → POA → POAU --------------------
        self.resultado_pad = ResultadoPAD.objects.create(
            id_cadena='FLUX-RP', codigo_resultado='FLUX-RP',
            denominacion='Resultado PAD Flujo', lineamiento_pad='02',
            vigencia_desde=GESTION, vigencia_hasta=2030,
            cod_geografico='031001', eta='GAM Sacaba', correlativo=1,
            segmento='01', resultado_sectorial_catalogo=resultado_sectorial,
            entidad_territorial_cgeo=cgeo, lineamiento_pad_catalogo=lineamiento,
        )
        self.producto_pad = ProductoPAD.objects.create(
            codigo_producto='FLUX-PP', denominacion='Producto PAD Flujo',
            resultado_pad=self.resultado_pad, correlativo=1, segmento='01',
        )
        self.resultado_pei = ResultadoPEI.objects.create(
            codigo_resultado='FLUX-RI', denominacion='Resultado PEI Flujo',
            cod_entidad='1312', entidad='GAM Sacaba', cod_oei='03',
            vigencia_desde=GESTION, vigencia_hasta=2030, correlativo=1,
            segmento='01', entidad_codificadora=self.entidad,
        )
        self.producto_pei = ProductoPEI.objects.create(
            codigo_producto='FLUX-PI', denominacion='Producto PEI Flujo',
            resultado_pei=self.resultado_pei, correlativo=1, segmento='01',
        )
        ArticulacionPADPEI.objects.create(
            producto_pad=self.producto_pad, producto_pei=self.producto_pei,
        )
        self.accion = AccionPOA.objects.create(
            codigo_accion='FLUX-ACP', denominacion='Acción POA Flujo',
            producto_pei=self.producto_pei, gestion=GESTION, correlativo=1,
            segmento='001',
        )
        self.operacion = OperacionPOAU.objects.create(
            codigo_operacion='FLUX-OP', denominacion='Operación Flujo',
            tipo_operacion='Operación', accion_poa=self.accion,
            correlativo=1, segmento='001',
        )
        self.actividad = ActividadPOAU.objects.create(
            codigo_actividad='FLUX-ACT', denominacion='Actividad Flujo',
            operacion=self.operacion, correlativo=1, segmento='001',
        )
        self.tarea = TareaPOAU.objects.create(
            codigo_tarea='FLUX-TAR', denominacion='Tarea Flujo',
            actividad=self.actividad, correlativo=1, segmento='001',
        )

    # -- E2E secuencial (estilo FlujoCompletoE2ETests) --------------------

    def test_cadena_estrategica_completa(self):
        """§74/§84: PAD → PEI → POA → POAU de punta a punta con códigos."""
        # --------------------------------------------------------------
        # (d) La articulación PAD→PEI debe estar registrada y ser única
        # --------------------------------------------------------------
        enlaces = ArticulacionPADPEI.objects.filter(
            producto_pad=self.producto_pad,
            producto_pei=self.producto_pei,
        )
        self.assertEqual(enlaces.count(), 1,
                         'la articulación PAD-PEI debe estar registrada')

        # --------------------------------------------------------------
        # (a) Descenso: ResultadoPAD → ... → TareaPOAU (8 eslabones)
        # --------------------------------------------------------------
        cadena = MotorArticulacion.cadena_descendente(
            'ResultadoPAD', self.resultado_pad.pk,
        )
        self.assertEqual(
            [e['entidad_tipo'] for e in cadena], ORDEN_DESCENDENTE,
            'la cadena descendente debe recorrer los 8 eslabones en orden',
        )
        self.assertEqual(cadena[0]['codigo'], 'FLUX-RP')
        self.assertEqual(cadena[1]['codigo'], 'FLUX-PP')
        self.assertEqual(cadena[2]['codigo'], 'FLUX-RI')
        self.assertEqual(cadena[3]['codigo'], 'FLUX-PI')
        self.assertEqual(cadena[4]['codigo'], 'FLUX-ACP')
        self.assertEqual(cadena[5]['codigo'], 'FLUX-OP')
        self.assertEqual(cadena[6]['codigo'], 'FLUX-ACT')
        self.assertEqual(cadena[7]['codigo'], 'FLUX-TAR')
        self.assertTrue(
            all(e['gestion'] == GESTION for e in cadena),
            'todos los eslabones deben pertenecer a la gestión 2027',
        )

        # --------------------------------------------------------------
        # (b) Ascenso: TareaPOAU → ... → ResultadoPAD (camino inverso)
        # --------------------------------------------------------------
        inversa = MotorArticulacion.cadena_ascendente(
            'TareaPOAU', self.tarea.pk,
        )
        self.assertEqual(
            [e['entidad_tipo'] for e in inversa],
            list(reversed(ORDEN_DESCENDENTE)),
            'la cadena ascendente debe ser el camino inverso exacto',
        )
        self.assertEqual(inversa[-1]['entidad_tipo'], 'ResultadoPAD',
                         'el ascenso debe alcanzar el marco superior PAD')

        # --------------------------------------------------------------
        # (c) Código oficial: 16 segmentos desde el eslabón terminal;
        #     cada eslabón es válido en el dominio (validar, igual que
        #     los tests de codificacion: generar desde la tarea)
        # --------------------------------------------------------------
        eslabones = [
            self.resultado_pad, self.producto_pad, self.resultado_pei,
            self.producto_pei, self.accion, self.operacion, self.actividad,
            self.tarea,
        ]
        for eslabon in eslabones:
            self.assertTrue(
                CodificadorService.validar(eslabon),
                f'la cadena de {type(eslabon).__name__} debe ser válida '
                f'en el dominio',
            )

        codigo = CodificadorService.generar_codigo_completo(self.tarea)
        self.assertEqual(
            codigo, CODIGO_OFICIAL_16,
            'la tarea (eslabón terminal) debe materializar el código '
            'completo de 16 segmentos',
        )
        self.assertFalse(self.tarea.articulacion_incompleta)
        self.assertTrue(CodificadorService.validar_codigo(codigo))

        # --------------------------------------------------------------
        # (c') El código completo queda asignado en el eslabón terminal
        #      (la persistencia oficial es vía promover_a_oficial)
        # --------------------------------------------------------------
        self.assertEqual(
            self.tarea.codigo_completo_articulacion, CODIGO_OFICIAL_16,
            'el código completo debe quedar asignado en el registro',
        )

    # -- Verificaciones puntuales ----------------------------------------

    def test_codigo_operativo_por_eslabon_poa(self):
        """§74: el código operativo GESTION.ENTIDAD.ACP[.OP.ACT.TAR]."""
        esperados = {
            self.accion: '2027.1312.001',
            self.operacion: '2027.1312.001.001',
            self.actividad: '2027.1312.001.001.001',
            self.tarea: '2027.1312.001.001.001.001',
        }
        for eslabon, esperado in esperados.items():
            self.assertEqual(
                CodificadorService.generar_codigo_operativo(eslabon), esperado,
                f'el código operativo de {type(eslabon).__name__} debe ser '
                f'{esperado}',
            )

    def test_articulacion_pad_pei_es_el_puente_estrategico(self):
        """§84: el ascenso desde el PEI cruza el puente PAD-PEI sin
        ambigüedad (una sola fila de ArticulacionPADPEI)."""
        self.assertEqual(ArticulacionPADPEI.objects.count(), 1)
        enlace = ArticulacionPADPEI.objects.get(producto_pei=self.producto_pei)
        self.assertEqual(enlace.producto_pad, self.producto_pad)

        cadena = MotorArticulacion.cadena_ascendente(
            'ProductoPEI', self.producto_pei.pk,
        )
        self.assertEqual(
            [e['entidad_tipo'] for e in cadena],
            ['ProductoPEI', 'ResultadoPEI', 'ProductoPAD', 'ResultadoPAD'],
            'el puente PAD-PEI debe conectar ambos instrumentos',
        )

    def test_descendente_desde_producto_pei_no_inventa_tramo_pad(self):
        """§84: el descenso desde el propio PEI emite el tramo POA/POAU
        (columna vertebral), sin remontarse al PAD."""
        cadena = MotorArticulacion.cadena_descendente(
            'ProductoPEI', self.producto_pei.pk,
        )
        self.assertEqual(
            [e['entidad_tipo'] for e in cadena],
            ['ProductoPEI', 'AccionPOA', 'OperacionPOAU', 'ActividadPOAU',
             'TareaPOAU'],
        )
        self.assertNotIn('ProductoPAD', [e['entidad_tipo'] for e in cadena])
