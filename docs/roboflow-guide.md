# Guía paso a paso: entrenamiento en Roboflow (Fase 3)

Verificada contra la documentación de Roboflow el 2026-11-23. Los nombres exactos de menús pueden variar un poco. Si algo no coincide, tómale captura y se ajusta la guía.

## Hechos verificados que condicionan el plan
- Arquitecturas de clasificación disponibles: ViT (Base), ResNet (18/34/50/101) y DINOv3 (Base, Small), con resolución por defecto 224x224.
- En clasificación, la métrica que muestra Roboflow tras entrenar es Accuracy. La evaluación detallada (matriz de confusión por clase) es de planes de pago, por eso el análisis científico se hace en `ml/evaluation` con scikit-learn.
- Una versión del dataset es una instantánea congelada. El preprocesamiento y el aumento de datos se configuran al generarla.
- Costos en créditos (https://roboflow.com/credits): 1 crédito = 10 000 imágenes subidas, o 20 000 imágenes creadas en versiones, o 30 minutos de entrenamiento en GPU. Roboflow muestra el costo estimado antes de entrenar; anótalo.
- Plan gratuito: los proyectos son públicos. TrashNet es MIT y las imágenes ya son públicas, así que no hay problema. Revisa los créditos mensuales vigentes en https://roboflow.com/pricing (las fuentes de terceros discrepan entre 10 y 15).

## Paso 1. Crear el proyecto
1. Entra a https://app.roboflow.com y crea (o elige) un workspace.
2. Crea un proyecto nuevo. Nombre sugerido: `ecovision-trashnet`.
3. Tipo de proyecto: **Classification (Single-Label)**.
4. Licencia: la que ofrezca la pantalla. MIT es coherente con TrashNet.
5. 📸 Captura: pantalla del proyecto recién creado.

## Paso 2. Subir las imágenes con las particiones ya definidas
1. En tu equipo, el contenido está en `ml/data/roboflow_upload/` (y empaquetado en `ml/data/roboflow_upload.zip`). Si no existen, ejecuta `04_prepare_roboflow_upload.py`.
2. En el proyecto, ve a **Upload** y arrastra la carpeta `roboflow_upload` completa (o el ZIP). Roboflow toma el split de los nombres de carpeta `train`, `valid`, `test` y la clase del nombre de subcarpeta.
3. Cuando termine el procesamiento, **Save and Continue** o equivalente.
4. Verifica en el dataset:
   - 2521 imágenes en total.
   - 6 clases con estos nombres exactos: cardboard, glass, metal, paper, plastic, trash.
   - Split: train 1764, valid 378, test 379.
   - Por clase (train/valid/test): cardboard 283/60/60, glass 348/75/75, metal 286/62/61, paper 415/88/91, plastic 336/72/72, trash 96/21/20.
5. **No uses ninguna opción de "rebalancear" o "re-split"**. Las particiones ya están fijadas y auditadas.
6. Si los conteos no coinciden, detente y avísame con una captura.
7. 📸 Captura: vista del dataset con conteos por clase y por split.

## Paso 3. Versión 1 (línea base, sin aumento de datos)
1. Ve a **Versions** y crea una versión nueva.
2. Preprocesamiento: Auto-Orient y Resize a 224x224 (el tamaño por defecto de los modelos de clasificación).
3. Aumento de datos: **ninguno**.
4. Genera la versión. Anota el número (será `1`).
5. Entrena: **Train**, arquitectura **ResNet-50** (coherente con el material de la Unidad 2), checkpoint público por defecto.
6. Anota el costo estimado en créditos antes de confirmar.
7. Al terminar, anota: fecha y hora, accuracy, y guarda las curvas de entrenamiento.
8. 📸 Capturas: configuración de la versión, pantalla de entrenamiento y resultados.

## Paso 4. Versión 2 (con aumento de datos solo en entrenamiento)
1. Crea una nueva versión con el mismo preprocesamiento que la v1.
2. Aumentos recomendados (solo los que Roboflow ofrezca para clasificación): volteo horizontal y vertical, rotación moderada (±15°), y brillo/exposición leves. Evita cambios de tono (hue), porque el color ayuda a distinguir cartón, vidrio y plástico.
3. Confirma que los aumentos se aplican solo a train. Tras generarla, valid debe seguir en 378 y test en 379.
4. Entrena con **la misma arquitectura (ResNet-50)**, para que la única diferencia entre v1 y v2 sea el aumento.
5. Anota los mismos datos que en la v1.

## Paso 5. Versión 3 (opcional, otra arquitectura)
Si los créditos alcanzan, entrena la versión con mejores resultados de validación usando **ViT Base** y compara. Cambia una sola cosa por experimento. Si no hay créditos suficientes, se documenta como limitación.

## Paso 6. Selección
1. Compara solo la accuracy de **validación** (no mires test).
2. Si hay empate o diferencias muy pequeñas, elige el modelo más simple y justifícalo.
3. Anota la versión elegida. Su `model_id` tiene el formato `proyecto/versión`, por ejemplo `ecovision-trashnet/2`.

## Paso 7. Credenciales y datos que debes darme
1. Obtén tu **Private API Key** en Roboflow (Settings, sección API; el workspace ID está en esa misma página).
2. **No me pegues la API key en el chat.** Crea el archivo `backend/.env` copiando `backend/.env.example` y escribe ahí:
   ```
   ROBOFLOW_API_KEY=tu_clave
   ROBOFLOW_MODEL_ID=proyecto/versión
   ```
   `.env` está en `.gitignore`.
3. Si la clave llegó a mostrarse en una captura o en el chat, regenérala.
4. Pégame en el chat estos datos (no son secretos): workspace, nombre del proyecto, versión elegida y versiones entrenadas con su accuracy de validación, fecha de entrenamiento, arquitectura, preprocesamiento, aumentos y créditos usados.

## Evidencias a guardar
Guarda las capturas en `docs/evidence/` con nombre `fase3_<descripcion>.png`.

| Evidencia | Para la rúbrica |
|---|---|
| Proyecto creado | Criterio 3 |
| Dataset con conteos por clase y split | Criterios 2 y 3 |
| Configuración de cada versión (preproceso, aumento) | Criterio 3 |
| Curvas y accuracy de cada entrenamiento | Criterio 3 |
| Versión seleccionada y su model_id | Criterios 3 y 4 |
