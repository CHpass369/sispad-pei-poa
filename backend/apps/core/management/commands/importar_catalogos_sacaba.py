"""
Management command para importar los catálogos oficiales del GAM Sacaba
para la gestión 2027.

Carga:
    - Versión oficial y vigente del clasificador (fuentes de financiamiento
      y organismos financiadores) según el Clasificador Presupuestario MEFP 2027.
    - Fuentes de financiamiento y organismos financiadores oficiales.
    - Distritos reales del municipio de Sacaba.
    - Secretarías (unidades organizacionales), direcciones administrativas
      y unidades ejecutoras de la estructura del GAM Sacaba.

Idempotente: puede ejecutarse varias veces sin duplicar registros.

Uso:
    python manage.py importar_catalogos_sacaba --gestion=2027
    python manage.py importar_catalogos_sacaba --gestion=2027 \\
        --clasificadores-pdf="/ruta/CLASIFICADORES 2027.pdf"
"""
import hashlib
import os
from datetime import date

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.catalogos.models import (
    VersionClasificador, FuenteFinanciamiento, OrganismoFinanciador,
)
from apps.gestion.models import GestionFiscal
from apps.gestion.services import crear_gestion
from apps.organizacion.models import (
    TipoUnidad, UnidadOrganizacional, DireccionAdministrativa,
    UnidadEjecutora,
)

# apps.territorio requiere PostGIS y no está en settings_test_sqlite, donde
# su módulo ni siquiera puede importarse; la carga de distritos es opcional.
if 'apps.territorio' in settings.INSTALLED_APPS:
    from apps.territorio.models import Distrito
else:
    Distrito = None

NORMA = 'RM N° 271 de 31/07/2026 - Directrices de Formulación Presupuestaria 2027'
FECHA_NORMA = date(2026, 7, 31)
CODIGO_FUENTE_VERSION = 'CLASIFICADORES-PRESUPUESTARIOS-2027-MEFP'
PROCEDENCIA_NORMATIVA = (
    'Ministerio de Economía y Finanzas Públicas - '
    'Clasificadores Presupuestarios Gestión 2027'
)
METADATOS_IMPORTACION = {
    'fuente': 'clasificadores-mefp-2027',
    'norma': 'RM N° 271',
}

FUENTES_FINANCIAMIENTO = [
    ('10', 'Tesoro General de la Nación'),
    ('11', 'T.G.N. Otros Ingresos'),
    ('20', 'Recursos Específicos'),
    ('41', 'Transferencias T.G.N.'),
    ('42', 'Transferencias de Recursos Específicos'),
    ('43', 'Transferencias de Crédito Externo'),
    ('44', 'Transferencias de Donación Externa'),
    ('45', 'Transferencias de Crédito Interno'),
    ('46', 'Transferencias T.G.N. Otros Ingresos'),
    ('47', 'Transferencia de Donación Interna'),
    ('70', 'Crédito Externo'),
    ('80', 'Donación Externa'),
    ('87', 'Donación Interna'),
    ('90', 'Crédito Interno'),
    ('91', 'Préstamos T.G.N.'),
    ('92', 'Préstamos de Recursos Específicos'),
    ('93', 'Préstamos de Crédito Externo'),
    ('94', 'Préstamos de Donación Externa'),
    ('95', 'Préstamos de Crédito Interno'),
    ('96', 'Préstamos T.G.N. Otros Ingresos'),
    ('97', 'Préstamos de Donación Interna'),
]

ORGANISMOS_FINANCIADORES = [
    ('111', 'Tesoro General de la Nación'),
    ('113', 'Tesoro General de la Nación - Coparticipación Tributaria'),
    ('119', 'Tesoro General de la Nación - Impuesto Directo a los Hidrocarburos'),
    ('120', 'Tesoro General de la Nación - Impuesto a la Participación en Juegos'),
    ('210', 'Recursos Específicos de los Gobiernos Autónomos Municipales e Indígena Originario Campesino'),
    ('220', 'Regalías'),
    ('230', 'Otros Recursos Específicos'),
    ('314', 'Corporación Andina de Fomento'),
    ('411', 'Banco Interamericano de Desarrollo'),
    ('413', 'Fondo Financiero para el Desarrollo de la Cuenca del Plata'),
    ('515', 'Agencia Suiza para el Desarrollo y la Cooperación'),
]

