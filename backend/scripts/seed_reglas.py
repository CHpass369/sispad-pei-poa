"""
Semilla de reglas presupuestarias legales.
Idempotente: python manage.py shell < scripts/seed_reglas.py
"""
from apps.normativa.models import ReglaPresupuestariaLegal

reglas = [
    {
        'codigo': 'limite_gasto_funcionamiento',
        'nombre': 'Límite de gasto de funcionamiento',
        'descripcion': 'Los gastos de funcionamiento no pueden superar el 60% del presupuesto total asignado al municipio, según normativa vigente.',
        'tipo': 'limite',
        'severidad': 'bloqueante',
        'parametros': {'porcentaje': 0.60, 'base_calculo': 'presupuesto_total'},
        'condicion_aplicabilidad': 'Aplica a todas las gestiones con presupuesto definido',
        'gestion_desde': 2024,
        'fuente_normativa': 'Ley N.º 482 GAMs, Directrices de Formulación Presupuestaria',
        'mensaje': 'El gasto de funcionamiento (Bs {gasto_funcionamiento}) supera el límite legal del {porcentaje}% del presupuesto total (Bs {limite}). Debe reducir el gasto de funcionamiento o ajustar la clasificación presupuestaria.',
    },
    {
        'codigo': 'no_superar_techo',
        'nombre': 'No superar techo presupuestario',
        'descripcion': 'El monto formulado no puede superar el techo presupuestario asignado a la unidad o programa.',
        'tipo': 'limite',
        'severidad': 'bloqueante',
        'parametros': {},
        'condicion_aplicabilidad': 'Aplica a toda formulación con techo asignado',
        'gestion_desde': 2024,
        'fuente_normativa': 'NB SPO, Directrices de Formulación',
        'mensaje': 'El monto formulado supera el techo asignado. Debe reducir el presupuesto solicitado o solicitar una redistribución de techo.',
    },
    {
        'codigo': 'consistencia_anual_plurianual',
        'nombre': 'Consistencia anual/plurianual',
        'descripcion': 'El presupuesto anual debe ser consistente con la programación plurianual, con una tolerancia del 5%.',
        'tipo': 'consistencia',
        'severidad': 'advertencia',
        'parametros': {'tolerancia': 0.05},
        'condicion_aplicabilidad': 'Aplica cuando existe programación plurianual registrada',
        'gestion_desde': 2024,
        'fuente_normativa': 'Directrices de Formulación Presupuestaria',
        'mensaje': 'El presupuesto anual difiere en más del {tolerancia}% de la programación plurianual. Verifique la consistencia entre ambos.',
    },
    {
        'codigo': 'gasto_sus',
        'nombre': 'Asignación obligatoria SUS',
        'descripcion': 'El municipio debe asignar al menos el 10% de su presupuesto al Sistema Único de Salud (SUS).',
        'tipo': 'minimo',
        'severidad': 'bloqueante',
        'parametros': {'porcentaje': 0.10},
        'condicion_aplicabilidad': 'Aplica cuando existan servicios de salud municipal',
        'gestion_desde': 2024,
        'fuente_normativa': 'Ley N.º 1152, Decreto Supremo N.º 3471',
        'mensaje': 'La asignación al SUS (Bs {asignado}) es inferior al {porcentaje}% mínimo requerido del presupuesto total (Bs {minimo}). Debe incrementar la asignación.',
    },
    {
        'codigo': 'renta_dignidad',
        'nombre': 'Asignación obligatoria Renta Dignidad',
        'descripcion': 'El municipio debe aportar el 0.75% de sus recursos para la Renta Dignidad.',
        'tipo': 'minimo',
        'severidad': 'bloqueante',
        'parametros': {'porcentaje': 0.0075},
        'condicion_aplicabilidad': 'Aplica a todos los municipios',
        'gestion_desde': 2024,
        'fuente_normativa': 'Ley N.º 3791 Renta Dignidad',
        'mensaje': 'El aporte a la Renta Dignidad es inferior al {porcentaje}% requerido del presupuesto.',
    },
    {
        'codigo': 'seguridad_ciudadana',
        'nombre': 'Asignación obligatoria Seguridad Ciudadana',
        'descripcion': 'El municipio debe asignar al menos el 10% de sus recursos para seguridad ciudadana.',
        'tipo': 'minimo',
        'severidad': 'bloqueante',
        'parametros': {'porcentaje': 0.10},
        'condicion_aplicabilidad': 'Aplica a todos los municipios',
        'gestion_desde': 2024,
        'fuente_normativa': 'Ley N.º 264 Seguridad Ciudadana',
        'mensaje': 'La asignación a seguridad ciudadana es inferior al {porcentaje}% mínimo requerido.',
    },
    {
        'codigo': 'proyecto_sisin',
        'nombre': 'Proyecto de inversión con código SISIN',
        'descripcion': 'Todo proyecto de inversión pública debe contar con código SISIN-WEB válido.',
        'tipo': 'consistencia',
        'severidad': 'bloqueante',
        'parametros': {},
        'condicion_aplicabilidad': 'Aplica solo a proyectos de inversión pública',
        'gestion_desde': 2024,
        'fuente_normativa': 'NB inversión pública, SISIN-WEB',
        'mensaje': 'El proyecto de inversión no tiene código SISIN. Registre el proyecto en SISIN-WEB antes de incluirlo en el POA.',
    },
    {
        'codigo': 'documentacion_obligatoria',
        'nombre': 'Documentación obligatoria',
        'descripcion': 'Toda acción de corto plazo debe tener documentos de respaldo.',
        'tipo': 'documentacion',
        'severidad': 'advertencia',
        'parametros': {},
        'condicion_aplicabilidad': 'Aplica a toda acción en estado de revisión o aprobación',
        'gestion_desde': 2024,
        'fuente_normativa': 'NB SPO, Directrices de Formulación',
        'mensaje': 'Existen acciones sin documentos de respaldo. Adjunte la documentación técnica y legal correspondiente.',
    },
    {
        'codigo': 'articulacion_pei',
        'nombre': 'Articulación con PEI',
        'descripcion': 'Toda acción de corto plazo debe articularse con una acción de mediano plazo del PEI.',
        'tipo': 'consistencia',
        'severidad': 'bloqueante',
        'parametros': {},
        'condicion_aplicabilidad': 'Aplica a toda acción de corto plazo formulada',
        'gestion_desde': 2024,
        'fuente_normativa': 'Ley N.º 777 SPIE',
        'mensaje': 'Existen acciones de corto plazo sin articulación con el PEI. Debe vincular cada acción a una acción de mediano plazo.',
    },
]

for regla in reglas:
    ReglaPresupuestariaLegal.objects.get_or_create(
        codigo=regla['codigo'],
        defaults=regla
    )

print(f'{ReglaPresupuestariaLegal.objects.count()} reglas presupuestarias legales creadas')
