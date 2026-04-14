"""
Metro Events — Models Package
Import all models here so Flask-Migrate can detect them.
"""

from .user import User
from .client import Client
from .event import Event
from .quote import Quote, QuoteItem
from .payment import Payment
from .task import Task
from .inventory import InventoryItem, Reservation
from .supplier import Supplier, PurchaseOrder
from .checklist import ChecklistItem
from .moodboard import MoodboardPeg
from .event_log import EventLog
from .after_event import AfterEvent
from .event_file import EventFile

__all__ = [
    "User", "Client", "Event", "Quote", "QuoteItem",
    "Payment", "Task", "InventoryItem", "Reservation",
    "Supplier", "PurchaseOrder", "ChecklistItem",
    "MoodboardPeg", "EventLog", "AfterEvent", "EventFile",
]
