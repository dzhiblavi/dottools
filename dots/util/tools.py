import yaml
import subprocess
from typing import List, Any, Optional, Tuple


def has_gpu() -> bool:
    try:
        subprocess.check_call(
            args=["nvidia-smi"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=True,
        )
        return True

    except subprocess.SubprocessError:
        return False


def load_yaml_by_path(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def safe_dump_yaml_lines(obj: Any, indent: int = 2) -> List[str]:
    return yaml.dump(obj, indent=indent).replace("%", "%%").splitlines()


def find_instances_of_subclasses(
    obj: Any, base_class: type, prefix: Optional[str] = None
) -> List[Tuple[str, Any]]:
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
