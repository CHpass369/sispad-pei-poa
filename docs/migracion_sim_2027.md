# Migración controlada de códigos SIM-2027

Este procedimiento migra únicamente los ocho niveles canónicos de
`articulacion` a correlativos numéricos **PROVISIONALES**. Conserva IDs,
relaciones, gestión, descripciones y el código original en `codigo_fuente`.
No oficializa catálogos inciertos ni elimina filas legacy.

## 1. Dry-run persistente

```bash
cd backend
python manage.py migrar_codigos_sim \
  --gestion 2027 \
  --manifest ../backups/t5/manifests/sim-2027-dry-run.json
```

El comando guarda el manifiesto en JSON con permisos `0600` y registra una
ejecución append-only en `EjecucionMigracionSIM`. Revisar IDs, jerarquía,
códigos anterior/nuevo, warnings y copiar el `manifest_hash` impreso.

## 2. Commit con backup obligatorio y restauración probada

```bash
python manage.py migrar_codigos_sim \
  --gestion 2027 \
  --commit \
  --expected-hash HASH_DEL_DRY_RUN \
  --usuario responsable@gamsacaba.gob.bo \
  --backup-dir ../backups/t5 \
  --manifest ../backups/t5/manifests/sim-2027-commit.json
```

Antes de abrir la transacción de datos, el comando:

1. crea un dump PostgreSQL en formato custom;
2. valida su catálogo con `pg_restore --list`;
3. lo restaura en una base temporal aislada;
4. compara los conteos canónicos, incluidos `ResultadoPAD` y `ProductoPAD`, y del espejo POAU;
5. elimina la base temporal;
6. solo entonces bloquea filas, vuelve a verificar el hash y aplica cambios.

Si falla cualquier paso, no se escribe ningún código ni homologación.

## 3. Segunda ejecución

Repetir primero el dry-run y luego el commit con su hash. Una base ya migrada
debe informar `cambios_aplicados=0` y `homologaciones_creadas=0`. La nueva fila
de auditoría se conserva; no es un cambio de datos canónicos.

## Restauración / rollback controlado

No se borran ni modifican homologaciones para “deshacer” una ejecución. La
reversa autorizada es restaurar el dump completo durante una ventana de
mantenimiento:

```bash
export PGPASSWORD='***'
dropdb --host HOST --port PUERTO --username USUARIO --force BASE
createdb --host HOST --port PUERTO --username USUARIO --template template0 BASE
pg_restore --host HOST --port PUERTO --username USUARIO \
  --dbname BASE --exit-on-error --no-owner --no-acl \
  /ruta/sispoa_pre_t5_YYYYMMDDTHHMMSSZ_PID.dump
python manage.py check
```

Validar después los conteos RT=1, PT=1, RI=1, PI=1, ACP=1, OP=1, ACT=19,
TAR=139 y el espejo POAU. Nunca ejecutar `DELETE`/`UPDATE` sobre `HomologacionCodigo`,
`EjecucionMigracionSIM` o `MapeoLineamientoPADLegacy`: las tres historias son
append-only también en PostgreSQL.
