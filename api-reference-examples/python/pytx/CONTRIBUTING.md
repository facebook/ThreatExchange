# Contributing

If you would like to contribute to pytx, you can do the following:

[Fork][fork] the repo and then [clone][clone] it locally:

[fork]: https://help.github.com/articles/fork-a-repo/
[clone]: https://help.github.com/articles/which-remote-url-should-i-use/

    git clone git@github.com:your-username/ThreatExchange

## Branch locally and develop!
Make a branch in your cloned fork. We suggest naming the branch by feature name
or “issue_XX” where XX is the issue number the branch is associated with. Make
your changes in your branch and test thoroughly. If this is a large feature you
can push your branch to your fork often. This allows you to request feedback for how things are progressing instead of dumping a large code change all at once.

When making commits to your branch, make sure you write [well-formed][wf] commit messages and update documentation accordingly (see the next section).

[wf]: https://github.com/erlang/otp/wiki/Writing-good-commit-messages

### pre-commit
pytx uses [pre-commit] to ensure the code aligns with PEP-8 and passes some basic python linting.

After building a virtualenv to do development work out of you wanna `pre-commit install` one time.

After that, whenever you commit, pre-commit will run and either fix up minor issues in your files or let you know about them. Fix the issues, stage the files, and then commit again. Once there are no issues, the commit will succeed. To skip the checks, use `git commit --no-verify`

But `--no-verify` is so uncool.

### Running Tests
pytx is a bit short on tests, but you could help fix that.
To run the tests `make test`

## Documenting Changes
It is important to keep documentation up-to-date. Make sure to add and update
docstrings where appropriate. If the additions/changes require updates to the
documentation in the `docs` directory, make sure to change those as well.

The `docs` directory uses Sphinx and `rst` format for generating documentation.
If you are making any documentation-related changes, you can locally generate
the documentation by running `make docs`. This will create a `build/docs` directory with all of the content. You can open the generated `index.html` file with a browser and see what it looks like.

Once the documentation makes it to the main repo's Main branch,
[readthedocs][rd] will pick it up and build it automatically.

[rd]: https://pytx.readthedocs.org/en/latest/index.html

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
the PR; it will get updated automagically!).
