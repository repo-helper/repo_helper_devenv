#!/usr/bin/env python3
#
#  __init__.py
"""
Create virtual environments with repo-helper.
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
from typing import Dict, Optional

# 3rd party
import click
import repo_helper
import virtualenv  # type: ignore
from click import ClickException, Context, Option
from consolekit.options import colour_option, verbose_option
from consolekit.terminal_colours import Fore, resolve_color_default
from domdf_python_tools.paths import PathPlus
from domdf_python_tools.stringlist import DelimitedList
from domdf_python_tools.typing import PathLike
from repo_helper.cli import cli_command
from repo_helper.core import RepoHelper
# from virtualenv.create.pyenv_cfg import PyEnvCfg
from virtualenv.run import session_via_cli  # type: ignore
from virtualenv.run.session import Session  # type: ignore
from virtualenv.seed.wheels import pip_wheel_env_run  # type: ignore

__author__: str = "Dominic Davis-Foster"
__copyright__: str = "2020 Dominic Davis-Foster"
__license__: str = "MIT License"
__version__: str = "0.2.0"
__email__: str = "dominic@davis-foster.co.uk"

__all__ = ["devenv", "read_pyvenv", "install_requirements"]


def version_callback(ctx: Context, param: Option, value: int):
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


@verbose_option()
@click.argument(
		"dest",
		type=click.STRING,
		default="venv",
		)
@click.option(
		"--version",
		count=True,
		expose_value=False,
		is_eager=True,
		help="Show the version and exit.",
		callback=version_callback,  # type: ignore
		)
@colour_option()
@cli_command()
def devenv(dest: str = "venv", verbose: int = 0, colour: Optional[bool] = None):
	"""
	Create a virtualenv.
	"""

	rh = RepoHelper(PathPlus.cwd())
	modname = rh.templates.globals["modname"]

	venvdir = rh.target_repo / dest
	args = [str(venvdir), "--prompt", f"({modname}) ", "--seeder", "pip", "--download"]
	if verbose:
		args.append("--verbose")
	if verbose >= 2:
		args.append("--verbose")

	of_session = session_via_cli(args)

	if not of_session.seeder.enabled:  # pragma: no cover
		sys.exit(1)

	with of_session:
		of_session.run()

		if verbose:
			click.echo("Installing library requirements.")

		install_requirements(of_session, rh.target_repo / "requirements.txt", verbosity=verbose)

		if verbose:
			click.echo("Installing test requirements.")

		if rh.templates.globals["enable_tests"]:
			install_requirements(
					of_session,
					rh.target_repo / rh.templates.globals["tests_dir"] / "requirements.txt",
					verbosity=verbose
					)

	if verbose:
		click.echo('')

	update_pyvenv(venvdir)

	click.echo(
			Fore.GREEN("Successfully created development virtualenv."),
			color=resolve_color_default(colour),
			)


def install_requirements(
		session: Session,
		requirements_file: PathLike,
		verbosity: int = 1,
		):
	"""
	Install requirements into a virtualenv.

	:param session:
	:param requirements_file:
	:param verbosity:
	"""

	cmd = [
			session.creator.exe,
			"-m",
			"pip",
			"install",
			"--disable-pip-version-check",
			"-r",
			requirements_file,
			]

	if verbosity < 1:
		cmd.append("--quiet")
	elif verbosity > 1:
		cmd.append("--verbose")

	try:
		session.seeder._execute(
				[str(x) for x in cmd],
				pip_wheel_env_run(session.seeder.extra_search_dir, session.seeder.app_data),
				)
	except RuntimeError:  # pragma: no cover
		raise ClickException(f"Could not install from {requirements_file}")


# def update_pyvenv(venv_dir: PathLike):
# 	# Fails for trailing whitespace - bug in virtualenv
# 	venv_dir = PathPlus(venv_dir)
#
# 	pyvenv_config = PyEnvCfg.from_folder(venv_dir)
# 	pyvenv_config["repo_helper_devenv"] = __version__
# 	pyvenv_config.write()


def update_pyvenv(venv_dir: PathLike) -> None:
	venv_dir = PathPlus(venv_dir)

	pyvenv_config: Dict[str, str] = read_pyvenv(venv_dir)
	pyvenv_config["repo_helper_devenv"] = __version__

	with (venv_dir / "pyvenv.cfg").open('w') as fp:
		for key, value in pyvenv_config.items():
			value = f" = " + str(value).replace('\n', '\n\t')
			fp.write(f"{key}{value}\n")


def read_pyvenv(venv_dir: PathLike) -> Dict[str, str]:
	"""
	Reads the ``pyvenv.cfg`` for the given virtualenv, and returns a ``key: value`` mapping of its contents.

	:param venv_dir:

	.. versionadded:: 0.2.0
	"""

	venv_dir = PathPlus(venv_dir)

	pyvenv_config: Dict[str, str] = {}

	for line in (venv_dir / "pyvenv.cfg").read_lines():
		if line:
			key, value, *_ = line.split(" = ")
			pyvenv_config[key] = value

	return pyvenv_config
