#!/usr/bin/env python3
#
#  cli.py
"""
Create virtual environments with ``repo-helper``.
"""
#
#  Copyright © 2020-2021 Dominic Davis-Foster <dominic@davis-foster.co.uk>
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#  DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#  OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
#  OR OTHER DEALINGS IN THE SOFTWARE.
#

# stdlib
import sys

# 3rd party
import click
from consolekit.options import colour_option, flag_option, verbose_option, version_option
from consolekit.terminal_colours import ColourTrilean
from domdf_python_tools.typing import PathLike
from repo_helper.cli import cli_command

__all__ = ["devenv", "version_callback"]


def version_callback(ctx: click.Context, param: click.Option, value: int):  # noqa: D103
	if not value or ctx.resilient_parsing:
		return

	# 3rd party
	import repo_helper
	import virtualenv  # type: ignore
	from domdf_python_tools.stringlist import DelimitedList

	# this package
	import repo_helper_devenv

	parts = DelimitedList([f"repo_helper_devenv version {repo_helper_devenv.__version__}"])

	if value > 1:
		parts.extend([
				f"virualenv {virtualenv.__version__}",
				f"repo_helper {repo_helper.__version__}",
				])

	click.echo(f"{parts:, }", color=ctx.color)
	ctx.exit()


@verbose_option()
@colour_option()
@version_option(callback=version_callback)
@flag_option(
		"-U",
		"--upgrade",
		help="Upgrade all specified packages to the newest available version.",
		)
@click.argument(
		"dest",
		type=click.STRING,
		default="venv",
		)
@cli_command()
def devenv(
		dest: PathLike = "venv",
		verbose: int = 0,
		colour: ColourTrilean = None,
		upgrade: bool = False,
		):
	"""
	Create a virtualenv.
	"""

	# 3rd party
	from consolekit.terminal_colours import Fore, resolve_color_default
	from domdf_python_tools.paths import PathPlus

	# this package
	from repo_helper_devenv import mkdevenv

	ret = mkdevenv(PathPlus.cwd(), dest, verbose, upgrade=upgrade)

	if ret:
		sys.exit(ret)  # pragma: no cover
	else:
		click.echo(
				Fore.GREEN("Successfully created development virtualenv."),
				color=resolve_color_default(colour),
				)
