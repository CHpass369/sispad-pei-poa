from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import ActaPriorizacion


@receiver(post_delete, sender=ActaPriorizacion)
def eliminar_acta_de_google(
    sender,
    instance,
    **kwargs,
):
    """
    Cuando un acta se elimina definitivamente de PostgreSQL,
    limpia en Google Sheets todas las filas relacionadas
    con esa acta.

    El borrado en Google se ejecuta después de confirmar
    la transacción en PostgreSQL.
    """

    acta_id = instance.id

    def ejecutar():
        from .services.google_sheets import (
            eliminar_acta_google,
        )

        eliminar_acta_google(
            acta_id
        )

    transaction.on_commit(
        ejecutar
    )
