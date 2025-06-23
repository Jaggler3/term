.PHONY: install run dev clean format lint type-check check-all

install:
	pip install -r requirements.txt
	pip install -e .

run:
	piko
	
dev:
	python watch.py watchmedo auto-restart --directory=./piko --pattern="*.py" --recursive -- piko

clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -exec rm -r {} +

# Formatting and linting commands
format:
	black .
	isort .

lint:
	ruff check . --fix

type-check:
	mypy .

check-all: format lint type-check

