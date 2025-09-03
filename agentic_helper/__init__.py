"""Agentic Helper package

Provides modular components for the AI planning assistant:
- config: environment and settings
- logging_config: central logger setup
- models: Pydantic data models
- llm: LLM provider setup
- utils: helper utilities (plan formatting, progress, etc.)
- tools: LangChain tools for planning and management
- agent: Planning agent built on LangGraph
"""

import warnings

# Suppress noisy deprecation warnings from Pydantic v2 triggered by LangChain tools
try:
    from pydantic.warnings import PydanticDeprecatedSince20

    warnings.filterwarnings(
        "ignore",
        message=r".*`__fields__` attribute is deprecated.*",
        category=PydanticDeprecatedSince20,
        module=r"langchain_core.tools.base",
    )
except Exception:
    # Fallback: best-effort suppression by message if category import fails
    warnings.filterwarnings(
        "ignore",
        message=r".*`__fields__` attribute is deprecated.*",
        module=r"langchain_core.tools.base",
    )

__all__ = [
    "config",
    "logging_config",
    "models",
    "llm",
    "utils",
    "tools",
    "agent",
]
