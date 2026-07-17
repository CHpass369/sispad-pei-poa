# Matriz de Roles y Permisos — SISPAD-PEI-POA

Matriz completa de 12 roles del sistema contra todas las acciones disponibles en cada modulo.

## Simbologia

| Simbolo | Significado |
|---------|-------------|
| ✓ | Acceso completo (lectura + escritura) |
| 👁️ | Solo lectura |
| ✏️ | Escritura parcial (solo creacion/edicion de ciertos registros) |
| 🗑️ | Puede eliminar |
| ✗ | Sin acceso |

---

## 1. Modulo Dashboard

| Accion | superadmin | tecnico_admin | planificador | evaluador | jefe_ue | director | tecnico_ue | operador | beneficiario | proveedor | control_interno | control_social |
|--------|:----------:|:-------------:|:------------:|:---------:|:-------:|:--------:|:----------:|:--------:|:------------:|:---------:|:---------------:|:--------------:|
| Ver resumen general | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 👁️ | 👁️ | 👁️ | ✗ | 👁️ | 👁️ |
| Ver indicadores clave | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 👁️ | 👁️ | 👁️ | ✗ | 👁️ | 👁️ |
| Ver alertas | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 👁️ | 👁️ | ✗ | ✗ | 👁️ | 👁️ |
| Configurar dashboard | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |

---

## 2. Modulo Usuarios

| Accion | superadmin | tecnico_admin | planificador | evaluador | jefe_ue | director | tecnico_ue | operador | beneficiario | proveedor | control_interno | control_social |
|--------|:----------:|:-------------:|:------------:|:---------:|:-------:|:--------:|:----------:|:--------:|:------------:|:---------:|:---------------:|:--------------:|
| Ver listado | ✓ | ✓ | 👁️ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Crear usuario | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Editar usuario | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Eliminar usuario | 🗑️ | 🗑️ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Asignar roles | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Restablecer contraseña | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Ver detalle | ✓ | ✓ | 👁️ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |

---

## 3. Modulo Organizacion

| Accion | superadmin | tecnico_admin | planificador | evaluador | jefe_ue | director | tecnico_ue | operador | beneficiario | proveedor | control_interno | control_social |
|--------|:----------:|:-------------:|:------------:|:---------:|:-------:|:--------:|:----------:|:--------:|:------------:|:---------:|:---------------:|:--------------:|
| Ver estructura | ✓ | ✓ | 👁️ | ✗ | 👁️ | 👁️ | 👁️ | ✗ | 👁️ | ✗ | 👁️ | ✗ |
| Crear unidad | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Editar unidad | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Eliminar unidad | 🗑️ | 🗑️ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Asignar usuarios a unidad | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Gestionar DAs | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Gestionar UEs | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |

---

## 4. Modulo Catalogos

| Accion | superadmin | tecnico_admin | planificador | evaluador | jefe_ue | director | tecnico_ue | operador | beneficiario | proveedor | control_interno | control_social |
|--------|:----------:|:-------------:|:------------:|:---------:|:-------:|:--------:|:----------:|:--------:|:------------:|:---------:|:---------------:|:--------------:|
| Ver catalogos | ✓ | ✓ | 👁️ | ✗ | ✗ | ✗ | ✗ | ✗ | 👁️ | ✗ | ✗ | ✗ |
| Crear item | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Editar item | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Eliminar item | 🗑️ | 🗑️ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Importar catalogo | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Gestionar versiones | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Exportar catalogo | ✓ | ✓ | 👁️ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |

---

## 5. Modulo Gestion Fiscal

