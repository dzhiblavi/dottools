import os
import yaml

from functools import partial

from dots.util.logger import logger


def _env_tag_handler(_, node):
    return os.environ.get(node.value) or ""


def _eval_tag_handler(_, node, locals):
    try:
        return eval(node.value, {}, locals)  # pylint: disable=eval-used
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


def load_yaml_constructor(tag, handler):
    yaml.SafeLoader.add_constructor(tag, handler)


def load_common_yaml_constructors(include_base_dir, eval_locals):
    from yamlinclude import YamlIncludeConstructor

    YamlIncludeConstructor.add_to_loader_class(
        loader_class=yaml.SafeLoader,
        base_dir=include_base_dir,
    )
    load_yaml_constructor("!env", _env_tag_handler)
    load_yaml_constructor("!eval", partial(_eval_tag_handler, locals=eval_locals))
