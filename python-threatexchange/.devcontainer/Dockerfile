# See here for image contents: https://github.com/microsoft/vscode-dev-containers/tree/v0.163.1/containers/javascript-node/.devcontainer/base.Dockerfile

# [Install python]
# TODO: pin version later. Otherwise starting up will be too slow.
FROM python:3.8-buster

# [Unixname wrestling]
# Some of our script (docker-related) are dependent on the unixname. Would 
# need to setup the environment with *your* unixname as the defualt user.
ARG unixname
RUN groupadd --gid 1000 developers \
  && useradd --uid 1000 --gid developers --shell /bin/bash --create-home $unixname \
  && usermod -aG sudo $unixname

# [Install Tools!]
RUN apt-get update && DEBIAN_FRONTEND=noninteractive \
  apt-get -y install --no-install-recommends git make jq sudo \
  software-properties-common apt-transport-https ca-certificates curl \
  gnupg lsb-release tmux zsh vim less

# [Allow sudo] Need sudo later in post-create to open up docker socket
ARG unixname
RUN echo "$unixname ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

# [Install node] Node.js version: 15 only. Stolen from: https://github.com/nodejs/docker-node/blob/main/15/buster/Dockerfile
RUN groupadd --gid 1001 node \
  && useradd --uid 1001 --gid node --shell /bin/bash --create-home node

# [Install GitHub CLI]
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-key C99B11DEB97541F0 \
  && apt-add-repository https://cli.github.com/packages \
  && apt update \
  && apt install gh

# [Shell Dotfiles]
ARG unixname
COPY --chown=${unixname} zshrc /home/$unixname/.zshrc

ARG unixname
COPY --chown=${unixname} bashrc /home/$unixname/.bashrc

# [Shell Histories] The volume is mounted in devcontainer.json
ARG unixname
RUN BASH_SNIPPET="export PROMPT_COMMAND='history -a' && export HISTFILE=/commandhistory/.bash_history" \
  && ZSH_SNIPPET="HISTFILE=/commandhistory/.zsh_history" \
  && mkdir -p /commandhistory \
  && touch /commandhistory/.bash_history \
  && touch /commandhistory/.zsh_history \
  && chown -R $unixname /commandhistory \
  && echo $BASH_SNIPPET >> "/home/$unixname/.bashrc" \
  && echo $ZSH_SNIPPET >> "/home/$unixname/.zshrc" \
  && echo $ZSH_SNIPPET >> "/home/$unixname/.profile"
# Also appends ZSH_SNIPPET to ~/.profile in case users want to overwrite zshrc file
# e.g. https://code.visualstudio.com/docs/remote/containers#_personalizing-with-dotfile-repositories


# [Forward Docker requests to host docker engine]
# Volume is mounted and so is the socket. The socket configuration is within
# devcontainer.json
VOLUME [ "/var/lib/docker"]