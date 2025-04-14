import os
import json
import re
import logging
from typing import Any, Dict, List, TypedDict

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('openai').setLevel(logging.WARNING)

class TutorState(TypedDict):
    user_profile: Dict[str, Any]
    current_course: str
    current_lesson: str
    history: List[Dict[str, str]]
    completed_courses: List[str]
    user_input: str
    analysis: Dict[str, Any]
    multi_requests: List[Dict[str, Any]]
    agent_responses: Dict[str, str]
    agent_partial_responses: Dict[str, List[str]]
    conversational_response: str
    context_references: Dict[str, Any]
    db_history: str
    should_exit: bool
