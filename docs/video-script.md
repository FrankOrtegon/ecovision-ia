# Guion del video (máximo 10 minutos)

Todas las cifras salen de `docs/Informe_EcoVision_IA.pdf` y de `ml/results/`. Si se vuelve a evaluar, regenerar el informe y actualizar este guion.

| Tiempo | Contenido | Qué se muestra |
|---|---|---|
| 0:00–1:00 | Problema y objetivo: identificar mal un material dificulta su separación; el sistema clasifica el material aparente y no decide si es reciclable | Módulo Inicio |
| 1:00–2:30 | Dataset TrashNet: 2527 imágenes, 6 clases, desequilibrio (otros residuos 5,42 %), 6 imágenes excluidas por etiquetas contradictorias, particiones 70/15/15 sin fuga | Figuras de distribución y ejemplos; `dataset.md` |
| 2:30–4:30 | Entrenamiento en Roboflow: ResNet50, línea base frente a aumento de datos, comparación solo con validación (McNemar p = 0,678), elección del modelo 1 | Proyecto en Roboflow, receta de aumento, tabla de validación |
| 4:30–6:00 | Evaluación final sobre prueba (379 imágenes): exactitud 88,65 %, F1 macro 0,856, AUC macro 0,980; clase otros residuos F1 0,619; confusión papel→cartón; sobreconfianza | Matriz de confusión, ROC y PR; diagrama de fiabilidad |
| 6:00–8:30 | Demostración en vivo: clasificar una imagen real; lote con un archivo inválido; evaluación del conjunto de prueba con CSV (mismas cifras que el script); Acerca del modelo | Aplicación desplegada |
| 8:30–9:30 | Arquitectura y seguridad: la clave solo en el backend, validación de entradas, 100 pruebas automatizadas, contenedor Docker, Render y Vercel | Diagrama, `/docs` de la API |
| 9:30–10:00 | Limitaciones (dominio, clase minoritaria, probabilidades omitidas, calibración) y trabajo futuro | Diapositiva final |

Consejos: grabar con la aplicación ya "despierta" (Render gratuito tarda ~1 minuto tras 15 minutos sin tráfico) y tener las imágenes de la demostración preparadas.
