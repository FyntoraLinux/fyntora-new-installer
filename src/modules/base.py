"""
Base system installation module.
Handles core system setup including filesystem creation, pacstrap, and basic configuration.
"""

import os
from typing import Dict, Any
from lib.module_base import ModuleBase


class BaseModule(ModuleBase):
    """
    Module for installing the base Arch Linux system.
    """

    def __init__(self):
        super().__init__(
            name="base",
            description="Base Arch Linux system installation",
            dependencies=[],
        )

    def validate(self) -> bool:
        """
        Validate base installation requirements.
        """
        self.log("Starting base module validation...")

        # Check if we're running as root or have sudo access
        if os.geteuid() != 0:
            self.log("Base installation requires root privileges")
            return False

        # Check if pacstrap is available
        stdout, stderr, code = self.helper.SysRunCommand(["which", "pacstrap"])
        if code != 0:
            self.log(
                "pacstrap command not found - arch-install-scripts package may not be installed"
            )
            return False

        # Validate required config
        device = self.get_config("device")
        self.log(f"Device config: {device}")
        if not device:
            self.log("No installation device specified")
            return False

        # Check if device exists (optional - partitioning will create partitions)
        if not os.path.exists(device):
            self.log(
                f"Warning: Device {device} does not exist yet - this is OK for partitioning"
            )
        else:
            self.log(f"Device {device} exists")

        mount_point = self.get_config("mount_point", "/mnt")
        self.log(f"Mount point config: {mount_point}")
        if not os.path.exists(mount_point):
            self.log(f"Creating mount point {mount_point}")
            try:
                os.makedirs(mount_point, exist_ok=True)
            except Exception as e:
                self.log(f"Failed to create mount point {mount_point}: {str(e)}")
                return False
        else:
            self.log(f"Mount point {mount_point} exists")

        self.log("Base module validation passed")
        return True

    def install(self) -> bool:
        """
        Install the base Arch Linux system.
        """
        try:
            device = self.get_config("device")
            mount_point = self.get_config("mount_point", "/mnt")

            # Partition and format the device
            if not self._partition_device(device):
                return False

            # Mount the partitions
            if not self._mount_partitions(device, mount_point):
                return False

            # Install base packages
            base_packages = self.get_config(
                "base_packages", ["base", "base-devel", "linux", "linux-firmware"]
            )

            cmd = ["pacstrap", "-K", mount_point] + base_packages
            stdout, stderr, code = self.helper.SysRunCommand(cmd, as_root=True)
            if code != 0:
                self.log(f"Failed to install base packages: {stderr}")
                return False

            # Generate fstab
            if not self._generate_fstab(mount_point):
                return False

            self._installed = True
            self.log("Base system installation completed successfully")
            return True

        except Exception as e:
            self.log(f"Base installation failed: {str(e)}")
            return False

    def _partition_device(self, device: str) -> bool:
        """
        Partition the installation device.
        """
        # Check if device exists
        if not os.path.exists(device):
            self.log(f"Device {device} does not exist")
            return False

        # Create partition table
        self.log(f"Creating GPT partition table on {device}")
        stdout, stderr, code = self.helper.SysRunCommand(
            ["parted", "-s", device, "mklabel", "gpt"], as_root=True
        )
        if code != 0:
            self.log(f"Failed to create partition table: {stderr}")
            return False

        # Create EFI partition (512MB)
        self.log("Creating EFI partition")
        stdout, stderr, code = self.helper.SysRunCommand(
            ["parted", "-s", device, "mkpart", "EFI", "fat32", "1MiB", "513MiB"],
            as_root=True,
        )
        if code != 0:
            self.log(f"Failed to create EFI partition: {stderr}")
            return False

        # Set EFI partition as ESP
        stdout, stderr, code = self.helper.SysRunCommand(
            ["parted", "-s", device, "set", "1", "esp", "on"], as_root=True
        )
        if code != 0:
            self.log(f"Failed to set ESP flag: {stderr}")
            return False

        # Create root partition (remaining space minus swap)
        total_size = self._get_device_size(device)
        swap_size = self.get_config("swap_size", 8)  # GB

        if total_size > 0:
            # Calculate partition sizes
            efi_end = 513  # MiB
            swap_start = total_size - (swap_size * 1024)  # Convert GB to MiB
            root_end = swap_start - 1

            # Create root partition
            self.log("Creating root partition")
            stdout, stderr, code = self.helper.SysRunCommand(
                [
                    "parted",
                    "-s",
                    device,
                    "mkpart",
                    "root",
                    "ext4",
                    "513MiB",
                    f"{root_end}MiB",
                ],
                as_root=True,
            )
            if code != 0:
                self.log(f"Failed to create root partition: {stderr}")
                return False

            # Create swap partition
            self.log("Creating swap partition")
            stdout, stderr, code = self.helper.SysRunCommand(
                [
                    "parted",
                    "-s",
                    device,
                    "mkpart",
                    "swap",
                    "linux-swap",
                    f"{swap_start}MiB",
                    "100%",
                ],
                as_root=True,
            )
            if code != 0:
                self.log(f"Failed to create swap partition: {stderr}")
                return False
        else:
            # Fallback: create root partition with remaining space
            self.log("Creating root partition (fallback)")
            stdout, stderr, code = self.helper.SysRunCommand(
                ["parted", "-s", device, "mkpart", "root", "ext4", "513MiB", "100%"],
                as_root=True,
            )
            if code != 0:
                self.log(f"Failed to create root partition: {stderr}")
                return False

        self.log("Partitioning completed successfully")
        return True

    def _get_device_size(self, device: str) -> int:
        """
        Get device size in MiB.
        """
        try:
            stdout, stderr, code = self.helper.SysRunCommand(
                ["blockdev", "--getsize64", device]
            )
            if code == 0:
                bytes_size = int(stdout.strip())
                return bytes_size // (1024 * 1024)  # Convert to MiB
        except:
            pass
        return 0

    def _mount_partitions(self, device: str, mount_point: str) -> bool:
        """
        Format and mount the partitions.
        """
        efi_partition = f"{device}1"
        root_partition = f"{device}2"
        swap_partition = f"{device}3" if self._partition_exists(f"{device}3") else None

        # Format EFI partition
        self.log("Formatting EFI partition")
        stdout, stderr, code = self.helper.SysRunCommand(
            ["mkfs.fat", "-F32", efi_partition], as_root=True
        )
        if code != 0:
            self.log(f"Failed to format EFI partition: {stderr}")
            return False

        # Format root partition
        self.log("Formatting root partition")
        stdout, stderr, code = self.helper.SysRunCommand(
            ["mkfs.ext4", root_partition], as_root=True
        )
        if code != 0:
            self.log(f"Failed to format root partition: {stderr}")
            return False

        # Format and enable swap if it exists
        if swap_partition:
            self.log("Formatting swap partition")
            stdout, stderr, code = self.helper.SysRunCommand(
                ["mkswap", swap_partition], as_root=True
            )
            if code != 0:
                self.log(f"Failed to format swap partition: {stderr}")
                return False

            stdout, stderr, code = self.helper.SysRunCommand(
                ["swapon", swap_partition], as_root=True
            )
            if code != 0:
                self.log(f"Failed to enable swap: {stderr}")
                # Don't fail here, swap is optional

        # Mount root partition
        self.log("Mounting root partition")
        os.makedirs(mount_point, exist_ok=True)
        stdout, stderr, code = self.helper.SysRunCommand(
            ["mount", root_partition, mount_point], as_root=True
        )
        if code != 0:
            self.log(f"Failed to mount root partition: {stderr}")
            return False

        # Mount EFI partition
        efi_mount = os.path.join(mount_point, "boot", "EFI")
        os.makedirs(efi_mount, exist_ok=True)
        stdout, stderr, code = self.helper.SysRunCommand(
            ["mount", efi_partition, efi_mount], as_root=True
        )
        if code != 0:
            self.log(f"Failed to mount EFI partition: {stderr}")
            return False

        self.log("Partition mounting completed successfully")
        return True

    def _partition_exists(self, partition: str) -> bool:
        """
        Check if a partition exists.
        """
        return os.path.exists(partition)

    def _generate_fstab(self, mount_point: str) -> bool:
        """
        Generate /etc/fstab for the installed system.
        """
        stdout, stderr, code = self.helper.SysRunCommand(
            ["genfstab", "-U", mount_point], as_root=False
        )
        if code != 0:
            self.log(f"Failed to generate fstab: {stderr}")
            return False

        # Write fstab to the mounted system
        fstab_path = os.path.join(mount_point, "etc", "fstab")
        os.makedirs(os.path.dirname(fstab_path), exist_ok=True)

        with open(fstab_path, "w") as f:
            f.write(stdout)

        self.log("Generated fstab successfully")
        return True
