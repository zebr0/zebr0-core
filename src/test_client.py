import pathlib
import tempfile

import pytest

import zebr0


@pytest.fixture(scope="module")
def server():
    with zebr0.TestServer() as server:
        yield server


def test_default_url():
    client = zebr0.Client(configuration_file="")

    assert client.get("email") == "mazerty@gmail.com"


def test_default_levels(server):
    server.data = {"knock-knock": "who's there?"}
    client = zebr0.Client("http://127.0.0.1:8000", configuration_file="")

    assert client.get("knock-knock") == "who's there?"


def test_deepest_level(server):
    server.data = {"lorem/ipsum/dolor": "sit amet"}
    client = zebr0.Client("http://127.0.0.1:8000", levels=["lorem", "ipsum"], configuration_file="")

    assert client.get("dolor") == "sit amet"


def test_intermediate_level(server):
    server.data = {"consectetur/elit": "sed do"}
    client = zebr0.Client("http://127.0.0.1:8000", levels=["consectetur", "adipiscing"], configuration_file="")

    assert client.get("elit") == "sed do"


def test_root_level(server):
    server.data = {"incididunt": "ut labore"}
    client = zebr0.Client("http://127.0.0.1:8000", levels=["eiusmod", "tempor"], configuration_file="")

    assert client.get("incididunt") == "ut labore"


def test_missing_key_and_default_value(server):
    server.data = {}
    client = zebr0.Client("http://127.0.0.1:8000", levels=["dolore", "magna"], configuration_file="")

    assert client.get("aliqua") == ""
    assert client.get("aliqua", default="default") == "default"


def test_strip(server):
    server.data = {"knock-knock": "\nwho's there?\n"}
    client = zebr0.Client("http://127.0.0.1:8000", configuration_file="")

    assert client.get("knock-knock", strip=False) == "\nwho's there?\n"
    assert client.get("knock-knock") == "who's there?"


def test_basic_render(server):
    server.data = {"template": "{{ url }} {{ levels[0] }} {{ levels[1] }}"}
    client = zebr0.Client("http://127.0.0.1:8000", levels=["lorem", "ipsum"], configuration_file="")

    assert client.get("template", render=False) == "{{ url }} {{ levels[0] }} {{ levels[1] }}"
    assert client.get("template") == "http://127.0.0.1:8000 lorem ipsum"


def test_recursive_render(server):
    server.data = {
        "answer": "42",
        "template": "the answer is {{ 'answer' | get }}"
    }
    client = zebr0.Client("http://127.0.0.1:8000", configuration_file="")

    assert client.get("template") == "the answer is 42"


def test_recursive_nested_render(server):
    server.data = {
        "what": "memes",
        "star_wars/what": "droids",
        "star_wars/punctuation_mark": ".",
        "star_wars/slang/punctuation_mark": ", duh!",
        "template": "these aren't the {{ 'what' | get }} you're looking for{{ 'punctuation_mark' | get }}"
    }
    client = zebr0.Client("http://127.0.0.1:8000", levels=["star_wars", "slang"], configuration_file="")

    assert client.get("template") == "these aren't the droids you're looking for, duh!"


def test_render_with_default(server):
    server.data = {"template": "{{ 'missing_key' | get('default') }}"}
    client = zebr0.Client("http://127.0.0.1:8000", configuration_file="")

    assert client.get("template") == "default"


def test_configuration_file(server):
    with tempfile.TemporaryDirectory() as tmp:
        configuration_file = tmp + "/zebr0.conf"
        pathlib.Path(configuration_file).write_text('{"url": "http://127.0.0.1:8000", "levels": ["lorem", "ipsum"]}', zebr0.ENCODING)

        server.data = {"lorem/ipsum/dolor": "sit amet"}
        client = zebr0.Client(configuration_file=configuration_file)

        assert client.get("dolor") == "sit amet"


def test_save_configuration():
    with tempfile.TemporaryDirectory() as tmp:
        client = zebr0.Client("http://127.0.0.1:8000", levels=["lorem", "ipsum"], configuration_file="")

        configuration_file = tmp + "/zebr0.conf"
        client.save_configuration(configuration_file)

        assert pathlib.Path(configuration_file).read_text(zebr0.ENCODING) == '{"url": "http://127.0.0.1:8000", "levels": ["lorem", "ipsum"]}'
