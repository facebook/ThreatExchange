# Contributing
Please see [CONTRIBUTING](../CONTRIBUTING.md) for how to make contributions develop locally and open PRs

## Code Style
threatexchange uses [black](https://PyPI.org/project/black/) for consistent formatting across
the projects python source files. After installing black locally, you can automatically
format all the python-threatexchange files by running the following command from the repository root.

```shell
black ./python-threatexchange/
```

Additionally, your IDE may have support for automatically re-formatting your source files
using black through your IDE settings.

When in doubt, follow the style of the file you are editing, and if starting new files, be consistent within.

## python typing and `mypy`
We are aiming for full strict coverage via PEP484 typing annotations. However, this is a work in progress. We use [mypy](https://mypy.readthedocs.io/en/stable/index.html) to do typechecking.

### `# type: ignore`
We are not all typing experts yet, and we've confused ourselves with Generics, Aliases and object hierarchies, and occasionally `# type: ignored`. If you end up in a sticky situation and decide to throw in the towel on typing and use `# type: ignore`, use `mypy --show-error-codes` to only ignore the specific error code, and expect discussion on the PR on the level of effort needed to make the code compliant.

### New Files or Directories
When creating new files or directories, please first try and make them compatible with `--strict` to do this, add in the mypy.ini file
```
[path.to.module]
strict = True
```
Read more about mypy configuration [here](https://mypy.readthedocs.io/en/stable/config_file.html#config-file).

## Tests
python-threatexchange uses [pytest](https://docs.pytest.org/en/7.1.x/) for unittesting. From the root python-threatexchange directory use 
```shell
py.test
```
to run tests.

### Writing Tests
New functionality should have unittests. Core functionality like SignalType and SignalExchangeAPI have good examples of tests in their various directories.

We prefer tests to live in their own files in the /tests/ directory where the code under test is. 

### Skipped Tests
Many tests rely on extensions that are not installed by default when you install `threatexchange`. It is okay to submit a PR without running skipped tests, they will be run by workflow. If you find out that tests are failing, you can follow the instructions in the extensions directories to install the needed dependencies, which will make the tests runnable locally.

### Installing Locally
A quick way to iterate on the script is to simply install it locally. The
fastest way to do this is

    cd ThreatExchange/python-threatexchange
    make package
    make local_install
    threatexchange --help

## Releasing A New PyPI version
Releases of the library are managed by a [GitHub action](../.github/workflows/python-threatexchange-release.yaml), which are triggered by changes to [version.txt](./version.txt). 

Version releases should be in a PR on their own, and not included with functional changes.

To create a new release to [PyPI](https://PyPI.org/project/threatexchange/), update [version.txt](./version.txt)
to the new release name in a PR. Once the PR is approved and merged, the CI process
will publish the new version to [PyPI](https://PyPI.org/), shortly after a test publish to Test PyPI.

### PyPI test instance versions
We sometimes do release candidate previews to the PyPI test instance. If you have the credentials for the threatexchange account, you can build and release a test package by heading to the python-threatexchange root directory and do:

```shell
$ make clean
$ make package
$ make push
```

## Extensions
We will only rarely add new extensions, which require additional dependencies, and are not enabled by default. We encourage authors to write and own their own extensions! Feel free to create PR's to add your own extensions to the list of known ones in the README.

# Writing Pull Requests
Thank you for considering writing improvements to the library! We accept pull requests! Developers on the project tend to use fork repos, rather than development branches. A good writeup of this flow [lives here](https://gist.github.com/Chaser324/ce0505fbed06b947d962).

## Before Submitting a PR
Make sure to run all the local tests and linters. They should complete quickly:

```shell
# From the python-threatexchange root directory
$ black .
$ python -m mypy threatexchange
$ py.test
```

## Draft Reviews and RFC
If you are not sure about a potential change, and want to get feedback on a review, you can still submit a PR as a draft PR, or clearly label the PR with "[RFC]" (request for comment). Reviewers will know not to merge your changes but may still send you an Accept if they would merge it without changes (or use "Request Changes" to indicate the same thing, just that they want you to convert from draft).

## Github Actions & Lints
All GitHub action failures are actionable, and reviewers will not merge your code until they are all green. You can get a review even if a lint is failing but expect a "Request Changes" even if everything else looks perfect.

## During the Review
Feel free to request specific reviewers, but any member of the threatexchange team may review your PR. You only need one "approval" even if multiple people have commented or reviewed your changes. 

Depending on the reviewer, you may also see some annotations in the comments:
* blocking: This indicates that there is a change that the reviewer would not accept the PR without further discussion. This may not mean that there is anything wrong with your code, just that the reviewer is uncertain (you will sometimes see 'blocking question:' used similarly.
* nit: This may be a stylistic preference or minor efficiency in the code that does not affect the correctness. Most reviewers will still accept code if you feel strongly about the current form (though it can help to explain why you think it is better).
* ignorable: This comment is explicitly not blocking.
* alt/code golf: The reviewer is providing an alternative implementation that might be shorter or have a stylistic difference. These are always ignorable if you prefer the way you wrote it originally.

## Resolving Conversations
Standard practice is to let the commentor who created a comment thread, or another reviewer "resolve conversations" after you’ve responded to or addressed the issue. Reviewers may un-resolve conversations they think still need discussion. 

## Clearing Reviews After Response
Sometimes Github will still show "Changes Requested" even if you have responded to all changes (or interactions with conversation resolution). Please [dismiss reviews with changes requested](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/reviewing-changes-in-pull-requests/dismissing-a-pull-request-review) that are stuck in "Requested Changes" once you think you have addressed everything.

## Acceptance & Merging
For general members of the public, your reviewer will merge your change as soon as they believe it is good enough, even though they may have outstanding nits/comments on your PR that you may want to respond to. You can do a follow-up PR to do cleanup, or if you prefer to respond to every comment, you can leave your PR in "draft" and only convert it once you have it in the exact state you want.

### Authors with merge access
For threatexchange members with merge ability, we general allow the author to respond to any final comments, make final tweaks, and merge on their own once the PR is accepted. This includes a degree of trust that you aren't adding something that the author would probably want further discussion on. With great power there must also come great responsibility!
