"""
Interview State Machine for RIPIS
Manages the flow and state of the mock interview.
"""
from enum import Enum, auto
from typing import Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import json
import os
import sys
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.ai_engine import AIEngine
from core.prompt_templates import (
    GREETING_PROMPT, TOPIC_SELECTION_PROMPT, QUESTION_PROMPT,
    FEEDBACK_PROMPT, HINT_PROMPT, FOLLOW_UP_PROMPT, CLOSING_PROMPT
)
from config import QUESTIONS_DIR


class InterviewState(Enum):
    """States of the interview flow."""
    IDLE = auto()
    GREETING = auto()
    TOPIC_SELECTION = auto()
    QUESTION_PRESENTING = auto()
    CANDIDATE_SOLVING = auto()
    GIVING_HINT = auto()
    FOLLOW_UP = auto()
    CLOSING = auto()
    ENDED = auto()


@dataclass
class InterviewContext:
    """Holds the current interview context."""
    interview_type: str = ""
    difficulty: str = "medium"
    current_question: str = ""
    current_code: str = ""
    hints_given: int = 0
    questions_asked: list = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    transcript: list = field(default_factory=list)  # List of (speaker, text) tuples
    
    # Retry tracking to prevent repetitive questions
    follow_up_attempts: int = 0
    max_retries: int = 5  # 5 attempts before moving on
    last_question_type: str = ""  # Track what we last asked about
    
    # Mistake tracking for end-of-interview feedback
    mistakes: list = field(default_factory=list)  # List of {"question": str, "wrong_answer": str, "correction": str}


