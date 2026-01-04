# Makefile for the Fyntora Linux Installer

.PHONY: install install-desktop install-server install-interactive list-modules test clean

# Default target
install: install-interactive

# Interactive installation (recommended)
install-interactive:
	@echo "Starting Fyntora Linux Interactive Installer..."
	python install.py --interactive

# Install desktop profile (non-interactive)
install-desktop:
	@echo "Installing Fyntora Linux Desktop..."
	python install.py desktop

# Install server profile (non-interactive)
install-server:
	@echo "Installing Fyntora Linux Server..."
	python install.py server

# Install modular desktop profile (non-interactive)
install-modular:
	@echo "Installing Fyntora Linux Desktop (Modular)..."
	python install.py desktop_modular

# List available modules
list-modules:
	@echo "Available modules:"
	python -c "import sys, os; sys.path.insert(0, 'src'); from installer import ModularInstaller; installer = ModularInstaller(); installer.list_available_modules()"

# Run basic tests
test:
	@echo "Running basic validation tests..."
	python -c "import sys, os; sys.path.insert(0, 'src'); from modules import ModuleRegistry; registry = ModuleRegistry(); print('Modules loaded successfully:', len(registry.get_available_modules()))"

# Clean up generated files
clean:
	@echo "Cleaning up..."
	rm -f installer.log
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Help target
help:
	@echo "Available targets:"
	@echo "  install             - Interactive installation (recommended)"
	@echo "  install-interactive - Interactive installation (recommended)"
	@echo "  install-desktop     - Install desktop profile (non-interactive)"
	@echo "  install-server      - Install server profile (non-interactive)"
	@echo "  install-modular     - Install modular desktop profile (non-interactive)"
	@echo "  list-modules        - List all available modules"
	@echo "  test                - Run basic validation tests"
	@echo "  clean               - Clean up generated files"
	@echo "  help                - Show this help message"