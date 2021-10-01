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

1. Download the docker image:
```
$ docker pull public.ecr.aws/l5b3f6x2/threatexchange/hmalite:latest
...
Status: Downloaded newer image for public.ecr.aws/l5b3f6x2/threatexchange/hmalite:latest
public.ecr.aws/l5b3f6x2/threatexchange/hmalite:latest
```
2. Run the docker image, pointing it at your favorite port (here we use 5000)
```
$ docker image ls
REPOSITORY                                       TAG                 IMAGE ID            CREATED             SIZE
public.ecr.aws/l5b3f6x2/threatexchange/hmalite   latest              33e9c2756d58        2 hours ago         1.1GB

$ docker run -d -p 5000:80 public.ecr.aws/l5b3f6x2/threatexchange/hmalite:latest
```
3. Visit the beautifully designed landing page by going to localhost:5000 in your browser
![image](https://user-images.githubusercontent.com/1654004/109725464-0a065580-7b66-11eb-9b61-a817d2b536d8.png)

From here, you can replace the index with .csv files downloaded from ThreatExchange or your own sources (protip: a file with one PDQ hash per line is a csv file).

4. Ping the API with curl or by visiting the right endpoint. If using the built-in sample data, it has metadata similar to what is stored on ThreatExchange
```
$ curl localhost:5000/v1/hashes/query?hash=b3485b12693aa21374197089daa65b4db57d9eb68acb4d467db4eceaaa85c351
{
  "match": true,
  "result": [
    {
      "data": {
        "hash": "b3485b12693aa21374197089daa65b4db57d9eb68acb4d467db4eceaaa85c350",
        "meta": [
          "3525057520847482",
          "2020-07-31T18:47:52+0000",
          "media_priority_pdq_samples disputed media_priority_samples media_type_photo"
        ]
      },
      "distance": -1
    }
  ]
}

# Note - this was with an index of size 200k as well
$ time (head -n 10000 ~/200k_pdq | parallel --progress -j32 'curl -s localhost:5000/v1/hashes/query?hash={} >/dev/null')

Computer:jobs running/jobs completed/%of started jobs/Average seconds to complete
local:0/10000/100%/0.0s

real    0m29.166s
```
# Running with your own data
## Docker Commit
We're going to take advantage of the fact the entirety of the the `threatexchange` cli is included in the image
1. Spin up the container
```
$ docker run <MY_IMAGE>
```
2. Set up an interactive session on the container, and set the ThreatExchange credentials via the environment (you can also use the alternatives to environment if you are not worried about bash history and you are only planning on using the image privately.
```
$ docker exec  -e TXTOKEN=<APP TOKEN> -it <MY_IMAGE> bash
image$ vim ~/te.cfg  # Set up the collabo config with the correct settings
image$ threatexchange fetch
# Output will live in the home directory, named after the collab
# for example, a collab named "Foo Bar Baz" will end up in "~/foo_bar_baz"
# (someone should do a PR to make this easier to control)
$ ls ~/foo_bar_baz
pdq.te
video_md5.te
...
$ realpath ~/foo_bar_baz/pdq.te
/home/root/foo_bar_baz/pdq.te
```
3. Commit your docker image, which now has the right content on disk
```
$ docker commit <MY_IMAGE> my_image_with_fetched_data
$ docker run -e CSV_FILE=/home/root/foo_bar_baz/pdq.te my_image_with_fetched_data 
```

## Docker Compose
Produce the files you want to be included in your docker image with the process of your choice.
When composing, you'll need to add both the files and also add a `CSV_FILE` environment variable pointing to the location you are adding them to.

<TODO - an example>

# Contributing to HMA-lite
For current contributing guidance, please see [CONTRIBUTING.md](CONTRIBUTING.md).
