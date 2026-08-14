"""Auditable, deterministic, and idempotent migration of SIM-2027 codes."""
from __future__ import annotations

import hashlib
import json
import os
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q

from apps.articulacion.models import (
    AccionPOA,
    ActividadPOAU,
    LineamientoPAD as LineamientoPADLegacy,
    OperacionPOAU,
    ProductoPAD,
    ProductoPEI,
    ResultadoPAD,
    ResultadoPEI,
    TareaPOAU,
)
from apps.codificacion.models import (
    EjecucionMigracionSIM,
    EntidadCodificadora,
    HomologacionCodigo,
    LineamientoPAD,
    MapeoLineamientoPADLegacy,
    SecuenciaCodigo,
)
from apps.codificacion.services.codificador import CodificadorService
from apps.pad.models import LineamientoEstrategico


class MigracionSIMService:
    """Plan and execute the SIM migration without inventing official sources."""

    VERSION_MANIFIESTO = 1
    MOTIVO = 'Migración controlada SIM-2027 a código numérico PROVISIONAL'
    SIM_PREFIX = 'SIM-'
    SPECS = (
        ('resultado_pad', ResultadoPAD, 'codigo_resultado', None),
        ('producto_pad', ProductoPAD, 'codigo_producto', 'resultado_pad'),
        ('resultado_pei', ResultadoPEI, 'codigo_resultado', None),
        ('producto_pei', ProductoPEI, 'codigo_producto', 'resultado_pei'),
        ('accion_poa', AccionPOA, 'codigo_accion', 'producto_pei'),
        ('operacion_poau', OperacionPOAU, 'codigo_operacion', 'accion_poa'),
        ('actividad_poau', ActividadPOAU, 'codigo_actividad', 'operacion'),
        ('tarea_poau', TareaPOAU, 'codigo_tarea', 'actividad'),
    )
    SPEC_BY_LEVEL = {spec[0]: spec for spec in SPECS}

    def __init__(self, *, gestion=2027, usuario=None):
        if not isinstance(gestion, int) or isinstance(gestion, bool) or gestion < 1:
            raise ValidationError({'gestion': 'La gestión debe ser un entero positivo.'})
        self.gestion = gestion
        self.usuario = usuario

    @staticmethod
    def _texto_normalizado(value):
        value = unicodedata.normalize('NFKC', str(value or ''))
        return re.sub(r'\s+', ' ', value).strip().casefold()

    def _queryset(self, level, model, legacy_field):
        source_filter = Q(**{f'{legacy_field}__startswith': self.SIM_PREFIX}) | Q(
            codigo_fuente__startswith=self.SIM_PREFIX,
        )
        if level in {'resultado_pad', 'resultado_pei'}:
            scope = Q(vigencia_desde=self.gestion)
        elif level == 'producto_pad':
            scope = Q(resultado_pad__vigencia_desde=self.gestion)
        elif level == 'producto_pei':
            scope = Q(resultado_pei__vigencia_desde=self.gestion)
        elif level == 'accion_poa':
            scope = Q(gestion=self.gestion)
        elif level == 'operacion_poau':
            scope = Q(accion_poa__gestion=self.gestion)
        elif level == 'actividad_poau':
            scope = Q(operacion__accion_poa__gestion=self.gestion)
        else:
            scope = Q(actividad__operacion__accion_poa__gestion=self.gestion)
        return model.objects.filter(source_filter, scope)

    @staticmethod
    def _source_code(row, legacy_field):
        source = row.codigo_fuente or getattr(row, legacy_field)
        if not source.startswith(MigracionSIMService.SIM_PREFIX):
            raise ValidationError({
                'codigo_fuente': f'{row.pk} no conserva un código fuente SIM.',
            })
        return source

    def _gestion_row(self, row):
        contexto = CodificadorService._contexto(row)
        return CodificadorService._gestion(contexto)

    @staticmethod
    def _parent_id(row, parent_field):
        return getattr(row, f'{parent_field}_id') if parent_field else None

    def _sequence_base(self, level, parent_id, entidad):
        sequence = SecuenciaCodigo.objects.filter(
            nivel=level,
            padre_id=parent_id,
            gestion=self.gestion,
            entidad=entidad,
        ).first()
        return sequence.ultimo_valor if sequence else 0

    def _plan_entries(self):
        entidad = EntidadCodificadora.objects.filter(
            codigo=CodificadorService.ENTIDAD_CODIFICADORA,
            activo=True,
        ).first()
        if entidad is None:
            raise ValidationError({'entidad': 'No existe la entidad activa 1312.'})

        entries = []
        target_by_id = {}
        for level, model, legacy_field, parent_field in self.SPECS:
            rows = list(self._queryset(level, model, legacy_field))
            rows.sort(key=lambda row: (
                str(self._parent_id(row, parent_field) or ''),
                self._source_code(row, legacy_field),
                str(row.pk),
            ))
            groups = defaultdict(list)
            for row in rows:
                groups[self._parent_id(row, parent_field)].append(row)

            for parent_id in sorted(groups, key=lambda value: str(value or '')):
                grouped_rows = groups[parent_id]
                existing_values = {
                    row.correlativo for row in grouped_rows if row.correlativo is not None
                }
                base = self._sequence_base(level, parent_id, entidad)
                if existing_values and base < max(existing_values):
                    raise ValidationError({
                        'secuencia': (
                            f'La secuencia {level}/{parent_id} está detrás de los '
                            'correlativos persistidos.'
                        ),
                    })
                next_value = base
                for row in grouped_rows:
                    if row.correlativo is None:
                        next_value += 1
                        correlativo = next_value
                    else:
                        correlativo = row.correlativo
                    segmento = CodificadorService.normalizar(
                        self._segment_name(level), correlativo,
                    )
                    target = self._target_code(
                        level=level,
                        row=row,
                        segmento=segmento,
                        target_by_id=target_by_id,
                        entidad=entidad,
                    )
                    source = self._source_code(row, legacy_field)
                    current = getattr(row, legacy_field)
                    warnings = self._row_warnings(level, row)
                    fully_applied = (
                        current == target
                        and row.codigo_fuente == source
                        and row.correlativo == correlativo
                        and row.segmento == segmento
                        and row.codigo_normalizado == segmento
                        and row.estado_codigo == row.ESTADO_CODIGO_PROVISIONAL
                    )
                    hierarchy = self._hierarchy(row)
                    entry = {
                        'nivel': level,
                        'modelo': model.__name__,
                        'id': str(row.pk),
                        'padre_id': str(parent_id) if parent_id else None,
                        'codigo_anterior': source,
                        'codigo_actual': current,
                        'codigo_nuevo': target,
                        'correlativo': correlativo,
                        'segmento': segmento,
                        'jerarquia': hierarchy,
                        'warnings': warnings,
                        'estado_aplicacion': 'aplicado' if fully_applied else 'pendiente',
                    }
                    entries.append(entry)
                    target_by_id[row.pk] = target
        return entries

    @staticmethod
    def _segment_name(level):
        return {
            'resultado_pad': 'RT',
            'producto_pad': 'PT',
            'resultado_pei': 'RI',
            'producto_pei': 'PI',
            'accion_poa': 'ACP',
            'operacion_poau': 'OP',
            'actividad_poau': 'ACT',
            'tarea_poau': 'TAR',
        }[level]

    def _target_code(self, *, level, row, segmento, target_by_id, entidad):
        if level == 'resultado_pad':
            return segmento
        if level == 'producto_pad':
            return f'{target_by_id[row.resultado_pad_id]}.{segmento}'
        if level == 'resultado_pei':
            return f'{entidad.codigo}.{segmento}'
        if level == 'producto_pei':
            return f'{target_by_id[row.resultado_pei_id]}.{segmento}'
        if level == 'accion_poa':
            return f'{self.gestion}.{entidad.codigo}.{segmento}'
        parent_field = self.SPEC_BY_LEVEL[level][3]
        return f'{target_by_id[getattr(row, f"{parent_field}_id")]}.{segmento}'

    @staticmethod
    def _hierarchy(row):
        contexto = CodificadorService._contexto(row)
        return [
            {'nivel': key, 'id': str(value.pk)}
            for key, value in contexto.items()
            if key != 'articulacion_ambigua' and value is not None
        ]

    @staticmethod
    def _row_warnings(level, row):
        warnings = []
        contexto = CodificadorService._contexto(row)
        resultado_pad = contexto['resultado_pad']
        resultado_pei = contexto['resultado_pei']
        if resultado_pad is None:
            warnings.append('PAD_FALTANTE_FK_NULL')
        elif (
            resultado_pad.resultado_sectorial_catalogo_id is None
            or resultado_pad.entidad_territorial_cgeo_id is None
            or resultado_pad.lineamiento_pad_catalogo_id is None
        ):
            warnings.append('CATALOGOS_NACIONALES_PAD_INCOMPLETOS')
        if resultado_pei is not None and not str(resultado_pei.cod_oei).isdigit():
            warnings.append('OE_SIN_FUENTE_CONFIABLE')
        if contexto['articulacion_ambigua']:
            warnings.append('ARTICULACION_PAD_PEI_AMBIGUA')
        if level in {'accion_poa', 'operacion_poau', 'actividad_poau', 'tarea_poau'}:
            warnings.append('ANCHO_OPERATIVO_INSTITUCIONAL_NO_NORMATIVO')
        return warnings

    def _lineamiento_entries(self):
        entries = []
        legacy_sets = (
            (
                MapeoLineamientoPADLegacy.ORIGEN_ARTICULACION,
                LineamientoPADLegacy.objects.filter(
                    gestion_desde__lte=self.gestion,
                    gestion_hasta__gte=self.gestion,
                ),
                'denominacion',
            ),
            (
                MapeoLineamientoPADLegacy.ORIGEN_PAD,
                LineamientoEstrategico.objects.filter(gestion=self.gestion),
                'nombre',
            ),
        )
        for origin, queryset, name_field in legacy_sets:
            for legacy in queryset.order_by('codigo', 'pk'):
                name = getattr(legacy, name_field)
                candidates = [
                    item for item in LineamientoPAD.objects.filter(
                        codigo=legacy.codigo,
                        version_catalogo__gestion=self.gestion,
                    ).order_by('pk')
                    if self._texto_normalizado(item.denominacion)
                    == self._texto_normalizado(name)
                ]
                status = (
                    'mapeable' if len(candidates) == 1
                    else 'ambiguo' if len(candidates) > 1
                    else 'sin_correspondencia'
                )
                entries.append({
                    'origen': origin,
                    'legacy_id': str(legacy.pk),
                    'codigo': legacy.codigo,
                    'denominacion': name,
                    'estado': status,
                    'canonico_id': str(candidates[0].pk) if len(candidates) == 1 else None,
                    'candidatos': [str(item.pk) for item in candidates],
                })
        return entries

    @classmethod
    def _hash_payload(cls, manifest):
        entries = []
        for entry in manifest['entradas']:
            entries.append({
                key: value for key, value in entry.items()
                if key not in {'codigo_actual', 'estado_aplicacion'}
            })
        return {
            'version': manifest['version'],
            'gestion': manifest['gestion'],
            'entradas': entries,
            'lineamientos': manifest['lineamientos']['entradas'],
        }

    @classmethod
    def _calculate_hash(cls, manifest):
        payload = json.dumps(
            cls._hash_payload(manifest),
            ensure_ascii=False,
            sort_keys=True,
            separators=(',', ':'),
        ).encode('utf-8')
        return hashlib.sha256(payload).hexdigest()

    def construir_manifiesto(self):
        entries = self._plan_entries()
        lineamientos = self._lineamiento_entries()
        counts = Counter(entry['nivel'] for entry in entries)
        manifest = {
            'version': self.VERSION_MANIFIESTO,
            'gestion': self.gestion,
            'estado_codigo_destino': 'provisional',
            'entradas': entries,
            'lineamientos': {
                'entradas': lineamientos,
                'mapeables': sum(item['estado'] == 'mapeable' for item in lineamientos),
                'ambiguos': sum(item['estado'] == 'ambiguo' for item in lineamientos),
                'sin_correspondencia': sum(
                    item['estado'] == 'sin_correspondencia' for item in lineamientos
                ),
            },
            'resumen': {
                'registros': len(entries),
                'cambios_planificados': sum(
                    entry['estado_aplicacion'] == 'pendiente' for entry in entries
                ),
                'por_nivel': {
                    level: counts[level] for level, *_ in self.SPECS
                },
                'warnings': sum(len(entry['warnings']) for entry in entries),
            },
        }
        manifest['manifest_hash'] = self._calculate_hash(manifest)
        return manifest

    @classmethod
    def verificar_hash(cls, manifest):
        return manifest.get('manifest_hash') == cls._calculate_hash(manifest)

    @staticmethod
    def persistir_manifiesto(manifest, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(f'{path.suffix}.tmp-{os.getpid()}')
        data = json.dumps(
            manifest,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        ) + '\n'
        try:
            fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
            os.chmod(path, 0o600)
        finally:
            if temporary.exists():
                temporary.unlink()

    def auditar(self):
        manifest = self.construir_manifiesto()
        EjecucionMigracionSIM.objects.create(
            gestion=self.gestion,
            modo=EjecucionMigracionSIM.MODO_DRY_RUN,
            manifest_hash=manifest['manifest_hash'],
            manifest=manifest,
            cambios_planificados=manifest['resumen']['cambios_planificados'],
            warnings=manifest['resumen']['warnings'],
            usuario=self.usuario,
        )
        return manifest

    def _lock_manifest_rows(self, manifest):
        by_level = defaultdict(list)
        for entry in manifest['entradas']:
            by_level[entry['nivel']].append(entry['id'])
        for level, model, *_ in self.SPECS:
            list(model.objects.select_for_update().filter(
                pk__in=by_level[level],
            ).order_by('pk'))

    def _apply_entry(self, entry, entidad, manifest_hash):
        level, model, legacy_field, parent_field = self.SPEC_BY_LEVEL[entry['nivel']]
        row = model.objects.select_related().get(pk=entry['id'])
        current_source = self._source_code(row, legacy_field)
        if current_source != entry['codigo_anterior']:
            raise ValidationError({'codigo_fuente': 'El código fuente cambió tras el dry-run.'})

        if entry['estado_aplicacion'] == 'aplicado':
            return False, False

        if row.correlativo is None:
            emitted = CodificadorService.siguiente_correlativo(
                level,
                self._parent_id(row, parent_field),
                self.gestion,
                entidad,
            )
            if emitted != entry['correlativo']:
                raise ValidationError({
                    'secuencia': 'El correlativo emitido difiere del manifiesto aprobado.',
                })
            row.correlativo = emitted
        elif row.correlativo != entry['correlativo']:
            raise ValidationError({'correlativo': 'El correlativo cambió tras el dry-run.'})

        row.codigo_fuente = entry['codigo_anterior']
        row.segmento = entry['segmento']
        row.codigo_normalizado = entry['segmento']
        row.estado_codigo = row.ESTADO_CODIGO_PROVISIONAL
        setattr(row, legacy_field, entry['codigo_nuevo'])
        update_fields = [
            legacy_field,
            'codigo_fuente',
            'correlativo',
            'segmento',
            'codigo_normalizado',
            'estado_codigo',
        ]
        if isinstance(row, ResultadoPEI):
            row.cod_entidad = entidad.codigo
            row.entidad_codificadora = entidad
            if not str(row.cod_oei).isdigit():
                row.cod_oei = ''
            update_fields.extend(['cod_entidad', 'entidad_codificadora', 'cod_oei'])

        CodificadorService.generar_codigo_completo(row)
        update_fields.extend(['codigo_completo_articulacion', 'articulacion_incompleta'])
        row.save(update_fields=[*update_fields, 'updated_at'])

        _, created = HomologacionCodigo.objects.get_or_create(
            tipo_entidad=level,
            entidad_id=row.pk,
            codigo_nuevo=entry['codigo_nuevo'],
            defaults={
                'codigo_anterior': entry['codigo_anterior'],
                'motivo': self.MOTIVO,
                'gestion': self.gestion,
                'usuario': self.usuario,
                'documento_respaldo': 'Manifiesto SHA-256 ' + manifest_hash,
            },
        )
        return True, created

    def _consolidar_lineamientos(self, manifest):
        created = 0
        existing = 0
        for entry in manifest['lineamientos']['entradas']:
            if entry['estado'] != 'mapeable':
                continue
            _, was_created = MapeoLineamientoPADLegacy.objects.get_or_create(
                origen=entry['origen'],
                legacy_id=entry['legacy_id'],
                defaults={
                    'codigo_legacy': entry['codigo'],
                    'denominacion_legacy': entry['denominacion'],
                    'lineamiento_pad_id': entry['canonico_id'],
                    'manifest_hash': manifest['manifest_hash'],
                    'usuario': self.usuario,
                },
            )
            created += was_created
            existing += not was_created
        return {'mapeos_creados': created, 'mapeos_existentes': existing}

    @transaction.atomic
    def consolidar_lineamientos(self):
        return self._consolidar_lineamientos(self.construir_manifiesto())

    @transaction.atomic
    def ejecutar(self, *, expected_hash, backup):
        if self.usuario is None or not getattr(self.usuario, 'pk', None):
            raise ValidationError({'usuario': 'El usuario responsable es obligatorio.'})
        if not backup or not backup.get('restore_validated'):
            raise ValidationError({'backup': 'El dump debe superar una restauración validada.'})
        if not re.fullmatch(r'[0-9a-f]{64}', str(backup.get('sha256', ''))):
            raise ValidationError({'backup': 'El dump requiere SHA-256 válido.'})

        manifest = self.construir_manifiesto()
        if manifest['manifest_hash'] != expected_hash:
            raise ValidationError({'hash': 'El hash del manifiesto no coincide.'})
        self._lock_manifest_rows(manifest)
        locked_manifest = self.construir_manifiesto()
        if locked_manifest['manifest_hash'] != expected_hash:
            raise ValidationError({'hash': 'Los datos cambiaron después del dry-run.'})

        entidad = EntidadCodificadora.objects.select_for_update().get(
            codigo=CodificadorService.ENTIDAD_CODIFICADORA,
            activo=True,
        )
        applied = 0
        homologations = 0
        for entry in locked_manifest['entradas']:
            changed, homologated = self._apply_entry(
                entry, entidad, expected_hash,
            )
            applied += changed
            homologations += homologated
        lineamientos = self._consolidar_lineamientos(locked_manifest)

        EjecucionMigracionSIM.objects.create(
            gestion=self.gestion,
            modo=EjecucionMigracionSIM.MODO_COMMIT,
            manifest_hash=expected_hash,
            manifest=locked_manifest,
            cambios_planificados=locked_manifest['resumen']['cambios_planificados'],
            cambios_aplicados=applied,
            homologaciones_creadas=homologations,
            mapeos_lineamiento_creados=lineamientos['mapeos_creados'],
            warnings=locked_manifest['resumen']['warnings'],
            backup_path=str(backup['path']),
            backup_sha256=backup['sha256'],
            backup_restore_validated=True,
            usuario=self.usuario,
        )
        return {
            'manifest_hash': expected_hash,
            'cambios_aplicados': applied,
            'homologaciones_creadas': homologations,
            **lineamientos,
        }
