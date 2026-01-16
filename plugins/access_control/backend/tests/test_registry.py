"""
Tests for the Access Control Plugin Registry

This module contains unit tests for the CustomPluginRegistry class,
verifying plugin registration, discovery, and query functionality.

Validates: Requirements 1.2, 1.3
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Add the source directory to the path to import registry directly
src_path = Path(__file__).parent.parent / "src" / "access_control"
if str(src_path.parent) not in sys.path:
    sys.path.insert(0, str(src_path.parent))

# Import directly from the registry module to avoid Django dependencies
from access_control.registry import (
    CustomPluginRegistry,
    PluginInfo,
    custom_plugin_registry,
    discover_plugins,
    get_all_plugins,
    get_plugin,
    register_plugin,
)


class TestPluginInfo:
    """Tests for the PluginInfo dataclass."""
    
    def test_plugin_info_creation(self):
        """Test creating a PluginInfo instance."""
        info = PluginInfo(
            plugin_type="test_plugin",
            name="Test Plugin",
            version="1.0.0",
            description="A test plugin",
            author="Test Author",
        )
        
        assert info.plugin_type == "test_plugin"
        assert info.name == "Test Plugin"
        assert info.version == "1.0.0"
        assert info.description == "A test plugin"
        assert info.author == "Test Author"
        assert info.is_active is True
    
    def test_plugin_info_to_dict(self):
        """Test converting PluginInfo to dictionary."""
        info = PluginInfo(
            plugin_type="test_plugin",
            name="Test Plugin",
            version="2.0.0",
        )
        
        result = info.to_dict()
        
        assert result["plugin_type"] == "test_plugin"
        assert result["name"] == "Test Plugin"
        assert result["version"] == "2.0.0"
        assert result["is_active"] is True
    
    def test_plugin_info_from_dict(self):
        """Test creating PluginInfo from dictionary."""
        data = {
            "name": "My Plugin",
            "version": "3.0.0",
            "description": "Description",
            "author": "Author",
            "license": "MIT",
        }
        
        info = PluginInfo.from_dict("my_plugin", data)
        
        assert info.plugin_type == "my_plugin"
        assert info.name == "My Plugin"
        assert info.version == "3.0.0"
        assert info.description == "Description"
        assert info.author == "Author"
        assert info.license == "MIT"
    
    def test_plugin_info_from_dict_with_defaults(self):
        """Test creating PluginInfo from minimal dictionary."""
        data = {"name": "Minimal Plugin"}
        
        info = PluginInfo.from_dict("minimal", data)
        
        assert info.plugin_type == "minimal"
        assert info.name == "Minimal Plugin"
        assert info.version == "1.0.0"  # default
        assert info.description == ""  # default
        assert info.is_active is True  # default


class TestCustomPluginRegistry:
    """Tests for the CustomPluginRegistry class."""
    
    @pytest.fixture(autouse=True)
    def setup_registry(self):
        """Reset the registry before each test."""
        # Create a fresh registry instance for testing
        self.registry = CustomPluginRegistry()
        self.registry.clear()
        # Mark as discovered to prevent auto-discovery during tests
        self.registry._discovered = True
        yield
        self.registry.clear()
    
    def test_singleton_pattern(self):
        """Test that CustomPluginRegistry follows singleton pattern."""
        registry1 = CustomPluginRegistry()
        registry2 = CustomPluginRegistry()
        
        assert registry1 is registry2
    
    def test_register_plugin(self):
        """Test registering a plugin."""
        plugin_info = {
            "name": "Test Plugin",
            "version": "1.0.0",
            "description": "A test plugin",
        }
        
        result = self.registry.register("test_plugin", plugin_info)
        
        assert result.plugin_type == "test_plugin"
        assert result.name == "Test Plugin"
        assert self.registry.has_plugin("test_plugin")
    
    def test_register_plugin_empty_type_raises_error(self):
        """Test that registering with empty plugin_type raises ValueError."""
        with pytest.raises(ValueError, match="plugin_type cannot be empty"):
            self.registry.register("", {"name": "Test"})
    
    def test_register_plugin_updates_existing(self):
        """Test that registering an existing plugin updates it."""
        self.registry.register("test_plugin", {"name": "Original"})
        self.registry.register("test_plugin", {"name": "Updated"})
        
        plugin = self.registry.get_plugin("test_plugin")
        assert plugin.name == "Updated"
    
    def test_unregister_plugin(self):
        """Test unregistering a plugin."""
        self.registry.register("test_plugin", {"name": "Test"})
        
        result = self.registry.unregister("test_plugin")
        
        assert result is True
        assert not self.registry.has_plugin("test_plugin")
    
    def test_unregister_nonexistent_plugin(self):
        """Test unregistering a non-existent plugin returns False."""
        result = self.registry.unregister("nonexistent")
        
        assert result is False
    
    def test_get_plugin(self):
        """Test getting a specific plugin."""
        self.registry.register("test_plugin", {"name": "Test Plugin"})
        
        plugin = self.registry.get_plugin("test_plugin")
        
        assert plugin is not None
        assert plugin.name == "Test Plugin"
    
    def test_get_plugin_nonexistent(self):
        """Test getting a non-existent plugin returns None."""
        plugin = self.registry.get_plugin("nonexistent")
        
        assert plugin is None
    
    def test_get_all_plugins(self):
        """Test getting all registered plugins."""
        self.registry.register("plugin1", {"name": "Plugin 1"})
        self.registry.register("plugin2", {"name": "Plugin 2"})
        
        plugins = self.registry.get_all_plugins()
        
        assert len(plugins) == 2
        assert "plugin1" in plugins
        assert "plugin2" in plugins
    
    def test_get_all_plugins_returns_copy(self):
        """Test that get_all_plugins returns a copy."""
        self.registry.register("test_plugin", {"name": "Test"})
        
        plugins = self.registry.get_all_plugins()
        plugins["new_plugin"] = PluginInfo("new", "New")
        
        # Original registry should not be affected
        assert not self.registry.has_plugin("new_plugin")
    
    def test_get_all_plugins_list(self):
        """Test getting all plugins as a list."""
        self.registry.register("plugin1", {"name": "Plugin 1"})
        self.registry.register("plugin2", {"name": "Plugin 2"})
        
        plugins = self.registry.get_all_plugins_list()
        
        assert len(plugins) == 2
        assert all(isinstance(p, PluginInfo) for p in plugins)
    
    def test_get_active_plugins(self):
        """Test getting only active plugins."""
        self.registry.register("active", {"name": "Active", "is_active": True})
        self.registry.register("inactive", {"name": "Inactive", "is_active": False})
        
        active = self.registry.get_active_plugins()
        
        assert len(active) == 1
        assert "active" in active
    
    def test_get_plugin_types(self):
        """Test getting list of plugin types."""
        self.registry.register("plugin1", {"name": "Plugin 1"})
        self.registry.register("plugin2", {"name": "Plugin 2"})
        
        types = self.registry.get_plugin_types()
        
        assert set(types) == {"plugin1", "plugin2"}
    
    def test_has_plugin(self):
        """Test checking if a plugin exists."""
        self.registry.register("test_plugin", {"name": "Test"})
        
        assert self.registry.has_plugin("test_plugin") is True
        assert self.registry.has_plugin("nonexistent") is False
    
    def test_clear(self):
        """Test clearing the registry."""
        self.registry.register("test_plugin", {"name": "Test"})
        self.registry._discovered = True
        
        self.registry.clear()
        
        assert len(self.registry._plugins) == 0
        assert self.registry._discovered is False


class TestPluginDiscovery:
    """Tests for plugin discovery functionality."""
    
    @pytest.fixture
    def temp_plugins_dir(self):
        """Create a temporary plugins directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugins_dir = Path(tmpdir) / "plugins"
            plugins_dir.mkdir()
            yield plugins_dir
    
    @pytest.fixture(autouse=True)
    def setup_registry(self):
        """Reset the registry before each test."""
        registry = CustomPluginRegistry()
        registry.clear()
        yield
        registry.clear()
    
    def test_discover_plugins_from_directory(self, temp_plugins_dir):
        """Test discovering plugins from a directory."""
        # Create a test plugin
        plugin_dir = temp_plugins_dir / "test_plugin"
        plugin_dir.mkdir()
        
        plugin_info = {
            "name": "Test Plugin",
            "version": "1.0.0",
            "description": "A test plugin",
        }
        
        with open(plugin_dir / "baserow_plugin_info.json", "w") as f:
            json.dump(plugin_info, f)
        
        registry = CustomPluginRegistry()
        registry.clear()
        
        # Mock the plugins directory search
        with patch.object(
            registry, "_find_plugins_directory", return_value=temp_plugins_dir
        ):
            plugins = registry.discover_plugins(force=True)
        
        assert "test_plugin" in plugins
        assert plugins["test_plugin"].name == "Test Plugin"
    
    def test_discover_plugins_skips_excluded(self, temp_plugins_dir):
        """Test that excluded plugins are skipped during discovery."""
        # Create an excluded plugin (access_control)
        excluded_dir = temp_plugins_dir / "access_control"
        excluded_dir.mkdir()
        
        with open(excluded_dir / "baserow_plugin_info.json", "w") as f:
            json.dump({"name": "Access Control"}, f)
        
        registry = CustomPluginRegistry()
        registry.clear()
        
        with patch.object(
            registry, "_find_plugins_directory", return_value=temp_plugins_dir
        ):
            plugins = registry.discover_plugins(force=True)
        
        assert "access_control" not in plugins
    
    def test_discover_plugins_skips_hidden_directories(self, temp_plugins_dir):
        """Test that hidden directories are skipped during discovery."""
        # Create a hidden directory
        hidden_dir = temp_plugins_dir / ".hidden_plugin"
        hidden_dir.mkdir()
        
        with open(hidden_dir / "baserow_plugin_info.json", "w") as f:
            json.dump({"name": "Hidden Plugin"}, f)
        
        registry = CustomPluginRegistry()
        registry.clear()
        
        with patch.object(
            registry, "_find_plugins_directory", return_value=temp_plugins_dir
        ):
            plugins = registry.discover_plugins(force=True)
        
        assert ".hidden_plugin" not in plugins
    
    def test_discover_plugins_handles_missing_info_file(self, temp_plugins_dir):
        """Test discovering plugins without info file."""
        # Create a plugin directory without info file
        plugin_dir = temp_plugins_dir / "no_info_plugin"
        plugin_dir.mkdir()
        
        registry = CustomPluginRegistry()
        registry.clear()
        
        with patch.object(
            registry, "_find_plugins_directory", return_value=temp_plugins_dir
        ):
            plugins = registry.discover_plugins(force=True)
        
        # Plugin should still be registered with minimal info
        assert "no_info_plugin" in plugins
        assert plugins["no_info_plugin"].name == "no_info_plugin"
    
    def test_discover_plugins_handles_invalid_json(self, temp_plugins_dir):
        """Test handling of invalid JSON in plugin info file."""
        # Create a plugin with invalid JSON
        plugin_dir = temp_plugins_dir / "invalid_json_plugin"
        plugin_dir.mkdir()
        
        with open(plugin_dir / "baserow_plugin_info.json", "w") as f:
            f.write("{ invalid json }")
        
        registry = CustomPluginRegistry()
        registry.clear()
        
        with patch.object(
            registry, "_find_plugins_directory", return_value=temp_plugins_dir
        ):
            # Should not raise an exception
            plugins = registry.discover_plugins(force=True)
        
        # Invalid plugin should not be registered
        assert "invalid_json_plugin" not in plugins
    
    def test_discover_plugins_caches_result(self, temp_plugins_dir):
        """Test that discovery result is cached."""
        plugin_dir = temp_plugins_dir / "test_plugin"
        plugin_dir.mkdir()
        
        with open(plugin_dir / "baserow_plugin_info.json", "w") as f:
            json.dump({"name": "Test Plugin"}, f)
        
        registry = CustomPluginRegistry()
        registry.clear()
        
        with patch.object(
            registry, "_find_plugins_directory", return_value=temp_plugins_dir
        ) as mock_find:
            registry.discover_plugins()
            registry.discover_plugins()  # Second call should use cache
        
        # _find_plugins_directory should only be called once
        assert mock_find.call_count == 1
    
    def test_discover_plugins_force_refresh(self, temp_plugins_dir):
        """Test forcing a refresh of plugin discovery."""
        plugin_dir = temp_plugins_dir / "test_plugin"
        plugin_dir.mkdir()
        
        with open(plugin_dir / "baserow_plugin_info.json", "w") as f:
            json.dump({"name": "Test Plugin"}, f)
        
        registry = CustomPluginRegistry()
        registry.clear()
        
        with patch.object(
            registry, "_find_plugins_directory", return_value=temp_plugins_dir
        ) as mock_find:
            registry.discover_plugins()
            registry.discover_plugins(force=True)  # Force refresh
        
        # _find_plugins_directory should be called twice
        assert mock_find.call_count == 2
    
    def test_refresh_clears_and_rediscovers(self, temp_plugins_dir):
        """Test that refresh clears and re-discovers plugins."""
        plugin_dir = temp_plugins_dir / "test_plugin"
        plugin_dir.mkdir()
        
        with open(plugin_dir / "baserow_plugin_info.json", "w") as f:
            json.dump({"name": "Test Plugin"}, f)
        
        registry = CustomPluginRegistry()
        registry.clear()
        
        with patch.object(
            registry, "_find_plugins_directory", return_value=temp_plugins_dir
        ):
            registry.discover_plugins()
            
            # Manually add a plugin
            registry.register("manual_plugin", {"name": "Manual"})
            
            # Refresh should clear manual plugin
            registry.refresh()
        
        assert "test_plugin" in registry._plugins
        assert "manual_plugin" not in registry._plugins


