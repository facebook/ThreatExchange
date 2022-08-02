# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import unittest
import typing as t

from threatexchange.signal_type.signal_base import TrivialSignalTypeIndex
from threatexchange.signal_type.index import SignalTypeIndex
from threatexchange.signal_type.pdq.pdq_index import PDQIndex


class TestIndexUpdates(unittest.TestCase):
    __test__ = False

    def get_first_set(self) -> t.Iterable[t.Tuple[str, t.Any]]:
        return []

    def get_second_set(self) -> t.Iterable[t.Tuple[str, t.Any]]:
        return []

    def get_index(
        self, initial_set: t.Iterable[t.Tuple[str, t.Any]]
    ) -> SignalTypeIndex:
        raise NotImplementedError

    def test_index_updates_actually_update_the_index(self):
        index = self.get_index(self.get_first_set())

        self.assertEqual(len(index.query(self.get_first_set()[0][0])), 1)
        self.assertEqual(len(index.query(self.get_second_set()[0][0])), 0)

        index.add_all(self.get_second_set())

        self.assertEqual(len(index.query(self.get_first_set()[0][0])), 1)
        self.assertEqual(len(index.query(self.get_second_set()[0][0])), 1)


class TestTrivialTypeIndexUpdates(TestIndexUpdates):
    __test__ = True

    def get_index(
        self, initial_set: t.Iterable[t.Tuple[str, t.Any]]
    ) -> SignalTypeIndex:
        return TrivialSignalTypeIndex.build(initial_set)

    def get_first_set(self) -> t.Iterable[t.Tuple[str, t.Any]]:
        return [
            ("55fc67a4e8d667d9668700c1920ff190", {"meta_data": 12}),
            ("5c4474f0e17bb56d0d73cca24c77e0d7", {"meta_data": 12}),
            ("e08572ca2db00e1f375d93b55b36a996", {"meta_data": 12}),
            ("ff2194f1208a9e07d41ad91ca64d3783", {"meta_data": 12}),
            ("07b261455844fcf348b56dc6511ffd72", {"meta_data": 12}),
            ("7f0ddfb32b98164a32bacc2bbc6f55ae", {"meta_data": 12}),
            ("36643e26bb7b12bc469fc9770c6e7252", {"meta_data": 12}),
            ("280791a55386db1997d4c9c21db8344b", {"meta_data": 12}),
        ]

    def get_second_set(self) -> t.Iterable[t.Tuple[str, t.Any]]:
        return [
            ("2624c75d21e5b991500812d84bf66d69", {"meta_data": 12}),
            ("46521c378a9070ce9da52f867c6eb024", {"meta_data": 12}),
            ("e757566a235fe9cef79478390c1a4d8b", {"meta_data": 12}),
            ("487a15edcec640fe8286b068e25ba2b3", {"meta_data": 12}),
            ("49442339bca61bda78a69a5de4d956f6", {"meta_data": 12}),
            ("5fd5ad963c42398ca8beabec76647d45", {"meta_data": 12}),
            ("353767ed43bfb3445086e16a0a7a6c52", {"meta_data": 12}),
            ("9c9657285b98b8cfb9a3de8570c6e8a1", {"meta_data": 12}),
            ("73a8d3f9fc517806673b50d965466943", {"meta_data": 12}),
            ("420e238441fb34901697f02f086ff466", {"meta_data": 12}),
        ]


