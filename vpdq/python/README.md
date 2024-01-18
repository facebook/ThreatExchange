# vpdq Python Binding
This is a Python binding library to the vPDQ (video PDQ) hashing algorithm by Meta.

It is written in Cython.

Development is hosted on [GitHub](https://github.com/facebook/ThreatExchange/tree/main/vpdq).

Windows is currently not supported by the Cython bindings.

## Installation

Install from [PyPI](https://pypi.org/project/vpdq/)

```sh
python -m pip install vpdq --upgrade
```

####  OR

Install locally (run from root vpdq folder):

```sh
python -m pip install -e .
```

You should now be able to run `python -c "import vpdq"` without error.

### Usage
```py
import vpdq

# A vpdq hash is a list of vpdqFeatures.
#
# Each vpdqFeature has five attributes:
# quality: int
# frame_number: int
# hash: Hash256 (Video frame hashed by PDQ) 
# hex: str (64 digit hex string representation of hash)
# timestamp: double

vpdqFeatures = vpdq.computeHash("my_video.mp4")

for feature in vpdqFeatures:
    print(f"{feature.frame_number},{feature.hex},{feature.quality},{feature.timestamp}")
```

Sample Output:
```
0,e271017837246aaccddea259648fb7d62f435c89d9e99b2497763e216c8d055c,100,0
1,c0f11178372c6aaccddea259648fbfd62f434c89c9e99b249772be216c8d055c,98,1
2,c0f10b78372c6aacc5dea25b748fb7d22f434c89c9a9db249772b6216c8d855c,80,2
3,c0f00b7837247aaccddea25b128fb7d22f434c894da9cb349776b621668dc55c,100,3
...
```

## Development

See [CONTRIBUTING.md](../CONTRIBUTING.md) for development instructions.