class TestModuleLevelFunctions:
    """Tests for module-level convenience functions."""
    
    @pytest.fixture(autouse=True)
    def setup_registry(self):
        """Reset the global registry before each test."""
        custom_plugin_registry.clear()
        # Mark as discovered to prevent auto-discovery during tests
        custom_plugin_registry._discovered = True
        yield
        custom_plugin_registry.clear()
    
    def test_register_plugin_function(self):
        """Test the register_plugin convenience function."""
        result = register_plugin("test_plugin", {"name": "Test Plugin"})
        
        assert result.plugin_type == "test_plugin"
        assert custom_plugin_registry.has_plugin("test_plugin")
    
    def test_get_plugin_function(self):
        """Test the get_plugin convenience function."""
        register_plugin("test_plugin", {"name": "Test Plugin"})
        
        plugin = get_plugin("test_plugin")
        
        assert plugin is not None
        assert plugin.name == "Test Plugin"
    
    def test_get_all_plugins_function(self):
        """Test the get_all_plugins convenience function."""
        register_plugin("plugin1", {"name": "Plugin 1"})
        register_plugin("plugin2", {"name": "Plugin 2"})
        
        plugins = get_all_plugins()
        
        assert len(plugins) == 2
    
    def test_discover_plugins_function(self):
        """Test the discover_plugins convenience function."""
        # This test just verifies the function doesn't raise an error
        # Actual discovery depends on the file system
        custom_plugin_registry._discovered = True  # Skip actual discovery
        
        plugins = discover_plugins()
        
        assert isinstance(plugins, dict)


