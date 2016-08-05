#!/usr/bin/env python

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from karr_lab_build_utils.core import BuildHelper
import argparse


def main():
    """ Command line program to archive a coverage report:
    * Copy report to artifacts directory
    * Upload report to Coveralls
    """

    parser = argparse.ArgumentParser(description='Archive coverage report')
    args = parser.parse_args()

    buildHelper = BuildHelper()
    buildHelper.archive_coverage_report()

if __name__ == "__main__":
    main()