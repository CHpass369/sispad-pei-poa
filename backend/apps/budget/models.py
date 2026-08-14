"""Modelos del ciclo presupuestario SIS-POA (apps.budget).

Fase 1 (gestión fiscal): no se crean entidades de negocio nuevas — la
entidad de gestión es `apps.gestion.GestionFiscal`, extendida con los
estados del ciclo (CONFIGURACION/HABILITADA/EN_FORMULACION/VIGENTE/CERRADA).

Las entidades del dominio (techo directivo, aperturas, distribución,
reformulaciones…) se agregan en fases posteriores.
"""
