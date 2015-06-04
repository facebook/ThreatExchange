.. _developing:

Developing
==========

Running Tests
-------------
.. code-block:: bash

    $ make test

Building Docs
-------------
.. code-block:: bash

    $ make docs

pre-commit
----------
pytx uses pre-commit_ to ensure the code aligns with PEP-8 and passes some basic python linting.

.. _pre-commit: http://pre-commit.com

In brief, after building a virtualenv to do development work out of you wanna the following one time:

.. code-block:: bash

    $ pre-commit install

After that, whenever you commit, pre-commit will run and either fix up minor issues in your files or let you know about them. Fix the issues, stage the files, and then commit again. Once there are no issues, the commit will succeed. To skip the checks, use:

.. code-block:: bash

    $ git commit --no-verify

But `--no-verify` is so uncool.
