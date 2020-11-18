import pathlib
import subprocess
import tempfile

import pytest

import zebr0


@pytest.fixture(scope="module")
def server():
    with zebr0.TestServer() as server:
        yield server


def run(command):
    sp = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding=zebr0.ENCODING)
    (stdout, stderr) = sp.communicate()

    assert sp.returncode == 0
    assert stderr == ""

    return stdout


def test_with_defaults(server):
    with tempfile.TemporaryDirectory() as tmp:
        file = pathlib.Path(tmp + "/zebr0.conf")

        assert run("./zebr0-setup --configuration-file {}".format(file)) == ""
        assert file.read_text(zebr0.ENCODING) == '{"url": "https://zebr0.mazerty.fr", "levels": []}'


def test_nominal(server):
    with tempfile.TemporaryDirectory() as tmp:
        server.data = {"lorem/ipsum/key": "value"}
        file = pathlib.Path(tmp + "/zebr0.conf")

        assert run("./zebr0-setup --url http://localhost:8000 --levels lorem ipsum --configuration-file {} --test key".format(file)) == "value"
        assert file.read_text(zebr0.ENCODING) == '{"url": "http://localhost:8000", "levels": ["lorem", "ipsum"]}'
