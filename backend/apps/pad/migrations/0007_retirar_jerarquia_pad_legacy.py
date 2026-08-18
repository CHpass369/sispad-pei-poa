from django.db import migrations


class Migration(migrations.Migration):
    """Retires the legacy PAD hierarchy, keeping only the sector catalog.

    The hierarchy (policy -> guideline -> territorial result -> territorial
    product -> annual programming, plus SIPEB articulation and its audit log)
    was the backing store of the ``/articulador`` wizard, now replaced by
    Matriz PAD over ``articulacion.BorradorMatrizPAD``. It held 6 demo rows.

    ``SectorPAD`` survives: it holds the 20 canonical municipal sectors and
    has no equivalent elsewhere. Relocating it requires the official
    sector -> PDESA component mapping, which does not yet exist in the system.
    """

    dependencies = [
        ('pad', '0006_alter_programacionanualpad_options'),
        ('poau', '0005_remove_poau_producto_territorial'),
    ]

    operations = [
        migrations.RemoveField(model_name='articulacionlog', name='usuario'),
        migrations.RemoveField(model_name='articulacionsipeb', name='resultado'),
        migrations.RemoveField(model_name='programacionanualpad', name='producto'),
        migrations.RemoveField(model_name='programacionanualpad', name='resultado'),
        migrations.RemoveField(model_name='productoterritorial', name='resultado'),
        migrations.RemoveField(model_name='resultadoterritorial', name='lineamiento'),
        migrations.RemoveField(model_name='resultadoterritorial', name='sector'),
        migrations.RemoveField(model_name='lineamientoestrategico', name='politica'),
        migrations.DeleteModel(name='ArticulacionLog'),
        migrations.DeleteModel(name='ArticulacionSIPEB'),
        migrations.DeleteModel(name='ProgramacionAnualPAD'),
        migrations.DeleteModel(name='ProductoTerritorial'),
        migrations.DeleteModel(name='ResultadoTerritorial'),
        migrations.DeleteModel(name='LineamientoEstrategico'),
        migrations.DeleteModel(name='PoliticaPAD'),
    ]
