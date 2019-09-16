# Description

This is a pure-Python implementation of PDQ.

# Dependencies

This uses the Python Image Library.

```
sudo pip3 install Image
sudo pip3 install pillow
```

# Computing photo hashes

```
$ export PYTHONPATH=
$ python ./pdqhashing/tools/pdq_photo_hasher_tool.py --pdq ../../data/bridge-mods/*g
d8f8f0cce0f4a84f0e370a22028f67f0b36e2ed596623e1d33e6b39c4e9c9b22,100,../../data/bridge-mods/aaa-orig.jpg
d8f8f0cce0f4a84f0e370a22028f67f0b36e2ed596623e1d33e6b39c4e9c9b22,100,../../data/bridge-mods/blur-a-little.jpg
d8f8f0cce0f4e84f0637022a028f67f0b36e2ed596623e1d33e6b39c4e9c9b22,100,../../data/bridge-mods/blur-a-lot.jpg
d8f8f0cce0f4e84d06370a32068f67f0b36e2ed596623e1d33e6339c4e9c9b22,100,../../data/bridge-mods/high-contrast.jpg
d8f8f0cce0f4e84f0e370a22028f67f0b36e2ed596621e1d33e6b39c4e9c9b22,100,../../data/bridge-mods/high-saturation.jpg
d8f8f0cce0f4a84f0e370a22038f67f0b36e2ed596621e1d33e6b39c4e9c9b22,100,../../data/bridge-mods/sharpen-a-little.jpg
d0f8f1cec0f4a8470a370a32238f67f0b36e2ef597231e1d72a6a39c4e9c9b22,100,../../data/bridge-mods/sharpen-a-lot.jpg
d8f8f0cce0f4a84f0e370a22038f67f0b36e2ed596621e1d33e6b39c4e9c9b22,100,../../data/bridge-mods/shrink-a-little.jpg
d0f8f1ccc0f4a84d0a370a3a228f67f0b36e2ed5b6623e1d33e6339c4e9c9b22,100,../../data/bridge-mods/shrink-a-lot.jpg
d8f8f1eec0f4a84f0e37022a078f63f0b36e2ed596621e1d33e6239c4e9c9b22,100,../../data/bridge-mods/square-128x128.jpg
d8f8f0cec4f4a84f0637022a078f67f0b36e2ee5b6621e1d33e6239c4e9c9b22,100,../../data/bridge-mods/square-256x256.jpg
d8f8f0cec0f4a84f0637022a278f67f0b36e2ed596621e1d33e6339c4e9c9b22,100,../../data/bridge-mods/square-512x512.jpg
```

# Testing

See also https://docs.python.org/3/library/unittest.html

```
$ python -m unittest pdqhashing/tests/matrix_test.py
$ python -m unittest pdqhashing/tests/hash256_test.py
$ python -m unittest pdqhashing/tests/pdq_test.py
```
