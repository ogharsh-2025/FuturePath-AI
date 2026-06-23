from backend.app.ai.embeddings import EmbeddingEngine
from backend.app.ai.recommender import RecommenderEngine

def test_cosine_similarity():
    """
    Test standard math behaviors for the cosine similarity wrapper.
    """
    # Identical vectors -> 100.0%
    vec_a = [1.0, 0.0, 0.0, 1.0]
    vec_b = [1.0, 0.0, 0.0, 1.0]
    similarity = EmbeddingEngine.calculate_similarity(vec_a, vec_b)
    assert similarity == 100.0

    # Orthogonal vectors -> 0.0%
    vec_c = [1.0, 0.0, 0.0]
    vec_d = [0.0, 1.0, 0.0]
    similarity_ortho = EmbeddingEngine.calculate_similarity(vec_c, vec_d)
    assert similarity_ortho == 0.0

    # Empty inputs -> 0.0%
    assert EmbeddingEngine.calculate_similarity([], []) == 0.0

def test_skill_gap_analysis():
    """
    Test set-difference analysis for skills list.
    """
    resume_skills = ["Python", "FastAPI", "Git"]
    job_skills = ["Python", "FastAPI", "Docker", "Kubernetes", "Git"]
    
    missing = RecommenderEngine.analyze_skill_gap(resume_skills, job_skills)
    assert missing == ["Docker", "Kubernetes"]

    # Verify case insensitivity matching works correctly
    resume_skills_lower = ["python", "fastapi"]
    missing_casing = RecommenderEngine.analyze_skill_gap(resume_skills_lower, job_skills)
    assert "Docker" in missing_casing
    assert "Python" not in missing_casing
