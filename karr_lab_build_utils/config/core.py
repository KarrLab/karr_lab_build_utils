""" Configuration

:Author: Jonathan Karr <jonrkarr@gmail.com>
:Date: 2018-03-01
:Copyright: 2018, Karr Lab
:License: MIT
"""

import configobj
import os
import pkg_resources
import wc_utils.config.core


def get_config(extra=None):
    """ Get configuration

    Args:
        extra (:obj:`dict`, optional): additional configuration to override

    Returns:
        :obj:`configobj.ConfigObj`: nested dictionary with the configuration settings loaded from the configuration source(s).
    """
    paths = wc_utils.config.core.ConfigPaths(
        default=pkg_resources.resource_filename('karr_lab_build_utils', 'config/core.default.cfg'),
        schema=pkg_resources.resource_filename('karr_lab_build_utils', 'config/core.schema.cfg'),
        user=(
            'karr_lab_build_utils.cfg',
            os.path.expanduser('~/.wc/karr_lab_build_utils.cfg'),
        ),
    )

    return wc_utils.config.core.ConfigManager(paths).get_config(extra=extra)
