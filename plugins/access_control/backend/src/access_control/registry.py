"""
Access Control Plugin Registry

This module implements the plugin registry that automatically discovers
and manages all custom plugins installed in the system.

The registry provides:
- Dynamic discovery of installed plugins from the plugins directory
- Registration and management of custom plugins
- Query methods to retrieve plugin information

Validates: Requirements 1.2, 1.3
"""

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class PluginInfo:
    """
    Data class representing plugin information.
    
    Attributes:
        plugin_type: Unique identifier for the plugin (derived from directory name)
        name: Human-readable name of the plugin
        version: Plugin version string
        description: Plugin description
        author: Plugin author
        license: Plugin license (optional)
        modules: Dictionary of module paths
        is_active: Whether the plugin is currently active
        permission_levels: 支持的权限级别列表,如 ["use", "configure"]
        admin_only: 是否仅管理员可用
    """
    plugin_type: str
    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    license: str = ""
    modules: Dict[str, str] = field(default_factory=dict)
    is_active: bool = True
    permission_levels: List[str] = field(default_factory=lambda: ["use", "configure"])
    admin_only: bool = False
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "plugin_type": self.plugin_type,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "license": self.license,
            "modules": self.modules,
            "is_active": self.is_active,
            "permission_levels": self.permission_levels,
            "admin_only": self.admin_only,
        }
    
    @classmethod
    def from_dict(cls, plugin_type: str, data: dict) -> "PluginInfo":
        """Create PluginInfo from dictionary."""
        return cls(
            plugin_type=plugin_type,
            name=data.get("name", plugin_type),
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            author=data.get("author", ""),
            license=data.get("license", ""),
            modules=data.get("modules", {}),
            is_active=data.get("is_active", True),
            permission_levels=data.get("permission_levels", ["use", "configure"]),
            admin_only=data.get("admin_only", False),
        )


