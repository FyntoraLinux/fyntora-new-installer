"""
Services management module.
Handles systemd service enablement and configuration.
"""

import os
from typing import Dict, Any, List
from lib.module_base import ModuleBase


class ServicesModule(ModuleBase):
    """
    Module for systemd services management.
    """

    def __init__(self):
        super().__init__(
            name="services",
            description="Systemd services management",
            dependencies=["base"],
        )

    def validate(self) -> bool:
        """
        Validate services configuration.
        """
        mount_point = self.get_config("mount_point", "/mnt")
        if not os.path.exists(mount_point):
            self.log(f"Mount point {mount_point} does not exist")
            return False

        return True

    def install(self) -> bool:
        """
        Services are typically enabled during configuration phase.
        This module mainly validates the service list.
        """
        services = self.get_config("services", [])
        if not services:
            self.log("No services specified for management")
            self._installed = True
            return True

        self._installed = True
        self.log(f"Validated {len(services)} services for management")
        return True

    def configure(self) -> bool:
        """
        Enable specified services.
        """
        try:
            mount_point = self.get_config("mount_point", "/mnt")
            services = self.get_config("services", [])

            for service in services:
                if not self._enable_service_chroot(mount_point, service):
                    self.log(f"Failed to enable service: {service}")
                    return False

            self.log(f"Successfully enabled {len(services)} services")
            return True

        except Exception as e:
            self.log(f"Services configuration failed: {str(e)}")
            return False

    def _enable_service_chroot(self, mount_point: str, service: str) -> bool:
        """
        Enable a systemd service in the chroot environment.
        """
        cmd = ["arch-chroot", mount_point, "systemctl", "enable", service]
        stdout, stderr, code = self.helper.SysRunCommand(cmd, as_root=True)

        if code != 0:
            self.log(f"Failed to enable {service}: {stderr}")
            return False

        self.log(f"Enabled service: {service}")
        return True