| Accion | superadmin | tecnico_admin | planificador | evaluador | jefe_ue | director | tecnico_ue | operador | beneficiario | proveedor | control_interno | control_social |
|--------|:----------:|:-------------:|:------------:|:---------:|:-------:|:--------:|:----------:|:--------:|:------------:|:---------:|:---------------:|:--------------:|
| Ver gestiones | ✓ | ✓ | ✓ | 👁️ | ✓ | ✓ | 👁️ | 👁️ | 👁️ | ✗ | 👁️ | 👁️ |
| Crear gestion | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Editar gestion | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Abrir/cerrar gestion | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Gestionar ciclos | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Gestionar etapas | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Exportar | ✓ | ✓ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | ✗ | 👁️ | 👁️ |

---

## 6. Modulo Planificacion

| Accion | superadmin | tecnico_admin | planificador | evaluador | jefe_ue | director | tecnico_ue | operador | beneficiario | proveedor | control_interno | control_social |
|--------|:----------:|:-------------:|:------------:|:---------:|:-------:|:--------:|:----------:|:--------:|:------------:|:---------:|:---------------:|:--------------:|
| Ver planes | ✓ | ✓ | ✓ | 👁️ | 👁️ | 👁️ | 👁️ | ✗ | 👁️ | ✗ | 👁️ | ✗ |
| Crear plan | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Editar plan | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Eliminar plan | 🗑️ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Gestionar nodos | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Gestionar AMP | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Gestionar ACP | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Articular nodos | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Versionar plan | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Aprobar version | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Exportar | ✓ | ✓ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | ✗ | 👁️ | ✗ | 👁️ | ✗ |

---

## 7. Modulo PAD (Plan Anual de Desarrollo)

| Accion | superadmin | tecnico_admin | planificador | evaluador | jefe_ue | director | tecnico_ue | operador | beneficiario | proveedor | control_interno | control_social |
|--------|:----------:|:-------------:|:------------:|:---------:|:-------:|:--------:|:----------:|:--------:|:------------:|:---------:|:---------------:|:--------------:|
| Ver PAD | ✓ | ✓ | ✓ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | ✗ | 👁️ | 👁️ |
| Crear sector/politica | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Editar politica | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Crear resultado territorial | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Editar resultado territorial | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Crear producto territorial | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Editar producto territorial | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Enviar resultado (workflow) | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Aprobar resultado | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Gestionar articulacion SIPEB | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Gestionar programacion anual | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Ver articulacion log | ✓ | ✓ | ✓ | 👁️ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Exportar PAD | ✓ | ✓ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | ✗ | 👁️ | 👁️ |

---

## 8. Modulo POAU (Plan Operativo Anual por Unidad)

| Accion | superadmin | tecnico_admin | planificador | evaluador | jefe_ue | director | tecnico_ue | operador | beneficiario | proveedor | control_interno | control_social |
|--------|:----------:|:-------------:|:------------:|:---------:|:-------:|:--------:|:----------:|:--------:|:------------:|:---------:|:---------------:|:--------------:|
| Ver POAU | ✓ | ✓ | 👁️ | 👁️ | ✓ | 👁️ | 👁️ | 👁️ | 👁️ | ✗ | 👁️ | 👁️ |
| Crear POAU | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Editar POAU | ✓ | ✓ | ✗ | ✗ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Eliminar POAU | 🗑️ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Crear actividad | ✓ | ✓ | ✗ | ✗ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Editar actividad | ✓ | ✓ | ✗ | ✗ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Registrar ejecucion fisica | ✓ | ✓ | ✗ | ✗ | ✓ | ✗ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |
| Registrar ejecucion financiera | ✓ | ✓ | ✗ | ✗ | ✓ | ✗ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |
| Aprobar POAU unidad | ✓ | ✓ | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Aprobar POAU consolidado | ✓ | ✓ | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Exportar POAU | ✓ | ✓ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | ✗ | 👁️ | 👁️ |

---

## 9. Modulo Indicadores

