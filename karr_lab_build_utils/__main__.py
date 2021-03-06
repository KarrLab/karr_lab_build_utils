""" Karr Lab build utilities

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2016-10-27
:Copyright: 2018, Karr Lab
:License: MIT
"""

import cement
from karr_lab_build_utils.core import BuildHelper, BuildHelperError
import karr_lab_build_utils
import os
import sys
import traceback


class BaseController(cement.Controller):
    """ Base controller for command line application """

    class Meta:
        label = 'base'
        description = "Karr Lab build utilities"
        help = "Karr Lab build utilities"
        arguments = [
            (['-v', '--version'], dict(action='version', version=karr_lab_build_utils.__version__)),
        ]

    @cement.ex(help='Archive test report')
    def archive_test_report(self):
        """ Upload test report to history server """
        buildHelper = BuildHelper()
        buildHelper.archive_test_report()

    @cement.ex(help='Install requirements')
    def install_requirements(self):
        """ Install requirements """
        buildHelper = BuildHelper()
        buildHelper.install_requirements()

    @cement.ex(help="Upgrade the packages from the Karr Lab's GitHub organization")
    def upgrade_karr_lab_packages(self):
        """ Upgrade the packages from the Karr Lab's GitHub organization """
        buildHelper = BuildHelper()
        buildHelper.upgrade_karr_lab_packages()

    @cement.ex(hide=True)
    def _default(self):
        self._parser.print_help()


class CreatePackageController(cement.Controller):
    """ Create a package

    * Create local and remote Git repositories;
    * Setup the directory structure of the repository;
    * Add the repository to CircleCI, Coveralls, Code Climate, Read the Docs, and code.karrlab.org;
    * Update the downstream dependencies of the package''s dependencies
    """

    class Meta:
        label = 'create-package'
        description = (
            '- Create local and remote Git repositories;\n'
            '    - Setup the directory structure of the repository;\n'
            '    - Add the repository to CircleCI, Coveralls, Code Climate, Read the Docs, and code.karrlab.org;\n'
            '    - Update the downstream dependencies of the package''s dependencies'
        )
        help = (
            '- Create local and remote Git repositories;\n'
            '    - Setup the directory structure of the repository;\n'
            '    - Add the repository to CircleCI, Coveralls, Code Climate, Read the Docs, and code.karrlab.org;\n'
            '    - Update the downstream dependencies of the package''s dependencies'
        )
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['--pypi-repository'], dict(
                default='pypi', type=str, help='Repository upload package (e.g. pypi or testpypi)')),
        ]

    @cement.ex(hide=True)
    def _default(self):
        args = self.app.pargs
        buildHelper = BuildHelper()
        buildHelper.create_package(pypi_repository=args.pypi_repository)


class CreateRepositoryController(cement.Controller):
    """ Create a GitHub repository and clone the repository locally """

    class Meta:
        label = 'create-repository'
        description = 'Create a GitHub repository and clone the repository locally'
        help = 'Create a GitHub repository and clone the repository locally'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['name'], dict(
                type=str, help='Name of the repository (i.e. repo_<name>)')),
            (['--description'], dict(
                default='', type=str, help='Description of the repository')),
            (['--public'], dict(
                default=False, action='store_true', help='if set, make the repository public')),
            (['--dirname'], dict(
                default=None, type=str, help='Path for the repository')),
        ]

    @cement.ex(hide=True)
    def _default(self):
        args = self.app.pargs
        buildHelper = BuildHelper()
        buildHelper.create_repository(args.name, description=args.description, private=(not args.public), dirname=args.dirname)


