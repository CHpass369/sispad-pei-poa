"""Convierte el PDF de codificación organizacional del GAMS a JSON.

    pdftotext -bbox-layout "CODIFICACION 2026.pdf" cod.xml
    python scripts/parse_codificacion_gams.py cod.xml filas.json

El PDF sale de una planilla y no se deja leer por líneas: las celdas están
combinadas y su texto se envuelve en varias líneas, así que el contenido de una
celda alta cae encima de las filas vecinas. Por eso el parser NO agrupa por
línea:

  - Ancla cada fila en la columna CÓDIGO, que trae un valor por fila.
  - Une los códigos que el PDF parte cuando el original lleva un espacio
    ("SP -DPD-17-1").
  - Reparte cada columna de denominación entre las anclas de SU nivel, porque
    una celda combinada está centrada sobre todo su bloque y no cabe en una
    banda vertical.
  - Descarta la cabecera y repara las palabras que el ajuste de línea corta a
    la mitad sin guion.

Las correcciones al final del archivo (CORTES, REASIGNAR, AREAS_FUERA_DE_PATRON)
son específicas del documento 2026: revisarlas si cambia el formato.
"""
import json, re, sys, pathlib

XML = pathlib.Path(sys.argv[1])
SALIDA = pathlib.Path(sys.argv[2])