class TestPluginRegistryIntegrity:
    """
    Property-based tests for plugin registry integrity.
    
    Validates: Requirements 1.2, 1.3
    Property 1: Plugin registry integrity - newly registered plugins
    should immediately appear in the registry.
    """
    
    @pytest.fixture(autouse=True)
    def setup_registry(self):
        """Reset the registry before each test."""
        registry = CustomPluginRegistry()
        registry.clear()
        # Mark as discovered to prevent auto-discovery during tests
        registry._discovered = True
        yield
        registry.clear()
    
    def test_registered_plugin_immediately_available(self):
        """
        Property: For any plugin registered, it should immediately
        be available in the registry.
        
        Validates: Requirements 1.2, 1.3
        """
        registry = CustomPluginRegistry()
        registry._discovered = True  # Prevent auto-discovery
        
        # Register multiple plugins
        plugins_to_register = [
            ("plugin_a", {"name": "Plugin A", "version": "1.0.0"}),
            ("plugin_b", {"name": "Plugin B", "version": "2.0.0"}),
            ("plugin_c", {"name": "Plugin C", "version": "3.0.0"}),
        ]
        
        for plugin_type, plugin_info in plugins_to_register:
            registry.register(plugin_type, plugin_info)
            
            # Immediately verify the plugin is available
            retrieved = registry.get_plugin(plugin_type)
            assert retrieved is not None
            assert retrieved.plugin_type == plugin_type
            assert retrieved.name == plugin_info["name"]
            assert retrieved.version == plugin_info["version"]
            
            # Verify it appears in all plugins list
            all_plugins = registry.get_all_plugins()
            assert plugin_type in all_plugins
    
    def test_plugin_count_matches_registrations(self):
        """
        Property: The number of plugins in the registry should match
        the number of unique registrations.
        
        Validates: Requirements 1.2, 1.3
        """
        registry = CustomPluginRegistry()
        registry._discovered = True  # Prevent auto-discovery
        
        # Register plugins
        for i in range(5):
            registry.register(f"plugin_{i}", {"name": f"Plugin {i}"})
        
        assert len(registry.get_all_plugins()) == 5
        
        # Re-registering should not increase count
        registry.register("plugin_0", {"name": "Plugin 0 Updated"})
        assert len(registry.get_all_plugins()) == 5
    
    def test_unregistered_plugin_not_available(self):
        """
        Property: After unregistering a plugin, it should no longer
        be available in the registry.
        
        Validates: Requirements 1.2, 1.3
        """
        registry = CustomPluginRegistry()
        registry._discovered = True  # Prevent auto-discovery
        
        # Register and then unregister
        registry.register("test_plugin", {"name": "Test"})
        assert registry.has_plugin("test_plugin")
        
        registry.unregister("test_plugin")
        assert not registry.has_plugin("test_plugin")
        assert registry.get_plugin("test_plugin") is None



