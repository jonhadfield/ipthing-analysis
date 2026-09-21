.PHONY: sync report open

sync:
	uv sync

report:
	uv run ipthing-report

open: report
	open docs/index.html