class SetupRepositoryController(cement.Controller):
    """ Setup a local Git repository with the default directory structure """

    class Meta:
        label = 'setup-repository'
        description = 'Setup a local Git repository with the default directory structure'
        help = 'Setup a local Git repository with the default directory structure'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['name'], dict(
                type=str, help='Name of the repository (i.e. repo_<name>)')),
            (['--description'], dict(
                default='', type=str, help='Description of the repository')),
            (['--keyword'], dict(
                dest='keywords', default=[], type=str, action='append', help='Keyword for the repository')),
            (['--dependency'], dict(
                dest='dependencies', default=[], type=str, action='append', help='Karr Lab package that the package depends on')),
            (['--public'], dict(
                default=False, action='store_true', help='if set, make the repository public')),
            (['--build-image-version'], dict(
                default=None, type=str, help='Build image version')),
            (['--dirname'], dict(
                default=None, type=str, help='Path for the repository')),
            (['--coveralls-repo-badge-token'], dict(
                default=None, type=str, help='Coveralls badge token for the repository')),
            (['--code-climate-repo-id'], dict(
                default=None, type=str, help='Code Climate ID the repository')),
            (['--code-climate-repo-badge-token'], dict(
                default=None, type=str, help='Code Climate badge token for the repository')),
        ]

    @cement.ex(hide=True)
    def _default(self):
        args = self.app.pargs
        buildHelper = BuildHelper()
        buildHelper.setup_repository(
            args.name, description=args.description, keywords=args.keywords, dependencies=args.dependencies,
            private=(not args.public), build_image_version=args.build_image_version, dirname=args.dirname,
            coveralls_repo_badge_token=args.coveralls_repo_badge_token,
            code_climate_repo_id=args.code_climate_repo_id, code_climate_repo_badge_token=args.code_climate_repo_badge_token)


class CreateDocumentationTemplateController(cement.Controller):
    """ Create a Sphinx documentation template for a package """

    class Meta:
        label = 'create-documentation-template'
        description = 'Create a Sphinx documentation template for a package'
        help = 'Create a Sphinx documentation template for a package'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['--dirname'], dict(
                default='.', type=str, help="Path to the package; default='.'")),
        ]

    @cement.ex(hide=True)
    def _default(self):
        args = self.app.pargs
        buildHelper = BuildHelper()
        buildHelper.create_documentation_template(dirname=args.dirname)


class DownloadInstallPackageConfigFilesController(cement.Controller):
    """ Download and install configuration files from GitHub configuration repository """

    class Meta:
        label = 'download-install-package-config-files'
        description = 'Download and install configuration files from GitHub configuration repository'
        help = 'Download and install configuration files from GitHub configuration repository'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = []

    @cement.ex(hide=True)
    def _default(self):
        args = self.app.pargs
        buildHelper = BuildHelper()
        buildHelper.download_package_config_files()
        buildHelper.install_package_config_files()


class RunTestsController(cement.Controller):
    """ cement.Controller for run_tests.

    Run unit tests located at `test-path`.
    Optionally, generate a coverage report.
    Optionally, save the results to an XML file.
    """

    class Meta:
        label = 'run-tests'
        description = 'Run unit tests located at `test_path`'
        help = 'Run unit tests located at `test_path`'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['--test-path'], dict(
                type=str, default=None, help=(
                    'Path to tests to run. '
                    'The path should be relative to the current directory, or an absolute path. '
                    'Default: the value of the environment variable `test_path` or '
                    '`./tests` if the environment variable has not been set.'))),
            (['--dirname'], dict(
                type=str, default='.', help="Path to package to test; default='.'")),
            (['--n-workers'], dict(
                type=int, default=1, help='Numbers of workers to run tests`')),
            (['--i-worker'], dict(
                type=int, default=0, help='Index of worker within {0 .. n-workers - 1}')),
            (['--verbose'], dict(
                default=False, action='store_true', help='if set display test output')),
            (['--with-xunit'], dict(
                default=False, action='store_true', help='if set save test results to XML file')),
            (['--with-coverage'], dict(
                default=False, action='store_true', help='if set assess code coverage')),
            (['--coverage-dirname'], dict(
                type=str, default='tests/reports', help="Directory to store coverage data; default='tests/reports'")),
            (['--coverage-type'], dict(
                type=str, default='branch',
                help="Type of coverage analysis to run {statement, branch, or multiple-decision}; default='branch'")),
            (['--environment'], dict(
                type=str, default='local',
                help="Environment to run tests (local, docker, or circleci); default='local'")),
            (['--ssh-key-filename'], dict(
                type=str, default='~/.ssh/id_rsa', help='Path to GitHub SSH key')),
            (['--keep-docker-container'], dict(
                dest='remove_docker_container', action='store_false', default=True, help='Keep Docker container')),
        ]

    @cement.ex(hide=True)
    def _default(self):
        args = self.app.pargs

        # if `test_path` was not specified at the command line, try to get it from the `test_path` environment variable
        # which can be set in CircleCI via build parameters
        if args.test_path is None:
            if 'test_path' in os.environ:
                test_path = os.getenv('test_path')
            else:
                test_path = 'tests'
        else:
            test_path = args.test_path

        verbose = args.verbose or bool(int(os.getenv('verbose', '0')))

        # get coverage type
        coverage_type = karr_lab_build_utils.core.CoverageType[args.coverage_type.lower().replace('-', '_')]

        # run tests
        buildHelper = BuildHelper()
        buildHelper.run_tests(dirname=args.dirname, test_path=test_path,
                              n_workers=args.n_workers, i_worker=args.i_worker,
                              verbose=verbose, with_xunit=args.with_xunit,
                              with_coverage=args.with_coverage, coverage_dirname=args.coverage_dirname,
                              coverage_type=coverage_type, environment=karr_lab_build_utils.core.Environment[args.environment],
                              ssh_key_filename=args.ssh_key_filename, remove_docker_container=args.remove_docker_container)


