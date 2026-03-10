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
# Búsqueda básica
python main.py --query "restaurantes" --location "CDMX"

# Con opciones
python main.py \
  --query "dentistas" \
  --location "Monterrey" \
  --max-results 10 \
  --format json \
  --output ./resultados

# Ver navegador (sin headless)
python main.py --query "cafés" --location "Guadalajara" --no-headless
```

## Opciones

| Opción | Alias | Default | Descripción |
|---|---|---|---|
| `--query` | `-q` | *requerido* | Tipo de negocio |
| `--location` | `-l` | *requerido* | Ciudad/zona |
| `--max-results` | `-n` | `20` | Máximo de resultados |
| `--format` | `-f` | `both` | `csv`, `json`, o `both` |
| `--output` | `-o` | `./output` | Directorio de salida |
| `--headless` | | `true` | `--no-headless` para ver el navegador |

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

## Licencia

MIT
