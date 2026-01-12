# stdlib
import sys
from typing import ContextManager

# 3rd party
import deprecation  # type: ignore[import-untyped]
import pytest
from domdf_python_tools.compat import PYPY, nullcontext
from domdf_python_tools.paths import PathPlus
from virtualenv import session_via_cli  # type: ignore[import-untyped]

# this package
import repo_helper_devenv
from repo_helper_devenv import install_requirements


@deprecation.fail_if_not_removed
def test_install_requirements(tmp_pathplus: PathPlus):
	args = [
			str(tmp_pathplus / "venv"),
			"--prompt",
			"(demo_venv) ",
			"--seeder",
			"pip",
			"--download",
			]

	of_session = session_via_cli(args)

	assert of_session.seeder.enabled

	with of_session:
		of_session.run()

	(tmp_pathplus / "requirements.txt").write_text("click")

	cm: ContextManager

	if repo_helper_devenv.__version__ == "0.4.0":
		cm = nullcontext()
	else:
		cm = pytest.warns(DeprecationWarning)

	with cm:
		install_requirements(of_session, tmp_pathplus / "requirements.txt")

	# Check list of packages in virtualenv
	venv_dir = tmp_pathplus / "venv"

	if sys.platform == "win32":
		version_dirs = [(venv_dir / "Lib")]
	elif PYPY:
		version_dirs = [venv_dir]
	else:
		version_dirs = list((venv_dir / "lib").glob("py*"))

	for version_dir in version_dirs:

		assert (version_dir / "site-packages" / "click").is_dir()
