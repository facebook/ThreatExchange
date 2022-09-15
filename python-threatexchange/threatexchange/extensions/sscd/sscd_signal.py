# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Wrapper around the Photo SSCD signal type with pre-trained settings.

The pre-trained settings used are sscd_disc_mixup (ResNet50)

Requires the installations of torch, torchvision, others
"""

import typing as t
import pathlib
import os.path

import torch
import json
from torchvision import transforms
from PIL import Image

from threatexchange.content_type.content_base import ContentType
from threatexchange.content_type.photo import PhotoContent

from threatexchange.signal_type import index, signal_base
from threatexchange.extensions.sscd.index import SSCDSignalTypeIndex


class SSCDSignal(signal_base.FileHasher, signal_base.SignalType):
    """Demonstrator for SSCD Signal Type"""

    @classmethod
    def get_name(cls) -> str:
        # If you are training your own sscd or using alternatives, consider
        # the naming convention sscd-dataset
        # So this would be "sscd-ResNet50"
        # Another suggested approach is "sscd-ResNeXt101"
        return "sscd"

    @classmethod
    def validate_signal_str(cls, signal_str: str) -> str:
        v = json.loads(signal_str)
        assert isinstance(v, list)
        assert len(v) == 512
        return signal_str.strip()

    @classmethod
    def get_content_types(cls) -> t.List[t.Type[ContentType]]:
        return [PhotoContent]

    @classmethod
    def hash_from_file(cls, file: pathlib.Path) -> str:
        model = torch.jit.load(os.path.expanduser("~/sscd_disc_mixup.torchscript.pt"))
        img = Image.open(str(file)).convert("RGB")
        normalize = transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        )
        small_288 = transforms.Compose(
            [
                transforms.Resize(288),
                transforms.ToTensor(),
                normalize,
            ]
        )
        batch = small_288(img).unsqueeze(0)
        embedding = model(batch)[0, :]

        return json.dumps([v.item() for v in embedding])

    @classmethod
    def compare_hash(
        cls,
        hash1: str,
        hash2: str,
        l2_dist_threshold: float = 0.7,
    ) -> signal_base.SignalComparisonResult:
        assert 0 <= l2_dist_threshold <= 1

        h1 = torch.Tensor(json.loads(hash1))
        h2 = torch.Tensor(json.loads(hash2))
        l2_dist = (h1 - h2).norm()

        return signal_base.SignalComparisonResult(
            l2_dist <= l2_dist_threshold,
            index.SignalSimilarityInfoWithSingleDistance(l2_dist),
        )

    @classmethod
    def get_index_cls(cls) -> t.Type[index.SignalTypeIndex]:
        return SSCDSignalTypeIndex

    @staticmethod
    def get_examples() -> t.List[str]:
        return []
