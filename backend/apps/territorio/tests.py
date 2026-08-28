"""Padrón maestro de organizaciones territoriales: importación y dominio."""
import json
import os
import tempfile

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.gestion.testing import habilitar_gestion_para_tests
from apps.territorio.management.commands import (
    importar_organizaciones_territoriales as importador,
)
from apps.territorio.models import (
    DirigenteTerritorial, Distrito, TipoUnidadTerritorial, UnidadTerritorial,
    clave_organizacion,
)

User = get_user_model()
DOMINIO = '/api/v1/unidades-territoriales/dominio/'

# Las ocho columnas de `LISTA DE LIMITES DE OTB *.xlsx`, en su orden real.
ENCABEZADOS = ['Nº', 'ORGANIZACIÓN SOCIAL TERRITORIAL', 'NOMBRE DEL DIRIGENTE',
               'CARGO', 'TELEFONO', 'DISTRITO', '¿presento?', 'OBSERVACIONES']


def planilla(filas, hoja='1. Equipamiento'):
    """Arma un libro con la forma exacta que entregan los distritos."""
    import openpyxl

    libro = openpyxl.Workbook()
    ws = libro.active
    ws.title = hoja
    ws.append(['', 'DETALLES'])
    ws.append(ENCABEZADOS)
    for fila in filas:
        ws.append(fila)
    ruta = os.path.join(tempfile.mkdtemp(), 'padron.xlsx')
    libro.save(ruta)
    return ruta


class ClaveOrganizacionTests(TestCase):
    def test_vuelve_a_pegar_las_siglas_punteadas(self):
        # Las dos grafías conviven en las planillas de los doce distritos.
        self.assertEqual(clave_organizacion('O.T.B. VILLA MERCEDES'),
                         clave_organizacion('OTB VILLA MERCEDES'))
        self.assertEqual(clave_organizacion('SUBCENTRAL U.T.C. TEMPORAL BAJO'),
                         'SUBCENTRAL UTC TEMPORAL BAJO')

    def test_una_letra_suelta_al_final_es_parte_del_nombre(self):
        self.assertEqual(clave_organizacion('OTB SAN JOSE B'), 'OTB SAN JOSE B')

    def test_no_traduce_abreviaturas(self):
        # `J.V.` y `JUNTA VECINAL` son la misma organización en la vida real,
        # pero equipararlas sería adivinar: quedan como claves distintas.
        self.assertNotEqual(clave_organizacion('J.V. CAPILLA'),
                            clave_organizacion('JUNTA VECINAL CAPILLA'))


class DeducirTipoTests(TestCase):
    def test_reconoce_las_grafias_de_la_planilla(self):
        # Los doce distritos escriben lo mismo de cuatro formas distintas.
        for nombre, esperado in [
            ('OTB ULINCATE CENTRO', TipoUnidadTerritorial.OTB),
            ('O.T.B. SAN JOSE', TipoUnidadTerritorial.OTB),
            ('OTB. VILLA MERCEDES', TipoUnidadTerritorial.OTB),
            ('JUNTA VECINAL TACOLOMA ALTA', TipoUnidadTerritorial.JUNTA_VECINAL),
            ('J.V. CAPILLA', TipoUnidadTerritorial.JUNTA_VECINAL),
            ('JV EL PROGRESO', TipoUnidadTerritorial.JUNTA_VECINAL),
            ('SINDICATO AGRARIO CHAQUIMAYU', TipoUnidadTerritorial.SINDICATO),
            ('SUBCENTRAL LAVA LAVA', TipoUnidadTerritorial.SUBCENTRAL),
            ('COMUNIDAD LAICACOTA', TipoUnidadTerritorial.COMUNIDAD),
        ]:
            self.assertEqual(importador.deducir_tipo(nombre), esperado, nombre)

    def test_lo_que_no_declara_su_tipo_queda_en_otro(self):
        # 'HUAYLLANI CHICO' no dice qué es: inventarle un tipo sería inventar dato.
        self.assertEqual(importador.deducir_tipo('HUAYLLANI CHICO'),
                         TipoUnidadTerritorial.OTRO)

    def test_otbenal_no_se_confunde_con_otb(self):
        # El prefijo tiene que ser una palabra entera, no un arranque de letras.
        self.assertEqual(importador.deducir_tipo('OTBENAL CENTRAL'),
                         TipoUnidadTerritorial.OTRO)


