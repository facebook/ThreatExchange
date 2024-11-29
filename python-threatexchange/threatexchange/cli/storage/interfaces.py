import abc
from dataclasses import dataclass
import typing as t
from content_type.content_base import ContentType


@dataclass
class ContentTypeConfig:
    """
    Holder for ContentType configuration.
    """

    # Content types that are not enabled should not be used in hashing/matching
    enabled: bool
    content_type: t.Type[ContentType]


class IContentTypeConfigStore(metaclass=abc.ABCMeta):
    """Interface for accessing ContentType configuration"""

    @abc.abstractmethod
    def get_content_type_configs(self) -> t.Mapping[str, ContentTypeConfig]:
        """
        Return all installed content types.
        """
