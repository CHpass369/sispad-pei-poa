"""Importador del catálogo maestro (lotes por módulo).

Cada módulo expone ``importar(reporte, gestion)`` y devuelve el
``ReporteLote``; el comando ``importar_catalogo_maestro`` orquesta el orden
crítico y el modo dry-run (transaction.atomic + rollback).
"""
