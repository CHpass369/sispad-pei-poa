# PIP SACABA · Prototipo Angular inspirado en Boron

Prototipo navegable para la **Plataforma Integral de Planificación (PIP) del Gobierno Autónomo Municipal de Sacaba**.

## Alcance

- Dashboard institucional PIP.
- Navegación a SIS-PE, SIS-POA y SIS-PRO.
- SIS-PE: Articulación Estratégica, Matriz PAD y Matriz PEI.
- SIS-POA: Gestión Fiscal, Techos Presupuestarios, Distribución, POA, POAU y Seguimiento.
- SIS-PRO: Cartera, Condiciones Previas, Preinversión, Contratación y Ejecución.
- Módulos transversales: Catálogos Maestros y Administración/Seguridad.
- Sidebar colapsable y móvil.
- Light/Dark mode.
- Diseño neubrutalista original, inspirado en los patrones visuales de Boron, sin copiar su código.

## Stack del prototipo

- Angular 21.x standalone
- Angular Router
- SCSS
- Sin librerías UI adicionales
- Datos mock locales

## Ejecutar

```bash
npm install
npm start
```

Luego abrir `http://localhost:4200`.

## Integración posterior sugerida

1. Reemplazar los mocks por servicios `HttpClient`.
2. Conectar API Gateway / backend PIP.
3. Aplicar RBAC por sistema, módulo y unidad organizacional.
4. Integrar catálogo maestro, gestión fiscal y articulaciones con IDs persistentes.
5. Separar dominios por features lazy-loaded cuando se conecte al backend real.
6. Incorporar gráficos con la librería aprobada por el proyecto, si se requiere.

## Nota de versión

Se usa Angular 21.x para mantener compatibilidad amplia con Node.js 22.x. El diseño y la arquitectura pueden migrarse a Angular 22 siguiendo la guía oficial de actualización.
