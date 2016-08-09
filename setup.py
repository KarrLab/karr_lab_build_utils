from setuptools import setup, find_packages
import karr_lab_build_utils
import os
import sys

# parse requirements.txt
install_requires = [line.rstrip() for line in open('requirements.txt')]

setup(
    name="Karr-Lab-build-utils",
    version=karr_lab_build_utils.__version__,
    description="Karr Lab build utilities",
    url="https://github.com/KarrLab/Karr-Lab-build-utils",
    download_url='https://github.com/KarrLab/Karr-Lab-build-utils/tarball/{}'.format(karr_lab_build_utils.__version__),
    author="Jonathan Karr",
    author_email="jonrkarr@gmail.com",
    license="MIT",
    keywords='unit test coverage API documentation nose xunit junit unitth HTML Coveralls Sphinx',
    packages=find_packages(exclude=['tests', 'tests.*']),
    package_data={
        'karr_lab_build_utils': ['lib'],
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
            'karr-lab-build-utils = karr_lab_build_utils.__main__:main',
            'karr-lab-build-utils-{:d} = karr_lab_build_utils.__main__:main'.format(sys.version_info[0]),
            ],
    },
)
