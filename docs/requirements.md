# Requisitos, contexto y objetivos

## Contexto
Instituciones educativas y organizaciones con programas de gestión ambiental necesitan identificar correctamente los materiales para separarlos y aprovecharlos. Usuarios: estudiantes, docentes, personal administrativo y responsables de sostenibilidad.

## Problema
La identificación incorrecta del material dificulta su separación y aprovechamiento.

## Objetivo general
Desarrollar y desplegar una aplicación web que clasifique imágenes de residuos en seis categorías de material aparente con un modelo de visión por computador entrenado con TrashNet, e informe su rendimiento con métricas verificables.

## Objetivos específicos
1. Preparar y documentar el dataset TrashNet con particiones estratificadas 70/15/15 (semilla 42) sin fuga de datos.
2. Entrenar y seleccionar un clasificador en Roboflow justificando los ajustes.
3. Evaluar el modelo sobre un conjunto de prueba independiente con precision, recall, F1, matriz de confusión, ROC y AUC.
4. Exponer el modelo mediante una API REST en FastAPI sin exponer credenciales.
5. Construir una interfaz en español para clasificación individual, por lotes, evaluación e información del modelo.
6. Desplegar el sistema en la nube y documentar la evidencia.

## Alcance y límites
El sistema no determina si un residuo es reciclable. Clasifica el tipo de material aparente según las categorías aprendidas.

## Requisitos
La lista completa de requisitos funcionales, no funcionales y criterios de aceptación está en `.kiro/specs/ecovision-ia/requirements.md`.

## Justificación y utilidad
Pendiente de redactar con referencias verificadas en la Fase 9 (informe APA 7).
