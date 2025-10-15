# ==========================================================
# Makefile for the command_describer project
# ==========================================================

# Main module name
PACKAGE = command_describer
ENV = myenv
BIN_NAME = cmddesc

# ----------------------------------------------------------
# Main commands
# ----------------------------------------------------------

# Install the package in editable (development) mode
install:
	pip install -e .

# Run the CLI program (Python)
run:
	$(ENV)/bin/cmddesc

# Clean up compiled files and build artifacts
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf build/ dist/ *.spec

# Uninstall the package
uninstall:
	pip uninstall -y $(PACKAGE)

# Run unit tests (if you have a tests/ directory)
test:
	pytest -v

# Full rebuild: clean + uninstall + install
rebuild: clean uninstall install

# Run code linting (check code quality)
lint:
	flake8 $(PACKAGE)

# ----------------------------------------------------------
# Build Linux standalone binary via PyInstaller
# ----------------------------------------------------------
# Includes dict_json folder and config.json
build-binary:
	pyinstaller --onefile \
		--add-data "command_describer/data/dict_json:dict_json" \
		--add-data "command_describer/data/config.json:." \
		-n $(BIN_NAME) \
		command_describer/main.py

# Run the compiled binary
run-binary:
	./dist/$(BIN_NAME)

# ----------------------------------------------------------
# Help
# ----------------------------------------------------------
help:
	@echo "Available commands:"
	@echo "  make install        -> Install the package in editable mode"
	@echo "  make run            -> Run the CLI (Python)"
	@echo "  make clean          -> Remove temporary/compiled files and build artifacts"
	@echo "  make uninstall      -> Uninstall the package"
	@echo "  make test           -> Run unit tests"
	@echo "  make rebuild        -> Clean + reinstall everything"
	@echo "  make lint           -> Run code style checks"
	@echo "  make build-binary   -> Build a standalone Linux binary with PyInstaller"
	@echo "  make run-binary     -> Run the compiled standalone binary"
