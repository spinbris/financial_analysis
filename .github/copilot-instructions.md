# AI Agent Instructions for Financial Research SDK

This codebase implements a modular financial research system using specialized AI agents. Here's what you need to know to work effectively with this code:

## Architecture Overview

The system follows a pipeline architecture with distinct stages:
1. Planning (`planner_agent.py`) - Converts user queries into search strategies
2. Search (`search_agent.py`) - Executes web searches for relevant financial data
3. Analysis (`financials_agent.py`, `risk_agent.py`) - Specialized analysts for specific aspects
4. Writing (`writer_agent.py`) - Synthesizes findings into structured reports
5. Verification (`verifier_agent.py`) - Validates report quality and completeness

Key file: `manager.py` orchestrates the entire workflow.

## Development Patterns

### Agent Configuration
- Agents are defined using the `Agent` class with specific instructions and output types
- Output types use Pydantic models for structured data (see `FinancialSearchPlan`, `FinancialReportData`)
- Example in `planner_agent.py`:
  ```python
  planner_agent = Agent(
      name="FinancialPlannerAgent",
      instructions=PROMPT,
      model="o3-mini",
      output_type=FinancialSearchPlan
  )
  ```

### Agent Communication
- Agents communicate through strongly-typed data models
- Sub-agents can be exposed as tools to other agents (see `_write_report` in `manager.py`)
- Custom output extractors handle specialized data transformations

### Async Operation
- All agent operations are async
- Use `Runner.run()` for single operations
- Use `Runner.run_streamed()` for long-running operations with progress updates

## Key Workflows

### Running the Agent
```bash
python -m examples.financial_research_agent.main
```

### Development
1. New agents should be added to `financial_research_agent/agents/`
2. Update `manager.py` to integrate new agents into the pipeline
3. Define Pydantic models for structured data exchange

## Integration Points
- Uses OpenAI's trace system for monitoring
- Web search integration for data gathering
- Rich console for progress display

## Common Tasks

### Adding a New Agent
1. Create new file in `agents/` directory
2. Define output model using Pydantic
3. Create agent with instructions and model
4. Update `manager.py` to integrate the agent

### Modifying the Pipeline
- Edit `FinancialResearchManager.run()` in `manager.py`
- Each stage is implemented as a separate async method

## Known Patterns
- Use `custom_span` for tracing specific operations
- Progress updates use `printer.update_item()` for user feedback
- Error handling relies on try/except in search operations