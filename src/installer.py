# Installer.py -> The Modular Core Installer.
# Fyntora Linux

import yaml
import os
import sys
from typing import Dict, Any, List, Optional

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from lib.runcmd import CommandUseHelper
from modules import ModuleRegistry


class ModularInstaller:
    """
    Main installer class that orchestrates module-based installation.
    """

    def __init__(self):
        self.helper = CommandUseHelper()
        self.registry = ModuleRegistry()
        self.profile_loader = ProfileLoader()

    def install_from_profile(
        self, profile_name: str, config_override: Optional[Dict[str, Any]] = None
    ):
        """
        Install system using a profile configuration.
        """
        print(f"Loading profile: {profile_name}")
        profile_data = self.profile_loader.load(profile_name)

        # Convert profile to module configuration
        module_config = self._profile_to_modules(profile_data)

        # Apply config overrides
        if config_override:
            module_config.update(config_override)

        # Install using modules
        return self.install_with_modules(module_config)

    def install_with_modules(self, config: Dict[str, Any]) -> bool:
        """
        Install system using specified module configuration.
        """
        try:
            # Configure modules
            self.registry.configure_modules(config)

            # Get list of modules to install
            modules_to_install = config.get("modules", [])
            if not modules_to_install:
                print("No modules specified for installation")
                return False

            print(f"Installing modules: {', '.join(modules_to_install)}")

            # Resolve dependencies and get execution order
            execution_order = self.registry.resolve_dependencies(modules_to_install)
            print(f"Execution order: {', '.join(execution_order)}")

            # Validate all modules
            if not self.registry.validate_modules(execution_order):
                print("Module validation failed")
                return False

            # Install modules
            for module_name in execution_order:
                module = self.registry.get_module(module_name)
                if not module:
                    print(f"Module not found: {module_name}")
                    return False

                print(f"Installing module: {module_name} - {module.description}")

                if not module.install():
                    print(f"Failed to install module: {module_name}")
                    return False

                print(f"✓ Module {module_name} installed successfully")

            # Configure modules (services, etc.)
            for module_name in execution_order:
                module = self.registry.get_module(module_name)
                if not module:
                    print(f"Module not found: {module_name}")
                    return False

                print(f"Configuring module: {module_name}")

                if not module.configure():
                    print(f"Failed to configure module: {module_name}")
                    return False

                print(f"✓ Module {module_name} configured successfully")

            print("Installation completed successfully!")
            return True

        except Exception as e:
            print(f"Installation failed: {str(e)}")
            return False

    def _profile_to_modules(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert profile format to module configuration.
        Supports both new modular format and legacy format.
        """
        # Check if it's already a modular profile
        if "modules" in profile_data:
            return profile_data

        # Convert legacy profile format to module configuration
        config = {
            "global": {
                "mount_point": "/mnt",
                "hostname": profile_data.get("profile", {})
                .get("name", "archlinux")
                .lower(),
                "locale": "en_US.UTF-8",
                "timezone": "UTC",
            },
            "modules": [
                "base",
                "bootloader",
                "network",
                "packages",
                "services",
                "config",
            ],
            "base": {
                "device": "/dev/sda",  # This should be configurable
                "base_packages": ["base", "base-devel", "linux", "linux-firmware"],
            },
            "network": {
                "hostname": profile_data.get("profile", {})
                .get("name", "archlinux")
                .lower(),
                "network_manager": "NetworkManager",
            },
            "packages": {"packages": profile_data.get("packages", [])},
            "services": {"services": profile_data.get("services", [])},
        }

        # Add post-install commands as a custom module config
        post_commands = profile_data.get("post_install_commands", [])
        if post_commands:
            config["post_install"] = {"commands": post_commands}

        return config

    def list_available_modules(self):
        """
        List all available modules.
        """
        modules = self.registry.get_available_modules()
        print("Available modules:")
        for module_name in modules:
            module = self.registry.get_module(module_name)
            if module:
                print(f"  {module_name}: {module.description}")
                if module.dependencies:
                    print(f"    Dependencies: {', '.join(module.dependencies)}")
            else:
                print(f"  {module_name}: Module not found")


class ProfileLoader:
    """
    Legacy profile loader for backward compatibility.
    """

    def __init__(self, profiles_dir="src/profiles"):
        self.profiles_dir = profiles_dir

    def load(self, profile_name):
        """
        Load a YAML profile by name (without .yaml)
        """
        profile_path = os.path.join(self.profiles_dir, f"{profile_name}.yaml")

        if not os.path.exists(profile_path):
            raise FileNotFoundError(f"Profile '{profile_name}' not found")

        with open(profile_path, "r") as f:
            data = yaml.safe_load(f)

        self._validate(data)
        return data

    def _validate(self, data):
        required_keys = ["profile", "packages"]
        for key in required_keys:
            if key not in data:
                raise ValueError(f"Profile missing required key: {key}")


def main():
    """
    Main entry point for the installer.
    """
    if len(sys.argv) < 2 or sys.argv[1] in ["--help", "-h"]:
        print("Fyntora Linux Installer")
        print("Usage:")
        print(
            "  python install.py --interactive              # Interactive installation"
        )
        print("  python install.py <profile_name> [options]   # Install from profile")
        print()
        print("Options:")
        print("  --device /dev/sdX    Override installation device")
        print("  --mount /mnt         Override mount point")
        print()
        print("Examples:")
        print("  python install.py --interactive")
        print("  python install.py desktop")
        print("  python install.py desktop_modular --device /dev/nvme0n1")
        return 0

    if sys.argv[1] == "--interactive":
        # Import here to avoid circular imports
        from .interactive_installer import InteractiveInstaller

        installer = InteractiveInstaller()
        success = installer.run()
        return 0 if success else 1

    # Parse arguments
    profile_name = None
    config_override = {"global": {"mount_point": "/mnt"}}

    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg.startswith("--"):
            if arg == "--device" and i + 1 < len(sys.argv):
                config_override["global"]["device"] = sys.argv[i + 1]
                i += 2
            elif arg == "--mount" and i + 1 < len(sys.argv):
                config_override["global"]["mount_point"] = sys.argv[i + 1]
                i += 2
            else:
                print(f"Unknown option: {arg}")
                return 1
        else:
            if profile_name is None:
                profile_name = arg
            else:
                print(f"Unexpected argument: {arg}")
                return 1
            i += 1

    if not profile_name:
        print("Error: No profile specified")
        return 1

    installer = ModularInstaller()

    success = installer.install_from_profile(profile_name, config_override)
    return 0 if success else 1

    # Profile-based installation
    profile_name = sys.argv[1]

    installer = ModularInstaller()

    # For now, use default configuration
    # In a full implementation, this would load from config files
    config_override = {
        "global": {
            "device": "/dev/sda",  # Should be detected or specified
            "mount_point": "/mnt",
        }
    }

    success = installer.install_from_profile(profile_name, config_override)
    return 0 if success else 1

    # Profile-based installation
    profile_name = sys.argv[1]

    installer = ModularInstaller()

    # For now, use default configuration
    # In a full implementation, this would load from config files
    config_override = {
        "global": {
            "device": "/dev/sda",  # Should be detected or specified
            "mount_point": "/mnt",
        }
    }

    success = installer.install_from_profile(profile_name, config_override)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
