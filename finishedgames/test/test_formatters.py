import subprocess
import sys

SOURCE_FOLDER = "."


def test_isort_compliance() -> None:
    binary_location = subprocess.check_output("which isort",
                                              shell=True,
                                              stderr=sys.stderr).decode("ascii").replace("\n", "")
    print("")
    result = subprocess.check_output("{} -rc --atomic {}".format(binary_location, SOURCE_FOLDER),
                                     shell=True,
                                     stderr=sys.stderr).decode("utf-8")

    print(result)
    assert all([
        "Fixing " not in result,
        "ERROR: " not in result,
    ]), result
