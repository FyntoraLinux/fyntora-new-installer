"""
User management module.
Handles user creation, password setting, and sudo configuration.
"""

import os
from typing import Dict, Any, List
from lib.module_base import ModuleBase


class UserModule(ModuleBase):
    """
    Module for user management.
    """

    def __init__(self):
        super().__init__(
            name="user",
            description="User creation and management",
            dependencies=["base"],
        )

    def validate(self) -> bool:
        """
        Validate user configuration requirements.
        """
        users = self.get_config("users", [])
        if not users:
            self.log("No users specified for creation")
            return False

        mount_point = self.get_config("mount_point", "/mnt")
        if not os.path.exists(mount_point):
            self.log(f"Mount point {mount_point} does not exist")
            return False

        # Validate each user configuration
        for user in users:
            if not isinstance(user, dict) or "username" not in user:
                self.log("Invalid user configuration - missing username")
                return False

        return True

    def install(self) -> bool:
        """
        Create users and configure sudo.
        """
        try:
            mount_point = self.get_config("mount_point", "/mnt")
            users = self.get_config("users", [])

            # Install sudo if not present
            if not self.helper.CheckPackage("sudo"):
                if not self.helper.InstallPackage("sudo"):
                    self.log("Failed to install sudo")
                    return False

            # Create users
            for user_config in users:
                if not self._create_user(mount_point, user_config):
                    return False

            # Configure sudo
            if not self._configure_sudo(mount_point):
                return False

            self._installed = True
            self.log("User management completed successfully")
            return True

        except Exception as e:
            self.log(f"User management failed: {str(e)}")
            return False

    def _create_user(self, mount_point: str, user_config: Dict[str, Any]) -> bool:
        """
        Create a user with the specified configuration.
        """
        username = user_config["username"]
        password = user_config.get("password", "")
        groups = user_config.get("groups", ["wheel"])
        shell = user_config.get("shell", "/bin/bash")

        # Create the user
        cmd = ["useradd", "-m", "-s", shell]
        if groups:
            cmd.extend(["-G", ",".join(groups)])
        cmd.append(username)

        # Run in chroot environment
        chroot_cmd = ["arch-chroot", mount_point] + cmd
        stdout, stderr, code = self.helper.SysRunCommand(chroot_cmd, as_root=True)
        if code != 0:
            self.log(f"Failed to create user {username}: {stderr}")
            return False

        # Set password if provided
        if password:
            if not self._set_user_password(mount_point, username, password):
                return False

        self.log(f"Created user {username}")
        return True

    def _set_user_password(
        self, mount_point: str, username: str, password: str
    ) -> bool:
        """
        Set password for a user.
        """
        # Use chpasswd for setting password
        chpasswd_input = f"{username}:{password}"
        cmd = ["arch-chroot", mount_point, "chpasswd"]
        stdout, stderr, code = self.helper.SysRunCommand(
            cmd, as_root=True, input_text=chpasswd_input
        )
        if code != 0:
            self.log(f"Failed to set password for {username}: {stderr}")
            return False

        self.log(f"Set password for user {username}")
        return True

    def _configure_sudo(self, mount_point: str) -> bool:
        """
        Configure sudo to allow wheel group users.
        """
        sudoers_path = os.path.join(mount_point, "etc", "sudoers.d", "wheel")
        os.makedirs(os.path.dirname(sudoers_path), exist_ok=True)

        sudoers_content = "%wheel ALL=(ALL:ALL) ALL\n"

        with open(sudoers_path, "w") as f:
            f.write(sudoers_content)

        # Set proper permissions
        stdout, stderr, code = self.helper.SysRunCommand(
            ["chmod", "0440", sudoers_path], as_root=True
        )
        if code != 0:
            self.log(f"Failed to set sudoers permissions: {stderr}")
            return False

        self.log("Configured sudo for wheel group")
        return True
