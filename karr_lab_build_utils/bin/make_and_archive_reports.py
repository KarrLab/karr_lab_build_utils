
#!/usr/bin/env python

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from karr_lab_build_utils.core import BuildHelper
import argparse


def main():
    """ Make and archive reports;
    * Generate HTML test history reports
    * Generate HTML coverage reports
    * Generate HTML API documentation
    * Archive coverage reports to Coveralls
    """

    parser = argparse.ArgumentParser(description='Make and archive reports')
    args = parser.parse_args()

    buildHelper = BuildHelper()
    buildHelper.make_and_archive_reports()

if __name__ == "__main__":
    main()