DISTRITOS = [
    ('D1', 'DISTRITO 1'),
    ('D2', 'DISTRITO 2'),
    ('D3', 'DISTRITO 3'),
    ('D4', 'DISTRITO 4'),
    ('D5', 'DISTRITO 5'),
    ('D6', 'DISTRITO 6'),
    ('D7', 'DISTRITO 7'),
    ('DA', 'DISTRITO AGUIRRE'),
    ('DCH', 'DISTRITO CHIÑATA'),
    ('DP', 'DISTRITO PALCA'),
    ('DU', 'DISTRITO UCUCHI'),
    ('DLL', 'DISTRITO LAVA LAVA'),
]

SECRETARIAS = [
    ('STAFF-MAE', 'STAFF MAE', 'Staff de Alcaldía'),
    ('CM', 'CM', 'Concejo Municipal'),
    ('SMFA', 'SMFA', 'Secretaría Municipal de Finanzas y Administración'),
    ('SMPDT', 'SMPDT', 'Secretaría Municipal de Planificación y Desarrollo Territorial'),
    ('SMMTyDP', 'SMMTyDP', 'Secretaría Municipal de Medio Ambiente y Desarrollo Productivo'),
    ('SMIS', 'SMIS', 'Secretaría Municipal de Infraestructura y Servicios'),
    ('SMDHI', 'SMDHI', 'Secretaría Municipal de Desarrollo Humano Integral'),
    ('SMS', 'SMS', 'Secretaría Municipal de Salud'),
]

DIRECCIONES_ADMINISTRATIVAS = [
    ('1', 'SECRETARIA DE ADMINISTRACION Y FINANZAS'),
    ('2', 'HOSPITAL DE SEGUNDO NIVEL MEXICO'),
    ('3', 'ADMINISTRACION CONCEJO MUNICIPAL'),
    ('4', 'HOSPITAL DE SEGUNDO NIVEL SOLOMON KLEIN'),
    ('5', 'SECRETARIA DE INFRAESTRUCTURA Y SERVICIOS'),
]

UNIDADES_EJECUTORAS = [
    ('1', '1', 'SECRETARIA MUNICIPAL DE FINANZAS Y ADMINISTRACION'),
    ('2', '2', 'HOSPITAL DE SEGUNDO NIVEL MEXICO'),
    ('3', '1', 'SECRETARIA MUNICIPAL DE PLANIFICACION Y DESARROLLO TERRITORIAL'),
    ('4', '1', 'SECRETARIA MUNICIPAL DE INFRAESTRUCTURA Y SERVICIOS'),
    ('5', '1', 'SECRETARIA MUNICIPAL DE DESARROLLO HUMANO INTEGRAL'),
    ('6', '3', 'CONCEJO MUNICIPAL'),
    ('7', '1', 'SECRETARIA MUNICIPAL DE MEDIO AMBIENTE Y DESARROLLO PRODUCTIVO'),
    ('10', '2', 'HOSPITAL DE SEGUNDO NIVEL MEXICO - AREA DE SALUD'),
    ('11', '4', 'HOSPITAL DE SEGUNDO NIVEL SOLOMON KLEIN - AREA DE SALUD'),
    ('12', '5', 'SECRETARIA MUNICIPAL DE INFRAESTRUCTURA - AREA DE SALUD'),
    ('13', '1', 'STAFF DE ALCALDIA'),
]


