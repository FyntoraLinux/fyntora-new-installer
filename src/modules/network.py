"""
Network configuration module.
Handles hostname, hosts file, and network services setup.
"""

import os
from typing import Dict, Any
from lib.module_base import ModuleBase


class NetworkModule(ModuleBase):
    """
    Module for network configuration.
    """

    def __init__(self):
        super().__init__(
            name="network",
            description="Network configuration and services",
            dependencies=["base"],
        )

    def validate(self) -> bool:
        """
        Validate network configuration requirements.
        """
        hostname = self.get_config("hostname")
        if not hostname:
            self.log("No hostname specified")
            return False

        mount_point = self.get_config("mount_point", "/mnt")
        if not os.path.exists(mount_point):
            self.log(f"Mount point {mount_point} does not exist")
            return False

        return True

    def install(self) -> bool:
        """
        Install and configure network components.
        """
        try:
            mount_point = self.get_config("mount_point", "/mnt")
            hostname = self.get_config("hostname")
            network_manager = self.get_config("network_manager", "NetworkManager")

            # Install network packages
            network_packages = [network_manager]
            for pkg in network_packages:
                if not self.helper.InstallPackage(pkg):
                    self.log(f"Failed to install {pkg}")
                    return False

            # Configure hostname
            if not self._set_hostname(mount_point, hostname):
                return False

            # Configure hosts file
            if not self._configure_hosts(mount_point, hostname):
                return False

            self._installed = True
            self.log("Network configuration completed successfully")
            return True

        except Exception as e:
            self.log(f"Network configuration failed: {str(e)}")
            return False

    def configure(self) -> bool:
        """
        Enable network services.
        """
        try:
            network_manager = self.get_config("network_manager", "NetworkManager")

            # Enable network manager service
            stdout, stderr, code = self.helper.SysRunCommand(
                ["systemctl", "enable", network_manager], as_root=True
            )
            if code != 0:
                self.log(f"Failed to enable {network_manager}: {stderr}")
                return False

            self.log(f"Enabled {network_manager} service")
            return True

        except Exception as e:
            self.log(f"Network service configuration failed: {str(e)}")
            return False

    def _set_hostname(self, mount_point: str, hostname: str) -> bool:
        """
        Set the system hostname.
        """
        hostname_path = os.path.join(mount_point, "etc", "hostname")
        os.makedirs(os.path.dirname(hostname_path), exist_ok=True)

        with open(hostname_path, "w") as f:
            f.write(hostname + "\n")

        self.log(f"Set hostname to {hostname}")
        return True

    def _configure_hosts(self, mount_point: str, hostname: str) -> bool:
        """
        Configure /etc/hosts file.
        """
        hosts_path = os.path.join(mount_point, "etc", "hosts")
        os.makedirs(os.path.dirname(hosts_path), exist_ok=True)

        hosts_content = f"""127.0.0.1\tlocalhost
::1\t\tlocalhost
127.0.1.1\t{hostname}.localdomain\t{hostname}
"""

        with open(hosts_path, "w") as f:
            f.write(hosts_content)

        self.log("Configured hosts file")
        return True
