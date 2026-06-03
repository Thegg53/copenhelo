.PHONY: help install sync run-elo run-leaderboard clean

VENV_DIR := .venv
PYTHON := $(VENV_DIR)/bin/python
UV := $(shell which uv)

help:
	@echo "Available commands:"
	@echo "  make install       - Create and setup virtual environment with dependencies"
	@echo "  make sync          - Sync dependencies from lock file"
	@echo "  make run-elo       - Run ELO calculator"
	@echo "  make run-leaderboard - Generate leaderboard"
	@echo "  make run           - Run both calculator and leaderboard"
	@echo "  make clean         - Remove virtual environment and cache"
	@echo "  make shell         - Activate virtual environment shell"

install: $(VENV_DIR)
	@echo "✓ Virtual environment ready"

$(VENV_DIR):
	@echo "Creating virtual environment..."
	python3 -m venv $(VENV_DIR)
	@echo "Installing dependencies with uv..."
ifdef UV
	$(UV) pip install -e .
else
	$(PYTHON) -m pip install --upgrade pip setuptools wheel
	$(PYTHON) -m pip install -e .
endif
	@echo "✓ Installation complete"

sync: $(VENV_DIR)
	@echo "Syncing dependencies..."
ifdef UV
	$(UV) pip sync
else
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e .
endif
	@echo "✓ Sync complete"

run-elo: $(VENV_DIR)
	@echo "Running ELO calculator..."
	$(PYTHON) scripts/elo_calculator.py

run-leaderboard: $(VENV_DIR)
	@echo "Generating leaderboard..."
	$(PYTHON) scripts/leaderboard_generator.py

run: run-elo run-leaderboard
	@echo "✓ All tasks complete"

shell: $(VENV_DIR)
	@echo "Activating virtual environment..."
	@echo "Run: source $(VENV_DIR)/bin/activate"

clean:
	@echo "Cleaning up..."
	rm -rf $(VENV_DIR)
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✓ Cleanup complete"
