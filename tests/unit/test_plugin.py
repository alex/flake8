"""Tests for flake8.plugins.manager.Plugin."""
import optparse

import mock
import pytest

from flake8 import exceptions
from flake8.plugins import manager


def test_load_plugin_fallsback_on_old_setuptools():
    """Verify we fallback gracefully to on old versions of setuptools."""
    entry_point = mock.Mock(spec=['load'])
    plugin = manager.Plugin('T000', entry_point)

    plugin.load_plugin()
    entry_point.load.assert_called_once_with(require=False)


def test_load_plugin_avoids_deprecated_entry_point_methods():
    """Verify we use the preferred methods on new versions of setuptools."""
    entry_point = mock.Mock(spec=['require', 'resolve', 'load'])
    plugin = manager.Plugin('T000', entry_point)

    plugin.load_plugin(verify_requirements=True)
    assert entry_point.load.called is False
    entry_point.require.assert_called_once_with()
    entry_point.resolve.assert_called_once_with()


def test_load_plugin_is_idempotent():
    """Verify we use the preferred methods on new versions of setuptools."""
    entry_point = mock.Mock(spec=['require', 'resolve', 'load'])
    plugin = manager.Plugin('T000', entry_point)

    plugin.load_plugin(verify_requirements=True)
    plugin.load_plugin(verify_requirements=True)
    plugin.load_plugin()
    assert entry_point.load.called is False
    entry_point.require.assert_called_once_with()
    entry_point.resolve.assert_called_once_with()


def test_load_plugin_only_calls_require_when_verifying_requirements():
    """Verify we do not call require when verify_requirements is False."""
    entry_point = mock.Mock(spec=['require', 'resolve', 'load'])
    plugin = manager.Plugin('T000', entry_point)

    plugin.load_plugin()
    assert entry_point.load.called is False
    assert entry_point.require.called is False
    entry_point.resolve.assert_called_once_with()


def test_load_plugin_catches_and_reraises_exceptions():
    """Verify we raise our own FailedToLoadPlugin."""
    entry_point = mock.Mock(spec=['require', 'resolve'])
    entry_point.resolve.side_effect = ValueError('Test failure')
    plugin = manager.Plugin('T000', entry_point)

    with pytest.raises(exceptions.FailedToLoadPlugin):
        plugin.load_plugin()


def test_load_noncallable_plugin():
    """Verify that we do not load a non-callable plugin."""
    entry_point = mock.Mock(spec=['require', 'resolve', 'load'])
    entry_point.resolve.return_value = mock.NonCallableMock()
    plugin = manager.Plugin('T000', entry_point)

    with pytest.raises(exceptions.FailedToLoadPlugin):
        plugin.load_plugin()
    entry_point.resolve.assert_called_once_with()


def test_plugin_property_loads_plugin_on_first_use():
    """Verify that we load our plugin when we first try to use it."""
    entry_point = mock.Mock(spec=['require', 'resolve', 'load'])
    plugin = manager.Plugin('T000', entry_point)

    assert plugin.plugin is not None
    entry_point.resolve.assert_called_once_with()


def test_execute_calls_plugin_with_passed_arguments():
    """Verify that we pass arguments directly to the plugin."""
    entry_point = mock.Mock(spec=['require', 'resolve', 'load'])
    plugin_obj = mock.Mock()
    plugin = manager.Plugin('T000', entry_point)
    plugin._plugin = plugin_obj

    plugin.execute('arg1', 'arg2', kwarg1='value1', kwarg2='value2')
    plugin_obj.assert_called_once_with(
        'arg1', 'arg2', kwarg1='value1', kwarg2='value2'
    )

    # Extra assertions
    assert entry_point.load.called is False
    assert entry_point.require.called is False
    assert entry_point.resolve.called is False


def test_version_proxies_to_the_plugin():
    """Verify that we pass arguments directly to the plugin."""
    entry_point = mock.Mock(spec=['require', 'resolve', 'load'])
    plugin_obj = mock.Mock(spec_set=['version'])
    plugin_obj.version = 'a.b.c'
    plugin = manager.Plugin('T000', entry_point)
    plugin._plugin = plugin_obj

    assert plugin.version == 'a.b.c'


def test_register_options():
    """Verify we call add_options on the plugin only if it exists."""
    # Set up our mocks and Plugin object
    entry_point = mock.Mock(spec=['require', 'resolve', 'load'])
    plugin_obj = mock.Mock(spec_set=['name', 'version', 'add_options',
                                     'parse_options'])
    option_manager = mock.Mock(spec=['register_plugin'])
    plugin = manager.Plugin('T000', entry_point)
    plugin._plugin = plugin_obj

    # Call the method we're testing.
    plugin.register_options(option_manager)

    # Assert that we call add_options
    plugin_obj.add_options.assert_called_once_with(option_manager)


def test_register_options_checks_plugin_for_method():
    """Verify we call add_options on the plugin only if it exists."""
    # Set up our mocks and Plugin object
    entry_point = mock.Mock(spec=['require', 'resolve', 'load'])
    plugin_obj = mock.Mock(spec_set=['name', 'version', 'parse_options'])
    option_manager = mock.Mock(spec=['register_plugin'])
    plugin = manager.Plugin('T000', entry_point)
    plugin._plugin = plugin_obj

    # Call the method we're testing.
    plugin.register_options(option_manager)

    # Assert that we register the plugin
    assert option_manager.register_plugin.called is False


def test_provide_options():
    """Verify we call add_options on the plugin only if it exists."""
    # Set up our mocks and Plugin object
    entry_point = mock.Mock(spec=['require', 'resolve', 'load'])
    plugin_obj = mock.Mock(spec_set=['name', 'version', 'add_options',
                                     'parse_options'])
    option_values = optparse.Values({'enable_extensions': []})
    option_manager = mock.Mock()
    plugin = manager.Plugin('T000', entry_point)
    plugin._plugin = plugin_obj

    # Call the method we're testing.
    plugin.provide_options(option_manager, option_values, None)

    # Assert that we call add_options
    plugin_obj.parse_options.assert_called_once_with(
        option_manager, option_values, None
    )
