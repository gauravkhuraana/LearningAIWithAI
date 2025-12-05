# GitHub Copilot Instructions for LearningAIWithAI

## Project Overview

This is an **AI experimentation repository** focused on exploring Azure OpenAI integration patterns, multi-agent systems, and LLM optimization techniques. The codebase demonstrates different approaches to building AI-powered applications using Azure services.

## Architecture & Key Patterns

### Multi-Agent Systems (Two Approaches)

**1. Azure AI Agents SDK** (`multiAgentAzure.py`)
- Uses native `azure.ai.agents` with `ConnectedAgentTool` for agent-to-agent communication
- Authentication via `DefaultAzureCredential` (excludes environment/managed identity)
- Requires `PROJECT_ENDPOINT` env var for Azure AI project

**2. OpenAI SDK with Azure** (`multiAgentOpenAI.py`)
- Uses `openai.AzureOpenAI` with Assistants API (beta)
- Manual orchestration: create assistants → create thread → run sequentially → collect results
- Deprecation warning suppressed for Assistants API (transitioning to Responses API)
- Each agent runs against the same thread for context sharing

**Key Difference**: Azure SDK has built-in orchestration; OpenAI SDK requires manual coordination.

### MCP (Model Context Protocol) Integration

**Educational File** (`mcpADOagent.py`)
- Demonstrates Semantic Kernel integration with MCP servers
- **IMPORTANT**: `from semantic_kernel.connectors.mcp import MCPPlugin` may not exist in current versions
- Shows architectural pattern: `User Prompt → AI Model → MCP Tools → External API → Results`
- Contains async function that's never called (intentional for reference)

### TOON Format Optimization

**Token Reduction** (`toonVsJson.py`)
- Demonstrates TOON format: 20-60% token reduction vs JSON
- Uses `tiktoken` for token counting with Azure OpenAI
- Pattern: encode data → send to LLM → decode response
- Install TOON from GitHub: `git+https://github.com/toon-format/toon-python.git`

## Environment Setup

### Required Environment Variables (`.env`)
```env
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
PROJECT_ENDPOINT=https://your-project-endpoint.azurewebsites.net/  # For Azure AI Agents
```

**Critical**: Always use `python-dotenv` and `load_dotenv()` at the start of scripts.

## Development Workflows

### Running Examples
```bash
# Install dependencies
pip install -r requirements.txt

# Run TOON comparison demo
python toonVsJson.py

# Run multi-agent examples
python multiAgentAzure.py      # Azure AI Agents SDK
python multiAgentOpenAI.py     # OpenAI Assistants API
```

### Console Clearing Pattern
All scripts start with: `os.system('cls' if os.name=='nt' else 'clear')`

## Project-Specific Conventions

### Import Organization
1. Standard library (`os`, `warnings`)
2. Third-party (`dotenv`, `openai`, `azure.*`)
3. Local imports (currently none)

### Agent Instruction Pattern
```python
agent_instructions = """
Clear, concise instructions in triple-quoted docstring.
Use specific examples and structured output formats.
"""
```

### Error Handling
- Suppress deprecation warnings: `warnings.filterwarnings("ignore", category=DeprecationWarning)`
- Use environment variables with fallbacks: `os.getenv("KEY", "default")`
- **Known Issue**: `mcpADOagent.py` lacks env var validation (will raise KeyError)

## Custom AI Agents (.github/agents/)

Three specialized agents for testing and quality:

1. **codeReviewer.agent.md**: Code quality, security, performance reviews
2. **SeniorTestArchitect.agent.md**: Strategic test case design (70% positive, 20% edge, 10% negative)
3. **TestDataGenerator.agent.md**: Test data with boundaries and security payloads

**Usage**: Reference with `@codeReviewer`, `@SeniorTestArchitect`, `@TestDataGenerator` in Copilot Chat

## Azure OpenAI Integration Patterns

### API Version Management
- Current: `2024-05-01-preview` (OpenAI SDK)
- Assistants API is deprecated → transitioning to Responses API
- Always check Azure OpenAI docs for latest supported versions

### Authentication Patterns
```python
# Pattern 1: API Key (OpenAI SDK)
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

# Pattern 2: DefaultAzureCredential (Azure SDK)
agents_client = AgentsClient(
    endpoint=project_endpoint,
    credential=DefaultAzureCredential(
        exclude_environment_credential=True,
        exclude_managed_identity_credential=True
    )
)
```

## Dependencies & Known Issues

### Critical Dependencies
- `azure-ai-agents>=1.0.0` - Azure AI Agents SDK
- `openai>=1.0.0` - OpenAI SDK with Azure support
- `semantic-kernel>=1.0.0` - **Warning**: MCP plugin path may be incorrect
- `tiktoken>=0.5.0` - Token counting for GPT models

### Known Limitations
1. **mcpADOagent.py**: Semantic Kernel MCP integration not fully functional
2. **multiAgentOpenAI.py**: Using deprecated Assistants API (working but transitioning)
3. **No tests**: Project is experimental, no test suite exists

## When Adding New Features

1. **Multi-Agent Systems**: Choose Azure SDK for production, OpenAI SDK for experimentation
2. **Token Optimization**: Consider TOON format for high-volume LLM calls
3. **Environment Config**: Always add new vars to `.env.example` with documentation
4. **Agent Definitions**: Add custom agents to `.github/agents/` following existing patterns
5. **Educational Code**: Include architectural diagrams and "why" explanations (see `mcpADOagent.py`)

## Quick Reference

**Start a new AI experiment:**
1. Create Python file with dotenv pattern
2. Add Azure OpenAI client initialization
3. Clear console at start
4. Use descriptive agent instructions
5. Document the "why" with comments

**Test Azure connection:**
```python
from openai import AzureOpenAI
client = AzureOpenAI(...)
response = client.chat.completions.create(
    model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    messages=[{"role": "user", "content": "Hello"}]
)
```
