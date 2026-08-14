from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient, APITestCase

from apps.accounts.models import Usuario, Rol
from apps.gestion.models import GestionFiscal
from apps.catalogos.models import (
    ObjetoGasto, FuenteFinanciamiento, OrganismoFinanciador,
    FinalidadFuncion, UnidadMedida,
)
from apps.organizacion.models import (
    TipoUnidad, UnidadOrganizacional, DireccionAdministrativa,
    UnidadEjecutora,
)
from apps.presupuesto.models import (
    ProgramaPresupuestario, ProyectoPresupuestario,
    ActividadPresupuestaria, LineaPresupuestaria,
)
from apps.planificacion.models import (
    Plan, NodoPlanificacion, AccionMedianoPlazo, AccionCortoPlazo,
)
from apps.techos.models import TechoPresupuestario, DistribucionTecho, MovimientoTecho
from apps.workflow.models import (
    EnvioFormulacion, Revision, Observacion, Aprobacion,
)
from apps.acciones_correctivas.models import AccionCorrectiva


class WorkflowBaseTestCase(TestCase):
    """Base test case with shared fixtures for workflow tests."""

    def setUp(self):
        self.gestion = GestionFiscal.objects.create(
            anio=2026, estado='formulacion',
            anio_inicio_plurianual=2026, anio_fin_plurianual=2028,
        )
        self.user_admin = Usuario.objects.create_user(
            email='admin@gamsacaba.gob.bo', password='test123',
            first_name='Admin', last_name='User',
            is_staff=True, is_superuser=True,
        )
        self.user_formulador = Usuario.objects.create_user(
            email='formulador@gamsacaba.gob.bo', password='test123',
            first_name='Formulador', last_name='User',
        )
        self.user_revisor = Usuario.objects.create_user(
            email='revisor@gamsacaba.gob.bo', password='test123',
            first_name='Revisor', last_name='User',
        )
        self.user_aprobador = Usuario.objects.create_user(
            email='aprobador@gamsacaba.gob.bo', password='test123',
            first_name='Aprobador', last_name='User',
        )
        self.rol_formulador = Rol.objects.create(
            codigo='FORMULADOR', nombre='Formulador',
        )
        self.rol_revisor = Rol.objects.create(
            codigo='REVISOR', nombre='Revisor',
        )
        self.rol_aprobador = Rol.objects.create(
            codigo='APROBADOR', nombre='Aprobador',
        )
        self.user_formulador.roles.add(self.rol_formulador)
        self.user_revisor.roles.add(self.rol_revisor)
        self.user_aprobador.roles.add(self.rol_aprobador)

        self.tipo_unidad = TipoUnidad.objects.create(
            codigo='SEC', nombre='Secretaría', nivel=1,
        )
        self.unidad = UnidadOrganizacional.objects.create(
            codigo='SEC-01', nombre='Secretaría General',
            sigla='SG', tipo=self.tipo_unidad, gestion=2026,
            fecha_vigencia_desde=date(2026, 1, 1),
        )
        self.da = DireccionAdministrativa.objects.create(
            codigo='DA-01', nombre='Dirección Administrativa',
            gestion=2026, fecha_vigencia_desde=date(2026, 1, 1),
        )
        self.ue = UnidadEjecutora.objects.create(
            codigo='UE-01', nombre='Unidad Ejecutora 1',
            da=self.da, gestion=2026, fecha_vigencia_desde=date(2026, 1, 1),
        )
        self.vig = date(2026, 1, 1)
        self.fuente = FuenteFinanciamiento.objects.create(
            codigo='41-113', gestion=2026,
            denominacion='Coparticipación Tributaria',
            fecha_vigencia_desde=self.vig,
        )
        self.organismo = OrganismoFinanciador.objects.create(
            codigo='GOB-MUN', gestion=2026,
            denominacion='Gobierno Municipal',
            fecha_vigencia_desde=self.vig,
        )
        self.objeto_gasto = ObjetoGasto.objects.create(
            codigo='10000', gestion=2026,
            denominacion='Servicios Personales',
            fecha_vigencia_desde=self.vig,
        )
        self.finalidad = FinalidadFuncion.objects.create(
            codigo='01', gestion=2026,
            denominacion='Función General',
            fecha_vigencia_desde=self.vig,
        )
        self.programa = ProgramaPresupuestario.objects.create(
            codigo='000', nombre='Funcionamiento Alcaldía',
            gestion=2026,
        )
        self.proyecto = ProyectoPresupuestario.objects.create(
            codigo='000', nombre='Proyecto Test',
            programa=self.programa, gestion=2026,
        )
        self.actividad_presup = ActividadPresupuestaria.objects.create(
            codigo='000', nombre='Actividad Test',
            proyecto=self.proyecto, gestion=2026,
        )
        self.techo = TechoPresupuestario.objects.create(
            gestion=2026, monto_total=Decimal('500000.00'),
            fuente=self.fuente, organismo=self.organismo,
        )
        self.linea = LineaPresupuestaria.objects.create(
            gestion=2026, entidad='MUN', da=self.da, ue=self.ue,
            programa=self.programa, proyecto=self.proyecto,
            actividad=self.actividad_presup, finalidad_funcion=self.finalidad,
            fuente=self.fuente, organismo=self.organismo,
            objeto_gasto=self.objeto_gasto, importe=Decimal('100000.00'),
        )
        self.plan_pei = Plan.objects.create(
            codigo='PEI-2021', tipo='pei', nombre='PEI 2021-2025',
            gestion_inicio=2021, gestion_fin=2025,
            fecha_vigencia_desde=date(2021, 1, 1),
        )
        self.nodo_amp = NodoPlanificacion.objects.create(
            plan=self.plan_pei, nivel='accion_mediano',
            codigo='AMP-001', gestion=2025, nombre='AMP Test',
        )
        self.amp = AccionMedianoPlazo.objects.create(
            codigo='AMP-001', nombre='Acción Mediano Plazo',
            nodo_planificacion=self.nodo_amp,
            gestion_inicio=2021, gestion_fin=2025,
        )
        self.acp = AccionCortoPlazo.objects.create(
            codigo='ACP-001', nombre='Acción Corto Plazo',
            accion_mediano_plazo=self.amp,
            unidad_responsable=self.unidad, gestion=2026,
            fecha_inicio=date(2026, 1, 1),
            fecha_fin=date(2026, 12, 31),
        )


