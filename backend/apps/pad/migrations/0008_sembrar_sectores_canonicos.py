from django.db import migrations

# The 20 canonical municipal sectors, recovered from the pre-rename database
# (gams_sis_poa) where they were the only complete copy. Codes are the two
# digit SS segment used across PAD instruments.
SECTORES = [
    ('01', 'Salud'),
    ('02', 'Deportes'),
    ('03', 'Educación'),
    ('04', 'Culturas'),
    ('05', 'Justicia'),
    ('06', 'Seguridad ciudadana'),
    ('07', 'Defensa'),
    ('08', 'Urbanismo y vivienda'),
    ('09', 'Transportes'),
    ('10', 'Telecomunicaciones y tecnologías de información'),
    ('11', 'Medio ambiente'),
    ('12', 'Recursos hídricos'),
    ('13', 'Saneamiento básico'),
    ('14', 'Agropecuario'),
    ('15', 'Industria'),
    ('16', 'Comercio'),
    ('17', 'Turismo'),
    ('18', 'Minería'),
    ('19', 'Hidrocarburos'),
    ('20', 'Energía'),
]


def sembrar(apps, schema_editor):
    """Seeds the sector catalog, leaving any pre-existing row untouched."""
    SectorPAD = apps.get_model('pad', 'SectorPAD')
    for codigo, nombre in SECTORES:
        SectorPAD.objects.get_or_create(codigo=codigo, defaults={'nombre': nombre})


def revertir(apps, schema_editor):
    """Removes only the seeded codes, and only when still untouched."""
    SectorPAD = apps.get_model('pad', 'SectorPAD')
    for codigo, nombre in SECTORES:
        SectorPAD.objects.filter(codigo=codigo, nombre=nombre).delete()


class Migration(migrations.Migration):
    """Loads the canonical sector catalog into the surviving PAD model.

    ``SectorPAD`` is the only model kept from the retired legacy PAD app and
    its table was empty. Relocating this catalog to its definitive domain
    still requires the official sector -> PDESA component mapping, which does
    not yet exist in the system.
    """

    dependencies = [
        ('pad', '0007_retirar_jerarquia_pad_legacy'),
    ]

    operations = [
        migrations.RunPython(sembrar, revertir),
    ]
