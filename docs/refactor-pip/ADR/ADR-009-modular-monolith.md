# ADR-009 — Monolito modular Django (sin microservicios; eventos de dominio internos)

- **Fecha:** 2026-08-15
- **Estado:** Aceptado
- **Relacionado con:** ADR-002, ADR-004; plan maestro §3.16, §16; `ARQUITECTURA_ACTUAL.md` §1, §5

## Contexto

El sistema actual es una sola aplicación Django con 27 apps y 200 modelos sobre una base PostgreSQL 16/PostGIS, Celery + Redis para colas, y un motor de outbox ya existente (`EventoOutbox`, `MensajeEntrante`) usado para transferencias SIS-PRO ↔ SIS-POA. El flujo techo → distribución → asignación → programación exige consistencia transaccional fuerte dentro de una gestión, y la cadena PGDESA → proyecto exige trazabilidad íntegra. El plan maestro §3.16 prohíbe explícitamente introducir microservicios en esta etapa, y §16.1 mantiene una sola base por la consistencia y trazabilidad entre SIS-PE, SIS-POA y SIS-PRO. Sin embargo, las apps actuales están acopladas entre sí (consultas cruzadas directas, docstrings y lógica mezclada, `articulacion` como contenedor general), lo que impide evolucionar cada contexto por separado.

## Decisión

1. **PIP es un monolito modular Django**: alta cohesión dentro de cada app/bounded context, bajo acoplamiento entre ellos, integridad transaccional en el mismo proceso y la misma base. No se introducen microservicios, ni colas de mensajería externas (Kafka/RabbitMQ) en esta etapa.
2. **Comunicación entre contexts por contrato**: servicios de dominio y selectors públicos por contexto; prohibido importar modelos internos de otra app de dominio (reglas R1-R3 de la arquitectura objetivo). El frontend consume solo `/api/v2/` (ADR-002 del plan maestro).
3. **Eventos de dominio internos con patrón outbox**: los cambios de estado relevantes que otros contexts deben conocer (p. ej. versión aprobada, reforma aplicada, proyecto transferido) se publican como eventos en `pip_integracion.evento_outbox` dentro de la misma transacción (outbox transaccional) y se despachan por el worker de Celery; los consumidores procesan vía `mensaje_entrante`. No hay dual-write entre contexts.
4. **Celery + Redis se mantienen para trabajo pesado** (exportación de POA completa, reportes, despacho de outbox, beat diario `exportar-poa-completo-diario`), pero nunca como mecanismo de consistencia de negocio: la fuente de verdad es la transacción de la base.
5. **Reglas de dependencia por contrato** (ADR-004): SIS-PRO no accede a internals de SIS-POA; SIS-POA solo consume versiones aprobadas del SIS-PE; las integraciones externas pasan por PIP INTEGRACIÓN.

## Consecuencias

Positivas:

- Consistencia transaccional garantizada en el flujo operativo: techo → distribución → asignación → programación en una sola transacción.
- Despliegue simple (un proceso de aplicación), costos operativos bajos y sin coordinación distribuida.
- La refactorización es incremental: los límites de dominio se refuerzan sin cambiar la topología de despliegue (plan maestro §5.1).

Negativas:

- El escalado es vertical o por réplicas de lectura; el punto único de escritura limita el throughput (aceptable para la escala municipal).
- La disciplina de no importar modelos de otras apps requiere refactorizar acoplamientos existentes (principalmente desde y hacia `articulacion` y `inversion`).
- El outbox introduce latencia eventual en notificaciones entre contexts: los lectores críticos (p. ej. validación de techo) se resuelven por contrato síncrono dentro del contexto, no por evento.

## Alternativas consideradas

1. **Microservicios por SIS (SIS-PE, SIS-POA, SIS-PRO como servicios separados)**: descartado por el plan maestro §3.16 y §16.1: rompe la transaccionalidad del ciclo operativo y multiplica la infraestructura sin beneficio en esta escala.
2. **Kafka/RabbitMQ como bus de eventos**: descartado en esta etapa: el outbox sobre PostgreSQL + Celery cubre la necesidad actual; un bus real se evalúa solo si aparecen consumidores externos no transaccionales.
3. **Dual-write directo entre apps (escribir en la tabla del otro contexto)**: descartado: es la fuente de las inconsistencias actuales; se reemplaza por eventos de dominio.
