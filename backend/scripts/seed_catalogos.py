"""
Semilla de catálogos presupuestarios y estructura programática municipal 2026.
Idempotente: python manage.py shell < scripts/seed_catalogos.py
"""
from datetime import date
from apps.catalogos.models import (
    ObjetoGasto, FuenteFinanciamiento, OrganismoFinanciador,
    UnidadMedida, TipoOperacion, TipoProducto
)
from apps.presupuesto.models import ProgramaPresupuestario

GESTION = 2026
VIGENCIA = date(2026, 1, 1)

# === OBJETOS DEL GASTO (partidas presupuestarias) ===
objetos = [
    ('10000', 'SERVICIOS PERSONALES', 'Gastos en personal permanente y eventual'),
    ('20000', 'SERVICIOS NO PERSONALES', 'Servicios básicos, mantenimiento, pasajes'),
    ('30000', 'MATERIALES Y SUMINISTROS', 'Material de escritorio, limpieza, construcción'),
    ('40000', 'ACTIVOS REALES', 'Maquinaria, equipo, vehículos, inmuebles'),
    ('50000', 'ACTIVOS FINANCIEROS', 'Depósitos, fideicomisos, acciones'),
    ('60000', 'SERVICIO DE LA DEUDA', 'Amortización e intereses de deuda'),
    ('70000', 'TRANSFERENCIAS', 'Transferencias corrientes y de capital'),
    ('80000', 'IMPUESTOS Y REGALÍAS', 'Impuestos, regalías y tasas'),
    ('90000', 'OTROS GASTOS', 'Gastos no clasificados anteriormente'),
]
for cod, nom, desc in objetos:
    ObjetoGasto.objects.get_or_create(
        codigo=cod, gestion=GESTION,
        defaults={'denominacion': nom, 'descripcion': desc,
                  'fecha_vigencia_desde': VIGENCIA, 'fuente_normativa': 'Directrices 2026'}
    )

# === FUENTES DE FINANCIAMIENTO ===
fuentes = [
    ('10', 'RECURSOS ESPECÍFICOS', 'Recursos propios municipales'),
    ('20', 'RECURSOS DE COPARTICIPACIÓN', 'Coparticipación tributaria'),
    ('30', 'IDH', 'Impuesto Directo a los Hidrocarburos'),
    ('41', 'DONACIÓN EXTERNA', 'Donaciones de organismos internacionales'),
    ('42', 'DONACIÓN INTERNA', 'Donaciones de entidades nacionales'),
    ('50', 'CRÉDITO EXTERNO', 'Préstamos de organismos internacionales'),
    ('60', 'CRÉDITO INTERNO', 'Préstamos del sistema financiero nacional'),
    ('70', 'TRANSFERENCIAS DEL TGN', 'Transferencias del Tesoro General de la Nación'),
    ('80', 'SALDOS DE CAJA Y BANCOS', 'Saldos de gestiones anteriores'),
]
for cod, nom, desc in fuentes:
    FuenteFinanciamiento.objects.get_or_create(
        codigo=cod, gestion=GESTION,
        defaults={'denominacion': nom, 'descripcion': desc,
                  'fecha_vigencia_desde': VIGENCIA}
    )

# === ORGANISMOS FINANCIADORES ===
organismos = [
    ('111', 'TESORO GENERAL DE LA NACIÓN', 'TGN'),
    ('112', 'GOBIERNO AUTÓNOMO MUNICIPAL', 'Recursos propios municipales'),
    ('211', 'BID', 'Banco Interamericano de Desarrollo'),
    ('212', 'BM', 'Banco Mundial'),
    ('213', 'CAF', 'CAF - Banco de Desarrollo'),
    ('221', 'FNDR', 'Fondo Nacional de Desarrollo Regional'),
    ('310', 'COOPERACIÓN BILATERAL', 'Cooperación de gobiernos extranjeros'),
    ('320', 'COOPERACIÓN MULTILATERAL', 'Cooperación de organismos multilaterales'),
    ('410', 'ONGS', 'Organizaciones No Gubernamentales'),
]
for cod, nom, sig in organismos:
    OrganismoFinanciador.objects.get_or_create(
        codigo=cod, gestion=GESTION,
        defaults={'denominacion': nom, 'descripcion': sig,
                  'fecha_vigencia_desde': VIGENCIA}
    )

