"""User state management"""
from dataclasses import dataclass, field
from typing import List, Optional
from utils.api_client import BookInfo


@dataclass
class UserState:
    """State for a single user"""
    user_id: int
    intro_message: str = ""
    books: List[BookInfo] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    current_book_index: int = 0
    search_query: str = ""
    # Clarification flow state
    awaiting_clarification: bool = False
    original_vague_query: str = ""
    clarification_questions: str = ""

    def has_books(self) -> bool:
        """Check if user has books in state"""
        return len(self.books) > 0

    def get_current_book(self) -> Optional[BookInfo]:
        """Get current book"""
        if not self.has_books() or self.current_book_index >= len(self.books):
            return None
        return self.books[self.current_book_index]

    def get_current_recommendation(self) -> str:
        """Get current recommendation text"""
        if (not self.recommendations or
            self.current_book_index >= len(self.recommendations)):
            return ""
        return self.recommendations[self.current_book_index]

    def can_go_prev(self) -> bool:
        """Check if can go to previous book"""
        return self.current_book_index > 0

    def can_go_next(self) -> bool:
        """Check if can go to next book"""
        return self.current_book_index < len(self.books) - 1

    def go_prev(self):
        """Move to previous book"""
        if self.can_go_prev():
            self.current_book_index -= 1

    def go_next(self):
        """Move to next book"""
        if self.can_go_next():
            self.current_book_index += 1


class StateManager:
    """Singleton manager for user states"""
    _instance = None
    _states: dict[int, UserState] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StateManager, cls).__new__(cls)
        return cls._instance

    def get_state(self, user_id: int) -> UserState:
        """Get or create state for user"""
        if user_id not in self._states:
            self._states[user_id] = UserState(user_id=user_id)
        return self._states[user_id]

    def set_state(self, user_id: int, state: UserState):
        """Set state for user"""
        self._states[user_id] = state

    def clear_state(self, user_id: int):
        """Clear state for user"""
        if user_id in self._states:
            del self._states[user_id]

    def has_state(self, user_id: int) -> bool:
        """Check if user has state"""
        return user_id in self._states
