
---
title: AI SWE Agent
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
---

# AI SWE Agent

Repository-aware AI software engineering agent.


# 🚀 AI SWE Agent

An autonomous repository-aware AI Software Engineering Agent capable of cloning GitHub repositories, localizing bugs, generating multi-file fixes using LLMs, validating changes, preventing regressions, and executing code safely inside Docker sandboxes.

Built with Python, FastAPI, Docker, AST analysis, repository intelligence, and LLM-powered code generation.

---

# Demo

AI SWE Agent performs the following workflow automatically:

```text
Issue Description
        ↓
Repository Clone
        ↓
Repository Analysis
        ↓
Multi-File Context Building
        ↓
Bug Localization
        ↓
LLM Fix Generation
        ↓
AST Validation
        ↓
Regression Detection
        ↓
Docker Sandbox Execution
        ↓
Verified Fix Output
```

---

# Key Features

## Repository-Aware Bug Fixing

Unlike simple code assistants that only see a single file, AI SWE Agent understands:

* Repository structure
* Imports
* Call relationships
* Related files
* Multi-file dependencies

Example:

```text
src/flask/blueprints.py
src/flask/sansio/blueprints.py
```

The agent analyzes both files simultaneously before generating fixes.

---

## Automatic GitHub Repository Cloning

Given:

```json
{
  "repo_url": "https://github.com/pallets/flask",
  "issue": "Blueprint registration bug"
}
```

The system:

* Clones repository
* Creates isolated workspace
* Builds repository context
* Starts autonomous repair loop

---

## Multi-File Context Builder

The agent automatically discovers:

* Imports
* Callers
* Related files
* Symbol usage

Example:

```text
REPOSITORY PROFILE:
src/flask/blueprints.py

IMPORTS:
- flask.sansio.blueprints

RELATED FILES:
- src/flask/sansio/blueprints.py

CALLERS:
- Blueprint registration flow
```

---

## LLM-Powered Fix Generation

Supported Models:

* Llama 3.1 8B Instant
* Llama 3.3 70B Versatile

Features:

* Multi-model fallback
* Automatic retry
* Structured response parsing
* Repository-aware prompting

---

## Autonomous Retry Loop

The agent automatically retries when:

* LLM output is invalid
* Validation fails
* Regression is detected
* Rate limits occur

Example:

```text
ATTEMPT 1
↓
Validation Failed

ATTEMPT 2
↓
Retry Generation

ATTEMPT 3
↓
Validated Fix
```

---

## AST Validation

Generated code is parsed before execution.

Example:

```python
ast.parse(generated_code)
```

Detects:

* Syntax errors
* Unclosed strings
* Invalid Python structures
* Broken code generation

---

## Regression Detection Engine

The system prevents:

* Function deletion
* Class deletion
* Structural regressions

Example:

```text
Removed Function:
get_send_file_max_age

Removed Class:
BlueprintSetupState
```

Such changes are automatically rejected.

---

## Scope Validation

Ensures the LLM only modifies intended files.

Prevents:

* Unrelated changes
* Repository corruption
* Hallucinated file creation

---

## Docker Sandbox Execution

All generated code executes inside isolated Docker containers.

Benefits:

* Safe execution
* Dependency isolation
* No host system contamination

Repository validation mode:

```bash
python -m py_compile
```

is used for framework repositories to avoid import-chain failures.

---

## Automatic Rate Limit Recovery

Handles:

* API throttling
* Temporary model failures
* Fallback model switching

Example:

```text
RATE_LIMIT
↓
Wait
↓
Fallback Model
↓
Retry
```

---

## Observability & Debug Logging

Built-in tracing includes:

```text
DEBUG BEFORE_LLM
DEBUG AFTER_LLM

DEBUG BEFORE_PARSE
DEBUG AFTER_PARSE

DEBUG BEFORE_SCOPE
DEBUG AFTER_SCOPE

DEBUG BEFORE_REGRESSION
DEBUG AFTER_REGRESSION

MODEL_RESPONSE_LEN
FILE_CONTEXT_LEN
```

Useful for debugging autonomous agent behavior.

---

# Architecture

```text
                 ┌───────────────┐
                 │ GitHub Repo   │
                 └───────┬───────┘
                         │
                         ▼
              ┌──────────────────┐
              │ Repository Clone │
              └────────┬─────────┘
                       │
                       ▼
             ┌────────────────────┐
             │ Context Builder    │
             └─────────┬──────────┘
                       │
                       ▼
             ┌────────────────────┐
             │ Bug Localization   │
             └─────────┬──────────┘
                       │
                       ▼
             ┌────────────────────┐
             │ LLM Generation     │
             └─────────┬──────────┘
                       │
                       ▼
             ┌────────────────────┐
             │ AST Validation     │
             └─────────┬──────────┘
                       │
                       ▼
             ┌────────────────────┐
             │ Regression Check   │
             └─────────┬──────────┘
                       │
                       ▼
             ┌────────────────────┐
             │ Docker Execution   │
             └─────────┬──────────┘
                       │
                       ▼
                Verified Fix
```

---

# Tech Stack

Backend

* Python
* FastAPI

AI

* Groq API
* Llama 3.1 8B
* Llama 3.3 70B

Repository Processing

* GitPython
* AST Analysis

Execution

* Docker

Validation

* AST Validation
* Scope Validation
* Regression Validation

Infrastructure

* Uvicorn
* REST APIs

---

# API

## Run Agent

```http
POST /api/run-agent
```

Request:

```json
{
  "repo_url": "https://github.com/pallets/flask",
  "issue": "Blueprint registration issue"
}
```

Response:

```json
{
  "task_id": "12345"
}
```

---

## Get Task Status

```http
GET /api/task/{task_id}
```

Response:

```json
{
  "status": "running",
  "logs": [],
  "result": {}
}
```

---

# Example Test Payloads

## Flask

```json
{
  "repo_url": "https://github.com/pallets/flask",
  "issue": "Blueprint registration issue causes incorrect route registration."
}
```

## Requests

```json
{
  "repo_url": "https://github.com/psf/requests",
  "issue": "Session cookies are not persisted correctly between requests."
}
```

## FastAPI

```json
{
  "repo_url": "https://github.com/fastapi/fastapi",
  "issue": "Dependency injection fails when using nested routers."
}
```

## Django

```json
{
  "repo_url": "https://github.com/django/django",
  "issue": "URL reverse lookup fails for nested namespaces."
}
```

---

# Future Roadmap

* Git diff generation
* Pull request generation
* SWE-bench evaluation
* Multi-language support
* Agent benchmarking
* Parallel repository analysis
* Test-suite execution
* Code coverage validation

---

# Resume Impact

This project demonstrates:

* AI Engineering
* Backend Development
* Distributed Systems Thinking
* Dockerization
* Repository Analysis
* Static Analysis
* Autonomous Agents
* LLM Integration
* Software Validation Pipelines
* Production Engineering

---

# Author

Vamshi Durgam

Python Backend Developer | AI Tooling Engineer | Full Stack Developer
