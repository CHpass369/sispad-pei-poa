"""Catálogo de secciones del EDTP según tipología RM 115.

Índice dinámico: las secciones se activan/desactivan por tipología,
perfil sectorial y complejidad (RM 115).
"""

SECCIONES_COMUNES = [
    ('01', 'Diagnóstico de la situación actual', True),
    ('02', 'Objetivos generales y específicos', True),
    ('03', 'Estudio de mercado: demanda y oferta', True),
    ('04', 'Tamaño del proyecto', True),
    ('05', 'Localización del proyecto', True),
    ('06', 'Ingeniería del proyecto', True),
    ('07', 'Equipamiento', False),
    ('08', 'Capacitación y asistencia técnica', False),
    ('09', 'Evaluación de impacto ambiental', True),
    ('10', 'Prevención y gestión de riesgos y cambio climático', True),
    ('11', 'Determinación de costos de inversión', True),
    ('12', 'Plan de operación y mantenimiento', True),
    ('13', 'Organización para la implementación', True),
    ('14', 'Evaluación económica', True),
    ('15', 'Evaluación social', False),
    ('16', 'Sostenibilidad operativa', True),
    ('17', 'Análisis de sensibilidad', True),
    ('18', 'Estructura de financiamiento', True),
    ('19', 'Cronograma físico-financiero', True),
    ('20', 'Pliego de especificaciones técnicas', True),
    ('21', 'Conclusiones y recomendaciones', True),
]

SECCIONES_TIPO_IV = [
    ('01', 'Diagnóstico institucional', True),
    ('02', 'Objetivos, componentes y resultados', True),
    ('03', 'Presupuesto de inversión', True),
    ('04', 'Organización para la implementación', True),
    ('05', 'Plan de trabajo y cronograma', True),
    ('06', 'Ingeniería del proyecto, si corresponde', False),
    ('07', 'Equipamiento, si corresponde', False),
    ('08', 'Determinación de costos de inversión', True),
    ('09', 'Pliego de especificaciones técnicas', True),
    ('10', 'Conclusiones y recomendaciones', True),
]

SECCIONES_TIPO_V = [
    ('01', 'Antecedentes', True),
    ('02', 'Justificación de la investigación', True),
    ('03', 'Marco teórico', True),
    ('04', 'Metodología de investigación', True),
    ('05', 'Plan de trabajo', True),
    ('06', 'Cronograma y difusión de resultados', True),
    ('07', 'Presupuesto con memorias de cálculo', True),
    ('08', 'Pertinencia, coherencia y evaluación multicriterio', True),
    ('09', 'Conclusiones y recomendaciones', True),
]

TIPOLOGIA_TIPO_IV = 'IV'
TIPOLOGIA_TIPO_V = 'V'


def secciones_para(tipologia_rm115):
    """Devuelve [(codigo, titulo, requerida)] según la tipología."""
    if tipologia_rm115 == TIPOLOGIA_TIPO_IV:
        return SECCIONES_TIPO_IV
    if tipologia_rm115 == TIPOLOGIA_TIPO_V:
        return SECCIONES_TIPO_V
    return SECCIONES_COMUNES