class Command(BaseCommand):
    help = (
        'Importa los catálogos oficiales del GAM Sacaba (clasificadores '
        'presupuestarios MEFP 2027, distritos y estructura organizacional)'
    )

    def add_arguments(self, parser):
        parser.add_argument('--gestion', type=int, default=2027,
                            help='Gestión fiscal a importar (default: 2027)')
        parser.add_argument(
            '--clasificadores-pdf', required=False, default='',
            help='Ruta al PDF de clasificadores presupuestarios 2027; '
                 'su SHA-256 se usa como hash_fuente de la versión oficial',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        gestion_anio = options['gestion']
        self.stdout.write(self.style.NOTICE(
            f'=== INICIO IMPORTACIÓN CATÁLOGOS GAM SACABA (gestión {gestion_anio}) ==='
        ))

        # 1. Gestión fiscal
        gestion = self._crear_gestion(gestion_anio)

        # 2. Versiones oficiales y vigentes del clasificador
        hash_fuente = self._hash_fuente(options['clasificadores_pdf'])
        version_fuentes = self._crear_version(
            VersionClasificador.TIPO_FUENTE_FINANCIAMIENTO, gestion_anio,
            hash_fuente,
        )
        version_organismos = self._crear_version(
            VersionClasificador.TIPO_ORGANISMO_FINANCIADOR, gestion_anio,
            hash_fuente,
        )

        # 3. Fuentes de financiamiento
        self._importar_fuentes(gestion_anio, version_fuentes)

        # 4. Organismos financiadores
        self._importar_organismos(gestion_anio, version_organismos)

        # 5. Distritos
        self._importar_distritos()

        # 6. Secretarías (unidades organizacionales)
        self._importar_secretarias(gestion)

        # 7. Direcciones administrativas
        das = self._importar_direcciones(gestion)

        # 8. Unidades ejecutoras
        self._importar_ues(gestion, das)

        self.stdout.write(self.style.SUCCESS(
            f'Importación de catálogos completada exitosamente (gestión {gestion_anio})'
        ))

    # ============================================================
    # 1. GESTIÓN FISCAL
    # ============================================================
    def _crear_gestion(self, gestion_anio):
        gestion = GestionFiscal.objects.filter(anio=gestion_anio).first()
        if gestion:
            self.stdout.write(
                f'[1/8] Gestión fiscal {gestion_anio} ya existía (se reutiliza).'
            )
            return gestion
        gestion = crear_gestion(gestion_anio)
        self.stdout.write(self.style.SUCCESS(
            f'[1/8] Gestión fiscal {gestion_anio} creada.'
        ))
        return gestion

    # ============================================================
    # 2. VERSIONES DEL CLASIFICADOR
    # ============================================================
    def _hash_fuente(self, ruta_pdf):
        if ruta_pdf:
            if not os.path.isfile(ruta_pdf):
                raise CommandError(
                    f'No se encontró el archivo de clasificadores: {ruta_pdf}'
                )
            with open(ruta_pdf, 'rb') as fh:
                return hashlib.sha256(fh.read()).hexdigest()
        # Sin PDF: hash del propio código de la versión (64 hex, estable).
        return hashlib.sha256(CODIGO_FUENTE_VERSION.encode()).hexdigest()

    def _crear_version(self, tipo, gestion_anio, hash_fuente):
        version, creada = VersionClasificador.objects.update_or_create(
            tipo=tipo,
            gestion=gestion_anio,
            vigente=True,
            defaults={
                'norma': NORMA,
                'fecha_norma': FECHA_NORMA,
                'codigo_fuente': CODIGO_FUENTE_VERSION,
                'procedencia_normativa': PROCEDENCIA_NORMATIVA,
                'clasificacion_fuente': VersionClasificador.FUENTE_OFICIAL,
                'vigente': True,
                'hash_fuente': hash_fuente,
            },
        )
        accion = 'creada' if creada else 'actualizada'
        self.stdout.write(
            f'[2/8] Versión {tipo} {gestion_anio} {accion} '
            f'(vigente, oficial, hash {version.hash_fuente[:12]}…).'
        )
        return version

    # ============================================================
    # 3. FUENTES DE FINANCIAMIENTO
    # ============================================================
    def _importar_fuentes(self, gestion_anio, version):
        creadas = actualizadas = 0
        for codigo, denominacion in FUENTES_FINANCIAMIENTO:
            _, creada = FuenteFinanciamiento.objects.update_or_create(
                codigo=codigo, gestion=gestion_anio,
                defaults={
                    'denominacion': denominacion,
                    'version_clasificador': version,
                    'fecha_vigencia_desde': date(gestion_anio, 1, 1),
                    'activo': True,
                    'metadatos_importacion': METADATOS_IMPORTACION,
                },
            )
            if creada:
                creadas += 1
            else:
                actualizadas += 1
        self.stdout.write(
            f'[3/8] Fuentes de financiamiento: {creadas} creadas, '
            f'{actualizadas} actualizadas (total {len(FUENTES_FINANCIAMIENTO)}).'
        )

    # ============================================================
    # 4. ORGANISMOS FINANCIADORES
    # ============================================================
    def _importar_organismos(self, gestion_anio, version):
        creados = actualizados = 0
        for codigo, denominacion in ORGANISMOS_FINANCIADORES:
            _, creado = OrganismoFinanciador.objects.update_or_create(
                codigo=codigo, gestion=gestion_anio,
                defaults={
                    'denominacion': denominacion,
                    'version_clasificador': version,
                    'fecha_vigencia_desde': date(gestion_anio, 1, 1),
                    'activo': True,
                    'metadatos_importacion': METADATOS_IMPORTACION,
                },
            )
            if creado:
                creados += 1
            else:
                actualizados += 1
        self.stdout.write(
            f'[4/8] Organismos financiadores: {creados} creados, '
            f'{actualizados} actualizados (total {len(ORGANISMOS_FINANCIADORES)}).'
        )

    # ============================================================
    # 5. DISTRITOS
    # ============================================================
    def _importar_distritos(self):
        if Distrito is None:
            self.stdout.write(self.style.WARNING(
                '[5/8] apps.territorio no está disponible en este settings '
                '(requiere PostGIS); se omite la carga de distritos.'
            ))
            return
        creados = actualizados = 0
        for codigo, nombre in DISTRITOS:
            _, creado = Distrito.objects.update_or_create(
                codigo=codigo,
                defaults={'nombre': nombre},
            )
            if creado:
                creados += 1
            else:
                actualizados += 1
        self.stdout.write(
            f'[5/8] Distritos: {creados} creados, '
            f'{actualizados} actualizados (total {len(DISTRITOS)}).'
        )

    # ============================================================
    # 6. SECRETARÍAS (UNIDADES ORGANIZACIONALES)
    # ============================================================
    def _importar_secretarias(self, gestion):
        gestion_anio = gestion.anio
        tipo_sec, _ = TipoUnidad.objects.get_or_create(
            codigo='SEC', defaults={'nombre': 'Secretaría', 'nivel': 1},
        )
        TipoUnidad.objects.get_or_create(
            codigo='DIR', defaults={'nombre': 'Dirección', 'nivel': 2},
        )
        TipoUnidad.objects.get_or_create(
            codigo='UNI', defaults={'nombre': 'Unidad', 'nivel': 3},
        )
        creadas = actualizadas = 0
        for codigo, sigla, nombre in SECRETARIAS:
            _, creada = UnidadOrganizacional.objects.update_or_create(
                codigo=codigo, gestion=gestion,
                defaults={
                    'nombre': nombre,
                    'sigla': sigla,
                    'tipo': tipo_sec,
                    'fecha_vigencia_desde': date(gestion_anio, 1, 1),
                    'activo': True,
                },
            )
            if creada:
                creadas += 1
            else:
                actualizadas += 1
        self.stdout.write(
            f'[6/8] Secretarías: {creadas} creadas, '
            f'{actualizadas} actualizadas (total {len(SECRETARIAS)}).'
        )

    # ============================================================
    # 7. DIRECCIONES ADMINISTRATIVAS
    # ============================================================
    def _importar_direcciones(self, gestion):
        gestion_anio = gestion.anio
        das = {}
        creadas = actualizadas = 0
        for codigo, nombre in DIRECCIONES_ADMINISTRATIVAS:
            da, creada = DireccionAdministrativa.objects.update_or_create(
                codigo=codigo, gestion=gestion,
                defaults={
                    'nombre': nombre,
                    'fecha_vigencia_desde': date(gestion_anio, 1, 1),
                    'activo': True,
                },
            )
            das[codigo] = da
            if creada:
                creadas += 1
            else:
                actualizadas += 1
        self.stdout.write(
            f'[7/8] Direcciones administrativas: {creadas} creadas, '
            f'{actualizadas} actualizadas (total {len(DIRECCIONES_ADMINISTRATIVAS)}).'
        )
        return das

    # ============================================================
    # 8. UNIDADES EJECUTORAS
    # ============================================================
    def _importar_ues(self, gestion, das):
        gestion_anio = gestion.anio
        creadas = actualizadas = 0
        for codigo, da_codigo, nombre in UNIDADES_EJECUTORAS:
            _, creada = UnidadEjecutora.objects.update_or_create(
                codigo=codigo, da=das[da_codigo], gestion=gestion,
                defaults={
                    'nombre': nombre,
                    'fecha_vigencia_desde': date(gestion_anio, 1, 1),
                    'activo': True,
                },
            )
            if creada:
                creadas += 1
            else:
                actualizadas += 1
        self.stdout.write(
            f'[8/8] Unidades ejecutoras: {creadas} creadas, '
            f'{actualizadas} actualizadas (total {len(UNIDADES_EJECUTORAS)}).'
        )
