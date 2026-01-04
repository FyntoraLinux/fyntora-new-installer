"""
Package management module.
Handles installation of packages based on profiles and custom package lists.
"""

import os
from typing import Dict, Any, List
from lib.module_base import ModuleBase


class PackageModule(ModuleBase):
    """
    Module for package management.
    """

    def __init__(self):
        super().__init__(
            name="packages",
            description="Package installation and management",
            dependencies=["base"],
        )

    def validate(self) -> bool:
        """
        Validate package installation requirements.
        """
        mount_point = self.get_config("mount_point", "/mnt")
        if not os.path.exists(mount_point):
            self.log(f"Mount point {mount_point} does not exist")
            return False

        return True

    def install(self) -> bool:
        """
        Install packages based on configuration.
        """
        try:
            mount_point = self.get_config("mount_point", "/mnt")
            packages = self.get_config("packages", [])

            if not packages:
                self.log("No packages specified for installation")
                # This is not necessarily an error - some profiles might not need extra packages
                self._installed = True
                return True

            # Install packages using pacman in chroot
            for package in packages:
                if not self._install_package_chroot(mount_point, package):
                    self.log(f"Failed to install package: {package}")
                    return False

            self._installed = True
            self.log(f"Successfully installed {len(packages)} packages")
            return True

        except Exception as e:
            self.log(f"Package installation failed: {str(e)}")
            return False

    def _install_package_chroot(self, mount_point: str, package: str) -> bool:
        """
        Install a package using pacman in chroot environment.
        """
        cmd = [
            "arch-chroot",
            mount_point,
            "pacman",
            "-S",
            "--noconfirm",
            "--needed",
            package,
        ]
        stdout, stderr, code = self.helper.SysRunCommand(cmd, as_root=True)

        if code != 0:
            self.log(f"Failed to install {package}: {stderr}")
            return False

        self.log(f"Installed package: {package}")
        return True