class DockerController(cement.Controller):
    """ Base controller for Docker tasks """

    class Meta:
        label = 'docker'
        description = 'Docker utilities'
        help = 'Docker utilities'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = []

    @cement.ex(hide=True)
    def _default(self):
        self._parser.print_help()


class DockerCreateContainerController(cement.Controller):
    """ Create a Docker container for running tests """

    class Meta:
        label = 'create-container'
        description = 'Create a Docker container for running tests'
        help = 'Create a Docker container for running tests'
        stacked_on = 'docker'
        stacked_type = 'nested'
        arguments = [
            (['--ssh-key-filename'], dict(
                type=str, default='~/.ssh/id_rsa', help='Path to GitHub SSH key')),
        ]

    @cement.ex(hide=True)
    def _default(self):
        args = self.app.pargs
        buildHelper = BuildHelper()
        container = buildHelper.create_docker_container(ssh_key_filename=args.ssh_key_filename)
        print('Created Docker container {0} with volume {0}'.format(container))


class InstallPackageToDockerContainerController(cement.Controller):
    """ Copy and install a package to a Docker container """
    class Meta:
        label = 'install-package-to-container'
        description = 'Copy and install a package to a Docker container'
        help = 'Copy and install a package to a Docker container'
        stacked_on = 'docker'
        stacked_type = 'nested'
        arguments = [
            (['container'], dict(type=str, help="Container id")),
            (['--dirname'], dict(
                type=str, default='.', help="Path to package to test; default='.'")),
        ]

    @cement.ex(hide=True)
    def _default(self):
        args = self.app.pargs
        buildHelper = BuildHelper()
        buildHelper.install_package_to_docker_container(args.container, dirname=args.dirname)


class RunTestsInDockerContainerController(cement.Controller):
    """ Run tests in a Docker container """

    class Meta:
        label = 'run-tests-in-container'
        description = 'Run tests in a Docker container'
        help = 'Run tests in a Docker container'
        stacked_on = 'docker'
        stacked_type = 'nested'
        arguments = [
            (['container'], dict(type=str, help="Container id")),
            (['--test-path'], dict(
                type=str, default=None, help=(
                    'Path to tests to run. '
                    'The path should be relative to the current directory, or an absolute path. '
                    'Default: the value of the environment variable `test_path` or '
                    '`./tests` if the environment variable has not been set.'))),
            (['--n-workers'], dict(
                type=int, default=1, help='Numbers of workers to run tests`')),
            (['--i-worker'], dict(
                type=int, default=0, help='Index of worker within {0 .. n-workers - 1}')),
            (['--verbose'], dict(
                default=False, action='store_true', help='if set display test output')),
            (['--with-xunit'], dict(
                default=False, action='store_true', help='if set save test results to XML file')),
            (['--with-coverage'], dict(
                default=False, action='store_true', help='if set assess code coverage')),
            (['--coverage-dirname'], dict(
                type=str, default='tests/reports', help="Directory to store coverage data; default='tests/reports'")),
            (['--coverage-type'], dict(
                type=str, default='branch',
                help="Type of coverage analysis to run {statement, branch, or multiple-decision}; default='branch'")),
        ]

    @cement.ex(hide=True)
    def _default(self):
        # if `test_path` was not specified at the command line, try to get it from the `test_path` environment variable
        # which can be set in CircleCI via build parameters
        args = self.app.pargs
        if args.test_path is None:
            if 'test_path' in os.environ:
                test_path = os.getenv('test_path')
            else:
                test_path = 'tests'
        else:
            test_path = args.test_path

        verbose = args.verbose or bool(int(os.getenv('verbose', '0')))

        # get coverage type
        coverage_type = karr_lab_build_utils.core.CoverageType[args.coverage_type.lower().replace('-', '_')]

        # run tests
        buildHelper = BuildHelper()
        buildHelper.run_tests_in_docker_container(args.container, test_path=test_path,
                                                  n_workers=args.n_workers, i_worker=args.i_worker,
                                                  verbose=verbose, with_xunit=args.with_xunit,
                                                  with_coverage=args.with_coverage, coverage_dirname=args.coverage_dirname,
                                                  coverage_type=coverage_type)


