from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from openpyxl import Workbook


def create_demo_source_workbook(path):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = 'Base'
    for _ in range(4):
        sheet.append([None] * 62)

    task_number = 1
    for activity_number in range(1, 20):
        row = [None] * 62
        if activity_number == 1:
            row[0] = 'EM-001'
            row[4] = 'Dirección Jurídica'
            row[18] = 'Fortalecer la gestión jurídica municipal'
            row[20] = '000 0 001'
            row[22] = 'Prestar servicios de asesoramiento jurídico'
        row[23] = f'Actividad jurídica {activity_number:02d}'
        row[25] = f'Entregable de actividad {activity_number:02d}'
        row[26] = f'Indicador de actividad {activity_number:02d}'
        row[27] = '(Ejecutado / Programado) x 100'
        row[28] = 'Número'
        row[33] = 12
        row[34] = date(2027, 1, 1)
        row[35] = date(2027, 12, 31)
        for month in range(12):
            row[37 + month * 2] = 1
            row[38 + month * 2] = 0
        sheet.append(row)

        task_count = 8 if activity_number <= 6 else 7
        for _ in range(task_count):
            task_row = [None] * 62
            task_row[24] = f'Tarea jurídica {task_number:03d}'
            task_row[25] = f'Entregable de tarea {task_number:03d}'
            task_row[26] = f'Indicador de tarea {task_number:03d}'
            task_row[27] = '(Ejecutado / Programado) x 100'
            task_row[28] = 'Número'
            task_row[33] = 1
            task_row[34] = date(2027, 1, 1)
            task_row[35] = date(2027, 12, 31)
            sheet.append(task_row)
            task_number += 1

    workbook.save(path)
    workbook.close()
    return Path(path)


class DemoSourceWorkbookMixin:
    @classmethod
    def setUpClass(cls):
        cls._source_directory = TemporaryDirectory()
        cls.source_file = create_demo_source_workbook(
            Path(cls._source_directory.name) / 'demo-poau-2027.xlsx'
        )
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        try:
            super().tearDownClass()
        finally:
            cls._source_directory.cleanup()
