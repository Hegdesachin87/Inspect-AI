# test-an-llm-with-inspect-ai

- Created at: 2025-08-21
- Created by: `🐢 Arun Godwin Patel @ Code Creations`

## Table of contents

- [Setup](#setup)
  - [System](#system)
  - [Installation](#installation)
- [Walkthrough](#walkthrough)
  - [Code Structure](#code-structure)
  - [Tech stack](#tech-stack)
  - [Build from scratch](#build-from-scratch)
    - [1. Create a virtual environment](#1-create-a-virtual-environment)
    - [2. Activate the virtual environment](#2-activate-the-virtual-environment)
    - [3. Install the required packages](#3-install-the-required-packages)
    - [4. Setup evaluations](#4-setup-evaluations)
    - [5. View logs](#5-view-logs)

## Setup

### System

This code repository was tested on the following computers:

- Windows 11

At the time of creation, this code was built using `Python 3.13.7`

### Installation

1. Install `virtualenv`

```bash
# 1. Open a CMD terminal
# 2. Install virtualenv globally
pip install virtualenv
```

2. Create a virtual environment

```bash
python -m venv venv
```

3. Activate the virtual environment

```bash
# Windows
.\venv\Scripts\activate
# Mac
source venv/bin/activate
```

4. Install the required packages

```bash
pip install -r requirements.txt
```

5. Run the scripts

```bash
python tasks/hello_world.py
python tasks/theory_of_mind.py
python tasks/gsm8k.py
...
```

## Walkthrough

### Code Structure

The code directory structure is as follows:

```plaintext
test-an-llm-with-inspect-ai
logs
tasks
|   └──hello_world.py
|   └──theory_of_mind.py
|   └──gs8mk.py
|   └──...
│   .gitignore
│   README.md
│   requirements.txt
```

The `logs/` folder is automatically created when you run one of the evaluation scripts. It contains the log file for the evaluation run.

The `tasks/` folder contains scripts that include tasks for the evaluation runs.

The `.gitignore` file specifies the files and directories that should be ignored by Git.

The `requirements.txt` file lists the Python packages required by the application.

### Tech stack

**LLM**

- `OpenAI`

**Evaluation**

- `Inspect AI`: https://inspect.aisi.org.uk/

### Build from scratch

#### 1. Create a virtual environment

```bash
python -m venv venv
```

#### 2. Activate the virtual environment

```bash
# Windows
.\venv\Scripts\activate
# Mac
source venv/bin/activate
```

#### 3. Install the required packages

```bash
pip install -r requirements.txt
```

#### 4. Setup evaluations

```bash
inspect eval tasks/hello_world.py --model openai/gpt-4o-mini
inspect eval tasks/theory_of_mind.py --model openai/gpt-4o-mini
inspect eval tasks/gsm8k.py --model openai/gpt-4o-mini
```

#### 5. View logs

```bash
inspect view
```

This completes the evaluation of an LLM using the Inspect AI framework!

## Happy coding! 🚀

```bash
🐢 Arun Godwin Patel @ Code Creations
```
