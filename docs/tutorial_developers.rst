Tutorial for WC modeling software developers
============================================

Configuring files not to statically analyze
-------------------------------------------
The ``static_analyses.ignore_files`` key of ``/path/to/repo/.karr_lab_build_utils.yml`` should represent a list of glob patterns not to statically analyze. E.g.::
    
    static_analyses:
      ignore_files:
          - karr_lab_build_utils/templates/*


Configuring tests of downstream dependencies
--------------------------------------------

The ``downstream_dependencies`` key of ``/path/to/repo/.karr_lab_build_utils.yml`` should represent a list of the names of the downstream dependencies of your package. For example, if your package is used by ``wc_lang`` and ``wc_sim``, ``.karr_lab_build_utils.yml`` should contain::

    downstream_dependencies:
      - wc_lang
      - wc_sim


Configuring build email notifications
-------------------------------------

The ``email_notifications`` key of ``/path/to/repo/.karr_lab_build_utils.yml`` should represent a list of email addresses to receive notifications of the build status of your package. E.g.::
    
    email_notifications:
      - jonrkarr@gmail.com


Configuring packages
---------------------------

The ``karr_lab_build_configs`` repository should contain all of the configuration (.cfg) files needed to run your tests. This should include all usernames, passwords, and tokens needed to run your tests.
