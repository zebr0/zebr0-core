import argparse

import zebr0


def test_defaults():
    argparser = zebr0.build_argument_parser()
    args = argparser.parse_args([])
    assert args == argparse.Namespace(url=None, levels=None, cache=None, configuration_file="/etc/zebr0.conf")


def test_long_parameters():
    argparser = zebr0.build_argument_parser()
    args = argparser.parse_args(["--url", "http://localhost:8000", "--levels", "lorem", "ipsum", "--cache", "1", "--configuration-file", "/tmp/zebr0.conf"])
    assert args == argparse.Namespace(url="http://localhost:8000", levels=["lorem", "ipsum"], cache=1, configuration_file="/tmp/zebr0.conf")


def test_short_parameters():
    argparser = zebr0.build_argument_parser()
    args = argparser.parse_args(["-u", "http://localhost:8000", "-l", "lorem", "ipsum", "-c", "1", "-f", "/tmp/zebr0.conf"])
    assert args == argparse.Namespace(url="http://localhost:8000", levels=["lorem", "ipsum"], cache=1, configuration_file="/tmp/zebr0.conf")
