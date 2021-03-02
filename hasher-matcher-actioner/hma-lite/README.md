# Hasher-Matcher-Actioner Lite (HMA-lite)

While HMA is a full prototype reference architecture, hmalite is a single image toy prototype to test approaches for HMA itself. 

The goals are as follows:
1. Single docker image
2. Simple bootstrap process
3. Reasonable-ish match API performance for PDQ

# General Architecture
The docker image runs a python service using flask to spin up a simple web server. It loads a PDQ index into memory using simple formats.

# Running HMA-lite
The easiest way to demonstrate HMA is to directly run docker image.

TODO - steps

# Contributing to HMA-lite
For current contributing guidance, please see [CONTRIBUTING.md](CONTRIBUTING.md).
