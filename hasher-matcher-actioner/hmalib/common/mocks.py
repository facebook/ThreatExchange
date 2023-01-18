# Copyright (c) Meta Platforms, Inc. and affiliates.

import typing as t


class MockedThreatExchangeAPI:

    app_id = my_app_id = "a1"
    other_app_id = "a2"
    third_app_id = "a3"

    @classmethod
    def build_descriptors(
        cls, privacy_members: t.List[str], seed: int
    ) -> t.List[t.Dict[str, t.Any]]:
        apps: t.List[str] = [cls.my_app_id, cls.other_app_id, cls.third_app_id]
        return [
            {
                "owner": {"id": app},
                "id": app + "|" + str(seed),
                "privacy_type": "HAS_PRIVACY_GROUP",
                "privacy_members": privacy_members,
            }
            for app in apps
        ]

    @property
    def indicator_to_desriptors(self) -> t.Dict[str, t.List[t.Dict[str, t.Any]]]:
        return {
            "2862392437204724": self.build_descriptors(["pg 4"], 2862392437204724),
            "4194946153908639": self.build_descriptors(["pg 4"], 4194946153908639),
            "3027465034605137": self.build_descriptors(["pg 3"], 3027465034605137),
        }

    # for convenience
    @property
    def descriptors(self) -> t.List[t.Dict[str, t.Any]]:
        return [d for ds in self.indicator_to_desriptors.values() for d in ds]

    def get_threat_descriptors_from_indicator(
        self, indicator
    ) -> t.List[t.Dict[str, t.Any]]:
        return self.indicator_to_desriptors[indicator]

    def get_threat_descriptors(
        self, descriptor_ids: t.List[int], **kwargs
    ) -> t.List[t.Dict[str, t.Any]]:
        descriptors = [d for d in self.descriptors if d["id"] in descriptor_ids]
        if "privacy_members" in kwargs.get("fields", []):
            # Can only get privacy_memebers field from apps you own
            # otherwise GraphAPI will error
            assert all(
                descriptor["owner"]["id"] == self.my_app_id
                for descriptor in descriptors
            )
        return descriptors

    def react_to_threat_descriptor(self, descriptor_id, reaction) -> t.List[t.Any]:
        # can only react to a descriptor that exists
        assert descriptor_id in (descriptor["id"] for descriptor in self.descriptors)
        return [None, None, {"success": True}]

    def upload_threat_descriptor(self, postParams, *vargs):
        # Find the indicator for the descriptor we're trying to copy
        descriptor_set = [
            descriptor_set
            for descriptor_set in self.indicator_to_desriptors.values()
            if postParams["descriptor_id"]
            in [descriptor["id"] for descriptor in descriptor_set]
        ][0]
        return [
            None,
            None,
            {
                "success": True,
                "id": [
                    descriptor["id"]
                    for descriptor in descriptor_set
                    if descriptor["owner"]["id"] == str(self.my_app_id)
                ][0],
            },
        ]

    def copy_threat_descriptor(self, postParams, *vargs):
        return self.upload_threat_descriptor(postParams, *vargs)

    def delete_threat_descriptor(self, id: str, *vargs):
        assert id in (descriptor["id"] for descriptor in self.descriptors)
        return [
            None,
            None,
            {
                "success": True,
                "id": id,
            },
        ]

    def remove_reaction_from_threat_descriptor(self, descriptor_id, reaction) -> None:
        # can only react to a descriptor that exists
        assert descriptor_id in (descriptor["id"] for descriptor in self.descriptors)
        return None
