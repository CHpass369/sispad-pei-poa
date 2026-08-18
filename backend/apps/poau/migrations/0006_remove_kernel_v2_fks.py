from django.db import migrations


class Migration(migrations.Migration):
    """Drops the FKs into the retired strategic kernel.

    Both columns were entirely unpopulated. The strategic link they expressed
    (POA -> approved PEI version, action -> strategic node) returns when SIS-PE
    is rebuilt.
    """

    dependencies = [
        ('poau', '0005_remove_poau_producto_territorial'),
    ]

    operations = [
        migrations.RemoveField(model_name='poainstitucional', name='version_pei'),
        migrations.RemoveField(model_name='accioncortoplazo', name='nodo_pei'),
    ]
