import argparse
import logging
import os.path
import sys

import requests


class ArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_argument("-c", "--conf", nargs="?", default="/etc/zebr0")
        self.add_argument("-u", "--url", nargs="?")
        self.add_argument("-p", "--project", nargs="?")
        self.add_argument("-s", "--stage", nargs="?")
        self.add_argument("--debug", action="store_true")

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


class Service:
    def __init__(self, args):
        self.url = args.url
        self.project = args.project
        self.stage = args.stage

        # sets up a basic value cache, to avoid downloading the same value twice
        self._cache = {}

        # initializes the logger
        self._logger = logging.getLogger(__name__ + "." + __class__.__name__)

    def lookup(self, key, strip=True):
        """
        Looks for the value of the given key in the remote repository.
        The value is then stored in a local cache to speed up subsequent calls.

        :param key: key to look for
        :param strip: whether to strip the value off leading and trailing whitespaces or not
        :return: value of the given key in the remote repository
        """

        if not self._cache.get(key):
            # if the key isn't cached, looks for it in the remote repository, then stores it
            self._cache[key] = self._remote_lookup(key, strip)

        return self._cache.get(key)

    def _remote_lookup(self, key, strip):
        self._logger.info("looking for key '%s' in remote repository", key)

        # first it will look for the key at the most specific level: url/project/stage
        # if it fails, it will try less specific urls until the key is found
        for path in [[self.url, self.project, self.stage, key],
                     [self.url, self.project, key],
                     [self.url, key]]:
            response = requests.get("/".join(path))
            if response.ok:
                return response.text.strip() if strip else response.text

        # if not, raises an error
        raise LookupError("key '{}' not found anywhere for project '{}', stage '{}' in '{}'".format(key, self.project, self.stage, self.url))
