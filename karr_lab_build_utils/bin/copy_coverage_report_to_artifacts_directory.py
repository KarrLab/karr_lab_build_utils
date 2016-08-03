#!/usr/bin/env python

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from karr_lab_build_utils.core import BuildHelper
import argparse


def main():
    """ Command line program to copy coverage report to CircleCI artifacts directory """

    parser = argparse.ArgumentParser(description='Copy coverage report to CircleCI artifacts directory')
    args = parser.parse_args()

    buildHelper = BuildHelper()
    buildHelper.copy_coverage_report_to_artifacts_directory()

if __name__ == "__main__":
    main()
