# encontreras 🎯 | Autonomous Outbound Agent

*[English version below](#english-version)*

**Encontreras** es un Agente Autónomo (PoC) en Python diseñado para la extracción, enriquecimiento y evaluación semántica de prospectos comerciales (B2B Lead Generation). 

## 🎯 Finalidad: De un Scraper a un Agente de Inteligencia

La mayoría de las herramientas de extracción se limitan a descargar listas vacías de Google Maps. **Encontreras** fue diseñado con una mentalidad de **Inteligencia de Ventas (Outbound)**. Su objetivo es demostrar cómo se puede *abstraer información de valor y contexto* a partir de la huella digital pública de un negocio, antes de realizar el primer contacto.

En lugar de solo darte un teléfono, la herramienta perfila al prospecto: ¿Su página web está optimizada? ¿Están activos en redes sociales? ¿Tienen buenas reseñas pero mala presencia digital? Esta información es oro para redactar mensajes en frío (Cold DMs/Emails) sumamente personalizados.

---

## ⚙️ ¿Cómo Funciona? (El Pipeline)

El sistema opera como un embudo de enriquecimiento en cascada:

1. **Scraping Base (Google Maps)**: Extrae el NAP (Name, Address, Phone), horarios, categoría, nivel de precios y reseñas de los negocios en una ciudad específica.
2. **Auditoría y Enriquecimiento Web**: Navega automáticamente a la página web del negocio (si tiene). Extrae correos electrónicos, encuentra sus redes sociales reales y **evalúa la salud del sitio** (ej. si la página está caída, si le falta la etiqueta H1 o si no está optimizada para celulares).
3. **Termómetro Social**: Visita sus perfiles de Instagram, TikTok y Facebook para extraer su conteo de seguidores, dando una idea de su alcance y tamaño de audiencia.
4. **Entity Resolution (Deduplicación)**: Limpia la base de datos fusionando registros duplicados usando el teléfono y el dominio web como identificadores únicos.
5. **Lead Scoring (Calificación)**: Clasifica la calidad del lead (Excelente, Rescatado, Débil) del 0 al 5 basándose en la completitud de sus datos y su huella web.

---

## 🚀 Cómo Probarlo (Prueba de Concepto)

Instala las dependencias y corre la herramienta en tu propia terminal para ver la extracción en vivo.

### 1. Instalación
```bash
# Crear y activar entorno virtual
python -m venv .venv
source .venv/bin/activate

# Instalar dependencias del proyecto
pip install -e .

# Instalar los navegadores automatizados (Playwright)
playwright install chromium
```

### 2. Ejecutar una Extracción (CLI)
Para ver la "magia" en vivo, te recomendamos correr la herramienta desactivando el modo "oculto" (headless) para que veas cómo el robot navega por las páginas.

```bash
# Ejemplo: Buscar academias en Monterrey (abriendo el navegador visualmente)
.venv/bin/python main.py run --query "academia" --location "Monterrey" --max-results 10 --no-headless
```
*Al terminar, los datos se guardarán automáticamente en la carpeta `/output` en formatos `.csv` y `.json`.*

### 3. Visualizar los Resultados (Dashboard Local)
El proyecto incluye un dashboard web interactivo para analizar y filtrar los prospectos recolectados.

```bash
# Levantar el servidor local con auto-recarga
.venv/bin/python main.py serve --reload
```
Abre **[http://localhost:8888](http://localhost:8888)** en tu navegador. 
Allí podrás ver la tabla de resultados, hacer clic en cada prospecto para ver su diagnóstico completo, y filtrar rápidamente aquellos negocios que tienen una **"Web con problemas"**.

#### 🤖 Levantar el Worker de Tareas (Opcional para extracciones desde la Web)
💡 **Novedad**: Los datos ahora se guardan en una **base de datos SQLite** (`output/encontreras.db`). Para poder lanzar extracciones directamente desde el Dashboard visual y que se procesen por debajo como colas de trabajo (Sidekiq-style), necesitas abrir una segunda terminal y prender el consumidor de Huey:

```bash
# En otra terminal (Terminal 2) con el entorno virtual activado
.venv/bin/huey_consumer src.core.tasks.huey
```

---

## 🧠 Fase 2: Inteligencia Artificial & Notion (Implementado)

### 4. Configurar Variables de Entorno

```bash
cp .env.example .env
```

Abre `.env` con tu editor y pega las 3 llaves que obtendrás a continuación:

#### 🔑 `GEMINI_API_KEY` — Google AI Studio (Gratis)
1. Ve a **[aistudio.google.com/apikey](https://aistudio.google.com/apikey)**
2. Inicia sesión con tu cuenta de Google
3. Clic en **"Create API Key"** → selecciona un proyecto (o crea uno)
4. Copia la llave (empieza con `AIza...`)

> 💡 El tier gratuito de Gemini Flash incluye ~15 requests/min y ~1M tokens/día.

#### 🔑 `NOTION_TOKEN` — Integración de Notion
1. Ve a **[notion.so/profile/integrations](https://www.notion.so/profile/integrations)**
2. Clic en **"+ Nueva integración"** → nómbrala `encontreras-sync`
3. Asegúrate de que tenga permisos de **Leer**, **Insertar** y **Actualizar contenido**
4. Copia el **Internal Integration Secret** (empieza con `ntn_...`)
5. ⚠️ **Paso extra**: Abre tu base de datos Sniper List en Notion → `•••` → **Conexiones** → **Conectar a** → `encontreras-sync`

#### 🔑 `NOTION_DATABASE_ID` — El ID de tu Sniper List
1. Abre tu base de datos "Sniper List" en el **navegador**
2. Copia la URL, que se ve así:
   ```
   https://www.notion.so/tu-workspace/abc123def456...?v=xyz
                                       ^^^^^^^^^^^^^^^^
                                       ESTE es tu Database ID
   ```
3. El ID es la cadena de 32 caracteres **después del último `/`** y **antes del `?`**

### 5. Analizar Prospectos con IA (Gemini Flash)
Ejecuta la IA sobre los prospectos con Score ≥ 3 para generar contexto, análisis y un DM personalizado:
```bash
.venv/bin/python main.py synthesize
```

### 6. Sincronizar a Notion (Sniper List)
Envía los prospectos ya analizados a tu base de datos de Notion:
```bash
.venv/bin/python main.py notion-sync
```

---

# English Version

**Encontreras** is an Autonomous Agent (Proof of Concept) in Python designed for the extraction, enrichment, and semantic evaluation of B2B sales prospects.

## 🎯 Purpose: From Scraper to Intelligence Agent

Most extraction tools are limited to downloading empty lists from Google Maps. **Encontreras** was built with an **Outbound Sales Intelligence** mindset. Its goal is to demonstrate how to *abstract valuable information and context* from a business's public digital footprint before making the first contact.

Instead of just giving you a phone number, the agent profiles the prospect: Is their website optimized? Are they active on social media? Do they have good reviews but a poor digital presence? This information is gold for crafting highly personalized Cold DMs/Emails.

---

## ⚙️ How it Works (The Pipeline)

The system operates as a cascading enrichment funnel:

1. **Base Scraping (Google Maps)**: Extracts NAP (Name, Address, Phone), hours, category, price level, and reviews of businesses in a specific city.
2. **Web Audit & Enrichment**: Automatically navigates to the business's website (if available). Extracts emails, finds real social media links, and **evaluates site health** (e.g., if the page is down, missing an H1 tag, or not mobile-optimized).
3. **Social Thermometer**: Visits their Instagram, TikTok, and Facebook profiles to extract follower counts, providing a proxy for their reach and audience size.
4. **Entity Resolution (Deduplication)**: Cleans the database by merging duplicate records using phone numbers and web domains as unique identifiers.
5. **Lead Scoring**: Classifies lead quality (Excellent, Rescued, Weak) from 0 to 5 based on data completeness and their digital footprint.

---

## 🚀 How to Test It (Proof of Concept)

Install the dependencies and run the agent in your own terminal to see the live extraction.

### 1. Installation
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install project dependencies
pip install -e .

# Install automated browsers (Playwright)
playwright install chromium
```

### 2. Run an Extraction (CLI)
To see the "magic" live, we recommend running the tool with the "headless" mode disabled so you can watch the robot navigate the pages.

```bash
# Example: Search for dance academies in Monterrey (opening the browser visually)
.venv/bin/python main.py run --query "academia" --location "Monterrey" --max-results 10 --no-headless
```
*Upon completion, data is automatically saved in the `/output` folder in `.csv` and `.json` formats.*

### 3. View Results (Local Dashboard)
The project includes an interactive web dashboard to analyze and filter the collected prospects.

```bash
# Start the local server with hot-reload
.venv/bin/python main.py serve --reload
```
Open **[http://localhost:8888](http://localhost:8888)** in your browser. 
There you can view the results table, click on each prospect for a full diagnostic, and quickly filter businesses that have a **"Website with issues"**.

#### 🤖 Start the Background Worker (Optional for Web Extractions)
💡 **New Feature**: Data is now persistently saved to a local **SQLite database** (`output/encontreras.db`). To trigger new background extractions directly from the Dashboard UI form via job queues (Sidekiq-style), open a second terminal and start the Huey consumer:

```bash
# In another terminal (Terminal 2) with the virtual environment activated
.venv/bin/huey_consumer src.core.tasks.huey
```

---

## 🧠 Phase 2: AI Intelligence & Notion Sync (Implemented)

### 4. Set Up Environment Variables

```bash
cp .env.example .env
```

Open `.env` with your editor and paste the 3 keys you'll obtain below:

#### 🔑 `GEMINI_API_KEY` — Google AI Studio (Free)
1. Go to **[aistudio.google.com/apikey](https://aistudio.google.com/apikey)**
2. Sign in with your Google account
3. Click **"Create API Key"** → select a project (or create one)
4. Copy the key (starts with `AIza...`)

> 💡 The free tier of Gemini Flash includes ~15 requests/min and ~1M tokens/day.

#### 🔑 `NOTION_TOKEN` — Notion Integration
1. Go to **[notion.so/profile/integrations](https://www.notion.so/profile/integrations)**
2. Click **"+ New integration"** → name it `encontreras-sync`
3. Make sure it has **Read**, **Insert**, and **Update content** permissions
4. Copy the **Internal Integration Secret** (starts with `ntn_...`)
5. ⚠️ **Extra step**: Open your Sniper List database in Notion → `•••` → **Connections** → **Connect to** → `encontreras-sync`

#### 🔑 `NOTION_DATABASE_ID` — Your Sniper List ID
1. Open your "Sniper List" database in the **browser**
2. Copy the URL, which looks like:
   ```
   https://www.notion.so/your-workspace/abc123def456...?v=xyz
                                         ^^^^^^^^^^^^^^^^
                                         THIS is your Database ID
   ```
3. The ID is the 32-character string **after the last `/`** and **before the `?`**

### 5. Analyze Prospects with AI (Gemini Flash)
Run AI synthesis on leads with Score ≥ 3 to generate context, analysis, and a personalized DM:
```bash
.venv/bin/python main.py synthesize
```

### 6. Sync to Notion (Sniper List)
Push AI-analyzed leads to your Notion database:
```bash
.venv/bin/python main.py notion-sync
```

---
*Open Source / MIT License*
