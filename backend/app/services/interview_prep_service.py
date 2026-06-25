from sqlalchemy.orm import Session
from backend.app.models.extended_models import InterviewAttempt
import re

class InterviewPrepService:
    QUESTION_BANK = {
        "Technical": {
            "Easy": [
                "What is the difference between a list and a tuple in Python?",
                "What is a primary key in a database, and why is it important?",
                "Explain the difference between GET and POST HTTP requests."
            ],
            "Medium": [
                "How does FastAPI handle asynchronous requests using async/await?",
                "Explain how indexes work in PostgreSQL and how they speed up queries.",
                "What is the difference between a relational database and a NoSQL database?"
            ],
            "Hard": [
                "Explain the difference between optimistic and pessimistic locking in concurrent transactions.",
                "How does the GIL (Global Interpreter Lock) in Python affect multi-threading and multi-processing?",
                "Design a distributed rate-limiting system for a high-traffic REST API."
            ]
        },
        "HR": {
            "Easy": [
                "Tell me about yourself and your professional background.",
                "Why are you interested in joining our company?",
                "What are your long-term career aspirations?"
            ],
            "Medium": [
                "What is your greatest strength and weakness, and how are you addressing the weakness?",
                "Where do you see yourself in 3 to 5 years?",
                "How do you handle high-pressure deadlines or heavy workloads?"
            ],
            "Hard": [
                "Why should we hire you over other candidates with similar technical backgrounds?",
                "Describe a situation where you disagreed with a manager. How did you handle it?",
                "What are your salary expectations, and how do you justify them based on your experience?"
            ]
        },
        "Behavioral": {
            "Easy": [
                "Describe a project you built that you are proud of.",
                "How do you manage your time when working on multiple tasks?",
                "Tell me about a time you worked closely with a team member."
            ],
            "Medium": [
                "Describe a time when you made a mistake on a project. How did you fix it and what did you learn?",
                "Explain a situation where you had to prioritize competing project requirements.",
                "Tell me about a time you went above and beyond your standard responsibilities."
            ],
            "Hard": [
                "Give an example of a time you led a team under severe constraints or tight timelines.",
                "Describe a scenario where you had to adapt to a sudden, major change in project goals.",
                "Tell me about a time you successfully convinced stakeholders to adopt a controversial design pattern."
            ]
        },
        "Coding": {
            "Easy": [
                "Write a function to check if a given string is a palindrome.",
                "Find the maximum and minimum numbers in an unsorted array.",
                "Reverse a singly linked list in-place."
            ],
            "Medium": [
                "Given an array of integers, return the indices of the two numbers that add up to a specific target.",
                "Implement a basic token-bucket rate limiting algorithm.",
                "Find the longest substring without repeating characters."
            ],
            "Hard": [
                "Design and implement an LRU (Least Recently Used) cache with O(1) operations.",
                "Write a function to merge k sorted linked lists.",
                "Implement a Trie (Prefix Tree) data structure supporting insert, search, and startsWith."
            ]
        }
    }

    KEYWORD_EVALUATION = {
        "list and a tuple": ["immutable", "mutable", "syntax", "brackets", "parentheses", "memory"],
        "primary key": ["unique", "identifier", "null", "index", "foreign key"],
        "get and post": ["url", "body", "idempotent", "secure", "parameters", "headers"],
        "fastapi": ["async", "await", "concurrency", "event loop", "uvicorn", "non-blocking"],
        "indexes": ["b-tree", "scan", "lookup", "overhead", "write", "speed"],
        "relational database": ["sql", "nosql", "schema", "acid", "document", "scale", "joins"],
        "locking": ["concurrent", "optimistic", "pessimistic", "deadlock", "version", "row"],
        "gil": ["thread", "concurrency", "cpu-bound", "io-bound", "parallel", "multiprocessing"],
        "rate-limiting": ["redis", "token bucket", "window", "ip", "distributed", "middleware"],
        "tell me about yourself": ["experience", "projects", "skills", "passion", "career"],
        "why are you interested": ["culture", "mission", "values", "growth", "product"],
        "long-term": ["senior", "architect", "lead", "skills", "management"],
        "strength and weakness": ["learning", "adaptable", "communication", "focus", "initiative"],
        "3 to 5 years": ["growth", "expert", "lead", "responsibilities", "impact"],
        "high-pressure": ["prioritize", "break down", "communicate", "agile", "calm"],
        "why should we hire": ["fit", "value", "experience", "motivated", "contribute"],
        "disagreed": ["listen", "data", "compromise", "respect", "professional"],
        "salary": ["market", "value", "experience", "flexible", "benefits"],
        "project you built": ["architected", "implemented", "impact", "learned", "stack"],
        "time": ["calendar", "jira", "prioritize", "deadlines", "trello"],
        "closely with a team": ["collaboration", "communication", "shared", "supported", "git"],
        "mistake": ["owned", "resolved", "learned", "prevented", "communicated"],
        "prioritize": ["impact", "effort", "moscow", "urgency", "stakeholders"],
        "above and beyond": ["initiative", "extra", "impact", "documentation", "mentored"],
        "constraints": ["delegated", "scoped", "milestones", "mvp", "communicated"],
        "sudden": ["agile", "refactored", "pivoted", "flexible", "collaborated"],
        "convinced": ["data", "demo", "metrics", "roi", "trade-offs"],
        "palindrome": ["reverse", "pointers", "o(n)"],
        "maximum and minimum": ["loop", "o(n)", "comparison"],
        "linked list": ["pointer", "next", "prev", "head", "node"],
        "two numbers": ["hashmap", "dictionary", "complement", "indices", "o(n)"],
        "token-bucket": ["capacity", "refill", "timestamp", "tokens"],
        "longest substring": ["sliding window", "hashset", "pointers", "o(n)"],
        "lru": ["hashmap", "doubly linked list", "head", "tail", "o(1)"],
        "k sorted": ["heap", "priority queue", "divide and conquer", "merge"],
        "trie": ["node", "children", "end of word", "prefix", "character"]
    }

    @classmethod
    def get_questions(cls, category: str, difficulty: str) -> list[str]:
        return cls.QUESTION_BANK.get(category, {}).get(difficulty, [
            "Explain your technical experience.",
            "Describe a complex architectural problem you solved.",
            "What is your approach to system testing?"
        ])

    @classmethod
    def submit_attempt(cls, db: Session, user_id: int, category: str, difficulty: str, questions: list[str], answers: list[str]) -> InterviewAttempt:
        score_sum = 0
        feedbacks = []

        for idx, (question, answer) in enumerate(zip(questions, answers)):
            # Heuristic evaluator: check answer length & relevant keywords
            words = answer.strip().split()
            word_count = len(words)
            
            # Base score on length (up to 40 points)
            length_score = min(40, (word_count / 15) * 10)
            
            # Match keywords (up to 60 points)
            keyword_score = 0
            matching_key = None
            for key in cls.KEYWORD_EVALUATION:
                if key in question.lower():
                    matching_key = key
                    break
                    
            if matching_key:
                req_keywords = cls.KEYWORD_EVALUATION[matching_key]
                found_kws = [kw for kw in req_keywords if kw in answer.lower()]
                kw_ratio = len(found_kws) / len(req_keywords)
                keyword_score = kw_ratio * 60
                feedback_txt = f"Found {len(found_kws)} relevant concepts: {', '.join(found_kws)}. "
                if len(found_kws) < len(req_keywords) // 2:
                    feedback_txt += f"To improve, consider incorporating concepts like: {', '.join(list(set(req_keywords) - set(found_kws))[:3])}."
                else:
                    feedback_txt += "Great usage of domain-specific terminology."
            else:
                # Default generic keyword search
                default_kws = ["engineered", "implemented", "optimized", "team", "learned", "structure"]
                found_kws = [kw for kw in default_kws if kw in answer.lower()]
                keyword_score = (len(found_kws) / len(default_kws)) * 60
                feedback_txt = f"Good detail. Try to be more specific in explaining technical implementations."

            q_score = int(length_score + keyword_score)
            q_score = max(10, min(100, q_score))
            score_sum += q_score
            
            feedbacks.append({
                "question": question,
                "score": q_score,
                "word_count": word_count,
                "feedback": feedback_txt
            })

        overall_score = int(score_sum / max(1, len(questions)))
        
        # Structure feedback dictionary
        feedback_data = {
            "overall_feedback": (
                "Excellent job! You demonstrated deep technical knowledge." if overall_score >= 80 
                else "Solid performance. Work on explaining key concepts with more details and structured terms." if overall_score >= 50
                else "Consider practicing the technical keywords and structure your answers using the STAR method (Situation, Task, Action, Result)."
            ),
            "question_breakdowns": feedbacks
        }

        # Save to DB
        attempt = InterviewAttempt(
            user_id=user_id,
            category=category,
            difficulty=difficulty,
            questions=questions,
            answers=answers,
            score=overall_score,
            feedback=feedback_data
        )
        db.add(attempt)
        db.commit()
        db.refresh(attempt)
        
        return attempt

    @staticmethod
    def get_attempts_history(db: Session, user_id: int) -> list[InterviewAttempt]:
        return db.query(InterviewAttempt).filter(InterviewAttempt.user_id == user_id).order_by(InterviewAttempt.created_at.desc()).all()
