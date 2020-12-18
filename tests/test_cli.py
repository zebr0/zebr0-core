import pytest

import zebr0


@pytest.fixture(scope="module")
def server():
    with zebr0.TestServer() as server:
        yield server


def test_with_defaults(tmp_path, capsys):
    file = tmp_path.joinpath("zebr0.conf")

    zebr0.main(["--configuration-file", str(file)])
    assert capsys.readouterr().out == ""
    assert file.read_text(zebr0.ENCODING) == '{"url": "https://hub.zebr0.io", "levels": [], "cache": 300}'


def test_nominal(server, tmp_path, capsys):
    server.data = {"lorem/ipsum/key": "value"}
    file = tmp_path.joinpath("zebr0.conf")

    zebr0.main(["--url", "http://localhost:8000", "--levels", "lorem", "ipsum", "--cache", "1", "--configuration-file", str(file), "--test", "key"])
    assert capsys.readouterr().out == "value\n"
    assert file.read_text(zebr0.ENCODING) == '{"url": "http://localhost:8000", "levels": ["lorem", "ipsum"], "cache": 1}'
