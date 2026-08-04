from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.articulacion.models import (
    AccionPOA,
    ActividadPOAU,
    OperacionPOAU,
    ProductoPEI,
    ResultadoPEI,
    TareaPOAU,
)
from apps.catalogos.models import (
    ClasificadorInstitucional,
    FuenteFinanciamiento,
    ObjetoGasto,
    OrganismoFinanciador,
    VersionClasificador,
)
from apps.organizacion.models import (
    DireccionAdministrativa,
    TipoUnidad,
    UnidadEjecutora,
    UnidadOrganizacional,
)
from apps.presupuesto.models import (
    ActividadPresupuestaria,
    ProgramaPresupuestario,
    ProyectoPresupuestario,
)


pytestmark = pytest.mark.django_db


def crear_version(tipo, gestion=2026, codigo_fuente=None):
    version = VersionClasificador.objects.filter(
        tipo=tipo, gestion=gestion, vigente=True
    ).first()
    if version:
        return version
    return VersionClasificador.objects.create(
        tipo=tipo,
        gestion=gestion,
        norma='RM MEFP 249/2025',
        fecha_norma=date(2025, 6, 24),
        codigo_fuente=codigo_fuente or f'RM-249-{tipo}',
        procedencia_normativa='Clasificadores Presupuestarios 2026',
        hash_fuente='9719fd35d33a4ce0278aef96a5599cb93aa4d9f148d45f57adf81730d5a90ccf',
        clasificacion_fuente=VersionClasificador.FUENTE_OFICIAL,
        vigente=True,
    )


def crear_cadena_operativa(gestion=2026):
    resultado = ResultadoPEI.objects.create(
        codigo_resultado=f'RI-T4-{gestion}',
        denominacion='Resultado PEI T4',
        cod_entidad='1312',
        entidad='GAM Sacaba',
        vigencia_desde=gestion,
        vigencia_hasta=gestion,
    )
    producto = ProductoPEI.objects.create(
        codigo_producto=f'PI-T4-{gestion}',
        denominacion='Producto PEI T4',
        resultado_pei=resultado,
    )
    accion = AccionPOA.objects.create(
        codigo_accion=f'ACP-T4-{gestion}',
        denominacion='Acción POA T4',
        producto_pei=producto,
        gestion=gestion,
    )
    operacion = OperacionPOAU.objects.create(
        codigo_operacion=f'OP-T4-{gestion}',
        denominacion='Operación T4',
        tipo_operacion='Operación',
        accion_poa=accion,
    )
    actividad = ActividadPOAU.objects.create(
        codigo_actividad=f'ACT-T4-{gestion}',
        denominacion='Actividad T4',
        operacion=operacion,
    )
    tarea = TareaPOAU.objects.create(
        codigo_tarea=f'TAR-T4-{gestion}',
        denominacion='Tarea T4',
        actividad=actividad,
    )
    return operacion, actividad, tarea


