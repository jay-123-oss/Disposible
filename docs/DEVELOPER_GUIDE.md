# Developer Guide

## System Principles
- **Fractal Decomposition**: Problem solving is decomposed through self-similar agent structures.
- **Separation of Concerns**: Core infrastructure (`core/`) is strictly decoupled from domain agents (`agents/`).
- **Deterministic Fallbacks**: Agents operate gracefully even when external LLM endpoints are unavailable.
