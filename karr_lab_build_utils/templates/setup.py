import setuptools
try:
    import setuptools_utils
except ImportError:
    import pip
    pip.main(['install', 'git+https://github.com/KarrLab/setuptools_utils.git#egg=setuptools_utils'])
    import setuptools_utils
import os

name = '{{ name }}'
dirname = os.path.dirname(__file__)

# get package metadata
md = setuptools_utils.get_package_metadata(dirname, name)

# install package
setup(
    name=name,
    version=md.version,
    description=name,
    long_description=md.long_description,
    url="https://github.com/KarrLab/" + name,
    download_url='https://github.com/KarrLab/' + name,
    author="Karr Lab",
    author_email="karr@mssm.com",
    license="MIT",
    keywords='',
    packages=find_packages(exclude=['tests', 'tests.*']),
    package_data={
        name: [
            'VERSION',
        ],
    },
    install_requires=md.install_requires,
    extras_require=md.extras_require,
    tests_require=md.tests_require,
    dependency_links=md.dependency_links,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
    ],
    entry_points={
        'console_scripts': [
        ],
    },
)
