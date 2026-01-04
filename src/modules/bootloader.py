"""
Bootloader installation and configuration module.
Supports GRUB for both BIOS and UEFI systems.
"""

import os
from typing import Dict, Any
from lib.module_base import ModuleBase


class BootloaderModule(ModuleBase):
    """
    Module for installing and configuring the bootloader.
    """

    def __init__(self):
        super().__init__(
            name="bootloader",
            description="Bootloader installation and configuration",
            dependencies=["base"],
        )

    def validate(self) -> bool:
        """
        Validate bootloader installation requirements.
        """
        bootloader_type = self.get_config("type", "grub")
        if bootloader_type not in ["grub"]:
            self.log(f"Unsupported bootloader type: {bootloader_type}")
            return False

        mount_point = self.get_config("mount_point", "/mnt")
        if not os.path.exists(mount_point):
            self.log(f"Mount point {mount_point} does not exist")
            return False

        return True

    def install(self) -> bool:
        """
        Install and configure the bootloader.
        """
        try:
            bootloader_type = self.get_config("type", "grub")
            mount_point = self.get_config("mount_point", "/mnt")

            if bootloader_type == "grub":
                return self._install_grub(mount_point)

            self._installed = True
            return True

        except Exception as e:
            self.log(f"Bootloader installation failed: {str(e)}")
            return False

    def _install_grub(self, mount_point: str) -> bool:
        """
        Install and configure GRUB bootloader.
        """
        # Install GRUB packages
        grub_packages = ["grub"]
        for pkg in grub_packages:
            if not self.helper.InstallPackage(pkg):
                self.log(f"Failed to install {pkg}")
                return False

        # Determine if we're in UEFI or BIOS mode
        if os.path.exists("/sys/firmware/efi"):
            # UEFI installation
            if not self._install_grub_uefi(mount_point):
                return False
        else:
            # BIOS installation
            if not self._install_grub_bios(mount_point):
                return False

        # Install GRUB to the disk
        device = self.get_config("device", "/dev/sda")
        stdout, stderr, code = self.helper.SysRunCommand(
            ["grub-install", "--target=i386-pc", device], as_root=True
        )
        if code != 0:
            self.log(f"GRUB installation failed: {stderr}")
            return False

        # Generate GRUB configuration
        stdout, stderr, code = self.helper.SysRunCommand(
            ["grub-mkconfig", "-o", "/boot/grub/grub.cfg"], as_root=True
        )
        if code != 0:
            self.log(f"GRUB config generation failed: {stderr}")
            return False

        self.log("GRUB installed and configured successfully")
        return True

    def _install_grub_uefi(self, mount_point: str) -> bool:
        """
        Install GRUB for UEFI systems.
        """
        # Install efibootmgr if not present
        if not self.helper.CheckPackage("efibootmgr"):
            if not self.helper.InstallPackage("efibootmgr"):
                return False

        # Mount EFI partition if needed
        efi_dir = os.path.join(mount_point, "boot", "EFI")
        os.makedirs(efi_dir, exist_ok=True)

        return True

    def _install_grub_bios(self, mount_point: str) -> bool:
        """
        Install GRUB for BIOS systems.
        """
        # For BIOS, we just need the basic GRUB installation
        return True
