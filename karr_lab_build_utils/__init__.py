import pkg_resources

from ._version import __version__
# :obj:`str`: version

# API
from .core import (CoverageType, Environment,
                   BuildHelper, BuildHelperError,
                   TestResults, TestCaseResult, TestCaseResultType)
