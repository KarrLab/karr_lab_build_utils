#!/usr/bin/env python

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from karr_lab_build_utils.core import BuildHelper
import argparse


def main():
    """ Download XML test report history from lab server """

    parser = argparse.ArgumentParser(description='Download XML test report history from lab server')
    args = parser.parse_args()

    buildHelper = BuildHelper()
    buildHelper.download_nose_test_report_history_from_lab_server()

if __name__ == "__main__":
    main()
