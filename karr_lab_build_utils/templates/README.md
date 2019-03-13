[//]: # ( [![PyPI package](https://img.shields.io/pypi/v/{{ name }}.svg)](https://pypi.python.org/pypi/{{ name }}) )
{% if private %}[![Documentation](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://docs.karrlab.org/{{ name }}){% else %}[![Documentation](https://readthedocs.org/projects/{{ name|replace("_", "-") }}/badge/?version=latest)](https://docs.karrlab.org/{{ name }}){% endif %}
[![Test results](https://circleci.com/gh/KarrLab/{{ name }}.svg?style=shield{% if private %}&circle-token={{ circleci_repo_token }}{% endif %})](https://circleci.com/gh/KarrLab/{{ name }})
[![Test coverage](https://coveralls.io/repos/github/KarrLab/{{ name }}/badge.svg{% if private %}?t={{ coveralls_repo_badge_token }}{% endif %})](https://coveralls.io/github/KarrLab/{{ name }})
[![Code analysis](https://api.codeclimate.com/v1/badges/{{ code_climate_repo_badge_token }}/maintainability)]({% if private %}https://codeclimate.com/repos/{{ code_climate_repo_id }}){% else %}https://codeclimate.com/github/KarrLab/{{ name }}{% endif %})
[![License](https://img.shields.io/github/license/KarrLab/{{ name }}.svg)](LICENSE)
![Analytics](https://ga-beacon.appspot.com/UA-86759801-1/{{ name }}/README.md?pixel)

# {{ name }}

Write an overview

## Installation
1. Install dependencies
2. Install the latest release from PyPI
  ```
  pip install {{ name }}.git[all]
  ```
3. Install the latest revision from GitHub
  ```
  pip install git+https://github.com/KarrLab/{{ name }}.git#egg={{ name }}[all]
  ```

## Documentation
Please see the [API documentation](https://docs.karrlab.org/{{ name }}).

## License
The package is released under the [MIT license](LICENSE).

## Development team
This package was developed by the [Karr Lab](https://www.karrlab.org) at the Icahn School of Medicine at Mount Sinai in New York, USA.

## Questions and comments
Please contact the [Karr Lab](https://www.karrlab.org) with any questions or comments.
