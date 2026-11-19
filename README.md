# Online Quiz System

**Software Engineering Mini Project | Team 73 | Project ID: 73**  
**PES University**

## 1. Project Overview

The Online Quiz System is a web-based application developed to provide an interactive platform for conducting timed multiple-choice quizzes. Users can register, log in, browse quiz categories, attempt quizzes, receive scores and answer-wise feedback, review their previous attempts, and compare their performance through a leaderboard.

The application also provides administrative functionality for managing quiz categories and questions.

## 2. Team Members

| Sl. No. | Team Member | SRN |
|---|---|---|
| 1 | Nakshathira | PES2UG24AM096 |
| 2 | Poojitha P. | PES2UG24AM112 |
| 3 | Sharanya N. | PES2UG24AM150 |
| 4 | Ragul Rajkumar S. | PES2UG24AM128 |

## 3. Key Features

### User Features
- User registration, login and logout.
- Browse available quiz categories.
- Select and attempt multiple-choice quizzes.
- Countdown timer with automatic submission on timeout.
- Automatic answer evaluation and score calculation.
- Detailed result reports with question-wise feedback.
- Persistent quiz attempt history.
- Leaderboard with quiz-wise filtering and ranking based on score and completion time.

### Administrator Features
- Role-based access to administrative functionality.
- Administrator dashboard.
- Add quiz categories.
- View quizzes and their questions.
- Add, edit and delete quiz questions.
- Input validation for question text, answer options and correct answers.

## 4. Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| Backend Framework | Flask |
| Database | SQLite |
| Frontend | HTML, CSS, JavaScript |
| Template Engine | Jinja2 |
| Authentication and Password Hashing | Werkzeug |
| Version Control | Git and GitHub |

## 5. Project Structure

```text
online-quiz-system/
│
├── Sprint1_S1-01_S1-06/
│   ├── app.py
│   ├── schema.sql
│   ├── init_db.py
│   ├── requirements.txt
│   ├── templates/
│   └── static/
│
├── Sprint2_S2-01_S2-14/
│   ├── app.py
│   ├── schema.sql
│   ├── init_db.py
│   ├── requirements.txt
│   ├── templates/
│   └── static/
│
├── Software requirement specification[SE].pdf
├── 73_SW_Architecture (1).pdf
├── Team 73_Project Test Plan.pdf
├── Team_73_jira_backlog.xlsx
├── Team73_Test_Cases (2).xlsx
├── Team73_Test_Cases_Evidence-2.docx
├── sprint_1_recording.mov
└── sprint_2_recording.mov
```

## 6. Installation and Execution

### Prerequisites
- Python 3
- pip
- Git

### Clone the repository

```bash
git clone https://github.com/OnlineQuizTeam73-SE/online-quiz-system.git
cd online-quiz-system
```

### Set up the Sprint 2 application

```bash
cd Sprint2_S2-01_S2-14

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

### Initialize the database

```bash
python init_db.py
```

**Important:** The initialization script recreates the local SQLite database and resets existing data. Run it only when setting up a fresh local database.

### Start the application

```bash
export SECRET_KEY="choose-a-long-random-value"   # optional for local testing, required for real use
python app.py                                      # add FLASK_DEBUG=1 to turn on Flask debug mode
```

Open the application in a browser:

```text
http://127.0.0.1:5000
```

## 7. Database

The application uses SQLite to store:

- User details and roles.
- Quiz categories.
- Quiz information and time limits.
- Multiple-choice questions and correct answers.
- Quiz results, scores and completion times.

Passwords are stored as hashes rather than plain-text values.

## 8. Testing and Verification

The team maintained a consolidated test register covering 30 test cases across authentication, quiz functionality, scoring, results, leaderboard, administrator access, security and usability.

Latest consolidated verification results:

| Status | Number of Test Cases |
|---|---:|
| PASS | 20 |
| PARTIAL | 10 |
| FAIL | 0 |
| **Total** | **30** |

Partial cases indicate that some acceptance conditions or evidence remain incomplete; they are not counted as fully passed.

Refer to `Team73_Test_Cases_Evidence-2.docx` for the detailed execution evidence.

## 9. Local Docker and Jenkins Demonstration

The Sprint 2 app can be built from the repository root and run at
`http://127.0.0.1:8000`. The Docker image uses Gunicorn and stores SQLite data
in the named volume `online-quiz-team73-data`; the host port is bound to
localhost only.

```bash
export PATH="$HOME/.docker/bin:$PATH"
docker build -t se-final-app .
docker volume create online-quiz-team73-data
export SECRET_KEY="$(python3.12 -c 'import secrets; print(secrets.token_urlsafe(48))')"
docker run --detach --name se-final-container --restart unless-stopped \
  --publish 127.0.0.1:8000:8000 \
  --volume online-quiz-team73-data:/data \
  --env APP_ENV=production \
  --env DATABASE_PATH=/data/quiz.db \
  --env SECRET_KEY \
  se-final-app
```

For Jenkins, install Docker Desktop and Jenkins LTS, configure a Secret text
credential with ID `flask-secret-key`, and create a Pipeline job from the
`main` branch and `Jenkinsfile`. Jenkins requires Python 3.12, Git, `curl`, and
access to the local Docker engine. The [Docker and Jenkins setup guide](docs/CICD_SETUP.md)
covers installation, safe database import, pipeline setup, persistence checks,
and troubleshooting.

The existing Sprint 2 tests passed **64 tests at 99% coverage** in the isolated
Python 3.12 test environment. Jenkins 2.580.2 and its Pipeline plugins are
installed, and the Jenkins UI responds in the browser. The Global Secret text
credential ID `flask-secret-key` exists. Docker Desktop 4.99.0 is running with
Docker 29.9.3 and Compose 5.7.0. The `se-final-app` image and a localhost-only
container are running; SQLite persistence passed a container replacement
check. The saved Pipeline job has not completed a build because remote `main`
does not yet contain the Jenkinsfile. See the verification record in the
setup guide for the current status.

## 10. Sprint Demonstrations

- [Sprint 1 Demonstration Video](sprint_1_recording.mov)
- [Sprint 2 Demonstration Video](sprint_2_recording.mov)

## 11. Project Documentation

- [Software Requirements Specification](<Software requirement specification[SE].pdf>)
- [Software Architecture](<73_SW_Architecture (1).pdf>)
- [Project Test Plan](<Team 73_Project Test Plan.pdf>)
- [Team 73 Jira Backlog](Team_73_jira_backlog.xlsx)
- [Test Cases Register](<Team73_Test_Cases (2).xlsx>)
- [Consolidated Test Evidence](Team73_Test_Cases_Evidence-2.docx)

## 12. Security Note

The application uses password hashing and role-based access restrictions. The supplied database initialization data is intended for local testing. Before any public deployment, configure a secure application secret, replace test credentials, and use HTTPS.

---

**Team 73 | Online Quiz System**  
Software Engineering Mini Project  
PES University
