import subprocess  # nosec
import sys

SOURCE_FOLDER = "."


"""
pytest-mypy exists, but needs more fiddling with config files than this test-based linting
"""


def test_mypy_compliance() -> None:
    binary_location = (
        subprocess.check_output("which mypy", shell=True, stderr=sys.stderr).decode("ascii").replace("\n", "")  # nosec
    )
    print("")
    result = subprocess.call(
        "{} --config-file ../mypy.ini {}".format(binary_location, SOURCE_FOLDER),
        shell=True,  # nosec
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    assert result == 0  # nosec