class CustomPluginRegistry:
    """
    Registry for managing custom plugins.
    
    This registry automatically discovers all installed custom plugins
    and provides methods to query and manage them.
    
    The registry uses a singleton pattern to ensure only one instance exists.
    
    Validates: Requirements 1.2, 1.3
    """
    
    _instance: Optional["CustomPluginRegistry"] = None
    _plugins: Dict[str, PluginInfo]
    _discovered: bool
    
    # Plugins to exclude from the registry (system plugins, not custom plugins)
    EXCLUDED_PLUGINS = frozenset([
        "access_control",  # This plugin itself
    ])
    
    # Plugin info filename
    PLUGIN_INFO_FILENAME = "baserow_plugin_info.json"
    
    def __new__(cls) -> "CustomPluginRegistry":
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._plugins = {}
            cls._instance._discovered = False
        return cls._instance
    
    def register(self, plugin_type: str, plugin_info: dict) -> PluginInfo:
        """
        Register a plugin with the registry.
        
        Args:
            plugin_type: Unique identifier for the plugin
            plugin_info: Dictionary containing plugin metadata
            
        Returns:
            The registered PluginInfo object
            
        Raises:
            ValueError: If plugin_type is empty or already registered
        """
        if not plugin_type:
            raise ValueError("plugin_type cannot be empty")
        
        if plugin_type in self._plugins:
            logger.warning(
                f"Plugin '{plugin_type}' is already registered, updating..."
            )
        
        info = PluginInfo.from_dict(plugin_type, plugin_info)
        self._plugins[plugin_type] = info
        
        logger.info(f"Registered plugin: {plugin_type} ({info.name})")
        return info
    
    def unregister(self, plugin_type: str) -> bool:
        """
        Unregister a plugin from the registry.
        
        Args:
            plugin_type: The plugin type identifier
            
        Returns:
            True if the plugin was unregistered, False if not found
        """
        if plugin_type in self._plugins:
            del self._plugins[plugin_type]
            logger.info(f"Unregistered plugin: {plugin_type}")
            return True
        return False
    
    def get_plugin(self, plugin_type: str) -> Optional[PluginInfo]:
        """
        Get a specific plugin by type.
        
        Args:
            plugin_type: The plugin type identifier
            
        Returns:
            PluginInfo object or None if not found
        """
        # Ensure plugins are discovered
        if not self._discovered:
            self.discover_plugins()
        
        return self._plugins.get(plugin_type)
    
    def get_all_plugins(self) -> Dict[str, PluginInfo]:
        """
        Get all registered plugins.
        
        Returns:
            Dictionary of all registered plugins (plugin_type -> PluginInfo)
        """
        # Ensure plugins are discovered
        if not self._discovered:
            self.discover_plugins()
        
        return self._plugins.copy()
    
    def get_all_plugins_list(self) -> List[PluginInfo]:
        """
        Get all registered plugins as a list.
        
        Returns:
            List of all registered PluginInfo objects
        """
        return list(self.get_all_plugins().values())
    
    def get_active_plugins(self) -> Dict[str, PluginInfo]:
        """
        Get all active plugins.
        
        Returns:
            Dictionary of active plugins (plugin_type -> PluginInfo)
        """
        return {
            k: v for k, v in self.get_all_plugins().items() 
            if v.is_active
        }
    
    def get_plugin_types(self) -> List[str]:
        """
        Get list of all registered plugin types.
        
        Returns:
            List of plugin type identifiers
        """
        return list(self.get_all_plugins().keys())
    
    def has_plugin(self, plugin_type: str) -> bool:
        """
        Check if a plugin is registered.
        
        Args:
            plugin_type: The plugin type identifier
            
        Returns:
            True if the plugin is registered, False otherwise
        """
        return plugin_type in self.get_all_plugins()
    
    def discover_plugins(self, force: bool = False) -> Dict[str, PluginInfo]:
        """
        Discover and register all installed custom plugins.
        
        This method scans the plugins directory for installed plugins
        and registers them with the registry.
        
        Args:
            force: If True, re-discover plugins even if already discovered
            
        Returns:
            Dictionary of discovered plugins
            
        Validates: Requirements 1.2, 1.3
        """
        if self._discovered and not force:
            return self._plugins.copy()
        
        logger.info("Discovering installed plugins...")
        
        # Find the plugins directory
        plugins_dir = self._find_plugins_directory()
        
        if plugins_dir and plugins_dir.exists():
            self._scan_plugins_directory(plugins_dir)
        else:
            logger.warning(
                f"Plugins directory not found. "
                f"Searched paths: {self._get_search_paths()}"
            )
        
        self._discovered = True
        
        logger.info(
            f"Plugin discovery complete. "
            f"Found {len(self._plugins)} plugin(s): {list(self._plugins.keys())}"
        )
        
        return self._plugins.copy()
    
    def _find_plugins_directory(self) -> Optional[Path]:
        """
        Find the plugins directory.
        
        Returns:
            Path to the plugins directory or None if not found
        """
        for search_path in self._get_search_paths():
            path = Path(search_path)
            if path.exists() and path.is_dir():
                return path
        return None
    
    def _get_search_paths(self) -> List[str]:
        """
        Get list of paths to search for plugins directory.
        
        Returns:
            List of directory paths to search
        """
        paths = []
        
        # Check environment variable first
        env_path = os.environ.get("BASEROW_PLUGINS_DIR")
        if env_path:
            paths.append(env_path)
        
        # Get the current file's directory and traverse up to find plugins
        current_dir = Path(__file__).resolve().parent
        
        # Traverse up to find the project root (where plugins directory is)
        # Current path: plugins/access_control/backend/src/access_control/registry.py
        # We need to go up 5 levels to reach the project root
        for _ in range(10):  # Max 10 levels up
            potential_plugins_dir = current_dir / "plugins"
            if potential_plugins_dir.exists():
                paths.append(str(potential_plugins_dir))
                break
            current_dir = current_dir.parent
        
        # Also check common relative paths from working directory
        cwd = Path.cwd()
        paths.extend([
            str(cwd / "plugins"),
            str(cwd.parent / "plugins"),
        ])
        
        return paths
    
    def _scan_plugins_directory(self, plugins_dir: Path) -> None:
        """
        Scan the plugins directory and register found plugins.
        
        Args:
            plugins_dir: Path to the plugins directory
        """
        for item in plugins_dir.iterdir():
            if not item.is_dir():
                continue
            
            plugin_type = item.name
            
            # Skip excluded plugins
            if plugin_type in self.EXCLUDED_PLUGINS:
                logger.debug(f"Skipping excluded plugin: {plugin_type}")
                continue
            
            # Skip hidden directories
            if plugin_type.startswith(".") or plugin_type.startswith("_"):
                continue
            
            # Look for plugin info file
            plugin_info_path = item / self.PLUGIN_INFO_FILENAME
            
            if plugin_info_path.exists():
                try:
                    plugin_info = self._load_plugin_info(plugin_info_path)
                    self.register(plugin_type, plugin_info)
                except Exception as e:
                    logger.error(
                        f"Failed to load plugin info for '{plugin_type}': {e}"
                    )
            else:
                # Register plugin with minimal info if no info file exists
                logger.debug(
                    f"No {self.PLUGIN_INFO_FILENAME} found for '{plugin_type}', "
                    f"registering with minimal info"
                )
                self.register(plugin_type, {"name": plugin_type})
    
    def _load_plugin_info(self, path: Path) -> dict:
        """
        Load plugin info from a JSON file.
        
        Args:
            path: Path to the plugin info JSON file
            
        Returns:
            Dictionary containing plugin info
            
        Raises:
            json.JSONDecodeError: If the file is not valid JSON
            IOError: If the file cannot be read
        """
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def clear(self) -> None:
        """
        Clear all registered plugins.
        
        This is mainly useful for testing.
        """
        self._plugins.clear()
        self._discovered = False
        logger.info("Plugin registry cleared")
    
    def refresh(self) -> Dict[str, PluginInfo]:
        """
        Refresh the plugin registry by re-discovering plugins.
        
        Returns:
            Dictionary of discovered plugins
        """
        self.clear()
        return self.discover_plugins(force=True)


# Global plugin registry instance
custom_plugin_registry = CustomPluginRegistry()


# Convenience functions for module-level access
def register_plugin(plugin_type: str, plugin_info: dict) -> PluginInfo:
    """
    Register a plugin with the global registry.
    
    Args:
        plugin_type: Unique identifier for the plugin
        plugin_info: Dictionary containing plugin metadata
        
    Returns:
        The registered PluginInfo object
    """
    return custom_plugin_registry.register(plugin_type, plugin_info)


def get_plugin(plugin_type: str) -> Optional[PluginInfo]:
    """
    Get a specific plugin from the global registry.
    
    Args:
        plugin_type: The plugin type identifier
        
    Returns:
        PluginInfo object or None if not found
    """
    return custom_plugin_registry.get_plugin(plugin_type)


def get_all_plugins() -> Dict[str, PluginInfo]:
    """
    Get all plugins from the global registry.
    
    Returns:
        Dictionary of all registered plugins
    """
    return custom_plugin_registry.get_all_plugins()


def discover_plugins(force: bool = False) -> Dict[str, PluginInfo]:
    """
    Discover and register all installed custom plugins.
    
    Args:
        force: If True, re-discover plugins even if already discovered
        
    Returns:
        Dictionary of discovered plugins
    """
    return custom_plugin_registry.discover_plugins(force=force)
