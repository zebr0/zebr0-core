import argparse

import zebr0


def test_defaults():
    argparser = zebr0.ArgumentParser()
    args = argparser.parse_args([])
    assert args == argparse.Namespace(url="https://zebr0.mazerty.fr", levels=[], configuration_file="/etc/zebr0.conf")


def test_long_parameters():
    argparser = zebr0.ArgumentParser()
    args = argparser.parse_args(["--url", "http://localhost:8000", "--levels", "lorem", "ipsum", "--configuration-file", "/tmp/zebr0.conf"])
    assert args == argparse.Namespace(url="http://localhost:8000", levels=["lorem", "ipsum"], configuration_file="/tmp/zebr0.conf")


def test_short_parameters():
    argparser = zebr0.ArgumentParser()
    args = argparser.parse_args(["-u", "http://localhost:8000", "-l", "lorem", "ipsum", "-c", "/tmp/zebr0.conf"])
    assert args == argparse.Namespace(url="http://localhost:8000", levels=["lorem", "ipsum"], configuration_file="/tmp/zebr0.conf")
