# See here for image contents: https://github.com/microsoft/vscode-dev-containers/tree/v0.163.1/containers/javascript-node/.devcontainer/base.Dockerfile

# [Install python]
# TODO: pin version later. Otherwise starting up will be too slow.
# Note: We specify AMD64 architecture as it is currently the only one supported for this devcontainer
# relevant for ARM architecture machines as using `python:3.8-buster` will have it try to use that instead
FROM amd64/python:3.9-buster

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

# [Install node] Node.js version: 16 only. Stolen from: https://github.com/nodejs/docker-node/blob/main/16/buster/Dockerfile
RUN groupadd --gid 1001 node \
  && useradd --uid 1001 --gid node --shell /bin/bash --create-home node

ENV NODE_VERSION 16.16.0

RUN ARCH= && dpkgArch="$(dpkg --print-architecture)" \
  && case "${dpkgArch##*-}" in \
  amd64) ARCH='x64';; \
  ppc64el) ARCH='ppc64le';; \
  s390x) ARCH='s390x';; \
  arm64) ARCH='arm64';; \
  armhf) ARCH='armv7l';; \
  i386) ARCH='x86';; \
  *) echo "unsupported architecture"; exit 1 ;; \
  esac \
  # gpg keys listed at https://github.com/nodejs/node#release-keys
  && set -ex \
  && for key in \
  4ED778F539E3634C779C87C6D7062848A1AB005C \
  94AE36675C464D64BAFA68DD7434390BDBE9B9C5 \
  74F12602B6F1C4E913FAA37AD3A89613643B6201 \
  71DCFD284A79C3B38668286BC97EC7A07EDE3FC1 \
  8FCCA13FEF1D0C2E91008E09770F7A9A5AE15600 \
  C4F0DFFF4E8C1A8236409D08E73BC641CC11F4C8 \
  C82FA3AE1CBEDC6BE46B9360C43CEC45C17AB93C \
  DD8F2338BAE7501E3DD5AC78C273792F7D83545D \
  A48C2BEE680E841632CD4E44F07496B3EB3C1762 \
  108F52B48DB57BB0CC439B2997B01419BD92F80A \
  B9E2F5981AA6E0CD28160D9FF13993A75599653C \
  ; do \
  gpg --batch --keyserver hkps://keys.openpgp.org --recv-keys "$key" || \
  gpg --batch --keyserver keyserver.ubuntu.com --recv-keys "$key" ; \
  done \
  && curl -fsSLO --compressed "https://nodejs.org/dist/v$NODE_VERSION/node-v$NODE_VERSION-linux-$ARCH.tar.xz" \
  && curl -fsSLO --compressed "https://nodejs.org/dist/v$NODE_VERSION/SHASUMS256.txt.asc" \
  && gpg --batch --decrypt --output SHASUMS256.txt SHASUMS256.txt.asc \
  && grep " node-v$NODE_VERSION-linux-$ARCH.tar.xz\$" SHASUMS256.txt | sha256sum -c - \
  && tar -xJf "node-v$NODE_VERSION-linux-$ARCH.tar.xz" -C /usr/local --strip-components=1 --no-same-owner \
  && rm "node-v$NODE_VERSION-linux-$ARCH.tar.xz" SHASUMS256.txt.asc SHASUMS256.txt \
  && ln -s /usr/local/bin/node /usr/local/bin/nodejs \
  # smoke tests
  && node --version \
  && npm --version

ENV YARN_VERSION 1.22.15

RUN set -ex \
  && for key in \
  6A010C5166006599AA17F08146C2130DFD2497F5 \
  ; do \
  gpg --batch --keyserver hkps://keys.openpgp.org --recv-keys "$key" || \
  gpg --batch --keyserver keyserver.ubuntu.com --recv-keys "$key" ; \
  done \
  && curl -fsSLO --compressed "https://yarnpkg.com/downloads/$YARN_VERSION/yarn-v$YARN_VERSION.tar.gz" \
  && curl -fsSLO --compressed "https://yarnpkg.com/downloads/$YARN_VERSION/yarn-v$YARN_VERSION.tar.gz.asc" \
  && gpg --batch --verify yarn-v$YARN_VERSION.tar.gz.asc yarn-v$YARN_VERSION.tar.gz \
  && mkdir -p /opt \
  && tar -xzf yarn-v$YARN_VERSION.tar.gz -C /opt/ \
  && ln -s /opt/yarn-v$YARN_VERSION/bin/yarn /usr/local/bin/yarn \
  && ln -s /opt/yarn-v$YARN_VERSION/bin/yarnpkg /usr/local/bin/yarnpkg \
  && rm yarn-v$YARN_VERSION.tar.gz.asc yarn-v$YARN_VERSION.tar.gz \
  # smoke test
  && yarn --version
# [Install Node] complete

# [Install Docker CLI]
RUN export DEBIAN_FRONTEND=noninteractive \
  && curl -fsSL https://download.docker.com/linux/debian/gpg | gpg \
  --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
  &&  echo \
  "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \
  && apt-get update && apt-get -y install docker-ce-cli

# [Install Terraform CLI]
RUN curl -fsSL https://apt.releases.hashicorp.com/gpg | apt-key add - \
  && apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main" \
  && apt-get update && apt-get install terraform

# [Install GitHub CLI]
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-key 23F3D4EA75716059 \
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

# [Install AWS CLI] Using pip install because the apt version is old. Doesn't
# support all ecr commands.
RUN pip3 install awscli --upgrade
