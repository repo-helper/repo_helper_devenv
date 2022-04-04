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
import types
from typing import Dict

# 3rd party
import pyproject_devenv
import shippinglabel
import virtualenv  # type: ignore
from deprecation_alias import deprecated
from domdf_python_tools.paths import PathPlus
from domdf_python_tools.typing import PathLike
from pyproject_devenv.config import ConfigDict
from repo_helper.core import RepoHelper
from virtualenv.run.session import Session  # type: ignore

__author__: str = "Dominic Davis-Foster"
__copyright__: str = "2020-2021 Dominic Davis-Foster"
__license__: str = "MIT License"
__version__: str = "0.6.0"
__email__: str = "dominic@davis-foster.co.uk"

__all__ = ["mkdevenv", "read_pyvenv", "install_requirements"]

virtualenv_version = tuple(map(int, virtualenv.__version__.split('.')[:3]))


class _RepoHelperDevenv(pyproject_devenv._Devenv):

	def __init__(
			self,
			project_dir: PathLike,
			venv_dir: PathLike = "venv",
			*,
			verbosity: int = 1,
			upgrade: bool = False,
			):

		rh = RepoHelper(project_dir)
		rh.load_settings()

		self.project_dir = rh.target_repo

		self.config: ConfigDict = {
				"name": rh.templates.globals["modname"],
				"dependencies": [],
				"optional_dependencies": rh.templates.globals["extras_require"],
				"build_dependencies": None,
				}

		self.venv_dir = self.project_dir / venv_dir
		self.verbosity: int = int(verbosity)
		self.upgrade: bool = upgrade

		# TODO: config option
		self.extras_to_install = sorted(self.config["optional_dependencies"])

	def install_project_requirements(self, of_session):
		"""
		Install the project's requirements/dependencies.

		:param of_session:
		"""

		self.report_installing("project requirements")

		self.install_requirements(
				of_session,
				requirements_file=self.project_dir / "requirements.txt",
				)

	def update_pyvenv(self) -> None:
		"""
		Read and update the ``pyvenv.cfg`` file of the virtualenv.
		"""

		update_pyvenv(self.venv_dir)


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

	return _RepoHelperDevenv(repo_dir, venv_dir, verbosity=verbosity, upgrade=upgrade).create()


@deprecated(
		deprecated_in="0.5.0",
		removed_in="1.0.0",
		current_version=__version__,
		)
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

	namespace = types.SimpleNamespace()
	namespace.verbosity = int(verbosity)
	namespace.upgrade = upgrade

	_RepoHelperDevenv.install_requirements(
			namespace,  # type: ignore
			session,
			requirements_file=requirements_file,
			)


def update_pyvenv(venv_dir: PathLike) -> None:
	venv_dir = PathPlus(venv_dir)

	pyvenv_config: Dict[str, str] = shippinglabel.read_pyvenv(venv_dir)
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

	:rtype:
	"""

	return shippinglabel.read_pyvenv(venv_dir)