class TestRealPluginDiscovery:
    """
    Integration tests for real plugin discovery.
    
    These tests verify that the registry can discover actual plugins
    installed in the plugins directory.
    """
    
    @pytest.fixture(autouse=True)
    def setup_registry(self):
        """Reset the registry before each test."""
        registry = CustomPluginRegistry()
        registry.clear()
        yield
        registry.clear()
    
    def test_discover_real_plugins(self):
        """
        Test that the registry discovers real plugins from the plugins directory.
        
        This test verifies that the plugin discovery mechanism works correctly
        with the actual plugins installed in the project.
        
        Validates: Requirements 1.2, 1.3
        """
        registry = CustomPluginRegistry()
        registry.clear()
        
        # Force discovery
        plugins = registry.discover_plugins(force=True)
        
        # We should find at least some of the known plugins
        # (excluding access_control which is in EXCLUDED_PLUGINS)
        known_plugins = {
            "ai_assistant",
            "excel_importer",
            "row_author_tracker",
            "table_permissions",
        }
        
        discovered_types = set(plugins.keys())
        
        # At least some known plugins should be discovered
        found_plugins = known_plugins & discovered_types
        assert len(found_plugins) > 0, (
            f"Expected to find some of {known_plugins}, "
            f"but only found {discovered_types}"
        )
        
        # Verify plugin info is correctly loaded
        for plugin_type in found_plugins:
            plugin = plugins[plugin_type]
            assert plugin.plugin_type == plugin_type
            assert plugin.name  # Should have a name
            assert plugin.version  # Should have a version
    
    def test_access_control_excluded_from_discovery(self):
        """
        Test that access_control plugin is excluded from discovery.
        
        The access_control plugin should not appear in the list of
        discovered plugins since it's the plugin providing the registry.
        """
        registry = CustomPluginRegistry()
        registry.clear()
        
        plugins = registry.discover_plugins(force=True)
        
        assert "access_control" not in plugins
    
    def test_newly_registered_plugin_appears_immediately(self):
        """
        Test that a newly registered plugin appears immediately in the registry.
        
        This is a key requirement: when a new plugin is installed,
        it should be immediately available in the plugin list.
        
        Validates: Requirements 1.2, 1.3
        """
        registry = CustomPluginRegistry()
        registry.clear()
        
        # First discover existing plugins
        initial_plugins = registry.discover_plugins(force=True)
        initial_count = len(initial_plugins)
        
        # Register a new plugin manually
        new_plugin_info = {
            "name": "New Test Plugin",
            "version": "1.0.0",
            "description": "A newly installed plugin",
        }
        registry.register("new_test_plugin", new_plugin_info)
        
        # The new plugin should immediately appear
        all_plugins = registry.get_all_plugins()
        assert "new_test_plugin" in all_plugins
        assert len(all_plugins) == initial_count + 1
        
        # Verify the plugin info
        new_plugin = registry.get_plugin("new_test_plugin")
        assert new_plugin.name == "New Test Plugin"
        assert new_plugin.version == "1.0.0"
