.PHONY: help install install-dev run test lint format clean migrate

help:
	@echo "Comandos disponibles:"
	@echo "  make install      - Instalar dependencias de producción"
	@echo "  make install-dev  - Instalar dependencias de desarrollo"
	@echo "  make run          - Correr servidor de desarrollo"
	@echo "  make test         - Ejecutar tests"
	@echo "  make lint         - Ejecutar linter"
	@echo "  make format       - Formatear código"
	@echo "  make migrate      - Ejecutar migraciones"
	@echo "  make clean        - Limpiar archivos temporales"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest tests/ -v --cov=app --cov-report=html

lint:
	flake8 app/ tests/
	mypy app/

format:
	black app/ tests/
	isort app/ tests/

migrate:
	alembic upgrade head

migrate-create:
	@if [ -z "$(msg)" ]; then \
		echo "Error: debes pasar un mensaje con msg='tu mensaje'"; \
		exit 1; \
	fi
	alembic revision --autogenerate -m "$(msg)"

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .mypy_cache

