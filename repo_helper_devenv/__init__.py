#!/usr/bin/env python3
#
#  __init__.py
"""
Create virtualenvs with repo-helper.
"""
#
#  Copyright © 2020 Dominic Davis-Foster <dominic@davis-foster.co.uk>
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

#  Parts based on virtualenv
#  https://github.com/pypa/virtualenv/blob/main/LICENSE
#  Copyright 2020 The virtualenv developers
#  MIT Licensed
#

# stdlib
import sys

# 3rd party
import click
import repo_helper
import virtualenv
from domdf_python_tools.paths import PathPlus
from domdf_python_tools.stringlist import DelimitedList
from repo_helper.cli import cli_command
from repo_helper.core import RepoHelper
from virtualenv.run import build_parser
from virtualenv.run.session import Session
from virtualenv.seed.wheels import pip_wheel_env_run

__all__ = ["version_callback", "devenv"]

__author__: str = "Dominic Davis-Foster"
__copyright__: str = "2020 Dominic Davis-Foster"
__license__: str = "MIT License"
__version__: str = "0.0.0"
__email__: str = "dominic@davis-foster.co.uk"


def version_callback(ctx, param, value):
	if not value or ctx.resilient_parsing:
		return

	parts = DelimitedList([f"repo_helper_devenv version {__version__}"])

	if value > 1:
		parts.extend([
				f"virualenv {virtualenv.__version__}",
				f"repo_helper {repo_helper.__version__}",
				])

	click.echo(f"{parts:, }", color=ctx.color)
	ctx.exit()


@click.option(
		"--version",
		count=True,
		expose_value=False,
		is_eager=True,
		help="Show the version and exit.",
		callback=version_callback,
		)
@cli_command()
def devenv():
	"""
	Create a virtualenv.
	"""

	rh = RepoHelper(PathPlus.cwd())
	modname = rh.templates.globals["modname"]

	venvdir = rh.target_repo / "venv"
	args = (str(venvdir), "--prompt", f"({modname}) ", "--seeder", "pip", "--download")

	parser, elements = build_parser(args, None, True)
	options = parser.parse_args(args)

	creator, seeder, activators = tuple(e.create(options) for e in elements)  # create types
	of_session = Session(options.verbosity, options.app_data, parser._interpreter, creator, seeder, activators)

	if not seeder.enabled:
		sys.exit(1)

	# Install requirements
	cmd = [
			creator.exe,
			"-m",
			"pip",
			"install",
			"--disable-pip-version-check",
			"-r",
			rh.target_repo / "requirements.txt",
			]

	if rh.templates.globals["enable_tests"]:
		cmd.extend([
				"-r",
				rh.target_repo / rh.templates.globals["tests_dir"] / "requirements.txt",
				])

	seeder._execute(
			[str(x) for x in cmd],
			pip_wheel_env_run(seeder.extra_search_dir, seeder.app_data),
			)

	with of_session:
		of_session.run()

	click.echo("Successfully created development virtualenv.")
