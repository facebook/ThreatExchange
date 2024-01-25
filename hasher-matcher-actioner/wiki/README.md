# Editing this Wiki

Locally, you can run Gollum, which is the Github wiki editor to edit your files into shape before publishing to github.

Note, there are no pull-requests for wikis. You can only commit. 

Contributors to ThreatExchange should automatically have push access on the wiki.

## Cloning the wiki

```shell
$ git clone https://github.com/facebook/ThreatExchange.wiki 
```

## Setting up the docker image

```shell
$ cd ThreatExchange.wiki
ThreatExchange.wiki$ docker build -t threatexchange.wiki:latest .
```

## Starting the editor

```
ThreatExchange.wiki$ docker run -p 9999:80 -v`pwd`:/var/wiki threatexchange.wiki:latest
```

Then, navigate to [http://localhost:9999](http://localhost:9999).
