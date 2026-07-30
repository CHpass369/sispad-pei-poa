"""Tests del mixin abstracto CodigoSegmentadoModel (T2.1).

El mixin concentra los campos de codificación oficial segmentada que se
aplican a los 8 modelos operativos de articulación. La generación del
código completo (16 segmentos) es responsabilidad del CodificadorService
(T3); aquí solo se verifica la estructura de campos, los defaults y la
generación del segmento propio del nivel con zfill.
"""
import pytest
from django.core.exceptions import ValidationError
from django.db import models

from apps.codificacion.models import CodigoSegmentadoModel


class TestEstructuraDelMixin:
    """Campos y metadatos que el mixin debe aportar a cada modelo concreto."""

    def test_es_modelo_abstracto(self):
        assert CodigoSegmentadoModel._meta.abstract is True

    def test_hereda_timestamped(self):
        """Los modelos concretos conservan created_at/updated_at del core."""
        nombres = {f.name for f in CodigoSegmentadoModel._meta.fields}
        assert {'created_at', 'updated_at'} <= nombres

    def test_correlativo_es_positive_integer_nullable(self):
        campo = CodigoSegmentadoModel._meta.get_field('correlativo')
        assert isinstance(campo, models.PositiveIntegerField)
        # Nullable: los registros vivos SIM-2027 aún no tienen correlativo.
        assert campo.null is True

    def test_segmento_es_charfield_en_blanco(self):
        campo = CodigoSegmentadoModel._meta.get_field('segmento')
        assert isinstance(campo, models.CharField)
        assert campo.blank is True
        assert campo.default == ''

    def test_codigo_fuente_preserva_original(self):
        campo = CodigoSegmentadoModel._meta.get_field('codigo_fuente')
        assert isinstance(campo, models.CharField)
        assert campo.blank is True
        assert campo.max_length >= 50  # ej. 'SIM-2027-OP-01'

    def test_codigo_normalizado_existe_en_blanco(self):
        campo = CodigoSegmentadoModel._meta.get_field('codigo_normalizado')
        assert isinstance(campo, models.CharField)
        assert campo.blank is True

    def test_codigo_completo_no_editable_y_en_blanco(self):
        """El código completo lo escribe SOLO el backend (T3); nunca el frontend."""
        campo = CodigoSegmentadoModel._meta.get_field('codigo_completo_articulacion')
        assert campo.editable is False
        assert campo.blank is True
        # 16 segmentos con separadores: 57 chars; margen razonable.
        assert campo.max_length >= 57

    def test_estado_codigo_default_provisional(self):
        campo = CodigoSegmentadoModel._meta.get_field('estado_codigo')
        assert campo.default == CodigoSegmentadoModel.ESTADO_CODIGO_PROVISIONAL

    def test_estado_codigo_choices_provisional_u_oficial(self):
        valores = {valor for valor, _ in CodigoSegmentadoModel.ESTADO_CODIGO_CHOICES}
        assert valores == {
            CodigoSegmentadoModel.ESTADO_CODIGO_PROVISIONAL,
            CodigoSegmentadoModel.ESTADO_CODIGO_OFICIAL,
        }


class NivelDePrueba(CodigoSegmentadoModel):
    """Subclase mínima para probar la lógica pura del mixin (sin tabla)."""

    ANCHO_SEGMENTO = 3

    class Meta:
        abstract = True


class NivelDePrueba2Digitos(CodigoSegmentadoModel):
    ANCHO_SEGMENTO = 2

    class Meta:
        abstract = True


class TestGenerarSegmento:
    """generar_segmento: correlativo -> str con zfill según ancho del nivel."""

    def test_nivel_3_digitos_rellena_con_ceros(self):
        assert NivelDePrueba.generar_segmento(7) == '007'

    def test_nivel_3_digitos_conserva_tres_cifras(self):
        assert NivelDePrueba.generar_segmento(123) == '123'

    def test_nivel_2_digitos_rellena_con_ceros(self):
        assert NivelDePrueba2Digitos.generar_segmento(7) == '07'

    def test_nivel_2_digitos_conserva_dos_cifras(self):
        assert NivelDePrueba2Digitos.generar_segmento(12) == '12'

    def test_mixin_sin_ancho_declarado_falla(self):
        """El mixin exige que cada nivel concrete su ANCHO_SEGMENTO."""
        with pytest.raises(NotImplementedError):
            CodigoSegmentadoModel.generar_segmento(1)

    @pytest.mark.parametrize(
        'nivel,correlativo,esperado',
        [
            (NivelDePrueba2Digitos, 1, '01'),
            (NivelDePrueba2Digitos, 99, '99'),
            (NivelDePrueba, 1, '001'),
            (NivelDePrueba, 999, '999'),
        ],
    )
    def test_limites_validos_producen_ancho_exacto(
        self, nivel, correlativo, esperado,
    ):
        segmento = nivel.generar_segmento(correlativo)

        assert segmento == esperado
        assert len(segmento) == nivel.ANCHO_SEGMENTO

    @pytest.mark.parametrize(
        'nivel,correlativo',
        [
            (NivelDePrueba2Digitos, 0),
            (NivelDePrueba2Digitos, -1),
            (NivelDePrueba2Digitos, 100),
            (NivelDePrueba, 0),
            (NivelDePrueba, -1),
            (NivelDePrueba, 1000),
            (NivelDePrueba, True),
            (NivelDePrueba, '7'),
            (NivelDePrueba, 7.0),
        ],
    )
    def test_rechaza_valores_fuera_del_dominio(self, nivel, correlativo):
        with pytest.raises(ValidationError):
            nivel.generar_segmento(correlativo)

    @pytest.mark.parametrize('nivel', [NivelDePrueba2Digitos, NivelDePrueba])
    def test_none_representa_legacy_aun_no_codificado(self, nivel):
        assert nivel.generar_segmento(None) == ''
