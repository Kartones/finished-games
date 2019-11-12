import subprocess
import sys

SOURCE_FOLDER = "."


def test_isort_compliance() -> None:
    binary_location = subprocess.check_output("which isort",
                                              shell=True,
                                              stderr=sys.stderr).decode("ascii").replace("\n", "")
    print("")
    result = subprocess.call("{} -rc --atomic {}".format(binary_location, SOURCE_FOLDER),
                             shell=True,
                             stdout=sys.stdout,
                             stderr=sys.stderr)
    # isort only returns non-zero on fatal error
    assert result == 0