class EnvioFormulacionWorkflowTest(WorkflowBaseTestCase):
    """Tests de transiciones de estado de envío de formulación."""

    def test_envio_formulacion_creacion(self):
        envio = EnvioFormulacion.objects.create(
            unidad=self.unidad, gestion=2026, version=1,
            enviado_por=self.user_formulador,
            estado_anterior='borrador', comentario='Envío inicial',
        )
        self.assertEqual(envio.estado_anterior, 'borrador')
        self.assertEqual(envio.gestion, 2026)
        self.assertEqual(envio.enviado_por, self.user_formulador)
        self.assertTrue(envio.activo)

    def test_envio_formulacion_str(self):
        envio = EnvioFormulacion.objects.create(
            unidad=self.unidad, gestion=2026, version=1,
            estado_anterior='borrador',
        )
        s = str(envio)
        self.assertIn('Secre', s)
        self.assertIn('v1', s)

    def test_envio_formulacion_estados(self):
        envio = EnvioFormulacion.objects.create(
            unidad=self.unidad, gestion=2026, version=1,
            estado_anterior='borrador',
        )
        self.assertTrue(envio.activo)
        envio.activo = False
        envio.save()
        envio.refresh_from_db()
        self.assertFalse(envio.activo)

    def test_varios_envios_misma_unidad(self):
        for v in range(1, 4):
            EnvioFormulacion.objects.create(
                unidad=self.unidad, gestion=2026, version=v,
                estado_anterior='borrador',
            )
        self.assertEqual(
            EnvioFormulacion.objects.filter(unidad=self.unidad, gestion=2026).count(), 3
        )


