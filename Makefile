.PHONY: install test figures diagrams all clean

install:
	pip install -r requirements.txt

test:
	pytest -q

figures:
	python figures/make_plots.py

diagrams:
	bash figures/diagrams/make_diagrams.sh

all: test figures diagrams

clean:
	rm -rf figures/out .pytest_cache **/__pycache__
