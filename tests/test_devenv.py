# stdlib
import re
import sys
from typing import Dict

# 3rd party
import pytest
from consolekit.testing import CliRunner, Result
from domdf_python_tools.compat import PYPY
from domdf_python_tools.paths import PathPlus, in_directory
from domdf_python_tools.utils import strtobool
from dulwich.repo import Repo

# this package
from repo_helper_devenv import __version__, read_pyvenv
from repo_helper_devenv.cli import devenv


def test_devenv(temp_repo: Repo):
	lib_requirements = [
			"click",
			"flask",
			"werkzeug",
			"consolekit",
			"requests",
			"apeye",
			]

	test_requirements = [
			"pytest",
			"hypothesis",
			]

	repo_path = PathPlus(temp_repo.path)
	(repo_path / "requirements.txt").write_lines(lib_requirements)

	(repo_path / "tests").mkdir()
	(repo_path / "tests/requirements.txt").write_lines(test_requirements)

	with in_directory(temp_repo.path):
		runner = CliRunner()
		result: Result = runner.invoke(devenv)
		assert result.exit_code == 0
		assert result.stdout == 'Successfully created development virtualenv.\n'

	# Check list of packages in virtualenv
	venv_dir = repo_path / "venv"

	if sys.platform == "win32":
		version_dirs = [(venv_dir / "Lib")]
	elif PYPY:
		version_dirs = [venv_dir]
	else:
		version_dirs = list((venv_dir / "lib").glob("py*"))

	for version_dir in version_dirs:

		for package in lib_requirements:
			assert (version_dir / "site-packages" / package).is_dir()

		for package in test_requirements:
			assert (version_dir / "site-packages" / package).is_dir()

	assert len(version_dirs) == 1

	pyvenv_config: Dict[str, str] = read_pyvenv(venv_dir)

	assert "prompt" in pyvenv_config
	assert pyvenv_config["prompt"] == "(repo_helper_demo) "

	assert "repo_helper_devenv" in pyvenv_config
	assert pyvenv_config["repo_helper_devenv"] == __version__

	assert "virtualenv" in pyvenv_config

	assert "include-system-site-packages" in pyvenv_config
	assert not strtobool(pyvenv_config["include-system-site-packages"])


# TODO: pytest.param(("--upgrade",), id="upgrade"),
#       pytest.param(("-U",), id="upgrade short"),


@pytest.mark.parametrize("tests", [True, False])
@pytest.mark.parametrize(
		"extra_args",
		[
				pytest.param(("--verbose", ), id="verbose"),
				pytest.param(("--verbose", "--verbose"), id="very verbose"),
				pytest.param(("-v", ), id="verbose short"),
				pytest.param(("-v", "--verbose"), id="very verbose short"),
				pytest.param(("-vv", ), id="very verbose short short"),
				pytest.param(("--verbose", "--upgrade"), id="verbose upgrade"),
				pytest.param(("-vU", ), id="verbose short upgrade short"),
				]
		)
def test_devenv_verbose(temp_repo: Repo, extra_args, tests):
	lib_requirements = [
			"click",
			"flask",
			"werkzeug",
			"consolekit",
			"requests",
			"apeye",
			]

	test_requirements = [
			"pytest",
			"hypothesis",
			]

	repo_path = PathPlus(temp_repo.path)
	(repo_path / "requirements.txt").write_lines(lib_requirements)

	if tests:
		(repo_path / "tests").mkdir()
		(repo_path / "tests/requirements.txt").write_lines(test_requirements)
	else:
		with (repo_path / "repo_helper.yml").open('a') as fp:
			fp.write("enable_tests: false")

	with in_directory(temp_repo.path):
		runner = CliRunner()
		result: Result = runner.invoke(devenv, args=extra_args)
		assert result.exit_code == 0

	assert "Installing project requirements" in result.stdout
	assert "Successfully created development virtualenv." in result.stdout

	if tests:
		assert "Installing test requirements" in result.stdout


def test_version(tmp_pathplus):

	with in_directory(tmp_pathplus):
		runner = CliRunner()
		result: Result = runner.invoke(devenv, args=["--version"])
		assert result.exit_code == 0

	assert result.stdout == f"repo_helper_devenv version {__version__}\n"


def test_version_version(tmp_pathplus):

	with in_directory(tmp_pathplus):
		runner = CliRunner()
		result: Result = runner.invoke(devenv, args=["--version", "--version"])
		assert result.exit_code == 0

	assert re.match(
			rf"repo_helper_devenv version {re.escape(__version__)}, virualenv \d+\.\d+\.\d+, repo_helper \d+\.\d+\.\d+\n",
			result.stdout,
			)