class InterviewStateMachine:
    """Manages the interview flow and state transitions."""
    
    def __init__(self, ai_engine: AIEngine):
        self.ai_engine = ai_engine
        self.state = InterviewState.IDLE
        self.context = InterviewContext()
        self.questions_bank = self._load_questions()
        
        # Callbacks for UI updates
        self.on_state_change: Optional[Callable[[InterviewState], None]] = None
        self.on_ai_response: Optional[Callable[[str], None]] = None
        self.on_editor_write: Optional[Callable[[str], None]] = None
        
    def _load_questions(self) -> dict:
        """Load questions from the questions bank."""
        questions_file = os.path.join(QUESTIONS_DIR, "dsa_questions.json")
        if os.path.exists(questions_file):
            with open(questions_file, 'r') as f:
                return json.load(f)
        return self._get_default_questions()
    
    def _get_default_questions(self) -> dict:
        """Return default questions if no file exists."""
        return {
            "DSA": {
                "easy": [
                    {
                        "title": "Two Sum",
                        "description": """Given an array of integers 'nums' and an integer 'target', return indices of the two numbers such that they add up to target.

You may assume that each input would have exactly one solution, and you may not use the same element twice.

Example:
Input: nums = [2, 7, 11, 15], target = 9
Output: [0, 1]
Explanation: Because nums[0] + nums[1] == 9, we return [0, 1].""",
                        "hints": [
                            "Think about what complement you need for each number",
                            "A hash map can help you look up values in O(1) time",
                            "For each number, check if (target - number) exists in your hash map"
                        ],
                        "follow_ups": [
                            "What's the time complexity of your solution?",
                            "Can you solve it in one pass?",
                            "What if there could be multiple valid pairs?"
                        ]
                    },
                    {
                        "title": "Valid Parentheses",
                        "description": """Given a string containing just the characters '(', ')', '{', '}', '[' and ']', determine if the input string is valid.

An input string is valid if:
1. Open brackets must be closed by the same type of brackets.
2. Open brackets must be closed in the correct order.

Example 1: Input: "()" → Output: true
Example 2: Input: "()[]{}" → Output: true
Example 3: Input: "(]" → Output: false""",
                        "hints": [
                            "Think about what data structure helps with matching pairs in order",
                            "A stack is perfect for this - push opening brackets, pop for closing",
                            "When you see a closing bracket, the top of stack should be its matching opening bracket"
                        ],
                        "follow_ups": [
                            "What's the space complexity?",
                            "What if we only had one type of bracket?",
                            "How would you handle an empty string?"
                        ]
                    }
                ],
                "medium": [
                    {
                        "title": "Longest Substring Without Repeating Characters",
                        "description": """Given a string s, find the length of the longest substring without repeating characters.

Example 1:
Input: s = "abcabcbb"
Output: 3
Explanation: The answer is "abc", with the length of 3.

Example 2:
Input: s = "bbbbb"
Output: 1
Explanation: The answer is "b", with the length of 1.""",
                        "hints": [
                            "Think about using a sliding window approach",
                            "Use a set or hash map to track characters in current window",
                            "When you find a duplicate, shrink the window from the left"
                        ],
                        "follow_ups": [
                            "What's the time complexity?",
                            "Could you optimize the space usage?",
                            "What if the string contains unicode characters?"
                        ]
                    },
                    {
                        "title": "Container With Most Water",
                        "description": """You are given an integer array 'height' of length n. Find two lines that together with the x-axis form a container that holds the most water.

Return the maximum amount of water a container can store.

Example:
Input: height = [1,8,6,2,5,4,8,3,7]
Output: 49
Explanation: The max area is between index 1 (height 8) and index 8 (height 7).""",
                        "hints": [
                            "Think about what determines the area: width and the shorter height",
                            "Two pointers starting from both ends could be useful",
                            "Always move the pointer pointing to the shorter line - why?"
                        ],
                        "follow_ups": [
                            "Why do we move the shorter pointer?",
                            "Can we prove this greedy approach is optimal?",
                            "What's the time and space complexity?"
                        ]
                    }
                ]
            },
            "System Design": {
                "medium": [
                    {
                        "title": "Design a URL Shortener",
                        "description": """Design a URL shortening service like TinyURL.

Requirements:
- Given a long URL, generate a short unique alias
- When user accesses short URL, redirect to original
- Handle high read traffic
- URLs should expire after a configurable time

What components would you need? How would you handle the ID generation?""",
                        "hints": [
                            "Think about how to generate unique short IDs",
                            "Consider using base62 encoding for short URLs",
                            "Think about caching for frequently accessed URLs"
                        ],
                        "follow_ups": [
                            "How would you handle URL collisions?",
                            "How would you scale this to millions of URLs?",
                            "What database would you choose and why?"
                        ]
                    }
                ]
            }
        }
    
    def start_interview(self) -> str:
        """Start a new interview session."""
        print("[State] Starting interview...")
        self.state = InterviewState.GREETING
        self.context = InterviewContext()
        self.context.start_time = datetime.now()
        self.ai_engine.reset_conversation()
        
        if self.on_state_change:
            self.on_state_change(self.state)
        
        # Generate greeting
        print("[State] Generating greeting...")
        response = self.ai_engine.generate_response(GREETING_PROMPT)
        print(f"[State] Greeting response: {response[:100] if response else 'NONE'}...")
        self._add_to_transcript("AI", response)
        return response
    
    def process_user_input(self, user_input: str, current_code: str = "") -> str:
        """Process user input based on current state."""
        print(f"[State] Processing input in state {self.state.name}: {user_input[:50]}...")
        self._add_to_transcript("User", user_input)
        self.context.current_code = current_code
        
        if self.state == InterviewState.GREETING:
            return self._handle_greeting_response(user_input)
        elif self.state == InterviewState.TOPIC_SELECTION:
            return self._handle_topic_selection(user_input)
        elif self.state == InterviewState.CANDIDATE_SOLVING:
            return self._handle_solving_response(user_input)
        elif self.state == InterviewState.FOLLOW_UP:
            return self._handle_follow_up_response(user_input)
        elif self.state == InterviewState.GIVING_HINT:
            return self._handle_post_hint(user_input)
        else:
            print(f"[State] Unexpected state, generating contextual response")
            return self._generate_contextual_response(user_input)
    
    def _handle_greeting_response(self, user_input: str) -> str:
        """Handle response after greeting - detect topic and present question."""
        print(f"[State] Handling greeting response: {user_input[:50]}...")
        
        # Detect interview type from user input
        user_lower = user_input.lower()
        if "dsa" in user_lower or "data structure" in user_lower or "algorithm" in user_lower or "coding" in user_lower:
            self.context.interview_type = "DSA"
        elif "system" in user_lower or "design" in user_lower:
            self.context.interview_type = "System Design"
        elif "dbms" in user_lower or "database" in user_lower or "sql" in user_lower:
            self.context.interview_type = "DBMS"
        elif "os" in user_lower or "operating" in user_lower:
            self.context.interview_type = "Operating Systems"
        else:
            self.context.interview_type = "DSA"  # Default
        
        print(f"[State] Detected interview type: {self.context.interview_type}")
        
        # Skip topic confirmation - directly present the question
        # This avoids the AI generating two questions that get mixed
        return self._present_question()
    
    def _handle_topic_selection(self, user_input: str) -> str:
        """Handle topic selection and present question."""
        return self._present_question()
    
    def _present_question(self) -> str:
        """Present an AI-generated question to the candidate."""
        self.state = InterviewState.QUESTION_PRESENTING
        if self.on_state_change:
            self.on_state_change(self.state)
        
        interview_type = self.context.interview_type
        difficulty = self.context.difficulty
        
        # Have AI generate the question
        print(f"[State] Asking AI to generate a {interview_type} ({difficulty}) question...")
        prompt = QUESTION_PROMPT.format(
            interview_type=interview_type,
            difficulty=difficulty
        )
        response = self.ai_engine.generate_response(prompt)
        print(f"[State] AI question response: {response[:100] if response else 'NONE'}...")
        
        # Parse the AI response to extract question parts
        question_title, question_text, explanation = self._parse_question_response(response)
        
        print(f"[State] Parsed question title: {question_title}")
        
        # Store the question for context
        self.context.current_question = question_text
        self.context.questions_asked.append(question_title)
        self.context.hints_given = 0
        
        # Write the AI-generated question to the editor
        if self.on_editor_write:
            self.on_editor_write(f"/* Question: {question_title}\n\n{question_text}\n*/\n\n// Your solution:\n")
        
        # The explanation is what the AI will speak
        if not explanation:
            explanation = f"Alright, I've written the question in the editor. Take a look at the problem and walk me through your approach before you start coding."
        
        self._add_to_transcript("AI", explanation)
        
        self.state = InterviewState.CANDIDATE_SOLVING
        if self.on_state_change:
            self.on_state_change(self.state)
        
        return explanation
    
    def _parse_question_response(self, response: str) -> tuple:
        """Parse AI response to extract question title, text, and explanation."""
        import re
        
        question_title = "Interview Question"
        question_text = ""
        explanation = ""
        
        if not response:
            return question_title, "Please solve the problem.", "Let me give you a problem to work on."
        
        # Try to parse structured format with --- delimiters
        # Look for QUESTION_TITLE:
        title_match = re.search(r'QUESTION_TITLE:\s*(.+?)(?=---|$)', response, re.IGNORECASE | re.DOTALL)
        if title_match:
            question_title = title_match.group(1).strip().strip('"').strip("'")
        
        # Look for QUESTION_TEXT:
        text_match = re.search(r'QUESTION_TEXT:\s*(.+?)(?=VERBAL:|EXPLANATION:|$)', response, re.IGNORECASE | re.DOTALL)
        if text_match:
            question_text = text_match.group(1).strip()
        
        # Look for VERBAL: or EXPLANATION:
        exp_match = re.search(r'(?:VERBAL|EXPLANATION):\s*(.+?)$', response, re.IGNORECASE | re.DOTALL)
        if exp_match:
            explanation = exp_match.group(1).strip()
        
        # Fallback: if structured parsing failed, use the whole response
        if not question_text and not explanation:
            # Just use the whole response as explanation and create a simple question
            explanation = response
            question_text = response
        
        # Clean up any remaining delimiters
        question_title = question_title.replace('---', '').strip()
        question_text = question_text.replace('---', '').strip()
        explanation = explanation.replace('---', '').strip()
        
        return question_title, question_text, explanation
    
    def _handle_solving_response(self, user_input: str) -> str:
        """Handle candidate's response while solving."""
        print(f"[State] Handling solving response: {user_input[:50]}...")
        
        # Detect if input looks like garbage (likely speech recognition error)
        if self._is_garbage_input(user_input):
            print(f"[State] Detected garbage input, ignoring: {user_input}")
            return "I didn't catch that. Could you repeat?"
        
        # Check if they're asking for a hint
        if self._is_asking_for_hint(user_input):
            print("[State] User is asking for a hint")
            self.context.follow_up_attempts = 0  # Reset retry counter
            return self._give_hint()
        
        # Check if they seem done
        if self._seems_finished(user_input):
            print("[State] User seems finished")
            self.context.follow_up_attempts = 0  # Reset retry counter
            return self._ask_follow_up()
        
        # Track follow-up attempts to avoid repetition
        self.context.follow_up_attempts += 1
        print(f"[State] Follow-up attempt: {self.context.follow_up_attempts}/{self.context.max_retries}")
        
        # If we've asked too many times, move on
        if self.context.follow_up_attempts >= self.context.max_retries:
            print("[State] Max retries reached, moving on...")
            self.context.follow_up_attempts = 0
            return self._move_on_or_conclude()
        
        # Provide simple feedback without asking repetitive questions
        print("[State] Generating feedback...")
        prompt = FEEDBACK_PROMPT.format(
            question=self.context.current_question,
            current_code=self.context.current_code,
            user_speech=user_input,
            hints_given=self.context.hints_given
        )
        response = self.ai_engine.generate_response(prompt)
        print(f"[State] Feedback response: {response[:80] if response else 'NONE'}...")
        
        # Fallback if AI returns empty
        if not response:
            response = "[UNCLEAR] Okay, continue."
        
        # Check for [WRONG] tag and record the mistake
        if "[WRONG]" in response.upper():
            mistake = {
                "question": self.context.current_question[:100],
                "wrong_answer": user_input,
                "correction": response.replace("[WRONG]", "").replace("[wrong]", "").strip()
            }
            self.context.mistakes.append(mistake)
            print(f"[State] Recorded mistake: {user_input[:50]}...")
        
        # Clean up the tag for display (keep the correction visible)
        display_response = response
        for tag in ["[CORRECT]", "[WRONG]", "[UNCLEAR]", "[correct]", "[wrong]", "[unclear]"]:
            display_response = display_response.replace(tag, "").strip()
        
        self._add_to_transcript("AI", display_response)
        return display_response
    
    def _is_garbage_input(self, text: str) -> bool:
        """Check if input looks like speech recognition garbage."""
        if not text or len(text) < 3:
            return True
        
        # If it's just 'the' or similar short noise
        if text.lower().strip() in ["the", "a", "an", "uh", "um"]:
            return True
        
        # Check for nonsensical word patterns (too many short words in a row)
        words = text.split()
        if len(words) > 3:
            short_words = sum(1 for w in words if len(w) <= 2)
            if short_words / len(words) > 0.6:  # More than 60% are tiny words
                return True
        
        return False
    
    def _move_on_or_conclude(self) -> str:
        """Give feedback on mistakes, then move to next question or conclude."""
        
        # First, give feedback on any mistakes made on this question
        feedback = ""
        if self.context.mistakes:
            recent_mistakes = [m for m in self.context.mistakes if self.context.current_question[:50] in m['question']]
            if recent_mistakes:
                feedback = "Before we move on, let me give you some feedback. "
                for m in recent_mistakes[-2:]:  # Last 2 mistakes from this question
                    feedback += f"{m['correction']} "
                feedback += "\n\n"
        
        # Check if we should present another question or end
        if len(self.context.questions_asked) < 2:  # Allow up to 2 questions
            print("[State] Moving to next question with feedback...")
            next_question = self._present_question()
            return feedback + "Let's move on to the next problem. " + next_question
        else:
            print("[State] Concluding interview...")
            return feedback + self.end_interview()
    
    def _is_asking_for_hint(self, user_input: str) -> bool:
        """Check if user is asking for a hint."""
        hint_keywords = ["hint", "help", "stuck", "don't know", "not sure", "confused", "clue"]
        return any(kw in user_input.lower() for kw in hint_keywords)
    
    def _seems_finished(self, user_input: str) -> bool:
        """Check if user seems to have finished their solution."""
        done_keywords = ["done", "finished", "complete", "that's it", "that's my solution", "works", "should work"]
        return any(kw in user_input.lower() for kw in done_keywords)
    
    def _give_hint(self) -> str:
        """Provide a hint to the candidate."""
        self.state = InterviewState.GIVING_HINT
        if self.on_state_change:
            self.on_state_change(self.state)
        
        self.context.hints_given += 1
        hint_level = min(self.context.hints_given, 3)
        
        prompt = HINT_PROMPT.format(
            question=self.context.current_question,
            current_code=self.context.current_code,
            hints_given=self.context.hints_given - 1,
            hint_level=hint_level
        )
        response = self.ai_engine.generate_response(prompt)
        self._add_to_transcript("AI", response)
        
        self.state = InterviewState.CANDIDATE_SOLVING
        return response
    
    def _handle_post_hint(self, user_input: str) -> str:
        """Handle response after giving a hint."""
        self.state = InterviewState.CANDIDATE_SOLVING
        return self._handle_solving_response(user_input)
    
    def _ask_follow_up(self) -> str:
        """Ask a follow-up question."""
        self.state = InterviewState.FOLLOW_UP
        if self.on_state_change:
            self.on_state_change(self.state)
        
        prompt = FOLLOW_UP_PROMPT.format(
            question=self.context.current_question,
            current_code=self.context.current_code
        )
        response = self.ai_engine.generate_response(prompt)
        self._add_to_transcript("AI", response)
        return response
    
    def _handle_follow_up_response(self, user_input: str) -> str:
        """Handle response to follow-up question."""
        # Provide feedback on their follow-up answer
        prompt = f"""The candidate was asked a follow-up question after solving:
{self.context.current_question}

Their code:
```
{self.context.current_code}
```

Their follow-up response: "{user_input}"

Provide brief feedback (1-2 sentences). If this was a good answer, acknowledge it.
Then either ask another follow-up or transition to ending the interview."""

        response = self.ai_engine.generate_response(prompt)
        self._add_to_transcript("AI", response)
        
        # Check if we should end or continue
        if len(self.context.questions_asked) >= 2:
            return self.end_interview()
        
        return response
    
    def end_interview(self) -> str:
        """End the interview session."""
        self.state = InterviewState.CLOSING
        if self.on_state_change:
            self.on_state_change(self.state)
        
        self.context.end_time = datetime.now()
        
        # Build mistakes summary for the closing
        mistakes_summary = ""
        if self.context.mistakes:
            mistakes_summary = "MISTAKES MADE DURING INTERVIEW:\n"
            for i, mistake in enumerate(self.context.mistakes, 1):
                mistakes_summary += f"{i}. They said: \"{mistake['wrong_answer'][:50]}...\"\n"
                mistakes_summary += f"   Correction: {mistake['correction'][:100]}\n"
        else:
            mistakes_summary = "No major mistakes recorded during this interview."
        
        print(f"[State] Ending interview with {len(self.context.mistakes)} recorded mistakes")
        
        prompt = CLOSING_PROMPT.format(
            questions_covered=", ".join(self.context.questions_asked),
            mistakes_summary=mistakes_summary
        )
        response = self.ai_engine.generate_response(prompt)
        self._add_to_transcript("AI", response)
        
        self.state = InterviewState.ENDED
        return response
    
    def _generate_contextual_response(self, user_input: str) -> str:
        """Generate a contextual response for unexpected states."""
        response = self.ai_engine.generate_response(user_input)
        self._add_to_transcript("AI", response)
        return response
    
    def _add_to_transcript(self, speaker: str, text: str):
        """Add an entry to the transcript."""
        self.context.transcript.append({
            "speaker": speaker,
            "text": text,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_session_summary(self) -> dict:
        """Get a summary of the interview session."""
        return {
            "interview_type": self.context.interview_type,
            "questions_asked": self.context.questions_asked,
            "total_hints": self.context.hints_given,
            "duration": str(self.context.end_time - self.context.start_time) if self.context.end_time else "In progress",
            "transcript": self.context.transcript
        }
    
    def request_hint(self) -> str:
        """Explicitly request a hint (triggered by UI button)."""
        if self.state == InterviewState.CANDIDATE_SOLVING:
            return self._give_hint()
        return "Hints are available while solving a problem."