class TestPdqIndexUpdates(TestIndexUpdates):
    __test__ = True

    def get_index(
        self, initial_set: t.Iterable[t.Tuple[str, t.Any]]
    ) -> SignalTypeIndex:
        return PDQIndex.build(initial_set)

    def get_first_set(self) -> t.Iterable[t.Tuple[str, t.Any]]:
        return [
            (
                "7c70f604bc24c9db8d9b5e3c7e7c3e3c1e3c0b3820db08e698e6c0c6c3c7e391",
                {"meta_data": 12},
            ),
            (
                "5e53f66078ec5b664fa338682f5866f96f404b4e671925e15e0e5d198663865c",
                {"meta_data": 12},
            ),
            (
                "2af1dc14d59f27eeada8dd54e05ca07b54881f8007f0e9f5a9fc265fdd02d180",
                {"meta_data": 12},
            ),
            (
                "d33c9979cbab36ba44ed72aa1358d6a7ac928d4168963512fbb511643336c4cb",
                {"meta_data": 12},
            ),
            (
                "dd24e2fc80f93cb6259c1f91b387e18fec71f03f38cefc07d40e3d88d2009f80",
                {"meta_data": 12},
            ),
            (
                "d63aa91c969b892494cacbb0d5ba994a6596d52a2db1d2b88daad20697b959f3",
                {"meta_data": 12},
            ),
            (
                "379dbbb1d27499aac9fa8c89bccc4e5b126ca5688ca572c119ce2c6418b3df1c",
                {"meta_data": 12},
            ),
            (
                "989038bb3c5b1a339d397f231f0b0f3f090caf768d5ecf27c685677a21309285",
                {"meta_data": 12},
            ),
            (
                "2f03781a0a98d2579160569fc7dcf97a2c80eda7192712de98e635fdd5651a16",
                {"meta_data": 12},
            ),
            (
                "5d871b14393d2533e6e3e6c6cecc98ceb989b93187b1f6346aa72a434a4bc898",
                {"meta_data": 12},
            ),
            (
                "600f3fa345ac8c55e39352c9ce2baf4828f4533610cadb93ae6d7d25d099cee2",
                {"meta_data": 12},
            ),
            (
                "3a50b8642da4569bd55bdaa9562d65ae5b132272f4e86b2a5949a575aaae5529",
                {"meta_data": 12},
            ),
            (
                "a6798c6971ce39ce6c319e70f0943d87387c0e03f078279ecf0f1f1c30df1863",
                {"meta_data": 12},
            ),
        ]

    def get_second_set(self) -> t.Iterable[t.Tuple[str, t.Any]]:
        return [
            (
                "002f5dd87fe4d01bff76203d803f07c517833ef907f2ae0f0044fc9c4013ff6a",
                {"meta_data": 12},
            ),
            (
                "5e74b3c76c1a48e4a7981f63c8cd3732878b5075a9b246459ae3f5fa4e24c9c1",
                {"meta_data": 12},
            ),
            (
                "8dff1f318060f01381c9e01fcee6d83ff831f189e00e9e047c76f381fdd007cb",
                {"meta_data": 12},
            ),
            (
                "0bd0b99c6374ac509981760ec9c3f4035e8b303e44eb55ab03fa00fec1faffd5",
                {"meta_data": 12},
            ),
            (
                "2d24e51c3c76245c9bf31d20239555c88a77b496ae53e412baf7aab352d34b4e",
                {"meta_data": 12},
            ),
            (
                "454db29134aa3b565f78f9abb1c51ce58c2a2a7485724163fc39af98569ce81e",
                {"meta_data": 12},
            ),
            (
                "b0f815db7693c05a4b765a66584dd92cdb952c31b46335e124ce049c7eb82ddb",
                {"meta_data": 12},
            ),
            (
                "d864307439ed1784e39ce2192c7a1e7a77e3c1e38987199d9bbcfeb804426dc2",
                {"meta_data": 12},
            ),
            (
                "378948acdbf83661247ebbdfcc39863631af7d0acb54249c0501cfb6fc127823",
                {"meta_data": 12},
            ),
            (
                "c4b54f9e32c67134c704ce16dc6d31873634b339c263c44cc9c7958f1a396fb5",
                {"meta_data": 12},
            ),
            (
                "5a6a69bd8016d6c2c37a6ca5d38ca83f97c24f2830b595a5eeb56231f88df225",
                {"meta_data": 12},
            ),
            (
                "7ef85906403879e4a9f03c5ecf71285e4f7b9f40be9b010efd8001cea3c62f78",
                {"meta_data": 12},
            ),
            (
                "361da9e6cf1b72f5cea0344e5bb6e70939f4c70328ace762529cac704297354a",
                {"meta_data": 12},
            ),
        ]
