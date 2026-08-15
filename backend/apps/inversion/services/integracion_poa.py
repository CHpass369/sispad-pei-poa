"""Contrato de dominio SIS-PRO -> SIS-POA (ADR-002 / ADR-010).

SIS-PRO (apps.inversion) consume el SIS-POA como sistema externo: lee
actividades de la jerarquía canónica de poau (PoA institucional -> Acción de
corto plazo -> Operación -> Actividad, ADR-002) y vincula proyectos a
actividades mediante `VinculoProyectoActividad`, modelo propio de SIS-PRO.

Reglas del contrato:
- SIS-PRO NUNCA escribe en tablas internas de poau / articulacion / budget:
  las escrituras de este módulo ocurren solo en modelos de apps.inversion.
- Las lecturas de poau se hacen únicamente por los métodos expuestos aquí.
- El paquete de transferencia (JSON + GeoJSON + documentos) es el punto único
  de exportación hacia SIS-POA (plan maestro §26 y §48), reutilizando
  `construir_paquete_transferencia` de services_preinversion.
"""
from django.core.exceptions import ValidationError

from apps.inversion.models_v2 import VinculoProyectoActividad
from apps.poau.models_v2 import Actividad

from ..services_preinversion import construir_paquete_transferencia


class IntegracionPoaContract:
    """Contrato explícito de cómo SIS-PRO consume SIS-POA.

    Solo lectura de poau; toda escritura ocurre en modelos propios de
    inversion (VinculoProyectoActividad). No se tocan internals del SIS-POA.
    """

    def actividades_poa_disponibles(self, gestion):
        """Actividades del SIS-POA de una gestión, disponibles para vincular.

        Devuelve una lista de dicts con id, codigo, denominacion (nombre) y
        unidad (id de la UnidadOrganizacional responsable). No escribe en poau.
        """
        return [
            {
                'id': str(a.id),
                'codigo': a.codigo,
                'denominacion': a.nombre,
                'unidad': a.operacion.unidad_id,
            }
            for a in Actividad.objects.filter(
                operacion__accion__poa__gestion=gestion,
            ).select_related('operacion')
        ]

    def vincular_proyecto_a_actividad(self, proyecto, actividad_id, usuario=None):
        """Vincula un proyecto de SIS-PRO a una actividad del SIS-POA.

        Valida que la actividad exista (ValidationError con mensaje claro),
        crea el `VinculoProyectoActividad` (modelo propio de inversion) y
        devuelve el vínculo. Idempotente: si el vínculo ya existe, lo devuelve.
        `usuario` es el responsable de la acción (reservado para la auditoría
        de PIP INTEGRACIÓN, fase futura); el modelo no persiste al autor.
        """
        try:
            actividad = Actividad.objects.get(pk=actividad_id)
        except Actividad.DoesNotExist:
            raise ValidationError(
                f'La actividad {actividad_id} del SIS-POA no existe.'
            )
        vinculo, _ = VinculoProyectoActividad.objects.get_or_create(
            proyecto=proyecto, actividad=actividad,
        )
        return vinculo

    def proyectos_de_actividad(self, actividad_id):
        """Vínculos (con proyecto) de una actividad del SIS-POA. Lectura pura."""
        return (
            VinculoProyectoActividad.objects
            .filter(actividad_id=actividad_id)
            .select_related('proyecto')
        )

    def paquete_transferencia_poa(self, proyecto):
        """Paquete de solo lectura hacia SIS-POA (JSON + GeoJSON + documentos).

        Delega en `construir_paquete_transferencia` de services_preinversion
        (única fuente del paquete; plan maestro §26 y §48).
        """
        return construir_paquete_transferencia(proyecto)
