"""
System configuration module.
Handles locale, timezone, and other system settings.
"""

import os
from typing import Dict, Any
from lib.module_base import ModuleBase


class ConfigModule(ModuleBase):
    """
    Module for system configuration.
    """

    def __init__(self):
        super().__init__(
            name="config",
            description="System configuration (locale, timezone, etc.)",
            dependencies=["base"],
        )

    def validate(self) -> bool:
        """
        Validate configuration requirements.
        """
        mount_point = self.get_config("mount_point", "/mnt")
        if not os.path.exists(mount_point):
            self.log(f"Mount point {mount_point} does not exist")
            return False

        return True

    def install(self) -> bool:
        """
        System configuration is handled during configuration phase.
        """
        self._installed = True
        return True

    def configure(self) -> bool:
        """
        Configure system settings.
        """
        try:
            mount_point = self.get_config("mount_point", "/mnt")

            # Configure locale
            if not self._configure_locale(mount_point):
                return False

            # Configure timezone
            if not self._configure_timezone(mount_point):
                return False

            # Configure hostname (already done in network module, but ensure it's set)
            if not self._configure_hostname(mount_point):
                return False

            # Configure locale settings
            if not self._configure_locale_settings(mount_point):
                return False

            self.log("System configuration completed successfully")
            return True

        except Exception as e:
            self.log(f"System configuration failed: {str(e)}")
            return False

    def _configure_locale(self, mount_point: str) -> bool:
        """
        Configure system locale.
        """
        locale = self.get_config("locale", "en_US.UTF-8")

        # Uncomment the locale in /etc/locale.gen
        locale_gen_path = os.path.join(mount_point, "etc", "locale.gen")
        if os.path.exists(locale_gen_path):
            try:
                with open(locale_gen_path, "r") as f:
                    content = f.read()

                # Uncomment the desired locale
                locale_line = f"{locale} UTF-8"
                if locale_line in content:
                    content = content.replace(f"#{locale_line}", locale_line)

                    with open(locale_gen_path, "w") as f:
                        f.write(content)

                    self.log(f"Uncommented locale: {locale}")
                else:
                    self.log(f"Locale {locale} not found in locale.gen")
                    return False
            except Exception as e:
                self.log(f"Failed to configure locale.gen: {str(e)}")
                return False
        else:
            self.log("locale.gen not found")
            return False

        # Generate locales
        stdout, stderr, code = self.helper.SysRunCommand(
            ["arch-chroot", mount_point, "locale-gen"], as_root=True
        )
        if code != 0:
            self.log(f"Failed to generate locales: {stderr}")
            return False

        self.log("Locale configuration completed")
        return True

    def _configure_timezone(self, mount_point: str) -> bool:
        """
        Configure system timezone.
        """
        timezone = self.get_config("timezone", "UTC")

        # Create symlink for timezone
        localtime_path = os.path.join(mount_point, "etc", "localtime")
        timezone_path = f"/usr/share/zoneinfo/{timezone}"

        # Remove existing symlink if it exists
        if os.path.exists(localtime_path) or os.path.islink(localtime_path):
            os.remove(localtime_path)

        stdout, stderr, code = self.helper.SysRunCommand(
            ["arch-chroot", mount_point, "ln", "-sf", timezone_path, "/etc/localtime"],
            as_root=True,
        )
        if code != 0:
            self.log(f"Failed to set timezone: {stderr}")
            return False

        self.log(f"Timezone set to: {timezone}")
        return True

    def _configure_hostname(self, mount_point: str) -> bool:
        """
        Ensure hostname is configured (should be done by network module).
        """
        hostname = self.get_config("hostname", "archlinux")
        hostname_path = os.path.join(mount_point, "etc", "hostname")

        # Check if hostname file exists and has content
        if os.path.exists(hostname_path):
            with open(hostname_path, "r") as f:
                current_hostname = f.read().strip()
                if current_hostname == hostname:
                    self.log(f"Hostname already set to: {hostname}")
                    return True

        # Set hostname
        os.makedirs(os.path.dirname(hostname_path), exist_ok=True)
        with open(hostname_path, "w") as f:
            f.write(f"{hostname}\n")

        self.log(f"Hostname set to: {hostname}")
        return True

    def _configure_locale_settings(self, mount_point: str) -> bool:
        """
        Configure locale.conf and other locale settings.
        """
        locale = self.get_config("locale", "en_US.UTF-8")
        locale_conf_path = os.path.join(mount_point, "etc", "locale.conf")

        # Create locale.conf
        os.makedirs(os.path.dirname(locale_conf_path), exist_ok=True)
        with open(locale_conf_path, "w") as f:
            f.write(f"LANG={locale}\n")

        self.log(f"Locale settings configured: {locale}")
        return True
