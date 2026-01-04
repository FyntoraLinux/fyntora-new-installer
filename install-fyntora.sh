#!/bin/bash
# Fyntora Linux Auto-Installer Script
# This script is meant to be run from the live environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    print_error "This script must be run as root!"
    echo "Please run: sudo $0"
    exit 1
fi

# Check if we're in a live environment
if [[ ! -d "/run/archiso" ]]; then
    print_warning "This doesn't appear to be a live environment."
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check internet connection
print_status "Checking internet connection..."
if ! ping -c 1 -q google.com >/dev/null 2>&1; then
    print_error "No internet connection detected!"
    print_error "Please connect to the internet and try again."
    exit 1
fi
print_status "Internet connection OK"

# Update package databases
print_status "Updating package databases..."
pacman -Sy --noconfirm

# Install dependencies if needed
if ! command -v python3 &> /dev/null; then
    print_status "Installing Python..."
    pacman -S --noconfirm python
fi

# Check for installer files
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALLER_DIR="$SCRIPT_DIR"

# Verify this is the installer directory
if [[ ! -f "$INSTALLER_DIR/install.py" ]] || [[ ! -d "$INSTALLER_DIR/src" ]]; then
    print_error "This doesn't appear to be the Fyntora installer directory."
    print_error "Please run this script from the installer root directory."
    print_error "Expected files: install.py, src/"
    exit 1
fi

print_status "Found Fyntora installer at: $INSTALLER_DIR"

# Run the interactive installer
print_status "Starting Fyntora Linux Installer..."
python3 install.py --interactive

# Check if installation was successful
if [[ $? -eq 0 ]]; then
    print_status "Installation completed successfully!"
    print_status "You can now reboot into your new Fyntora Linux system."
    print_warning "Don't forget to remove the installation media before rebooting."
    read -p "Reboot now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        reboot
    fi
else
    print_error "Installation failed!"
    print_error "Check the installer.log file for details."
    exit 1
fi