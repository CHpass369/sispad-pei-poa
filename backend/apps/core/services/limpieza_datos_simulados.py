"""Allowlisted, transactional cleanup of simulated SISPOA data.

The cleanup intentionally knows the provenance of the data that was created by
the repository seed scripts.  It does not infer that a record is disposable
from a year, a status, or a single text fragment.  Matching a common exact
identifier (for example ``PGDESA-2026-2050``, ``PDESA-2026-2030``, the
organizational code ``GAM`` or a ``LineamientoPAD`` coded ``01``-``20``) is an
exact-key collision, not ownership proof: a legitimate institutional record can
carry the same key.  Normal commit deletes only rows that carry an explicit
deterministic ownership marker (a ``SIM-2027``/``DEMO-`` prefix, an
``@demo.sispoa.local`` email suffix, ``metadatos_importacion__demo=True`` or a
code that literally names DEMO).  Rows that collide on common exact identifiers
without such a marker are reported in the manifest as ambiguous and are only
reachable through the clearly named dangerous opt-in
``--include-ambiguous-test-data``.  Every deletion is represented in the
manifest before it is executed and the protected reference check rejects the
transaction when a candidate would remove or break a non-candidate row.
"""

from __future__ import annotations

import copy
import logging
from collections import OrderedDict
from typing import Iterable

from django.db import models, transaction
from django.db.models import Q

from apps.accounts.models import Rol, Usuario
from apps.articulacion.models import (
    AccionPOA,
    ActividadNormativa,
    ActividadPOAU,
    AcuerdoInternacional,
    ArticulacionPADPEI,
    AsignacionObjetoGasto,
    CodigoNivel,
    IndicadorCadena,
    LineamientoPAD,
    OperacionPOAU,
    ProductoPAD,
    ProductoPEI,
    ResultadoPAD,
    ResultadoPEI,
    SeguimientoPresupuesto,
    TareaNormativa,
    TareaPOAU,
)
from apps.acciones_correctivas.models import (
    AccionCorrectiva,
    CompromisoAccionCorrectiva,
)
from apps.catalogos import models as catalog_models
from apps.gestion.models import CicloFormulacion, EtapaFormulacion, GestionFiscal
from apps.notificaciones.models import (
    Notificacion,
    PreferenciaNotificacion,
    TipoNotificacion,
)
from apps.organizacion.models import (
    AsignacionUsuarioUnidad,
    DireccionAdministrativa,
    TipoUnidad,
    UnidadEjecutora,
    UnidadOrganizacional,
)
from apps.pad.models import (
    ArticulacionSIPEB,
    LineamientoEstrategico,
    PoliticaPAD,
    ProductoTerritorial,
    ProgramacionAnualPAD,
    ResultadoTerritorial,
    SectorPAD,
)
from apps.planificacion.models import (
    AccionCortoPlazo,
    AccionMedianoPlazo,
    ArticulacionPlanificacion,
    NodoPlanificacion,
    Plan,
    PlanVersion,
)
from apps.presupuesto.models import (
    ActividadPresupuestaria,
    LineaPresupuestaria,
    ProgramaPresupuestario,
    ProyectoPresupuestario,
)
from apps.reportes.models import ReporteGenerado
from apps.techos.models import DistribucionTecho, MovimientoTecho, TechoPresupuestario
from apps.workflow.models import EnvioFormulacion, Observacion, Revision


logger = logging.getLogger(__name__)


class CleanupError(RuntimeError):
    """Raised when cleanup cannot prove that the deletion is safe."""


CANONICAL_SECTOR_CODES = tuple(f"{index:02d}" for index in range(1, 21))
CANONICAL_ODS_CODES = tuple(f"{index:02d}" for index in range(1, 18))
REQUIRED_ADMIN_EMAIL = "admin@gamsacaba.gob.bo"

AMBIGUOUS_USER_EMAILS = (
    "test@test.com",
    "test57df8edb@test.com",
    "test70bb5ed4@test.com",
)
AMBIGUOUS_UNIT_CODES = ("U-TEST",)
AMBIGUOUS_TERRITORIAL_RESULT_CODES = (
    "123123",
    "8766",
    "asdfasdf",
    "TEST.1",
    "TEST.FULL.1",
)

