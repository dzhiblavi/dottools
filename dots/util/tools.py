from typing import Any, Optional
import yaml


def safe_dump_yaml(obj: Any, indent: int = 2) -> str:
    return yaml.dump(obj, indent=indent).replace("%", "%%")


def safe_dump_yaml_lines(obj: Any, indent: int = 2):
    return safe_dump_yaml(obj, indent).splitlines()


def find_instances_of_subclasses(
    obj: Any, base_class: type, prefix: Optional[str] = None
):
    """
    Finds all object of classes inherited of base_class
    and returns them in list paired with their paths in obj
    """

    if prefix is None:
        prefix = ""

    items = None

    if issubclass(type(obj), base_class):
        return [(prefix, obj)]

    if isinstance(obj, list):
        items = enumerate(obj)

    if isinstance(obj, dict):
        items = obj.items()

    if items is None:
        return []

    result = []
    for key, item in items:
        result.extend(find_instances_of_subclasses(item, base_class, f"{prefix}.{key}"))

    return result
