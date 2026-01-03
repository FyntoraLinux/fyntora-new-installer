# Installer.py -> The Core Installer.
# Fyntora Linux

import importlib.util
import os
from lib.runcmd import ArchInstallerHelper

def load_profile(profile_path):
    """Load a profile module from a file path."""
    spec = importlib.util.spec_from_file_location("profile", profile_path)
    profile = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(profile)
    return profile


if __name__ == "__main__":
    helper = ArchInstallerHelper()

    # Load the 'desktop' profile
    profile_path = os.path.join("src", "profiles", "desktop.py")
    profile = load_profile(profile_path)

    print(f"Running profile: {profile.profile_name}")

    # Install packages
    for pkg in profile.packages:
        helper.InstallPackage(pkg)

    # Run post-install commands
    for cmd in profile.post_install_commands:
        helper.SysRunCommand(cmd, as_root=True)