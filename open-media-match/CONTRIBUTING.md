# Contributing to Open Media Match

Thanks for your interest in contributing to Open Media Match! Contributions from the community are essential to the success of this project, and we aim to make it as easy as possible for anyone to hack on Open Media Match and contribute code back.

If your developer onboarding experience is anything less than awesome, please file a GitHub issue with as much relevant information as possible.

To contribute, you will need, at the minimum:
 * A GitHub account
 * A development machine (e.g., your laptop)
 * A basic understanding of the Python language

Open Media Match is written in Python, uses [Flask](https://flask.palletsprojects.com/), and presents a REST API over HTTP. Familiarity with these core technologies will be advantageous.

Please see CONTRIBUTING in the repo root for more general guidelines on how to contribute by developing locally and submitting pull requests on GitHub.

# Developer onboarding and environment setup

There are a few different ways you can set up a development instance of Open Media Match and get to work.

## Visual Studio Code with a Dev Container (recommended)

This is the option that we recommend, and the one that will receive priority support from us. We leverage the excellent automation capabilities of Visual Studio Code and Docker to bring you consistent and repeatable turnkey dev environments that aim to eliminate "broken/works on my machine" scenarios.

Linux, macOS, and Windows are all viable host operating systems.

Corporate managed laptops can be a problem if what you are permitted to install and run is heavily restricted. There is a limit to how much of this we can mitigate from our end, and an unmanaged off-corp-net laptop may give you a better overall experience.

### Prerequisites

Install the following prerequisites on your desktop machine, if you don't already have them.

 * [Docker Desktop](https://www.docker.com/products/docker-desktop/)
 * [Visual Studio Code](https://code.visualstudio.com)

Note that if you are a Meta employee, your pre-installed build of Visual Studio Code will not be compatible, so be sure to install the stock version. Fortunately, you can run both versions side-by-side.

### Install the "Dev Containers" extension in Visual Studio Code

The [Dev Containers](https://code.visualstudio.com/docs/devcontainers/containers) extension is an innovative bit of glue between VSCode and Docker that automates the process of spinning up a containerized development environment with in-repo config.

### Get started

 * Clone this Git repository locally. If you are a non-Windows OS, you can do this through the CLI or through the "Clone Git Repository..." shortcut on the VS Code welcome screen.
   * [Windows] You'll have to do a trick to get the correct line endings for your devcontainer on checkout. The instructions for that can be found in the [hasher-matcher-actioner README](../hasher-matcher-actioner/CONTRIBUTING.md#vs-code-devcontainers--automated-development-environment).
 * Open the `open-media-match` folder in VSCode
 * VSCode should ask you if you want to reopen the folder in a Dev Container. Select "Reopen in Container".
 * Wait for the container to build

The VSCode window should now be replaced with a new one with `open-media-match` as the project root.

You should also see a Terminal panel within VSCode containing `Serving Flask app 'OpenMediaMatch'` and some other startup/initialization messages from Flask. This shows that the Flask server is up and running.

Open a second terminal panel. This will give you a Bash prompt. From here you can "ping" the Flask server with cURL to test its liveness. Try `curl localhost:5000/status`. You should receive the `I-AM-ALIVE` response back.

### Hello World

As an exercise, let's add a quick "hello world" API endpoint:

In your Bash terminal, run `curl localhost:5000/hello`. You should get a 404 error indicating that the `/hello` endpoint doesn't exist.

Let's add the endpoint. In `src/OpenMediaMatch/__init__.py`, add a route to the Flask app like so:

```python
@app.route("/hello")
def hello_world():
    return "Hello, world!\n"
```

Retry the `curl localhost:5000/hello`, you should now see your greeting message come back instead of the 404 error.

## Self-managed Python dev environment

If you're a seasoned Python developer and have your dev environment set up just-so, you should have no problem hacking on Open Media Match, as the project is laid out in standard Python Package format.

# How do I ...

## Persist the local development database?

Be aware that this might break stuff that assumes the database is clean or empty. Yes, this needs improving.

To persist the database, edit `.devcontainer/docker-compose.yaml` and uncomment the lines indicated. Then, rebuild the devcontainer.
