# Installer.py -> The Core Installer.
# Fyntora Linux

import yaml
import os
from lib.runcmd import CommandUseHelper

class ProfileLoader:
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

if __name__ == "__main__":
    helper = CommandUseHelper()
    loader = ProfileLoader()

    profile = loader.load("desktop")

    print(f"Installing profile: {profile['profile']['name']}")
    print(profile['profile'].get("description", ""))

    # Install packages
    for pkg in profile.get("packages", []):
        helper.InstallPackage(pkg)

    # Enable services
    for service in profile.get("services", []):
        helper.SysRunCommand(
            ["systemctl", "enable", service],
            as_root=True
        )

    # Run post-install commands
    for cmd in profile.get("post_install_commands", []):
        helper.SysRunCommand(cmd, as_root=True)
