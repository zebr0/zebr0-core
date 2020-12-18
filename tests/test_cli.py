import subprocess

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


def test_with_defaults(tmp_path):
    file = tmp_path.joinpath("zebr0.conf")

    assert run(f"./zebr0-setup --configuration-file {file}") == ""
    assert file.read_text(zebr0.ENCODING) == '{"url": "https://hub.zebr0.io", "levels": [], "cache": 300}'


def test_nominal(server, tmp_path):
    server.data = {"lorem/ipsum/key": "value"}
    file = tmp_path.joinpath("zebr0.conf")

    assert run(f"./zebr0-setup --url http://localhost:8000 --levels lorem ipsum --cache 1 --configuration-file {file} --test key") == "value\n"
    assert file.read_text(zebr0.ENCODING) == '{"url": "http://localhost:8000", "levels": ["lorem", "ipsum"], "cache": 1}'
