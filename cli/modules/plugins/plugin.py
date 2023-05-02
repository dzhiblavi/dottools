import abc

from modules.util.logger import logger


class _PluginRegistry:
    def __init__(self):
        self._name_to_clazz = {}

    def register(self, clazz):
        name = clazz.__name__

        assert name not in self._name_to_clazz, \
               f'Plugin with name {name} is already registered as {clazz}'

        assert name[0].isupper(), \
               f'Plugin name should start with uppercase letter: {name}'

        self._name_to_clazz[name] = clazz

    def create(self, config, name=None):
        logger().info(
            [
                'Resolving plugin...',
                'plugin_name\t= %s',
                'config\t= %s',
            ],
            name, config.to_dict(),
        )

        if name and name in self._name_to_clazz:
            clazz = self._name_to_clazz[name]
            logger().info('Plugin with name %s is registered as %s', name, clazz)
            return clazz(config)

        if config.istype(list):
            logger().info('Object considered to be a list of plugins')
            return ListOfPlugins(config)

        if config.istype(dict):
            logger().info('Object considered to be a dict of plugins')
            return DictOfPlugins(config)

        assert False, f'Failed to create plugin: name={name}, config={config}'


_global_plugin_registry = _PluginRegistry()


def registry():
    global _global_plugin_registry
    return _global_plugin_registry


class Plugin(abc.ABC):
    def __init__(self, config):
        self.config = config

    def build(self):
        pass

    def _get_all_plugins_impl(self, name_prefix):
        plugins_list = self.get_plugins_list()

        if plugins_list is None:
            return [(name_prefix, self)]

        concat = []
        for name, plug in plugins_list:
            concat.extend(plug._get_all_plugins_impl(f'{name_prefix}.{name}'))

        return concat

    def get_all_plugins_list(self):
        return self._get_all_plugins_impl('')

    def get_plugins_list(self):
        """
        Returns the list of immediate child plugins or None in case it is not a container of plugins
        """
        return None

    @abc.abstractmethod
    def difference(self):
        """
        Should return a list of strings representing difference
        of the self.config and the current state, i.e.

            D: [(str, D), ...]
        """
        pass

    @abc.abstractmethod
    def backup(self):
        """
        Should perform backup
        """
        pass

    @abc.abstractmethod
    def apply(self):
        """
        Applies configuration stored in self.config
        """
        pass

    @staticmethod
    def log_difference(difference):
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
    def any_difference(difference):
        for tag, diff in difference:
            if not diff:
                continue

            if isinstance(diff[0], str):
                return True
            else:
                if Plugin.any_difference(diff):
                    return True

        return False


class _PluginsContainer(Plugin):
    def __init__(self, config, plugins_list):
        super().__init__(config)
        self._plugins = plugins_list

    def build(self):
        for item in self._plugins:
            item.build()

    def get_plugins_list(self):
        return self._plugins

    def difference(self):
        return [
            (plugin_name, plugin_instance.difference())
            for plugin_name, plugin_instance in self._plugins
        ]

    def backup(self):
        return [
            (plugin_name, plugin_instance.backup())
            for plugin_name, plugin_instance in self._plugins
        ]

    def apply(self):
        return [
            (plugin_name, plugin_instance.apply())
            for plugin_name, plugin_instance in self._plugins
        ]


class ListOfPlugins(_PluginsContainer):
    """
    Container for a list of multiple plugins, i.e.:

    plugins:
      - plugin_a:
          # plugin config goes here
          key: value

      - plugin_b:
          key: value

    Should be a list where each item is a plugin instance itself
    """

    def __init__(self, config):
        plugins_list = []

        for item_cfg in config.astype(list):
            item = item_cfg.astype(dict)

            assert len(item.keys()) == 1, \
                   f'Illegal plugin specification: {item}'

            plugin_name = next(iter(item.keys()))

            plugins_list.append(
                (plugin_name, registry().create(item[plugin_name], plugin_name)),
            )

        super().__init__(config, plugins_list)


class DictOfPlugins(_PluginsContainer):
    """
    Container for a dict of multiple plugins, i.e.:

    plugins:
      plugin_a:
        # plugin config goes here
        key: value

      plugin_b:
        key: value

    Should be a dict where each item is a plugin_name: plugin_config itself
    """

    def __init__(self, config):
        plugins_list = []

        for plugin_name, plugin_config in config.astype(dict).items():
            plugins_list.append(
                (plugin_name, registry().create(plugin_config, plugin_name)),
            )

        super().__init__(config, plugins_list)
