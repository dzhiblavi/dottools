import abc

from dots.config.config import Config
from dots.util import tools
from dots.util.logger import logger, Tags


class Plugin(abc.ABC):
    def __init__(self, config: Config) -> None:
        self.config = config

    def to_dict(self):
        """
        Returns object-like representation of the plugin
        instance (for debugging and informational purposes)
        """

        common = {
            "type": type(self).__name__,
            "config": self.config.to_dict(),
        }
        common.update(self._to_dict_extra())
        return common

    def _to_dict_extra(self):
        """
        Returns a dictionary with extra information on
        this plugin instance (variables etc)
        """
        return {}

    def build(self):
        """
        Should return an object associated with the result
        ob building this plugin instance (maybe None)
        """

    def difference(self):
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
    def log_difference(difference) -> None:
        for tag, diff in difference:
            with logger().indent(label=f"diff({tag})"):
                if not diff:
                    logger().info("No difference")
                    continue

                if isinstance(diff[0], str):
                    logger().log(
                        Tags.DIFF,
                        "".join(diff).replace("%", "%%"),
                    )
                else:
                    Plugin.log_difference(diff)

    @staticmethod
    def any_difference(difference) -> bool:
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
        self._name_to_clazz = {}

    def register(self, clazz) -> None:
        name: str = clazz.__name__

        assert name[
            0
        ].isupper(), f"Plugin name should start with capital character found {name}"

        assert (
            name not in self._name_to_clazz
        ), f"Plugin with name {name} is already registered as {clazz}"

        assert name[
            0
        ].isupper(), f"Plugin name should start with uppercase letter: {name}"

        self._name_to_clazz[f"plug.{name}"] = clazz

    def _get_plugin_spec(self, config: Config, key: str):
        assert config.istype(dict), "TBD"
        as_dict = config.astype(dict)

        if key is None:
            keys = as_dict.keys()
            assert len(keys) == 1
            key = next(iter(keys))

        plugin_name = key
        plugin_config = as_dict[plugin_name]

        if plugin_name == "Plugin":
            assert (
                "type" in plugin_config
            ), f'"type" field not found in Plugin: config {plugin_config}'

            plugin_name = plugin_config.get("type").astype(str)
            plugin_config = plugin_config.get("config", {})

        assert plugin_name in self._name_to_clazz, "TBD"
        return plugin_name, plugin_config

    def create_plugin(self, config: Config, key: str = None) -> Plugin:
        """
        Creates a registered plugin from configuration like

        plug.PluginName:
            # plugin config goes here
            key: value
            ...

        or

        Plugin:
            type: plug.PluginName
            config:
                # plugin config goes here
                key: value
                ...
        """

        plugin_name, plugin_config = self._get_plugin_spec(config, key)

        logger().info(
            [
                "Creating plugin...",
                "name=\t %s",
                "config:",
            ]
            + tools.safe_dump_yaml_lines(plugin_config.to_dict()),
            plugin_name,
        )

        assert (
            plugin_name in self._name_to_clazz
        ), f"Plugin with name {plugin_name} not found"
        return self._name_to_clazz[plugin_name](plugin_config)

    def create_all_plugins(self, config: Config):
        """
        Given any yaml-like object creates all plugins that it can find in it
        and returns dictionary with the same k/v except plugin specs are replaced
        with plugin instances themselves, i.e.:

        key:
            - plug.PluginName:
                # plugin config
                ...

        transforms to

        key:
            - <instance of plugin PluginName>
        """

        if config.istype(dict):
            plugins = {}
            conf_dict = config.astype(dict)

            for key, value in conf_dict.items():
                if key == "Plugin" or key.startswith("plug."):
                    # A plugin
                    plugins[key] = self.create_plugin(config, key)
                else:
                    # Not a plugin, simply recurse
                    plugins[key] = self.create_all_plugins(value)

            return plugins

        if config.istype(list):
            return [self.create_all_plugins(item) for item in config.astype(list)]

        return config


_global_plugin_registry = _PluginRegistry()


def registry():
    global _global_plugin_registry  # pylint: disable=global-variable-not-assigned
    return _global_plugin_registry
