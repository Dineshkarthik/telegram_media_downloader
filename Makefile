TEST_ARTIFACTS ?= /tmp/coverage

# Detect Python version and set appropriate requirements file
PYTHON_VERSION := $(shell python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
REQUIREMENTS_FILE := requirements-$(PYTHON_VERSION).txt
DEV_REQUIREMENTS_FILE := dev-requirements-$(PYTHON_VERSION).txt

# Fallback to generic requirements.txt if version-specific file doesn't exist
ifeq ($(wildcard $(REQUIREMENTS_FILE)),)
REQUIREMENTS_FILE := requirements.txt
endif
ifeq ($(wildcard $(DEV_REQUIREMENTS_FILE)),)
DEV_REQUIREMENTS_FILE := dev-requirements.txt
endif

.PHONY: install dev_install static_type_check pylint style_check test show_version

show_version:
	@echo "Python version: $(PYTHON_VERSION)"
	@echo "Using requirements file: $(REQUIREMENTS_FILE)"
	@echo "Using dev requirements file: $(DEV_REQUIREMENTS_FILE)"

install:
	python3 -m pip install --upgrade pip setuptools
	python3 -m pip install -r $(REQUIREMENTS_FILE)

dev_install: install
	python3 -m pip install -r $(DEV_REQUIREMENTS_FILE)

static_type_check:
	python3 -m mypy media_downloader.py utils --ignore-missing-imports

pylint:
	python3 -m pylint media_downloader.py utils -r y

style_check: static_type_check pylint

test:
	python3 -m pytest --cov media_downloader --doctest-modules \
		--cov utils \
		--cov-report term-missing \
		--cov-report html:${TEST_ARTIFACTS} \
		--junit-xml=${TEST_ARTIFACTS}/media-downloader.xml \
		tests/
