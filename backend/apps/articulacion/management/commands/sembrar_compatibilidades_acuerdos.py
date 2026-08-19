"""Seed classified agreement compatibilities from the current catalog.

The command deliberately resolves every agreement by ``tipo_acuerdo`` and
``codigo``. It never creates a missing catalog item and never relies on UUIDs
from a particular database.
"""

import re
import unicodedata

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.articulacion.models import (
    AcuerdoInternacional,
    CompatibilidadAcuerdoInternacional,
)


CBD_TARGET_2 = 'https://www.cbd.int/gbf/targets/2/'
CBD_TARGET_3 = 'https://www.cbd.int/gbf/targets/3/'
CBD_TARGET_8 = 'https://www.cbd.int/gbf/targets/8/'
CBD_TARGET_12 = 'https://www.cbd.int/gbf/targets/12/'
CBD_TARGET_14 = 'https://www.cbd.int/gbf/targets/14/'
UNCCD_LDN = 'https://www.unccd.int/land-and-life/land-degradation-neutrality/overview'
SOURCE_VERSION = 'KMGBF 2022 / Agenda 2030 / catálogo vigente'


OFFICIAL_KMGBF_RELATIONS = (
    ('6.6', '2', CBD_TARGET_2, 'Target 2, sección C', 'ODS 6.6 aparece entre los elementos del ODS relacionados con Target 2.'),
    ('6.6', '3', CBD_TARGET_3, 'Target 3, sección C', 'ODS 6.6 aparece entre los elementos del ODS relacionados con Target 3.'),
    ('14.2', '2', CBD_TARGET_2, 'Target 2, sección C', 'ODS 14.2 aparece entre los elementos del ODS relacionados con Target 2.'),
    ('15.1', '2', CBD_TARGET_2, 'Target 2, sección C', 'ODS 15.1 aparece entre los elementos del ODS relacionados con Target 2.'),
    ('15.3', '2', CBD_TARGET_2, 'Target 2, sección C', 'ODS 15.3 aparece entre los elementos del ODS relacionados con Target 2.'),
    ('11.4', '3', CBD_TARGET_3, 'Target 3, sección C', 'ODS 11.4 aparece entre los elementos del ODS relacionados con Target 3.'),
    ('14.5', '3', CBD_TARGET_3, 'Target 3, sección C', 'ODS 14.5 aparece entre los elementos del ODS relacionados con Target 3.'),
    ('15.4', '3', CBD_TARGET_3, 'Target 3, sección C', 'ODS 15.4 aparece entre los elementos del ODS relacionados con Target 3.'),
    ('13.1', '8', CBD_TARGET_8, 'Target 8, sección C', 'ODS 13.1 aparece entre los elementos del ODS relacionados con Target 8.'),
    ('13.2', '8', CBD_TARGET_8, 'Target 8, sección C', 'ODS 13.2 aparece entre los elementos del ODS relacionados con Target 8.'),
    ('14.3', '8', CBD_TARGET_8, 'Target 8, sección C', 'ODS 14.3 aparece entre los elementos del ODS relacionados con Target 8.'),
    ('11.7', '12', CBD_TARGET_12, 'Target 12, sección C', 'ODS 11.7 aparece entre los elementos del ODS relacionados con Target 12.'),
    ('11.b', '12', CBD_TARGET_12, 'Target 12, sección C', 'ODS 11.b aparece entre los elementos del ODS relacionados con Target 12.'),
    ('15.9', '14', CBD_TARGET_14, 'Target 14, sección C', 'ODS 15.9 aparece entre los elementos del ODS relacionados con Target 14.'),
)

SEMANTIC_TOPIC_TERMS = {
    '6': {'agua', 'acuatico', 'ecosistema', 'humedal', 'biodiversidad', 'saneamiento'},
    '11': {'urbano', 'ciudad', 'espacio', 'verde', 'planificacion', 'biodiversidad'},
    '13': {'clima', 'climatico', 'adaptacion', 'resiliencia', 'desastre'},
    '14': {'marino', 'costero', 'oceano', 'pesca', 'biodiversidad', 'ecosistema'},
    '15': {'tierra', 'suelo', 'bosque', 'ecosistema', 'biodiversidad', 'degradacion', 'montana'},
}

