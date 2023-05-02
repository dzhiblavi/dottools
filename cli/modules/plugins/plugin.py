import abc

from typing import Type, Dict, Tuple, List
from modules.config import Config
from modules.util import tools
from modules.util.logger import logger


class Plugin(abc.ABC):
    def __init__(self, config: Config) -> None:
        self.config = config

    def to_dict(self):
        """
        Returns object-like representation of the plugin
        instance (for debugging and informational purposes)
        """

        return {
            'type': type(self).__name__,
            'config': self.config.to_dict(),
        }

    def build(self):
        """
        Should return an object associated with the result
        ob building this plugin instance (maybe None)
        """

    def difference(self) -> List[Tuple[str, List[str]]]:
        """
        Should return a list of strings representing difference
        of the self.config and the current state, i.e.
        """
        return []

    def backup(self) -> None:
        """
        Should perform backup if needed
        """

    def apply(self) -> None:
        """
        Applies configuration stored in self.config
        """

    @staticmethod
    def log_difference(difference: List[Tuple[str, List[str]]]) -> None:
        for tag, diff in difference:
            with logger().indent(label=f'diff({tag})'):
                if not diff:
                    logger().info('No difference')
                    continue

                if isinstance(diff[0], str):
                    logger().diff(''.join(diff).replace('%', '%%'))
                else:
                    Plugin.log_difference(diff)

    @staticmethod
    def any_difference(difference: List[Tuple[str, List[str]]]) -> bool:
        for _, diff in difference:
            if not diff:
                continue

            if isinstance(diff[0], str):
                return True

            if Plugin.any_difference(diff):
                return True

        return False


class _PluginRegistry:
    def __init__(self) -> None:
        self._name_to_clazz: Dict[str, Type[Plugin]] = {}

    def register(self, clazz: Type[Plugin]) -> None:
        name: str = clazz.__name__

        assert name not in self._name_to_clazz, \
               f'Plugin with name {name} is already registered as {clazz}'

        assert name[0].isupper(), \
               f'Plugin name should start with uppercase letter: {name}'

        self._name_to_clazz[name] = clazz

    def _get_plugin_spec(self, config: Config) -> Tuple[str, Config]:
        if not config.istype(dict):
            return None, None

        as_dict = config.astype(dict)
        keys = as_dict.keys()

        if len(keys) != 1:
            return None, None

        plugin_name = next(iter(keys))
        plugin_config = as_dict[plugin_name]

        if plugin_name == 'Plugin':
            assert 'type' in plugin_config, \
                   f'"type" field not found in Plugin: config {plugin_config}'

            plugin_name = plugin_config.get('type').astype(str)
            plugin_config = plugin_config.get('config', {})

        if plugin_name not in self._name_to_clazz:
            return None, None

        return plugin_name, plugin_config

    def create_plugin(self, config: Config) -> Plugin:
        """
        Creates a registered plugin from configuration like

        PluginName:
            # plugin config goes here
            key: value
            ...

        or

        Plugin:
            type: PluginName
            config:
                # plugin config goes here
                key: value
                ...
        """

        plugin_name, plugin_config = self._get_plugin_spec(config)

        logger().info(
            [
                'Creating plugin...',
                'name=\t %s',
                'config:',
            ] + tools.safe_dump_yaml_lines(plugin_config.to_dict()),
            plugin_name,
        )

        assert plugin_name in self._name_to_clazz, f'Plugin with name {plugin_name} not found'
        return self._name_to_clazz[plugin_name](plugin_config)

    def create_all_plugins(self, config: Config):
        """
        Given any yaml-like object creates all plugins that it can find in it
        and returns dictionary with the same k/v except plugin specs are replaced
        with plugin instances themselves, i.e.:

        key:
            - PluginName:
                # plugin config
                ...

        transforms to

        key:
            - <instance of plugin PluginName>
        """

        name, _ = self._get_plugin_spec(config)
        if name is not None:
            return self.create_plugin(config)

        if config.istype(dict):
            return {
                key: self.create_all_plugins(value)
                for key, value in config.astype(dict).items()
            }

        if config.istype(list):
            return [
                self.create_all_plugins(item)
                for item in config.astype(list)
            ]

        return config


_global_plugin_registry = _PluginRegistry()


def registry():
    global _global_plugin_registry  # pylint: disable=global-variable-not-assigned
    return _global_plugin_registry
