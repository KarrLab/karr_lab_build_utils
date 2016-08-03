#!/usr/bin/env python

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from karr_lab_build_utils.core import BuildHelper
import argparse


def main():
    """ Upload XML and HTML test reports to lab server """

    parser = argparse.ArgumentParser(description='Upload XML and HTML test reports to lab server')
    args = parser.parse_args()

    buildHelper = BuildHelper()
    buildHelper.upload_test_reports_to_lab_server()

if __name__ == "__main__":
    main()
