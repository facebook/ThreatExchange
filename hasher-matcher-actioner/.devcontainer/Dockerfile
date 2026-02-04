FROM mcr.microsoft.com/vscode/devcontainers/python:3.13-bullseye

RUN rm -f /etc/apt/sources.list.d/yarn.list \
  && apt-get update && export DEBIAN_FRONTEND=noninteractive \
  && apt-get -y install --no-install-recommends postgresql-client \
  && apt-get clean -y && rm -rf /var/lib/apt/lists/*

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
