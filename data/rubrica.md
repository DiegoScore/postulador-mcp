# Rúbrica de evaluación de ofertas

Calibrada con 5 ofertas reales de AI/ML en Chile.

## Reglas inviolables
1. Usa SOLO lo que está en el perfil (get_profile). Si algo no aparece, es una brecha, no una suposición.
2. Nunca inventes experiencia, años, métricas ni herramientas. Nunca sugieras responder algo falso en un formulario.
3. Los bullets se eligen por id; no se redactan bullets nuevos.
4. Evita bullets con `revisar_metrica: true` salvo que aporten algo que ningún otro bullet cubre.
5. Las experiencias de tipo "proyecto de investigación" no se presentan como "modelo en producción".

## Puntaje (0-100)
Parte en 50 y ajusta:
- Requisitos obligatorios cumplidos con evidencia en bullets: +5 a +8 cada uno (núcleo del rol pesa más).
- Requisito obligatorio solo "listado" en habilidades, sin bullet que lo respalde: +0 a +2.
- Requisito obligatorio ausente: -5 a -10 (más si es el núcleo del rol o aparece como bloque entero, ej. un stack cloud completo que el perfil no tiene).
- Años exigidos: dentro del rango 0; bajo por <1 año -5; bajo por más -10.
- Deseables cumplidos: +1 a +3 cada uno. Diferencial fuerte (ej. LLMs/agentes en un rol de DS clásico): +3 a +5.
- Modalidad incompatible o empresa excluida (perfil.filtros.empresas_excluidas): descartar.

Referencias: ≥80 calce muy alto (postular con prioridad) · 70-79 postular · 60-69 postular con prioridad baja · <65 umbral del perfil, normalmente descartar.

## Variantes
Las variantes disponibles están en `variantes` del perfil. Criterio general:
- ai_engineer: agentes, LLMs, IA generativa, rol "AI Engineer" generalista.
- ai_backend: backend + IA (APIs, microservicios, integración de agentes).
- ml_data: ML/DL clásico, data science, predicción, clasificación, pipelines de datos.
- fullstack: desarrollo web donde la IA es secundaria (si el perfil la define).

## Formato de salida (save_evaluation)
- empresa, cargo, url
- puntaje (int)
- variante
- bullets: lista ordenada de ids (6-9), lo más relevante primero
- calce: lista de frases cortas (requisito -> evidencia)
- brechas: lista ordenada de mayor a menor peso, con cómo enmarcarla honestamente
- respuestas: dict con borradores (ej. "por_que_empresa", preguntas del formulario). Basadas solo en el perfil.

## Patrones observados en el mercado (para recomendar mejoras de portafolio)
- Segmentación / no supervisado.
- GCP (Vertex AI, BigQuery, Cloud Run).
- MLOps (MLflow, monitoreo, drift, CI/CD para ML).
- AWS (Lambda, API Gateway, S3, Bedrock) + FastAPI.
- MCP.
