# ADR Template

Copia este archivo como `ADR-###-slug-descriptivo.md` (ejemplo: `ADR-012-versionado-api-v3.md`), completa las secciones y agrégalo a la tabla del índice en `docs/adr/README.md`.

## ADR-ID

`ADR-###` — el número debe ser el siguiente disponible en el registro (`docs/adr/README.md`).

## TITLE

Título breve y descriptivo de la decisión (ejemplo: *Versionado de API V3*).

## STATUS

Uno de: `Propuesto`, `Aceptado`, `Deprecado`, `Superseded por ADR-XXX`.

- `Aceptado`: la decisión está en vigor y es de referencia.
- `Superseded por ADR-XXX`: la decisión fue reemplazada; se conserva por contexto, sin reescribirla.

## CONTEXT

El problema, fuerza o situación que motiva la decisión. Hechos verificables del repositorio: qué existe hoy, qué falla, por qué se necesita decidir. Sin opiniones aún.

## DECISION

La decisión tomada, en términos concretos y accionables: qué se adopta, dónde vive, cómo se aplica. Incluir solo lo efectivamente implementado o aprobado.

## ALTERNATIVES

Alternativas consideradas y la razón de su rechazo. Mínimo una; si no las hubo, declararlo explícitamente.

## CONSEQUENCES

- **Positivas**: beneficios esperados y observados.
- **Negativas**: costos, riesgos y mitigaciones.

## MIGRATION IMPACT

Impacto de la decisión sobre datos, código o frontend existentes. Si el impacto es nulo, declararlo. Si hay trabajo futuro derivado, indicar dónde se registra (por ejemplo, `tasks/backlog/`).