| Accion | superadmin | tecnico_admin | planificador | evaluador | jefe_ue | director | tecnico_ue | operador | beneficiario | proveedor | control_interno | control_social |
|--------|:----------:|:-------------:|:------------:|:---------:|:-------:|:--------:|:----------:|:--------:|:------------:|:---------:|:---------------:|:--------------:|
| Ver indicadores | ✓ | ✓ | ✓ | 👁️ | ✓ | 👁️ | 👁️ | 👁️ | 👁️ | ✗ | 👁️ | ✗ |
| Crear indicador | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Editar indicador | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Eliminar indicador | 🗑️ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Gestionar metas programadas | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Gestionar operaciones | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Gestionar tareas | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Gestionar productos | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Ver medios verificacion | ✓ | ✓ | ✓ | 👁️ | ✓ | 👁️ | 👁️ | 👁️ | 👁️ | ✗ | 👁️ | ✗ |
| Calcular avance | ✓ | ✓ | ✓ | 👁️ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Exportar indicadores | ✓ | ✓ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | ✗ | 👁️ | ✗ |

---

## 10. Modulo Presupuesto

| Accion | superadmin | tecnico_admin | planificador | evaluador | jefe_ue | director | tecnico_ue | operador | beneficiario | proveedor | control_interno | control_social |
|--------|:----------:|:-------------:|:------------:|:---------:|:-------:|:--------:|:----------:|:--------:|:------------:|:---------:|:---------------:|:--------------:|
| Ver programas | ✓ | ✓ | ✓ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | ✗ | 👁️ | ✗ |
| Crear programa | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Ver lineas presupuestarias | ✓ | ✓ | ✓ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | ✗ | 👁️ | ✗ |
| Crear linea presupuestaria | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Editar linea presupuestaria | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Eliminar linea | 🗑️ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Validar reglas legales | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Exportar presupuesto | ✓ | ✓ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | ✗ | 👁️ | ✗ |

---

## 11. Modulo Techos Presupuestarios

| Accion | superadmin | tecnico_admin | planificador | evaluador | jefe_ue | director | tecnico_ue | operador | beneficiario | proveedor | control_interno | control_social |
|--------|:----------:|:-------------:|:------------:|:---------:|:-------:|:--------:|:----------:|:--------:|:------------:|:---------:|:---------------:|:--------------:|
| Ver techos | ✓ | ✓ | ✓ | ✗ | 👁️ | 👁️ | ✗ | ✗ | 👁️ | ✗ | 👁️ | ✗ |
| Crear techo | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Editar techo | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Eliminar techo | 🗑️ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Distribuir techo | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Registrar movimientos | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Aprobar movimiento | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Exportar techos | ✓ | ✓ | 👁️ | ✗ | 👁️ | 👁️ | ✗ | ✗ | ✗ | ✗ | 👁️ | ✗ |

---

## 12. Modulo Inversion

| Accion | superadmin | tecnico_admin | planificador | evaluador | jefe_ue | director | tecnico_ue | operador | beneficiario | proveedor | control_interno | control_social |
|--------|:----------:|:-------------:|:------------:|:---------:|:-------:|:--------:|:----------:|:--------:|:------------:|:---------:|:---------------:|:--------------:|
| Ver proyectos | ✓ | ✓ | ✓ | 👁️ | 👁️ | 👁️ | 👁️ | ✗ | 👁️ | 👁️ | 👁️ | ✗ |
| Crear proyecto | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Editar proyecto | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Eliminar proyecto | 🗑️ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Gestionar programacion | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Registrar avance | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ |
| Subir documentos | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ |
| Exportar proyectos | ✓ | ✓ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | ✗ | 👁️ | 👁️ | 👁️ | ✗ |

---

## 13. Modulo Territorio

