import os
import yaml
from dt.context import context
from dt.util.logger import logger


def env_tag(loader, node):
    return os.environ.get(node.value) or ''


def context_rel_tag(loader, node):
    return context().rel(path=node.value)


def context_dot_tag(loader, node):
    return context().rel(path=f'dots/{node.value}')


def plugin_tag(loader, node):
    return f'plug.{node.value}'


def _eval(value, local):
    try:
        return eval(value, {}, local)  # pylint: disable=eval-used
    except Exception as error:
        logger().error(
            [
                'Failed to evaluate !eval tag',
                'value\t= %s',
                'error\t= %s',
                'local\t= %s'
            ],
            value, error, str(local),
        )
        raise


def eval_tag(eval_locals):
    def eval(_, node):
        return _eval(node.value, local=eval_locals)

    return eval


def load_all_yaml_constructors(include_base_dir, eval_locals):
    from yamlinclude import YamlIncludeConstructor
    YamlIncludeConstructor.add_to_loader_class(
        loader_class=yaml.SafeLoader,
        base_dir=include_base_dir,
    )

    tags = {
        '!env': env_tag,
        '!rel': context_rel_tag,
        '!dot': context_dot_tag,
        '!plug': plugin_tag,
        '!eval': eval_tag(eval_locals),
    }

    for tag_name, tag_action in tags.items():
        yaml.SafeLoader.add_constructor(tag_name, tag_action)
