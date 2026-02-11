# Makefile for common development tasks

.PHONY: help install migrate run test clean format lint docker-build docker-run

help:
	@echo "Data Management Service - Available Commands:"
	@echo "  make install       - Install dependencies"
	@echo "  make migrate       - Run database migrations"
	@echo "  make run           - Run development server"
	@echo "  make test          - Run tests"
	@echo "  make clean         - Clean up cache files"
	@echo "  make format        - Format code with black"
	@echo "  make lint          - Run linting checks"
	@echo "  make shell         - Open Django shell"
	@echo "  make superuser     - Create superuser"

install:
	pip install -r requirements.txt

migrate:
	python manage.py makemigrations
	python manage.py migrate

run:
	python manage.py runserver

test:
	python manage.py test

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage

format:
	black .
	isort .

lint:
	flake8 .
	black --check .
	isort --check-only .

shell:
	python manage.py shell

superuser:
	python manage.py createsuperuser

collectstatic:
	python manage.py collectstatic --noinput

check:
	python manage.py check
	python manage.py check --deploy
