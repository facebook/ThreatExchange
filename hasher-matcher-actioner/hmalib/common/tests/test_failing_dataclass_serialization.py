import typing as t
from dataclasses import dataclass, field

from hmalib.common import aws_dataclass


@dataclass
class NotSoSimple(aws_dataclass.HasAWSSerialization):
    e: t.Set[float] = field(default_factory=lambda: {1.3, 4.2})


"""
I have no idea what's going on. If you comment out the class defined above and
run tests, they fail with a deserialization error.

My numerous attempts at figuring out exactly what is wrong have failed. The
problem started after introducing S3ImageSubmissionBatchMessage in
message_models.py. If you swap out the type of image_submissions:
t.List[S3ImageSubmission]

to any a primitive list like `image_submissions: t.List[int]`, there are no
failures. Spooky!

The failure exception looks like:

E           hmalib.common.aws_dataclass.AWSSerializationFailure: Deserialization
error: Expected typing.Set[float] got <class 'list'> ([Decimal('1.3'),
Decimal('4.2')])
"""
