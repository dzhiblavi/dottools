import os
import re

from dots.yaml import loader
from dots.config import builder
from dots.plugins import plugin

from dots.context import init_context, Context, context
from dots.util import tools
from dots.util.logger import StdErrLogger, Tags, TAGS_DEPENDENCIES, logger, init_logger


def _get_must_be_enabled_tags(command):
    must_be_enabled = [
        Tags.OUTPUT,
    ]

    if command in {"plan"}:
        must_be_enabled.append(Tags.ACTION)

    if command in {"diff"}:
        must_be_enabled.append(Tags.DIFF)

    return must_be_enabled


def _get_logging_tags(name_list, command):
    must_be_enabled = _get_must_be_enabled_tags(command)
    tag_list = [Tags[name.upper()] for name in name_list]

    for tag in must_be_enabled:
        if tag in tag_list:
            continue

        tag_list.append(tag)

    while True:
        changed = False

        for tag, deps_list in TAGS_DEPENDENCIES.items():
            if tag in tag_list:
                for dep in deps_list:
                    if dep in tag_list:
                        continue

                    tag_list.append(dep)
                    changed = True

        if not changed:
            return tag_list


def _setup_yaml_constructors(base_include_dir, eval_locals):
    def _context_rel_tag_handler(_, node):
        return context().rel(path=node.value)

    def _plugin_tag_handler(_, node):
        return f"plug.{node.value}"

    loader.add_common_yaml_constructors(base_include_dir, eval_locals)
    loader.add_yaml_constructor("!rel", _context_rel_tag_handler)
    loader.add_yaml_constructor("!plug", _plugin_tag_handler)


def _apply_command(plugin_instance, command):
    with logger().indent(label=f"{type(plugin_instance).__name__}.{command}"):
        if command == "compile":
            logger().log(
                Tags.OUTPUT,
                [""] + tools.safe_dump_yaml_lines(plugin_instance.to_dict()),
            )
        elif command == "diff":
            plugin.Plugin.log_difference(plugin_instance.difference())
        elif command in {"plan", "apply"}:
            if not plugin.Plugin.any_difference(plugin_instance.difference()):
                logger().info("No difference, nothing done")
            else:
                plugin_instance.apply()
        else:
            assert False, f"Invalid command {command}"


def run(
    dottools_root,
    config_file_path,
    field,
    command,
    color,
    log,
):
    config_path = os.path.realpath(config_file_path)

    init_logger(
        StdErrLogger(
            _get_logging_tags(log.split(","), command),
            color == "yes",
        )
    )

    init_context(
        Context(
            config_path=config_path,
            dottools_root=os.path.realpath(dottools_root),
            dry_run=command in {"config", "diff", "plan", "compile"},
        ),
    )

    _setup_yaml_constructors(
        base_include_dir=context().cfg_dir,
        eval_locals={
            "ctx": context(),
        },
    )

    yml = loader.load_rich_yaml_from(config_path)
    cfg = builder.create_config(yml)

    if command == "dump":
        print(tools.safe_dump_yaml(yml))
        return

    matcher = re.compile(field)
    plugins_object = plugin.registry().create_all_plugins(cfg)
    all_plugins = tools.find_instances_of_subclasses(
        plugins_object, base_class=plugin.Plugin
    )

    for name, plug in all_plugins:
        if not matcher.search(name):
            logger().info(
                [
                    "Skipping plugin since it does not match field",
                    "plugin\t= %s",
                    "regex\t= %s",
                ],
                name,
                field,
            )
            continue

        with logger().indent(label=name):
            plug.build()
            _apply_command(plug, command)
