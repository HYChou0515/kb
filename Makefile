.PHONY: help style test-style test-func test-integration test report report-html \
        clean clean-coverage clean-runtime clean-data clean-mock clean-all kill-stale

help:
	@echo "Targets:"
	@echo "  style             Auto-fix: ruff format + ruff check --fix on src/ + tests/"
	@echo "  test-style        Verify: ruff format --check + ruff check + ty check (no writes)"
	@echo "  test-func         Run pytest on tests/ (skips integration markers)"
	@echo "  test-integration  Run only integration tests (real cognee + LLM, slow, costs tokens)"
	@echo "  test              Run test-style then test-func (style failure stops)"
	@echo "  report            Run pytest under coverage and print text report"
	@echo "  report-html       Same as report, plus write htmlcov/index.html"
	@echo
	@echo "  kill-stale        SIGTERM/KILL leftover kb-api / opencode / openchamber procs"
	@echo "  clean             SAFE: runtime caches only (opencode_data, openchamber, __pycache__)"
	@echo "  clean-coverage    .coverage and htmlcov/"
	@echo "  clean-runtime     Alias for 'clean'"
	@echo "  clean-mock        Delete generated mock fab data CSVs (re-gen via demo.sh)"
	@echo "  clean-data        DESTRUCTIVE: autocrud + cognee + transcripts + reports +"
	@echo "                    active_sessions. ALL case studies + KB content gone. Confirms."
	@echo "  clean-all         clean + clean-coverage + clean-mock + clean-data (one confirm)"

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

# kb-api spawns opencode as a subprocess; opencode in turn spawns MCP server
# subprocesses; openchamber is its own tree. A botched Ctrl-C can leave any
# of those alive holding ports 8765 / 4096 / 3000. The script SIGTERM/SIGKILLs
# matching processes by pattern AND by port (in case process names changed).
kill-stale:
	@scripts/kill-stale.sh

# Safe to run anytime — these are pure runtime caches that demo.sh recreates.
# autocrud / cognee / transcripts / reports / active_sessions are NOT touched
# (those hold case study + KB content). Use clean-data for that.
clean: clean-runtime
clean-runtime: kill-stale
	rm -rf data/opencode_data data/openchamber
	find . -type d \( -name '__pycache__' -o -name '.pytest_cache' -o -name '.ruff_cache' \) \
		-not -path './.venv/*' -prune -exec rm -rf {} +
	@echo "removed: data/opencode_data data/openchamber __pycache__ .pytest_cache .ruff_cache"

clean-mock:
	rm -f data/mock-fab-data/*.csv data/mock-fab-data/*.json
	@echo "removed: data/mock-fab-data/*.csv (regenerable via scripts/demo.sh step 3)"

# DESTRUCTIVE — wipes every case study, every KB record, every prior RCA
# session and report. Recovery requires re-ingesting from external sources
# (primer, uploaded reports). Confirms before doing anything.
clean-data: kill-stale
	@echo "About to delete:"
	@echo "  - data/autocrud/        (every CaseStudy / Session / RCAReport / GlossaryEntry / DocumentSource)"
	@echo "  - .cognee_data/         (cognee's raw text store)"
	@echo "  - .cognee_system/       (cognee's graph + vector DB)"
	@echo "  - transcripts/          (archived session transcripts)"
	@echo "  - reports/              (rendered RCA report markdowns)"
	@echo "  - active_sessions/      (in-flight workspaces — UNFLUSHED CHANGES WILL BE LOST)"
	@printf "Type 'wipe' to confirm: " && read confirm && [ "$$confirm" = "wipe" ] || { echo "aborted."; exit 1; }
	rm -rf data/autocrud .cognee_data .cognee_system transcripts reports active_sessions
	@echo "wiped. Next demo.sh run rebuilds from scratch."

clean-all: kill-stale
	@echo "clean-all: runtime caches + coverage + mock data + ALL user data"
	@printf "Type 'wipe' to confirm: " && read confirm && [ "$$confirm" = "wipe" ] || { echo "aborted."; exit 1; }
	$(MAKE) clean-runtime
	$(MAKE) clean-coverage
	$(MAKE) clean-mock
	rm -rf data/autocrud .cognee_data .cognee_system transcripts reports active_sessions
	@echo "everything wiped."
