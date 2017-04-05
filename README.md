<!--[![PyPI package](https://img.shields.io/pypi/v/Karr-Lab-build-utils.svg)](https://pypi.python.org/pypi/Karr-Lab-build-utils)-->
[![Documentation](https://readthedocs.org/projects/karr-lab-build-utils/badge/?version=latest)](http://karr-lab-build-utils.readthedocs.org)
[![Test results](https://circleci.com/gh/KarrLab/Karr-Lab-build-utils.svg?style=shield)](https://circleci.com/gh/KarrLab/Karr-Lab-build-utils)
[![Test coverage](https://coveralls.io/repos/github/KarrLab/Karr-Lab-build-utils/badge.svg)](https://coveralls.io/github/KarrLab/Karr-Lab-build-utils)
[![Code analysis](https://codeclimate.com/github/KarrLab/Karr-Lab-build-utils/badges/gpa.svg)](https://codeclimate.com/github/KarrLab/Karr-Lab-build-utils)
[![License](https://img.shields.io/github/license/KarrLab/Karr-Lab-build-utils.svg)](LICENSE)
![Analytics](https://ga-beacon.appspot.com/UA-86759801-1/Karr-Lab-build-utils/README.md?pixel)

# Karr Lab build utilities

This package performs several aspects of the Karr Lab's build system:
* Tests code with Python 2 and 3 using pytest
* Uploads test reports to our test history server
* Uploads coverage report to Coveralls
* Generates HTML API documentation using Sphinx

The build system is primarily designed for:
* Code that is implemented with Python 2/3
* Tests that can be run with pytest
* Code that is documented with Sphinx in Napolean/Google style

## Installation
1. Install dependencies
  * `libffi-dev`
2. Install package 
  ```
  pip install git+git://github.com/KarrLab/Karr-Lab-build-utils#egg=karr_lab_build_utils
  ```

## Usage

### Package organization
To use the utilities, your package should follow this organization scheme:
```
/path/to/repo/
  LICENSE
  setup.py
  setup.cfg
  MANIFEST.in  
  requirements.txt
  README.md
  <repo_name>
    __init__.py
      __version__ = '<version_number>'
    __main__.py (optional, for command line programs)
  tests/
    requirements.txt
    fixtures/
      secret/ (git-ignored fixtures that contain usernames, passwords, and tokens)
  docs/
    conf.py
    requirements.txt
    index.rst
    _static (optional for any files needed for the documentation)
```

### Setup settings
The following options should be set in `setup.cfg`
```
[coverage:run]
source = 
    <repo_name>

[sphinx-apidocs]
packages = 
    <repo_name>
```

### Sphinx settings
Add/uncomment these lines in `docs/conf.py`
```
import os
import sys
sys.path.insert(0, os.path.abspath('..'))
```

Enable the napolean and google analytics extensions in `docs/conf.py`
```
extensions = [
    ...
    'sphinx.ext.napoleon',
    'sphinxcontrib.googleanalytics',
]
```

Set the version and release in `docs/conf.py`
```
version = <repo_name>.__version__
release = version
```

Set the napolean options in `docs/conf.py`
```
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
```

Configure `docs/conf.py` to use the Read the Docs theme
```
import sphinx_rtd_theme
html_theme = 'sphinx_rtd_theme'
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
```

Set the google analytics id in `docs/conf.py`
```
googleanalytics_id = 'UA-86340737-1'
```

Add the following to trigger API documentation when the documenation is compiled
```
from configparser import ConfigParser
from sphinx import apidoc

def run_apidoc(app):
    this_dir = os.path.dirname(__file__)
    parser = ConfigParser()
    parser.read(os.path.join(this_dir, '..', 'setup.cfg'))
    packages = parser.get('sphinx-apidocs', 'packages').strip().split('\n')
    for package in packages:
        apidoc.main(argv=['sphinx-apidoc', '-f', '-o', os.path.join(this_dir, 'source'), os.path.join(this_dir, '..', package)])

def setup(app):
    app.connect('builder-inited', run_apidoc)
```

### Sphinx examples

#### Class
```
class MyClass(object):
    ''' Short description

    Long description

    Attributes:
      arg1 (:obj:`type`): description
      arg2 (:obj:`type`): description
      …
    '''

    ...
```

#### Methods
```
def my_method(self, arg1, arg2):
    ''' Short description

    Long description

    Args:
      arg1 (:obj:`type`): description
      arg2 (:obj:`type`, optional): description
      …

    Returns:
      :obj:`type`: description

    Raises:
      :obj:`ErrorType`: description
      …
    '''

    ...
```

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
    - pip install git+git://github.com/KarrLab/Karr-Lab-build-utils#egg=karr_lab_build_utils
    - karr-lab-build-utils install-requirements
test:
  override:
    - karr-lab-build-utils run-tests --test_path tests --with_xml_report --with_coverage
  post:
    - karr-lab-build-utils make-and-archive-reports
```

## Documentation
Please see the [API documentation](http://Karr-Lab-build-utils.readthedocs.io).

## License
The build utilities are released under the [MIT license](LICENSE).

## Development team
This package was developed by [Jonathan Karr](http://www.karrlab.org) at the Icahn School of Medicine at Mount Sinai in New York, USA.

## Questions and comments
Please contact the [Jonathan Karr](http://www.karrlab.org) with any questions or comments.
