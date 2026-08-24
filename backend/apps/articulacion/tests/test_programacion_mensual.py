"""La programación mensual entra por una sola puerta, venga como venga.

Tres clientes escriben hoy el mismo campo `programacion_mensual` con tres formas
incompatibles: el importador de POAUs manda los meses en minúscula, el asistente
POAU del frontend los manda en MAYÚSCULA y el formulario de matriz M3 manda un
array de doce posiciones. Los tres postean a los mismos endpoints.

Estos tests fijan que las tres formas converjan a una sola y que lo que no encaja
se rechace con un mensaje, en vez de entrar mudo y desaparecer después de una
agregación por mes.
"""
import pytest
from rest_framework import serializers

from apps.articulacion.programacion_mensual import MESES, normalizar


class TestFormasQueEscribenLosClientes:
    """Las tres formas reales que hoy llegan a la API."""

    def test_importador_manda_minuscula(self):
        assert normalizar({'enero': 230.0, 'junio': 100.0}) == {
            'enero': 230.0, 'junio': 100.0,
        }

    def test_asistente_poau_manda_mayuscula(self):
        assert normalizar({'ENERO': 230, 'JUNIO': 100}) == {
            'enero': 230, 'junio': 100,
        }

    def test_formulario_m3_manda_lista_de_doce(self):
        lista = [230, None, None, None, None, 100, None, None, None, None,
                 None, None]
        assert normalizar(lista) == {'enero': 230, 'junio': 100}

    def test_las_tres_formas_dan_el_mismo_resultado(self):
        objeto_min = {'enero': 230, 'junio': 100}
        objeto_may = {'ENERO': 230, 'JUNIO': 100}
        lista = [230, None, None, None, None, 100] + [None] * 6
        assert normalizar(objeto_min) == normalizar(objeto_may) == normalizar(lista)


class TestValoresVacios:
    """Una grilla en blanco no deja un objeto de nulos dando vueltas."""

    @pytest.mark.parametrize('vacio', [None, '', {}, [None] * 12])
    def test_sin_datos_queda_en_nulo(self, vacio):
        assert normalizar(vacio) is None

    def test_los_meses_sin_valor_no_ocupan_lugar(self):
        entrada = {mes: None for mes in MESES}
        entrada['marzo'] = 50
        assert normalizar(entrada) == {'marzo': 50}

    def test_numero_escrito_como_texto_se_acepta(self):
        assert normalizar({'Enero': '230.50'}) == {'enero': 230.5}


class TestLoQueSeRechaza:
    """Antes entraba en silencio; ahora falla con un mensaje que se entiende."""

    def test_mes_inventado(self):
        with pytest.raises(serializers.ValidationError) as exc:
            normalizar({'jonuary': 5})
        assert 'no es un mes válido' in str(exc.value)

    def test_lista_de_largo_distinto_a_doce(self):
        with pytest.raises(serializers.ValidationError) as exc:
            normalizar([1] * 11)
        assert 'doce posiciones' in str(exc.value) or '12 posiciones' in str(exc.value)

    def test_texto_suelto(self):
        with pytest.raises(serializers.ValidationError):
            normalizar('enero=5')

    def test_valor_que_no_es_numero(self):
        with pytest.raises(serializers.ValidationError) as exc:
            normalizar({'enero': 'mucho'})
        assert 'debe ser un número' in str(exc.value)

    def test_booleano_no_pasa_por_numero(self):
        with pytest.raises(serializers.ValidationError):
            normalizar({'enero': True})

    def test_el_mismo_mes_con_dos_grafias(self):
        with pytest.raises(serializers.ValidationError) as exc:
            normalizar({'enero': 10, 'ENERO': 20})
        assert 'dos veces' in str(exc.value)


class TestLaAgregacionPorMesYaNoPierdePlata:
    """El defecto que motivó todo esto, fijado como test."""

    def test_lo_guardado_en_mayuscula_suma_al_agrupar_por_minuscula(self):
        # Antes: una fila con 'JUNIO' era ignorada por una consulta que
        # agrupaba por 'junio', y el total bajaba sin dar error.
        guardado = normalizar({'JUNIO': 905})
        assert guardado['junio'] == 905
        assert sum(guardado.values()) == 905

    def test_el_total_no_cambia_al_normalizar(self):
        entrada = {'ENERO': 100, 'FEBRERO': 200, 'MARZO': 300}
        assert sum(normalizar(entrada).values()) == 600
