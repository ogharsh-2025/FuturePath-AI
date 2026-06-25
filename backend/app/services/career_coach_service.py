import uuid
from sqlalchemy.orm import Session
from backend.app.models.extended_models import ChatSession
from backend.app.repositories.resume_repository import ResumeRepository
from backend.app.repositories.recommendation_repository import RecommendationRepository
from backend.app.repositories.job_repository import JobRepository

class CareerCoachService:
    @staticmethod
    def get_session(db: Session, user_id: int, session_id: str = None) -> ChatSession:
        """
        Retrieves or creates a ChatSession for a given user.
        """
        if not session_id:
            session_id = str(uuid.uuid4())
            
        session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if not session:
            session = ChatSession(
                user_id=user_id,
                session_id=session_id,
                history=[]
            )
            db.add(session)
            db.commit()
            db.refresh(session)
        return session

    @classmethod
    def process_chat_message(cls, db: Session, user_id: int, message: str, session_id: str = None) -> dict:
        """
        Processes a chat message by matching intent and using user database context.
        """
        session = cls.get_session(db, user_id, session_id)
        
        # Load user context
        resume = ResumeRepository.get_by_user_id(db, user_id)
        skills = [s.skill_name for s in resume.skills] if resume else []
        
        recs = db.query(RecommendationRepository.model).filter(
            RecommendationRepository.model.user_id == user_id
        ).order_backrel = None
        # Let's get the recommendations manually or using queries
        from backend.app.models.recommendation import Recommendation
        from backend.app.models.job import Job
        
        recommendations = db.query(Recommendation).filter(Recommendation.user_id == user_id).all()
        job_matches = []
        for rec in recommendations[:3]:
            job = db.query(Job).filter(Job.id == rec.job_id).first()
            if job:
                job_matches.append(job.title)

        # Context Strings
        skills_str = ", ".join(skills) if skills else "No skills uploaded yet"
        jobs_str = ", ".join(job_matches) if job_matches else "No job matches yet"

        # Match intents
        message_lower = message.lower()
        reply = ""
        
        if "hello" in message_lower or "hi" in message_lower or "hey" in message_lower:
            reply = (
                f"Hello! I am your AI Career Coach. I've analyzed your profile. "
                f"You currently have skills in **{skills_str}** and matching roles in **{jobs_str}**. "
                f"How can I help you accelerate your career path today? Ask me about 'interview prep', 'resume improvement', 'skills gap', or 'salary predictions'!"
            )
        elif "resume" in message_lower or "cv" in message_lower or "optimize" in message_lower:
            reply = (
                "Your resume is the key to unlocking interviews. Here are the core actions to take:\n\n"
                "1. **Strengthen bullet points**: Always start with an active verb (e.g. *Engineered*, *Spearheaded*, *Orchestrated*) rather than *Worked on*.\n"
                "2. **Quantify results**: E.g., 'Optimized query latency by 40% saving $12k annually.'\n"
                "3. **Align sections**: Group into Summary, Technical Skills, Professional Experience, Projects, and Education.\n\n"
                "Would you like me to scan your resume for weak bullet points?"
            )
        elif "skills" in message_lower or "gap" in message_lower or "missing" in message_lower or "learn" in message_lower:
            reply = (
                f"Based on your profile, your active skills are **{skills_str}**.\n\n"
                "To increase your match probability for high-paying roles, I recommend acquiring:\n"
                "• **Docker & Kubernetes**: Critical for containerized microservices scaling.\n"
                "• **Cloud Providers (AWS/GCP)**: High demand for infrastructure automation.\n"
                "• **System Design**: Essential for backend roles to scale databases and APIs.\n\n"
                "I can generate a personalized 4-week learning roadmap for any of these skills. What target role are you aiming for?"
            )
        elif "interview" in message_lower or "prep" in message_lower or "questions" in message_lower or "practice" in message_lower:
            reply = (
                "Mock interview prep is highly correlated with success! Here are 3 key categories of questions you should practice:\n\n"
                "• **Behavioral (STAR Method)**: Describe a time you resolved a technical disagreement in a team.\n"
                "• **System Design**: Design an rate limiter or design a URL shortener.\n"
                "• **Coding & Algorithms**: Practice hash table operations and graph traversals.\n\n"
                "You can start a Mock Interview Session in the 'Interview Prep' tab. Would you like me to quiz you on a Python or System Design question right here?"
            )
        elif "salary" in message_lower or "pay" in message_lower or "negotiate" in message_lower:
            reply = (
                "Salary depends heavily on experience, target tech stack, and location.\n\n"
                "• For backend engineers with Python/FastAPI/Docker skills, average salaries range from **$110,000 to $145,000** in the US.\n"
                "• Learning Kubernetes or AWS DevOps tools adds an estimated **$15,000 - $25,000** premium to your profile.\n"
                "• Always negotiate using counter-offers and data points about your specialized skills.\n\n"
                "Check out the 'Salary Insights' tab for a targeted estimate based on your specific skills!"
            )
        elif "project" in message_lower or "portfolio" in message_lower or "github" in message_lower:
            reply = (
                "Building high-impact portfolio projects is the best way to prove engineering capability.\n\n"
                "• **For Backend Developer**: Build an API Gateway with rate limiting, logging, and JWT auth.\n"
                "• **For DevOps**: Create a multi-service GitOps repository with Terraform, Helm, and GitHub Actions.\n"
                "• **For Machine Learning**: Deploy an end-to-end model pipeline with FastAPI, Docker, and MLflow.\n\n"
                "Ensure your README is exhaustive and contains architecture diagrams and deployment links!"
            )
        else:
            # Fallback smart conversational responder
            reply = (
                f"That's an excellent question. As your career coach, I suggest exploring how that fits into your target roadmap. "
                f"With your skills in **{skills_str}**, focusing on building projects and optimizing your resume for matching roles like **{jobs_str}** will maximize your return on investment. "
                f"What specific topic or tech stack would you like to discuss next?"
            )

        # Update Session History
        new_history = list(session.history) if session.history else []
        new_history.append({"role": "user", "content": message})
        new_history.append({"role": "assistant", "content": reply})
        
        # SQLAlchemy requires re-assigning JSON field to trigger mutation detection
        session.history = new_history
        db.add(session)
        db.commit()
        db.refresh(session)

        # Format history for schema response
        formatted_history = []
        for msg in session.history:
            formatted_history.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        return {
            "session_id": session.session_id,
            "reply": reply,
            "history": formatted_history
        }
