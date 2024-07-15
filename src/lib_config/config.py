import os
import re

import yaml
from deepmerge.merger import Merger


def get_config() -> dict:
    merger: Merger = Merger(
        [
            (list, ["override"]),
            (dict, ["merge"]),
            (set, ["override"]),
        ],
        ["override"],
        ["override"],
    )
    config: dict = {}

    loader = yaml.SafeLoader
    # pattern for env vars: look for ${word}
    pattern = re.compile(r".*?\${(\w+)}.*?")
    # the tag will be used to mark where to start searching for the pattern
    # e.g. somekey: !ENV somestring${MYENVVAR}blah blah blah
    loader.add_implicit_resolver("!ENV", pattern, None)
    loader.add_constructor("!ENV", __create_env_var_constructor(pattern))

    # get current working directory
    cwd = os.getcwd()
    # get path to /configuration by iterating up the directory tree
    while not os.path.exists(os.path.join(cwd, "configuration")):
        cwd = os.path.dirname(cwd)
        if cwd == "/":
            raise Exception("Could not find /configuration")

    # load common parameters file
    common_config_filepath = os.path.join(cwd, "configuration", "parameters.yaml")
    print(f"loading common configuration at {common_config_filepath}")
    with open(common_config_filepath) as f:
        merger.merge(config, yaml.load(f, Loader=loader) or {})

    # load env parameters file and override common parameters
    env = os.environ.get("ENV", "")
    if env:
        config_filepath = os.path.join(cwd, "configuration", f"parameters.{env}.yaml")
        print(f"loading configuration for {env=} - {config_filepath}")
        with open(config_filepath) as f:
            merger.merge(config, yaml.load(f, Loader=loader) or {})

    return config


def __create_env_var_constructor(pattern):
    def constructor_env_variables(loader, node):
        """
        Extracts the environment variable from the node's value
        :param yaml.Loader loader: the yaml loader
        :param node: the current node in the yaml
        :return: the parsed string that contains the value of the environment
        variable
        """
        value = loader.construct_scalar(node)
        match = pattern.findall(value)  # to find all env variables in line
        if match:
            full_value = value
            for g in match:
                full_value = full_value.replace(f"${{{g}}}", os.environ.get(g, g))
            return full_value
        return value

    return constructor_env_variables
