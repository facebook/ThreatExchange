# Overview

vPDQ has a CPP implementation and a Python binding that is created with Cython.

Note: Python scripts are used for testing the CPP implementation, but they do not require the Python binding to be installed. They are located in the [cpp](./cpp) folder.

See the CPP section in the [README](./README.md#cpp-implementation) for how to setup a development environmnet.

## Contributing
Please see [CONTRIBUTING](../CONTRIBUTING.md) for how to make contributions develop locally and open PRs

---

# CPP Development

### Code Style

clang-format is used for formatting CPP source files.

Format with clang-format:
```sh
find cpp/vpdq -iname '*.h' -o -iname '*.cpp' | xargs clang-format -i
```

### Building

See [CPP Development in README](./README.md#building) for build instructions.

### Tests

Run the CPP regression test
```sh
python vpdq/cpp/regtest.py
```

---

# Python Bindings Development

### Code Style

[black](https://pypi.org/project/black/) is used for formatting Python.

Install black:
```sh
python -m pip install black
```

Format all files in `vpdq/`:

```sh
python -m black ./
```

### Dependencies

All dependencies from the CPP implementation are required to build the binding. See [README](./README.md#cpp-implementation) for more information.

Ubuntu may require `python3-dev` to compile the bindings and `pkg-config` packages to compile vpdq.

Creating a [venv](https://docs.python.org/3/library/venv.html) is optional, but recommended during development. See [setuptools documentation](https://setuptools.pypa.io/en/latest/userguide/development_mode.html) for more information.


### Install

In `vpdq/`:
```sh
python install --editable .
```

You should now be able to run `python -c "import vpdq"` without error.

See [setuptools documentation](https://setuptools.pypa.io/en/latest/userguide/development_mode.html) for more information.

### Tests

The tests use sample videos from `ThreatExchange/tmk/sample-videos`

Run the tests:
```sh
python -m pip install pytest
python -m pytest
```

### Distributing

[build](https://github.com/pypa/build) is used for building, packaging, and distributing the Python bindings.

In `vpdq/`:

Install dependencies:
```sh
python -m pip install -r packaging-requirements.txt
```

Build package:
```sh
python -m build --sdist 
```

Build wheel:
```sh
python -m build --wheel
```

The package/wheel should now be in `dist/`.

### Publishing

Releases of the python-binding library are managed by a [GitHub action](../.github/workflows/vpdq-release.yaml), triggered by changes to [version.txt](./version.txt).

To create a new release to [PyPI](https://pypi.org/project/vpdq/), update [version.txt](./version.txt) to the new release name in a PR. Once the PR is approved and merges, the CI process will publish the new version to PyPI, shortly after a test publish to Test PyPI.