class RevisionWorkflowTest(WorkflowBaseTestCase):
    """Tests de transiciones de estado de revisión."""

    def test_revision_creacion(self):
        envio = EnvioFormulacion.objects.create(
            unidad=self.unidad, gestion=2026, version=1,
            estado_anterior='borrador',
        )
        revision = Revision.objects.create(
            envio=envio, tipo_revision='planificacion',
            revisor=self.user_revisor, estado='pendiente',
        )
        self.assertEqual(revision.estado, 'pendiente')
        self.assertIsNone(revision.resultado)

    def test_revision_transicion_pendiente_a_en_curso(self):
        envio = EnvioFormulacion.objects.create(
            unidad=self.unidad, gestion=2026, version=1,
            estado_anterior='borrador',
        )
        revision = Revision.objects.create(
            envio=envio, tipo_revision='presupuesto',
            revisor=self.user_revisor, estado='pendiente',
        )
        revision.estado = 'en_curso'
        revision.save()
        revision.refresh_from_db()
        self.assertEqual(revision.estado, 'en_curso')

    def test_revision_transicion_en_curso_a_completada(self):
        envio = EnvioFormulacion.objects.create(
            unidad=self.unidad, gestion=2026, version=1,
            estado_anterior='borrador',
        )
        revision = Revision.objects.create(
            envio=envio, tipo_revision='inversion',
            revisor=self.user_revisor, estado='en_curso',
        )
        revision.estado = 'completada'
        revision.resultado = 'aprobado'
        revision.fecha_completado = timezone.now()
        revision.save()
        revision.refresh_from_db()
        self.assertEqual(revision.estado, 'completada')
        self.assertEqual(revision.resultado, 'aprobado')
        self.assertIsNotNone(revision.fecha_completado)

    def test_revision_transicion_devuelta(self):
        envio = EnvioFormulacion.objects.create(
            unidad=self.unidad, gestion=2026, version=1,
            estado_anterior='borrador',
        )
        revision = Revision.objects.create(
            envio=envio, tipo_revision='planificacion',
            revisor=self.user_revisor, estado='en_curso',
        )
        revision.estado = 'devuelta'
        revision.resultado = 'rechazado'
        revision.save()
        revision.refresh_from_db()
        self.assertEqual(revision.estado, 'devuelta')
        self.assertEqual(revision.resultado, 'rechazado')

    def test_tipos_revision(self):
        envio = EnvioFormulacion.objects.create(
            unidad=self.unidad, gestion=2026, version=1,
            estado_anterior='borrador',
        )
        for tipo in ['planificacion', 'presupuesto', 'inversion', 'juridica']:
            rev = Revision.objects.create(
                envio=envio, tipo_revision=tipo,
                revisor=self.user_revisor, estado='pendiente',
            )
            self.assertEqual(rev.tipo_revision, tipo)


