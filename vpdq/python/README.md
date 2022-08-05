# vpdq
This is a Python binding library to the vPDQ (video PDQ) hashing algorithm by Meta. The project is at [github](https://github.com/facebook/ThreatExchange/tree/main/vpdq)

## Installation
### Install library
```
pip install vpdq
```
### Install FFmpeg

Before using VPDQ to create hashes, you must install FFmpeg. FFmpeg is easiest to use if accessible via the `$PATH` environment variable.

There are a variety of ways to install FFmpeg, such as the [official download links](https://ffmpeg.org/download.html), or using your package manager of choice (e.g. `sudo apt install ffmpeg` on Debian/Ubuntu, `brew install ffmpeg` on OS X, etc.).

Regardless of how FFmpeg is installed, you can check if your environment path is set correctly by running the `ffmpeg` command from the terminal, as in the following example (truncated for brevity):

```
$ ffmpeg
ffmpeg version 4.4.2 Copyright (c) 2000-2021 the FFmpeg developers
```

> **Note**: The actual version information displayed here may vary from one system to another; but if a message such as `ffmpeg: command not found` appears instead of the version information, FFmpeg is not properly installed.

### Usage
```
import vpdq
vpdqHashes = vpdq.computeHash("file_path")
# Each hash have five attributes
# quality: int
# frame_number: int
# hash: list
# hex: str (64 digits hex string representation of hash)
# timestamp: double
for hash in vpdqHashes:
    print(str(hash.frame_number) + "," + hash.hex + "," + str(hash.quality) + "," + str(hash.timestamp))
```
Sample Output:
```
0,e271017837246aaccddea259648fb7d62f435c89d9e99b2497763e216c8d055c,100,0
1,c0f11178372c6aaccddea259648fbfd62f434c89c9e99b249772be216c8d055c,98,1
2,c0f10b78372c6aacc5dea25b748fb7d22f434c89c9a9db249772b6216c8d855c,80,2
3,c0f00b7837247aaccddea25b128fb7d22f434c894da9cb349776b621668dc55c,100,3
....
```