# AI-Powered Autonomous Code Remediation Agent

An intelligent, containerized agentic system designed to automate the localization and remediation of software bugs. This project demonstrates end-to-end AI engineering, moving from high-level objective planning to automated code execution and verification.

---

## 🚀 Project Overview
This system serves as an autonomous debugging assistant. Given a repository and a bug report, the agent:
1. **Analyzes** the codebase to identify the root cause.
2. **Plans** a remediation strategy.
3. **Executes** the fix in an isolated, containerized environment.
4. **Validates** the fix using automated test suites to ensure no regressions.

## 🏗️ System Architecture
The agent is built on a custom, state-machine-inspired architecture in Python, moving away from rigid frameworks to ensure granular control over the execution flow.

[Image of autonomous agent architecture showing reasoning engine, tool integration, and verification layer]

## 🛠️ Key Features
* **Autonomous Reasoning Loop:** A robust, state-based retry loop that manages the lifecycle of a debugging task, from analysis to verification.
* **Containerized Execution:** Uses Docker to isolate the sandbox, ensuring that code remediation and execution do not impact the host environment.
* **AST-Based Validation:** Implements Abstract Syntax Tree (AST) validation to ensure code changes are syntactically correct and follow project-specific constraints.
* **Regression Testing:** Automated integration with `pytest` to ensure that proposed fixes do not break existing functionality.
* **Error Resilience:** Built-in fault tolerance including automated retries with exponential backoff and circuit-breaking patterns for LLM API calls.

## ⚙️ Technical Stack
* **Core:** Python 3.12+
* **Orchestration:** Custom State-Machine Logic (AsyncIO)
* **API:** FastAPI (for task ingestion and status tracking)
* **Containers:** Docker / Docker Compose
* **Observability:** Structured JSON Logging & AST Validation
* **Testing:** Pytest

## 📈 Engineering Challenges Solved (The "10 LPA" Narrative)
* **Dependency & Runtime Isolation:** Resolved complex pathing and initialization errors by implementing a structured modular import system and containerized execution, ensuring 1:1 environment parity between development and production.
* **State Management:** Overcame the non-determinism of LLMs by implementing a rigorous retry loop that maintains state integrity across multiple attempts, preventing infinite recursion.
* **Context Window Optimization:** Engineered a context-builder that dynamically retrieves relevant repository files, significantly reducing token consumption while maintaining deep-context accuracy for the LLM.

## 🚀 How to Run
### Prerequisites
- Docker & Docker Compose
- Python 3.12+

### Quick Start
1. Clone the repository: `git clone <your-repo-link>`
2. Start the services: `docker-compose up --build`
3. Access the API documentation: Navigate to `http://localhost:8000/docs`

---
## 🧪 Testing
The project includes a comprehensive suite of unit tests. Run them via:
`docker-compose run backend pytest`

---
*Built as a production-ready AI engineering project, prioritizing system reliability, observability, and modular design.*