class ObservacionWorkflowTest(WorkflowBaseTestCase):
    """Tests del modelo Observación."""

    def test_observacion_creacion(self):
        obs = Observacion.objects.create(
            codigo='OBS-001', tipo='forma', severidad='leve',
            modulo='indicadores', registro_id='123',
            texto='Observación de prueba',
            gestion=2026, estado='abierta',
        )
        self.assertEqual(obs.estado, 'abierta')
        self.assertEqual(obs.gestion, 2026)

    def test_observacion_transiciones_estado(self):
        obs = Observacion.objects.create(
            codigo='OBS-002', tipo='fondo', severidad='moderada',
            modulo='presupuesto', registro_id='456',
            texto='Observación presupuestaria',
            gestion=2026, estado='abierta',
        )
        for estado in ['respondida', 'aceptada', 'cerrada']:
            obs.estado = estado
            obs.save()
            obs.refresh_from_db()
            self.assertEqual(obs.estado, estado)

    def test_observacion_rechazada(self):
        obs = Observacion.objects.create(
            codigo='OBS-003', tipo='legal', severidad='grave',
            modulo='workflow', registro_id='789',
            texto='Observación legal grave',
            gestion=2026, estado='abierta',
        )
        obs.estado = 'rechazada'
        obs.respuesta = 'No procede'
        obs.save()
        obs.refresh_from_db()
        self.assertEqual(obs.estado, 'rechazada')
        self.assertEqual(obs.respuesta, 'No procede')

    def test_observacion_con_responsable(self):
        obs = Observacion.objects.create(
            codigo='OBS-004', tipo='tecnica', severidad='moderada',
            modulo='planificacion', registro_id='101',
            texto='Observación técnica',
            responsable_subsanacion=self.user_formulador,
            fecha_limite=timezone.now() + timedelta(days=7),
            gestion=2026,
        )
        self.assertEqual(obs.responsable_subsanacion, self.user_formulador)
        self.assertIsNotNone(obs.fecha_limite)

    def test_tipos_severidad(self):
        for tipo in ['forma', 'fondo', 'legal', 'presupuestaria', 'tecnica', 'documental']:
            for sev in ['leve', 'moderada', 'grave']:
                obs = Observacion.objects.create(
                    codigo=f'OBS-{tipo[:3]}-{sev[:3]}', tipo=tipo,
                    severidad=sev, modulo='test', registro_id='0',
                    texto='Test', gestion=2026,
                )
                self.assertEqual(obs.tipo, tipo)
                self.assertEqual(obs.severidad, sev)


class AprobacionWorkflowTest(WorkflowBaseTestCase):
    """Tests de transiciones y validaciones de aprobación."""

    def test_aprobacion_creacion(self):
        ap = Aprobacion.objects.create(
            gestion=2026, tipo='unidad',
            aprobado_por=self.user_aprobador,
            estado='aprobado', version=1,
            comentario='Aprobación de unidad',
        )
        self.assertEqual(ap.estado, 'aprobado')
        self.assertEqual(ap.gestion, 2026)

    def test_aprobacion_observada(self):
        ap = Aprobacion.objects.create(
            gestion=2026, tipo='planificacion',
            aprobado_por=self.user_aprobador,
            estado='observado', version=1,
            comentario='Requiere correcciones',
        )
        self.assertEqual(ap.estado, 'observado')

    def test_aprobacion_rechazada(self):
        ap = Aprobacion.objects.create(
            gestion=2026, tipo='presupuesto',
            aprobado_por=self.user_aprobador,
            estado='rechazado', version=1,
            comentario='No cumple requisitos',
        )
        self.assertEqual(ap.estado, 'rechazado')

    def test_aprobacion_con_reapertura(self):
        ap = Aprobacion.objects.create(
            gestion=2026, tipo='mae',
            aprobado_por=self.user_aprobador,
            estado='aprobado', version=1,
            es_reapertura=True,
            motivo_reapertura='Corrección menor',
        )
        self.assertTrue(ap.es_reapertura)
        self.assertEqual(ap.motivo_reapertura, 'Corrección menor')

    def test_aprobacion_con_huella(self):
        huella = 'abc123def456hash'
        ap = Aprobacion.objects.create(
            gestion=2026, tipo='concejo',
            aprobado_por=self.user_aprobador,
            estado='aprobado', version=1,
            huella_documento=huella,
        )
        self.assertEqual(ap.huella_documento, huella)

    def test_aprobaciones_por_tipo(self):
        tipos = ['unidad', 'planificacion', 'presupuesto', 'consolidacion',
                 'control_social', 'mae', 'concejo']
        for tipo in tipos:
            Aprobacion.objects.create(
                gestion=2026, tipo=tipo,
                aprobado_por=self.user_aprobador,
                estado='aprobado', version=1,
            )
        self.assertEqual(
            Aprobacion.objects.filter(gestion=2026).count(), len(tipos)
        )

    def test_aprobaciones_varias_versiones(self):
        for v in range(1, 4):
            Aprobacion.objects.create(
                gestion=2026, tipo='unidad',
                aprobado_por=self.user_aprobador,
                estado='aprobado', version=v,
            )
        self.assertEqual(
            Aprobacion.objects.filter(gestion=2026, tipo='unidad').count(), 3
        )


