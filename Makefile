.PHONY: help demo test

help:
	@echo "Makefile targets: demo, test"

demo:
	docker compose -f docker-compose.demo.yml up --build

test:
	python -m pytest -q
