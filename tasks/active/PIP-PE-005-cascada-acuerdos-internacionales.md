# TASK PIP-PE-005: Primera versión funcional de la cascada ODS-NDC-NDT-KMGBF

## DOMINIO

`sis-pe`

## OBJECTIVE

Implementar una cascada conservadora y trazable en el asistente PAD para filtrar NDC, NDT y KMGBF/30x30 mediante relaciones clasificadas, reutilizando `AcuerdoInternacional` y sin presentar sugerencias semánticas como compatibilidades normativas.

## CONTEXT

El motor de articulación ya posee `AcuerdoInternacional` y relaciones ManyToMany en `ResultadoPAD`; el asistente PAD carga actualmente todo el catálogo mediante API V1 y persiste códigos/IDs en el borrador. La API V2 ya expone `/api/v2/integracion/acuerdos/` desde `config/urls_v2.py`.

El crosswalk oficial solicitado se verificó en las páginas CBD Target 2, Target 3 y Target 8, además de ODS 15 de Naciones Unidas y LDN de UNCCD:

- `https://www.cbd.int/gbf/targets/2/`
- `https://www.cbd.int/gbf/targets/3/`
- `https://www.cbd.int/gbf/targets/8/`
- `https://sdgs.un.org/goals/goal15`
- `https://www.unccd.int/land-and-life/land-degradation-neutrality/overview`

El catálogo PAD frontend actual lista ODS con códigos de objetivo (`1`…`17`), mientras que el crosswalk requerido refiere metas ODS (`6.6`, `14.2`, etc.). El seed usa el código exacto cuando existe; si falta, proyecta documentalmente la meta al objetivo padre únicamente como relación `DERIVADA_DOCUMENTAL` candidata de confianza media. El vínculo ODS 15.3→NDT/LDN permanece condicionado a códigos exactos y trazables.

## CURRENT BEHAVIOR

- `pad-wizard.component.ts` carga todos los acuerdos desde `/articulacion/acuerdos/` vía `ApiService` V1.
- Los cuatro selectores muestran el catálogo completo, sin relaciones ni evidencia.
- El borrador conserva los códigos en `p2_acuerdos` y la materialización existente recibe objetos `{id, codigo}` cuando el catálogo conoce el ID.

## EXPECTED BEHAVIOR

- Una relación activa, no rechazada y clasificada filtra la siguiente etapa.
- La respuesta de compatibilidades incluye tipo, estado, confianza, fuente y evidencia.
- La UX identifica `Oficial`, `Derivada` y `Sugerencia IA`; nunca trata las dos últimas como normativas.
- Sin relaciones clasificadas no se muestra el catálogo completo; se presenta un mensaje explícito.
- Cambiar una selección upstream limpia selecciones downstream inválidas.
- Los códigos/IDs persistidos mantienen el contrato actual del borrador y materialización.

## IN SCOPE

- [x] Modelo `CompatibilidadAcuerdoInternacional`, migración, serializer y endpoint V2.
- [x] Comando idempotente `sembrar_compatibilidades_acuerdos` por códigos actuales.
- [x] Relaciones oficiales verificadas y sugerencias semánticas claramente clasificadas.
- [x] Fallback controlado de meta ODS a objetivo padre, sin degradarlo a relación oficial.
- [x] Fuentes CBD corregidas para Targets 12 y 14, con localizadores y evidencia coincidentes.
- [x] Servicio Angular V2 tipado e integración en el wizard PAD.
- [x] Tests focalizados de modelo, API, seed y frontend.

## OUT OF SCOPE

- Renombrar, borrar o reemplazar catálogos existentes.
- Crear un catálogo paralelo o modificar la materialización de borradores.
- Declarar relaciones nacionales NDC/NDT no verificadas.
- Convertir los 23 registros `COMPROMISO_3030` en “30/30” sin distinguir KMGBF.

## INVARIANTS

- `AcuerdoInternacional` es la única fuente de acuerdos.
- API V1 permanece intacta para el flujo legacy existente.
- La relación no puede tener origen y destino iguales ni conectar tipos iguales.
- No se presentan relaciones `RECHAZADA` ni inactivas como opciones.
- La cascada usa intersección conservadora para múltiples IDs aunque PAD hoy permita uno.

## DATABASE IMPACT

Nueva tabla `articulacion_compatibilidadacuerdointernacional` mediante migración determinista. Incluye timestamps y `created_by`/`updated_by` heredados de `TimeStampedModel`; no crea auditoría paralela. No modifica ni elimina datos existentes.

## API IMPACT

Nuevo endpoint V2 `GET /api/v2/integracion/compatibilidades/` con `origen_id`, `origen_ids`, `destino_tipo`, `estado` e `incluir_sugerencias`. Solo lectura para la UX.

## FRONTEND IMPACT

Nuevo servicio tipado con `HttpClient` y `environment.apiUrlV2`. El wizard PAD conservará códigos actuales y cambiará únicamente las opciones disponibles y las etiquetas de evidencia/confianza.

## FILES EXPECTED

