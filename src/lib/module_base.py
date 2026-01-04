"""
Base module class for the installer system.
Each installation module should inherit from this base class.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from .runcmd import CommandUseHelper


class ModuleBase(ABC):
    """
    Base class for all installer modules.
    """

    def __init__(
        self, name: str, description: str, dependencies: Optional[List[str]] = None
    ):
        self.name = name
        self.description = description
        self.dependencies = dependencies or []
        self.helper = CommandUseHelper()
        self.config: Dict[str, Any] = {}
        self._installed = False

    @abstractmethod
    def validate(self) -> bool:
        """
        Validate that the module can be installed with current configuration.
        Returns True if valid, False otherwise.
        """
        pass

    @abstractmethod
    def install(self) -> bool:
        """
        Perform the main installation tasks for this module.
        Returns True if successful, False otherwise.
        """
        pass

    def configure(self) -> bool:
        """
        Perform post-installation configuration.
        Default implementation does nothing.
        Returns True if successful, False otherwise.
        """
        return True

    def is_installed(self) -> bool:
        """
        Check if this module has been successfully installed.
        """
        return self._installed

    def set_config(self, config: Dict[str, Any]):
        """
        Set configuration for this module.
        """
        self.config.update(config)

    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value for this module.
        """
        return self.config.get(key, default)

    def log(self, message: str):
        """
        Log a message with module context.
        """
        self.helper._log(f"[{self.name}] {message}")

    def __repr__(self):
        return f"Module({self.name}: {self.description})"
