from typing import Any, Optional

from dots.config.config import Config


def _create_config_impl(obj: Any, parent: Optional[Config] = None) -> Config:
    if isinstance(obj, dict):
        config = Config(parent=parent)
        config.set_object(
            {
                key: _create_config_impl(value, parent=config)
                for key, value in obj.items()
            }
        )
        return config

    if isinstance(obj, list):
        config = Config(parent=parent)
        config.set_object([_create_config_impl(item, parent) for item in obj])
        return config

    return Config(obj, parent)


def create_config(obj: Any) -> Config:
    return _create_config_impl(obj)
