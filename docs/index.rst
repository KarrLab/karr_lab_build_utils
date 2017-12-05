`karr_lab_build_utils` documentation
====================================

This package performs several aspects of the Karr Lab's build system:

* Creates new Git repositories with the proper directory structure and files for our build system
* Installs and upgrades all of the requirements of a package
* Tests code with Python 2 and 3
  
  * Uses `pytest <https://docs.pytest.org>`_ or `nose <http://nose.readthedocs.io>`_ test runners
  * Uses `coverage <https://coverage.readthedocs.io>`_ or `instrumental <http://instrumental.readthedocs.io>`_ for statement, branch, or multiple condition coverage analysis
  * Runs the tests locally or using a `Docker <https://www.docker.com>`_ image or the CircleCI `local executor <https://circleci.com/docs/2.0/local-jobs>`_

* Uploads test reports to our `test history server <https://tests.karrlab.org>`_
* Uploads coverage reports to `Coveralls <https://coveralls.io>`_ and `Code Climate <https://codeclimate.com>`_
* Generates documentation using `Sphinx <http://www.sphinx-doc.org>`_
* Creates CircleCI builds for packages
* Create Code Climate builds for packages
* Triggers `CircleCI <https://circleci.com>`_ to test downstream dependencies
* Uploads packages to `PyPI <https://pypi.python.org>`_
* Statistically analyzes code using `Pylint <https://www.pylint.org>`_
* Identifies missing and unused dependencies

The build system is primarily designed for:

* Code that is implemented with Python 2/3
* Tests that can be run with pytest
* Code that is documented with Sphinx in `Napolean <https://sphinxcontrib-napoleon.readthedocs.io>`_/`Google style <http://google.github.io/styleguide/pyguide.html>`_
* Code that is versioned with `Git <https://git-scm.com>`_/`GitHub <https://github.com>`_
* Builds that are run on CircleCI
* Coverage reports that are hosted on Coveralls and Code Climate
* Documentation that is hosted on `Read the Docs <https://readthedocs.org>`_


Contents
--------

.. toctree::
   :maxdepth: 3
   :numbered:

   installation.rst
   tutorial.rst
   API documentation <source/modules.rst>
   about.rst
