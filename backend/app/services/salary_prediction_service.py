from sqlalchemy.orm import Session
from backend.app.models.extended_models import SalaryPrediction
import re

class SalaryPredictionService:
    @classmethod
    def predict_salary(cls, db: Session, user_id: int, skills: list[str], experience: int, location: str) -> dict:
        """
        Predicts salary range using experience, location, and skills with robust heuristics.
        Saves predictions to the database.
        """
        # Base Salary based on years of experience
        # 0 yrs -> $65,000. Each year adds $7,500. Caps at $160,000 base.
        base_salary = 65000 + (min(15, experience) * 7500)
        
        # Location Multipliers
        loc_lower = location.lower()
        location_multiplier = 1.0
        if any(w in loc_lower for w in ["san francisco", "sf", "new york", "ny", "seattle", "remote", "us", "usa"]):
            location_multiplier = 1.35
        elif any(w in loc_lower for w in ["london", "uk", "germany", "europe", "canada"]):
            location_multiplier = 1.05
        elif any(w in loc_lower for w in ["india", "bangalore", "asia"]):
            location_multiplier = 0.55
        elif any(w in loc_lower for w in ["singapore", "australia", "sydney"]):
            location_multiplier = 0.95

        # Skill Premiums
        skill_premium = 0.0
        skills_lower = [s.lower() for s in skills]
        
        devops_kws = ["docker", "kubernetes", "k8s", "aws", "gcp", "azure", "devops", "terraform", "ansible", "ci/cd"]
        ai_kws = ["machine learning", "ml", "deep learning", "pytorch", "tensorflow", "nlp", "computer vision", "transformers"]
        backend_kws = ["fastapi", "django", "flask", "postgresql", "redis", "mongodb", "graphql", "microservices", "go", "rust"]
        frontend_kws = ["react", "next.js", "vue", "typescript", "tailwind", "angular"]

        for s in skills_lower:
            if s in devops_kws:
                skill_premium += 0.04
            elif s in ai_kws:
                skill_premium += 0.05
            elif s in backend_kws:
                skill_premium += 0.03
            elif s in frontend_kws:
                skill_premium += 0.02

        # Cap skill premium at 30%
        skill_premium = min(0.30, skill_premium)
        
        # Calculate Average Salary
        avg_salary = int(base_salary * location_multiplier * (1.0 + skill_premium))
        
        # Add range variance
        min_salary = int(avg_salary * 0.88)
        max_salary = int(avg_salary * 1.15)
        
        # Confidence Score
        confidence = 0.85
        if not skills:
            confidence -= 0.15
        if not location:
            confidence -= 0.10
        if experience > 12 or experience < 1:
            confidence -= 0.05
        confidence = max(0.50, min(0.95, confidence))

        # Save to DB
        pred = SalaryPrediction(
            user_id=user_id,
            skills=", ".join(skills),
            experience=experience,
            location=location,
            min_salary=min_salary,
            avg_salary=avg_salary,
            max_salary=max_salary,
            confidence_score=confidence
        )
        db.add(pred)
        db.commit()
        db.refresh(pred)

        return {
            "min_salary": min_salary,
            "avg_salary": avg_salary,
            "max_salary": max_salary,
            "confidence_score": confidence
        }

    @classmethod
    def get_skill_trends(cls) -> dict:
        """
        Returns statistical trend indicators for tech skills.
        Used to feed ChartJS trends components.
        """
        return {
            "demanded_skills": [
                {"name": "Python", "percentage": 88, "salary_avg": 135000},
                {"name": "React", "percentage": 82, "salary_avg": 115000},
                {"name": "Docker", "percentage": 78, "salary_avg": 128000},
                {"name": "FastAPI", "percentage": 70, "salary_avg": 120000},
                {"name": "Kubernetes", "percentage": 65, "salary_avg": 145000},
                {"name": "PostgreSQL", "percentage": 74, "salary_avg": 118000},
                {"name": "AWS", "percentage": 79, "salary_avg": 138000}
            ],
            "growing_skills": [
                {"name": "FastAPI", "growth_rate": 35},
                {"name": "PyTorch", "growth_rate": 28},
                {"name": "TypeScript", "growth_rate": 24},
                {"name": "Next.js", "growth_rate": 22},
                {"name": "Kubernetes", "growth_rate": 18}
            ],
            "highest_paying_skills": [
                {"name": "Kubernetes", "avg_salary": 145000},
                {"name": "PyTorch", "avg_salary": 142000},
                {"name": "AWS", "avg_salary": 138000},
                {"name": "Python", "avg_salary": 135000},
                {"name": "Docker", "avg_salary": 128000}
            ]
        }