W = re.compile(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>')

# Límites de columna derivados del histograma de xMin.
COLUMNAS = [
    ('sec_cod',   0,   80),
    ('sec_den',  80,  150),
    ('dir_cod', 150,  178),
    ('dir_den', 178,  268),
    ('uni_cod', 268,  292),
    ('uni_den', 292,  378),
    ('are_cod', 378,  392),
    ('are_den', 392,  452),
    ('tipo',    452,  518),
    ('codigo',  518, 9999),
]

def columna(x):
    for nombre, x0, x1 in COLUMNAS:
        if x0 <= x < x1:
            return nombre
    return None

def desescapar(t):
    return (t.replace('&amp;', '&').replace('&lt;', '<')
             .replace('&gt;', '>').replace('&quot;', '"').replace('&apos;', "'"))

# El código de la última columna: EM · EM-DJR · EM-DJR-01 · EM-DJR-01-1
ANCLA = re.compile(r'^[A-Z]{2}(-[A-Z0-9]{3})?(-\d{2})?(-\d{1,2})?$')

filas = []
for pagina in XML.read_text().split('<page')[1:]:
    palabras = []
    for m in W.finditer(pagina):
        x0, y0, x1, y1, t = float(m[1]), float(m[2]), float(m[3]), float(m[4]), desescapar(m[5])
        palabras.append({'x': x0, 'y': (y0 + y1) / 2, 'col': columna(x0), 'txt': t})

    # Pie de la cabecera de la página: por debajo empieza la primera fila.
    # Un margen fijo recortaba el texto envuelto de esa primera fila.
    # Solo tokens que aparecen EXCLUSIVAMENTE en la cabecera: 'DE', 'UNIDAD'
    # y 'DIRECCIÓN' también son datos y subían el techo de más.
    ETIQUETAS = {'CÓD.', 'DENOMINACIÓN', 'CÓDIGO', 'UNIDADES', 'ÁREAS'}

    crudas = sorted((p for p in palabras if p['col'] == 'codigo'),
                    key=lambda p: (p['y'], p['x']))
    unidas, i = [], 0
    while i < len(crudas):
        grupo = [crudas[i]]
        while i + 1 < len(crudas) and abs(crudas[i + 1]['y'] - crudas[i]['y']) < 3:
            i += 1
            grupo.append(crudas[i])
        texto = ''.join(g['txt'] for g in grupo)
        unidas.append({'y': grupo[0]['y'], 'txt': texto})
        i += 1
    anclas = sorted((p for p in unidas if ANCLA.match(p['txt'])), key=lambda p: p['y'])
    if not anclas:
        continue

    primera_y = anclas[0]['y']
    cabecera = [p['y'] for p in palabras
                if p['y'] < primera_y and p['txt'] in ETIQUETAS]
    techo = max(cabecera) + 4 if cabecera else primera_y - 20

    # Banda vertical de cada fila: hasta el punto medio con sus vecinas.
    bandas = []
    for i, a in enumerate(anclas):
        # La primera fila de cada página no debe absorber la cabecera.
        arriba = (anclas[i - 1]['y'] + a['y']) / 2 if i else techo
        abajo = (a['y'] + anclas[i + 1]['y']) / 2 if i + 1 < len(anclas) else a['y'] + 20
        bandas.append((arriba, abajo, a))

    # Las celdas de denominación están COMBINADAS y centradas sobre todo su
    # bloque: 'SECRETARIA ...' queda muchas líneas por encima de su fila. Pero
    # cada columna solo tiene contenido en filas de su propio nivel, así que
    # cada palabra se asigna al ancla de ESE nivel más cercana, no por banda.
    NIVEL_DE = {'sec_den': 0, 'dir_den': 1, 'uni_den': 2, 'are_den': 3}
    # SF-DRT-1 (CAJA RECAUDADORA) es un ÁREA aunque su código tenga un solo
    # guion: su unidad es la "00". Sin esta excepción su nombre se iría a la
    # fila de área más cercana.
    AREAS_FUERA_DE_PATRON = {'SF-DRT-1'}
    por_nivel = {}
    for niv in set(NIVEL_DE.values()):
        por_nivel[niv] = [
            a for a in anclas
            if a['txt'].count('-') == niv
            or (niv == 3 and a['txt'] in AREAS_FUERA_DE_PATRON)
        ]
        if niv != 3:
            por_nivel[niv] = [a for a in por_nivel[niv]
                              if a['txt'] not in AREAS_FUERA_DE_PATRON]

    celdas = {a['txt']: {n: [] for n, _, _ in COLUMNAS} for a in anclas}
    orden = {a['txt']: i for i, a in enumerate(anclas)}

    for p in sorted(palabras, key=lambda p: (p['y'], p['x'])):
        if not p['col'] or p['col'] == 'codigo' or p['y'] < techo:
            continue
        niv = NIVEL_DE.get(p['col'])
        if niv is not None and por_nivel.get(niv):
            destino = min(por_nivel[niv], key=lambda a: abs(a['y'] - p['y']))
        else:
            destino = None
            for arriba, abajo, a in bandas:
                if arriba <= p['y'] < abajo:
                    destino = a
                    break
            if destino is None:
                continue
        celdas[destino['txt']][p['col']].append(p['txt'])

    for a in sorted(anclas, key=lambda a: orden[a['txt']]):
        fila = {n: ' '.join(v).strip() for n, v in celdas[a['txt']].items()}
        fila['codigo'] = a['txt']
        filas.append(fila)

# El ajuste de línea del PDF parte palabras a la mitad, sin guion.
CORTES = {
    'INTERINSTITUCIONAL ES': 'INTERINSTITUCIONALES',
    'REMUNERACIONE S': 'REMUNERACIONES',
    'ESTABLECIMIENT OS': 'ESTABLECIMIENTOS',
    'TELECOMUNICACI ONES': 'TELECOMUNICACIONES',
    'COMPLEMENTARI O': 'COMPLEMENTARIO',
    'SLIM- DNA': 'SLIM-DNA',
}
for fila in filas:
    for clave in ('sec_den', 'dir_den', 'uni_den', 'are_den'):
        for malo, bueno in CORTES.items():
            fila[clave] = fila[clave].replace(malo, bueno)

# Dos celdas altas cuyo texto se repartió mal entre áreas contiguas.
REASIGNAR = {
    'SM-DDP-49-3': 'CENTRO MUNICIPAL DE SEMILLAS Y BIOINSUMOS',
    'SM-DDP-49-4': 'CEMUSMA',
    'SD-DDH-52-2': 'UMADIS',
    'SD-DDH-52-3': 'SERVICIO LEGAL INTEGRAL MUNICIPAL (SLIM)',
}
for fila in filas:
    if fila['codigo'] in REASIGNAR:
        fila['are_den'] = REASIGNAR[fila['codigo']]

SALIDA.write_text(json.dumps(filas, ensure_ascii=False, indent=1))
print(f'filas parseadas: {len(filas)}')
