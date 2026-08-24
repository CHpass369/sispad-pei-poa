"""Une las dos ramas `0008` de `accounts` en una sola historia.

Dos ramas de trabajo partieron del mismo `0007_roles_poa_pe` sin saber una de la
otra, y cada una creó su propia `0008`:

- `0008_capacidad_gestion_reopen` — capacidad de reapertura de gestión, de la
  rama del candado de gestión fiscal;
- `0008_alcanceorganizacional_scope_rol_fiscal_year` — resolutor de alcance
  organizacional, que sigue en `0009` y `0010`.

Ambas quedaron aplicadas en la base de desarrollo, así que el esquema real es la
suma de las dos mientras que ninguna rama, por separado, lo describe. Al unirlas
en el código, Django encuentra dos hojas en el grafo de `accounts` y se niega a
migrar hasta que exista este nodo:

    CONFLICTO: app "accounts" tiene 2 hojas
      - 0008_capacidad_gestion_reopen
      - 0010_alcanceorganizacional_fiscal_year_to_fk

Esta migración no altera el esquema —no tiene operaciones— y existe únicamente
para declarar que las dos ramas convergen acá. Es el nodo que permite que
`migrate` vuelva a tener un único camino.

No confundir con una migración vacía por descuido: sin este archivo, un
despliegue falla al arrancar, no al usarse.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0008_capacidad_gestion_reopen'),
        ('accounts', '0010_alcanceorganizacional_fiscal_year_to_fk'),
    ]

    operations = []
