import time
from pathlib import Path

import pytest

import zebr0


@pytest.fixture(scope="module")
def server():
    with zebr0.TestServer() as server:
        yield server


def test_default_url():
    client = zebr0.Client(configuration_file=Path(""))

    assert client.get("domain-name") == "zebr0.io"


def test_default_levels(server):
    server.data = {"knock-knock": "who's there?"}
    client = zebr0.Client("http://127.0.0.1:8000", configuration_file=Path(""))

    assert client.get("knock-knock") == "who's there?"


def test_deepest_level(server):
    server.data = {"lorem/ipsum/dolor": "sit amet"}
    client = zebr0.Client("http://127.0.0.1:8000", levels=["lorem", "ipsum"], configuration_file=Path(""))

    assert client.get("dolor") == "sit amet"


def test_intermediate_level(server):
    server.data = {"consectetur/elit": "sed do"}
    client = zebr0.Client("http://127.0.0.1:8000", levels=["consectetur", "adipiscing"], configuration_file=Path(""))

    assert client.get("elit") == "sed do"


def test_root_level(server):
    server.data = {"incididunt": "ut labore"}
    client = zebr0.Client("http://127.0.0.1:8000", levels=["eiusmod", "tempor"], configuration_file=Path(""))

    assert client.get("incididunt") == "ut labore"


def test_missing_key_and_default_value(server):
    server.data = {}
    client = zebr0.Client("http://127.0.0.1:8000", levels=["dolore", "magna"], configuration_file=Path(""))

    assert client.get("aliqua") == ""
    assert client.get("aliqua", default="default") == "default"


def test_strip(server):
    server.data = {"knock-knock": "\nwho's there?\n"}
    client = zebr0.Client("http://127.0.0.1:8000", configuration_file=Path(""))

    assert client.get("knock-knock", strip=False) == "\nwho's there?\n"
    assert client.get("knock-knock") == "who's there?"


def test_basic_render(server):
    server.data = {"template": "{{ url }} {{ levels[0] }} {{ levels[1] }}"}
    client = zebr0.Client("http://127.0.0.1:8000", levels=["lorem", "ipsum"], configuration_file=Path(""))

    assert client.get("template", template=False) == "{{ url }} {{ levels[0] }} {{ levels[1] }}"
    assert client.get("template") == "http://127.0.0.1:8000 lorem ipsum"


def test_recursive_render(server):
    server.data = {
        "answer": "42",
        "template": "the answer is {{ 'answer' | get }}"
    }
    client = zebr0.Client("http://127.0.0.1:8000", configuration_file=Path(""))

    assert client.get("template") == "the answer is 42"


def test_recursive_nested_render(server):
    server.data = {
        "what": "memes",
        "star_wars/what": "droids",
        "star_wars/punctuation_mark": ".",
        "star_wars/slang/punctuation_mark": ", duh!",
        "template": "these aren't the {{ 'what' | get }} you're looking for{{ 'punctuation_mark' | get }}"
    }
    client = zebr0.Client("http://127.0.0.1:8000", levels=["star_wars", "slang"], configuration_file=Path(""))

    assert client.get("template") == "these aren't the droids you're looking for, duh!"


def test_render_with_default(server):
    server.data = {"template": "{{ 'missing_key' | get('default') }}"}
    client = zebr0.Client("http://127.0.0.1:8000", configuration_file=Path(""))

    assert client.get("template") == "default"


def test_read_ok(tmp_path, server):
    file = tmp_path.joinpath("file")
    file.write_text("content")
    server.data = {"template": "{{ '" + str(file) + "' | read }}"}
    client = zebr0.Client("http://127.0.0.1:8000", configuration_file=Path(""))

    assert client.get("template") == "content"


def test_read_ko(tmp_path, server):
    server.data = {"template": "{{ '" + str(tmp_path.joinpath("unknown_file")) + "' | read }}"}
    client = zebr0.Client("http://127.0.0.1:8000", configuration_file=Path(""))

    assert client.get("template") == ""


def test_cache(server):
    server.access_logs = []  # resetting server logs from previous tests

    server.data = {"ping": "pong", "yin": "yang"}
    client = zebr0.Client("http://127.0.0.1:8000", cache=1, configuration_file=Path(""))  # cache of 1 second for the purposes of the test

    assert client.get("ping") == "pong"  # "pong" is now in cache for "/ping"
    time.sleep(0.5)
    assert client.get("yin") == "yang"  # "yang" is now in cache for "/yin"
    time.sleep(0.1)
    server.data = {"ping": "peng", "yin": "yeng"}  # new values, shouldn't be used until cache has expired
    time.sleep(0.3)
    assert client.get("ping") == "pong"  # using cache for "/ping"
    time.sleep(0.2)
    assert client.get("ping") == "peng"  # 1.1 second has passed, cache has expired for "/ping", now fetching the new value
    assert client.get("yin") == "yang"  # still using cache for "/yin"
    time.sleep(0.5)
    assert client.get("yin") == "yeng"  # cache also has expired for "/yin", now fetching the new value

    assert server.access_logs == ["/ping", "/yin", "/ping", "/yin"]


def test_configuration_file(server, tmp_path):
    configuration_file = tmp_path.joinpath("zebr0.conf")
    configuration_file.write_text('{"url": "http://127.0.0.1:8000", "levels": ["lorem", "ipsum"], "cache": 1}', zebr0.ENCODING)

    server.data = {"lorem/ipsum/dolor": "sit amet"}
    client = zebr0.Client(configuration_file=configuration_file)

    assert client.get("dolor") == "sit amet"


def test_save_configuration(tmp_path):
    client = zebr0.Client("http://127.0.0.1:8000", levels=["lorem", "ipsum"], cache=1, configuration_file=Path(""))

    configuration_file = tmp_path.joinpath("zebr0.conf")
    client.save_configuration(configuration_file)

    assert configuration_file.read_text(zebr0.ENCODING) == '{"url": "http://127.0.0.1:8000", "levels": ["lorem", "ipsum"], "cache": 1}'
