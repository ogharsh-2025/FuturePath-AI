from backend.app.ai.embeddings import EmbeddingEngine

class RecommenderEngine:
    @staticmethod
    def recommend_jobs(resume_embedding: list[float], jobs: list, top_n: int = 10) -> list[dict]:
        """
        Compares the resume embedding against a list of jobs using cosine similarity.
        Returns a sorted list of dictionaries with job records and match scores.
        """
        recommendations = []
        for job in jobs:
            if not job.embedding:
                continue
            
            score = EmbeddingEngine.calculate_similarity(resume_embedding, job.embedding)
            recommendations.append({
                "job_id": job.id,
                "job": job,
                "match_score": score
            })
            
        # Sort by match_score in descending order
        recommendations.sort(key=lambda x: x["match_score"], reverse=True)
        return recommendations[:top_n]

    @staticmethod
    def analyze_skill_gap(resume_skills: list[str], job_skills: list[str]) -> list[str]:
        """
        Returns skills that are present in the job post but missing from the resume.
        """
        resume_set = {s.lower().strip() for s in resume_skills}
        missing = []
        for skill in job_skills:
            if skill.lower().strip() not in resume_set:
                missing.append(skill)
        return sorted(missing)
