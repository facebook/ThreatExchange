# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Core abstractions for classifier interface.

Classifier is a generalization of the concept that was original introduced in
the SignalType interface. The act of converting something into a Signal (hash)
and then comparing it against a known corpus is a specialization of adding
a label to a piece of content, aka classification.

This outer level of abstraction of taking content and returning labels allows
us to not only contain the hash -> match loop, but also to add compatibility
for services which provide classification, of which there are many in the
trust and safety space.

Some example classification services are Google's content safety API,
Amazon Rekognition, and others.

Similar to the ethos behind SignalType, this interface is not meant to be
the best or fastest integration with these services, but to allow easily
A/B testing different classification methods against your current stack.
"""

import abc
import typing as t
from dataclasses import dataclass

from threatexchange import common
from threatexchange.content_type import content_base

Self = t.TypeVar("Self", bound="Classifier")


@dataclass
class ClassificationInfo:
    """
    Whether the label is a match or not, as well as any additional metadata.
    """

    is_match: bool

    def weight_str(self) -> str:
        """
        Return a human-friendly representation of the label weight.

        If your classifier doesn't have a concept of weight,
        return empty string.
        """
        return ""

    def __str__(self) -> str:
        """Returns a human-friendly representation of the info"""
        weight = self.weight_str()
        if not weight:
            weight = "+" if self.is_match else "-"
        return weight


TClassificationInfo = t.TypeVar("TClassificationInfo", bound=ClassificationInfo)


@dataclass
class ClassificationResult(t.Generic[TClassificationInfo]):
    """
    Container for classification results from a classifier.

    Holds a collection of labels and provides methods for accessing
    and displaying them.

    You can extend this class to override the string formatting,
    as well as add helpers that are specific to the type.
    """

    labels: t.Dict[str, TClassificationInfo]

    @property
    def positive_labels(self) -> t.Dict[str, TClassificationInfo]:
        """Return only labels where is_match is True."""
        return {l: i for l, i in self.labels.items() if i.is_match}

    @property
    def has_match(self) -> bool:
        """Return True if any label is a positive match."""
        return any(i.is_match for i in self.labels.values())

    def __str__(self) -> str:
        """Return a human-readable representation for UI/logs."""
        labels = []
        for label, info in self.positive_labels.items():
            weight = info.weight_str()
            if weight:
                labels.append(f"{label}({weight})")
            else:
                labels.append(label)
        if not labels:
            return "None"
        return ",".join(labels)


class Classifier(abc.ABC):
    """
    Abstract base class for content classifiers.

    A classifier analyzes content and returns classification labels indicating
    what categories or attributes the content matches. Unlike SignalTypes which
    generate hashes for exact or fuzzy matching, classifiers provide semantic
    understanding of content.

    Classifiers may:
    - Make network calls to external APIs (e.g., cloud ML services)
    - Run local ML models
    - Apply rule-based classification logic

    Implementations should be stateless where possible, with configuration
    passed via __init__ or get_with_default_settings().
    """

    @classmethod
    def get_name(cls) -> str:
        """A compact name in lower_with_underscore style."""
        return common.class_name_to_human_name(cls.__name__, "Classifier")

    @classmethod
    @abc.abstractmethod
    def get_content_types(cls) -> t.List[t.Type[content_base.ContentType]]:
        """Return the content types this classifier can process."""
        pass

    @classmethod
    def get_with_default_settings(cls: t.Type[Self]) -> Self:
        """
        Create an instance with default settings.

        Override this method to handle authentication, configuration loading,
        or other initialization that requires discovering settings from the
        environment.

        Throws an exception if it fails to initialize.

        Returns:
            A configured Classifier instance ready for use.
        """
        return cls()

    @abc.abstractmethod
    def classify(
        self, content_type: t.Type[content_base.ContentType], content_val: str
    ) -> ClassificationResult:
        """
        Classify the given content and return results.

        Note:
            This method may make network calls for API-based classifiers.
        """
        pass