STOPWORDS = {
    'para', 'como', 'desde', 'hasta', 'entre', 'sobre', 'hacia', 'segun',
    'esta', 'este', 'estas', 'estos', 'tiene', 'tienen', 'ser', 'una', 'uno',
    'unos', 'unas', 'que', 'los', 'las', 'del', 'por', 'con', 'sin', 'sus',
    'al', 'en', 'de', 'y', 'o', 'a', 'la', 'el', 'se', 'han', 'más', 'mas',
}


def _normalizar(texto):
    texto = unicodedata.normalize('NFKD', str(texto or ''))
    return ''.join(char for char in texto if not unicodedata.combining(char)).lower()


def _tokens(texto):
    return {
        token for token in re.findall(r'[a-záéíóúñ]{4,}', _normalizar(texto))
        if token not in STOPWORDS
    }


class Command(BaseCommand):
    help = 'Siembra compatibilidades clasificadas de acuerdos internacionales por código.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Calcula las relaciones sin persistir cambios.',
        )

    def handle(self, *args, **options):
        self.creadas = 0
        self.actualizadas = 0
        self.omitidas = 0
        self.omisiones = []
        self.dry_run = options['dry_run']

        context = transaction.atomic() if not self.dry_run else _NoopContext()
        with context:
            self._seed_official_kmgbf()
            self._seed_derived_ldn()
            self._seed_semantic_suggestions()

        mode = 'DRY-RUN' if self.dry_run else 'persistido'
        self.stdout.write(self.style.SUCCESS(
            f'Compatibilidades {mode}: {self.creadas} creadas, '
            f'{self.actualizadas} actualizadas, {self.omitidas} omitidas.'
        ))
        for omission in self.omisiones:
            self.stdout.write(self.style.WARNING(f'  OMITIDA: {omission}'))

    def _acuerdo(self, tipo, codigo):
        return AcuerdoInternacional.objects.filter(
            tipo_acuerdo=tipo,
            codigo=codigo,
            activo=True,
        ).first()

    def _resolver_ods(self, codigo_meta):
        """Resolve an ODS target exactly, or conservatively to its goal parent."""
        exacto = self._acuerdo('ODS', codigo_meta)
        if exacto:
            return exacto, False

        if '.' not in codigo_meta:
            return None, False

        objetivo_padre = self._acuerdo('ODS', codigo_meta.split('.', 1)[0])
        return objetivo_padre, bool(objetivo_padre)

    def _seed_official_kmgbf(self):
        for ods_code, target_code, source_url, localizador, evidence in OFFICIAL_KMGBF_RELATIONS:
            origen, usa_fallback = self._resolver_ods(ods_code)
            destino = self._acuerdo('COMPROMISO_3030', target_code)
            if not origen or not destino:
                missing = ', '.join(
                    value for value, item in (
                        (f'ODS:{ods_code} (ni objetivo padre)', origen),
                        (f'COMPROMISO_3030:{target_code}', destino),
                    ) if not item
                )
                self._omit(f'No existe en el catálogo actual: {missing}')
                continue

            if usa_fallback:
                tipo_relacion = CompatibilidadAcuerdoInternacional.TiposRelacion.DERIVADA_DOCUMENTAL
                estado = CompatibilidadAcuerdoInternacional.Estados.CANDIDATA
                confianza = CompatibilidadAcuerdoInternacional.Confianzas.MEDIA
                localizador = (
                    f'{localizador} — meta ODS {ods_code} proyectada al objetivo ODS {origen.codigo}'
                )
                evidence = (
                    f'{evidence} El catálogo local no contiene la meta ODS {ods_code}; '
                    f'se proyecta documentalmente al objetivo ODS {origen.codigo}. '
                    'No es una relación oficial explícita a nivel de objetivo.'
                )
                justificacion = (
                    'Relación documental derivada por falta de un registro local de la meta ODS; '
                    'requiere validación y no debe presentarse como OFICIAL_EXPLICITA.'
                )
            else:
                tipo_relacion = CompatibilidadAcuerdoInternacional.TiposRelacion.OFICIAL_EXPLICITA
                estado = CompatibilidadAcuerdoInternacional.Estados.VALIDADA
                confianza = CompatibilidadAcuerdoInternacional.Confianzas.ALTA
                justificacion = 'Relación oficial explícita del crosswalk ODS–KMGBF solicitado.'

            self._upsert(
                origen=origen,
                destino=destino,
                tipo_relacion=tipo_relacion,
                estado=estado,
                confianza=confianza,
                fuente_url=source_url,
                fuente_titulo='Kunming-Montreal Global Biodiversity Framework — Target',
                fuente_version=SOURCE_VERSION,
                localizador=localizador,
                evidencia=evidence,
                justificacion=justificacion,
            )

    def _seed_derived_ldn(self):
        origen = self._acuerdo('ODS', '15.3')
        if not origen:
            self._omit('No existe ODS:15.3; no se crea el vínculo LDN/NDT.')
            return
        ndt = [
            acuerdo for acuerdo in AcuerdoInternacional.objects.filter(
                tipo_acuerdo='NDT',
                activo=True,
            )
            if {'neutralidad', 'degradacion', 'tierras'} <= _tokens(acuerdo.denominacion)
        ]
        if len(ndt) != 1:
            self._omit(
                'El vínculo LDN/NDT requiere exactamente un NDT del catálogo con '
                'los términos neutralidad, degradación y tierras.'
            )
            return
        self._upsert(
            origen=origen,
            destino=ndt[0],
            tipo_relacion=CompatibilidadAcuerdoInternacional.TiposRelacion.DERIVADA_DOCUMENTAL,
            estado=CompatibilidadAcuerdoInternacional.Estados.VALIDADA,
            confianza=CompatibilidadAcuerdoInternacional.Confianzas.ALTA,
            fuente_url=UNCCD_LDN,
            fuente_titulo='Land Degradation Neutrality — UNCCD',
            fuente_version=SOURCE_VERSION,
            localizador='Overview / definición de LDN',
            evidencia='ODS 15.3 define la neutralidad de la degradación de la tierra; UNCCD define el concepto LDN.',
            justificacion='Vínculo documental entre el concepto internacional ODS 15.3 y el NDT vigente del catálogo; no es una relación nacional explícita del crosswalk.',
        )

    def _seed_semantic_suggestions(self):
        for origen_tipo, destino_tipo in (
            ('ODS', 'NDC'),
            ('ODS', 'NDT'),
            ('NDC', 'NDT'),
            ('NDT', 'COMPROMISO_3030'),
        ):
            origenes = AcuerdoInternacional.objects.filter(
                tipo_acuerdo=origen_tipo,
                activo=True,
            ).order_by('codigo')
            destinos = AcuerdoInternacional.objects.filter(
                tipo_acuerdo=destino_tipo,
                activo=True,
            ).order_by('codigo')
            for origen in origenes:
                source_terms = _tokens(origen.denominacion)
                source_terms |= SEMANTIC_TOPIC_TERMS.get(origen.codigo, set())
                for destino in destinos:
                    overlap = sorted(source_terms & _tokens(destino.denominacion))
                    if not overlap:
                        continue
                    self._upsert(
                        origen=origen,
                        destino=destino,
                        tipo_relacion=CompatibilidadAcuerdoInternacional.TiposRelacion.SUGERENCIA_SEMANTICA,
                        estado=CompatibilidadAcuerdoInternacional.Estados.CANDIDATA,
                        confianza=CompatibilidadAcuerdoInternacional.Confianzas.BAJA,
                        fuente_url='',
                        fuente_titulo='Catálogo vigente — coincidencia temática',
                        fuente_version='Catálogo local vigente',
                        localizador='denominacion',
                        evidencia=f'Palabras/temas coincidentes: {", ".join(overlap)}.',
                        justificacion='Sugerencia semántica generada por coincidencia textual; requiere revisión y no constituye compatibilidad normativa.',
                    )

    def _upsert(self, **values):
        lookup = {
            key: values[key]
            for key in ('origen', 'destino', 'tipo_relacion', 'fuente_url')
        }
        defaults = {
            key: value for key, value in values.items() if key not in lookup
        }
        if self.dry_run:
            self.creadas += 1
            return
        _, created = CompatibilidadAcuerdoInternacional.objects.update_or_create(
            **lookup,
            defaults=defaults,
        )
        if created:
            self.creadas += 1
        else:
            self.actualizadas += 1

    def _omit(self, message):
        self.omitidas += 1
        self.omisiones.append(message)


class _NoopContext:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False