class LimpiarTelefonoTests(TestCase):
    def test_saca_el_decimal_que_agrega_openpyxl(self):
        self.assertEqual(importador.limpiar_telefono('65376999.0'), '65376999')
        self.assertEqual(importador.limpiar_telefono(None), '')


class ImportarPadronTests(TestCase):
    def setUp(self):
        self.distrito = Distrito.objects.create(codigo='D1', nombre='DISTRITO 1')
        self.archivo = planilla([
            [1, 'JUNTA VECINAL TACOLOMA ALTA', 'JOSE ALMARAZ', 'PRESIDENTE',
             '65376999.0', 'D-1', 'si', ''],
            [2, 'OTB ULINCATE CENTRO', 'GROVER COSSIO', 'PRESIDENTE',
             '72210053.0', 'D-1', 'si', 'SU SELLO LO TENIA SU VICEPRESIDENTE'],
            [3, 'COMUNIDAD LAICACOTA', 'GUIDO ESPINOZA', 'PRESIDENTE',
             '69546699.0', 'D-1', 'si', ''],
            # Las planillas traen cientos de filas en blanco al pie.
            [None, None, None, None, None, None, None, None],
        ])

    def importar(self, **extra):
        call_command('importar_organizaciones_territoriales',
                     archivo=self.archivo, distrito='D1', gestion=2027,
                     verbosity=0, **extra)

    def test_carga_organizaciones_y_dirigentes(self):
        self.importar()
        self.assertEqual(UnidadTerritorial.objects.count(), 3)
        self.assertEqual(DirigenteTerritorial.objects.count(), 3)

        otb = UnidadTerritorial.objects.get(nombre='OTB ULINCATE CENTRO')
        self.assertEqual(otb.distrito, self.distrito)
        self.assertEqual(otb.tipo, TipoUnidadTerritorial.OTB)
        self.assertEqual(otb.nombre_busqueda, 'OTB ULINCATE CENTRO')
        self.assertEqual(otb.dirigente_vigente.nombre, 'GROVER COSSIO')
        self.assertEqual(otb.dirigente_vigente.telefono, '72210053')
        self.assertEqual(otb.dirigente_vigente.gestion, 2027)

    def test_las_filas_en_blanco_no_entran(self):
        self.importar()
        self.assertFalse(UnidadTerritorial.objects.filter(nombre='').exists())

    def test_reimportar_no_duplica_ni_renumera(self):
        # La planilla se corrige y se vuelve a subir: eso no puede duplicar el
        # padrón ni cambiarle el código a quien ya lo tenía.
        self.importar()
        codigos = dict(UnidadTerritorial.objects.values_list('nombre', 'codigo'))
        self.importar()
        self.assertEqual(UnidadTerritorial.objects.count(), 3)
        self.assertEqual(DirigenteTerritorial.objects.count(), 3)
        self.assertEqual(
            dict(UnidadTerritorial.objects.values_list('nombre', 'codigo')),
            codigos)

    def test_una_organizacion_nueva_sigue_la_numeracion(self):
        self.importar()
        self.archivo = planilla([
            [1, 'OTB NUEVA ESPERANZA', 'ANA QUISPE', 'PRESIDENTE', '700.0',
             'D-1', 'si', ''],
        ])
        self.importar()
        nueva = UnidadTerritorial.objects.get(nombre='OTB NUEVA ESPERANZA')
        self.assertEqual(nueva.codigo, 'D1-004')

    def test_la_misma_organizacion_escrita_distinto_no_se_duplica(self):
        self.importar()
        self.archivo = planilla([
            [1, 'O.T.B. ULINCATE CENTRO', 'GROVER COSSIO', 'PRESIDENTE',
             '72210053.0', 'D-1', 'si', ''],
        ])
        self.importar()
        self.assertEqual(
            UnidadTerritorial.objects.filter(
                nombre_busqueda='OTB ULINCATE CENTRO').count(), 1)

    def test_el_padron_del_ano_siguiente_no_pisa_al_anterior(self):
        # El motivo de que el dirigente sea tabla aparte: la dirigencia rota y
        # el acta ya firmada tiene que poder decir quién presidía entonces.
        self.importar()
        self.archivo = planilla([
            [1, 'OTB ULINCATE CENTRO', 'MARIA VARGAS', 'PRESIDENTE', '711.0',
             'D-1', 'si', ''],
        ])
        call_command('importar_organizaciones_territoriales',
                     archivo=self.archivo, distrito='D1', gestion=2028,
                     verbosity=0)
        otb = UnidadTerritorial.objects.get(nombre='OTB ULINCATE CENTRO')
        self.assertEqual(otb.dirigentes.count(), 2)
        self.assertEqual(otb.dirigentes.get(gestion=2027).nombre, 'GROVER COSSIO')
        self.assertEqual(otb.dirigentes.get(gestion=2028).nombre, 'MARIA VARGAS')

    def test_dry_run_no_escribe(self):
        self.importar(dry_run=True)
        self.assertEqual(UnidadTerritorial.objects.count(), 0)

    def test_la_fila_repetida_dentro_de_la_planilla_se_ignora(self):
        self.archivo = planilla([
            [1, 'SUBCENTRAL U.T.C. TEMPORAL BAJO', 'LUIS ROJAS', 'SECRETARIO GENERAL',
             '700.0', 'D-1', 'si', ''],
            [2, 'SUBCENTRAL U.T.C. TEMPORAL BAJO', 'LUIS ROJAS', 'SECRETARIO GENERAL',
             '700.0', 'D-1', 'si', ''],
        ])
        self.importar()
        self.assertEqual(UnidadTerritorial.objects.count(), 1)

    def test_las_filas_sin_numero_son_encabezados_de_seccion(self):
        # Lava Lava no es una lista plana: intercala el nombre de la subcentral
        # sin número y debajo van sus miembros numerados desde 1. El primero de
        # esos encabezados dice «SINDICATOS», que no es ninguna organización.
        self.archivo = planilla([
            [None, 'SINDICATOS', '', '', '', '', '', ''],
            [1, 'SUBCENTRAL U.T.C. TEMPORAL BAJO', 'EDWIN CESPEDES', '', '',
             'LL', '', ''],
            [None, 'SUBCENTRAL EL TEMPORAL (PARTE CENTRO)', '', '', '', '', '', ''],
            [1, 'SINDICATO AGRARIO PIUSILLA', 'FREDDY REVOLLO', '', '', 'LL', '', ''],
        ])
        self.importar()
        self.assertEqual(
            sorted(UnidadTerritorial.objects.values_list('nombre', flat=True)),
            ['SINDICATO AGRARIO PIUSILLA', 'SUBCENTRAL U.T.C. TEMPORAL BAJO'])

    def test_una_planilla_entera_sin_numeros_falla_en_vez_de_vaciarse(self):
        self.archivo = planilla([
            [None, 'OTB SIN NUMERAR', 'ANA QUISPE', 'PRESIDENTE', '', '', '', ''],
        ])
        with self.assertRaises(CommandError):
            self.importar()

    def test_entre_dos_repetidas_gana_la_que_trae_dirigente(self):
        # Si ganara la primera a secas, una fila vacía puesta antes borraría al
        # dirigente y nadie se entera hasta que se emite el acta.
        self.archivo = planilla([
            [1, 'SUBCENTRAL U.T.C. TEMPORAL BAJO', '', '', '', 'LL', '', ''],
            [2, 'SUBCENTRAL U.T.C. TEMPORAL BAJO', 'EDWIN CESPEDES', '', '',
             'LL', '', ''],
        ])
        self.importar()
        self.assertEqual(UnidadTerritorial.objects.count(), 1)
        self.assertEqual(
            UnidadTerritorial.objects.get().dirigente_vigente.nombre,
            'EDWIN CESPEDES')

    def test_sin_dirigente_igual_entra_la_organizacion(self):
        # 114 de las 368 filas del conjunto completo no declaran cargo, y hay
        # celdas de dirigente vacías: la organización existe igual.
        self.archivo = planilla([
            [1, 'OTB SIN DIRIGENTE', '', '', '', 'D-1', '', ''],
        ])
        self.importar()
        self.assertEqual(UnidadTerritorial.objects.count(), 1)
        self.assertEqual(DirigenteTerritorial.objects.count(), 0)

    def test_distrito_inexistente_falla_temprano(self):
        with self.assertRaises(CommandError):
            call_command('importar_organizaciones_territoriales',
                         archivo=self.archivo, distrito='D99', gestion=2027,
                         verbosity=0)

    def test_hoja_inexistente_falla_temprano(self):
        with self.assertRaises(CommandError):
            call_command('importar_organizaciones_territoriales',
                         archivo=self.archivo, distrito='D1', gestion=2027,
                         hoja='NO EXISTE', verbosity=0)


