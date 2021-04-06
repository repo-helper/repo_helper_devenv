#!/usr/bin/env python3
#
#  __init__.py
"""
Create virtual environments with ``repo-helper``.

.. TODO:: Install extras
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
#  Parts based on virtualenv
#  https://github.com/pypa/virtualenv/blob/main/LICENSE
#  Copyright 2020 The virtualenv developers
#  MIT Licensed
#

# stdlib
import os
from typing import Dict

# 3rd party
import click
import shippinglabel
import virtualenv  # type: ignore
from click import ClickException
from deprecation_alias import deprecated
from domdf_python_tools.paths import PathPlus
from domdf_python_tools.typing import PathLike
from repo_helper.core import RepoHelper
from virtualenv.run import session_via_cli  # type: ignore
from virtualenv.run.session import Session  # type: ignore
from virtualenv.seed.wheels import pip_wheel_env_run  # type: ignore

__author__: str = "Dominic Davis-Foster"
__copyright__: str = "2020-2021 Dominic Davis-Foster"
__license__: str = "MIT License"
__version__: str = "0.4.0"
__email__: str = "dominic@davis-foster.co.uk"

__all__ = ["mkdevenv", "read_pyvenv", "install_requirements"]

virtualenv_version = tuple(map(int, virtualenv.__version__.split('.')))

if virtualenv_version >= (20, 4):
	_pip_wheel_env_run = pip_wheel_env_run

	def pip_wheel_env_run(search_dirs, app_data):
		return _pip_wheel_env_run(search_dirs, app_data, os.environ)


def mkdevenv(
		repo_dir: PathLike,
		venv_dir: PathLike = "venv",
		verbosity: int = 1,
		*,
		upgrade: bool = False,
		) -> int:
	"""
	Create a "devenv".

	.. versionadded:: 0.3.2

	:param repo_dir: The root of the repository to create the devenv for.
	:param venv_dir: The directory to create the devenv in, relative to ``repo_dir``.
	:param verbosity: The verbosity of the function. ``0`` = quiet, ``2`` = very verbose.
	:param upgrade: Whether to upgrade all specified packages to the newest available version.

	:rtype:

	.. versionchanged:: 0.4.0  Added the ``upgrade`` keyword-only argument.
	"""

	rh = RepoHelper(repo_dir)
	rh.load_settings()

	venvdir = rh.target_repo / venv_dir

	args = [
			str(venvdir),
			"--prompt",
			f"({rh.templates.globals['modname']}) ",
			"--seeder",
			"pip",
			"--download",
			]

	if verbosity:
		args.append("--verbose")
	if verbosity >= 2:
		args.append("--verbose")

	of_session = session_via_cli(args)

	if not of_session.seeder.enabled:  # pragma: no cover
		return 1

	with of_session:
		of_session.run()

		if verbosity:
			click.echo("Installing library requirements.")

		install_requirements(
				of_session,
				rh.target_repo / "requirements.txt",
				verbosity=verbosity,
				upgrade=upgrade,
				)

		if verbosity:
			click.echo("Installing test requirements.")

		if rh.templates.globals["enable_tests"]:
			install_requirements(
					of_session,
					rh.target_repo / rh.templates.globals["tests_dir"] / "requirements.txt",
					verbosity=verbosity,
					upgrade=upgrade,
					)

	if verbosity:
		click.echo('')

	update_pyvenv(venvdir)

	return 0


def install_requirements(
		session: Session,
		requirements_file: PathLike,
		verbosity: int = 1,
		*,
		upgrade: bool = False,
		):
	"""
	Install requirements into a virtualenv.

	:param session:
	:param requirements_file:
	:param verbosity: The verbosity of the function. ``0`` = quiet, ``2`` = very verbose.
	:param upgrade: Whether to upgrade all specified packages to the newest available version.

	.. versionchanged:: 0.4.0  Added the ``upgrade`` keyword-only argument.
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

	if upgrade:
		cmd.append("--upgrade")

	try:
		session.seeder._execute(
				[str(x) for x in cmd],
				pip_wheel_env_run(session.seeder.extra_search_dir, session.seeder.app_data),
				)
	except RuntimeError:  # pragma: no cover
		raise ClickException(f"Could not install from {requirements_file}")


def update_pyvenv(venv_dir: PathLike) -> None:
	venv_dir = PathPlus(venv_dir)

	pyvenv_config: Dict[str, str] = read_pyvenv(venv_dir)
	pyvenv_config["repo_helper_devenv"] = __version__

	with (venv_dir / "pyvenv.cfg").open('w') as fp:
		for key, value in pyvenv_config.items():
			value = f" = " + str(value).replace('\n', '\n\t')
			fp.write(f"{key}{value}\n")


@deprecated(
		deprecated_in="0.4.0",
		removed_in="1.0.0",
		current_version=__version__,
		details="Use 'shippinglabel.read_pyvenv' instead.",
		)
def read_pyvenv(venv_dir: PathLike) -> Dict[str, str]:
	"""
	Reads the ``pyvenv.cfg`` for the given virtualenv, and returns a ``key: value`` mapping of its contents.

	.. versionadded:: 0.3.2

	:param venv_dir:
	"""

	return shippinglabel.read_pyvenv(venv_dir)