# === UNIDADES DE MEDIDA ===
umedidas = [
    ('UN', 'Unidad', 'Unidad'),
    ('PER', 'Persona', 'Persona beneficiaria'),
    ('FAM', 'Familia', 'Familia beneficiaria'),
    ('M2', 'Metro cuadrado', 'Metro cuadrado'),
    ('KM', 'Kilómetro', 'Kilómetro'),
    ('HA', 'Hectárea', 'Hectárea'),
    ('M3', 'Metro cúbico', 'Metro cúbico'),
    ('LT', 'Litros', 'Litros'),
    ('KG', 'Kilogramo', 'Kilogramo'),
    ('TAL', 'Taller', 'Taller realizado'),
    ('CAP', 'Capacitación', 'Evento de capacitación'),
    ('DOC', 'Documento', 'Documento elaborado'),
    ('INF', 'Informe', 'Informe elaborado'),
    ('OBR', 'Obra', 'Obra ejecutada'),
    ('PRO', 'Proyecto', 'Proyecto ejecutado'),
    ('CAM', 'Campaña', 'Campaña realizada'),
    ('VIS', 'Visita', 'Visita realizada'),
    ('POR', 'Porcentaje', 'Porcentaje'),
]
for cod, nom, desc in umedidas:
    UnidadMedida.objects.get_or_create(
        codigo=cod, gestion=GESTION,
        defaults={'denominacion': nom, 'descripcion': desc,
                  'fecha_vigencia_desde': VIGENCIA}
    )

# === TIPOS DE OPERACIÓN ===
tipos_operacion = [
    ('ADM', 'Administración', 'Actividades administrativas'),
    ('TEC', 'Técnica', 'Actividades técnicas especializadas'),
    ('OPE', 'Operativa', 'Actividades operativas de campo'),
    ('CAP', 'Capacitación', 'Actividades de formación y capacitación'),
    ('DIF', 'Difusión', 'Actividades de difusión y comunicación'),
    ('CON', 'Control', 'Actividades de supervisión y control'),
    ('EVA', 'Evaluación', 'Actividades de evaluación y monitoreo'),
    ('MAN', 'Mantenimiento', 'Actividades de mantenimiento'),
]
for cod, nom, desc in tipos_operacion:
    TipoOperacion.objects.get_or_create(
        codigo=cod, gestion=GESTION,
        defaults={'denominacion': nom, 'descripcion': desc,
                  'fecha_vigencia_desde': VIGENCIA}
    )

# === TIPOS DE PRODUCTO ===
tipos_producto = [
    ('BIEN', 'Bien', 'Producto tangible'),
    ('SERV', 'Servicio', 'Prestación de servicio'),
    ('NORMA', 'Norma', 'Instrumento normativo'),
    ('OBRA', 'Obra', 'Infraestructura'),
    ('ESTUDIO', 'Estudio', 'Investigación o diagnóstico'),
    ('EVENTO', 'Evento', 'Actividad puntual'),
]
for cod, nom, desc in tipos_producto:
    TipoProducto.objects.get_or_create(
        codigo=cod, gestion=GESTION,
        defaults={'denominacion': nom, 'descripcion': desc,
                  'fecha_vigencia_desde': VIGENCIA}
    )