class PadronPortableTests(TestCase):
    """Llevar el padrón a otra base sin mover las planillas Excel."""

    def setUp(self):
        self.origen = Distrito.objects.create(codigo='D1', nombre='DISTRITO 1')
        self.otro = Distrito.objects.create(codigo='DLL', nombre='LAVA LAVA')
        unidad = UnidadTerritorial.objects.create(
            distrito=self.origen, codigo='D1-002', nombre='O.T.B. ULINCATE CENTRO',
            tipo=TipoUnidadTerritorial.OTB)
        DirigenteTerritorial.objects.create(
            unidad=unidad, gestion=2027, nombre='GROVER COSSIO',
            cargo='PRESIDENTE', telefono='72210053')
        DirigenteTerritorial.objects.create(
            unidad=unidad, gestion=2026, nombre='QUIEN ESTABA ANTES',
            cargo='PRESIDENTE', telefono='')
        UnidadTerritorial.objects.create(
            distrito=self.otro, codigo='DLL-001', nombre='SUBCENTRAL LAVA LAVA',
            tipo=TipoUnidadTerritorial.SUBCENTRAL)
        self.salida = os.path.join(tempfile.mkdtemp(), 'padron.json')

    def exportar(self, **extra):
        call_command('exportar_padron_territorial', salida=self.salida,
                     verbosity=0, **extra)
        with open(self.salida, encoding='utf-8') as archivo:
            return json.load(archivo)

    def test_el_distrito_viaja_por_codigo_y_no_por_id(self):
        # El id no puede viajar: se genera por base. Es todo el motivo por el
        # que `dumpdata` no sirve para esta tabla.
        datos = self.exportar()
        codigos = {o['distrito'] for o in datos['organizaciones']}
        self.assertEqual(codigos, {'D1', 'DLL'})
        volcado = json.dumps(datos)
        self.assertNotIn(str(self.origen.id), volcado)

    def test_carga_en_una_base_cuyos_distritos_tienen_otro_uuid(self):
        # Esto reproduce el servidor: mismos códigos, ids distintos.
        datos = self.exportar()
        viejos = {self.origen.id, self.otro.id}
        UnidadTerritorial.objects.all().delete()
        Distrito.objects.all().delete()
        Distrito.objects.create(codigo='D1', nombre='DISTRITO 1')
        Distrito.objects.create(codigo='DLL', nombre='LAVA LAVA')
        self.assertFalse(viejos & set(Distrito.objects.values_list('id', flat=True)))

        call_command('importar_padron_territorial', archivo=self.salida, verbosity=0)
        self.assertEqual(UnidadTerritorial.objects.count(), 2)
        unidad = UnidadTerritorial.objects.get(nombre='O.T.B. ULINCATE CENTRO')
        self.assertEqual(unidad.distrito.codigo, 'D1')
        self.assertEqual(unidad.codigo, 'D1-002')
        self.assertEqual(unidad.dirigente_vigente.nombre, 'GROVER COSSIO')
        self.assertEqual(unidad.dirigentes.count(), 2)

    def test_cargarlo_dos_veces_no_duplica(self):
        self.exportar()
        call_command('importar_padron_territorial', archivo=self.salida, verbosity=0)
        call_command('importar_padron_territorial', archivo=self.salida, verbosity=0)
        self.assertEqual(UnidadTerritorial.objects.count(), 2)
        # Los dos dirigentes de ULINCATE: el de 2027 y el de 2026.
        self.assertEqual(DirigenteTerritorial.objects.count(), 2)

    def test_un_distrito_que_no_existe_corta_antes_de_escribir(self):
        # Una carga a medias es peor que ninguna: nadie sabría qué distritos
        # quedaron adentro. Acá D1 sí existe y podría cargarse, pero como falta
        # DLL no se escribe una sola fila.
        self.exportar()
        UnidadTerritorial.objects.all().delete()
        self.otro.delete()
        with self.assertRaises(CommandError):
            call_command('importar_padron_territorial', archivo=self.salida,
                         verbosity=0)
        self.assertEqual(UnidadTerritorial.objects.count(), 0)

    def test_se_puede_exportar_sin_telefonos(self):
        datos = self.exportar(sin_telefonos=True)
        telefonos = {d['telefono'] for o in datos['organizaciones']
                     for d in o['dirigentes']}
        self.assertEqual(telefonos, {''})

    def test_filtrar_por_gestion_deja_solo_esos_dirigentes(self):
        datos = self.exportar(gestion=2027)
        gestiones = {d['gestion'] for o in datos['organizaciones']
                     for d in o['dirigentes']}
        self.assertEqual(gestiones, {2027})

    def test_un_json_de_otra_version_se_rechaza(self):
        with open(self.salida, 'w', encoding='utf-8') as archivo:
            json.dump({'version': 99, 'organizaciones': [{}]}, archivo)
        with self.assertRaises(CommandError):
            call_command('importar_padron_territorial', archivo=self.salida,
                         verbosity=0)

    def test_dry_run_no_escribe(self):
        self.exportar()
        UnidadTerritorial.objects.all().delete()
        call_command('importar_padron_territorial', archivo=self.salida,
                     dry_run=True, verbosity=0)
        self.assertEqual(UnidadTerritorial.objects.count(), 0)


