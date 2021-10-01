Getting Started with Contributing

# The Golden Rule
HMA-lite is a quick and dirty prototype. The rule you should always ask yourself before adding a feature, or potentially even fixing a bug is "should this just be added to Hasher-Matcher-Actioner proper instead?"

# Prerequisites
Docker is used to build and run the image and so is a requirement.

If you want to try and speed up your development, its easy to run the server locally, though you'll need all the python modules. The fastest way to get that is:

```
$ pip install -r requirements.txt
```

# Building the Docker Lambda Image

TBD

# Running Locally

```
$ cd hasher-matcher-actioner/hma-lite
$ FLASK_APP=hmalite.app:app FLASK_ENV=development flask run
# You can change config functionality using environment
$ CSV_FILE=/home/dcallies/.hmalite/te_samples_pdq.csv 
```

# Pushing a New Image

TBD
