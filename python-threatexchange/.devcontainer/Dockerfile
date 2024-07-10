ARG VARIANT=3.11-bullseye
FROM mcr.microsoft.com/vscode/devcontainers/python:${VARIANT}

RUN apt-get update -y && apt-get upgrade -y && apt-get install -y \
    cmake \
    libavdevice-dev \
    libavfilter-dev \
    libavformat-dev \
    libavcodec-dev \
    libswresample-dev \
    libswscale-dev \
    libavutil-dev

ARG NODE_VERSION="none"
RUN if [ "${NODE_VERSION}" != "none" ]; then su vscode -c "umask 0002 && . /usr/local/share/nvm/nvm.sh && nvm install ${NODE_VERSION} 2>&1"; fi

RUN BASH_SNIPPET="export PROMPT_COMMAND='history -a' && export HISTFILE=/commandhistory/.bash_history" \
  && ZSH_SNIPPET="HISTFILE=/commandhistory/.zsh_history" \
  && mkdir -p /commandhistory \
  && touch /commandhistory/.bash_history \
  && touch /commandhistory/.zsh_history \
  && chown -R vscode /commandhistory \
  && echo $BASH_SNIPPET >> "/home/vscode/.bashrc" \
  && echo $ZSH_SNIPPET >> "/home/vscode/.zshrc" \
  && echo $ZSH_SNIPPET >> "/home/vscode/.profile"