class DockerRemoveContainerController(cement.Controller):
    """ Remove a Docker container """

    class Meta:
        label = 'remove-container'
        description = 'Remove a Docker container'
        help = 'Remove a Docker container'
        stacked_on = 'docker'
        stacked_type = 'nested'
        arguments = [
            (['container'], dict(type=str, help="Container id")),
        ]

    @cement.ex(hide=True)
    def _default(self):
        args = self.app.pargs
        buildHelper = BuildHelper()
        buildHelper.remove_docker_container(args.container)


class FollowCircleciBuildController(cement.Controller):
    """ Follow a CircleCI build for a repository """
    class Meta:
        label = 'follow-circleci-build'
        description = 'Follow a CircleCI build for a repository'
        help = 'Follow a CircleCI build for a repository'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['--repo-type'], dict(
                type=str, default=None, help='Repository type (e.g., github)')),
            (['--repo-owner'], dict(
                type=str, default=None, help='Repository owner')),
            (['--repo-name'], dict(
                type=str, default=None, help='Name of the repository to build. This defaults to the name of the current repository.')),
            (['--has-private-dependencies'], dict(
                default=False, action='store_true',
                help=('Set if the build requires an SSH key for the Karr Lab machine user because the repository depends on '
                      'another private repository'))),
        ]

    @cement.ex(hide=True)
    def _default(self):
        args = self.app.pargs
        buildHelper = BuildHelper()
        buildHelper.follow_circleci_build(
            repo_type=args.repo_type, repo_owner=args.repo_owner,
            repo_name=args.repo_name,
            has_private_dependencies=args.has_private_dependencies)


class GetCircleciEnvironmentVariablesController(cement.Controller):
    """ Get the CircleCI environment variables for a repository and their partial values"""
    class Meta:
        label = 'get-circleci-environment-variables'
        description = 'Get the CircleCI environment variables for a repository and their partial values'
        help = 'Get the CircleCI environment variables for a repository and their partial values'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['--repo-type'], dict(
                type=str, default=None, help='Repository type (e.g., github)')),
            (['--repo-owner'], dict(
                type=str, default=None, help='Repository owner')),
            (['--repo-name'], dict(
                type=str, default=None, help='Name of the repository to build. This defaults to the name of the current repository.')),
        ]

    @cement.ex(hide=True)
    def _default(self):
        args = self.app.pargs
        buildHelper = BuildHelper()
        vars = buildHelper.get_circleci_environment_variables(
            repo_type=args.repo_type, repo_owner=args.repo_owner,
            repo_name=args.repo_name)
        for key, val in vars.items():
            print('{}={}'.format(key, val))


class SetCircleciEnvironmentVariableController(cement.Controller):
    """ Set a CircleCI environment variable for a repository """
    class Meta:
        label = 'set-circleci-environment-variable'
        description = 'Set a CircleCI environment variable for a repository'
        help = 'Set a CircleCI environment variable for a repository'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['name'], dict(
                type=str, help='Name of the environment variable.')),
            (['value'], dict(
                type=str, help='Value of the environment variable.')),
            (['--repo-type'], dict(
                type=str, default=None, help='Repository type (e.g., github)')),
            (['--repo-owner'], dict(
                type=str, default=None, help='Repository owner')),
            (['--repo-name'], dict(
                type=str, default=None, help='Name of the repository to build. This defaults to the name of the current repository.')),
        ]

    @cement.ex(hide=True)
    def _default(self):
        args = self.app.pargs
        buildHelper = BuildHelper()
        buildHelper.set_circleci_environment_variables(
            {args.name: args.value},
            repo_type=args.repo_type, repo_owner=args.repo_owner,
            repo_name=args.repo_name)


