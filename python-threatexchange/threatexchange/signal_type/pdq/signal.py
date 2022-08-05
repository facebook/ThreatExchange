# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Wrapper around the Photo PDQ signal type.
"""

import typing as t
import re

from threatexchange.signal_type.pdq.pdq_hasher import pdq_from_bytes
from threatexchange.content_type.content_base import ContentType
from threatexchange.content_type.photo import PhotoContent
from threatexchange.signal_type import signal_base
from threatexchange.signal_type.pdq.pdq_utils import simple_distance
from threatexchange.exchanges.impl.fb_threatexchange_signal import (
    HasFbThreatExchangeIndicatorType,
)
from threatexchange.signal_type.pdq.pdq_index import PDQIndex


class PdqSignal(
    signal_base.SimpleSignalType,
    signal_base.BytesHasher,
    HasFbThreatExchangeIndicatorType,
):
    """
    PDQ is an open source photo similarity algorithm.

    Unlike MD5s, which are sensitive to single pixel differences, PDQ has
    a concept of "distance" and can detect when content is visually similar.
    This property tends to make it much more effective at finding images that
    a human would claim are the same, but also opens the door for false
    positives.

    Which distance to use can differ based on the type of content being
    searched for. While the PDQ documentation suggests certain thresholds,
    they can sometimes vary depending on what you are comparing against.
    """

    INDICATOR_TYPE = "HASH_PDQ"

    # This may need to be updated (TODO make more configurable)
    # Hashes of distance less than or equal to this threshold are considered a 'match'
    PDQ_CONFIDENT_MATCH_THRESHOLD = 31
    # Images with less than quality 50 are too unreliable to match on
    QUALITY_THRESHOLD = 50

    @classmethod
    def get_content_types(cls) -> t.List[t.Type[ContentType]]:
        return [PhotoContent]

    @classmethod
    def get_index_cls(cls) -> t.Type[PDQIndex]:
        return PDQIndex

    @classmethod
    def validate_signal_str(cls, signal_str: str) -> str:
        """PDQ hash contains 64 hexidecimal characters."""
        if not re.match("^[0-9a-f]{64}$", signal_str):
            raise ValueError("invalid PDQ hash")
        return signal_str

    @classmethod
    def compare_hash(
        cls,
        hash1: str,
        hash2: str,
        pdq_dist_threshold: int = PDQ_CONFIDENT_MATCH_THRESHOLD,
    ) -> signal_base.SignalComparisonResult:
        dist = simple_distance(hash1, hash2)
        return signal_base.SignalComparisonResult.from_simple_dist(
            dist, pdq_dist_threshold
        )

    @classmethod
    def hash_from_bytes(cls, bytes_: bytes) -> str:
        pdq_hash, quality = pdq_from_bytes(bytes_)
        if quality < cls.QUALITY_THRESHOLD:
            return ""
        return pdq_hash

    @staticmethod
    def get_examples() -> t.List[str]:
        return [
            "acecf3355e3125c8e24e2f30e0d4ec4f8482b878b3c34cdbdf063278db275992",
            "8fb70f36e1c4181e82fde7d0f80138430e1e31f07b628e31ccbb687e87e1f307",
            "36b4665bca0c91f6aecb8948e3381e57e509ae7210e3cd1bd768288e56a95af9",
            "e875634b9df48df5bd7f1695c796287e8a0ec0603c0c478170fc9d0f81ea60f4",
            "42869d32fff9b14c100759e17b7c204628f97efca264c007f5e9bdfc004f2a73",
            "34f3b0e8d32c4d0728b3846d367720924988db6d365335b2cdacda4fb253a5b7",
            "26d306938936bd3c04a4d206b0dfe0f3e8e149335367b7ca878b698f7c778631",
            "b29d92b94c4c6970a4f6951ad8637ac861a5ce4d69b9696e82d99cb6a4bc41f9",
            "9b2b0382d917e67ee3e1c826397aa069686627639894752be7ded87a7fa12444",
            "6b5a27b7415a05db1c6e166ea49b7976b9652280868f95eb4aef85874f0eb811",
            "3cc0099973ddf04dde37c3b226e31f29f1d9f0973e06c16cc1693e128292e1ee",
            "6311f1a5d7a68ccaece763f252e0e0bdec9748c2117a17ad3e81fe819c38961a",
            "82ab03260d4638a71afee1c9b09bc3ff4f6e1dd2ec67fece139ee92926480016",
            "27111f2ccface1fa11db29436620febcd99908cb10c72001e634db3adfbbb6d4",
            "ced62bad954258f42e23904a6edc82a77db541622b598db6b124a6cb9496e7d3",
            "e0058feb769207e5c039571af056863d476c68cfee16d4b839cda1f70214cfb8",
            "4567c985b5381f727847b348ea51b6168cb4e8cda8cb4e9a2e9a289431c7f5dd",
            "4cf214d6c1cdac6d896c49b04cd5d31d99b9ca39aa19aa698521fa16975b47de",
            "b2d244a45d4d2a25bd6bab5b66a6d4dc12675649c9b1ab32a652acde90975365",
            "1eccc389c5db3db9b02647666bd24e8c9618e0e5342199de37104f1ef7659a87",
            "93312c67d0ce4d98b2332167ecccc3983eb3c367ed8c18d0ebb33867a74c7ca0",
            "029706dec6d995a9307e5ce4cf86352a307ed985c70f467f5c79eb408eca8cc1",
            "f13de9de2e5d46ea51749338e45ea9891a068e17c455bca745ab17de0e7241c4",
            "03baf64c4813b5e18bf47c0be2050ea1d1da7b4c84b795b37a4d6d9a92e06db6",
            "67688ddd44acd51a5955a6e5adad11d2eb716e9d43272431a53ccaa38a499cce",
            "3be791183317d478924b364898194967cb5e8c343974d90758adf1fd84d73f1a",
            "c34355696762a37277b65536b70c4f4caecc9b5c4dad19094ceda4919b6944e1",
            "33338a8c8f0cf735d30242f68b2bcf758d2fbc26dcb208f59bf0fcc20c83e0cc",
            "343b4330c1ef7eb0973e2acea47881a849cf0f23b71cd08e91f1a8b8175b5b57",
            "b3485b12693aa21374197089daa65b4db57d9eb68acb4d467db4eceaaa85c350",
            "f31b6d9a5a87cb18ae0cea07ed90bee0aa389b0bed4ce8f1e8b0aa4ca333e8a1",
            "3bb1f8b316cf5f4a6dc0aaad3a4c93dbe4210ef5f618804d7fa0ded7007ca420",
            "ae7969f3cb8f45c2424c8d0384fc8f2fbd401e2b5c0962b560cdb7d49d4b9a5c",
            "817e74fb37db7b33884585883612a37219ace677cccd999833326623cccc9999",
            "65b19665709e7cb72bcc4531e7cdba19dbc64381a58b0f3d9cb40d9a0434ecc3",
            "886f9bec7f026417c1d088e5986d361bf7db6d948095c06bfffc9f8f08020297",
            "5a195e995ed8ffceed60eda5b529f69282d20016005508174a5fd64af3acfda1",
            "871ea8e2fc7a6378f7038cc63c40e23823cc9c8f0a71e631f89c9fccce637165",
            "049f7bd4a80facf81e4b1ab0f934113d7ffb401916b48f2d24d92c596e746ad4",
            "c9196db227c290db4c982663b3e6491965bc96e65b232d99c6597166aee7964c",
            "948ba7f54ac4d69ba5668bda56a2350fa2552fe54d0976c64db8758668146da6",
            "7d868638534c2f1b60e318875f9ce6744f1ff77930e339c8ce72c635519c3940",
            "33da4b361f78c4ece516f631c4e9ad585326ce370dd0ed98726108b69d19659c",
            "a2965c4b8724a6f85a87cd78b0946ba3c56e318cf2f3ccce338c8c731c793978",
            "cd484c8934cd339c3328d273ca36d9624db724df3cdab26cd319c61cce993966",
            "4137bad4c42069ddb92b56f46849bf36c1845e4ba4f6b1255a9b6cd29328fb4c",
            "e6b917ce5357ecb89dc85347e030bc885bc7e031ac901bc76662e4a019c359ff",
            "8e071c5c1a803e13ad27d4000807015f7f38a940b403d4afdaff6b7fad6a7dbf",
            "8903e0caf8cdcaddd2ca31525235d226d5766ab5e2d352d3973e3e343cb4544c",
            "5c1c21f9a72354746addaf09947e72e42a1c817bd7e30a3cb95887837c3df814",
            "ea2b094d36a971665656e5329117d6d6a54188bdb6ea2b394aa8be88557685cf",
            "096a6f9e2a6e0227dbf9d729b8b0ecdd20d40cc5ff73c22a5300dee8dd03064f",
            "1520fd466a939134876f6931dada926bf9d02cbcb6d15b11caaa6348b4b296b7",
            "f2170be90152dced23d2b23bcce43b88d62e1981ef82484d3393ee64999f56d3",
            "e1f29c629e59c7c30bc111f31f5efbc600a5686de50e3f8603f4805dde122fe1",
            "9d9144a7bb2aaf8e69b59566b53de4bc982de7208d91df84a7e1012556c12979",
            "991929395c97a6d25629d393b393c66d72cb19c6cf6c4a6da1589cacc6b16354",
            "20a519697ad37e973c2dd5ac9d19c21bc2f7a1c7e5e2172163c138e3081eee3c",
            "b877b782c90b37045ad6507e2477ed3a8d855292a46db352092d61b9efcd6352",
            "76b7c3162d64cd197b34ceb7ac9419b29a8b324e66dab2b492d64f5856250ca6",
            "a5292c970b4e02a7838323ca3e60fddcdffbfe40fc545f8146158f4c332e04f9",
            "78690dd7b3646592e22b5ed6296dc495b1685c93936d4c9778c2c86c9d3bb312",
            "92943194d9d339432c8b465b132d1b8f53b79a4fc5a7a5664c766ad69333c598",
            "5214601cc96df3c91d618f81fc92b902c3e754ae2b9cc6f2b5d438f9ce4983dd",
            "aae8b8899506c668fed9540256662bd95aaafc16a9515baad426a5574beadaac",
            "a61be3bcbb90e88371aa3dc2fc4478f13cd2cf0441e1a44bfe4f5498c0f8c97c",
            "367f0d5f4c47db959319b2c4963524ee269034b42db9cd27cca4ccaf31e83329",
            "18c1a78dca8cd1ada77caad027ac9e76689c4e7854c221ae36eabda54eab525c",
            "c339b5d0bbe50cba5a49a1e6929b496db4f24e0bb8d74361063fe2d879011e3e",
            "2dcff03127895c4ec1b423f85e60b917c1dd666399320fcc7998cc77e60309dd",
            "4fa9d480727c3cee5e034635f242d6e9ddefa25226c9d46db245b640252d65da",
            "07d4e3fe078b5f997ce46201371b74244bc5b039e96a69cec4b51894d97cacc6",
            "384e1d64e37267f1579dba8d294acd6d8e6336426295d3bfd4948c9818d86565",
            "f48d11d17e36ac0897e76050e9eef60305f9cc8dfa0825dd69709a2f279f52d0",
            "4ee0deeed84e13df2153ac92ad700d6cf9cd802902295e92dad232decfc7c5c4",
            "cd7046e9766b09ed8d6adb9b111af29f7462661a8b70c97424e611f474c9d915",
            "d6a64aec574a94ad2c54b541c87c2f51b78b4a955a55dc2a6a5bb5a8956aaa55",
            "31a429cb9855d1aececae98456cce67d9b62c9985da96b9c0ee5f576701a02b2",
            "58583a5c2da6d6b59b1965ef54570b69a3245812aba9c6954cdb1d24b36f6a4b",
            "a3819313c4ef6f753b12c0bb4e343d4793d9e77e4c513ae05d1b85105a740f65",
            "986da6363ddc09e70a61027d62995c9e25a7dba29fe9b278adde6d9740361484",
            "223618f9d1d1edc76747561e38186579ddf19a8781c6468e377aeb3160311697",
            "5a418477d8b394ac87ae685d0bed718af4eab8b16a7159cc413c4a1f07ee8cb3",
            "afc25a0ad189abc5da81b446a7e2968275a329f1bdb42ceb2f7c1b28d6cc49ac",
            "b253da60de70841fa72fdde95da01bf00085d325daadb33d374e21885999cb65",
            "c1fc23dfacc4fbbdeec000ffc0723e534f8293f2f26f3c1d9301c1e0307c2303",
            "39b15a03464da499b393da0344f9b4b61326e841f8abbaa6e345e9c19fb62c7d",
            "3524cad37536a0a15b7ab28655f9ca06155b7eb091475df8aa96d569a692e964",
            "8dff1f318060f01381c9e01fcee6d83ff831f189e00e9e047c76f381fdd007cb",
            "65cb638943b86a324862f9e7a9af0fac721cf174bb278326b1a4baacac542e53",
            "17c880f4c3877b6b8149a5f4e0b65aabd06ba5d6bf1642fd02f9801ebd547c0b",
            "798af33dcb7199c13960ec2e9c9d96f114b24e0d4b196b5b8deead0c6581295a",
            "690c1728fed2432ed19f35d39e20db8e5529ac21ff8d60de01522d5b6e99694b",
            "cac53750bd3ecc9c7f5132238abcb0d07702c80f9d78337069e6c8ce325177e3",
            "9185ce616b9a31ce866159987acee663919938cc6e73139895c4cc337bde36cc",
            "b2c9a13ce255433ebd78abb5c7e3c7ced143e2bce63ac3d68a2d052a02700f91",
            "b0f3f24a7b283d9b0ac1ad4c31a4713e269bc37ad2e364989a4b9e44631779b3",
            "5a3b088aedd553391a5acc9867a57b369c73868d63847872bc5b878e33613a71",
            "f1f4d853351cc3a2cc72b6b4cfce70611acef1e18c71278ee4704b1a618cbcf1",
            "3a8ff5e1084efef300965f9cb969296dff2b04d67a94065ec9292129ef6b1090",
            "489e6e389861051311b2773b971e46c04ff2dce7348f33cc66f9cc9c9c8f3259",
            "80c5bf06678dc6481c8db3c6673508eac8736fbefd1e00c9bac9e0c085d93f37",
            "043f5f25f3a96e1d693b6146fe9276ff702345080f91c1df0411414b55c15ff9",
            "4509b4f4e3cc3798d6b0553b9c3295a56e071b1c467edb589671be82f90f4c64",
            "ed1bd85873cab7eecb4af16765fc84c8cb54b5b0485e07d1d51b514828a52ab8",
            "2d24e51c3c76245c9bf31d20239555c88a77b496ae53e412baf7aab352d34b4e",
            "378948acdbf83661247ebbdfcc39863631af7d0acb54249c0501cfb6fc127823",
            "7ef85906403879e4a9f03c5ecf71285e4f7b9f40be9b010efd8001cea3c62f78",
            "3d6cc503b7ec30131290efaf8a7676890b3636c98f3edb4804bec2337eca8137",
            "989038bb3c5b1a339d397f231f0b0f3f090caf768d5ecf27c685677a21309285",
            "20f66f3a2e6eff06d895a8f421c045e1c76f0bf87652d72ce7249412d8d52acc",
            "aa7c7de2940fa0f45ba15913a5f8aecd1a2c5178b517a8874bea2f53a25154b6",
            "dd24e2fc80f93cb6259c1f91b387e18fec71f03f38cefc07d40e3d88d2009f80",
            "d87353383f60a45cb7e26c9cd1674f85f2402cbcac09e9f3569dd97626889866",
            "f50d8a67ce5670d639a1cc4dd2d213acae70fc0b9a95e91115625ae50dbb8ef0",
            "8d814b61932efa9fb28794ac345c24e465f37f06c729ae6e74eb455318a15559",
            "ad6a2a4a525b5695d4a5e4b5a9482b4a0f4e56b4d4b5b1b5ab4b2f4aee4a54a5",
            "d79be0d3441a333041a43b240dfda34f99cae44ad99356c5423554f5ebec3dca",
            "2f03781a0a98d2579160569fc7dcf97a2c80eda7192712de98e635fdd5651a16",
            "5a6a69bd8016d6c2c37a6ca5d38ca83f97c24f2830b595a5eeb56231f88df225",
            "600f3fa345ac8c55e39352c9ce2baf4828f4533610cadb93ae6d7d25d099cee2",
            "361da9e6cf1b72f5cea0344e5bb6e70939f4c70328ace762529cac704297354a",
            "d864307439ed1784e39ce2192c7a1e7a77e3c1e38987199d9bbcfeb804426dc2",
            "7c70f604bc24c9db8d9b5e3c7e7c3e3c1e3c0b3820db08e698e6c0c6c3c7e391",
            "379dbbb1d27499aac9fa8c89bccc4e5b126ca5688ca572c119ce2c6418b3df1c",
            "3a50b8642da4569bd55bdaa9562d65ae5b132272f4e86b2a5949a575aaae5529",
            "454db29134aa3b565f78f9abb1c51ce58c2a2a7485724163fc39af98569ce81e",
            "2af1dc14d59f27eeada8dd54e05ca07b54881f8007f0e9f5a9fc265fdd02d180",
            "5d871b14393d2533e6e3e6c6cecc98ceb989b93187b1f6346aa72a434a4bc898",
            "5e74b3c76c1a48e4a7981f63c8cd3732878b5075a9b246459ae3f5fa4e24c9c1",
            "d63aa91c969b892494cacbb0d5ba994a6596d52a2db1d2b88daad20697b959f3",
            "a6798c6971ce39ce6c319e70f0943d87387c0e03f078279ecf0f1f1c30df1863",
            "002f5dd87fe4d01bff76203d803f07c517833ef907f2ae0f0044fc9c4013ff6a",
            "0bd0b99c6374ac509981760ec9c3f4035e8b303e44eb55ab03fa00fec1faffd5",
            "5e53f66078ec5b664fa338682f5866f96f404b4e671925e15e0e5d198663865c",
            "d33c9979cbab36ba44ed72aa1358d6a7ac928d4168963512fbb511643336c4cb",
            "c4b54f9e32c67134c704ce16dc6d31873634b339c263c44cc9c7958f1a396fb5",
            "b0f815db7693c05a4b765a66584dd92cdb952c31b46335e124ce049c7eb82ddb",
        ]
