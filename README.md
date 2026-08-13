# Bicycle Orders API

Servicio de pedidos de bicicletas diseñado como proyecto final de Arquitectura Hexagonal/Limpia. Permite crear, consultar y avanzar el estado de un pedido: `pending → confirmed → shipped`, o cancelar antes del envío.

## Entregables y diseño

- Capas: `domain` (entidades/reglas), `application` (casos de uso/puertos) e `infrastructure` (SQLAlchemy, configuración, eventos); `api.py` es el adaptador HTTP.
- FastAPI con OpenAPI/Swagger (`/docs`), JWT Bearer y validación de entrada.
- Pruebas unitarias, de contrato OpenAPI/HTTP e integración de repositorio.
- Alembic, Docker multi-stage, Docker Compose, CI de GitHub, lint, tipado, cobertura y auditoría `pip-audit`.
- Métricas Prometheus en `/metrics`, healthcheck en `/health` y eventos estructurados por logging.

Consulta [la arquitectura](docs/architecture.md) y las [medidas de seguridad](docs/security.md).

## Inicio rápido

Requiere Python 3.12 y Poetry.

```bash
cp .env.example .env
poetry install
poetry run alembic upgrade head
poetry run uvicorn practica_final.api:app --reload
```

Abra `http://localhost:8000/docs`. Para probar desde terminal:

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/token | python -c "import json,sys; print(json.load(sys.stdin)['access_token'])")
curl -X POST http://localhost:8000/orders -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"customer_email":"ana@example.com","lines":[{"bicycle_model":"Gravel 400","quantity":1,"unit_price_cents":99900}]}'
```

## Calidad

```bash
poetry run pytest
poetry run ruff check .
poetry run mypy src
poetry run pip-audit
```

## Contenedores

```bash
docker compose up --build
```

La configuración por defecto usa SQLite para desarrollo. Compose prepara PostgreSQL para despliegue; ejecutar `alembic upgrade head` como paso de release/migración. En producción se deben configurar `DATABASE_URL`, un secreto JWT fuerte y HTTPS.

## Decisiones y límites

`lines_json` mantiene el ejemplo compacto; en una evolución se normalizaría a `order_lines`, se añadiría inventario/pagos y se publicaría a un broker real. Los puertos actuales permiten sustituir esos adaptadores sin modificar dominio ni casos de uso.
