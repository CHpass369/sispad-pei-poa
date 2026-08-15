# SIS-POA — Testing del Ciclo Presupuestario

## 1. Números actuales (verificados)

| Suite | Cantidad |
|---|---|
| Tests backend de `apps/budget` (`tests.py`) | **191** (`def test_*`) |
| Specs frontend de `features/sis-poa/budget` | **75** (`it()/itAsync()` en 8 archivos) |
| Specs frontend totales (`frontend/sispoa/src`) | **225** |

El `pytest.ini` del backend configura: `DJANGO_SETTINGS_MODULE=config.settings`,
`testpaths = tests apps`. Se corre con la venv local + PostgreSQL 16 nativo
(`DB_HOST=localhost`; Docker no se usa en esta máquina).

## 2. Cómo correr

```powershell
# Backend (desde backend/): todos los tests
venv\Scripts\activate   # o el entorno del proyecto
pytest                  # 191 de budget + resto de apps y tests/

# Solo el módulo budget
pytest apps/budget/tests.py -q

# Solo una clase (ej. concurrencia)
pytest apps/budget/tests.py -k ControlConcurrencia -q

# Frontend (desde frontend/sispoa/)
npm run test            # ng test (karma + jasmine): 225 specs
```

Antes de correr: migraciones aplicadas (`python manage.py migrate`) y
fixtures/catálogos sembrados para la gestión de prueba.

## 3. Organización de `tests.py` (clases clave)

| Clase | Fase | Cubre |
|---|---|---|
| `TechoDirectivoComposicionTests` | 2 | composición §22, agregados por origen/fuente |
| `TechoDirectivoFlujoTests` | 2 | transiciones BORRADOR→EN_REVISION→APROBADO→FIJADO, OBSERVADO |
| `TechoDirectivoInmutabilidadTests` | 2 | versión fijada: rechazo de modificaciones, hash estable |
| `TechoDirectivoPermisosTests` / `TechoDirectivoDocumentoTests` | 2 | capacidades IAM, upload con sha256 |
| `FiscalYearApiTests` / `FiscalYearServiceTests` | 1 | enable/close, bloqueos, herencia de configuración |
| `ProgrammaticCategoryTests` / `CatalogOptionsTests` | 3 | árbol, duplicar a gestión, validaciones de nivel |
| `DistribucionAperturaTests` / `DistribucionReservaTests` / `DistribucionDashboardTests` | 4 | aperturas con fuentes, BUDGET_EXCEEDED por fuente, saldos |
| `ImportadorNormalizacionTests` | 5 | montos (`1.234.567,89`, `(123)`, `Bs`), códigos con ceros (`097`) |
| `ImportadorUploadTests` / `ImportadorValidacionTests` / `ImportadorAplicacionTests` | 5 | staging, severidades (CRITICAL bloquea apply), `#REF!`, duplicados, distritos |
| `TerritorialRepartoTests` / `TerritorialAplicarLiberarTests` | 6 | PORCENTAJE/POBLACION/MANUAL, ajuste de redondeo exacto, reservas DISTRITALES |
| `FijacionValidacionTests` / `FijacionFlujoTests` / `FijacionInmutabilidadTests` / `FijacionAjusteTests` / `FijacionChecksumTests` | 7 | Σfuente = techo − reservas, tolerancia 0.01, 409, versión nueva |
| `ControlSummaryTests` / `ControlReservaTests` / `ControlMovimientoTests` | 8 | invariante techo = distribuido + reservado + disponible |
| `ControlConcurrenciaTests` (`TransactionTestCase`) | 8 | **doble consumo**: A 80.000 + B 50.000 sobre 100.000 → el segundo falla |
| `ControlApiTests` | 8 | endpoints summary/validate |
| `ProgramacionObjetosGastoTests` | 9 | techo/programado/disponible por apertura, **409 BUDGET_EXCEEDED** |
| `ReformulacionCreacionTests` / `ReformulacionFlujoTests` / `ReformulacionTiposTests` / `ReformulacionAtomicidadTests` / `ReformulacionAuditoriaTests` | 10 | workflow, TRASPASO/INCREMENTO/DISMINUCION/CAMBIO_FUENTE, rollback total |
| `AuditoriaFase11Tests` | 11 | `EventoAuditoria` en operaciones + endpoint `/audit/` con `audit_read` |
| `FlujoCompletoE2ETests` (APIClient real, superuser) | 12 | **E2E completo**: habilitar → techo SIGEP → fijar → distribuir → fijar distribución → objetos del gasto → reformulación → auditoría |

## 4. Casos clave (por qué importan)

- **Fijación**: rechaza distribución incompleta listando diferencias por
  fuente; tolera el centavo residual (0.01); congela con checksum.
- **Inmutabilidad**: modelo (save) + API (409) impiden tocar versiones
  fijadas; `verificar_hash()` detecta corrupción.
- **Concurrencia**: `select_for_update` sobre el techo fijado garantiza que
  nunca se consuma más que el saldo (test con threads/TransactionTestCase).
- **Importador**: planillas GASTOS histórica/actual, headers desplazados,
  errores de Excel (#REF! → CRITICAL), ceros iniciales, montos por fuente
  sumados (CT+IDH→41).
- **E2E**: recorre el ciclo completo por API real con superuser, incluyendo
  la reformulación con traspaso y la consulta de auditoría.

## 5. Cobertura transversal

- Auditoría de Fase 11: cada operación del ciclo registra
  `EventoAuditoria` y el endpoint `/audit/` filtra por gestión/entidad/
  registro/usuario/acción/rango de fechas.
- Verificación base del plan: 963 tests backend + 150 frontend (Fase 0);
  con el ciclo se suman los 191 de budget y 75 specs del módulo.
