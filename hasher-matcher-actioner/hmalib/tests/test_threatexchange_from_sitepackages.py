# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import unittest
import site
import os
import pathlib


@unittest.skipIf(
    "IGNORE_PY_TX_LOCAL" in os.environ,
    "Explicitly asked to not run threatexchange in site-packages test",
)
class ThreatExchangeNotLocalTestCase(unittest.TestCase):
    def test_threatexchange_from_sitepackages(self):
        # If this fails, the test should fail.
        import threatexchange

        # All site packages
        all_site_packages = site.getsitepackages() + [site.getusersitepackages()]

        threatexchange_found_in_sitepackages = False
        # atleast one site package should contain threatexchange.
        for site_packages in all_site_packages:
            try:
                pathlib.PurePath(threatexchange.__file__).relative_to(site_packages)
                threatexchange_found_in_sitepackages = True
            except:
                pass

        if not threatexchange_found_in_sitepackages:
            print(
                """
python-threatexchange was not found in site-packages. This is usually when you
are testing a local copy of the library. To fix, run

$ ./scripts/set_threatexchange_source pypi

If you are actively testing things in an unreleased copy of the library, run

$ export IGNORE_PY_TX_LOCAL=1

or

$ IGNORE_PY_TX_LOCAL=1 python -m py.test
            """
            )
            raise ValueError("python-threatexchange was not found in site-packages.")
