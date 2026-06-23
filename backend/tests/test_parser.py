from backend.app.ai.parser import ResumeParser
from backend.app.ai.skill_extractor import SkillExtractor

def test_resume_regex_parsing():
    """
    Verifies that regex parses correct contact details and sections from resume text.
    """
    sample_resume = """
    Jane Doe
    jane.doe@email.com | (123) 456-7890
    
    Education
    Bachelor of Science in Computer Science
    University of California, Berkeley - 2022
    
    Experience
    Software Engineer Intern at Google
    Worked on backend APIs using Python, FastAPI and Docker. Created deployments.
    
    Skills
    Python, FastAPI, Docker, Kubernetes, Git, PostgreSQL
    """
    
    name = ResumeParser.extract_name(sample_resume)
    email = ResumeParser.extract_email(sample_resume)
    phone = ResumeParser.extract_phone(sample_resume)
    education = ResumeParser.extract_section(sample_resume, ["education"])
    experience = ResumeParser.extract_section(sample_resume, ["experience"])
    
    assert name == "Jane Doe"
    assert email == "jane.doe@email.com"
    assert phone is not None
    assert "Berkeley" in education
    assert "Google" in experience

def test_skill_extractor():
    """
    Verifies that the SkillExtractor detects defined technical competencies.
    """
    sample_text = "Proficient in Python, FastAPI, docker compose, git, and golang. Exploring PostgreSQL."
    skills = SkillExtractor.extract_skills(sample_text)
    
    assert "Python" in skills
    assert "FastAPI" in skills
    assert "Docker Compose" in skills
    assert "Git" in skills
    # golang normalizes to Go or Go is matched case-sensitively, check either:
    assert any(s in skills for s in ["Go", "Golang"])
    assert "PostgreSQL" in skills
