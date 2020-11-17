# stdlib

# 3rd party
import pytest
from click.testing import CliRunner, Result
from domdf_python_tools.paths import PathPlus, in_directory
from domdf_python_tools.utils import strtobool
from dulwich.repo import Repo

# this package
from pytest_regressions.file_regression import FileRegressionFixture

from repo_helper_devenv import __version__, devenv


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
		result: Result = runner.invoke(devenv, catch_exceptions=False)
		assert result.exit_code == 0
		assert result.stdout == 'Successfully created development virtualenv.\n'

	# Check list of packages in virtualenv
	venv_dir = repo_path / "venv"

	for version_dir in (venv_dir / "lib").glob('*'):
		print(version_dir)

		for package in lib_requirements:
			assert (version_dir / "site-packages" / package).is_dir()

		for package in test_requirements:
			assert (version_dir / "site-packages" / package).is_dir()

	pyvenv_config = dict(line.split(" = ") for line in (venv_dir / "pyvenv.cfg").read_lines() if line)

	assert "prompt" in pyvenv_config
	assert pyvenv_config["prompt"] == "(repo_helper_demo) "

	assert "repo_helper_devenv" in pyvenv_config
	assert pyvenv_config["repo_helper_devenv"] == __version__

	assert "virtualenv" in pyvenv_config

	assert "include-system-site-packages" in pyvenv_config
	assert not strtobool(pyvenv_config["include-system-site-packages"])


@pytest.mark.parametrize("tests", [True, False])
@pytest.mark.parametrize("extra_args", [
		pytest.param(("--verbose", ), id="verbose"),
		pytest.param(("--verbose", "--verbose"), id="very verbose"),
		pytest.param(("-v", ), id="verbose short"),
		pytest.param(("-v", "--verbose"), id="very verbose short"),
		pytest.param(("-vv", ), id="very verbose short short"),
		])
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
		with (repo_path / "repo_helper.yml").open("a") as fp:
			fp.write("enable_tests: false")

	with in_directory(temp_repo.path):
		runner = CliRunner()
		result: Result = runner.invoke(devenv, catch_exceptions=False, args=extra_args)
		assert result.exit_code == 0

	assert "Installing library requirements." in result.stdout
	assert "Successfully created development virtualenv." in result.stdout

	if tests:
		assert "Installing test requirements." in result.stdout


@pytest.mark.parametrize("extra_args", [
		pytest.param(("--version", ), id="version"),
		pytest.param(("--version", "--version"), id="version_version"),
		])
def test_version(tmp_pathplus, extra_args, file_regression: FileRegressionFixture):

	with in_directory(tmp_pathplus):
		runner = CliRunner()
		result: Result = runner.invoke(devenv, catch_exceptions=False, args=extra_args)
		assert result.exit_code == 0

	file_regression.check(result.stdout)