SEED_PLAN_CODES = (
    "PDES-2021",
    "PTDI-SAC",
    "PEI-2026",
    "PGDESA-2026-2050",
    "PDESA-2026-2030",
    "PEI-DEMO-2026",
)
SEED_AMP_CODES = tuple(f"AMP-{index:03d}" for index in range(1, 7)) + (
    "DEMO-AMP-01",
)
SEED_ACP_CODES = tuple(f"ACP-{index:03d}" for index in range(1, 7)) + (
    "DEMO-ACP-01",
)
SEED_UNIT_CODES = (
    "GAM",
    "SEC-PLA",
    "SEC-OBR",
    "DIR-PLA",
    "DIR-CAT",
    "DIR-OBR",
    "UPL",
    "UPRE",
    "UIP",
    "UMANT",
    "ORG-DEMO",
    "DIR-DEMO",
    "UE-DEMO",
)
SEED_TYPE_CODES = ("MAE", "SEC", "JEF", "UNI", "UE", "INST", "DIR")
SEED_DA_CODES = ("100", "200", "300", "DA-DEMO")
SEED_UE_CODES = ("UE-100", "UE-200", "UE-300", "UE-DEMO")
SEED_PROGRAM_CODES = ("P-001", "P-002", "P-003", "P-DEMO-01")
EXPLICIT_DEMO_CATALOG_CODES = {
    "ObjetoGasto": ("OG-DEMO",),
    "FuenteFinanciamiento": ("FF-DEMO",),
    "OrganismoFinanciador": ("OF-DEMO",),
    "FinalidadFuncion": ("FIN-DEMO",),
    "UnidadMedida": ("UM-DEMO",),
    "TipoOperacion": ("TOP-DEMO",),
    "TipoProducto": ("TP-DEMO",),
}

# Common exact identifiers that the repository seed scripts historically used.
# Matching a row by one of these keys alone is NOT ownership proof: a real
# institutional record could legitimately carry the same code (a PGDESA plan, a
# unit coded GAM, a LineamientoPAD numbered after its sector, ...).  Only codes
# that literally name DEMO are treated as explicit deterministic markers.
SEED_POLICY_CODES = ("POL-001", "POL-002", "POL-003", "DEMO-POL-01")
SEED_LINEAMIENTO_CODES = (
    "LIN-001-01",
    "LIN-001-02",
    "LIN-002-01",
    "LIN-002-02",
    "LIN-003-01",
    "LIN-003-002",
    "DEMO-LIN-01",
)

# Exact keys that are far too common to ever be treated as ownership proof:
# generic sector acronyms, the organizational code GAM, the canonical sector
# codes 01-20 that also number LineamientoPAD rows, and non-padded ODS
# duplicates 1-9.
AMBIGUOUS_SECTOR_PAD_CODES = ("INF", "DSB", "GAM")
AMBIGUOUS_LINEAMIENTO_PAD_CODES = CANONICAL_SECTOR_CODES
AMBIGUOUS_ODS_DUPLICATE_CODES = tuple(str(index) for index in range(1, 10))


