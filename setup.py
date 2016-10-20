from setuptools import setup, find_packages
import karr_lab_build_utils
import re
import os
import sys

# parse requirements.txt
install_requires = []
dependency_links = []
for line in open('requirements.txt'):
    pkg_src = line.rstrip()
    match = re.match('^git\+git://github.com/.*?/.*?\.git#egg=(.*?)$', pkg_src)
    if match:
        pkg_id = match.group(1)

        pkg_src = pkg_src.replace('git+git://github.com/', 'https://github.com/')
        pkg_src = pkg_src.replace('.git', '/tarball/master')
        pkg_src = pkg_src.replace('>=', '-')
        dependency_links.append(pkg_src)
    else:
        pkg_id = pkg_src
    install_requires.append(pkg_id)

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
    dependency_links=dependency_links,
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
