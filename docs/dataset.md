# Dataset

## Origen
TrashNet, Gary Thung y Mindy Yang, proyecto final de CS 229, Stanford. https://github.com/garythung/trashnet

- Licencia: MIT, según la API de GitHub.
- Archivo usado: `data/dataset-resized.zip` (42 834 870 bytes, SHA-256 `0bf47279...16b07c2`). Registro completo en `ml/results/dataset_source.json`.
- Descargado el 2026-11-23 (UTC) con `ml/scripts/01_download_dataset.py`.
- Los autores piden citar el repositorio al usar el dataset. Las fotos se tomaron sobre cartulina blanca con iPhone 7 Plus, 5S y SE.

## Categorías
Cardboard (cartón), Glass (vidrio), Metal, Paper (papel), Plastic (plástico), Trash (otros residuos).

## Exploración (`02_explore_dataset.py`, resultados en `ml/results/dataset_summary.json`)

| Clase | Imágenes | Proporción |
|---|---|---|
| cardboard | 403 | 15,95 % |
| glass | 501 | 19,83 % |
| metal | 410 | 16,22 % |
| paper | 594 | 23,51 % |
| plastic | 482 | 19,07 % |
| trash | 137 | 5,42 % |
| **Total** | **2527** | |

- Los conteos coinciden con los publicados por los autores.
- Todas las imágenes abren y verifican con Pillow. Ninguna está corrupta.
- Formato: 2527 JPEG, modo RGB, todas de 512 x 384 px. Tamaño de archivo entre 5,6 kB y 57,9 kB.
- Desequilibrio: la clase mayor (paper) es 4,34 veces la menor (trash). `trash` es la clase minoritaria y tendrá pocos ejemplos de prueba, por lo que sus métricas tendrán más incertidumbre.
- Figuras: `ml/results/figures/class_distribution.png`, `samples_per_class.png`, `image_sizes.png`.

### Duplicados
- Duplicados exactos (SHA-256): 3 pares, todos con **etiquetas contradictorias**: glass115/metal91, glass176/plastic152, glass389/plastic332. Se excluyen las 6 imágenes porque su etiqueta verdadera es ambigua (`ml/results/splits/excluded.csv`).
- Casi duplicados (hash perceptual, distancia de Hamming): 18 pares con distancia ≤ 2, de los cuales 4 son entre clases distintas. En fondos blancos este hash puede dar falsos positivos, por eso no se eliminan.
  Los pares conectados con distancia ≤ 2 forman 15 grupos que se asignan completos a una sola partición.

## Particiones (`03_split_dataset.py`)
- Imágenes usadas: 2521 (2527 menos 6 excluidas).
- Estratificación por etiqueta, semilla 42, 70/15/15, con los grupos de casi duplicados indivisibles.
- Archivos: `ml/results/splits/{train,val,test}.csv` con columnas `filename,label,split,sha256,group_id,relpath`.

| Clase | train | val | test |
|---|---|---|---|
| cardboard | 283 | 60 | 60 |
| glass | 348 | 75 | 75 |
| metal | 286 | 62 | 61 |
| paper | 415 | 88 | 91 |
| plastic | 336 | 72 | 72 |
| trash | 96 | 21 | 20 |
| **Total** | **1764 (69,97 %)** | **378 (14,99 %)** | **379 (15,03 %)** |

### Prevención de fuga
`tests/test_dataset_splits.py` comprueba que no hay nombres ni hashes compartidos entre particiones, que los grupos de casi duplicados no se dividen, que las proporciones son 70/15/15 y que las clases están presentes y estratificadas en cada partición. Las 5 pruebas pasan.

## Aumento de datos
Se aplicará solo sobre `train`, al generar la versión en Roboflow (Fase 3). `val` y `test` no se modifican.

## Conjunto de prueba
`test.csv` no se usa hasta la evaluación definitiva (Fase 4).

## Reproducción
```
uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -r ml/pyproject.toml
cd ml/scripts
python 01_download_dataset.py
python 02_explore_dataset.py
python 03_split_dataset.py
python 04_prepare_roboflow_upload.py
```
`04` genera `ml/data/roboflow_upload.zip` (2521 imágenes en `train/`, `valid/`, `test/` con subcarpeta por clase), que no se versiona.
