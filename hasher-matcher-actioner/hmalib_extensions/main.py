# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
This file holds simple hma_extension implementations. 
Primary as an example for incorporating others.

To use an extention you must specific a new entry point in 
setup.py 's entry_points group "hmalib_extensions"

For example the `print_arg` method below has been added to setup.py as
  "echo = hmalib_extensions.main:print_arg"

Once added hmalib can load these extentions via
`hmalib.common.extensions.load_extension_impl` 
e.g. 
```python3
from hmalib.common.extensions import load_extension_impl

fn = load_extension_impl("echo")

fn("Hello World!")
>> Hello World

```
"""


def print_arg(arg):
    """Example method use could use to test basic hma_extension support"""
    print(arg)
