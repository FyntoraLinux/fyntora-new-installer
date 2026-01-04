import subprocess
import datetime

class CommandUseHelper:
    def __init__(self, log_file="installer.log"):
        self.log_file = log_file

    def _log(self, message):
        """Append a timestamped message to the log file."""
        timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        with open(self.log_file, "a") as f:
            f.write(f"{timestamp} {message}\n")

    def SysRunCommand(self, command, as_root=False):
        """
        Runs a system command, optionally as root, and logs the result.
        
        :param command: Command to run (string or list)
        :param as_root: Whether to run with sudo
        :return: (stdout, stderr, returncode)
        """
        if as_root:
            if isinstance(command, list):
                command = ["sudo"] + command
            else:
                command = f"sudo {command}"

        try:
            if isinstance(command, str):
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
            else:
                result = subprocess.run(command, shell=False, capture_output=True, text=True)

            # Log command and output
            self._log(f"COMMAND: {command}")
            self._log(f"STDOUT: {result.stdout.strip()}")
            self._log(f"STDERR: {result.stderr.strip()}")
            self._log(f"RETURN CODE: {result.returncode}")

            return result.stdout.strip(), result.stderr.strip(), result.returncode
        except Exception as e:
            self._log(f"EXCEPTION: {e}")
            return "", str(e), -1

    def CheckPackage(self, package_name):
        """
        Checks if a package is installed using pacman.
        
        :param package_name: Name of the package
        :return: True if installed, False otherwise
        """
        stdout, stderr, code = self.SysRunCommand(["pacman", "-Q", package_name])
        if code == 0:
            self._log(f"Package '{package_name}' is already installed.")
            return True
        else:
            self._log(f"Package '{package_name}' is NOT installed.")
            return False

    def InstallPackage(self, package_name):
        """
        Installs a package using pacman if it is not already installed.
        
        :param package_name: Name of the package
        :return: True if installed successfully or already installed
        """
        if self.CheckPackage(package_name):
            return True

        stdout, stderr, code = self.SysRunCommand(["pacman", "-S", "--noconfirm", "--needed", package_name], as_root=True)
        if code == 0:
            self._log(f"Successfully installed '{package_name}'.")
            return True
        else:
            self._log(f"Failed to install '{package_name}'. Error: {stderr}")
            return False

# # Example usage
# if __name__ == "__main__":
#     helper = ArchInstallerHelper()
#     helper.SysRunCommand("echo Hello, Arch Installer!", as_root=False)
#     print(helper.CheckPackage("vim"))  # Check if vim is installed
#     helper.InstallPackage("vim")       # Install vim if missing


