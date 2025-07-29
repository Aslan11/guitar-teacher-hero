![Guitar Teacher Hero](./guitar-teacher-hero.png)

Based on [openai-agents-demos](https://github.com/temporal-community/openai-agents-demos)

This repository contains a single demo showcasing the OpenAI Agents Python SDK integrated with Temporal's durable execution. The remaining demos from the original project have been removed, leaving only the interactive guitar tab workflow.

More OpenAI Agents SDK samples can be found in Temporal's [samples-python repository](https://github.com/temporalio/samples-python/tree/main/openai_agents).

## Prerequisites

1. **Python 3.10+** - Required for the demos
2. **Temporal Server** - Must be running locally on `localhost:7233`
3. **OpenAI API Key** - Set as environment variable `OPENAI_API_KEY` (note, you will need enough quota on in your [OpenAI account](https://platform.openai.com/api-keys) to run this demo)
4. **PDF Generation Dependencies** - Required for PDF output (optional)

### Starting Temporal Server

```bash
# Install Temporal CLI
curl -sSf https://temporal.download/cli.sh | sh

# Start Temporal server
temporal server start-dev
```

## Setup

1. Clone this repository
2. Install dependencies:
   ```bash
   uv sync
   ```
3. Set your OpenAI API key:
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

### PDF Generation (optional)

For PDF generation functionality, you'll need WeasyPrint and its system dependencies:

#### macOS (using Homebrew)

```bash
brew install weasyprint
# OR install system dependencies for pip installation:
brew install pango glib gtk+3 libffi
```

#### Linux (Ubuntu/Debian)

```bash
# For package installation:
sudo apt install weasyprint

# OR for pip installation:
sudo apt install python3-pip libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0
```

#### Linux (Fedora)

```bash
# For package installation:
sudo dnf install weasyprint

# OR for pip installation:
sudo dnf install python-pip pango
```

#### Windows

1. Install Python from Microsoft Store
2. Install MSYS2 from https://www.msys2.org/
3. In MSYS2 shell: `pacman -S mingw-w64-x86_64-pango`
4. Set environment variable: `WEASYPRINT_DLL_DIRECTORIES=C:\msys64\mingw64\bin`

**Note:** PDF generation gracefully degrades when dependencies are unavailable - workflows will still generate markdown reports.

## Running the Demo

### Step 1: Start the Worker

In one terminal, start the worker that will handle the workflow:

```bash
uv run openai_agents/run_worker.py
```

Leave this running in the background. The worker registers the interactive guitar tab workflow and supporting activities.

### Step 2: Start the Interactive Workflow

In another terminal run the client script:

```bash
uv run openai_agents/run_interactive_guitar_tab_workflow.py "Teach me how to play Wonderwall on guitar"
```

### Interactive Guitar Tab Workflow

Learn guitar by generating tablature through an interactive multi-agent workflow. The workflow may ask clarifying questions before producing a markdown report and optional PDF.

**Files:**

- `openai_agents/workflows/guitar_tab_workflow.py` - Interactive guitar tab workflow
- `openai_agents/workflows/guitar_tab_agents/` - Guitar tab agent components
- `openai_agents/run_interactive_guitar_tab_workflow.py` - Interactive guitar tab client
- `openai_agents/workflows/pdf_generation_activity.py` - PDF generation activity

**Agents:**

- **Triage Agent**: Determines if clarifying questions are needed
- **Clarifying Agent**: Asks follow-up questions about the request
- **Instruction Agent**: Combines responses into a final instruction
- **Planner Agent**: Plans web searches for tabs or lessons
- **Search Agent**: Finds relevant tablature content
- **Writer Agent**: Produces markdown guitar tabs
- **PDF Generator Agent**: Converts markdown to PDF

**To run:**

```bash
uv run openai_agents/run_interactive_guitar_tab_workflow.py "Teach me how to play Wonderwall on guitar"
```

**Output:**

- `guitar_tab.md` - Markdown file with the tablature
- `pdf_output/<generated>.pdf` - PDF file if dependencies are installed

**Note:** The workflow may take a few minutes to finish due to searches and PDF generation.

## Project Structure

```
openai-agents-demos/
├── README.md                           # This file
├── pyproject.toml                      # Project dependencies
├── openai_agents/
│   ├── __init__.py
│   ├── run_worker.py                   # Worker that registers the workflow
│   ├── run_interactive_guitar_tab_workflow.py  # Client runner
│   └── workflows/
│       ├── __init__.py
│       ├── guitar_tab_workflow.py      # Workflow definition
│       ├── guitar_tab_manager.py       # Manager coordinating agents
│       ├── guitar_tab_agents/
│       │   ├── __init__.py
│       │   ├── clarifying_agent.py
│       │   ├── instruction_agent.py
│       │   ├── planner_agent.py
│       │   ├── search_agent.py
│       │   ├── triage_agent.py
│       │   └── writer_agent.py
│       ├── pdf_generation_activity.py  # PDF generation activity
│       └── research_agents/
│           ├── __init__.py
│           ├── pdf_generator_agent.py
│           └── research_models.py
```

## Development

### Code Quality Tools

```bash
# Format code
uv run -m black .
uv run -m isort .

# Type checking
uv run -m mypy --check-untyped-defs --namespace-packages .
uv run pyright .
```

## Key Features

- **Temporal Workflows**: Reliable orchestration using Temporal
- **OpenAI Agents**: Powered by the OpenAI Agents SDK for natural language processing
- **Interactive Workflow**: Supports clarifying questions before generating tablature
- **PDF Generation**: Optional PDF output alongside markdown

## License

MIT License - see the original project for full license details.