| Accion | superadmin | tecnico_admin | planificador | evaluador | jefe_ue | director | tecnico_ue | operador | beneficiario | proveedor | control_interno | control_social |
|--------|:----------:|:-------------:|:------------:|:---------:|:-------:|:--------:|:----------:|:--------:|:------------:|:---------:|:---------------:|:--------------:|
| Ver distritos | ✓ | ✓ | 👁️ | ✗ | 👁️ | 👁️ | 👁️ | ✗ | 👁️ | ✗ | ✗ | ✗ |
| Ver unidades territoriales | ✓ | ✓ | 👁️ | ✗ | 👁️ | 👁️ | 👁️ | ✗ | 👁️ | ✗ | ✗ | ✗ |
| Crear/editar territorio | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Gestionar localizaciones | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Ver mapas GeoServer | ✓ | ✓ | 👁️ | ✗ | 👁️ | 👁️ | 👁️ | ✗ | 👁️ | ✗ | ✗ | ✗ |
| Exportar GeoJSON | ✓ | ✓ | 👁️ | ✗ | 👁️ | 👁️ | 👁️ | ✗ | 👁️ | ✗ | ✗ | ✗ |

---

## 14. Modulo Workflow (Flujo de Aprobacion)

| Accion | superadmin | tecnico_admin | planificador | evaluador | jefe_ue | director | tecnico_ue | operador | beneficiario | proveedor | control_interno | control_social |
|--------|:----------:|:-------------:|:------------:|:---------:|:-------:|:--------:|:----------:|:--------:|:------------:|:---------:|:---------------:|:--------------:|
| Ver envios | ✓ | ✓ | ✓ | 👁️ | ✓ | ✓ | 👁️ | ✗ | 👁️ | ✗ | 👁️ | 👁️ |
| Enviar formulacion | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Crear revision | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Asignar revisor | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Registrar resultado revision | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Crear observacion | ✓ | ✓ | ✗ | 👁️ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Responder observacion | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Aprobar | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Rechazar/devolver | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Consolidar | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Pronunciamiento control social | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ |
| Ver huella documento | ✓ | ✓ | 👁️ | 👁️ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |

---

## 15. Modulo Reportes

| Accion | superadmin | tecnico_admin | planificador | evaluador | jefe_ue | director | tecnico_ue | operador | beneficiario | proveedor | control_interno | control_social |
|--------|:----------:|:-------------:|:------------:|:---------:|:-------:|:--------:|:----------:|:--------:|:------------:|:---------:|:---------------:|:--------------:|
| Ver reportes disponibles | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 👁️ | 👁️ | 👁️ | ✗ | 👁️ | 👁️ |
| Generar POA unidad | ✓ | ✓ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | ✗ | 👁️ | 👁️ |
| Generar POA consolidado | ✓ | ✓ | 👁️ | 👁️ | ✗ | 👁️ | ✗ | ✗ | ✗ | ✗ | 👁️ | 👁️ |
| Generar presupuesto | ✓ | ✓ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | ✗ | ✗ | 👁️ | ✗ |
| Generar mapa inversion | ✓ | ✓ | 👁️ | ✗ | 👁️ | 👁️ | 👁️ | ✗ | 👁️ | ✗ | 👁️ | ✗ |
| Generar observaciones | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | 👁️ | ✗ |
| Generar auditoria | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | 👁️ | ✗ |
| Generar expediente | ✓ | ✓ | 👁️ | 👁️ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | 👁️ | ✗ |
| Descargar reporte | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 👁️ | 👁️ | 👁️ | ✓ | ✓ | ✓ |
| Exportar a PDF | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 👁️ | 👁️ | ✗ | ✗ | ✓ | ✓ |
| Exportar a XLSX | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 👁️ | 👁️ | ✗ | ✗ | ✓ | ✓ |
| Exportar a CSV | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 👁️ | 👁️ | ✗ | ✗ | ✓ | ✗ |

---

## 16. Modulo Auditoria

