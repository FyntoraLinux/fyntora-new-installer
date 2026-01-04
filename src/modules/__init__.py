"""
Module registry and dependency resolver.
Manages module loading, validation, and execution order.
"""

import sys
import os

# Add parent directory to path for relative imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from typing import Dict, List, Any, Optional, Set
from lib.module_base import ModuleBase


class ModuleRegistry:
    """
    Registry for managing installer modules and their dependencies.
    """

    def __init__(self):
        self.modules: Dict[str, ModuleBase] = {}
        self._load_builtin_modules()

    def _load_builtin_modules(self):
        """
        Load all built-in modules.
        """
        from .base import BaseModule
        from .bootloader import BootloaderModule
        from .network import NetworkModule
        from .user import UserModule
        from .packages import PackageModule
        from .services import ServicesModule
        from .config import ConfigModule

        self.register_module(BaseModule())
        self.register_module(BootloaderModule())
        self.register_module(NetworkModule())
        self.register_module(UserModule())
        self.register_module(PackageModule())
        self.register_module(ServicesModule())
        self.register_module(ConfigModule())

    def register_module(self, module: ModuleBase):
        """
        Register a module in the registry.
        """
        self.modules[module.name] = module

    def get_module(self, name: str) -> Optional[ModuleBase]:
        """
        Get a module by name.
        """
        return self.modules.get(name)

    def get_available_modules(self) -> List[str]:
        """
        Get list of available module names.
        """
        return list(self.modules.keys())

    def resolve_dependencies(self, module_names: List[str]) -> List[str]:
        """
        Resolve module dependencies and return execution order.
        """
        resolved: List[str] = []
        visited: Set[str] = set()
        visiting: Set[str] = set()

        def visit(module_name: str):
            if module_name in visiting:
                raise ValueError(f"Circular dependency detected: {module_name}")
            if module_name in visited:
                return

            visiting.add(module_name)

            module = self.get_module(module_name)
            if not module:
                raise ValueError(f"Module not found: {module_name}")

            # Visit dependencies first
            for dep in module.dependencies:
                visit(dep)

            visiting.remove(module_name)
            visited.add(module_name)
            resolved.append(module_name)

        # Visit all requested modules
        for name in module_names:
            visit(name)

        return resolved

    def validate_modules(self, module_names: List[str]) -> bool:
        """
        Validate all modules in the list.
        """
        for name in module_names:
            module = self.get_module(name)
            if not module:
                print(f"Module not found: {name}")
                return False

            if not module.validate():
                print(f"Module validation failed: {name}")
                return False

        return True

    def configure_modules(self, config: Dict[str, Any]):
        """
        Configure all modules with the provided configuration.
        """
        for module in self.modules.values():
            module_config = config.get(module.name, {})
            if module_config:
                module.set_config(module_config)

            # Also set global config
            global_config = config.get("global", {})
            module.set_config(global_config)