class DeleteCircleciEnvironmentVariableController(cement.Controller):
    """ Delete a CircleCI environment variable for a repository """
    class Meta:
        label = 'delete-circleci-environment-variable'
        description = 'Delete a CircleCI environment variable for a repository'
        help = 'Delete a CircleCI environment variable for a repository'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['name'], dict(
                type=str, help='Name of the environment variable.')),
            (['--repo-type'], dict(
                type=str, default=None, help='Repository type (e.g., github)')),
            (['--repo-owner'], dict(
                type=str, default=None, help='Repository owner')),
            (['--repo-name'], dict(
                type=str, default=None, help='Name of the repository to build. This defaults to the name of the current repository.')),
        ]

    @cement.ex(hide=True)
    def _default(self):
        args = self.app.pargs
        buildHelper = BuildHelper()
        buildHelper.delete_circleci_environment_variable(args.name,
                                                         repo_type=args.repo_type, repo_owner=args.repo_owner,
                                                         repo_name=args.repo_name)


class CreateCodeClimateGithubWebhookController(cement.Controller):
    """ Create Code Climate GitHub webhook for the current repository """
    class Meta:
        label = 'create-code-climate-github-webhook'
        description = 'Create Code Climate GitHub webhook for the current repository'
        help = 'Create Code Climate GitHub webhook for the current repository'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['--repo-type'], dict(
                type=str, default=None, help='Repository type (e.g., github)')),
            (['--repo-owner'], dict(
                type=str, default=None, help='Repository owner')),
            (['--repo-name'], dict(
                type=str, default=None, help='Name of the repository to build. This defaults to the name of the current repository.')),
        ]

    @cement.ex(hide=True)
    def _default(self):
        args = self.app.pargs
        buildHelper = BuildHelper()
        buildHelper.create_code_climate_github_webhook(
            repo_type=args.repo_type, repo_owner=args.repo_owner, repo_name=args.repo_name)


class DoPostTestTasksController(cement.Controller):
    """ Do all post-test tasks for CircleCI """

    class Meta:
        label = 'do-post-test-tasks'
        description = 'Do all post-test tasks for CircleCI'
        help = 'Do all post-test tasks for CircleCI'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['installation_exit_code'], dict(
                type=int, help='Exit code of the package installation tasks')),
            (['tests_exit_code'], dict(
                type=int, help='Exit code of the tests')),
            (['--dry-run'], dict(
                default=False, dest='dry_run', action='store_true', help='If set, do not send results to Coveralls and Code Climate')),
        ]

    @cement.ex(hide=True)
    def _default(self):
        args = self.app.pargs
        dry_run = args.dry_run or bool(int(os.getenv('dry_run', '0')))

        """ Do all post-test tasks for CircleCI """
        buildHelper = BuildHelper()
        triggered_packages, not_triggered_packages, status, other_exception = buildHelper.do_post_test_tasks(
            args.installation_exit_code != 0, args.tests_exit_code != 0, dry_run=dry_run)

        # downstream triggered tests
        if triggered_packages:
            print('{} downstream builds were triggered'.format(len(triggered_packages)))
            for triggered_package in triggered_packages:
                print('  {}'.format(triggered_package))
        else:
            print("No downstream builds were triggered")
            if not_triggered_packages:
                for key, msg in not_triggered_packages.items():
                    print('  {}: {}'.format(key, msg.replace('\n', '\n  ')))

        # email notifications
        num_notifications = sum(status.values())
        if num_notifications > 0:
            print('{} notifications were sent'.format(num_notifications))

            if status['is_fixed']:
                print('  Build fixed')

            if status['is_old_error']:
                print('  Recurring error')

            if status['is_new_error']:
                print('  New error')

            if status['is_other_error']:
                print('  Other error')

            if status['is_new_downstream_error']:
                print('  Downstream error')
        else:
            print('No notifications were sent.')

        if status['is_other_error']:
            if other_exception:                
                traceback.print_tb(other_exception['traceback'])
                raise SystemExit('Post-test tasks were not successful: {}'.format(
                    other_exception['exception']))
            else:
                raise SystemExit('Post-test tasks were not successful')


