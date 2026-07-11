"""AI investigation summaries and SAR generation (OpenAI + template fallback)."""

from app.ai.investigator import generate_investigation_summary
from app.ai.sar import generate_sar_sections

__all__ = ["generate_investigation_summary", "generate_sar_sections"]