@pytest.fixture
def estructura_t4():
    categoria_version = VersionClasificador.objects.get(
        tipo=VersionClasificador.TIPO_CATEGORIA_PROGRAMATICA,
        gestion=2026,
        vigente=False,
    )
    fuente_version = crear_version(VersionClasificador.TIPO_FUENTE_FINANCIAMIENTO)
    organismo_version = crear_version(VersionClasificador.TIPO_ORGANISMO_FINANCIADOR)
    objeto_version = crear_version(VersionClasificador.TIPO_OBJETO_GASTO)
    inicio = date(2026, 1, 1)
    entidad = ClasificadorInstitucional.objects.create(
        codigo='1312',
        denominacion='Gobierno Autónomo Municipal de Sacaba',
        gestion=2026,
        fecha_vigencia_desde=inicio,
        fuente_normativa='Clasificadores 2026, PDF p. 15',
    )
    da = DireccionAdministrativa.objects.create(
        codigo='DA-FUENTE',
        nombre='Dirección Administrativa fuente',
        gestion=2026,
        fecha_vigencia_desde=inicio,
    )
    ue = UnidadEjecutora.objects.create(
        codigo='UE-FUENTE',
        nombre='Unidad Ejecutora fuente',
        da=da,
        gestion=2026,
        fecha_vigencia_desde=inicio,
    )
    programa = ProgramaPresupuestario.objects.create(codigo='400', nombre='Programa fuente', gestion=2026)
    proyecto = ProyectoPresupuestario.objects.create(
        codigo='10', nombre='Proyecto fuente', programa=programa, gestion=2026
    )
    actividad_presupuestaria = ActividadPresupuestaria.objects.create(
        codigo='01', nombre='Actividad fuente', proyecto=proyecto, gestion=2026
    )
    tipo_unidad = TipoUnidad.objects.create(codigo='T4', nombre='Tipo T4', nivel=1)
    unidad = UnidadOrganizacional.objects.create(
        codigo='UNI-T4',
        nombre='Unidad T4',
        tipo=tipo_unidad,
        gestion=2026,
        fecha_vigencia_desde=inicio,
    )
    fuente = FuenteFinanciamiento.objects.create(
        codigo='20',
        denominacion='Recursos específicos',
        gestion=2026,
        fecha_vigencia_desde=inicio,
        version_clasificador=fuente_version,
    )
    organismo = OrganismoFinanciador.objects.create(
        codigo='210',
        denominacion='Recursos específicos GAM/GAIOC',
        gestion=2026,
        fecha_vigencia_desde=inicio,
        version_clasificador=organismo_version,
    )
    objeto = ObjetoGasto.objects.create(
        codigo='11210',
        denominacion='Objeto T4',
        gestion=2026,
        fecha_vigencia_desde=inicio,
        version_clasificador=objeto_version,
        nivel=ObjetoGasto.NIVEL_DETALLE,
    )
    operacion, actividad, tarea = crear_cadena_operativa()
    return {
        'categoria_version': categoria_version,
        'entidad': entidad,
        'da': da,
        'ue': ue,
        'programa': programa,
        'proyecto': proyecto,
        'actividad_presupuestaria': actividad_presupuestaria,
        'unidad': unidad,
        'fuente': fuente,
        'organismo': organismo,
        'objeto': objeto,
        'operacion': operacion,
        'actividad': actividad,
        'tarea': tarea,
    }


def crear_categoria(data, **overrides):
    from apps.presupuesto.models import CategoriaProgramatica

    values = {
        'version_clasificador': data['categoria_version'],
        'entidad': data['entidad'],
        'da': data['da'],
        'ue': data['ue'],
        'programa': data['programa'],
        'proyecto': data['proyecto'],
        'actividad': data['actividad_presupuestaria'],
        'codigo_fuente': '1312|DA-FUENTE|UE-FUENTE|400|10|01',
        'procedencia_normativa': 'Apertura fuente pendiente de maestro SIGEP',
    }
    values.update(overrides)
    return CategoriaProgramatica.objects.create(**values)


def datos_asignacion(data, categoria, **overrides):
    values = {
        'categoria_programatica': categoria,
        'fuente': data['fuente'],
        'organismo': data['organismo'],
        'objeto_gasto': data['objeto'],
        'unidad': data['unidad'],
        'operacion': data['operacion'],
        'gestion': 2026,
        'monto_formulado': Decimal('1000.00'),
        'monto_vigente': Decimal('900.00'),
        'monto_ejecutado': Decimal('250.50'),
    }
    values.update(overrides)
    return values


class TestCategoriaProgramatica:
    def test_codigo_compuesto_se_calcula_en_backend_con_codigos_fuente(self, estructura_t4):
        categoria = crear_categoria(estructura_t4, codigo_compuesto='valor-del-frontend')

        assert categoria.codigo_compuesto == '1312.DA-FUENTE.UE-FUENTE.400.10.01'
        assert categoria.codigo_fuente == '1312|DA-FUENTE|UE-FUENTE|400|10|01'
        categoria.proyecto.codigo = '10-FUENTE'
        categoria.proyecto.save(update_fields=['codigo'])
        categoria.save()
        assert categoria.codigo_compuesto == '1312.DA-FUENTE.UE-FUENTE.400.10-FUENTE.01'

    def test_rechaza_entidad_distinta_de_1312_o_componentes_de_otra_gestion(self, estructura_t4):
        otra_entidad = ClasificadorInstitucional.objects.create(
            codigo='9999',
            denominacion='Otra entidad',
            gestion=2026,
            fecha_vigencia_desde=date(2026, 1, 1),
        )
        otra_da = DireccionAdministrativa.objects.create(
            codigo='DA-2025',
            nombre='DA anterior',
            gestion=2025,
            fecha_vigencia_desde=date(2025, 1, 1),
        )

        with pytest.raises(ValidationError) as entidad_error:
            crear_categoria(estructura_t4, entidad=otra_entidad)
        with pytest.raises(ValidationError) as gestion_error:
            crear_categoria(estructura_t4, da=otra_da)

        assert 'entidad' in entidad_error.value.message_dict
        assert 'da' in gestion_error.value.message_dict


