TEST_ARTIFACTS ?= /tmp/coverage

.PHONY: install dev_install static_type_check pylint style_check test

install:
	python3 -m pip install --upgrade pip setuptools
	python3 -m pip install -r requirements.txt

dev_install: install
	python3 -m pip install -r dev-requirements.txt

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
