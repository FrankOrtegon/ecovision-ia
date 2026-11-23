# Evaluación

Estado: pendiente (Fase 4). No hay resultados todavía.

## Protocolo
- Conjunto: `test.csv`, usado una sola vez con el modelo ya seleccionado.
- Métricas: accuracy, precision/recall/F1 por clase, macro y ponderadas, matriz de confusión, ROC one-vs-rest y AUC calculadas con probabilidades por clase.
- Si una clase no tiene positivos o negativos, su AUC no se calcula y se explica.
- Salidas en `ml/results/`: etiquetas reales y predichas, probabilidades, métricas, gráficos, reporte y versión del modelo.

## Formato del CSV de evaluación de la aplicación
```
filename,true_label
img001.jpg,plastic
img002.jpg,glass
```
UTF-8, cabecera obligatoria, etiquetas entre: cardboard, glass, metal, paper, plastic, trash.

## Resultados y análisis
Pendiente de ejecución.
