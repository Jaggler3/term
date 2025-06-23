.PHONY: install run dev clean format lint type-check check-all build publish

TOML_FILE := pyproject.toml
SETUP_FILE := setup.py


# Extract version from file
get-version:
	@grep -E '^version *= *"' $(TOML_FILE) | sed -E 's/.*"([0-9]+\.[0-9]+\.[0-9]+)".*/\1/'

bump-patch:
	@current=$$(make get-version); \
	new_version=$$(echo $$current | awk -F. '{ printf "%d.%d.%d", $$1, $$2, $$3+1 }'); \
	echo "Bumping patch: $$current -> $$new_version"; \
	make bump-version VERSION=$$new_version

bump-minor:
	@current=$$(make get-version); \
	new_version=$$(echo $$current | awk -F. '{ printf "%d.%d.%d", $$1, $$2+1, 0 }'); \
	echo "Bumping minor: $$current -> $$new_version"; \
	make bump-version VERSION=$$new_version

bump-major:
	@current=$$(make get-version); \
	new_version=$$(echo $$current | awk -F. '{ printf "%d.%d.%d", $$1+1, 0, 0 }'); \
	echo "Bumping major: $$current -> $$new_version"; \
	make bump-version VERSION=$$new_version

bump-version:
	@if [ -z "$(VERSION)" ]; then \
		echo "Usage: make bump-version VERSION=x.y.z"; \
		exit 1; \
	fi; \
	if ! echo "$(VERSION)" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+$$'; then \
		echo "Invalid version format: $(VERSION)"; \
		exit 1; \
	fi; \
	echo "Updating version to $(VERSION)"; \
	sed -i.bak 's/version = "[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*"/version = "$(VERSION)"/' $(TOML_FILE); \
	rm -f $(TOML_FILE).bak; \
	sed -i.bak 's/VERSION = "[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*"/VERSION = "$(VERSION)"/' $(SETUP_FILE); \
	rm -f $(SETUP_FILE).bak; \
	echo "Version bumped to: $(VERSION)"





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

build:
	python setup.py sdist bdist_wheel

publish:
	twine upload dist/* --config-file .pypirc

release:
	rm -rf dist
	make build
	make publish