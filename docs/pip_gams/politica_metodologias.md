# Política de versiones de metodología

**WP-01.** Reglas para parametrizar y versionar metodologías de planificación
dentro de PIP-GAMS.

## 1. Objetivo

Las metodologías nacionales/departamentales cambian (tipos de nodo, reglas de
código, validaciones). El sistema debe permitir:

- definir una metodología nueva sin tocar código;
- mantener múltiples metodologías vigentes en paralelo;
- asociar cada instrumento a la metodología con la que se formuló;
- preservar instrumentos aprobados aunque la metodología cambie.

## 2. Modelo

- `VersionMetodologia` — código, nombre, instrumento aplicable, vigencia,
  fuente oficial, estado, esquema de validación.
- `TipoNodoEstrategico` — pertenece a una metodología; define denominación,
  nivel/orden, permite hijos, cardinalidad, reglas de código y campos
  obligatorios parametrizados.
- `TipoVinculoEstrategico` — pertenece a una metodología; define origen
  permitido, destino permitido, cardinalidad, ponderación/justificación
  requerida.
- `VersionInstrumento` — referencia la metodología usada; inmutable tras
  aprobación.

## 3. Estados de metodología

`borrador → publicada → vigente → deprecada → retirada`

- **borrador:** en elaboración, no usable por instrumentos.
- **publicada:** usable por instrumentos nuevos.
- **vigente:** metodología actual oficial (puede haber varias vigentes por
  instrumento en transición).
- **deprecada:** no usable por instrumentos nuevos; instrumentos existentes
  se mantienen.
- **retirada:** solo lectura histórica.

## 4. Reglas

1. Un instrumento se formula contra **una sola** versión de metodología,
  fijada al crearlo y no cambiable después de aprobación.
2. Cambiar de metodología = **nueva versión del instrumento**, nunca edición
  de la anterior.
3. Una metodología **aprobada no se edita**: cualquier ajuste crea una nueva
  versión.
4. El checksum de la versión aprobada incluye el identificador de la
  metodología para trazabilidad.
5. La migración de datos no puede inventar metodologías: toda metodología
  necesaria para interpretar legacy se registra explícitamente antes de
  backfill (WP-05/06).
6. Los `NIVEL_CHOICES` rígidos de `NodoPlanificacion` no se replican en V2:
  los niveles provienen de `TipoNodoEstrategico`.

## 5. Política de versionado semántico de metodologías

`MAJOR.MINOR.PATCH`

- **MAJOR:** cambios de estructura (tipos de nodo, niveles, reglas de código).
- **MINOR:** nuevas validaciones o campos opcionales compatibles.
- **PATCH:** correcciones de redacción/descripción sin efecto estructural.
