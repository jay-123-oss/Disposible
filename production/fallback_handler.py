"""Fallback handler utility providing safe degradation, default responses, and secondary path execution."""

from __future__ import annotations

import logging
from typing import Any, Callable, Optional


logger = logging.getLogger("FractalCore.Production.FallbackHandler")


class FallbackHandlerUtil:
    """Safe fallback executor guaranteeing zero crashes in production."""

    @staticmethod
    def execute_with_fallback(
        primary_fn: Callable,
        fallback_fn: Optional[Callable] = None,
        default_value: Any = None,
        *args,
        **kwargs,
    ) -> Any:
        """Execute primary callable; on failure, invoke fallback or return default value."""
        try:
            return primary_fn(*args, **kwargs)
        except Exception as exc:
            logger.warning("Primary execution failed: %s. Engaging fallback...", exc)
            if fallback_fn is not None:
                try:
                    return fallback_fn(*args, **kwargs)
                except Exception as fb_exc:
                    logger.error("Fallback execution also failed: %s. Returning default value.", fb_exc)
            return default_value
