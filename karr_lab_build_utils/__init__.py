import pkg_resources

with open(pkg_resources.resource_filename('karr_lab_build_utils', 'VERSION'), 'r') as file:
    __version__ = file.read().strip()
# :obj:`str`: version

# API
from .core import (CoverageType, Environment,
                   BuildHelper, BuildHelperError,
                   TestResults, TestCaseResult, TestCaseResultType)