def _split_demo_codes(codes: Iterable[str]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Split seed identifiers into DEMO-named (deterministic markers) and common
    keys (ambiguous exact-key collisions)."""
    demo = tuple(code for code in codes if "DEMO" in code.upper())
    ambiguous = tuple(code for code in codes if "DEMO" not in code.upper())
    return demo, ambiguous


PLAN_DEMO_CODES, PLAN_AMBIGUOUS_CODES = _split_demo_codes(SEED_PLAN_CODES)
AMP_DEMO_CODES, AMP_AMBIGUOUS_CODES = _split_demo_codes(SEED_AMP_CODES)
ACP_DEMO_CODES, ACP_AMBIGUOUS_CODES = _split_demo_codes(SEED_ACP_CODES)
UNIT_DEMO_CODES, UNIT_AMBIGUOUS_CODES = _split_demo_codes(SEED_UNIT_CODES)
TYPE_DEMO_CODES, TYPE_AMBIGUOUS_CODES = _split_demo_codes(SEED_TYPE_CODES)
DA_DEMO_CODES, DA_AMBIGUOUS_CODES = _split_demo_codes(SEED_DA_CODES)
UE_DEMO_CODES, UE_AMBIGUOUS_CODES = _split_demo_codes(SEED_UE_CODES)
PROGRAM_DEMO_CODES, PROGRAM_AMBIGUOUS_CODES = _split_demo_codes(SEED_PROGRAM_CODES)
POLICY_DEMO_CODES, POLICY_AMBIGUOUS_CODES = _split_demo_codes(SEED_POLICY_CODES)
LINEAMIENTO_DEMO_CODES, LINEAMIENTO_AMBIGUOUS_CODES = _split_demo_codes(SEED_LINEAMIENTO_CODES)

CATALOG_MODELS = (
    catalog_models.ClasificadorInstitucional,
    catalog_models.RubroRecurso,
    catalog_models.ObjetoGasto,
    catalog_models.FuenteFinanciamiento,
    catalog_models.OrganismoFinanciador,
    catalog_models.EntidadTransferencia,
    catalog_models.FinalidadFuncion,
    catalog_models.UnidadMedida,
    catalog_models.TipoOperacion,
    catalog_models.TipoProducto,
    catalog_models.TipoProyecto,
    catalog_models.TipoFinanciamiento,
)


# The order is deliberately leaf-to-root.  Foreign keys using PROTECT are
# removed only after their dependent candidates have been removed.
DELETION_ORDER = (
    CompromisoAccionCorrectiva,
    AccionCorrectiva,
    Observacion,
    Revision,
    EnvioFormulacion,
    Notificacion,
    PreferenciaNotificacion,
    TipoNotificacion,
    ReporteGenerado,
    AsignacionUsuarioUnidad,
    SeguimientoPresupuesto,
    AsignacionObjetoGasto,
    TareaNormativa,
    ActividadNormativa,
    TareaPOAU,
    ActividadPOAU,
    OperacionPOAU,
    AccionPOA,
    ArticulacionPADPEI,
    IndicadorCadena,
    ProductoPAD,
    ResultadoPAD,
    LineamientoPAD,
    AcuerdoInternacional,
    ProductoPEI,
    ResultadoPEI,
    LineaPresupuestaria,
    ActividadPresupuestaria,
    ProyectoPresupuestario,
    DistribucionTecho,
    MovimientoTecho,
    TechoPresupuestario,
    ProgramaPresupuestario,
    ProgramacionAnualPAD,
    ArticulacionSIPEB,
    ProductoTerritorial,
    ResultadoTerritorial,
    LineamientoEstrategico,
    PoliticaPAD,
    AccionCortoPlazo,
    AccionMedianoPlazo,
    PlanVersion,
    ArticulacionPlanificacion,
    NodoPlanificacion,
    Plan,
    UnidadEjecutora,
    DireccionAdministrativa,
    UnidadOrganizacional,
    TipoUnidad,
    CicloFormulacion,
    EtapaFormulacion,
    GestionFiscal,
    *CATALOG_MODELS,
    AcuerdoInternacional,
    SectorPAD,
    Usuario,
)


def _as_pk_set(queryset) -> set:
    return set(queryset.values_list("pk", flat=True))


def _add(candidates: dict[type[models.Model], set], model, queryset) -> None:
    candidates.setdefault(model, set()).update(_as_pk_set(queryset))


def _filter_by_pks(model, pks: Iterable):
    return model._default_manager.filter(pk__in=list(pks))


def _build_candidate_sets(include_ambiguous_test_data: bool) -> dict[type[models.Model], set]:
    candidates: dict[type[models.Model], set] = {}

    user_q = Q(email__iendswith="@demo.sispoa.local")
    if include_ambiguous_test_data:
        user_q |= Q(cargo__icontains="demo")
    _add(candidates, Usuario, Usuario.objects.filter(user_q))
    if include_ambiguous_test_data:
        _add(candidates, Usuario, Usuario.objects.filter(email__in=AMBIGUOUS_USER_EMAILS))

    for catalog_model in CATALOG_MODELS:
        explicit_codes = EXPLICIT_DEMO_CATALOG_CODES.get(catalog_model.__name__, ())
        query = Q(codigo__in=explicit_codes) | Q(metadatos_importacion__demo=True)
        _add(candidates, catalog_model, catalog_model.objects.filter(query))

    unit_q = Q(codigo__in=UNIT_DEMO_CODES) | Q(codigo__startswith="SIM-2027")
    if include_ambiguous_test_data:
        unit_q |= Q(nombre__icontains="demo") | Q(codigo__in=AMBIGUOUS_UNIT_CODES)
        unit_q |= Q(codigo__in=UNIT_AMBIGUOUS_CODES)
    _add(candidates, UnidadOrganizacional, UnidadOrganizacional.objects.filter(unit_q))
    tipo_unidad_q = Q(codigo__in=TYPE_DEMO_CODES)
    da_q = Q(codigo__in=DA_DEMO_CODES)
    ue_q = Q(codigo__in=UE_DEMO_CODES)
    if include_ambiguous_test_data:
        tipo_unidad_q |= Q(codigo__in=TYPE_AMBIGUOUS_CODES)
        da_q |= Q(codigo__in=DA_AMBIGUOUS_CODES)
        ue_q |= Q(codigo__in=UE_AMBIGUOUS_CODES)
    _add(candidates, TipoUnidad, TipoUnidad.objects.filter(tipo_unidad_q))
    _add(candidates, DireccionAdministrativa, DireccionAdministrativa.objects.filter(da_q))
    _add(candidates, UnidadEjecutora, UnidadEjecutora.objects.filter(ue_q))

    if include_ambiguous_test_data:
        _add(candidates, GestionFiscal, GestionFiscal.objects.filter(anio=2026))
        _add(candidates, CicloFormulacion, CicloFormulacion.objects.filter(gestion__anio=2026))
        _add(candidates, EtapaFormulacion, EtapaFormulacion.objects.filter(ciclo__gestion__anio=2026))

    plan_q = Q(codigo__startswith="SIM-2027") | Q(codigo__in=PLAN_DEMO_CODES)
    if include_ambiguous_test_data:
        plan_q |= Q(descripcion__icontains="demo") | Q(codigo__in=PLAN_AMBIGUOUS_CODES)
    _add(candidates, Plan, Plan.objects.filter(plan_q))
    plan_ids = candidates.get(Plan, set())
    _add(candidates, NodoPlanificacion, NodoPlanificacion.objects.filter(plan_id__in=plan_ids))
    node_ids = candidates.get(NodoPlanificacion, set())
    _add(candidates, PlanVersion, PlanVersion.objects.filter(plan_id__in=plan_ids))
    _add(
        candidates,
        ArticulacionPlanificacion,
        ArticulacionPlanificacion.objects.filter(
            Q(nodo_origen_id__in=node_ids) | Q(nodo_destino_id__in=node_ids)
        ),
    )
    amp_q = (
        Q(codigo__startswith="SIM-2027")
        | Q(codigo__in=AMP_DEMO_CODES)
        | Q(nodo_planificacion_id__in=node_ids)
    )
    if include_ambiguous_test_data:
        amp_q |= Q(codigo__in=AMP_AMBIGUOUS_CODES)
    _add(candidates, AccionMedianoPlazo, AccionMedianoPlazo.objects.filter(amp_q))
    amp_ids = candidates.get(AccionMedianoPlazo, set())
    acp_q = (
        Q(codigo__startswith="SIM-2027")
        | Q(codigo__in=ACP_DEMO_CODES)
        | Q(accion_mediano_plazo_id__in=amp_ids)
        | Q(unidad_responsable_id__in=candidates.get(UnidadOrganizacional, set()))
    )
    if include_ambiguous_test_data:
        acp_q |= Q(codigo__in=ACP_AMBIGUOUS_CODES)
    _add(candidates, AccionCortoPlazo, AccionCortoPlazo.objects.filter(acp_q))

    policy_q = Q(codigo__in=POLICY_DEMO_CODES)
    if include_ambiguous_test_data:
        policy_q |= Q(nombre__icontains="demo") | Q(codigo__in=POLICY_AMBIGUOUS_CODES)
    _add(candidates, PoliticaPAD, PoliticaPAD.objects.filter(policy_q))
    policy_ids = candidates.get(PoliticaPAD, set())
    lineamiento_q = Q(politica_id__in=policy_ids) | Q(codigo__in=LINEAMIENTO_DEMO_CODES)
    if include_ambiguous_test_data:
        lineamiento_q |= (
            Q(nombre__icontains="demo") | Q(codigo__in=LINEAMIENTO_AMBIGUOUS_CODES)
        )
    _add(candidates, LineamientoEstrategico, LineamientoEstrategico.objects.filter(lineamiento_q))
    lineamiento_ids = candidates.get(LineamientoEstrategico, set())
    territorial_result_q = Q(lineamiento_id__in=lineamiento_ids) | Q(codigo__startswith="DEMO-")
    if include_ambiguous_test_data:
        territorial_result_q |= Q(codigo__in=AMBIGUOUS_TERRITORIAL_RESULT_CODES)
    _add(candidates, ResultadoTerritorial, ResultadoTerritorial.objects.filter(territorial_result_q))
    territorial_result_ids = candidates.get(ResultadoTerritorial, set())
    _add(
        candidates,
        ProductoTerritorial,
        ProductoTerritorial.objects.filter(resultado_id__in=territorial_result_ids),
    )
    territorial_product_ids = candidates.get(ProductoTerritorial, set())
    _add(
        candidates,
        ProgramacionAnualPAD,
        ProgramacionAnualPAD.objects.filter(
            Q(resultado_id__in=territorial_result_ids)
            | Q(producto_id__in=territorial_product_ids)
        ),
    )
    _add(
        candidates,
        ArticulacionSIPEB,
        ArticulacionSIPEB.objects.filter(resultado_id__in=territorial_result_ids),
    )

    if include_ambiguous_test_data:
        _add(candidates, SectorPAD, SectorPAD.objects.filter(codigo__in=AMBIGUOUS_SECTOR_PAD_CODES))
        _add(
            candidates,
            LineamientoPAD,
            LineamientoPAD.objects.filter(codigo__in=AMBIGUOUS_LINEAMIENTO_PAD_CODES),
        )
        _add(
            candidates,
            AcuerdoInternacional,
            AcuerdoInternacional.objects.filter(
                tipo_acuerdo="ODS", codigo__in=AMBIGUOUS_ODS_DUPLICATE_CODES
            ),
        )
    resultado_pad_q = Q(cod_resultado_pds__startswith="DEMO-")
    if include_ambiguous_test_data:
        resultado_pad_q |= (
            Q(codigo_resultado__startswith="031001.")
            | Q(denominacion__icontains="demo")
        )
    _add(candidates, ResultadoPAD, ResultadoPAD.objects.filter(resultado_pad_q))
    resultado_pad_ids = candidates.get(ResultadoPAD, set())
    _add(candidates, ProductoPAD, ProductoPAD.objects.filter(resultado_pad_id__in=resultado_pad_ids))
    producto_pad_ids = candidates.get(ProductoPAD, set())

    resultado_pei_q = Q(codigo_resultado__startswith="SIM-2027")
    if include_ambiguous_test_data:
        resultado_pei_q |= Q(denominacion__icontains="demo") | Q(denominacion__icontains="simul")
    _add(candidates, ResultadoPEI, ResultadoPEI.objects.filter(resultado_pei_q))
    resultado_pei_ids = candidates.get(ResultadoPEI, set())
    producto_pei_q = (
        Q(resultado_pei_id__in=resultado_pei_ids)
        | Q(codigo_producto__startswith="SIM-2027")
    )
    if include_ambiguous_test_data:
        producto_pei_q |= Q(denominacion__icontains="demo")
    _add(candidates, ProductoPEI, ProductoPEI.objects.filter(producto_pei_q))
    producto_pei_ids = candidates.get(ProductoPEI, set())
    _add(
        candidates,
        ArticulacionPADPEI,
        ArticulacionPADPEI.objects.filter(
            Q(producto_pad_id__in=producto_pad_ids) | Q(producto_pei_id__in=producto_pei_ids)
        ),
    )
    _add(
        candidates,
        IndicadorCadena,
        IndicadorCadena.objects.filter(
            Q(producto_pad_id__in=producto_pad_ids) | Q(producto_pei_id__in=producto_pei_ids)
        ),
    )
    accion_poa_q = (
        Q(producto_pei_id__in=producto_pei_ids)
        | Q(codigo_accion__startswith="SIM-2027")
    )
    if include_ambiguous_test_data:
        accion_poa_q |= Q(denominacion__icontains="demo")
    _add(candidates, AccionPOA, AccionPOA.objects.filter(accion_poa_q))
    accion_poa_ids = candidates.get(AccionPOA, set())
    operacion_poau_q = (
        Q(accion_poa_id__in=accion_poa_ids)
        | Q(codigo_operacion__startswith="SIM-2027")
    )
    if include_ambiguous_test_data:
        operacion_poau_q |= Q(denominacion__icontains="demo")
    _add(candidates, OperacionPOAU, OperacionPOAU.objects.filter(operacion_poau_q))
    operacion_poau_ids = candidates.get(OperacionPOAU, set())
    actividad_poau_q = (
        Q(operacion_id__in=operacion_poau_ids)
        | Q(codigo_actividad__startswith="SIM-2027")
    )
    if include_ambiguous_test_data:
        actividad_poau_q |= Q(denominacion__icontains="demo")
    _add(candidates, ActividadPOAU, ActividadPOAU.objects.filter(actividad_poau_q))
    actividad_poau_ids = candidates.get(ActividadPOAU, set())
    tarea_poau_q = (
        Q(actividad_id__in=actividad_poau_ids)
        | Q(codigo_tarea__startswith="SIM-2027")
    )
    if include_ambiguous_test_data:
        tarea_poau_q |= Q(denominacion__icontains="demo")
    _add(candidates, TareaPOAU, TareaPOAU.objects.filter(tarea_poau_q))
    tarea_poau_ids = candidates.get(TareaPOAU, set())
    _add(
        candidates,
        ActividadNormativa,
        ActividadNormativa.objects.filter(actividad_id__in=actividad_poau_ids),
    )
    _add(candidates, TareaNormativa, TareaNormativa.objects.filter(tarea_id__in=tarea_poau_ids))
    _add(
        candidates,
        SeguimientoPresupuesto,
        SeguimientoPresupuesto.objects.filter(
            Q(accion_poa_id__in=accion_poa_ids)
            | Q(operacion_id__in=operacion_poau_ids)
            | Q(actividad_id__in=actividad_poau_ids)
            | Q(tarea_id__in=tarea_poau_ids)
            | Q(id_cadena__startswith="SP-DEMO")
        ),
    )
    _add(
        candidates,
        AsignacionObjetoGasto,
        AsignacionObjetoGasto.objects.filter(
            Q(accion_poa_id__in=accion_poa_ids)
            | Q(operacion_id__in=operacion_poau_ids)
            | Q(actividad_id__in=actividad_poau_ids)
            | Q(tarea_id__in=tarea_poau_ids)
            | Q(codigo_asignacion__startswith="DEMO-")
        ),
    )

    program_q = Q(codigo__in=PROGRAM_DEMO_CODES)
    if include_ambiguous_test_data:
        program_q |= Q(descripcion__icontains="demo") | Q(codigo__in=PROGRAM_AMBIGUOUS_CODES)
    _add(candidates, ProgramaPresupuestario, ProgramaPresupuestario.objects.filter(program_q))
    program_ids = candidates.get(ProgramaPresupuestario, set())
    _add(candidates, ProyectoPresupuestario, ProyectoPresupuestario.objects.filter(programa_id__in=program_ids))
    project_ids = candidates.get(ProyectoPresupuestario, set())
    _add(candidates, ActividadPresupuestaria, ActividadPresupuestaria.objects.filter(proyecto_id__in=project_ids))
    activity_budget_ids = candidates.get(ActividadPresupuestaria, set())
    _add(
        candidates,
        LineaPresupuestaria,
        LineaPresupuestaria.objects.filter(
            Q(programa_id__in=program_ids)
            | Q(proyecto_id__in=project_ids)
            | Q(actividad_id__in=activity_budget_ids)
            | Q(da_id__in=candidates.get(DireccionAdministrativa, set()))
            | Q(ue_id__in=candidates.get(UnidadEjecutora, set()))
        ),
    )
    techo_q = (
        Q(fuente_id__in=_catalog_ids(candidates, catalog_models.FuenteFinanciamiento))
        | Q(organismo_id__in=_catalog_ids(candidates, catalog_models.OrganismoFinanciador))
    )
    if include_ambiguous_test_data:
        techo_q |= Q(gestion=2026)
    _add(candidates, TechoPresupuestario, TechoPresupuestario.objects.filter(techo_q))
    techo_ids = candidates.get(TechoPresupuestario, set())
    _add(
        candidates,
        DistribucionTecho,
        DistribucionTecho.objects.filter(
            Q(techo_id__in=techo_ids)
            | Q(programa_id__in=program_ids)
            | Q(da_id__in=candidates.get(DireccionAdministrativa, set()))
            | Q(ue_id__in=candidates.get(UnidadEjecutora, set()))
            | Q(unidad_id__in=candidates.get(UnidadOrganizacional, set()))
        ),
    )
    _add(
        candidates,
        MovimientoTecho,
        MovimientoTecho.objects.filter(
            Q(techo_id__in=techo_ids)
            | Q(source_ceiling_id__in=techo_ids)
            | Q(destination_ceiling_id__in=techo_ids)
        ),
    )

    _add(
        candidates,
        AccionCorrectiva,
        AccionCorrectiva.objects.filter(
            Q(responsible_id__in=candidates.get(Usuario, set()))
            | Q(responsible_unit_id__in=candidates.get(UnidadOrganizacional, set()))
        ),
    )
    _add(
        candidates,
        CompromisoAccionCorrectiva,
        CompromisoAccionCorrectiva.objects.filter(
            accion_correctiva_id__in=candidates.get(AccionCorrectiva, set())
        ),
    )

    _add(candidates, EnvioFormulacion, EnvioFormulacion.objects.filter(unidad_id__in=candidates.get(UnidadOrganizacional, set())))
    envio_ids = candidates.get(EnvioFormulacion, set())
    _add(candidates, Revision, Revision.objects.filter(envio_id__in=envio_ids))
    revision_ids = candidates.get(Revision, set())
    _add(
        candidates,
        Observacion,
        Observacion.objects.filter(
            Q(revision_id__in=revision_ids) | Q(codigo__startswith="DEMO-")
        ),
    )

    _add(candidates, TipoNotificacion, TipoNotificacion.objects.filter(codigo__startswith="DEMO-"))
    notification_type_ids = candidates.get(TipoNotificacion, set())
    _add(
        candidates,
        Notificacion,
        Notificacion.objects.filter(
            Q(tipo_id__in=notification_type_ids)
            | Q(user_id__in=candidates.get(Usuario, set()))
            | Q(metadata__demo=True)
        ),
    )
    _add(
        candidates,
        PreferenciaNotificacion,
        PreferenciaNotificacion.objects.filter(user_id__in=candidates.get(Usuario, set())),
    )

    _add(
        candidates,
        ReporteGenerado,
        ReporteGenerado.objects.filter(
            Q(generado_por_id__in=candidates.get(Usuario, set()))
            | Q(parametros__demo=True)
        ),
    )

    _add(
        candidates,
        AsignacionUsuarioUnidad,
        AsignacionUsuarioUnidad.objects.filter(
            Q(usuario_id__in=candidates.get(Usuario, set()))
            | Q(unidad_id__in=candidates.get(UnidadOrganizacional, set()))
        ),
    )

    # Catalog rows used only by already selected budget/native records are
    # intentionally left alone unless they carry an explicit demo marker.
    # This is what keeps the cleanup from deleting an official catalog merely
    # because a demo row once referenced it.
    return candidates


def _build_ambiguous_exact_key_matches() -> dict[type[models.Model], set]:
    """Rows that collide on common exact seed identifiers but cannot prove
    ownership.

    They are excluded from normal-commit candidates and reported in the
    manifest as ambiguous; only the clearly named dangerous opt-in
    (``include_ambiguous_test_data``) reaches them.
    """
    matches: dict[type[models.Model], set] = {}
    _add(matches, Plan, Plan.objects.filter(codigo__in=PLAN_AMBIGUOUS_CODES))
    _add(
        matches,
        UnidadOrganizacional,
        UnidadOrganizacional.objects.filter(codigo__in=UNIT_AMBIGUOUS_CODES),
    )
    _add(matches, TipoUnidad, TipoUnidad.objects.filter(codigo__in=TYPE_AMBIGUOUS_CODES))
    _add(
        matches,
        DireccionAdministrativa,
        DireccionAdministrativa.objects.filter(codigo__in=DA_AMBIGUOUS_CODES),
    )
    _add(
        matches,
        UnidadEjecutora,
        UnidadEjecutora.objects.filter(codigo__in=UE_AMBIGUOUS_CODES),
    )
    _add(
        matches,
        AccionMedianoPlazo,
        AccionMedianoPlazo.objects.filter(codigo__in=AMP_AMBIGUOUS_CODES),
    )
    _add(
        matches,
        AccionCortoPlazo,
        AccionCortoPlazo.objects.filter(codigo__in=ACP_AMBIGUOUS_CODES),
    )
    _add(
        matches,
        PoliticaPAD,
        PoliticaPAD.objects.filter(codigo__in=POLICY_AMBIGUOUS_CODES),
    )
    _add(
        matches,
        LineamientoEstrategico,
        LineamientoEstrategico.objects.filter(codigo__in=LINEAMIENTO_AMBIGUOUS_CODES),
    )
    _add(
        matches,
        SectorPAD,
        SectorPAD.objects.filter(codigo__in=AMBIGUOUS_SECTOR_PAD_CODES),
    )
    _add(
        matches,
        LineamientoPAD,
        LineamientoPAD.objects.filter(codigo__in=AMBIGUOUS_LINEAMIENTO_PAD_CODES),
    )
    _add(
        matches,
        AcuerdoInternacional,
        AcuerdoInternacional.objects.filter(
            tipo_acuerdo="ODS", codigo__in=AMBIGUOUS_ODS_DUPLICATE_CODES
        ),
    )
    _add(
        matches,
        ProgramaPresupuestario,
        ProgramaPresupuestario.objects.filter(codigo__in=PROGRAM_AMBIGUOUS_CODES),
    )
    return matches


def _catalog_ids(candidates, model):
    return candidates.get(model, set())


def _preservation_snapshot() -> dict:
    return {
        "admin_pk": str(Usuario.objects.get(email=REQUIRED_ADMIN_EMAIL).pk)
        if Usuario.objects.filter(email=REQUIRED_ADMIN_EMAIL).exists()
        else None,
        "role_pks": sorted(str(pk) for pk in Rol.objects.values_list("pk", flat=True)),
        "codigo_nivel_pks": sorted(str(pk) for pk in CodigoNivel.objects.values_list("pk", flat=True)),
        "canonical_sector_pks": sorted(
            str(pk)
            for pk in SectorPAD.objects.filter(codigo__in=CANONICAL_SECTOR_CODES).values_list("pk", flat=True)
        ),
        "canonical_ods_pks": sorted(
            str(pk)
            for pk in AcuerdoInternacional.objects.filter(
                tipo_acuerdo="ODS", codigo__in=CANONICAL_ODS_CODES
            ).values_list("pk", flat=True)
        ),
    }


def _manifest_from_sets(
    candidates,
    include_ambiguous_test_data: bool,
    ambiguous: dict[type[models.Model], set] | None = None,
) -> dict:
    ordered = OrderedDict()
    for model in DELETION_ORDER:
        pks = candidates.get(model, set())
        if pks:
            ordered[model._meta.label] = {
                "model": model._meta.label,
                "count": len(pks),
                "primary_keys": sorted(str(pk) for pk in pks),
            }
    ambiguous_ordered = OrderedDict()
    ambiguous = ambiguous or {}
    for model in DELETION_ORDER:
        pks = ambiguous.get(model, set())
        if pks:
            ambiguous_ordered[model._meta.label] = {
                "model": model._meta.label,
                "count": len(pks),
                "primary_keys": sorted(str(pk) for pk in pks),
            }
    warnings = []
    if not include_ambiguous_test_data:
        warnings.append(
            "Ambiguous heuristic matches are excluded from deletion candidates. "
            "Pass --include-ambiguous-test-data only after explicit review."
        )
        warnings.append(
            "Rows matching common exact seed identifiers (e.g. PGDESA-2026-2050, "
            "PDESA-2026-2030, unit code GAM, LineamientoPAD 01-20) cannot prove "
            "ownership by key collision and are reported under "
            "ambiguous_excluded; they require --include-ambiguous-test-data."
        )
    return {
        "version": 1,
        "include_ambiguous_test_data": include_ambiguous_test_data,
        "preserved": _preservation_snapshot(),
        "candidates": ordered,
        "candidate_total": sum(entry["count"] for entry in ordered.values()),
        "ambiguous_excluded": ambiguous_ordered,
        "ambiguous_excluded_total": sum(
            entry["count"] for entry in ambiguous_ordered.values()
        ),
        "warnings": warnings,
    }


def build_cleanup_manifest(include_ambiguous_test_data: bool = False) -> dict:
    """Build a read-only manifest with counts and primary keys."""

    candidates = _build_candidate_sets(include_ambiguous_test_data)
    ambiguous = {}
    if not include_ambiguous_test_data:
        for model, pks in _build_ambiguous_exact_key_matches().items():
            ambiguous[model] = pks - candidates.get(model, set())
    return _manifest_from_sets(candidates, include_ambiguous_test_data, ambiguous)


def _manifest_sets(manifest: dict) -> dict[type[models.Model], set]:
    model_by_label = {model._meta.label: model for model in DELETION_ORDER}
    result = {}
    for label, details in manifest["candidates"].items():
        result[model_by_label[label]] = set(details["primary_keys"])
    return result


def validate_no_unplanned_protected_references(candidates: dict[type[models.Model], set]) -> None:
    """Reject candidate parents that would affect a non-candidate child."""

    for parent_model, parent_pks in candidates.items():
        if not parent_pks:
            continue
        for relation in parent_model._meta.related_objects:
            # M2M through rows are disposable join rows and are handled by the
            # database.  They cannot be an independently preserved business row.
            if relation.many_to_many:
                continue
            child_model = relation.related_model
            field_name = relation.field.name
            referenced = child_model._default_manager.filter(
                **{f"{field_name}__in": list(parent_pks)}
            )
            if not referenced.exists():
                continue
            candidate_child_pks = candidates.get(child_model, set())
            outside = referenced.exclude(pk__in=list(candidate_child_pks))
            on_delete = relation.on_delete
            if outside.exists() and on_delete in (models.PROTECT, models.RESTRICT, models.CASCADE):
                examples = list(outside.values_list("pk", flat=True)[:5])
                raise CleanupError(
                    f"{parent_model._meta.label} candidate has non-candidate "
                    f"{child_model._meta.label} references: {examples}"
                )

    duplicate_ods = candidates.get(AcuerdoInternacional, set())
    if duplicate_ods:
        demo_result_ids = candidates.get(ResultadoPAD, set())
        through = ResultadoPAD.acuerdo_ods.through
        outside = through.objects.filter(
            acuerdointernacional_id__in=list(duplicate_ods)
        ).exclude(resultadopad_id__in=list(demo_result_ids))
        if outside.exists():
            raise CleanupError(
                "A non-candidate ResultadoPAD references a non-canonical ODS duplicate"
            )


def validate_preserved_state(snapshot: dict) -> None:
    """Validate the invariants that make the cleanup safe to commit."""

    admin = Usuario.objects.filter(email=REQUIRED_ADMIN_EMAIL).first()
    if admin is None or not admin.is_superuser or not admin.is_staff:
        raise CleanupError("Required administrator was not preserved")
    if str(admin.pk) != snapshot["admin_pk"]:
        raise CleanupError("Required administrator primary key changed")

    current_role_pks = {str(pk) for pk in Rol.objects.values_list("pk", flat=True)}
    if not set(snapshot["role_pks"]).issubset(current_role_pks):
        raise CleanupError("A system role was removed")

    current_codigo_nivel_pks = {
        str(pk) for pk in CodigoNivel.objects.values_list("pk", flat=True)
    }
    if not set(snapshot["codigo_nivel_pks"]).issubset(current_codigo_nivel_pks):
        raise CleanupError("A CodigoNivel catalog row was removed")

    if set(
        SectorPAD.objects.filter(codigo__in=CANONICAL_SECTOR_CODES).values_list("codigo", flat=True)
    ) != set(CANONICAL_SECTOR_CODES):
        raise CleanupError("The canonical 20 SectorPAD rows are not preserved")
    if (
        AcuerdoInternacional.objects.filter(
            tipo_acuerdo="ODS", codigo__in=CANONICAL_ODS_CODES
        ).values("codigo").distinct().count()
        != len(CANONICAL_ODS_CODES)
    ):
        raise CleanupError("The canonical 17 ODS rows are not preserved")


def _assert_no_remaining_candidates(include_ambiguous_test_data: bool) -> None:
    remaining = _build_candidate_sets(include_ambiguous_test_data)
    remaining = {
        model: pks for model, pks in remaining.items() if pks and model not in (Rol, CodigoNivel)
    }
    if remaining:
        summary = {
            model._meta.label: sorted(str(pk) for pk in pks)[:5]
            for model, pks in remaining.items()
        }
        raise CleanupError(f"Simulated candidates remain after cleanup: {summary}")


def _delete_candidates(candidates: dict[type[models.Model], set]) -> int:
    total = 0
    for model in DELETION_ORDER:
        pks = candidates.get(model, set())
        if not pks:
            continue
        deleted, _ = _filter_by_pks(model, pks).delete()
        total += deleted
        logger.info(
            "simulated cleanup model=%s candidate_count=%s deleted_count=%s primary_keys=%s",
            model._meta.label,
            len(pks),
            deleted,
            sorted(str(pk) for pk in pks),
        )
    return total


def clean_simulated_data(
    *,
    commit: bool = False,
    include_ambiguous_test_data: bool = False,
) -> dict:
    """Return a manifest, or atomically delete exactly that manifest."""

    manifest = build_cleanup_manifest(include_ambiguous_test_data)
    if not commit:
        return {
            **manifest,
            "committed": False,
            "deleted": 0,
            "remaining_candidates": None,
        }

    snapshot = copy.deepcopy(manifest["preserved"])
    candidates = _manifest_sets(manifest)
    validate_no_unplanned_protected_references(candidates)
    with transaction.atomic():
        deleted = _delete_candidates(candidates)
        validate_preserved_state(snapshot)
        _assert_no_remaining_candidates(include_ambiguous_test_data)
    return {
        **manifest,
        "committed": True,
        "deleted": deleted,
        "remaining_candidates": 0,
    }
