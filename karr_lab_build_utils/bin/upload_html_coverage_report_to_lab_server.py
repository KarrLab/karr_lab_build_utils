#!/usr/bin/env python

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from karr_lab_build_utils.core import BuildHelper
import argparse


def main():
    """ Command line program to upload HTML coverage report to lab server """

    parser = argparse.ArgumentParser(description='Upload HTML coverage report to lab server')
    args = parser.parse_args()

    buildHelper = BuildHelper()
    buildHelper.upload_html_coverage_report_to_lab_server()

if __name__ == "__main__":
    main()
