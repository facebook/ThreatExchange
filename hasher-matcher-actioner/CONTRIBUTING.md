# Contributing to Open Media Match

Thanks for your interest in contributing to Open Media Match! Contributions from the community are essential to the success of this project, and we aim to make it as easy as possible for anyone to hack on Open Media Match and contribute code back.

If your developer onboarding experience is anything less than awesome, please file a GitHub issue with as much relevant information as possible.

To contribute, you will need, at the minimum:
 * A GitHub account
 * A development machine (e.g., your laptop)
 * A basic understanding of the Python language

Open Media Match is written in Python, uses [Flask](https://flask.palletsprojects.com/), and presents a REST API over HTTP. Familiarity with these core technologies will be advantageous.

Please see CONTRIBUTING in the repo root for more general guidelines on how to contribute by developing locally and submitting pull requests on GitHub.

# Releasing a New Version

To release a new version of the Open Media Match image, follow these steps:

1. **Update the version.txt file**

The version number is stored in the `version.txt` file located at the project subfolder. Modify this file to reflect the new version number (e.g., `v1.1.0`).

```bash
echo "v1.1.0" > version.txt
```

2. **Merge to main**
Once the `version.txt` file is updated, and merged to main a new build will be triggered automatically via the CI/CD pipeline. This will create a new Docker image with the updated version and be pushed to the registry.

3. **Verify the Build and Release**
Monitor the build process to ensure everything runs smoothly. Once the build completes, the new Docker image will be tagged with the updated version and pushed to the registry.

4. **Test the New Image**
After the new image is successfully built and tagged, it can be tested locally by using the tagged image or deployed to your environment. This process may vary depending on your deployment setup (e.g., Kubernetes, Docker Swarm, etc.).

**Notes:**
- Do the version increase on its own PR to separate version releases from code changes.
- Ensure any expected changes in the codebase are included in the release, and all tests are passing before modifying the `version.txt` file.
- For breaking changes, consider incrementing the major version number (e.g., `v2.0.0`).


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
   * [Windows] You'll have to do a trick to get the correct line endings for your devcontainer on checkout. The instructions for that can be found in the [hasher-matcher-actioner 1.0 CONTRIBUTING](https://github.com/facebook/ThreatExchange/blob/HMA_1.0_archive/hasher-matcher-actioner/CONTRIBUTING.md#vs-code-devcontainers--automated-development-environment).
 * Open the `open-media-match` folder in VSCode
 * VSCode should ask you if you want to reopen the folder in a Dev Container. Select "Reopen in Container".
 * Wait for the container to build

The VSCode window should now be replaced with a new one with `open-media-match` as the project root.

You should also see a Terminal panel within VSCode containing `Serving Flask app 'OpenMediaMatch'` and some other startup/initialization messages from Flask. This shows that the Flask server is up and running.

Open a second terminal panel. This will give you a Bash prompt. From here you can "ping" the Flask server with cURL to test its liveness. Try `curl localhost:5000/status`. You should receive the `I-AM-ALIVE` response back.

### Hello World

As an exercise, let's add a quick "hello world" API endpoint:

In your Bash terminal, run `curl localhost:5000/hello`. You should get a 404 error indicating that the `/hello` endpoint doesn't exist.

Let's add the endpoint. In `src/OpenMediaMatch/app.py`, add a route to the Flask app like so:

```python
@app.route("/hello")
def hello_world():
    return "Hello, world!\n"
```

Retry the `curl localhost:5000/hello`, you should now see your greeting message come back instead of the 404 error.

## Self-managed Python dev environment

If you're a seasoned Python developer and have your dev environment set up just-so, you should have no problem hacking on Open Media Match, as the project is laid out in standard Python Package format.

# How do I ...

## Run tests?
```bash
cd /workspace/src/OpenMediaMatch
py.test
```

## Run formatting?
```bash
cd /workspace/src/OpenMediaMatch
black
```
Although you can remove the need for this by setting the "black" extension as your default formatter for python, and then setting vscode to format on save, both of which you can do in the preferences.

## Run typechecking?
```bash
cd /workspace
mypy src/OpenMediaMatch
```
If you don't run it in this directory, mypyp won't be able to find its settings folder and you'll get different results than the CI.

## Save Keystrokes on Common commands
Add these to your ~/.bashrc file and then reload with `. ~/.bashrc`
```bash
alias b='(cd /workspace/src/OpenMediaMatch && black)'
alias my='(cd /workspace && mypy src/OpenMediaMatch)'
alias t='(cd /workspace/src/OpenMediaMatch && py.test)'
alias myt='my && t'
```

## Recover from mysterious errors during sever startup?
If you had a syntax error in your code when you opened vscode, the automatic flask run that is created for you may fail. You can easily manually run it!

Create a new terminal window, and then run:
```bash
cd /workspace
.devcontainer/startup.sh
```
This is the same command that automatic window runs. Keep fixing errors until it successfully starts.


### It's worse than that!
When you create your devcontainer, data inside is persisted. However, if dependencies to the devcontainer are changed, or a bad database migration appears, you may end up in a strange state that cannot be recovered from. To reset fresh, you will want to rebuild your devcontainer, which you can do from within vscode.

From the menu, go to "View" > "Command Pallet", and in the window that appears, complete to "Devcontainers: Rebuild container".

This will shutdown your container and rebuild it from scratch. 

## Reset my database?
If your database has gotten into a funky state, run
```bash
cd /workspace/src/OpenMediaMatch
flask reset_all_tables
```
to clear it out entirely. If you need some test data (a bank with some hashes), also check out
```bash
cd /workspace/src/OpenMediaMatch
flask seed
```

## Persist the local development database?

Be aware that this might break stuff that assumes the database is clean or empty. Yes, this needs improving.

To persist the database, edit `.devcontainer/docker-compose.yaml` and uncomment the lines indicated. Then, rebuild the devcontainer.

## Make a change to the database schema?

The source of truth for the database schema is `src/OpenMediaMatch/database.py`. The database is managed by SQLAlchemy. Make your schema changes here. You will find the following reference material handy:

[SQLAlchemy Type Hierarchy](https://docs.sqlalchemy.org/en/20/core/type_basics.html)

Now migrate the database using the Flask CLI:

```bash
flask db migrate
```

This will generate a migration file in `src/OpenMediaMatch/migrations/versions`, which you can apply to the local database like so:

```bash
flask db upgrade
```

Note that `flask` CLI commands need to be run from within the `src/OpenMediaMatch` folder.
