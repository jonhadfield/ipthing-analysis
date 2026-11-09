.PHONY: sync test report open

sync:
	uv sync

test:
	uv sync --group dev
	uv run pytest

report:
	uv run ipthing-report

open: report
	open docs/index.html
