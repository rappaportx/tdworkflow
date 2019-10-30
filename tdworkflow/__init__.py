import logging

import pkg_resources

from tdworkflow import client, workflow

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

__version__ = pkg_resources.get_distribution(__name__).version