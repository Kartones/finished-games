.PHONY: default deps base build stop shell test coverage run statics

export SERVICE_NAME := finished-games

BUILD_ENV ?= dev

HISTORY_FILE := ~/.bash_history.$(SERVICE_NAME)

# Required for the `deps` task
SHELL := $(shell which bash)

DOCKER := $(shell command -v docker)
COMPOSE := $(shell command -v docker) compose

COMPOSE_ENV := $(COMPOSE) -f build/$(BUILD_ENV)/docker-compose.yml
COMPOSE_CMD := $(COMPOSE_ENV) run --rm $(SERVICE_NAME)

export GID := $(shell id -g)
export UID := $(shell id -u)

deps:
ifndef DOCKER
	@echo "Docker is not available. Please install docker"
	@exit 1
endif
ifndef COMPOSE
	@echo "docker-compose is not available. Please install docker-compose"
	@exit 1
endif
	@touch $(HISTORY_FILE)

base: deps
	$(COMPOSE) -f build/base/docker-compose.yml build

build: base
	$(COMPOSE_ENV) build

stop:
	$(COMPOSE_ENV) stop
	$(COMPOSE_ENV) rm -f -v

shell: build
	$(COMPOSE_CMD) /bin/bash

run: build
	$(COMPOSE_ENV) run --rm --service-ports $(SERVICE_NAME);$(COMPOSE_ENV) stop

# remove -s flag if there is noise, but initially is handy for print() statements while building tests
test: build
	set -o pipefail; \
	$(COMPOSE_CMD) pytest -s

# opening html file currently only works on Linux
coverage: build
	set -o pipefail; \
	$(COMPOSE_CMD) pytest --cov-report html:../cov_html --cov=.; \
	xdg-open cov_html/index.html

statics: build
	$(COMPOSE_CMD) python3 manage.py collectstatic ${collectargs}