class DominioApiTests(TestCase):
    def setUp(self):
        habilitar_gestion_para_tests(2027)
        self.d1 = Distrito.objects.create(codigo='D1', nombre='DISTRITO 1')
        self.d2 = Distrito.objects.create(codigo='D2', nombre='DISTRITO 2')
        self.otb = UnidadTerritorial.objects.create(
            distrito=self.d1, codigo='D1-001', nombre='OTB ULINCATE CENTRO',
            tipo=TipoUnidadTerritorial.OTB)
        DirigenteTerritorial.objects.create(
            unidad=self.otb, gestion=2027, nombre='GROVER COSSIO',
            cargo='PRESIDENTE', telefono='72210053')
        UnidadTerritorial.objects.create(
            distrito=self.d2, codigo='D2-001', nombre='OTB VILLA MERCEDES',
            tipo=TipoUnidadTerritorial.OTB)

        self.cliente = APIClient()
        self.cliente.force_authenticate(
            User.objects.create_user(email='t@test.com', password='x12345678'))

    def test_devuelve_la_organizacion_con_su_dirigente_vigente(self):
        r = self.cliente.get(DOMINIO, {'distrito': str(self.d1.id)})
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data['total'], 1)
        fila = r.data['resultados'][0]
        self.assertEqual(fila['nombre'], 'OTB ULINCATE CENTRO')
        self.assertEqual(fila['dirigente'], 'GROVER COSSIO')
        self.assertEqual(fila['telefono'], '72210053')

    def test_filtra_por_distrito(self):
        r = self.cliente.get(DOMINIO, {'distrito': str(self.d2.id)})
        self.assertEqual([f['nombre'] for f in r.data['resultados']],
                         ['OTB VILLA MERCEDES'])

    def test_sin_paginar_devuelve_el_padron_entero(self):
        # El formulario necesita la lista completa para resolver la selección
        # sin volver al servidor; el distrito más grande tiene 79.
        for i in range(40):
            UnidadTerritorial.objects.create(
                distrito=self.d1, codigo=f'D1-1{i:02d}',
                nombre=f'OTB PRUEBA {i}', tipo=TipoUnidadTerritorial.OTB)
        r = self.cliente.get(DOMINIO, {'distrito': str(self.d1.id)})
        self.assertEqual(r.data['total'], 41)

    def test_el_dirigente_de_otra_gestion_no_se_muestra(self):
        # Sin padrón del año, el campo llega vacío y lo escribe el técnico.
        # Mostrar el presidente del año pasado sería peor que no mostrar nada.
        DirigenteTerritorial.objects.all().update(gestion=2026)
        r = self.cliente.get(DOMINIO, {'distrito': str(self.d1.id)})
        self.assertEqual(r.data['resultados'][0]['dirigente'], '')

    def test_busca_sin_tildes_ni_puntuacion(self):
        r = self.cliente.get(DOMINIO, {'q': 'o.t.b. ulincate'})
        self.assertEqual(r.data['total'], 1)

    def test_la_organizacion_dada_de_baja_no_aparece(self):
        self.otb.activa = False
        self.otb.save()
        r = self.cliente.get(DOMINIO, {'distrito': str(self.d1.id)})
        self.assertEqual(r.data['total'], 0)
