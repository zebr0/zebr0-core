from __future__ import annotations

import argparse
import http.server
import json
import pathlib
import threading
from typing import List, Optional

import jinja2
import requests

ENCODING = "utf-8"

URL = "url"
LEVELS = "levels"

URL_DEFAULT = "https://zebr0.mazerty.fr"
LEVELS_DEFAULT = []
CONFIGURATION_FILE_DEFAULT = "/etc/zebr0.conf"


class Client:
    def __init__(self, url: str = "", levels: Optional[List[str]] = None, configuration_file: str = CONFIGURATION_FILE_DEFAULT) -> None:
        # first set default values
        self.url = URL_DEFAULT
        self.levels = LEVELS_DEFAULT

        # then override with the configuration file if present
        try:
            configuration_string = pathlib.Path(configuration_file).read_text(ENCODING)
            configuration = json.loads(configuration_string)

            self.url = configuration.get(URL, URL_DEFAULT)
            self.levels = configuration.get(LEVELS, LEVELS_DEFAULT)
        except OSError:
            pass  # configuration file not found, ignored

        # finally override with the parameters if present
        if url:
            self.url = url
        if levels:
            self.levels = levels

        # and set up templating
        self.jinja_environment = jinja2.Environment(keep_trailing_newline=True)
        self.jinja_environment.globals[URL] = self.url
        self.jinja_environment.globals[LEVELS] = self.levels
        self.jinja_environment.filters["get"] = self.get

    def get(self, key: str, default: str = "", render: bool = True, strip: bool = True) -> str:
        # let's do this with a nice recursive function :)
        def fetch(levels):
            full_url = "/".join([self.url] + levels + [key])
            response = requests.get(full_url)

            if response.ok:
                return response.text  # if the key is found, we return the value
            elif levels:
                return fetch(levels[:-1])  # if not, we try at the parent level
            else:
                return default  # if we're at the top level, the key just doesn't exist, we return the default value

        value = fetch(self.levels)  # let's try at the deepest level first

        value = self.jinja_environment.from_string(value).render() if render else value  # templating
        value = value.strip() if strip else value  # stripping

        return value

    def save_configuration(self, configuration_file: str = CONFIGURATION_FILE_DEFAULT) -> None:
        configuration = {URL: self.url, LEVELS: self.levels}
        configuration_string = json.dumps(configuration)
        pathlib.Path(configuration_file).write_text(configuration_string, ENCODING)


class TestServer:
    """
    Rudimentary key-value HTTP server, for development or testing purposes only.
    The keys and their values are stored in a dictionary, that can be defined either in the constructor or through the "data" attribute.

    Basic usage:

    >>> server = TestServer({"key": "value", ...})
    >>> server.start()
    >>> ...
    >>> server.stop()

    Or as a context manager, in which case the server will be started automatically, then stopped at the end of the "with" block:

    >>> with TestServer() as server:
    >>>    server.data = {"key": "value", ...}
    >>>    ...

    :param data: the keys and their values stored in a dictionary, defaults to an empty dictionary
    :param address: the address the server will be listening to, defaults to 127.0.0.1
    :param port: the port the server will be listening to, defaults to 8000
    """

    def __init__(self, data: dict = None, address: str = "127.0.0.1", port: int = 8000) -> None:
        self.data = data or {}

        class RequestHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(zelf):
                key = zelf.path[1:]  # the key is the request's path, minus the leading "/"
                value = self.data.get(key)

                if value:  # standard HTTP behavior
                    zelf.send_response(200)
                    zelf.end_headers()
                    zelf.wfile.write(str(value).encode(ENCODING))
                else:
                    zelf.send_response(404)
                    zelf.end_headers()

        self.server = http.server.ThreadingHTTPServer((address, port), RequestHandler)

    def start(self) -> None:
        """ Starts the server in a separate thread. """
        threading.Thread(target=self.server.serve_forever).start()

    def stop(self) -> None:
        """ Stops the server. """
        self.server.shutdown()
        self.server.server_close()

    def __enter__(self) -> TestServer:
        """ When used as a context manager, starts the server at the beginning of the "with" block. """
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """ When used as a context manager, stops the server at the end of the "with" block. """
        self.stop()


class ArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_argument("-u", "--url", default=URL_DEFAULT, help="")
        self.add_argument("-l", "--levels", nargs="*", default=LEVELS_DEFAULT, help="")
        self.add_argument("-c", "--configuration-file", default=CONFIGURATION_FILE_DEFAULT, help="")
