# Contributing

If you would like to contribute to vPDQ, you can do the following:

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
vPDQ uses [black](https://pypi.org/project/black/) for consistent formatting across
the projects Python source files and clang-format for formating CPP source files. 
After installing black and clang-format locally, you can automatically format all the vpdq files by running the following command from the repository root.

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

## Documenting Changes
It is important to keep documentation up-to-date. Make sure to add and update
docstrings where appropriate.

## Submit a PR
Once you are happy with your changes and ready for a PR, you can submit a PR to
the main project. In most cases you’ll be looking to compare against the Main
branch, but there are instances where you’re making changes that you want to go
into a specific branch. Make sure when submitting your PR that you choose the
right destination branch.

Once you’ve submitted a PR you're waiting on us. In most cases we like to have
a core developer get some eyes on the code and the feature to make sure
there’s no general issues. They might require you to go back and make some more
changes (simply edit your local branch and push to the branch associated with
the PR; it will get updated automagically!) .

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