# === PROGRAMAS PRESUPUESTARIOS (categorías programáticas municipales) ===
programas = [
    ('10', 'ADMINISTRACIÓN GENERAL', 'Actividades centrales de dirección y administración'),
    ('11', 'ADMINISTRACIÓN TRIBUTARIA', 'Gestión y recaudación de ingresos municipales'),
    ('12', 'FORTALECIMIENTO INSTITUCIONAL', 'Desarrollo organizacional y capacidades'),
    ('20', 'DESARROLLO ECONÓMICO LOCAL', 'Promoción del desarrollo económico'),
    ('21', 'PRODUCCIÓN AGROPECUARIA', 'Fomento a la producción agropecuaria'),
    ('22', 'TURISMO', 'Promoción y desarrollo turístico'),
    ('23', 'DEFENSA DEL CONSUMIDOR', 'Protección de derechos del consumidor'),
    ('30', 'SALUD', 'Servicios de salud municipal'),
    ('31', 'SANEAMIENTO BÁSICO', 'Agua potable y alcantarillado'),
    ('32', 'GESTIÓN DE RESIDUOS SÓLIDOS', 'Limpieza urbana y residuos'),
    ('33', 'RIEGO', 'Sistemas de riego'),
    ('34', 'MEDIO AMBIENTE', 'Gestión ambiental y recursos naturales'),
    ('35', 'RECURSOS HÍDRICOS', 'Gestión de cuencas y agua'),
    ('36', 'GESTIÓN DE RIESGOS', 'Prevención y atención de desastres'),
    ('40', 'EDUCACIÓN', 'Servicios educativos municipales'),
    ('41', 'DEPORTE', 'Promoción deportiva e infraestructura'),
    ('42', 'CULTURA', 'Promoción cultural y patrimonio'),
    ('50', 'INFRAESTRUCTURA URBANA', 'Vías, equipamiento y espacio público'),
    ('51', 'CAMINOS VECINALES', 'Caminos rurales y vecinales'),
    ('52', 'ENERGÍA Y ALUMBRADO PÚBLICO', 'Alumbrado público y energía'),
    ('53', 'CATASTRO', 'Catastro y ordenamiento territorial'),
    ('54', 'TRANSPORTE URBANO', 'Ordenamiento del transporte'),
    ('60', 'SERVICIOS FUNERARIOS Y CEMENTERIOS', 'Administración de cementerios'),
    ('61', 'FAENADO', 'Matadero y control sanitario'),
    ('70', 'SEGURIDAD CIUDADANA', 'Seguridad y protección ciudadana'),
    ('71', 'FELCV', 'Prevención de violencia'),
    ('72', 'PREVENCIÓN DE VIOLENCIA', 'Prevención de violencia y discriminación'),
    ('80', 'DESARROLLO SOCIAL', 'Desarrollo social y comunitario'),
    ('81', 'ATENCIÓN A GRUPOS VULNERABLES', 'Personas con discapacidad, adultos mayores'),
    ('82', 'NIÑEZ Y ADOLESCENCIA', 'Protección de la niñez y adolescencia'),
    ('83', 'PARTICIPACIÓN Y CONTROL SOCIAL', 'Mecanismos de control social'),
    ('90', 'SERVICIO DE LA DEUDA', 'Amortización y servicio de la deuda'),
    ('91', 'RENTA DIGNIDAD', 'Aporte a la Renta Dignidad'),
    ('92', 'ASIGNACIONES OBLIGATORIAS', 'Otras asignaciones legales'),
]
for cod, nom, desc in programas:
    ProgramaPresupuestario.objects.get_or_create(
        codigo=cod, gestion=GESTION,
        defaults={'nombre': nom, 'descripcion': desc}
    )

print(f'Semilla de catálogos {GESTION}:')
print(f'  - {ObjetoGasto.objects.filter(gestion=GESTION).count()} objetos del gasto')
print(f'  - {FuenteFinanciamiento.objects.filter(gestion=GESTION).count()} fuentes')
print(f'  - {OrganismoFinanciador.objects.filter(gestion=GESTION).count()} organismos')
print(f'  - {UnidadMedida.objects.filter(gestion=GESTION).count()} unidades de medida')
print(f'  - {TipoOperacion.objects.filter(gestion=GESTION).count()} tipos de operación')
print(f'  - {TipoProducto.objects.filter(gestion=GESTION).count()} tipos de producto')
print(f'  - {ProgramaPresupuestario.objects.filter(gestion=GESTION).count()} programas')