class MakeAndArchiveReportsController(cement.Controller):
    """ Make and archive reports:

    * Generate HTML test history reports
    * Generate HTML API documentation
    * Archive coverage report to Coveralls and Code Climate
    """

    class Meta:
        label = 'make-and-archive-reports'
        description = 'Make and archive reports'
        help = 'Make and archive reports'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['--coverage-dirname'], dict(
                type=str, default='tests/reports', help="Directory to store coverage data; default='tests/reports'")),
            (['--dry-run'], dict(
                default=False, dest='dry_run', action='store_true', help='If set, do not send results to Coveralls and Code Climate')),
        ]

    @cement.ex(hide=True)
    def _default(self):
        args = self.app.pargs

        dry_run = args.dry_run or bool(int(os.getenv('dry_run', '0')))

        buildHelper = BuildHelper()
        buildHelper.make_and_archive_reports(coverage_dirname=args.coverage_dirname, dry_run=dry_run)


class CombineCoverageReportsController(cement.Controller):
    """ Combine coverage reports """

    class Meta:
        label = 'combine-coverage-reports'
        description = 'Combine coverage reports (.coverage.*) into a single file (.coverage)'
        help = 'Combine coverage reports (.coverage.*) into a single file (.coverage)'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['--coverage-dirname'], dict(
                type=str, default='tests/reports', help="Directory to store coverage data; default='tests/reports'")),
        ]

    @cement.ex(hide=True)
    def _default(self):
        args = self.app.pargs
        buildHelper = BuildHelper()
        buildHelper.combine_coverage_reports(coverage_dirname=args.coverage_dirname)


class ArchiveCoverageReportController(cement.Controller):
    """ Archive a coverage report:

    * Upload report to Coveralls and Code Climate
    """

    class Meta:
        label = 'archive-coverage-report'
        description = 'Archive coverage report'
        help = 'Archive coverage report'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['--coverage-dirname'], dict(
                type=str, default='tests/reports', help="Directory to store coverage data; default='tests/reports'")),
            (['--dry-run'], dict(
                default=False, dest='dry_run', action='store_true', help='If set, do not send results to Coveralls and Code Climate')),
        ]

    @cement.ex(hide=True)
    def _default(self):
        """ Archive a coverage report:

        * Upload report to Coveralls and Code Climate
        """
        args = self.app.pargs
        dry_run = args.dry_run or bool(int(os.getenv('dry_run', '0')))
        buildHelper = BuildHelper()
        buildHelper.archive_coverage_report(coverage_dirname=args.coverage_dirname, dry_run=dry_run)


class UploadCoverageReportToCoverallsController(cement.Controller):
    """ Upload coverage report to Code Climate """

    class Meta:
        label = 'upload-coverage-report-to-coveralls'
        description = 'Upload coverage report to Coveralls'
        help = 'Upload coverage report to Coveralls'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['--coverage-dirname'], dict(
                type=str, default='tests/reports', help="Directory to store coverage data; default='tests/reports'")),
            (['--dry-run'], dict(
                default=False, dest='dry_run', action='store_true', help='If set, do not send results to Coveralls')),
        ]

    @cement.ex(hide=True)
    def _default(self):
        """ Upload coverage report to Coveralls """
        args = self.app.pargs
        dry_run = args.dry_run or bool(int(os.getenv('dry_run', '0')))
        buildHelper = BuildHelper()
        buildHelper.upload_coverage_report_to_coveralls(coverage_dirname=args.coverage_dirname, dry_run=dry_run)


class UploadCoverageReportToCodeClimateController(cement.Controller):
    """ Upload coverage report to Code Climate """

    class Meta:
        label = 'upload-coverage-report-to-code-climate'
        description = 'Upload coverage report to Code Climate'
        help = 'Upload coverage report to Code Climate'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['--coverage-dirname'], dict(
                type=str, default='tests/reports', help="Directory to store coverage data; default='tests/reports'")),
            (['--dry-run'], dict(
                default=False, dest='dry_run', action='store_true', help='If set, do not send results to Code Climate')),
        ]

    @cement.ex(hide=True)
    def _default(self):
        """ Upload coverage report to Code Climate """
        args = self.app.pargs
        dry_run = args.dry_run or bool(int(os.getenv('dry_run', '0')))
        buildHelper = BuildHelper()
        buildHelper.upload_coverage_report_to_code_climate(coverage_dirname=args.coverage_dirname, dry_run=dry_run)


