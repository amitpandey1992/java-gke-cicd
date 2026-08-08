# AI-Powered CI/CD Failure Analyzer

![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-green)
![Ollama](https://img.shields.io/badge/Ollama-Llama3-orange)

An intelligent application that automatically analyzes CI/CD build failures using Generative AI. It connects to popular CI systems, retrieves failed logs, uses RAG (Retrieval-Augmented Generation) with past failures, and provides actionable summaries and fix suggestions.

## Architecture

```text
+-----------+    +-------------+     +-------------+
| CI/CD     |    | FastAPI     |     | LLM Engine  |
| (Jenkins, |--->| Analyzer    |---->| (Ollama /   |
| GitHub)   |    | API         |     |  Vertex AI) |
+-----------+    +-------------+     +-------------+
                        |
                 +------+------+
                 |             |
           +----------+  +----------+
           | Postgres |  | ChromaDB |
           | (Stats)  |  | (Memory) |
           +----------+  +----------+
```

## Features

- **Automated Log Retrieval**: Connects to Jenkins, GitHub Actions, and TeamCity APIs.
- **AI Analysis**: Uses Llama 3 (via Ollama) or Vertex AI to analyze build logs.
- **RAG Memory**: Remembers past fixes using ChromaDB similarity search.
- **Dashboard Metrics**: Stores statistics in PostgreSQL.
- **Slack Notifications**: Pushes AI summaries to Slack.

## Prerequisites

- Python 3.11+
- Docker and Docker Compose
- [Ollama](https://ollama.ai/) installed locally (if using local AI)

## Quick Start (Local Development)

1. **Clone the repository**
2. **Setup virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```
4. **Start infrastructure**:
   ```bash
   docker-compose up -d
   ```
5. **Run the API**:
   ```bash
   uvicorn app.main:app --reload
   ```

## VM Deployment Steps

To deploy on an Ubuntu 22.04 ARM VM (e.g., Oracle Cloud):

1. Upload the project files to the VM.
2. Run the setup script:
   ```bash
   chmod +x scripts/vm-setup.sh
   sudo ./scripts/vm-setup.sh
   ```

## API Documentation

Once the app is running, visit `http://localhost:8000/docs` for the interactive Swagger UI.

### Key Endpoints
- `POST /api/v1/analyze`: Trigger analysis for a specific build.
- `GET /api/v1/stats`: Retrieve historical failure statistics.
- `GET /health`: System health check.

## Configuration Reference

Check `.env.example` for all configurable variables. Key ones include:
- `AI_PROVIDER`: `ollama` or `vertex`
- `OLLAMA_MODEL`: Default `llama3`
- `JENKINS_URL`, `GITHUB_TOKEN`, etc.

## Project Structure

```
├── app/                  # Main application code
├── scripts/              # Setup and utility scripts
├── jenkins/              # Jenkins examples
├── github-actions/       # GitHub Actions examples
├── docker-compose.yml    # Infrastructure definitions
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

## Contributing

Pull requests are welcome! Please ensure code follows PEP 8 and includes appropriate type hints.

## License

This project is licensed under the MIT License.
