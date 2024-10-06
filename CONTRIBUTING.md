# Repo Organization and project-level CONTRIBUTING.md
This repository is organized as a collection of sub-projects, some of which reference each other. 
This explainer is about the entire repository, but there are more specific notes for how to
develop on subprojects in the various directories that contain them.

# Issues
We use GitHub issues to track public bugs. Please ensure your description is
clear and has sufficient instructions to be able to reproduce the issue.

Facebook has a [bounty program](https://www.facebook.com/whitehat/) for the safe
disclosure of security bugs. In those cases, please go through the process
outlined on that page and do not file a public issue.

# Contributing to facebook/ThreatExchange
## Get the code, Set up a fork
We prefer people use forks to develop on this repo, and do not accept development branches.

Here's an easy way to get started:

[Clone](https://help.github.com/articles/which-remote-url-should-i-use/) facebook/ThreatExchange.

   git clone git@github.com:your-username/ThreatExchange

Next, [fork]([fork](https://help.github.com/articles/fork-a-repo/) your own copy of the repo. 
Here's where you'll push development branches. Note the name, we'll need it in the next step.

Next, we'll add your forked copy as a remote.

    # From the root directory of your locally cloned repo
    git remote add fork git@github.com:<USUALLY_YOUR_USERNAME>/ThreatExchange 

Lastly, we'll add the fork as the preferred repo to push to

    # From the root directory of your locally cloned repo
     git config --global push.default fork

This will give you an easy develoment cycle for updating your copy:

    git co main  # co is a common shortcut for `checkout`
    git pull  # Get all the new commits from the upstream

If you are a git expert, you likely know of other ways to set this up, to your preference!

## Branch locally and develop!
First, make a branch in your cloned fork. 

    git co -b <MY_COOL_FEATURE_BRANCH_NAME>

We suggest naming the branch by feature name
or “issue_XX” where XX is the issue number the branch is associated with. Make
your changes in your branch and test thoroughly. 

    git commit -am "[hma] Made cool changes to hasher-matcher-actioner"
    git push  # Pushes to your fork if you followed the setup!

If this is a large feature you can push your branch to your fork often to save your work. 
When making commits to your branch, make sure you write [well-formed][wf] commit
messages and update documentation accordingly (see the next section).

[wf]: https://github.com/erlang/otp/wiki/Writing-good-commit-messages

## Making Big Changes
If you are considering making a larger change, consider reaching out via an issue first.
If your change will add a new API, new functionality, or refactor a large section of code,
it's best to socialize your intent first and get some feedback. Maintainers can let you know
if there are some concerns about the change (e.g. some projects deliberately minimize the number
of dependencies - if you are planning on pulling Node.js into a project, it's unlikely to be 
accepted! 

This is also a place where maintainers can give you pointers on what they'll be looking for in
testing. 

Don't let this step dissuade you, we want to work with you to help you figure out the best
solution. If we ultimately don't believe we can support it in the main repo, you are welcome
to develop it in a fork, and tried to pick flexible licenses to support this!

## Pull Requests
We actively welcome your pull requests!

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code lints.
6. If you haven't already, complete the Contributor License Agreement ("CLA").

### Contributor License Agreement ("CLA")
In order to accept your pull request, we need you to submit a CLA. You only need
to do this once to work on any of Facebook's open source projects.

Complete your CLA here: <https://code.facebook.com/cla>

### License
By contributing to ThreatExchange, you agree that your contributions will be licensed
under the LICENSE file in the root directory of sub-project's source tree.

### Documenting Changes
It is important to keep documentation up-to-date. Make sure to add and update
docstrings where appropriate.

### Testing and Test Plans
When possible, add unittesting for changes. You can often find a `tests` folder
in the directory you are working with, or in smaller projects, a top-level `tests`
folder that contains all the tests.

For changes that aren't easy to unittest, we still want to know you are sure your 
change does the right thing. Make sure to include the testing steps you used. 
If you add more testing steps (e.g. as a result of review feedback)

### Submit a PR
Once you are happy with your changes and ready for a PR, you can submit a PR to
the main project. In most cases you’ll be looking to compare against the main
branch - we don't use development branches in this repo.

For titling, prefer including the project name in brackets with a clear summary of the change.

E.g. for a hasher-matcher-actioner PR that adds a new /compare API endpoint, the title might be

   [hma] Add new /compare endpoint which compares signals

Make sure to include a summary of changes (especially the "why" or problem you are solving if it's new functionality and not described in an issue).
Make sure to link the issue if it's for an issue!

### Continuous Integration
If you are a new contributor, the continuous integration (CI) won't run until it's triggered by a maintainer of the repo. 
If there is CI failure, we usually won't merge the change!

### Review
Once you’ve submitted a PR you're waiting on us for review. We aim to check the repo every business day, but sometimes we are slow, especially if there aren't new changes.
We aim to try and get you a full review every business day (e.g. resulting in either "request changes" or merge), but we can't always do this. 
We don't expect it takes longer than 5 business days to get a first review.

To make changes on your code for review, checkout your branch again

    git checkout <MY_COOL_FEATURE_BRANCH_NAME> 

Make your changes as new commits (don't amend your previous commits as they break history and make it harder to review)

   git commit -m "fixed unittest failures"

Then push your changes to your fork again - they'll automatically update your PR!

   git push  # assumes you set up the default push target to your fork
 
Here are some things to expect from review:
1. If your summary isn't detailed and we aren't sure what the change is aiming to do, we might request changes without reviewing much of the code.
2. If you don't have a test plan or your change is missing updates for unittesting, we will likely request changes.
3. Different reviewers have different styles, but you may see various prefixes for comments, like `nit:`. Here's what they mean:
    1. `blocking:` This indicates that there is a change that the reviewer would not accept the PR without further discussion. This may not mean that there is anything wrong with your code, just that the reviewer is uncertain (you will sometimes see 'blocking question:' used similarly.
    2. `ignorable:` This comment is explicitly not blocking, and may just be a thought. You may be inspired to change code, reading it, but it's not expected.
    3. `nit:` This may be a stylistic preference or minor efficiency in the code that does not affect the correctness. Implicitly `ignorable:`, though if you like yours better, consider commenting why!
    4. `alt/code golf:` The reviewer is providing an alternative implementation that might be shorter or have a stylistic difference. Implicitly `ignorable:`
  
### Merging
Once your code is accepted, we usually merge it right away! If you don't want us to do this, please note it in the summary. You can always do followups as another PR!

### PR Sizes & Landing-and-iterating 
We generally prefer smaller changes (<100-500 lines of functional py code, not including unittests), and so if you have a larger feature, consider opening an issue to explain your full plans, and then doing a series of PRs all linking to that issue.
We understand that everyone contributing is essentially volunteering time, and so want to make the best use of your time as well. If you have run out of time to donate, and have already done a few passes of review, please let us know as a comment. 
A maintainer might be willing to finish your PR, or merge it as is, and make an issue to clean it up after. 
If you have contributed multiple PRs, we'll generally give you more slack in this department, since we have seen you come back!

