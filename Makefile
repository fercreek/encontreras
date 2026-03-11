# encontreras — Atajos de terminal
# Usa: make run q="tacos" l="CDMX"

PYTHON = .venv/bin/python
HUEY   = .venv/bin/huey_consumer

# ── Extracción ──────────────────────────────────────
run:
	$(PYTHON) main.py run --query "$(q)" --location "$(l)" --max-results $(or $(n),10)

run-visible:
	$(PYTHON) main.py run --query "$(q)" --location "$(l)" --max-results $(or $(n),10) --no-headless

# ── Dashboard ───────────────────────────────────────
serve:
	$(PYTHON) main.py serve --reload

worker:
	$(HUEY) src.core.tasks.huey

# ── IA & Notion ─────────────────────────────────────
synthesize:
	$(PYTHON) main.py synthesize

notion-sync:
	$(PYTHON) main.py notion-sync

# ── Utilidades ──────────────────────────────────────
install:
	python3 -m venv .venv
	.venv/bin/pip install -e .
	.venv/bin/playwright install chromium
	@echo "✔ Listo. Usa: make serve"

test:
	$(PYTHON) -m pytest

help:
	@echo ""
	@echo "  make run q=\"tacos\" l=\"CDMX\"     Extrae negocios"
	@echo "  make run-visible q=\"...\" l=\"...\" Extrae con navegador visible"
	@echo "  make serve                      Dashboard en :8888"
	@echo "  make worker                     Worker de Huey"
	@echo "  make synthesize                 IA analiza prospectos"
	@echo "  make notion-sync                Sube a Notion"
	@echo "  make install                    Setup desde cero"
	@echo "  make test                       Corre pytest"
	@echo ""

.PHONY: run run-visible serve worker synthesize notion-sync install test help