class MakeDocumentationController(cement.Controller):
    """ cement.Controller for make_documentation.

    Make HTML documentation. Optionally, spell check documentation.
    """

    class Meta:
        label = 'make-documentation'
        description = 'Make HTML documentation. Optionally, spell check documentation.'
        help = 'Make HTML documentation. Optionally, spell check documentation.'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['--spell-check'], dict(
                default=False, dest='spell_check', action='store_true', help='If set, spell check documentation')),
        ]

    @cement.ex(hide=True)
    def _default(self):
        args = self.app.pargs
        buildHelper = BuildHelper()
        buildHelper.make_documentation(spell_check=args.spell_check)


class CompileDownstreamDependenciesController(cement.Controller):
    """ Compile the downstream dependencies of a package by analyzing the requirements files of other packages """

    class Meta:
        label = 'compile-downstream-dependencies'
        description = 'Compile the downstream dependencies of a package by analyzing the requirements files of other packages'
        help = 'Compile the downstream dependencies of a package by analyzing the requirements files of other packages'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['--dirname'], dict(
                type=str, default='.', help='Path to package')),
            (['--packages-parent-dir'], dict(
                type=str, default='..', help='Path to the parent directory of the other packages')),
            (['--config-filename'], dict(
                type=str, default=None, help='Path to save the configuration including downstream dependencies in YAML format')),
        ]

    @cement.ex(hide=True)
    def _default(self):
        args = self.app.pargs
        buildHelper = BuildHelper()
        packages = buildHelper.compile_downstream_dependencies(
            dirname=args.dirname,
            packages_parent_dir=args.packages_parent_dir,
            config_filename=args.config_filename)

        if packages:
            print('The following downstream dependencies were found:')
            for package in packages:
                print('  {}'.format(package))
        else:
            print('No downstream packages were found.')


class ArePackageDependenciesAcyclicController(cement.Controller):
    """ Check if the package dependencies are acyclic so they are supported by CircleCI """

    class Meta:
        label = 'are-package-dependencies-acyclic'
        description = 'Check if the package dependencies are acyclic so they are supported by CircleCI'
        help = 'Check if the package dependencies are acyclic so they are supported by CircleCI'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['--packages-parent-dir'], dict(
                type=str, default='..', help='Path to the parent directory of the other packages')),
        ]

    @cement.ex(hide=True)
    def _default(self):
        args = self.app.pargs
        buildHelper = BuildHelper()
        if buildHelper.are_package_dependencies_acyclic(packages_parent_dir=args.packages_parent_dir):
            print('The dependencies are acyclic.')
        else:
            print('The dependencies are cyclic. This must be corrected for CircleCI.')


class VisualizePackageDependenciesController(cement.Controller):
    """ Visualize downstream package dependencies as a graph """

    class Meta:
        label = 'visualize-package-dependencies'
        description = 'Visualize downstream package dependencies as a graph'
        help = 'Visualize downstream package dependencies as a graph'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['--packages-parent-dir'], dict(
                type=str, default='..', help='Path to the parent directory of the other packages')),
            (['--out-filename'], dict(
                type=str, default='../package_dependencies.pdf', help='Path to save the visualization')),
        ]

    @cement.ex(hide=True)
    def _default(self):
        args = self.app.pargs
        buildHelper = BuildHelper()
        buildHelper.visualize_package_dependencies(packages_parent_dir=args.packages_parent_dir, out_filename=args.out_filename)


class AnalyzePackageController(cement.Controller):
    """ Perform static analyses of a package using Pylint """

    class Meta:
        label = 'analyze-package'
        description = 'Perform static analyses of a package using Pylint'
        help = 'Perform static analyses of a package using Pylint'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['package_name'], dict(
                type=str, help='Name of the package to analyze')),
            (['--messages'], dict(
                type=str, default='', help='comma-separated list of ids of Pylint checks to run')),
        ]

    @cement.ex(hide=True)
    def _default(self):
        args = self.app.pargs
        buildHelper = BuildHelper()
        if args.messages:
            messages = [msg.strip() for msg in args.messages.split(',')]
        else:
            messages = None
        buildHelper.analyze_package(args.package_name, messages=messages)


