# Dataset

## Origen
TrashNet, Gary Thung y Mindy Yang, proyecto final de CS 229, Stanford. https://github.com/garythung/trashnet

El repositorio pide citar el propio repositorio al usar el dataset. Las imágenes fueron tomadas sobre cartulina blanca con iPhone 7 Plus, 5S y SE, y la versión redimensionada es de 512 x 384.

## Categorías
Cardboard (cartón), Glass (vidrio), Metal, Paper (papel), Plastic (plástico), Trash (otros residuos).

## Conteos declarados por los autores (por verificar)
Glass 501, Paper 594, Cardboard 403, Plastic 482, Metal 410, Trash 137. Total 2527.

Estos valores son los publicados. Los conteos reales se calculan con `ml/scripts/02_explore_dataset.py` y se registran en `ml/results/dataset_summary.json`.

## Resultados de exploración
Pendiente de ejecución (Fase 2).

## Particiones
Plan: 70/15/15 estratificado, semilla 42, deduplicación previa, CSV en `ml/results/splits/`. Resultado real pendiente.

## Aumento de datos
Solo sobre entrenamiento, configurado en Roboflow (Fase 3).
