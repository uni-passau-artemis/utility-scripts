# SPDX-FileCopyrightText: 2024 Artemis UniPassau Utility Scripts Contributors
#
# SPDX-License-Identifier: CC0-1.0

.PHONY: format
format:
	poetry run black src/
	poetry run isort src/

.PHONY: lint
lint:
	poetry run black --check src/
	poetry run isort --check src/
	poetry run mypy src/
	poetry run ruff check src/
	poetry run reuse lint