| Accion | superadmin | tecnico_admin | planificador | evaluador | jefe_ue | director | tecnico_ue | operador | beneficiario | proveedor | control_interno | control_social |
|--------|:----------:|:-------------:|:------------:|:---------:|:-------:|:--------:|:----------:|:--------:|:------------:|:---------:|:---------------:|:--------------:|
| Ver eventos | ✓ | 👁️ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | 👁️ | ✗ |
| Filtrar por entidad | ✓ | 👁️ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | 👁️ | ✗ |
| Filtrar por usuario | ✓ | 👁️ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | 👁️ | ✗ |
| Ver datos previos/posteriores | ✓ | 👁️ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | 👁️ | ✗ |
| Exportar log | ✓ | 👁️ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | 👁️ | ✗ |
| Eliminar eventos | 🗑️ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |

---

## 17. Modulo Evaluacion

| Accion | superadmin | tecnico_admin | planificador | evaluador | jefe_ue | director | tecnico_ue | operador | beneficiario | proveedor | control_interno | control_social |
|--------|:----------:|:-------------:|:------------:|:---------:|:-------:|:--------:|:----------:|:--------:|:------------:|:---------:|:---------------:|:--------------:|
| Ver evaluaciones | ✓ | ✓ | 👁️ | ✓ | 👁️ | 👁️ | ✗ | ✗ | 👁️ | ✗ | 👁️ | 👁️ |
| Crear evaluacion | ✓ | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Editar evaluacion | ✓ | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Eliminar evaluacion | 🗑️ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Gestionar criterios | ✓ | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Registrar resultado | ✓ | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Gestionar lecciones | ✓ | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Gestionar recomendaciones | ✓ | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Aprobar evaluacion | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Ver pronunciamiento | ✓ | ✓ | ✗ | 👁️ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ |
| Exportar | ✓ | ✓ | 👁️ | 👁️ | 👁️ | 👁️ | ✗ | ✗ | 👁️ | ✗ | 👁️ | 👁️ |

---

## 18. Modulo Modificaciones

| Accion | superadmin | tecnico_admin | planificador | evaluador | jefe_ue | director | tecnico_ue | operador | beneficiario | proveedor | control_interno | control_social |
|--------|:----------:|:-------------:|:------------:|:---------:|:-------:|:--------:|:----------:|:--------:|:------------:|:---------:|:---------------:|:--------------:|
| Ver solicitudes | ✓ | ✓ | ✓ | 👁️ | ✓ | ✓ | 👁️ | 👁️ | 👁️ | ✗ | 👁️ | 👁️ |
| Crear solicitud | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ |
| Editar solicitud | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Enviar a revision | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Aprobar solicitud | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Rechazar solicitud | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Aplicar modificacion | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Ver impacto | ✓ | ✓ | 👁️ | 👁️ | ✓ | ✓ | 👁️ | 👁️ | 👁️ | ✗ | 👁️ | ✗ |
| Exportar | ✓ | ✓ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | ✗ | 👁️ | 👁️ |

---

## 19. Modulo Notificaciones

| Accion | superadmin | tecnico_admin | planificador | evaluador | jefe_ue | director | tecnico_ue | operador | beneficiario | proveedor | control_interno | control_social |
|--------|:----------:|:-------------:|:------------:|:---------:|:-------:|:--------:|:----------:|:--------:|:------------:|:---------:|:---------------:|:--------------:|
| Ver notificaciones | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ |
| Marcar leida | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ |
| Marcar todas leidas | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ |
| Ver preferencias | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ |
| Configurar preferencias | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ |
| Gestionar tipos notificacion | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |

---

## 20. Modulo Seguimiento

