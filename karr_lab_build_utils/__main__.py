from cement.core.foundation import CementApp
from cement.core.controller import CementBaseController, expose
from karr_lab_build_utils.core import BuildHelper
import karr_lab_build_utils
import sys


class BaseController(CementBaseController):
    """ Base controller for command line application """

    class Meta:
        label = 'base'
        description = "Karr Lab build utilities"

    @expose(help='Archive coverage report')
    def archive_coverage_report(self):
        """ Archive a coverage report:

        * Copy report to artifacts directory
        * Upload report to Coveralls and Code Climate
        """
        buildHelper = BuildHelper()
        buildHelper.archive_coverage_report()

    @expose(help='Archive documentation')
    def archive_documentation(self):
        """ Save documentation to artifacts directory """
        buildHelper = BuildHelper()
        buildHelper.archive_documentation()

    @expose(help='Archive test report')
    def archive_test_report(self):
        """ Upload test report to history server """
        buildHelper = BuildHelper()
        buildHelper.archive_test_report()

    @expose(help='Combine coverage reports (.coverage.*) into a single file (.coverage)')
    def combine_coverage_reports(self):
        """ Combine coverage reports """
        buildHelper = BuildHelper()
        buildHelper.combine_coverage_reports()

    @expose(help='Copy coverage report to CircleCI artifacts directory')
    def copy_coverage_report_to_artifacts_directory(self):
        """ Copy coverage report to CircleCI artifacts directory """
        buildHelper = BuildHelper()
        buildHelper.copy_coverage_report_to_artifacts_directory()

    @expose(help='Create CircleCI build for the current repository')
    def create_circleci_build(self):
        """ Create CircleCI build for the current repository """
        buildHelper = BuildHelper()
        buildHelper.create_circleci_build()

    @expose(help='Install requirements')
    def install_requirements(self):
        """ Install requirements """
        buildHelper = BuildHelper()
        buildHelper.install_requirements()

    @expose(help='Make and archive reports')
    def make_and_archive_reports(self):
        """ Make and archive reports:

        * Generate HTML test history reports
        * Generate HTML API documentation
        * Archive coverage report to Coveralls and Code Climate
        """
        buildHelper = BuildHelper()
        buildHelper.make_and_archive_reports()

    @expose(help='Make HTML coverage report')
    def make_documentation(self):
        """ Make HTML documentation """
        buildHelper = BuildHelper()
        buildHelper.make_documentation()

    @expose(help='Upload coverage report to Coveralls')
    def upload_coverage_report_to_coveralls(self):
        """ Upload coverage report to Coveralls """
        buildHelper = BuildHelper()
        buildHelper.upload_coverage_report_to_coveralls()

    @expose(help='Upload coverage report to Code Climate')
    def upload_coverage_report_to_code_climate(self):
        """ Upload coverage report to Code Climate """
        buildHelper = BuildHelper()
        buildHelper.upload_coverage_report_to_code_climate()

    @expose(help='Get version')
    def get_version(self):
        """ Get version """
        buildHelper = BuildHelper()
        print(buildHelper.get_version())


class RunTestsController(CementBaseController):
    """ Controller for run_tests.

    Run unit tests located at `test-path`. 
    Optionally, generate a coverage report. 
    Optionally, save the results to an XML file.
    """

    class Meta:
        label = 'run-tests'
        description = 'Run unit tests located at `test_path`'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['test_path'], dict(
                default='tests', type=str, help='path to tests that should be run')),
            (['--with-xunit'], dict(
                default=False, dest='with_xunit', action='store_true', help='True/False to save test results to XML file')),
            (['--with-coverage'], dict(
                default=False, dest='with_coverage', action='store_true', help='True/False to assess code coverage')),
        ]

    @expose(hide=True)
    def default(self):
        args = self.app.pargs
        buildHelper = BuildHelper()
        buildHelper.run_tests(test_path=args.test_path, with_xunit=args.with_xunit, with_coverage=args.with_coverage)


class App(CementApp):
    """ Command line application """
    class Meta:
        label = 'karr-lab-build-utils'
        base_controller = 'base'
        handlers = [
            BaseController,
            RunTestsController,
        ]


def main():
    with App() as app:
        app.run()

if __name__ == '__main__':
    main()
