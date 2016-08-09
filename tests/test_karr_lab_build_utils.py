""" Tests karr_lab_build_utils.

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2017-08-03
:Copyright: 2016, Karr Lab
:License: MIT
"""

from glob import glob
from karr_lab_build_utils.__main__ import App as KarrLabBuildUtilsCli
from karr_lab_build_utils.core import BuildHelper
import shutil
import os
import sys
import tempfile
import unittest

if sys.version_info >= (3, 0, 0):
    from test.support import EnvironmentVarGuard
else:
    from test.test_support import EnvironmentVarGuard


class TestKarrLabBuildUtils(unittest.TestCase):
    PROJECT_NAME = 'Karr-Lab-build-utils'
    COVERALLS_REPO_TOKEN = ''
    DUMMY_TEST = 'tests/test_karr_lab_build_utils.py:TestKarrLabBuildUtils.test_dummy_test'

    @staticmethod
    def construct_build_helper():
        env = EnvironmentVarGuard()
        env.set('CIRCLE_PROJECT_REPONAME', TestKarrLabBuildUtils.PROJECT_NAME)
        env.set('CIRCLE_BUILD_NUM', '0')
        env.set('CIRCLE_ARTIFACTS', tempfile.mkdtemp())
        env.set('CIRCLE_TEST_REPORTS', tempfile.mkdtemp())
        env.set('COVERALLS_REPO_TOKEN', TestKarrLabBuildUtils.COVERALLS_REPO_TOKEN)
        if not os.getenv('CIRCLECI'):
            with open('tests/fixtures/CODE_SERVER_PASSWORD', 'r') as file:
                env.set('CODE_SERVER_PASSWORD', file.read())

        with env:
            buildHelper = BuildHelper()

        return buildHelper

    def test_install_requirements(self):
        buildHelper = self.construct_build_helper()

        """ test API """
        buildHelper.install_requirements()

        """ test CLI """
        with KarrLabBuildUtilsCli(argv=['install-requirements']) as app:
            app.run()

    def test_run_tests(self):
        buildHelper = self.construct_build_helper()

        """ test API """
        latest_full_filename = os.path.join(buildHelper.proj_tests_nose_dir, '{0:s}.{1:s}.xml'.format(
            buildHelper.proj_tests_nose_latest_filename, buildHelper.get_python_version()))
        if os.path.isfile(latest_full_filename):
            os.remove(latest_full_filename)
        if os.path.isfile(buildHelper.proj_cov_filename):
            os.remove(buildHelper.proj_cov_filename)

        buildHelper.run_tests(test_path='tests/test_karr_lab_build_utils.py:TestKarrLabBuildUtils.test_dummy_test',
                              with_xunit=True, with_coverage=True)

        self.assertTrue(os.path.isfile(latest_full_filename))
        self.assertTrue(os.path.isfile('.coverage.{}'.format(buildHelper.get_python_version())))

        """ test CLI """
        argv = ['run-tests', TestKarrLabBuildUtils.DUMMY_TEST, '--with-xunit', '--with-coverage']
        with KarrLabBuildUtilsCli(argv=argv) as app:
            app.run()
            self.assertEqual(TestKarrLabBuildUtils.DUMMY_TEST, app.pargs.test_path)
            self.assertTrue(app.pargs.with_xunit)
            self.assertTrue(app.pargs.with_coverage)

    def test_make_and_archive_reports(self):
        buildHelper = self.construct_build_helper()
        buildHelper.run_tests(test_path='tests/test_karr_lab_build_utils.py:TestKarrLabBuildUtils.test_dummy_test',
                              with_xunit=True, with_coverage=True)

        py_v = buildHelper.get_python_version()
        shutil.copyfile(
            os.path.join(buildHelper.proj_tests_nose_dir, '{0:s}.{1:s}.xml'.format(
                buildHelper.proj_tests_nose_latest_filename, py_v)),
            os.path.join(buildHelper.proj_tests_nose_dir, '{0:d}.{1:s}.xml'.format(10000000000000001, py_v))
        )
        shutil.copyfile(
            os.path.join(buildHelper.proj_tests_nose_dir, '{0:s}.{1:s}.xml'.format(
                buildHelper.proj_tests_nose_latest_filename, py_v)),
            os.path.join(buildHelper.proj_tests_nose_dir, '{0:d}.{1:s}.xml'.format(10000000000000002, py_v))
        )

        """ test API """
        buildHelper.make_and_archive_reports()

        """ test CLI """
        with KarrLabBuildUtilsCli(argv=['make-and-archive-reports']) as app:
            app.run()

    def test_download_nose_test_report_history_from_lab_server(self):
        buildHelper = self.construct_build_helper()

        """ test API """
        buildHelper.download_nose_test_report_history_from_lab_server()

        """ test CLI """
        with KarrLabBuildUtilsCli(argv=['download-nose-test-report-history-from-lab-server']) as app:
            app.run()

    def test_make_test_history_report(self):
        buildHelper = self.construct_build_helper()
        buildHelper.run_tests(test_path='tests/test_karr_lab_build_utils.py:TestKarrLabBuildUtils.test_dummy_test',
                              with_xunit=True, with_coverage=True)

        for report_filename in glob(os.path.join(buildHelper.proj_tests_nose_dir, "[0-9]*.*.xml")):
            os.remove(report_filename)
        shutil.copyfile(
            os.path.join(buildHelper.proj_tests_nose_dir, '{0:s}.{1:s}.xml'.format(
                buildHelper.proj_tests_nose_latest_filename, buildHelper.get_python_version())),
            os.path.join(buildHelper.proj_tests_nose_dir, '{0:d}.{1:s}.xml'.format(
                10000000000000001, buildHelper.get_python_version()))
        )
        shutil.copyfile(
            os.path.join(buildHelper.proj_tests_nose_dir, '{0:s}.{1:s}.xml'.format(
                buildHelper.proj_tests_nose_latest_filename, buildHelper.get_python_version())),
            os.path.join(buildHelper.proj_tests_nose_dir, '{0:d}.{1:s}.xml'.format(
                10000000000000002, buildHelper.get_python_version()))
        )

        """ test API """
        if os.path.isdir(buildHelper.proj_tests_unitth_dir):
            shutil.rmtree(buildHelper.proj_tests_unitth_dir)
        if os.path.isdir(buildHelper.proj_tests_html_dir):
            shutil.rmtree(buildHelper.proj_tests_html_dir)

        buildHelper.make_test_history_report()

        self.assertTrue(os.path.isfile(os.path.join(
            buildHelper.proj_tests_unitth_dir, '{0:d}.{1:s}'.format(10000000000000001, buildHelper.get_python_version()), 'index.html')))
        self.assertTrue(os.path.isfile(os.path.join(
            buildHelper.proj_tests_unitth_dir, '{0:d}.{1:s}'.format(10000000000000002, buildHelper.get_python_version()), 'index.html')))
        self.assertTrue(os.path.isfile(os.path.join(buildHelper.proj_tests_html_dir, 'index.html')))

        """ test CLI """
        with KarrLabBuildUtilsCli(argv=['make-test-history-report']) as app:
            app.run()

    def test_archive_test_reports(self):
        buildHelper = self.construct_build_helper()
        buildHelper.run_tests(test_path='tests/test_karr_lab_build_utils.py:TestKarrLabBuildUtils.test_dummy_test',
                              with_xunit=True, with_coverage=True)

        py_v = buildHelper.get_python_version()

        for report_filename in glob(os.path.join(buildHelper.proj_tests_nose_dir, "[0-9]*.*.xml")):
            os.remove(report_filename)
        shutil.copyfile(
            os.path.join(buildHelper.proj_tests_nose_dir, '{0:s}.{1:s}.xml'.format(
                buildHelper.proj_tests_nose_latest_filename, py_v)),
            os.path.join(buildHelper.proj_tests_nose_dir, '{0:d}.{1:s}.xml'.format(buildHelper.build_num, py_v))
        )
        shutil.copyfile(
            os.path.join(buildHelper.proj_tests_nose_dir, '{0:s}.{1:s}.xml'.format(
                buildHelper.proj_tests_nose_latest_filename, py_v)),
            os.path.join(buildHelper.proj_tests_nose_dir, '{0:d}.{1:s}.xml'.format(10000000000000001, py_v))
        )
        shutil.copyfile(
            os.path.join(buildHelper.proj_tests_nose_dir, '{0:s}.{1:s}.xml'.format(
                buildHelper.proj_tests_nose_latest_filename, py_v)),
            os.path.join(buildHelper.proj_tests_nose_dir, '{0:d}.{1:s}.xml'.format(10000000000000002, py_v))
        )
        buildHelper.make_test_history_report()

        """ test API """
        buildHelper.archive_test_reports()

        """ test CLI """
        with KarrLabBuildUtilsCli(argv=['archive-test-reports']) as app:
            app.run()

    def test_upload_test_reports_to_lab_server(self):
        buildHelper = self.construct_build_helper()
        buildHelper.run_tests(test_path='tests/test_karr_lab_build_utils.py:TestKarrLabBuildUtils.test_dummy_test',
                              with_xunit=True, with_coverage=True)

        py_v = buildHelper.get_python_version()

        for report_filename in glob(os.path.join(buildHelper.proj_tests_nose_dir, "[0-9]*.*.xml")):
            os.remove(report_filename)
        shutil.copyfile(
            os.path.join(buildHelper.proj_tests_nose_dir, '{0:s}.{1:s}.xml'.format(
                buildHelper.proj_tests_nose_latest_filename, py_v)),
            os.path.join(buildHelper.proj_tests_nose_dir, '{0:d}.{1:s}.xml'.format(buildHelper.build_num, py_v))
        )
        shutil.copyfile(
            os.path.join(buildHelper.proj_tests_nose_dir, '{0:s}.{1:s}.xml'.format(
                buildHelper.proj_tests_nose_latest_filename, py_v)),
            os.path.join(buildHelper.proj_tests_nose_dir, '{0:d}.{1:s}.xml'.format(10000000000000001, py_v))
        )
        shutil.copyfile(
            os.path.join(buildHelper.proj_tests_nose_dir, '{0:s}.{1:s}.xml'.format(
                buildHelper.proj_tests_nose_latest_filename, py_v)),
            os.path.join(buildHelper.proj_tests_nose_dir, '{0:d}.{1:s}.xml'.format(10000000000000002, py_v))
        )
        buildHelper.make_test_history_report()

        """ test API """
        with buildHelper.get_connection_to_lab_server() as ftp:
            if ftp.path.isfile(ftp.path.join(buildHelper.serv_tests_nose_dir, '{0:d}.{1:s}.xml'.format(buildHelper.build_num, py_v))):
                ftp.remove(ftp.path.join(buildHelper.serv_tests_nose_dir,
                                         '{0:d}.{1:s}.xml'.format(buildHelper.build_num, py_v)))

            if ftp.path.isfile(ftp.path.join(buildHelper.serv_tests_unitth_dir, '{0:d}.{1:s}'.format(buildHelper.build_num, py_v), 'index.html')):
                ftp.remove(ftp.path.join(buildHelper.serv_tests_unitth_dir,
                                         '{0:d}.{1:s}'.format(buildHelper.build_num, py_v), 'index.html'))

            if ftp.path.isfile(ftp.path.join(buildHelper.serv_tests_html_dir, 'index.html')):
                ftp.remove(ftp.path.join(buildHelper.serv_tests_html_dir, 'index.html'))

        buildHelper.upload_test_reports_to_lab_server()

        with buildHelper.get_connection_to_lab_server() as ftp:
            self.assertTrue(ftp.path.isfile(ftp.path.join(
                buildHelper.serv_tests_nose_dir, '{0:d}.{1:s}.xml'.format(buildHelper.build_num, py_v))))
            self.assertTrue(ftp.path.isfile(ftp.path.join(buildHelper.serv_tests_unitth_dir,
                                                          '{0:d}.{1:s}'.format(buildHelper.build_num, py_v), 'index.html')))
            self.assertTrue(ftp.path.isfile(ftp.path.join(buildHelper.serv_tests_html_dir, 'index.html')))

        """ test CLI """
        with KarrLabBuildUtilsCli(argv=['upload-test-reports-to-lab-server']) as app:
            app.run()

    def test_combine_coverage_reports(self):
        for name in glob('.coverage*'):
            os.remove(name)

        buildHelper = self.construct_build_helper()
        buildHelper.run_tests(test_path='tests/test_karr_lab_build_utils.py:TestKarrLabBuildUtils.test_dummy_test',
                              with_xunit=True, with_coverage=True)
        shutil.move('.coverage.{}'.format(buildHelper.get_python_version()), '.coverage.1')
        shutil.copyfile('.coverage.1', '.coverage.2')

        """ test API """
        if os.path.isfile('.coverage'):
            os.remove('.coverage')
        self.assertTrue(os.path.isfile('.coverage.1'))
        self.assertTrue(os.path.isfile('.coverage.2'))

        buildHelper.combine_coverage_reports()

        self.assertTrue(os.path.isfile('.coverage'))
        self.assertTrue(os.path.isfile('.coverage.1'))
        self.assertTrue(os.path.isfile('.coverage.2'))

        """ test CLI """
        if os.path.isfile('.coverage'):
            os.remove('.coverage')
        self.assertTrue(os.path.isfile('.coverage.1'))
        self.assertTrue(os.path.isfile('.coverage.2'))

        with KarrLabBuildUtilsCli(argv=['combine-coverage-reports']) as app:
            app.run()

        self.assertTrue(os.path.isfile('.coverage'))
        self.assertTrue(os.path.isfile('.coverage.1'))
        self.assertTrue(os.path.isfile('.coverage.2'))

        # cleanup
        os.remove('.coverage.1')
        os.remove('.coverage.2')


    def test_make_html_coverage_report(self):
        buildHelper = self.construct_build_helper()
        buildHelper.run_tests(test_path='tests/test_karr_lab_build_utils.py:TestKarrLabBuildUtils.test_dummy_test',
                              with_xunit=True, with_coverage=True)
        shutil.move('.coverage.{}'.format(buildHelper.get_python_version()), '.coverage')

        """ test API """
        if os.path.isdir(buildHelper.proj_cov_html_dir):
            shutil.rmtree(buildHelper.proj_cov_html_dir)

        buildHelper.make_html_coverage_report()

        self.assertTrue(os.path.isfile(os.path.join(buildHelper.proj_cov_html_dir, 'index.html')))

        """ test CLI """
        with KarrLabBuildUtilsCli(argv=['make-html-coverage-report']) as app:
            app.run()

    def test_archive_coverage_report(self):
        buildHelper = self.construct_build_helper()
        buildHelper.run_tests(test_path='tests/test_karr_lab_build_utils.py:TestKarrLabBuildUtils.test_dummy_test',
                              with_xunit=True, with_coverage=True)

        buildHelper.combine_coverage_reports()
        buildHelper.make_html_coverage_report()

        """ test API """
        buildHelper.archive_coverage_report()

        """ test CLI """
        with KarrLabBuildUtilsCli(argv=['archive-coverage-report']) as app:
            app.run()

    def test_copy_coverage_report_to_artifacts_directory(self):
        buildHelper = self.construct_build_helper()
        buildHelper.run_tests(test_path='tests/test_karr_lab_build_utils.py:TestKarrLabBuildUtils.test_dummy_test',
                              with_xunit=True, with_coverage=True)

        abs_cov_filename = os.path.join(buildHelper.build_artifacts_dir, '.coverage')
        abs_cov_filename_v = os.path.join(buildHelper.build_artifacts_dir, '.coverage.{}'.format(buildHelper.get_python_version()))

        """ test API """
        if os.path.isfile(abs_cov_filename):
            os.remove(abs_cov_filename)
        if os.path.isfile(abs_cov_filename_v):
            os.remove(abs_cov_filename_v)

        buildHelper.copy_coverage_report_to_artifacts_directory()

        self.assertFalse(os.path.isfile(abs_cov_filename))
        self.assertTrue(os.path.isfile(abs_cov_filename_v))

        """ test CLI """
        with KarrLabBuildUtilsCli(argv=['copy-coverage-report-to-artifacts-directory']) as app:
            app.run()

    def test_upload_coverage_report_to_coveralls(self):
        buildHelper = self.construct_build_helper()
        buildHelper.run_tests(test_path='tests/test_karr_lab_build_utils.py:TestKarrLabBuildUtils.test_dummy_test',
                              with_xunit=True, with_coverage=True)

        shutil.move('.coverage.{}'.format(buildHelper.get_python_version()), '.coverage')

        """ test API """
        buildHelper.upload_coverage_report_to_coveralls()

        """ test CLI """
        with KarrLabBuildUtilsCli(argv=['upload-coverage-report-to-coveralls']) as app:
            app.run()

    def test_upload_html_coverage_report_to_lab_server(self):
        buildHelper = self.construct_build_helper()
        buildHelper.run_tests(test_path='tests/test_karr_lab_build_utils.py:TestKarrLabBuildUtils.test_dummy_test',
                              with_xunit=True, with_coverage=True)

        shutil.move('.coverage.{}'.format(buildHelper.get_python_version()), '.coverage')
        buildHelper.make_html_coverage_report()

        """ test API """
        with buildHelper.get_connection_to_lab_server() as ftp:
            if ftp.path.isfile(ftp.path.join(buildHelper.serv_cov_html_dir, 'index.html')):
                ftp.remove(ftp.path.join(buildHelper.serv_cov_html_dir, 'index.html'))

        buildHelper.upload_html_coverage_report_to_lab_server()

        with buildHelper.get_connection_to_lab_server() as ftp:
            self.assertTrue(ftp.path.isfile(ftp.path.join(buildHelper.serv_cov_html_dir, 'index.html')))

        """ test CLI """
        with KarrLabBuildUtilsCli(argv=['upload-html-coverage-report-to-lab-server']) as app:
            app.run()

    def test_make_documentation(self):
        buildHelper = self.construct_build_helper()

        """ test API """
        if os.path.isdir(buildHelper.proj_docs_build_html_dir):
            shutil.rmtree(buildHelper.proj_docs_build_html_dir)

        buildHelper.make_documentation()

        self.assertTrue(os.path.isfile(os.path.join(buildHelper.proj_docs_build_html_dir, 'index.html')))

        """ test CLI """
        with KarrLabBuildUtilsCli(argv=['make-documentation']) as app:
            app.run()

    def test_archive_documentation(self):
        """ setup """
        buildHelper = self.construct_build_helper()
        buildHelper.make_documentation()

        """ test API """
        with buildHelper.get_connection_to_lab_server() as ftp:
            if ftp.path.isfile(ftp.path.join(buildHelper.serv_docs_build_html_dir, 'index.html')):
                ftp.remove(ftp.path.join(buildHelper.serv_docs_build_html_dir, 'index.html'))

        buildHelper.archive_documentation()

        with buildHelper.get_connection_to_lab_server() as ftp:
            self.assertTrue(ftp.path.isfile(ftp.path.join(buildHelper.serv_docs_build_html_dir, 'index.html')))

        """ test CLI """
        with KarrLabBuildUtilsCli(argv=['archive-documentation']) as app:
            app.run()

    def test_upload_documentation_to_lab_server(self):
        """ setup """
        buildHelper = self.construct_build_helper()
        buildHelper.make_documentation()

        """ test API """
        with buildHelper.get_connection_to_lab_server() as ftp:
            if ftp.path.isfile(ftp.path.join(buildHelper.serv_docs_build_html_dir, 'index.html')):
                ftp.remove(ftp.path.join(buildHelper.serv_docs_build_html_dir, 'index.html'))

        buildHelper.upload_documentation_to_lab_server()

        with buildHelper.get_connection_to_lab_server() as ftp:
            self.assertTrue(ftp.path.isfile(ftp.path.join(buildHelper.serv_docs_build_html_dir, 'index.html')))

        """ test CLI """
        with KarrLabBuildUtilsCli(argv=['upload-documentation-to-lab-server']) as app:
            app.run()

    def test_dummy_test(self):
        buildHelper = self.construct_build_helper()
