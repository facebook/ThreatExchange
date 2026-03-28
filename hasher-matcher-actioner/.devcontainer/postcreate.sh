#!/bin/bash
set -e

pip install --no-cache-dir --editable .[all]

cp /workspace/.devcontainer/bash_aliases ~/.bash_aliases
echo '[ -f ~/.bash_aliases ] && source ~/.bash_aliases' >> ~/.bashrc