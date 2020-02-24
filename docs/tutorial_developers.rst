Tutorial for WC modeling software developers
============================================

Creating a new package
----------------------

Use the ``create-package`` command to create a new package (create local and remote repositories with the proper directory structure and files for our build system, add the repository to CircleCI, add the package to downstream dependencies of dependent packages, etc.). The command will prompt you for all of the information needed to create a repository and instruct you on how to create a new package, including linking it to `CircleCI <https://circleci.com/product/>`_, `Coveralls <https://coveralls.io>`_, `Code Climate <https://codeclimate.com/quality/>`_, and `Read the Docs <https://readthedocs.org>`_. The command should be run from the package's desired parent directory, e.g. with a current working directory of ``~/git_repositories``::

    cd ~/git_repositories
    karr_lab_build_utils create-package

``karr_lab_build_utils`` also provides two lower-level commands for creating, cloning, and initializing Git repositories. These commands are an alternative to the ``create-package`` command that does much more.

* ``create-repository``: Create a new GitHub repository and clone it locally.
* ``setup-repository``: Set up the file structure of a local Git repository.

.. code::

    cd ~/git_repositories
    karr_lab_build_utils create-repository
    karr_lab_build_utils setup-repository

These commands will create a repository with the following directory structure and files::

    /path/to/git_repositories/repo_and_package_name/
        LICENSE
        setup.py
        setup.cfg
        MANIFEST.in
        requirements.txt
        requirements.optional.txt
        README.md
        .karr_lab_build_utils.yml
        .gitignore
        repo_and_package_name/
            __init__.py
            __main__.py (optional, for command line programs)
            _version.py
        tests/
            requirements.txt
            fixtures/
        docs/
            conf.py
            requirements.txt
            requirements.rtd.txt
            index.rst


Developing a package
--------------------

Please see the `Software engineering <https://docs.karrlab.org/intro_to_wc_modeling/latest/concepts_skills/software_engineering/index.html>`_ section of "An Introduction to Whole-Cell Modeling."


Managing dependencies of packages
---------------------------------


Installing the dependencies for a package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Run the following command to install all of the requirements for the current package in the following files:

* ``requirements.txt``,
* ``requirements.optional.txt``,
* ``tests/requirements.txt``, and
* ``docs/requirements.txt``

.. code-block:: bash

    karr_lab_build_utils install-requirements

Finding missing requirements for a package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Run this command to find potentially missing requirements for the package ``package_name``::

    karr_lab_build_utils find-missing-requirements package_name

Finding unused requirements for a package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Run this command to identify potentially unused requirements for a package::

    karr_lab_build_utils find-unused-requirements package_name

Compiling the downstream dependencies of a package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To compile all of the downstream dependencies of a package perform these steps:

#. Clone all of our packages into a single directory, e.g., ``~/git_repositories``.
#. Run this command to compile the downstream dependencies of your package::

    karr_lab_build_utils compile-downstream-dependencies --packages-parent-dir ~/git_repositories

#. Optionally, add the ``--downstream-dependencies-filename`` option to save the dependencies to a YAML file::

    karr_lab_build_utils compile-downstream-dependencies --packages-parent-dir ~/git_repositories \
        --downstream-dependencies-filename .circleci/downstream_dependencies.yml


Configuring packages
---------------------------

The ``karr_lab_build_config`` repository should contain all of the whole-cell modeling and third party access credentials and configuration files needed to run your tests. This should include all usernames, passwords, and tokens needed to run your tests.

Configuration files for whole-cell modeling packages should be saved to the top-level directory of the ``karr_lab_build_config`` repository with the file pattern ``<package_name>.cfg``. 

All configuration files for third-party software should be saved to the ``third_party`` subdirectory of the ``karr_lab_build_config`` repository. In addition, ``third_party/paths.yml`` should contain a YAML-formatted dictionary whose keys are the names of the files in the ``third_party`` subdirectory and whose values are the locations that these files should be copied to.


Testing with pytest, coverage, instrumental, Docker, and CircleCI
-----------------------------------------------------------------

Running the tests for a package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Run this command to test the local package::

    karr_lab_build_utils run-tests

Evaluating the coverage of the tests
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Add the ``--coverage-type`` option to specify ``statement``, ``branch``, or ``multiple-condition`` coverage, e.g.::

    karr_lab_build_utils run-tests --with-coverage --coverage-type branch

Running tests with Docker or the CircleCI local executor
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Add the ``--environment`` option to specify ``local``, ``docker``, or ``circleci``, e.g.::

    karr_lab_build_utils run-tests --environment docker tests


Configuring tests of downstream dependencies
--------------------------------------------

The ``downstream_dependencies`` key of ``/path/to/repo/.karr_lab_build_utils.yml`` should represent a list of the names of the downstream dependencies of your package. For example, if your package is used by ``wc_lang`` and ``wc_sim``, ``.karr_lab_build_utils.yml`` should contain::

    downstream_dependencies:
      - wc_lang
      - wc_sim


Configuring the static analyses run by the build system
-------------------------------------------------------
The ``static_analyses.ignore_files`` key of ``/path/to/repo/.karr_lab_build_utils.yml`` should represent a list of glob patterns not to statically analyze. E.g.::
    
    static_analyses:
      ignore_files:
          - karr_lab_build_utils/templates/*


Configuring build email notifications
-------------------------------------

The ``email_notifications`` key of ``/path/to/repo/.karr_lab_build_utils.yml`` should represent a list of email addresses to receive notifications of the build status of your package. E.g.::
    
    email_notifications:
      - jonrkarr@gmail.com


Documenting code with Sphinx
----------------------------

Building the documentation for a package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Run this command to compile the documentation in HTML format for a package.::

    karr_lab_build_utils make-documentation

Spell checking documentation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Add the ``--spell-check`` option to spell check the documentation, e.g.::

    karr_lab_build_utils make-documentation --spell-check

The output will be saved to ``docs/_build/spelling/output.txt``.

White-listed words can be saved (1 word per line) to ``docs/spelling_wordlist.txt``.