- `backend/apps/articulacion/models.py` — crear el modelo de compatibilidad.
- `backend/apps/articulacion/migrations/0013_compatibilidad_acuerdo_internacional.py` — crear la tabla y constraints.
- `backend/apps/articulacion/serializers.py` — serializar compatibilidades y acuerdos anidados.
- `backend/apps/articulacion/views.py` / `urls.py` / `backend/config/urls_v2.py` — exponer el endpoint V2.
- `backend/apps/articulacion/management/commands/sembrar_compatibilidades_acuerdos.py` — seed idempotente.
- `backend/apps/articulacion/tests/test_compatibilidades.py` — cobertura backend.
- `frontend/sispoa/src/app/features/matrices-pad/pad/compatibilidades-acuerdos.service.ts` — contrato V2 tipado.
- `frontend/sispoa/src/app/features/matrices-pad/pad/pad-wizard.component.ts` — cascada, limpieza y etiquetas.
- `frontend/sispoa/src/app/features/matrices-pad/pad/pad-wizard.component.spec.ts` — cobertura frontend.

## DEPENDENCIES

Catálogo existente `AcuerdoInternacional` cargado localmente. La ejecución del seed depende de que los códigos exactos estén disponibles; el comando no creará acuerdos faltantes.

## ACCEPTANCE CRITERIA

- [ ] El modelo valida origen/destino distintos y tipos distintos, y evita duplicados por origen/destino/tipo/fuente.
- [ ] El endpoint filtra por ODS, destino, estado y sugerencias con orden determinista.
- [ ] El seed es idempotente, opera por códigos y reporta creadas/actualizadas/omitidas.
- [ ] ODS→NDC→NDT→KMGBF filtra opciones y limpia downstream inválido.
- [ ] La UI distingue Oficial/Derivada/Sugerencia IA y no muestra todo el catálogo si no hay relaciones.
- [ ] Tests focalizados y build/type-check ejecutados, con resultados reportados.

## TESTS

```bash
cd backend; python3 -m pytest apps/articulacion/tests/test_compatibilidades.py
cd backend; python3 manage.py makemigrations --check
cd frontend/sispoa; npm test -- --watch=false --include='src/app/features/matrices-pad/pad/pad-wizard.component.spec.ts'
cd frontend/sispoa; npm run build
```

## RISKS

- El catálogo actual puede contener objetivos ODS (`6`) y no metas (`6.6`); el seed proyectará esos cruces a nivel documental, con estado candidata y confianza media, evitando una falsa compatibilidad oficial.
- `COMPROMISO_3030` contiene 23 targets KMGBF; la etiqueta de UI debe reservar “30x30” para el contexto del target correspondiente.
- El workspace ya contiene cambios no relacionados; no deben sobrescribirse.

## ROLLBACK

Revertir los archivos de la tarea y ejecutar la migración inversa de `articulacion`; el comando de seed no borra relaciones existentes.

## FINAL REPORT

- **Archivos modificados:** `backend/apps/articulacion/models.py`, `serializers.py`, `views.py`, `backend/config/urls_v2.py`, `frontend/sispoa/src/app/features/matrices-pad/pad/pad-wizard.component.ts`.
- **Archivos creados:** migración `0013_compatibilidad_acuerdo_internacional.py`, comando de seed, tests backend/frontend y servicio `compatibilidades-acuerdos.service.ts`.
- **Migración:** `articulacion.0013_compatibilidad_acuerdo_internacional` aplicada en la base local PostgreSQL.
- **Endpoint:** `GET /api/v2/integracion/compatibilidades/` con filtros de origen, destino, estado e inclusión de sugerencias.
- **Seed local (baseline):** primera ejecución creó 441 sugerencias semánticas y omitió las relaciones de metas ODS no representadas por el catálogo local; no se inventaron relaciones ni se degradaron metas a objetivos oficiales.
- **Tests:** `40 passed` en backend focalizado; `3 passed` en el spec del wizard; `npm run build` exitoso; `makemigrations --check`, `manage.py check` y `git diff --check` exitosos.
- **Riesgos/deuda:** mientras el catálogo solo tenga objetivos ODS, varias metas pueden proyectarse al mismo par objetivo/Target y compartir una compatibilidad por la restricción de unicidad vigente; al incorporar metas exactas, el seed las clasificará como oficiales sin borrar relaciones existentes. Ruff no está instalado localmente y Angular no tiene target `lint` configurado (`ng lint` no pudo ejecutarse). No se modificaron los cambios preexistentes ajenos a esta tarea.

## REFINAMIENTO 2026-08-19

- **Plan:** resolver metas ODS primero por código exacto y luego por objetivo padre; clasificar el fallback como `DERIVADA_DOCUMENTAL`/`CANDIDATA`/`MEDIA`; conservar omitido el vínculo LDN/NDT sin códigos exactos; corregir las fuentes CBD de Targets 12 y 14; cubrir los casos con tests.
- **Implementación:** `sembrar_compatibilidades_acuerdos.py` añadió `_resolver_ods()` y evidencia explícita de la proyección. No se modificó el modelo, la cascada frontend ni la materialización.
- **Verificación local:** antes `441` compatibilidades, todas `SUGERENCIA_SEMANTICA`; después `452` (`441` sugerencias y `11` derivadas documentales), con el vínculo ODS 15.3→NDT omitido. La segunda ejecución mantuvo `452`.
- **Tests:** `10 passed` en `apps/articulacion/tests/test_compatibilidades.py`; `manage.py check`, compilación Python y `git diff --check` exitosos.

---
