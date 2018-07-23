import configparser
import logging

import requests

# default name and location of the zebr0 configuration file, common to most zebr0 programs
DEFAULT_FILENAME = "zebr0.ini"
DEFAULT_PATH = "/etc/" + DEFAULT_FILENAME

# reads the content of the configuration file
_parser = configparser.ConfigParser()
_parser.read([DEFAULT_PATH, DEFAULT_FILENAME])  # you can override the values with a file with the same name in the current directory

# keys to look for in the configuration file, with the default value if absent or if the configuration file doesn't exist
base_url = _parser.get("config", "base_url", fallback="https://raw.githubusercontent.com/zebr0/zebr0-config/master")


class Config:
    """
    Configuration service.

    Instanciate to look for keys in the remote repository, relative to the specified project and stage if present.
    """

    def __init__(self, project, stage):
        self.project = project
        self.stage = stage

        # sets up a basic value cache, to avoid downloading the same value twice
        self._cache = {}

        # initializes the logger
        self._logger = logging.getLogger(__name__)
        self._logger.info("base_url: %s", base_url)
        self._logger.info("project: %s", project)
        self._logger.info("stage: %s", stage)

    def lookup(self, key):
        """
        Looks for the value of the given key in the remote repository.
        The value is then stored in a local cache to speed up subsequent calls.

        :param key: key to look for
        :return: value of the given key in the remote repository
        """

        if not self._cache.get(key):
            # if the key isn't cached, looks for it in the remote repository, then stores it
            self._cache[key] = self._remote_lookup(key)

        return self._cache.get(key)

    def _remote_lookup(self, key):
        self._logger.info("looking for key '%s' in remote repository", key)

        # first it will look for the key at the most specific level: base_url/project/stage
        # if it fails, it will try less specific urls until the key is found
        for path in [[base_url, self.project, self.stage, key],
                     [base_url, self.project, key],
                     [base_url, key]]:
            response = requests.get("/".join(path))
            if response.ok:
                return response.text.strip()

        # if not, raises an error
        raise LookupError("key '{}' not found anywhere for project '{}', stage '{}' in '{}'".format(key, self.project, self.stage, base_url))
