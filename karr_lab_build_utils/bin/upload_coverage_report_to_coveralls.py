#!/usr/bin/env python

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from karr_lab_build_utils.core import BuildHelper
import argparse


def main():
    """ Command line program to upload coverage report to Coveralls """

    parser = argparse.ArgumentParser(description='Upload coverage report to Coveralls')
    args = parser.parse_args()

    buildHelper = BuildHelper()
    buildHelper.upload_coverage_report_to_coveralls()

if __name__ == "__main__":
    main()
