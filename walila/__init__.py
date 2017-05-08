# -*- coding: utf-8 -*-

"""
  Walila - Awesome toolkit for dobechina internal.
"""

import logging

logger = logging.getLogger(__name__)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(
    logging.Formatter("[Walila %(levelname)-7s] %(message)s")
)
logger.addHandler(console)
logger.setLevel(logging.INFO)


version_info = (1, 2, 2)
__version__ = ".".join([str(v) for v in version_info])