class FindMissingRequirementsController(cement.Controller):
    """ cement.Controller for finding missing requirements """

    class Meta:
        label = 'find-missing-requirements'
        description = 'Finding missing requirements for a package.'
        help = 'Finding missing requirements for a package.'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['package_name'], dict(
                type=str, help='Package name')),
            (['--dirname'], dict(
                type=str, default='.', help='Path to package')),
        ]

    @cement.ex(hide=True)
    def _default(self):
        args = self.app.pargs
        buildHelper = BuildHelper()
        missing = buildHelper.find_missing_requirements(
            args.package_name, dirname=args.dirname)
        missing = sorted(missing, key=lambda m: m[0])
        if missing:
            print('The following dependencies should likely be added to requirements.txt')
            for name, uses in missing:
                for use in uses:
                    for filename, lineno in use.locations:
                        print('  {:s} in {:s}:{:d} (due to `{:s}`)'.format(
                            name, os.path.relpath(filename), lineno, use.modname))
        else:
            print('requirements.txt appears to contain all of the dependencies')


class FindUnusedRequirementsController(cement.Controller):
    """ cement.Controller for finding unused requirements """

    class Meta:
        label = 'find-unused-requirements'
        description = 'Finding unused requirements for a package.'
        help = 'Finding unused requirements for a package.'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['package_name'], dict(
                type=str, help='Package name')),
            (['--dirname'], dict(
                type=str, default='.', help='Path to package')),
        ]

    @cement.ex(hide=True)
    def _default(self):
        args = self.app.pargs
        buildHelper = BuildHelper()
        unuseds = buildHelper.find_unused_requirements(
            args.package_name, dirname=args.dirname)
        if unuseds:
            print('The following requirements from requirements.txt may not be necessary:')
            for name in sorted(unuseds):
                print('  {}'.format(name))
        else:
            print('All of the dependencies appear to be necessary')


class UploadPackageToPypiController(cement.Controller):
    """ Upload package to PyPI
    """

    class Meta:
        label = 'upload-package-to-pypi'
        description = 'Upload package to PyPI'
        help = 'Upload package to PyPI'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['--dirname'], dict(
                type=str, default='.', help='Path to package (e.g. parent directory of setup.py)')),
            (['--repository'], dict(
                type=str, default='pypi', help='Repository upload package (e.g. pypi or testpypi)')),
            (['--do-not-upload-source'], dict(
                default=False, action='store_true', help='if set, do not upload source code to PyPI')),
            (['--do-not-upload-build'], dict(
                default=False, action='store_true', help='if set, do not upload build to PyPI')),
        ]

    @cement.ex(hide=True)
    def _default(self):
        args = self.app.pargs
        buildHelper = BuildHelper()
        buildHelper.upload_package_to_pypi(
            dirname=args.dirname,
            repository=args.repository,
            upload_source=not args.do_not_upload_source,
            upload_build=not args.do_not_upload_build)


class App(cement.App):
    """ Command line application """
    class Meta:
        label = 'karr_lab_build_utils'
        base_controller = 'base'
        handlers = [
            BaseController,
            CreatePackageController,
            CreateRepositoryController,
            SetupRepositoryController,
            CreateDocumentationTemplateController,
            DownloadInstallPackageConfigFilesController,
            RunTestsController,
            DockerController,
            DockerCreateContainerController,
            InstallPackageToDockerContainerController,
            RunTestsInDockerContainerController,
            DockerRemoveContainerController,
            FollowCircleciBuildController,
            GetCircleciEnvironmentVariablesController,
            SetCircleciEnvironmentVariableController,
            DeleteCircleciEnvironmentVariableController,
            CreateCodeClimateGithubWebhookController,
            DoPostTestTasksController,
            MakeAndArchiveReportsController,
            CombineCoverageReportsController,
            ArchiveCoverageReportController,
            UploadCoverageReportToCoverallsController,
            UploadCoverageReportToCodeClimateController,
            MakeDocumentationController,
            CompileDownstreamDependenciesController,
            ArePackageDependenciesAcyclicController,
            VisualizePackageDependenciesController,
            AnalyzePackageController,
            FindMissingRequirementsController,
            FindUnusedRequirementsController,
            UploadPackageToPypiController,
        ]


def main():
    with App() as app:
        app.run()
