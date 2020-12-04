# Contributing

If you would like to contribute to python-threatexchange, you can do the following:

[Fork][fork] the repo and then [clone][clone] it locally:

[fork]: https://help.github.com/articles/fork-a-repo/
[clone]: https://help.github.com/articles/which-remote-url-should-i-use/

    git clone git@github.com:your-username/ThreatExchange

## Branch locally and develop!
Make a branch in your cloned fork. We suggest naming the branch by feature name
or “issue_XX” where XX is the issue number the branch is associated with. Make
your changes in your branch and test thoroughly. If this is a large feature you
can push your branch to your fork often. This allows you to request feedback for
how things are progressing instead of dumping a large code change all at once.

When making commits to your branch, make sure you write [well-formed][wf] commit
messages and update documentation accordingly (see the next section).

[wf]: https://github.com/erlang/otp/wiki/Writing-good-commit-messages

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

## Documenting Changes
It is important to keep documentation up-to-date. Make sure to add and update
docstrings where appropriate.

## Submit a PR
Once you are happy with your changes and ready for a PR, you can submit a PR to
the main project. In most cases you’ll be looking to compare against the Master
branch, but there are instances where you’re making changes that you want to go
into a specific branch. Make sure when submitting your PR that you choose the
right destination branch.

Once you’ve submitted a PR you're waiting on us. In most cases we like to have
a core developer get some eyes on the code and the feature to make sure
there’s no general issues. They might require you to go back and make some more
changes (simply edit your local branch and push to the branch associated with
the PR; it will get updated automagically!) .

## Releasing Changes
Releases of the library are managed by a [GitHub action](../.github/workflows/python-threatexchange-release.yaml),
triggered by changes to [version.txt](./version.txt). To create a new release to
[PyPI](https://pypi.org/project/threatexchange/), update [version.txt](./version.txt)
to the new release name in a PR. Once the PR is approved and merges, the CI process
will publish the new version to PyPI, shortly after a test publish to Test PyPI.
