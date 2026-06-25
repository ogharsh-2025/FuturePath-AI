# Import all the models so that Base has them before being
# imported by Alembic or database creation scripts.
from backend.app.database.session import Base  # noqa
from backend.app.models.user import User  # noqa
from backend.app.models.skill import Skill, resume_skills, job_skills  # noqa
from backend.app.models.resume import Resume  # noqa
from backend.app.models.job import Job  # noqa
from backend.app.models.recommendation import Recommendation  # noqa
from backend.app.models.extended_models import (  # noqa
    LearningPath,
    CareerPrediction,
    GitHubProfile,
    PortfolioScore,
    SalaryPrediction,
    Notification,
    ChatSession,
    InterviewAttempt,
    ResumeScore,
    JobAlert
)

