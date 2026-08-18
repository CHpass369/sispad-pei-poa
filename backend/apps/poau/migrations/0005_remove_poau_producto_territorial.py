from django.db import migrations


class Migration(migrations.Migration):
    """Drops the FK to the retired legacy PAD hierarchy.

    The column held a single demo row; the live product chain is
    ``articulacion.ProductoPAD``, fed by the Matriz PAD wizard.
    """

    dependencies = [
        ('poau', '0004_poainstitucional_poau_poains_gestion_0ac185_idx'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='poau',
            name='producto_territorial',
        ),
    ]
