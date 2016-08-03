from pip.req import parse_requirements
from setuptools import setup
import os

# version
version = '0.0.1'

# parse requirements.txt
requirements = parse_requirements('requirements.txt')
install_requires = [str(ir.req) for ir in requirements]

setup(
    name="Karr-Lab-build-utils",
    version=version,
    description="Karr Lab build utilities",
    url="https://github.com/KarrLab/Karr-Lab-build-utils",
    download_url='https://github.com/KarrLab/Karr-Lab-build-utils/tarball/%s' % version,
    author="Jonathan Karr",
    author_email="jonrkarr@gmail.com",
    license="MIT",
    keywords='unit test coverage API documentation nose xunit junit unitth HTML Coveralls Sphinx',
    packages=["karr_lab_build_utils"],
    package_data={
        'karr_lab_build_utils': 'lib',
    },
    install_requires=install_requires,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
    ],
    entry_points={
        'console_scripts': [
            'karr-lab-build-utils-install-requirements = karr_lab_build_utils.bin.install_requirements:main',
            'karr-lab-build-utils-run-tests = karr_lab_build_utils.bin.run_tests:main',
            'karr-lab-build-utils-make-and-archive-reports = karr_lab_build_utils.bin.make_and_archive_reports:main',
            'karr-lab-build-utils-make-test-history-report = karr_lab_build_utils.bin.make_test_history_report:main',
            'karr-lab-build-utils-run-download-nose-test-report-history-from-lab-server = karr_lab_build_utils.bin.download_nose_test_report_history_from_lab_server:main',
            'karr-lab-build-utils-archive-test-reports = karr_lab_build_utils.bin.archive_test_reports:main',
            'karr-lab-build-utils-upload-test-reports-to-lab-server = karr_lab_build_utils.bin.upload_test_reports_to_lab_server:main',
            'karr-lab-build-utils-make-html-coverage-report = karr_lab_build_utils.bin.make_html_coverage_report:main',
            'karr-lab-build-utils-archive-coverage-report = karr_lab_build_utils.bin.archive_coverage_report:main',
            'karr-lab-build-utils-copy-coverage-report-to-artifacts-directory = karr_lab_build_utils.bin.copy_coverage_report_to_artifacts_directory:main',
            'karr-lab-build-utils-upload-coverage-report-to-coveralls = karr_lab_build_utils.bin.upload_coverage_report_to_coveralls:main',
            'karr-lab-build-utils-upload-html-coverage-report-to-lab-server = karr_lab_build_utils.bin.upload_html_coverage_report_to_lab_server:main',
            'karr-lab-build-utils-make-documentation = karr_lab_build_utils.bin.make_documentation:main',
            'karr-lab-build-utils-archive-documentation = karr_lab_build_utils.bin.archive_documentation:main',
            'karr-lab-build-utils-upload-documentation-to-lab-server = karr_lab_build_utils.bin.upload_documentation_to_lab_server:main',
        ],
    },
)
