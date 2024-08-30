import os
from functools import partial

import yaml

from dots.util.logger import logger
from dots.yaml.enrich import enrich_obj


def _env_tag_handler(_, node):
    return os.environ.get(node.value) or ""


def _eval_tag_handler(_, node, eval_locals):
    try:
        return eval(node.value, {}, eval_locals)  # pylint: disable=eval-used
    except Exception as error:
        logger().error(
            [
                "Failed to evaluate !eval tag",
                "value\t= %s",
                "error\t= %s",
                "local\t= %s",
            ],
            node.value,
            error,
            str(locals),
        )
        raise


def add_yaml_constructor(tag, handler):
    yaml.SafeLoader.add_constructor(tag, handler)


def add_common_yaml_constructors(include_base_dir, eval_locals):
    from yamlinclude import YamlIncludeConstructor

    YamlIncludeConstructor.add_to_loader_class(
        loader_class=yaml.SafeLoader,
        base_dir=include_base_dir,
    )
    add_yaml_constructor("!env", _env_tag_handler)
    add_yaml_constructor("!eval", partial(_eval_tag_handler, eval_locals=eval_locals))


def load_rich_yaml_from(path: str):
    with open(path, "r", encoding="utf-8") as file:
        return enrich_obj(yaml.safe_load(file))
