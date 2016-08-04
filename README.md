[![PyPI package](https://img.shields.io/pypi/v/Karr-Lab-build-utils.svg)](https://pypi.python.org/pypi/Karr-Lab-build-utils)
[![Documentation](https://readthedocs.org/projects/karr-lab-build-utils/badge/?version=latest)](http://karr-lab-build-utils.readthedocs.org)
[![Test results](https://circleci.com/gh/KarrLab/Karr-Lab-build-utils.svg?style=shield)](https://circleci.com/gh/KarrLab/Karr-Lab-build-utils)
[![Test coverage](https://coveralls.io/repos/github/KarrLab/Karr-Lab-build-utils/badge.svg)](https://coveralls.io/github/KarrLab/Karr-Lab-build-utils)
[![License](https://img.shields.io/github/license/KarrLab/Karr-Lab-build-utils.svg)](LICENSE.txt)

# Karr Lab build utilities

This package performs several aspects of the Karr Lab's build system:
* Generates HTML test history report from a collection of nose-style XML reports
* Generates HTML test coverage report
* Generates HTML API documentation
* Uploads XML and HTML test reports to the lab server
* Uploads coverage report to Coveralls
* Uploads HTML coverage report to the lab server
* Uploads HTML API documentation to the lab server

## Installation
1. Install dependencies
  * libffi-dev
2. Install package 
  ```
  pip install Karr-Lab-build-utils
  ```

## Example usage

### Command line
```
export CIRCLE_PROJECT_REPONAME=Karr-Lab-build-utils
export CIRCLE_BUILD_NUM=1
export CODE_SERVER_PASSWORD=*******
karr-lab-build-utils-install-requirements
karr-lab-build-utils-run-tests --test_path /path/to/tests --with_xml_report --with_coverage
karr-lab-build-utils-make-and-archive-reports
```

### CircleCI build configuration
```
machine:
  python:
    version: 2.7.11
dependencies:
  pre:
    - pip install Karr-Lab-build-utils
    - karr-lab-build-utils-install-requirements
test:
  override:
    - karr-lab-build-utils-run-tests --test_path tests --with_xml_report --with_coverage
  post:
    - karr-lab-build-utils-make-and-archive-reports
```

## Documentation
Please see the [API documentation](http://Karr-Lab-build-utils.readthedocs.io).

## License
The build utilities are released under the [MIT license](LICENSE.txt).

## Development team
This package was developed by [Jonathan Karr](http://www.karrlab.org) at the Icahn School of Medicine at Mount Sinai in New York, USA.

## Questions and comments
Please contact the [Jonathan Karr](http://www.karrlab.org) with any questions or comments.
