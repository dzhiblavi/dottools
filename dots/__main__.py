#!/usr/bin/env python3

import os
import argparse

from dots.util import env
from dots.util.logger import Tags
from dots import dottools


def _parse_args():
    parser = argparse.ArgumentParser(
        description="Yet another yet another dotfiles management tool"
    )

    parser.add_argument(
        "--config-file",
        "-c",
        help="Configuration description (.yaml)",
        default=os.getenv(env.CONFIG_FILE_PATH_ENV_VAR),
    )
    parser.add_argument(
        "--root",
        help="dottols root directory",
        default=os.getenv(
            env.ROOT_PATH_ENV_VAR,
            default=os.path.dirname(os.path.dirname(__file__)),
        ),
    )
    parser.add_argument(
        "--log",
        "-l",
        help=f'Enabled logging tags, (comma sep.) ({",".join(tag.name.lower() for tag in Tags)})',
        default="error",
        type=str,
    )
    parser.add_argument(
        "--field",
        "-f",
        help="The object to be processed",
        default=".*",
    )
    parser.add_argument(
        "--color",
        help="Whether to display color in output",
        choices=["yes", "no"],
        default="yes",
    )

    subparsers = parser.add_subparsers(title="Commands", dest="command")
    subparsers.add_parser("config", help="Print compiled configuration")
    subparsers.add_parser("diff", help="Show difference")
    subparsers.add_parser("apply", help="Apply configuration")
    subparsers.add_parser("compile", help="Show available plugins' configuration")
    subparsers.add_parser(
        "plan", help="Print actions that will be done when apply is used"
    )

    return parser.parse_args()


def main(args):
    dottools.run(
        dottools_root=args.root,
        config_file_path=args.config_file,
        field=args.field,
        command=args.command or "config",
        color=args.color,
        log=args.log,
    )


def cli_entrypoint():
    main(_parse_args())


if __name__ == "__main__":
    cli_entrypoint()
