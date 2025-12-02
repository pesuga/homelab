"""Calendar Sub-Agent Package

Specialized sub-agent for handling calendar-related tasks:
- Creating, viewing, modifying events
- Checking availability and conflicts
- Managing recurring events
- Sending reminders
"""

from .agent import CalendarSubAgent
from .tools import CalendarMCPTools

__all__ = ["CalendarSubAgent", "CalendarMCPTools"]