| Accion | superadmin | tecnico_admin | planificador | evaluador | jefe_ue | director | tecnico_ue | operador | beneficiario | proveedor | control_interno | control_social |
|--------|:----------:|:-------------:|:------------:|:---------:|:-------:|:--------:|:----------:|:--------:|:------------:|:---------:|:---------------:|:--------------:|
| Ver reportes seguimiento | ✓ | ✓ | 👁️ | 👁️ | ✓ | 👁️ | ✓ | ✓ | 👁️ | ✗ | 👁️ | 👁️ |
| Crear reporte | ✓ | ✓ | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Registrar entrada | ✓ | ✓ | ✗ | ✗ | ✓ | ✗ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |
| Validar reporte | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Aprobar reporte | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Ver alertas | ✓ | ✓ | 👁️ | 👁️ | ✓ | 👁️ | ✓ | ✓ | ✗ | ✗ | 👁️ | 👁️ |
| Resolver alerta | ✓ | ✓ | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Configurar umbrales | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Exportar | ✓ | ✓ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | ✗ | ✗ | 👁️ | 👁️ |

---

## 21. Modulo Acciones Correctivas

| Accion | superadmin | tecnico_admin | planificador | evaluador | jefe_ue | director | tecnico_ue | operador | beneficiario | proveedor | control_interno | control_social |
|--------|:----------:|:-------------:|:------------:|:---------:|:-------:|:--------:|:----------:|:--------:|:------------:|:---------:|:---------------:|:--------------:|
| Ver acciones correctivas | ✓ | ✓ | 👁️ | 👁️ | ✓ | 👁️ | ✓ | 👁️ | 👁️ | ✗ | 👁️ | ✗ |
| Crear accion correctiva | ✓ | ✓ | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Editar accion correctiva | ✓ | ✓ | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Registrar evidencia | ✓ | ✓ | ✗ | ✗ | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Verificar cumplimiento | ✓ | ✓ | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Gestionar compromisos | ✓ | ✓ | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Exportar | ✓ | ✓ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | ✗ | ✗ | 👁️ | ✗ |

---

## 22. Modulo Consolidacion

| Accion | superadmin | tecnico_admin | planificador | evaluador | jefe_ue | director | tecnico_ue | operador | beneficiario | proveedor | control_interno | control_social |
|--------|:----------:|:-------------:|:------------:|:---------:|:-------:|:--------:|:----------:|:--------:|:------------:|:---------:|:---------------:|:--------------:|
| Ver consolidacion | ✓ | ✓ | ✓ | 👁️ | ✓ | ✓ | 👁️ | ✗ | 👁️ | ✗ | 👁️ | 👁️ |
| Consolidar POA | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Validar consolidacion | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Aprobar consolidacion | ✓ | ✓ | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Pronunciamiento control social | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ |
| Aprobacion final MAE | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Exportar | ✓ | ✓ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | ✗ | 👁️ | ✗ | 👁️ | 👁️ |

---

## 23. Modulo Portal Publico

| Accion | superadmin | tecnico_admin | planificador | evaluador | jefe_ue | director | tecnico_ue | operador | beneficiario | proveedor | control_interno | control_social |
|--------|:----------:|:-------------:|:------------:|:---------:|:-------:|:--------:|:----------:|:--------:|:------------:|:---------:|:---------------:|:--------------:|
| Ver POA aprobado | ✓ | ✓ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ |
| Ver indicadores publicos | ✓ | ✓ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ |
| Ver productos PAD | ✓ | ✓ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ |
| Descargar reportes publicos | ✓ | ✓ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ |
| Ver mapa inversion | ✓ | ✓ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ | 👁️ |

---

## Resumen por Rol

| Rol | Total modulos con acceso | Modulos con escritura | Nivel |
|-----|:------------------------:|:---------------------:|:-----:|
| superadmin | 24 | 24 | Total |
| tecnico_admin | 24 | 22 | Alto |
| planificador | 18 | 12 | Alto |
| evaluador | 16 | 3 | Medio |
| jefe_ue | 16 | 10 | Medio |
| director | 18 | 5 | Medio |
| tecnico_ue | 14 | 4 | Bajo |
| operador | 14 | 4 | Bajo |
| beneficiario | 12 | 0 | Solo lectura |
| proveedor | 6 | 2 | Limitado |
| control_interno | 18 | 0 | Solo lectura |
| control_social | 12 | 1 | Pronunciamiento |
