`karr_lab_build_utils` documentation
====================================

This package performs several aspects of the Karr Lab's build system:

* Versionning with `Git <https://git-scm.com>`_ and `GitHub <https://github.com>`_

  * Creates new Git repositories with the proper directory structure and files for our build system

* Testing code with Python 2 and 3

  * Uses `pytest <https://docs.pytest.org>`_ or `nose <http://nose.readthedocs.io>`_ test runners
  * Uses `coverage <https://coverage.readthedocs.io>`_ or `instrumental <http://instrumental.readthedocs.io>`_ for statement, branch, or multiple condition coverage analysis
  * Runs the tests locally or using a `Docker <https://www.docker.com>`_ image or the CircleCI `local executor <https://circleci.com/docs/2.0/local-jobs>`_

* Static code analysis with Pylint

  * Statistically analyzes code using `Pylint <https://www.pylint.org>`_

* Documentation with Sphinx

  * Generates documentation using `Sphinx <http://www.sphinx-doc.org>`_

* Dependency management

  * Installs and upgrades all of the requirements of a package
  * Identifies missing and unused dependencies
  * Compiles downstream package dependencies
  * Visualizes downstream packages dependencies
  * Checks for cycles in package dependencies

* Continous integration with `CircleCI <https://circleci.com>`_

  * Creates CircleCI builds for packages
  * Gets, sets, and deletes environment variables
  * Triggers CircleCI to test downstream dependencies

* Test analysis with our `test history server <https://tests.karrlab.org>`_

  * Uploads test reports to our test history server

* Coverage analysis with `Coveralls <https://coveralls.io>`_

  * Uploads coverage reports to Coveralls

* Coverage analysis and static code analysis with `Code Climate <https://codeclimate.com>`_

  * Create Code Climate builds for packages
  * Uploads coverage reports to Code Climate

* Distribution with `PyPI <https://pypi.python.org>`_

  * Uploads packages to PyPI


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
