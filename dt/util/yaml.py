import os
import yaml
from dt.context import context


def env_tag(loader, node):
    return os.environ.get(node.value) or ''


def context_rel_tag(loader, node):
    return context().rel(path=node.value)


def context_dot_tag(loader, node):
    return context().rel(path=f'dots/{node.value}')


def plugin_tag(loader, node):
    return f'plug.{node.value}'


def load_all_yaml_constructors(base_dir):
    from yamlinclude import YamlIncludeConstructor
    YamlIncludeConstructor.add_to_loader_class(
        loader_class=yaml.SafeLoader,
        base_dir=base_dir,
    )

    yaml.SafeLoader.add_constructor('!env', env_tag)
    yaml.SafeLoader.add_constructor('!rel', context_rel_tag)
    yaml.SafeLoader.add_constructor('!dot', context_dot_tag)
    yaml.SafeLoader.add_constructor('!plug', plugin_tag)
