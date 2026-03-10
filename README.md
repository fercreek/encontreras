# encontreras

🔍 CLI Open Source para extraer y enriquecer datos de negocios desde Google Maps.

## Instalación

```bash
# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate

# Instalar dependencias
pip install -e .

# Instalar navegadores de Playwright
playwright install chromium
```

## Uso

```bash
# Búsqueda básica (Monterrey)
.venv/bin/python main.py run --query "restaurantes" --location "Monterrey" --max-results 20 --no-headless

# Con más opciones
.venv/bin/python main.py run \
  --query "dentistas" \
  --location "Monterrey" \
  --max-results 10 \
  --format json \
  --output ./resultados

# Modo headless (sin abrir navegador)
.venv/bin/python main.py run --query "cafés" --location "Monterrey" --max-results 20

# Abrir dashboard web para ver resultados
.venv/bin/python main.py serve
# Luego abre http://localhost:8888
```

> **Nota:** Usa `.venv/bin/python` directamente en lugar de `source .venv/bin/activate` para evitar problemas de shell.

## Opciones del comando `run`

| Opción | Alias | Default | Descripción |
|---|---|---|---|
| `--query` | `-q` | *requerido* | Tipo de negocio |
| `--location` | `-l` | *requerido* | Ciudad/zona |
| `--max-results` | `-n` | `20` | Máximo de resultados |
| `--format` | `-f` | `both` | `csv`, `json`, o `both` |
| `--output` | `-o` | `./output` | Directorio de salida |
| `--headless` | | `true` | `--no-headless` para ver el navegador |

## Opciones del comando `serve`

| Opción | Alias | Default | Descripción |
|---|---|---|---|
| `--output` | `-o` | `./output` | Directorio con los JSON |
| `--port` | `-p` | `8888` | Puerto del servidor |

## Pipeline

1. **Extracción** — Scrape de Google Maps (nombre, teléfono, web, dirección, rating)
2. **Enriquecimiento Web** — Visita cada sitio web para extraer emails e Instagram/TikTok/Facebook
3. **Enriquecimiento Social** — Visita perfiles sociales para obtener conteo de seguidores
4. **Entity Resolution** — Deduplica usando teléfono y dominio como llaves primarias
5. **Exportación** — Guarda resultados en CSV y/o JSON

## Estructura

```
encontreras/
├── main.py                    # CLI (Typer)
├── src/
│   ├── pipeline.py            # Orquestación del pipeline
│   ├── core/
│   │   ├── config.py          # Configuración, selectores, regex
│   │   ├── models.py          # Modelo de datos Business
│   │   ├── entity_resolution.py  # Deduplicación
│   │   └── exporter.py        # CSV/JSON export
│   └── extractors/
│       ├── google_maps.py     # Scraper de Google Maps
│       ├── website.py         # Enricher de sitios web
│       └── social.py          # Enricher de redes sociales
└── pyproject.toml
```

## Roadmap y Prueba de Concepto (PoC)

El proyecto está diseñado en dos fases, demostrando cómo se puede abstraer e inferir información de valor a partir de presencia digital pública.

### Fase 1: Extracción y Heurísticas Básicas (Actual)
Prueba de concepto funcional orientada a la recolección de datos puros y evaluación heurística.
- **Scraping Base**: Extracción de Google Maps (nombre, teléfono, ubicación, horarios, categoría).
- **Enriquecimiento Digital**: Rastreo de sitios web para detectar emails, redes sociales e hipervínculos de contacto.
- **Evaluación de Salud Web**: Análisis automatizado de status HTTP y SEO técnico básico (H1, Viewport móvil), útil para identificar *pain points* obvios.
- **Lead Scoring Heurístico**: Algoritmos basados en palabras clave y completitud de datos (del 0 al 5) para separar negocios reales de listados vacíos o spam.

### Fase 2: Abstracción Profunda y Análisis Semántico (En Desarrollo)
Evolución de la herramienta hacia un modelo de abstracción de datos avanzado, enfocado en medir el alcance real sin depender únicamente de métricas de vanidad.
- **Anatomía de Audiencias**: Abstracción de métricas más profundas en redes sociales (seguidores, cuentas seguidas, frecuencia y tipo de interacción) para inferir la madurez digital del prospecto.
- **Contexto de Negocio Inteligente**: Capacidades para entender no solo *qué* venden, sino a *quién* y *cómo* se posicionan, todo extraído implícitamente de sus rastros web y sociales.
- **Resolución de Entidades Avanzada**: Fusión de presencias digitales parciales y fracturadas de una empresa utilizando indicadores asimétricos.
- **Calificación Dinámica**: Transición de reglas duras a un modelo de *identificación de oportunidades* adaptable al nicho buscado (por ejemplo, detectar de manera automática que una página web mal estructurada pero con alto seguimiento social es un lead ideal para servicios de diseño web).

## Licencia

MIT