class TestAsignacionPresupuestariaUnidad:
    @pytest.mark.parametrize('nivel', ['operacion', 'actividad', 'tarea'])
    def test_acepta_exactamente_un_nivel_canonico_y_calcula_saldo(self, estructura_t4, nivel):
        from apps.presupuesto.models import AsignacionPresupuestariaUnidad

        categoria = crear_categoria(estructura_t4)
        niveles = {'operacion': None, 'actividad': None, 'tarea': None}
        niveles[nivel] = estructura_t4[nivel]

        asignacion = AsignacionPresupuestariaUnidad.objects.create(
            **datos_asignacion(estructura_t4, categoria, **niveles)
        )

        assert asignacion.nivel_operativo == nivel
        assert asignacion.saldo_por_ejecutar == Decimal('649.50')

    @pytest.mark.parametrize(
        'niveles',
        [
            {'operacion': None, 'actividad': None, 'tarea': None},
            {'operacion': 'operacion', 'actividad': 'actividad', 'tarea': None},
        ],
    )
    def test_constraint_rechaza_cero_o_multiples_niveles(self, estructura_t4, niveles):
        from apps.presupuesto.models import AsignacionPresupuestariaUnidad

        categoria = crear_categoria(estructura_t4)
        valores = {
            campo: estructura_t4[referencia] if referencia else None
            for campo, referencia in niveles.items()
        }
        asignacion = AsignacionPresupuestariaUnidad(
            **datos_asignacion(estructura_t4, categoria, **valores)
        )

        with pytest.raises(IntegrityError), transaction.atomic():
            AsignacionPresupuestariaUnidad.objects.bulk_create([asignacion])

    @pytest.mark.parametrize(
        'campo,valor',
        [
            ('monto_formulado', Decimal('-0.01')),
            ('monto_vigente', Decimal('-0.01')),
            ('monto_ejecutado', Decimal('-0.01')),
            ('monto_ejecutado', Decimal('900.01')),
        ],
    )
    def test_constraints_rechazan_montos_invalidos(self, estructura_t4, campo, valor):
        from apps.presupuesto.models import AsignacionPresupuestariaUnidad

        categoria = crear_categoria(estructura_t4)
        asignacion = AsignacionPresupuestariaUnidad(
            **datos_asignacion(estructura_t4, categoria, **{campo: valor})
        )

        with pytest.raises(IntegrityError), transaction.atomic():
            AsignacionPresupuestariaUnidad.objects.bulk_create([asignacion])

    def test_rechaza_duplicados_incluso_con_fks_operativas_null(self, estructura_t4):
        from apps.presupuesto.models import AsignacionPresupuestariaUnidad

        categoria = crear_categoria(estructura_t4)
        valores = datos_asignacion(estructura_t4, categoria, operacion=None, actividad=estructura_t4['actividad'])
        AsignacionPresupuestariaUnidad.objects.create(**valores)

        with pytest.raises(IntegrityError), transaction.atomic():
            AsignacionPresupuestariaUnidad.objects.bulk_create(
                [AsignacionPresupuestariaUnidad(**valores)]
            )

    def test_rechaza_gestion_incoherente_con_categoria_unidad_y_nivel(self, estructura_t4):
        from apps.presupuesto.models import AsignacionPresupuestariaUnidad

        categoria = crear_categoria(estructura_t4)
        asignacion = AsignacionPresupuestariaUnidad(
            **datos_asignacion(estructura_t4, categoria, gestion=2025)
        )

        with pytest.raises(ValidationError) as error:
            asignacion.full_clean()

        assert {'categoria_programatica', 'unidad', 'operacion'} <= set(error.value.message_dict)

    def test_rechaza_catalogo_vinculado_a_version_de_tipo_incorrecto(self, estructura_t4):
        from apps.presupuesto.models import AsignacionPresupuestariaUnidad

        categoria = crear_categoria(estructura_t4)
        version_objeto = estructura_t4['objeto'].version_clasificador
        FuenteFinanciamiento.objects.filter(pk=estructura_t4['fuente'].pk).update(
            version_clasificador=version_objeto
        )
        estructura_t4['fuente'].refresh_from_db()
        asignacion = AsignacionPresupuestariaUnidad(
            **datos_asignacion(estructura_t4, categoria)
        )

        with pytest.raises(ValidationError) as error:
            asignacion.full_clean()

        assert 'fuente' in error.value.message_dict
