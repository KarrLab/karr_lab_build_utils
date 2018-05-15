[//]: # ( [![PyPI package](https://img.shields.io/pypi/v/{{ name }}.svg)](https://pypi.python.org/pypi/{{ name }}) )
{% if private %}[![Documentation](https://img.shields.io/badge/docs-latest-brightgreen.svg)](http://docs.karrlab.org/{{ name }}){% else %}[![Documentation](https://readthedocs.org/projects/{{ name|replace("_", "-") }}/badge/?version=latest)](http://docs.karrlab.org/{{ name }}){% endif %}
[![Test results](https://circleci.com/gh/KarrLab/{{ name }}.svg?style=shield&circle-token={{ circleci_repo_token }})](https://circleci.com/gh/KarrLab/{{ name }})
[![Test coverage](https://coveralls.io/repos/github/KarrLab/{{ name }}/badge.svg?t={{ coveralls_repo_badge_token }})](https://coveralls.io/github/KarrLab/{{ name }})
[![Code analysis](https://api.codeclimate.com/v1/badges/{{ codeclimate_repo_badge_token }}/maintainability)]({% if private %}https://codeclimate.com/repos/{{ codeclimate_repo_id }}){% else %}https://codeclimate.com/github/KarrLab/{{ name }}{% endif %})
[![License](https://img.shields.io/github/license/KarrLab/{{ name }}.svg)](LICENSE)
![Analytics](https://ga-beacon.appspot.com/UA-86759801-1/{{ name }}/README.md?pixel)

# {{ name }}

Write an overview

## Installation
1. Install dependencies
2. Install this package 
  ```
  pip install git+git://github.com/KarrLab/{{ name }}#egg={{ name }}
  ```

## Documentation
Please see the [API documentation](http://docs.karrlab.org/{{ name }}).

## License
The package is released under the [MIT license](LICENSE).

## Development team
This package was developed by the [Karr Lab](http://www.karrlab.org) at the Icahn School of Medicine at Mount Sinai in New York, USA.

## Questions and comments
Please contact the [Karr Lab](http://www.karrlab.org) with any questions or comments.
