import subprocess
import sys

SOURCE_FOLDER = "."


"""
Both pytest-mypy and pytest-flake8 exist, but need more fiddling with config files than this test-based linting
"""


def test_flake8_compliance() -> None:
    binary_location = (
        subprocess.check_output("which flake8", shell=True, stderr=sys.stderr).decode("ascii").replace("\n", "")
    )
    print("")
    result = subprocess.call(
        "{} {}".format(binary_location, SOURCE_FOLDER), shell=True, stdout=sys.stdout, stderr=sys.stderr
    )
    assert result == 0


def test_mypy_compliance() -> None:
    binary_location = (
        subprocess.check_output("which mypy", shell=True, stderr=sys.stderr).decode("ascii").replace("\n", "")
    )
    print("")
    result = subprocess.call(
        "{} --config-file ../mypy.ini {}".format(binary_location, SOURCE_FOLDER),
        shell=True,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    assert result == 0
