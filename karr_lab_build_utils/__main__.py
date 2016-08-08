import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from cement.core.foundation import CementApp
from cement.core.controller import CementBaseController, expose
from karr_lab_build_utils.core import BuildHelper


class BaseController(CementBaseController):

    class Meta:
        label = 'base'
        description = "Karr Lab build utilities"

    @expose(help='Archive coverage report')
    def archive_coverage_report(self):
        """ Archive a coverage report:
        * Copy report to artifacts directory
        * Upload report to Coveralls
        * Upload HTML report to lab server
        """
        buildHelper = BuildHelper()
        buildHelper.archive_coverage_report()

    @expose(help='Archive documentation')
    def archive_documentation(self):
        """ Archive documentation:
        * Upload documentation to lab server
        """
        buildHelper = BuildHelper()
        buildHelper.archive_documentation()

    @expose(help='Archive test reports')
    def archive_test_reports(self):
        """ Archive test report:
        * Upload XML and HTML test reports to lab server
        """
        buildHelper = BuildHelper()
        buildHelper.archive_test_reports()

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

    @expose(help='Download XML test report history from lab server')
    def download_nose_test_report_history_from_lab_server(self):
        """ Download XML test report history from lab server """
        buildHelper = BuildHelper()
        buildHelper.download_nose_test_report_history_from_lab_server()

    @expose(help='Install requirements')
    def install_requirements(self):
        """ Install requirements """
        buildHelper = BuildHelper()
        buildHelper.install_requirements()

    @expose(help='Make and archive reports')
    def make_and_archive_reports(self):
        """ Make and archive reports;
        * Generate HTML test history reports
        * Generate HTML coverage reports
        * Generate HTML API documentation
        * Archive coverage report to Coveralls
        * Archive HTML coverage report to lab server
        """
        buildHelper = BuildHelper()
        buildHelper.make_and_archive_reports()

    @expose(help='Make HTML coverage report')
    def make_documentation(self):
        """ Make HTML documentation """
        buildHelper = BuildHelper()
        buildHelper.make_documentation()

    @expose(help='Make HTML coverage report')
    def make_html_coverage_report(self):
        """ Make HTML coverage report from .coverage file """
        buildHelper = BuildHelper()
        buildHelper.make_html_coverage_report()

    @expose(help='Make HTML test history report')
    def make_test_history_report(self):
        """ Make HTML test history report """
        buildHelper = BuildHelper()
        buildHelper.make_test_history_report()

    @expose(help='Upload coverage report to Coveralls')
    def upload_coverage_report_to_coveralls(self):
        """ Upload coverage report to Coveralls """
        buildHelper = BuildHelper()
        buildHelper.upload_coverage_report_to_coveralls()

    @expose(help='Upload documentation to lab server')
    def upload_documentation_to_lab_server(self):
        """ Upload documentation to lab server """
        buildHelper = BuildHelper()
        buildHelper.upload_documentation_to_lab_server()

    @expose(help='Upload HTML coverage report to lab server')
    def upload_html_coverage_report_to_lab_server(self):
        """ Upload HTML coverage report to lab server """
        buildHelper = BuildHelper()
        buildHelper.upload_html_coverage_report_to_lab_server()

    @expose(help='Upload XML and HTML test reports to lab server')
    def upload_test_reports_to_lab_server(self):
        """ Upload XML and HTML test reports to lab server """
        buildHelper = BuildHelper()
        buildHelper.upload_test_reports_to_lab_server()


class RunTestsController(CementBaseController):
    """ Run unit tests located at `test-path`. 
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
