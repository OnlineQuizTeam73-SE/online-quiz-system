# Local Docker and Jenkins Demonstration

This setup packages the Sprint 2 Flask application in Docker and lets Jenkins
test, build, deploy, and check it on the same Mac. It binds only to
`127.0.0.1`; it does not publish the application to the internet.

## Prerequisites and installation

This Mac reports `arm64` (Apple Silicon), macOS 26.6.2, and Homebrew 7.0.15.
Docker Desktop 4.99.0 is installed at `~/Applications/Docker.app` and is
running. Its user-level CLI tools are under `~/.docker/bin`. Use the Apple
silicon download from the
[official Docker Desktop for Mac instructions](https://docs.docker.com/desktop/setup/install/mac-install/).
The installer places Docker in Applications; starting it requires accepting
the Docker terms and may ask for an administrator password for recommended
settings. Start Docker Desktop from Applications and wait for its engine to
finish starting.

Check the processor before downloading Docker Desktop on another Mac with
`uname -m`: `arm64` means Apple silicon and `x86_64` means Intel. Docker
Desktop currently requires macOS 14 or later.

After Docker Desktop starts, verify it from Terminal:

```sh
export PATH="$HOME/.docker/bin:$PATH"
docker --version
docker compose version
docker info
docker run --rm hello-world
```

This project does not need Compose for its single container; the Jenkinsfile
and manual run command both use Docker directly.

Install Jenkins LTS using the official macOS Homebrew method. The current
formula depends on OpenJDK 21:

```sh
brew install jenkins-lts
brew services start jenkins-lts
"$(brew --prefix openjdk@21)/bin/java" -version
"$(brew --prefix openjdk@21)/bin/java" \
  -jar "$(brew --prefix jenkins-lts)/libexec/jenkins.war" --version
brew services list
```

Open [http://localhost:8080](http://localhost:8080) and complete the Jenkins
unlock and administrator setup screens. If the unlock screen requests its
initial administrator password, keep it private and read the path shown by
the Jenkins service logs or its configured `JENKINS_HOME`; on this
installation, the file is `~/.jenkins/secrets/initialAdminPassword`. Do not
paste the password into a terminal transcript or this chat. This Mac's Jenkins
2.580.2 installation has completed initial setup. The Jenkins LTS Homebrew
installer and Java compatibility are documented by
[Jenkins](https://www.jenkins.io/download/lts/macos/) and its
[Java support policy](https://www.jenkins.io/doc/administration/requirements/java/).

The agent running this job also needs Python 3.12 (`python3.12`), Git, `curl`,
and access to the Docker Desktop engine. The repository's GitHub Actions job
already uses Python 3.12. Keep this Jenkins agent dedicated to trusted builds
because the pipeline temporarily exposes the application secret to its deploy
step.

## Configure Jenkins

1. In **Manage Jenkins → Credentials → System → Global credentials
   (unrestricted) → Add Credentials**, choose **Secret text**, set **Scope** to
   **Global**, and set **ID** to `flask-secret-key`. Supply a long, randomly
   generated value from a password manager. The pipeline passes it to the
   environment through Jenkins' [Credentials Binding](https://www.jenkins.io/doc/pipeline/steps/credentials-binding/);
   it is not stored in the image or printed in the pipeline log.
2. Create a Jenkins **Pipeline** job configured as **Pipeline script from SCM**.
   Select Git, set the repository URL to
   `https://github.com/OnlineQuizTeam73-SE/online-quiz-system.git`, use the
   `*/main` branch specifier, and set the script path to `Jenkinsfile`.
3. Save the job and select **Build Now**. The Jenkinsfile independently checks
   the checked-out branch and stops unless it is `main`.

The Jenkins pipeline runs checkout, dependency installation, automated tests,
coverage generation and artifact archiving, Docker image build, local container
deployment, and an HTTP readiness check. A failed test stops the run before the
image or deployment stages. The HTML and XML coverage reports are archived on
the Jenkins build.

The Jenkins agent needs network access to install Python packages and pull the
`python:3.12-slim` base image. The existing GitHub Actions workflow remains
unchanged and continues to provide GitHub-hosted CI.

## Build and run directly with Docker

From the repository root, build the image and create the persistent volume:

```sh
export PATH="$HOME/.docker/bin:$PATH"
docker build -t se-final-app .
docker volume create online-quiz-team73-data
```

If you want the existing local quiz content, follow the safe one-time database
import below **before starting the first container**. Then set a fresh local
secret in the current shell and start the app on loopback only:

```sh
export SECRET_KEY="$(python3.12 -c 'import secrets; print(secrets.token_urlsafe(48))')"
docker run --detach \
  --name se-final-container \
  --restart unless-stopped \
  --publish 127.0.0.1:8000:8000 \
  --volume online-quiz-team73-data:/data \
  --env APP_ENV=production \
  --env DATABASE_PATH=/data/quiz.db \
  --env SECRET_KEY \
  se-final-app
```

Check the login page and logs:

```sh
curl --fail --silent --show-error http://127.0.0.1:8000/login >/dev/null
docker logs se-final-container
```

Do not run the Jenkins deployment while this manual container is using port
8000. Stop and remove the container first; the named volume is kept:

```sh
docker stop se-final-container
docker rm se-final-container
```

## Database persistence

The application stores its database at `/data/quiz.db` inside the container.
Jenkins mounts the named Docker volume `online-quiz-team73-data` at `/data`, so
database contents remain when Jenkins replaces the container. The container
startup applies `schema.sql` using `CREATE TABLE IF NOT EXISTS`; it never runs
`init_db.py`, deletes the database, or resets existing rows. A new empty volume
starts with an empty schema and can accept user registrations.

To start the demonstration with the existing local database and its sample
content, import it into a new Docker volume **before the first Jenkins build**.
Run this from the repository root. It reads the ignored local `quiz.db` as a
read-only source and copies it only when the destination database is absent:

```sh
docker volume create online-quiz-team73-data
docker run --rm \
  --volume online-quiz-team73-data:/data \
  --volume "$PWD/Sprint2_S2-01_S2-14/quiz.db:/source/quiz.db:ro" \
  python:3.12-slim sh -ec '
    if [ -e /data/quiz.db ]; then
      echo "Destination already exists; left it unchanged."
    else
      cp /source/quiz.db /data/quiz.db
      chown 10001:10001 /data
      chown 10001:10001 /data/quiz.db
      echo "Existing database copied into the persistent volume."
    fi
  '
```

Do not run this import command if the volume already contains data you want to
keep. The original `Sprint2_S2-01_S2-14/quiz.db` remains in place and is excluded
from Docker build context and images.

## Demonstrate the pipeline

1. Start Docker Desktop and the local Jenkins service.
2. Confirm Jenkins has the credential and prerequisites above. The pipeline
   checks out the repository's `main` branch, so the current Jenkinsfile and
   application changes must first be present on `main` in the SCM configured
   for the Jenkins job.
3. Watch checkout, dependency installation, the existing Sprint 2 tests,
   coverage report generation and archiving, image build, container deployment,
   and the readiness poll for the login page.
4. Open [http://127.0.0.1:8000/login](http://127.0.0.1:8000/login). If you
   imported the database, use its existing local demonstration accounts; with a
   fresh volume, register a user to demonstrate the app.
5. Run the pipeline again. The container is replaced, while the named database
   volume and its data remain.

To check persistence manually, register a user or add test content, remove the
manual container with the commands above, start it again with the same named
volume and the same secret, and sign in or check that content again. Never
remove the named volume to perform this test.

The app is available only on this Mac at `127.0.0.1:8000`. The Jenkins deploy
stage removes and replaces the container named `online-quiz-team73`; it does
not remove the `online-quiz-team73-data` volume.

## Verification record

- The existing Sprint 2 test suite passed **64 tests** with **99% coverage**
  under Python 3.12.16. Test dependencies and coverage files were isolated in
  `/private/tmp`; the repository's `quiz.db` was not used or changed.
- Jenkins LTS 2.580.2 and OpenJDK 21.0.13.1 were installed through Homebrew.
  Its LaunchAgent is running and uses the explicit OpenJDK 21 binary. The
  ordinary shell does not currently find `java` on `PATH`; for this Homebrew
  keg-only installation, set `JAVA_HOME=/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home`
  and add `$JAVA_HOME/bin` to `PATH` in the shell where Java commands are used.
  Jenkins 2.580.2 responds in the browser at `http://127.0.0.1:8080/login`.
  Shell `curl` from the current execution environment is refused despite the
  service listener; verify HTTP from Terminal on the Mac if needed. The
  Pipeline aggregator, Declarative Pipeline, Declarative Extension Points API,
  Model API, and core Workflow plugins are enabled after restart.
- The Global Secret text credential ID `flask-secret-key` is present with
  Global scope and Secret text type. Its value was not read. The existing job
  `SE-Final-CI-CD` is configured for the public repository, `*/main`, and the
  `Jenkinsfile` path. Its latest observed build (#4) failed at lightweight
  checkout because `Jenkinsfile` is not yet on remote `main`; no pipeline stage
  ran.
- Docker Desktop 4.99.0 is running from `~/Applications/Docker.app`. The
  Docker CLI is 29.9.3, Compose is 5.7.0, and the engine reports 29.9.3 on
  `aarch64`. `hello-world` ran successfully. This shell needs
  `~/.docker/bin` added to `PATH` to find the CLI and credential helper.
- The `se-final-app:latest` image built successfully. The `se-final-container`
  container is running with Gunicorn on `0.0.0.0:8000` inside Docker, published
  only as `127.0.0.1:8000`. The `/login` readiness request returned HTTP 200;
  the initialized database contains the seven expected SQLite tables.
- SQLite persistence was verified across container replacement using the new
  named volume `online-quiz-team73-data`. A temporary `PRAGMA user_version`
  marker survived replacement and was restored to its original value. No
  Docker volumes were deleted, and `Sprint2_S2-01_S2-14/quiz.db` was not used.
- The Jenkinsfile and Docker/application changes are local on a feature branch
  based on current `origin/main`. They must be merged into `main` before the
  saved job can retrieve and execute this Jenkinsfile. The changes remain
  staged and uncommitted per the user's direct instruction; they have not been
  pushed or opened as a PR.
- The Sprint 2 suite was rerun under Python 3.12.16: **64 passed**, **99%
  coverage**. HTML and XML coverage reports are in `/private/tmp` so no
  generated coverage artifacts were added to the project.
