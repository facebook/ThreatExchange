# Contributing
Please see [CONTRIBUTING](../CONTRIBUTING.md) for how to make contributions develop locally and open PRs
### Code Style
vPDQ uses [black](https://pypi.org/project/black/) for consistent formatting across
the projects Python source files and clang-format for formatting CPP source files. 
After installing black and clang-format locally, you can automatically format all the vPDQ files by running the following command from the repository root.

```shell
black ./vpdq/
find vpdq/ -iname '*.h' -o -iname '*.cpp' | xargs clang-format -i
```

### Installing Locally
vPDQ has two parts of codes: CPP implementation and python-binding library.
To use vPDQ, ffmpeg is required(https://www.ffmpeg.org/download.html)

To cmake CPP binary files:
```
cd vpdq/cpp/
mkdir -p build
cd build
cmake ..
make
```
To locally install python-binding library:
```
cd vpdq
python vpdq-release.py -i
```

### Running Tests(depends on "Installing Locally")

To run the CPP regression test
```
cd vpdq/cpp/
python regtest.py
```

To run the python-binding library test
```
cd vpdq
py.test
```

## Build local distribution
To create local distribution:
```
cd vpdq
python vpdq-release.py -r
```
The local distribution files are located at vpdq/dist/

## Releasing Changes
Releases of the python-binding library are managed by a [GitHub action](../.github/workflows/vpdq-release.yaml),
triggered by changes to [version.txt](./version.txt). To create a new release to
[PyPI](https://pypi.org/project/vpdq/), update [version.txt](./version.txt)
to the new release name in a PR. Once the PR is approved and merges, the CI process
will publish the new version to PyPI, shortly after a test publish to Test PyPI.
