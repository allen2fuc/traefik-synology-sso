.PHONY: install dev test lint clean

install:
	uv sync

dev:
	uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

test:
	uv run pytest tests/ -v

lint:
	uv run ruff check app/ tests/

# Mac (Apple Silicon) 默认构建 arm64，部署到 Intel NAS/云主机需指定 amd64
build:
	docker build --platform linux/amd64 -t uhub.service.ucloud.cn/allen2fuc/traefik-synology-sso:latest .

push: 
	docker push uhub.service.ucloud.cn/allen2fuc/traefik-synology-sso:latest

run:
	docker compose up -d

stop:
	docker compose down

restart:
	docker compose restart
clean:
	rm -rf .venv __pycache__ .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