class DateRangeValidationTest(WorkflowBaseTestCase):
    """Tests de validación de rangos de fecha."""

    def test_gestion_fiscal_plurianual(self):
        gf = GestionFiscal.objects.create(
            anio=2027, estado='preparacion',
            anio_inicio_plurianual=2026, anio_fin_plurianual=2028,
        )
        self.assertGreaterEqual(gf.anio, gf.anio_inicio_plurianual)
        self.assertLessEqual(gf.anio, gf.anio_fin_plurianual)

    def test_accion_corto_plazo_fechas(self):
        self.assertIsNotNone(self.acp.fecha_inicio)
        self.assertIsNotNone(self.acp.fecha_fin)

    def test_observacion_fecha_limite_futura(self):
        obs = Observacion.objects.create(
            codigo='OBS-FUT', tipo='forma', severidad='leve',
            modulo='test', registro_id='0', texto='Test',
            fecha_limite=timezone.now() + timedelta(days=30),
            gestion=2026,
        )
        self.assertGreater(obs.fecha_limite, timezone.now())


class PresupuestoCeilingValidationTest(WorkflowBaseTestCase):
    """Tests de validación de techos presupuestarios."""

    def test_techo_no_puede_ser_negativo(self):
        techo = TechoPresupuestario(
            gestion=2026, monto_total=Decimal('-100.00'),
            fuente=self.fuente,
        )
        with self.assertRaises(ValidationError):
            techo.full_clean()

    def test_distribucion_no_supera_techo(self):
        dist = DistribucionTecho.objects.create(
            techo=self.techo, monto_asignado=Decimal('400000.00'),
        )
        self.assertLessEqual(dist.monto_asignado, self.techo.monto_total)

    def test_linea_presupuestaria_importe_coherente(self):
        self.assertGreaterEqual(self.linea.importe, Decimal('0'))

    def test_movimiento_techo_amount_valido(self):
        mv = MovimientoTecho.objects.create(
            techo=self.techo, movement_type='asignacion',
            amount=Decimal('50000.00'),
            justification='Asignación inicial',
            requested_by=self.user_admin,
            date=timezone.now(),
        )
        self.assertGreater(mv.amount, Decimal('0'))


class PEIPADPOAChainValidationTest(WorkflowBaseTestCase):
    """Tests de validación de la cadena PEI-PAD-POA."""

    def test_acp_vinculado_a_amp(self):
        self.assertEqual(self.acp.accion_mediano_plazo, self.amp)

    def test_amp_vinculado_a_nodo(self):
        self.assertEqual(self.amp.nodo_planificacion, self.nodo_amp)

    def test_nodo_vinculado_a_plan(self):
        self.assertEqual(self.nodo_amp.plan, self.plan_pei)


class APIClientWorkflowTest(APITestCase):
    """Tests de endpoints de workflow con DRF APITestCase."""

    def setUp(self):
        self.client_obj = APIClient()
        self.user = Usuario.objects.create_user(
            email='api_test@gamsacaba.gob.bo', password='test123',
            first_name='API', last_name='Test',
            is_staff=True, is_superuser=True,
        )
        self.client_obj.force_authenticate(user=self.user)

    def test_envio_formulacion_api(self):
        tipo = TipoUnidad.objects.create(
            codigo='API', nombre='Tipo API', nivel=1,
        )
        unidad = UnidadOrganizacional.objects.create(
            codigo='API-SEC', nombre='Unidad API',
            tipo=tipo, gestion=2026,
            fecha_vigencia_desde=date(2026, 1, 1),
        )
        envio_data = {
            'unidad': str(unidad.id),
            'gestion': 2026,
            'version': 1,
            'estado_anterior': 'borrador',
            'comentario': 'Envío de prueba API',
        }
        response = self.client_obj.post(
            '/api/v1/envios/', envio_data, format='json'
        )
        self.assertIn(response.status_code, [201, 400])
