# TASK PIP-POA-003: Modal de creación de Gestión Fiscal

## DOMINIO

`sis-poa`

## OBJECTIVE

Implementar la creación de gestiones fiscales desde un modal accesible, con fechas anuales derivadas del año, documento de habilitación y usuario autenticado; mantener el contrato V2 compatible con registros legacy.

## CONTEXT

La pantalla `/sis-poa/budget/gestion-fiscal` actualmente crea inline mediante JSON y no permite cargar el documento de habilitación. `GestionFiscal` en `backend/apps/gestion` ya es la fuente canónica y conserva `fecha_cierre` como cierre operativo real.

## CURRENT BEHAVIOR

- `FiscalYearComponent` muestra el formulario de creación dentro de la página.
- `BudgetService.crear` envía JSON al endpoint V2.
- `FiscalYearSerializer` no expone fechas anuales ni aliases de cargado.
- `GestionFiscal` no tiene `fecha_inicio`, `fecha_cierre_programada` ni `documento_habilitacion`.

## EXPECTED BEHAVIOR

- `+ Nueva gestión` abre un modal centrado con overlay oscurecido/desenfocado y semántica de diálogo.
- El año editable recalcula `01/01/{año}` y `31/12/{año}` en cada cambio.
- El archivo es requerido en la UI; crear envía multipart y refresca la tabla.
- Usuario y fecha de cargado son read-only y provienen del backend/auth.
- El backend deriva fechas si no se reciben y no exige documento para no romper JSON/legacy.

## IN SCOPE

- [ ] Campos y migración de `GestionFiscal`.
- [ ] Contrato `FiscalYearSerializer` y creación multipart V2.
- [ ] Tipos y servicio Angular.
- [ ] Modal, formulario, accesibilidad y pruebas focalizadas.

## OUT OF SCOPE

- Cambios en API V1.
- Renombrado o eliminación de `fecha_cierre`.
- Nuevos modelos/apps o refactors de otros módulos.

## INVARIANTS

- API V2 permanece en `/api/v2/sis-poa/budget/fiscal-years/`.
- `fecha_cierre` continúa siendo `DateTimeField` para cierre operativo.
- Registros existentes sin documento siguen serializándose y las llamadas JSON siguen funcionando.

## DATABASE IMPACT

Migración determinista nueva en `apps.gestion` agregando dos `DateField` nullable/blank para compatibilidad y un `FileField` nullable/blank con `upload_to` de gestión fiscal.

## API IMPACT

`FiscalYearSerializer` expone `fecha_inicio`, `fecha_cierre_programada`, `documento_habilitacion`, `fecha_cargado` y `encargado_cargado`; aliases de cargado son read-only. POST acepta JSON o multipart.

## FRONTEND IMPACT

`FiscalYearComponent` y su template usan modal accesible; `BudgetService` admite `FiscalYearInput` y convierte la creación con archivo a `FormData` sin alterar el endpoint.

## FILES EXPECTED

- `backend/apps/gestion/models.py` — campos y derivación de fechas.
- `backend/apps/gestion/migrations/0004_*.py` — migración determinista.
- `backend/apps/budget/serializers.py` — contrato y creación segura.
- `backend/apps/budget/tests.py` — API/serializer/multipart.
- `frontend/sispoa/src/app/features/sis-poa/budget/budget.service.ts` — tipos y envío.
- `frontend/sispoa/src/app/features/sis-poa/budget/fiscal-year.component.{ts,html,spec.ts}` — modal y pruebas.

## DEPENDENCIES

`GestionFiscal` existente y endpoint V2 existente.

## ACCEPTANCE CRITERIA

- [ ] Fechas derivadas correctamente tras cambiar varias veces el año.
- [ ] Archivo requerido en UI, opcional para compatibilidad backend.
- [ ] Usuario/fecha read-only y no manipulables desde el formulario.
- [ ] Crear multipart, refrescar tabla y cancelar sin guardar.
- [ ] Tests focalizados, build frontend y `git diff --check` pasan.

## TESTS

```bash
cd backend && .venv/bin/python -m pytest apps/budget/tests.py -k FiscalYear
cd frontend/sispoa && CHROME_BIN=/snap/bin/chromium npm test -- --watch=false --include='src/app/features/sis-poa/budget/fiscal-year.component.spec.ts'
cd frontend/sispoa && npm run build
git diff --check
```

## RISKS

El `FileField` debe ser nullable para conservar registros legacy; no se debe confundir `fecha_cierre_programada` con el cierre operativo.

## ROLLBACK

Revertir únicamente los archivos de esta tarea y aplicar la migración inversa si la migración llegó a ejecutarse en un entorno de prueba.

## FINAL REPORT

Completar al cerrar la tarea.
