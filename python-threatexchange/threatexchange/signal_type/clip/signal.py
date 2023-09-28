from threatexchange.signal_type import signal_base

class CLIPSignal(
    signal_base.SimpleSignalType,
    signal_base.BytesHasher,
):
    """
    CLIP Signal Type.
    Article: https://arxiv.org/pdf/2103.00020.pdf

    CLIP is a neural network trained on a variety of (image, text) pairs.
    It can be used to generate image embeddings with semantic similarity, meaning
    that images with similar content will have similar embeddings.

    For example, two different images of cats will have higher cosine similarity
    than an image of a cat and an image of a tree.

    This type of hashing is robust to perceptual differences as long as the
    semantic content is the same.
    """

    INDICATOR_TYPE: str = "HASH_CLIP"
    CLIP_DISTANCE_THRESHOLD: float = 0.01  # TODO: Adjust as necessary, make configurable


    @classmethod
    def hash_from_bytes(cls, bytes_: bytes) -> str:
        """
        Generate a CLIP hash from a bytes object.
        """
        # TODO: Implement this
        pass


    @classmethod
    def compare_hash(cls, hash1: str, hash2: str, threshold: CLIP_DISTANCE_THRESHOLD) -> signal_base.SignalComparisonResult:
        # TODO: Implement this
        pass