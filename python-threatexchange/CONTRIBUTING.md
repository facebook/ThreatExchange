# Contributing
Please see [CONTRIBUTING](../CONTRIBUTING.md) for how to make contributions develop locally and open PRs
### Code Style
threatexchange uses [black](https://pypi.org/project/black/) for consistent formatting across
the projects python source files. After installing black locally, you can automatically
format all the python-threatexchange files by running the following command from the repository root.

```shell
black ./python-threatexchange/
```

Additionally, your IDE may have support for automatically re-formatting your source files
using black through your IDE settings.

### Running Tests
python-threatexchange is a bit short on tests, but you could help fix that.
To run the tests `make test`

### Installing Locally
A quick way to iterate on the script is to simply install it locally. The
fastest way to do this is

    cd ThreatExchange/python-threatexchange
    make package
    make local_install
    threatexchange --help

## Releasing Changes
Releases of the library are managed by a [GitHub action](../.github/workflows/python-threatexchange-release.yaml),
triggered by changes to [version.txt](./version.txt). To create a new release to
[PyPI](https://pypi.org/project/threatexchange/), update [version.txt](./version.txt)
to the new release name in a PR. Once the PR is approved and merges, the CI process
will publish the new version to PyPI, shortly after a test publish to Test PyPI.
