"""Carga los rangos de programa que fija la directriz de formulación.

Transcripción del Anexo VI, sección IV —Estructura Programática de Gastos de
los Gobiernos Autónomos Municipales e Indígena Originario Campesinos— de las
Directrices de Formulación Presupuestaria, aprobadas por Resolución Ministerial
N° 271 del 31 de julio de 2026.

Es catálogo normativo: se siembra desde la norma y no se edita a mano. Si el
Ministerio cambia la estructura, se agrega la gestión nueva y la anterior queda
como estaba.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.budget.models import RangoProgramaDirectriz

NORMA = 'RM 271/2026 - Directrices de Formulación Presupuestaria 2027'

# (desde, hasta, denominación, finalidad y función, sector económico)
MUNICIPAL = [
    (0, 0, 'FUNCIONAMIENTO ÓRGANO EJECUTIVO', '1.1.1', '14'),
    (1, 1, 'FUNCIONAMIENTO ÓRGANO DELIBERATIVO', '1.1.1', '14'),
    (2, 9, 'ADMINISTRACIÓN CENTRAL', '1.1.1', '14'),
    (100, 109, 'PROMOCIÓN Y FOMENTO A LA PRODUCCIÓN AGROPECUARIA',
     '4.2; 10.9.1', '1'),
    (110, 119, 'SANEAMIENTO BÁSICO', '5.2; 6.3', '10'),
    (120, 129, 'CONSTRUCCIÓN Y MANTENIMIENTO DE RIEGO Y/O MICRORIEGO',
     '4.2.1', '1'),
    (130, 139, 'DESARROLLO Y PRESERVACIÓN DEL MEDIO AMBIENTE', '5', '19'),
    (140, 149, 'ASEO URBANO, MANEJO Y TRATAMIENTO DE RESIDUOS SÓLIDOS',
     '5.1', '10'),
    (150, 159, 'FUENTES DE ENERGÍA Y APOYO A LA ELECTRIFICACIÓN',
     '4.3.5; 4.3.6', '5'),
    (160, 169, 'SERVICIO DE ALUMBRADO PÚBLICO', '6.4', '11'),
    (170, 179, 'INFRAESTRUCTURA URBANA Y RURAL', '4.4.3; 4.5.1; 6.1', '11'),
    (180, 189, 'GESTIÓN DE CAMINOS VECINALES', '4.5.1', '6'),
    (190, 199, 'SERVICIO DE CATASTRO URBANO Y RURAL', '6.1; 6.2; 4.9', '11'),
    (200, 209, 'GESTIÓN DE SALUD',
     '7; 10.4.1; 10.4.2; 10.9.1; 10.9.2', '8'),
    (210, 219, 'GESTIÓN DE EDUCACIÓN', '9; 10.9.1; 10.9.2', '9'),
    (220, 229, 'DESARROLLO Y PROMOCIÓN DEL DEPORTE', '8.1; 8.6; 10.9.1', '24'),
    (230, 239, 'PROMOCIÓN Y CONSERVACIÓN DE CULTURA Y PATRIMONIO',
     '8.2; 8.6; 10.9.1; 8.7', '22'),
    (240, 249, 'DESARROLLO Y FOMENTO DEL TURISMO',
     '4.7.1; 4.7.2; 4.7.3; 10.9.1; 4.7.6', '20'),
    (250, 259, 'PROMOCIÓN Y POLÍTICAS PARA GRUPOS VULNERABLES Y DE LA MUJER',
     '10.9.1; 10.9.2; 10.1; 10.2; 10.4.1; 10.4.2', '21; 23'),
    # La directriz singulariza el 251 dentro del rango anterior.
    (251, 251, 'PROMOCIÓN Y POLÍTICAS PARA GRUPOS VULNERABLES Y DE LA MUJER - '
     'PREVENCIÓN CONTRA LA VIOLENCIA HACIA LA MUJER', '10.9.1', '23.1.5'),
    (260, 269, 'DEFENSA Y PROTECCIÓN DE LA NIÑEZ Y ADOLESCENCIA',
     '10.4.1; 10.4.2; 10.9.1; 10.9.2', '21; 23'),
    (270, 279, 'VIALIDAD Y TRANSPORTE PÚBLICO', '4.5.1', '6'),
    (280, 289, 'DEFENSA DEL CONSUMIDOR', '4.1.1; 4.7.1', '13'),
    (290, 299, 'SERVICIO DE FAENADO DE GANADO', '4.2.4; 4.9', '1'),
    (300, 309, 'SERVICIO DE INHUMACIÓN, EXHUMACIÓN, CREMACIÓN Y TRASLADO DE '
     'RESTOS', '6.1; 6.2', '11'),
    (310, 319, 'GESTIÓN DE RIESGOS', '10.10; 5.7', '12; 16'),
    (320, 329, 'RECURSOS HÍDRICOS', '6.3', '12'),
    (330, 339, 'SERVICIOS DE SEGURIDAD CIUDADANA', '3; 10.9.1; 10.9.2', '15'),
    (340, 349, 'FORTALECIMIENTO INSTITUCIONAL', '1.1.1; 6.2', '18'),
    (350, 359, 'FOMENTO AL DESARROLLO ECONÓMICO LOCAL Y PROMOCIÓN DEL EMPLEO',
     '4.1; 4.4.2; 10.9.1', '3; 13'),
    (360, 890, 'OTROS PROGRAMAS ESPECÍFICOS', '', ''),
    (97, 97, 'PARTIDAS NO ASIGNABLES A PROGRAMAS - ACTIVOS FINANCIEROS '
     '(GRUPO 50000, OBJETO DEL GASTO 99100 Y OTRAS PREVISIONES)',
     '1.1.2', '14'),
    (98, 98, 'PARTIDAS NO ASIGNABLES A PROGRAMAS - TRANSFERENCIAS '
     '(GRUPO 70000)', '1.8', '14'),
    (99, 99, 'PARTIDAS NO ASIGNABLES A PROGRAMAS - DEUDAS (GRUPO 60000)',
     '1.7', '17'),
]

# La directriz lo dice expresamente: del 10 al 96 no se apropian ni se utilizan.
PROHIBIDO_DESDE, PROHIBIDO_HASTA = 10, 96


class Command(BaseCommand):
    help = 'Siembra los rangos de programa de la directriz de formulación.'

    def add_arguments(self, parser):
        parser.add_argument('--gestion', type=int, required=True)
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **opciones):
        gestion = opciones['gestion']
        if opciones['dry_run']:
            self.stdout.write(self.style.WARNING(
                f'[dry-run] {len(MUNICIPAL)} rangos para {gestion}, '
                'sin escribir.'))
            return
        self._guardar(gestion)

    @transaction.atomic
    def _guardar(self, gestion):
        creados = actualizados = 0
        for desde, hasta, denominacion, fin_fun, sector in MUNICIPAL:
            _, nuevo = RangoProgramaDirectriz.objects.update_or_create(
                gestion=gestion,
                nivel_entidad=RangoProgramaDirectriz.NIVEL_MUNICIPAL,
                desde=desde, hasta=hasta,
                defaults={
                    'denominacion': denominacion,
                    'finalidad_funcion': fin_fun,
                    'sector_economico': sector,
                    'normativa': NORMA,
                },
            )
            creados += nuevo
            actualizados += not nuevo
        self.stdout.write(self.style.SUCCESS(
            f'Directriz {gestion}: {creados} rangos creados, '
            f'{actualizados} actualizados.'))
