import argparse
import hashlib
import json
import logging
import os.path
import subprocess
import sys

import jinja2
import requests


class ArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_argument("-c", "--conf", default="/etc/zebr0", help="local zebr0 settings directory (default: /etc/zebr0)")
        self.add_argument("-u", "--url", help="url to the remote zebr0 configuration (root level)")
        self.add_argument("-p", "--project", help="project name (first level)")
        self.add_argument("-s", "--stage", help="stage name (second level)")
        self.add_argument("--debug", action="store_true", help="debug level for logs")

        self._logger = logging.getLogger(__name__ + "." + __class__.__name__)

    def parse_args(self, *args, **kwargs):
        args = super().parse_args(*args, **kwargs)

        # logs will be written to stderr (since most zebr0 command-line programs are pipes that read from stdin and write to stdout)
        stream_handler = logging.StreamHandler(sys.stderr)
        stream_handler.setFormatter(logging.Formatter("{asctime} | {levelname:<7.7} | {name:<25.25} | {message}", style="{"))
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG if args.debug else logging.INFO)
        root_logger.addHandler(stream_handler)

        missing_parameters = []

        for parameter in ["url", "project", "stage"]:
            if not getattr(args, parameter, ""):
                filename = os.path.join(args.conf, parameter)
                if os.path.isfile(filename):
                    with open(filename, "r") as file:
                        setattr(args, parameter, file.read().strip())
                else:
                    missing_parameters.append(parameter)
                    continue
            self._logger.info("%s: %s", parameter, getattr(args, parameter))

        if missing_parameters:
            raise Exception("missing parameters: {}".format(missing_parameters))

        return args


def sh(command):
    return subprocess.run(command, shell=True, stdout=subprocess.PIPE).stdout.decode("utf-8").strip()


def hash(string, algorithm="md5"):
    return hashlib.new(algorithm, string.encode("utf-8")).hexdigest()


class Service:
    def __init__(self, args):
        self.url = args.url
        self.project = args.project
        self.stage = args.stage

        # sets up jinja's template environment
        self.environment = jinja2.Environment(keep_trailing_newline=True)
        self.environment.globals["url"] = args.url
        self.environment.globals["project"] = args.project
        self.environment.globals["stage"] = args.stage
        self.environment.filters["json"] = json.loads
        self.environment.filters["lookup"] = self.lookup
        self.environment.filters["sh"] = sh
        self.environment.filters["hash"] = hash

        # sets up a basic value cache, to avoid downloading the same value twice
        self._cache = {}

        # initializes the logger
        self._logger = logging.getLogger(__name__ + "." + __class__.__name__)

    def lookup(self, key, default=None, render=True, strip=True):
        """
        Looks for the value of the given key in the remote repository.
        The value is then stored in a local cache to speed up subsequent calls.

        :param key: key to look for
        :param default: if specified, returns this value instead of raising an error if the key isn't found
        :param render: whether to render through jinja2 the content of the value or not
        :param strip: whether to strip the value off leading and trailing whitespaces or not
        :return: value of the given key in the remote repository
        """

        if not self._cache.get(key):
            # if the key isn't cached, looks for it in the remote repository, then stores it
            self._cache[key] = self._remote_lookup(key, default, render, strip)

        return self._cache.get(key)

    def _remote_lookup(self, key, default, render, strip):
        self._logger.info("looking for key '%s' in remote repository", key)

        # first it will look for the key at the most specific level: url/project/stage
        # if it fails, it will try less specific urls until the key is found
        for path in [[self.url, self.project, self.stage, key],
                     [self.url, self.project, key],
                     [self.url, key]]:
            response = requests.get("/".join(path))
            if response.ok:
                value = response.text if not render else self.render(response.text)
                return value if not strip else value.strip()

        # if not, returns the default value is specified, else raises an error
        if default:
            return default
        else:
            raise LookupError("key '{}' not found anywhere for project '{}', stage '{}' in '{}'".format(key, self.project, self.stage, self.url))

    def render(self, template):
        """
        Renders the given template through jinja's configured environment

        :param template: template string
        :return: rendered template string
        """
        return self.environment.from_string(template).render()
