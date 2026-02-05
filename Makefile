PYTHON = python3
PIP = pip
VENV = venv
BIN = $(VENV)/bin

all: setup lint unittest fosstest

setup:
	@echo "Setting up the environment..."
	$(PYTHON) -m venv $(VENV)
	$(BIN)/$(PIP) install --upgrade pip
	$(BIN)/$(PIP) install -r requirements.txt

lint:
	@echo "Running linters..."
	$(BIN)/pylint .

unittest:
	@echo "Running unit tests..."
	$(BIN)/pytest test/unit

fosstest:
	@echo "Running FOSS tests..."
	$(BIN)/pytest test/foss

clean:
	@echo "Cleaning up..."
	rm -rf $(VENV)
	find . -type d -name "__pycache__" -exec rm -rf {} +

.PHONY: all setup lint test clean
