# Contributing to ThreatExchange
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

## Pull Requests
We actively welcome your pull requests.

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code lints.
6. If you haven't already, complete the Contributor License Agreement ("CLA").

## Contributor License Agreement ("CLA")
In order to accept your pull request, we need you to submit a CLA. You only need
to do this once to work on any of Facebook's open source projects.

Complete your CLA here: <https://code.facebook.com/cla>

## Issues
We use GitHub issues to track public bugs. Please ensure your description is
clear and has sufficient instructions to be able to reproduce the issue.

Facebook has a [bounty program](https://www.facebook.com/whitehat/) for the safe
disclosure of security bugs. In those cases, please go through the process
outlined on that page and do not file a public issue.

## License
By contributing to ThreatExchange, you agree that your contributions will be licensed
under the LICENSE file in the root directory of this source tree.

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