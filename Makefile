.PHONY: install test simulation data audit real all

install:
	pip install -r requirements.txt
test:
	pytest
simulation:
	python scripts/run_simulation.py
data:
	python scripts/download_data.py
audit:
	python scripts/run_audit.py
real:
	python scripts/run_real.py
all: test simulation data audit real
