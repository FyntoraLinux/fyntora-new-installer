"""
Interactive installer with text-based user interface.
Provides guided installation experience for users.
"""

import os
import sys
import time
from typing import Dict, Any, List, Optional
from .installer import ModularInstaller
from lib.runcmd import CommandUseHelper


class InteractiveInstaller:
    """
    Interactive installer with guided prompts and menus.
    """

    def __init__(self):
        self.installer = ModularInstaller()
        self.helper = CommandUseHelper()
        self.config: Dict[str, Any] = {}

    def run(self) -> bool:
        """
        Main interactive installation flow.
        """
        try:
            self._show_welcome()
            self._check_requirements()

            if not self._select_installation_type():
                return False

            if not self._configure_installation():
                return False

            if not self._confirm_installation():
                return False

            return self._perform_installation()

        except KeyboardInterrupt:
            print("\n\nInstallation cancelled by user.")
            return False
        except Exception as e:
            print(f"\n\nInstallation failed: {str(e)}")
            return False

    def _show_welcome(self):
        """
        Display welcome screen and system information.
        """
        print("=" * 60)
        print("           Welcome to Fyntora Linux Installer")
        print("=" * 60)
        print()
        print("This installer will guide you through installing")
        print("Fyntora Linux on your system.")
        print()
        print("Please ensure you have:")
        print("• A backup of important data")
        print("• Sufficient disk space")
        print("• Internet connection for package downloads")
        print()
        print("Press Enter to continue or Ctrl+C to cancel...")
        input()

    def _check_requirements(self):
        """
        Check system requirements for installation.
        """
        print("Checking system requirements...")
        print()

        # Check if running as root
        if os.geteuid() != 0:
            print("❌ ERROR: This installer must be run as root!")
            print("   Please run: sudo python install.py --interactive")
            sys.exit(1)

        # Check for required tools
        required_tools = ["pacstrap", "genfstab", "arch-chroot"]
        missing_tools = []

        for tool in required_tools:
            if not self._check_command_exists(tool):
                missing_tools.append(tool)

        if missing_tools:
            print(f"❌ ERROR: Missing required tools: {', '.join(missing_tools)}")
            print("   Please install arch-install-scripts package")
            sys.exit(1)

        print("✅ System requirements met")
        print()

    def _check_command_exists(self, command: str) -> bool:
        """
        Check if a command exists in PATH.
        """
        stdout, stderr, code = self.helper.SysRunCommand(["which", command])
        return code == 0

    def _select_installation_type(self) -> bool:
        """
        Let user choose between profile-based or custom installation.
        """
        while True:
            print("Installation Type")
            print("-" * 20)
            print("1. Install from profile (recommended)")
            print("2. Custom installation (advanced)")
            print("3. Exit")
            print()

            choice = input("Select installation type (1-3): ").strip()

            if choice == "1":
                return self._select_profile()
            elif choice == "2":
                return self._custom_installation()
            elif choice == "3":
                print("Installation cancelled.")
                return False
            else:
                print("Invalid choice. Please try again.")
                print()

    def _select_profile(self) -> bool:
        """
        Let user select from available profiles.
        """
        print("Available Profiles")
        print("-" * 20)

        profiles_dir = "src/profiles"
        if not os.path.exists(profiles_dir):
            print("❌ No profiles directory found!")
            return False

        profiles = [f for f in os.listdir(profiles_dir) if f.endswith(".yaml")]
        if not profiles:
            print("❌ No profiles found!")
            return False

        for i, profile in enumerate(profiles, 1):
            profile_name = profile.replace(".yaml", "").replace("_", " ").title()
            print(f"{i}. {profile_name}")

        print(f"{len(profiles) + 1}. Back to main menu")
        print()

        while True:
            try:
                choice = int(input(f"Select profile (1-{len(profiles) + 1}): ").strip())

                if 1 <= choice <= len(profiles):
                    selected_profile = profiles[choice - 1].replace(".yaml", "")
                    print(f"Selected profile: {selected_profile}")
                    print()

                    # Load and display profile info
                    try:
                        profile_data = self.installer.profile_loader.load(
                            selected_profile
                        )
                        self._show_profile_info(profile_data)
                        self.config["profile"] = selected_profile
                        # Remove profile key from config to avoid overwriting profile data
                        config_override = {
                            k: v for k, v in self.config.items() if k != "profile"
                        }
                        return True
                    except Exception as e:
                        print(f"❌ Error loading profile: {str(e)}")
                        return False

                elif choice == len(profiles) + 1:
                    return False
                else:
                    print("Invalid choice. Please try again.")

            except ValueError:
                print("Please enter a number.")

    def _show_profile_info(self, profile_data: Dict[str, Any]):
        """
        Display information about the selected profile.
        """
        profile_info = profile_data.get("profile", {})
        name = profile_info.get("name", "Unknown")
        description = profile_info.get("description", "")

        print(f"Profile: {name}")
        if description:
            print(f"Description: {description}")

        packages = profile_data.get("packages", [])
        services = profile_data.get("services", [])

        print(f"Packages: {len(packages)}")
        print(f"Services: {len(services)}")
        print()

    def _custom_installation(self) -> bool:
        """
        Guide user through custom installation setup.
        """
        print("Custom Installation")
        print("-" * 20)
        print(
            "This will guide you through configuring each aspect of the installation."
        )
        print()

        # Select modules
        if not self._select_modules():
            return False

        # Configure each selected module
        for module_name in self.config.get("modules", []):
            if not self._configure_module(module_name):
                return False

        return True

    def _select_modules(self) -> bool:
        """
        Let user select which modules to install.
        """
        print("Module Selection")
        print("-" * 15)
        print("Select which components to install:")
        print()

        available_modules = self.installer.registry.get_available_modules()
        selected_modules = []

        for module_name in available_modules:
            module = self.installer.registry.get_module(module_name)
            if module:
                description = module.description

                while True:
                    choice = (
                        input(f"Install {module_name} ({description})? [Y/n]: ")
                        .strip()
                        .lower()
                    )
                    if choice in ["", "y", "yes"]:
                        selected_modules.append(module_name)
                        print(f"✓ Selected: {module_name}")
                        break
                    elif choice in ["n", "no"]:
                        print(f"✗ Skipped: {module_name}")
                        break
                    else:
                        print("Please enter 'y' or 'n'")

        if not selected_modules:
            print("❌ No modules selected!")
            return False

        self.config["modules"] = selected_modules
        print()
        return True

    def _configure_module(self, module_name: str) -> bool:
        """
        Configure a specific module.
        """
        print(f"Configuring {module_name}")
        print("-" * (13 + len(module_name)))

        # Basic configurations for common modules
        if module_name == "base":
            return self._configure_base()
        elif module_name == "network":
            return self._configure_network()
        elif module_name == "user":
            return self._configure_user()
        elif module_name == "packages":
            return self._configure_packages()

        # For other modules, use defaults
        print(f"Using default configuration for {module_name}")
        return True

    def _configure_base(self) -> bool:
        """
        Configure base system installation.
        """
        print("Base System Configuration")
        print("-" * 25)

        # Get installation device
        print("Available disk devices:")
        try:
            stdout, stderr, code = self.helper.SysRunCommand(
                ["lsblk", "-d", "-n", "-o", "NAME,SIZE"]
            )
            if code == 0:
                print(stdout)
            else:
                print("Could not list devices")
        except:
            print("Could not list devices")

        while True:
            device = input(
                "Installation device (e.g., /dev/sda, /dev/nvme0n1): "
            ).strip()
            if device:
                # Check if it's a valid block device
                if os.path.exists(device) and os.path.exists(
                    f"/sys/block/{os.path.basename(device)}"
                ):
                    self.config["device"] = device
                    print(f"✓ Selected device: {device}")
                    break
                else:
                    print(
                        "❌ Device not found or not a valid block device. Please check the path."
                    )
            else:
                print("Device cannot be empty.")

        # Base packages
        packages_input = input(
            "Additional base packages (comma-separated, or empty for defaults): "
        ).strip()
        if packages_input:
            packages = [pkg.strip() for pkg in packages_input.split(",")]
            self.config.setdefault("base", {}).setdefault("base_packages", []).extend(
                packages
            )

        return True

    def _configure_network(self) -> bool:
        """
        Configure network settings.
        """
        print("Network Configuration")
        print("-" * 20)

        hostname = input("System hostname: ").strip()
        if hostname:
            self.config.setdefault("network", {})["hostname"] = hostname

        return True

    def _configure_user(self) -> bool:
        """
        Configure user accounts.
        """
        print("User Configuration")
        print("-" * 18)

        users = []
        while True:
            username = input("Username (or empty to finish): ").strip()
            if not username:
                break

            password = input(f"Password for {username}: ").strip()
            if not password:
                print("Password cannot be empty")
                continue

            confirm_password = input("Confirm password: ").strip()
            if password != confirm_password:
                print("Passwords do not match")
                continue

            groups_input = input(
                "Additional groups (comma-separated, or empty for defaults): "
            ).strip()
            groups = ["wheel"]
            if groups_input:
                groups.extend([g.strip() for g in groups_input.split(",")])

            users.append({"username": username, "password": password, "groups": groups})

            print(f"✓ Added user: {username}")
            print()

        if users:
            self.config.setdefault("user", {})["users"] = users

        return True

    def _configure_packages(self) -> bool:
        """
        Configure package installation.
        """
        print("Package Configuration")
        print("-" * 20)

        packages_input = input(
            "Additional packages to install (comma-separated, or empty): "
        ).strip()
        if packages_input:
            packages = [pkg.strip() for pkg in packages_input.split(",")]
            # Get existing packages from config or empty list
            existing_packages = self.config.get("packages", [])
            if isinstance(existing_packages, list):
                existing_packages.extend(packages)
            else:
                existing_packages = packages
            self.config["packages"] = existing_packages

        return True

    def _configure_installation(self) -> bool:
        """
        Configure global installation settings.
        """
        print("Installation Configuration")
        print("-" * 25)

        # Mount point
        mount_point = input("Installation mount point [/mnt]: ").strip()
        if not mount_point:
            mount_point = "/mnt"
        self.config.setdefault("global", {})["mount_point"] = mount_point

        # Device override (for profile-based installations)
        current_device = self.config.get("global", {}).get("device", "")
        if current_device:
            print(f"Current device from profile: {current_device}")
            device_override = input(f"Override device [{current_device}]: ").strip()
            if device_override:
                if os.path.exists(device_override) and os.path.exists(
                    f"/sys/block/{os.path.basename(device_override)}"
                ):
                    self.config["global"]["device"] = device_override
                    print(f"✓ Device overridden to: {device_override}")
                else:
                    print("❌ Invalid device, keeping original.")
        else:
            # No device set, prompt for it
            print("Available disk devices:")
            try:
                stdout, stderr, code = self.helper.SysRunCommand(
                    ["lsblk", "-d", "-n", "-o", "NAME,SIZE"]
                )
                if code == 0:
                    print(stdout)
                else:
                    print("Could not list devices")
            except:
                print("Could not list devices")

            while True:
                device = input("Installation device (e.g., /dev/sda): ").strip()
                if (
                    device
                    and os.path.exists(device)
                    and os.path.exists(f"/sys/block/{os.path.basename(device)}")
                ):
                    self.config["global"]["device"] = device
                    print(f"✓ Selected device: {device}")
                    break
                else:
                    print("❌ Invalid device. Please check the path.")

        # Locale
        locale = input("System locale [en_US.UTF-8]: ").strip()
        if not locale:
            locale = "en_US.UTF-8"
        self.config.setdefault("global", {})["locale"] = locale

        # Timezone
        timezone = input("System timezone [UTC]: ").strip()
        if not timezone:
            timezone = "UTC"
        self.config.setdefault("global", {})["timezone"] = timezone

        # Confirm configuration
        print()
        print("Configuration Summary:")
        print("-" * 20)
        for key, value in self.config.items():
            if isinstance(value, dict):
                print(f"{key}:")
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, list):
                        print(
                            f"  {sub_key}: {', '.join(sub_value) if sub_value else 'none'}"
                        )
                    else:
                        print(f"  {sub_key}: {sub_value}")
            else:
                print(f"{key}: {value}")
        print()

        return True

    def _confirm_installation(self) -> bool:
        """
        Get final confirmation from user.
        """
        print("⚠️  WARNING: This will DESTROY all data on the selected device!")
        print("   Make sure you have backups of important data.")
        print()

        while True:
            confirm = input(
                "Are you sure you want to proceed? Type 'YES' to continue: "
            ).strip()
            if confirm == "YES":
                return True
            elif confirm.lower() in ["no", "cancel", "quit"]:
                print("Installation cancelled.")
                return False
            else:
                print("Please type 'YES' to proceed or 'no' to cancel.")

    def _perform_installation(self) -> bool:
        """
        Execute the actual installation.
        """
        print()
        print("Starting installation...")
        print("=" * 40)

        # Use the modular installer
        if "profile" in self.config:
            # Remove profile key from config to avoid overwriting profile data
            config_override = {k: v for k, v in self.config.items() if k != "profile"}
            success = self.installer.install_from_profile(
                self.config["profile"], config_override
            )
        else:
            success = self.installer.install_with_modules(self.config)

        if success:
            print()
            print("🎉 Installation completed successfully!")
            print()
            print("Next steps:")
            print("1. Reboot your system")
            print("2. Remove installation media")
            print("3. Login with your configured user account")
            print()
            print("Thank you for choosing Fyntora Linux!")
        else:
            print()
            print("❌ Installation failed!")
            print("Check the installer.log file for details.")

        return success
