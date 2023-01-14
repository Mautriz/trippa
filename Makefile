SRC_DIR		= src
TEST_DIR	= tests
CHECK_DIRS  = $(SRC_DIR) $(TEST_DIR)

.PHONY: check
check: format-check lint type-check test ## Launch all the checks (formatting, linting, type checking)

.PHONY: install
install: ## Install the dependencies from the lock file
	poetry run pip install --upgrade pip
	poetry install -v

.PHONY: update
update: ## Update python dependencies
	poetry update

.PHONY: format
format: ## Format repository code
	poetry run black $(CHECK_DIRS)
	poetry run isort $(CHECK_DIRS)

.PHONY: format-check
format-check: ## Check the code format with no actual side effects
	poetry run black --check $(CHECK_DIRS)
	poetry run isort --check $(CHECK_DIRS)

.PHONY: lint
lint: ## Launch the linting tool
	poetry run ruff $(SRC_DIR)
	poetry run ruff $(TEST_DIR)

.PHONY: type-check
type-check: ## Launch the type checking tool
	poetry run mypy $(CHECK_DIRS)

.PHONY: test
test: export APP_ENV = test
test: ## Launch the tests
	poetry run python -m pytest -s -vv tests

.PHONY: help
help: ## Show the available commands
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
