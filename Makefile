.PHONY: help style test-style test-func test-integration test report report-html clean-coverage

help:
	@echo "Targets:"
	@echo "  style             Auto-fix: ruff format + ruff check --fix on src/ + tests/"
	@echo "  test-style        Verify: ruff format --check + ruff check + ty check (no writes)"
	@echo "  test-func         Run pytest on tests/ (skips integration markers)"
	@echo "  test-integration  Run only integration tests (real cognee + LLM, slow, costs tokens)"
	@echo "  test              Run test-style then test-func (style failure stops)"
	@echo "  report            Run pytest under coverage and print text report"
	@echo "  report-html       Same as report, plus write htmlcov/index.html"
	@echo "  clean-coverage    Delete .coverage data file and htmlcov/"

style:
	uv run ruff format src tests
	uv run ruff check --fix src tests

test-style:
	uv run ruff format --check src tests
	uv run ruff check src tests
	uv run ty check src tests

test-func:
	uv run python -m coverage run -m pytest tests/ -m "not integration"

test-integration:
	uv run pytest tests/integration/ -m integration

test: test-style test-func

report: test
	uv run python -m coverage report

report-html: test
	uv run python -m coverage html
	@echo "HTML report: htmlcov/index.html"

clean-coverage:
	rm -rf .coverage htmlcov
