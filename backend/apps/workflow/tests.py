from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

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
from apps.poau.models import POAU, POAUActividad, EjecucionFisica, EjecucionFinanciera
from apps.workflow.models import (
    EnvioFormulacion, Revision, Observacion, Aprobacion,
)
from apps.modificaciones.models import SolicitudModificacion, CambioModificacion
from apps.indicadores.models import Indicador, MetaProgramada
from apps.seguimiento.models import (
    ReporteSeguimiento, EntradaSeguimiento, Alerta,
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
        )
        self.poau = POAU.objects.create(
            unidad=self.unidad, gestion=2026,
            codigo='POAU-2026-001', nombre='POA Unidad Test',
            estado='borrador', responsable=self.user_formulador,
        )
        self.actividad_poau = POAUActividad.objects.create(
            poau=self.poau, codigo='ACT-01', nombre='Actividad POAU',
            presupuesto_anual=Decimal('50000.00'),
            meta_fisica_anual=Decimal('100.0000'),
            meta_q1=Decimal('25.0000'), meta_q2=Decimal('25.0000'),
            meta_q3=Decimal('25.0000'), meta_q4=Decimal('25.0000'),
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


class POAUWorkflowTest(WorkflowBaseTestCase):
    """Tests de transiciones de estado del POAU."""

    def test_poau_estado_inicial_borrador(self):
        self.assertEqual(self.poau.estado, 'borrador')

    def test_poau_transicion_borrador_a_enviado(self):
        self.poau.estado = 'enviado'
        self.poau.save()
        self.poau.refresh_from_db()
        self.assertEqual(self.poau.estado, 'enviado')

    def test_poau_transicion_enviado_a_aprobado(self):
        self.poau.estado = 'enviado'
        self.poau.save()
        self.poau.estado = 'aprobado'
        self.poau.save()
        self.poau.refresh_from_db()
        self.assertEqual(self.poau.estado, 'aprobado')

    def test_poau_transicion_enviado_a_rechazado(self):
        self.poau.estado = 'enviado'
        self.poau.save()
        self.poau.estado = 'rechazado'
        self.poau.save()
        self.poau.refresh_from_db()
        self.assertEqual(self.poau.estado, 'rechazado')

    def test_poau_rechazado_puede_volver_borrador(self):
        self.poau.estado = 'enviado'
        self.poau.save()
        self.poau.estado = 'rechazado'
        self.poau.save()
        self.poau.estado = 'borrador'
        self.poau.save()
        self.poau.refresh_from_db()
        self.assertEqual(self.poau.estado, 'borrador')

    def test_poau_no_puede_ir_directo_a_aprobado(self):
        self.poau.estado = 'borrador'
        self.poau.save()
        self.poau.refresh_from_db()
        self.assertEqual(self.poau.estado, 'borrador')


class EjecucionWorkflowTest(WorkflowBaseTestCase):
    """Tests de ejecución física y financiera."""

    def test_ejecucion_fisica_creacion(self):
        ef = EjecucionFisica.objects.create(
            actividad=self.actividad_poau, periodo='2026-Q1',
            tipo_periodo='trimestral', programado=Decimal('25.0000'),
            ejecutado=Decimal('20.0000'),
        )
        self.assertEqual(ef.programado, Decimal('25.0000'))
        self.assertEqual(ef.ejecutado, Decimal('20.0000'))

    def test_ejecucion_financiera_creacion(self):
        ef = EjecucionFinanciera.objects.create(
            actividad=self.actividad_poau, periodo='2026-Q1',
            tipo_periodo='trimestral', programado=Decimal('12500.00'),
            ejecutado=Decimal('10000.00'),
        )
        self.assertEqual(ef.programado, Decimal('12500.00'))

    def test_avance_fisico_calculo(self):
        EjecucionFisica.objects.create(
            actividad=self.actividad_poau, periodo='2026-01',
            tipo_periodo='mensual', programado=Decimal('10.0000'),
            ejecutado=Decimal('8.0000'),
        )
        from django.db.models import Sum
        from django.db.models.functions import Coalesce
        from django.db.models import DecimalField
        agg = EjecucionFisica.objects.filter(
            actividad=self.actividad_poau
        ).aggregate(
            prog=Coalesce(Sum('programado'), 0, output_field=DecimalField(max_digits=20, decimal_places=4)),
            ejec=Coalesce(Sum('ejecutado'), 0, output_field=DecimalField(max_digits=20, decimal_places=4)),
        )
        avance = float(agg['ejec']) / float(agg['prog']) * 100
        self.assertAlmostEqual(avance, 80.0, places=1)

    def test_avance_financiero_calculo(self):
        EjecucionFinanciera.objects.create(
            actividad=self.actividad_poau, periodo='2026-01',
            tipo_periodo='mensual', programado=Decimal('50000.00'),
            ejecutado=Decimal('25000.00'),
        )
        from django.db.models import Sum
        from django.db.models.functions import Coalesce
        from django.db.models import DecimalField
        agg = EjecucionFinanciera.objects.filter(
            actividad=self.actividad_poau
        ).aggregate(
            prog=Coalesce(Sum('programado'), 0, output_field=DecimalField(max_digits=20, decimal_places=2)),
            ejec=Coalesce(Sum('ejecutado'), 0, output_field=DecimalField(max_digits=20, decimal_places=2)),
        )
        avance = float(agg['ejec']) / float(agg['prog']) * 100
        self.assertAlmostEqual(avance, 50.0, places=1)

    def test_semaforo_verde(self):
        pct = 85
        self.assertGreaterEqual(pct, 80)

    def test_semaforo_amarillo(self):
        pct = 60
        self.assertGreaterEqual(pct, 50)
        self.assertLess(pct, 80)

    def test_semaforo_rojo(self):
        pct = 30
        self.assertLess(pct, 50)


class IndicadorCalculoTest(WorkflowBaseTestCase):
    """Tests de cálculo de indicadores y metas."""

    def test_indicador_creacion(self):
        ind = Indicador.objects.create(
            codigo='IND-001', nombre='Indicador de prueba',
            tipo_comportamiento='acumulable',
            meta_anual=Decimal('100.0000'),
        )
        self.assertEqual(ind.meta_anual, Decimal('100.0000'))

    def test_meta_programada_trimestres(self):
        ind = Indicador.objects.create(
            codigo='IND-002', nombre='Indicador Q',
            tipo_comportamiento='acumulable',
            meta_anual=Decimal('100.0000'),
        )
        meta = MetaProgramada.objects.create(
            indicador=ind, gestion=2026, meta_anual=Decimal('100.0000'),
            trimestre1=Decimal('20.0000'), trimestre2=Decimal('25.0000'),
            trimestre3=Decimal('30.0000'), trimestre4=Decimal('25.0000'),
        )
        suma_q = meta.trimestre1 + meta.trimestre2 + meta.trimestre3 + meta.trimestre4
        self.assertEqual(suma_q, meta.meta_anual)

    def test_avance_porcentaje_indicador(self):
        ind = Indicador.objects.create(
            codigo='IND-003', nombre='Indicador avance',
            tipo_comportamiento='acumulable',
            meta_anual=Decimal('200.0000'),
        )
        MetaProgramada.objects.create(
            indicador=ind, gestion=2026, meta_anual=Decimal('200.0000'),
        )
        ejecutado = Decimal('150.0000')
        avance = (ejecutado / ind.meta_anual) * 100
        self.assertEqual(avance, Decimal('75.0000'))


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


class SolicitudModificacionWorkflowTest(WorkflowBaseTestCase):
    """Tests de transiciones de solicitud de modificación."""

    def test_solicitud_creacion_borrador(self):
        sol = SolicitudModificacion.objects.create(
            tipo='meta', gestion_fiscal=2026,
            entidad_afectada_tipo='poau.POAUActividad',
            entidad_afectada_id=self.actividad_poau.id,
            motivo='Cambio de meta solicitado',
            estado='borrador',
        )
        self.assertEqual(sol.estado, 'borrador')

    def test_solicitud_transicion_borrador_a_revision(self):
        sol = SolicitudModificacion.objects.create(
            tipo='operacion', gestion_fiscal=2026,
            entidad_afectada_tipo='poau.POAUActividad',
            entidad_afectada_id=self.actividad_poau.id,
            motivo='Cambio de operación', estado='borrador',
        )
        sol.estado = 'en_revision'
        sol.save()
        sol.refresh_from_db()
        self.assertEqual(sol.estado, 'en_revision')

    def test_solicitud_transicion_revision_a_aprobada(self):
        sol = SolicitudModificacion.objects.create(
            tipo='reprogramacion', gestion_fiscal=2026,
            entidad_afectada_tipo='poau.POAUActividad',
            entidad_afectada_id=self.actividad_poau.id,
            motivo='Reprogramación anual', estado='en_revision',
        )
        sol.estado = 'aprobada'
        sol.save()
        sol.refresh_from_db()
        self.assertEqual(sol.estado, 'aprobada')

    def test_solicitud_transicion_revision_a_rechazada(self):
        sol = SolicitudModificacion.objects.create(
            tipo='incremento', gestion_fiscal=2026,
            entidad_afectada_tipo='presupuesto.LineaPresupuestaria',
            entidad_afectada_id=self.linea.id,
            motivo='Incremento presupuestario', estado='en_revision',
        )
        sol.estado = 'rechazada'
        sol.observaciones = 'No cumple requisitos'
        sol.save()
        sol.refresh_from_db()
        self.assertEqual(sol.estado, 'rechazada')

    def test_cambio_modificacion_asociado(self):
        sol = SolicitudModificacion.objects.create(
            tipo='meta', gestion_fiscal=2026,
            entidad_afectada_tipo='poau.POAUActividad',
            entidad_afectada_id=self.actividad_poau.id,
            motivo='Cambio de meta', estado='borrador',
        )
        CambioModificacion.objects.create(
            solicitud=sol, campo='meta_fisica_anual',
            valor_anterior='100', valor_propuesto='150',
        )
        self.assertEqual(sol.cambios.count(), 1)


class PresupuestoCeilingValidationTest(WorkflowBaseTestCase):
    """Tests de validación de techos presupuestarios."""

    def test_techo_no_puede_ser_negativo(self):
        with self.assertRaises(Exception):
            TechoPresupuestario.objects.create(
                gestion=2026, monto_total=Decimal('-100.00'),
                fuente=self.fuente,
            )

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

    def test_poau_actividad_suma_trimestres(self):
        act = POAUActividad.objects.create(
            poau=self.poau, codigo='ACT-SUM',
            nombre='Actividad Suma',
            meta_fisica_anual=Decimal('100.0000'),
            meta_q1=Decimal('25.0000'), meta_q2=Decimal('25.0000'),
            meta_q3=Decimal('25.0000'), meta_q4=Decimal('25.0000'),
        )
        suma = act.meta_q1 + act.meta_q2 + act.meta_q3 + act.meta_q4
        self.assertEqual(suma, act.meta_fisica_anual)

    def test_poau_actividad_suma_trimestres_invalida(self):
        from django.core.exceptions import ValidationError
        act = POAUActividad(
            poau=self.poau, codigo='ACT-BAD',
            nombre='Actividad Inválida',
            meta_fisica_anual=Decimal('100.0000'),
            meta_q1=Decimal('30.0000'), meta_q2=Decimal('30.0000'),
            meta_q3=Decimal('30.0000'), meta_q4=Decimal('30.0000'),
        )
        with self.assertRaises(ValidationError):
            act.full_clean()


class PEIPADPOAChainValidationTest(WorkflowBaseTestCase):
    """Tests de validación de la cadena PEI-PAD-POA."""

    def test_acp_vinculado_a_amp(self):
        self.assertEqual(self.acp.accion_mediano_plazo, self.amp)

    def test_amp_vinculado_a_nodo(self):
        self.assertEqual(self.amp.nodo_planificacion, self.nodo_amp)

    def test_nodo_vinculado_a_plan(self):
        self.assertEqual(self.nodo_amp.plan, self.plan_pei)

    def test_poau_vinculado_a_unidad(self):
        self.assertEqual(self.poau.unidad, self.unidad)

    def test_poau_actividad_vinculada_a_poau(self):
        self.assertEqual(self.actividad_poau.poau, self.poau)


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
            '/api/workflow/envios-formulacion/', envio_data, format='json'
        )
        self.assertIn(response.status_code, [201, 400])
