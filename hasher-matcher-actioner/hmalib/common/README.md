# hmalib common libraries
`common` directories can quickly become collections of miscellania. This directory is no different! Add documentation for specific concepts that are stable.

When adding new files here, ask yourself if it's truly common, or might be specialized for specific components, and consider putting it there instead.

# Submodules

| Module Name   | Classes in this module should be .... |
| ------------- | ------------- |
| `configs`  | Direct or indirect subclasses of `hmalib.common.config.HMAConfig`. Represent some user-configurable, database backed entity.  |
| `messages`  | Request or Response classes for HTTP APIs supported by HMA. Alternatively Messages passed between systems using a queue. These classes should support serialization/deserialization, but not persistent storage.   |
| `models`  | Direct or indirect subclasses of `hmalib.common.model.DynamoDBItem`. These are database backed entities with methods for querying / scanning / writing instances of this class. |

# config.py
## HMAConfig
A quick interface for simple configs backed by dynamodb.

Uses dataclass reflection to try and simplifying going between AWS API types and local types. There's likely already an existing library somewhere that does this much better.

### How to Use
The unittests documents usage, but super quickly:

```py
import typing as t
from hmalib.common import config as hma_config

@dataclass
class MyCoolConfig(hma_config.HMAConfig):
	foo_id: int
  bar_name: str
  enabled: bool
  so_fancy: t.Set[str]
  woah_now_slow_down: t.Dict[str, t.List[float]]

# Do this at your favorite entry point  
HMAConfig.initialize(the_table_name_which_is_probably_set_by_environment_by_terraform)
  
instance = MyCoolConfig("TheNameWhichIsUnique", 5, "The Hotfix Bar", False, {"a", "b", "z"}, {"baz": [1.0, 2.3, 5.1]})
hma_config.update(instance)  # Creates if doesn't exist

the_same_instance = MyCoolConfig.get("TheNameWhichIsUnique")
returns_none = MyCoolConfig.get("MichaelMcDoesntExist")
# MyCoolConfig.getx("MichaelMcDoesntExist")  # If you are exceptional
all_configs = MyCoolConfig.get_all()
```

If you for some reason need multiple configs to share the same unique namespace, but have different config types, there's a `HMAConfigWithSubtypes` class that allows this, with instructions in the docstring instead of here because you probably don't need it.
