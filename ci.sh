#!/bin/bash
# Run all checks and tests in the ci pipeline
pdm run black  --target-version py310 $(git ls-files '*.py' '.ipynb')
pdm run isort $(git ls-files '*.py')
pdm run pydocstyle $(git ls-files 'cvml/dagster/**/*.py' 'cvml/utils/*.py' 'cvml/models/*.py') --verbose --convention=google --add-ignore=D104
pdm run pylama $(git ls-files '*.py')
pdm run mypy $(git ls-files '*.py')