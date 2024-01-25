FROM ruby:2.7

RUN apt-get -y update && apt-get -y install libicu-dev cmake git && rm -rf /var/lib/apt/lists/*

RUN gem install github-linguist
RUN gem install gollum
RUN gem install org-ruby  # optional

WORKDIR /var/wiki
ENTRYPOINT ["gollum", "--port", "80"]
EXPOSE 80

