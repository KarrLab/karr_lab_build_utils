import setuptools
try:
    import pkg_utils
except ImportError:
    import pip._internal
    pip._internal.main(['install', 'pkg_utils'])
    import pkg_utils
import os
import sys

name = 'karr_lab_build_utils'
dirname = os.path.dirname(__file__)
package_data = {
    name: [
        'VERSION',
        'templates/*',
        'templates/**/*',
        'config/*.cfg',
    ],
}

# get package metadata
md = pkg_utils.get_package_metadata(dirname, name, package_data_filename_patterns=package_data)

# read old console scripts
console_scripts = pkg_utils.get_console_scripts(dirname, name)

# install package
setuptools.setup(
    name=name,
    version=md.version,
    description="Karr Lab build utilities",
    long_description=md.long_description,
    url="https://github.com/KarrLab/" + name,
    download_url='https://github.com/KarrLab/' + name,
    author="Karr Lab",
    author_email="info@karrlab.org",
    license="MIT",
    keywords='unit test coverage API documentation nose xunit junit unitth HTML Coveralls Sphinx',
    packages=setuptools.find_packages(exclude=['tests', 'tests.*']),
    package_data=md.package_data,
    install_requires=md.install_requires,
    extras_require=md.extras_require,
    tests_require=md.tests_require,
    dependency_links=md.dependency_links,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
    ],
    entry_points={
        'console_scripts': [
            '{} = {}.__main__:main'.format(name, name),
            '{} = {}.__main__:main'.format(name.replace('_', '-'), name),
            '{}{:d} = {}.__main__:main'.format(name, sys.version_info[0], name),
            '{}{:d} = {}.__main__:main'.format(name.replace('_', '-'), sys.version_info[0], name),
        ],
    },
)

# restore old console scripts
pkg_utils.add_console_scripts(dirname, name, console_scripts)
