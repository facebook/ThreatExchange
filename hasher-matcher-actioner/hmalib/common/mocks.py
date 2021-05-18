import typing as t


class MockedThreatExchangeAPI:

    app_id = my_app_id = "a1"
    other_app_id = "a2"
    third_app_id = "a3"

    indicator_to_desriptors = {
        "2862392437204724": [
            {"owner": {"id": my_app_id}, "id": "11"},
            {"owner": {"id": other_app_id}, "id": "21"},
            {"owner": {"id": third_app_id}, "id": "31"},
        ],
        "4194946153908639": [
            {"owner": {"id": my_app_id}, "id": "12"},
            {"owner": {"id": other_app_id}, "id": "22"},
            {"owner": {"id": third_app_id}, "id": "32"},
        ],
        "3027465034605137": [
            {"owner": {"id": my_app_id}, "id": "13"},
            {"owner": {"id": other_app_id}, "id": "23"},
            {"owner": {"id": third_app_id}, "id": "33"},
        ],
    }

    def get_threat_descriptors_from_indicator(
        self, indicator
    ) -> t.List[t.Dict[str, t.Any]]:
        return self.indicator_to_desriptors[indicator]

    def react_to_threat_descriptor(self, descriptor, reaction) -> None:
        # can only react to a descriptor that exists
        assert descriptor in (
            descriptor["id"]
            for descriptor_set in self.indicator_to_desriptors.values()
            for descriptor in descriptor_set
        )
        return None

    def upload_threat_descriptor(self, postParams, *vargs):
        # Find the indicator for the descriptor we're trying to copy
        indicator = [
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
                    for descriptor in indicator
                    if descriptor["owner"]["id"] == str(self.my_app_id)
                ][0],
            },
        ]

    def copy_threat_descriptor(self, postParams, *vargs):
        return self.upload_threat_descriptor(postParams, *vargs)
