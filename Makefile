.PHONY: install
install:
	pipenv install --dev

.PHONY: shell
shell:
	pipenv shell

.PHONY: run-all
run:
	docker-compose up

.PHONY: run-consumer
run-consumer:
	docker-compose up consumer

.PHONY: run-producer
run-producer:
	docker-compose up producer

.PHONY: test
test: test-unit test-type test-style test-deps

.PHONY: test-unit
test-unit:
	pipenv run python -m unittest

.PHONY: test-coverage
test-coverage:
	pipenv run coverage run -m unittest

.PHONY: test-coverage-html
test-coverage-html: test-coverage
	pipenv run coverage html

.PHONY: test-type
test-type:
	pipenv run mypy  --ignore-missing-imports ./consumer ./producer ./schema_registry

.PHONY: test-style
test-style:
	pipenv run autopep8 --diff --recursive --aggressive ./consumer ./producer ./schema_registry
	pipenv run flake8 --show-source ./consumer ./producer ./schema_registry

.PHONY: test-deps
test-deps:
	 pipenv check
