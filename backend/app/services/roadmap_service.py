from sqlalchemy.orm import Session
from backend.app.repositories.resume_repository import ResumeRepository
from backend.app.repositories.job_repository import JobRepository
from backend.app.ai.recommender import RecommenderEngine

SKILL_ROADMAP_DATABASE = {
    "FastAPI": {
        "topics": ["FastAPI Routing, Path & Query Parameters", "Pydantic Models & Validation", "Dependency Injection Pattern", "SQLAlchemy ORM Integration", "OAuth2 & JWT Auth flow"],
        "resources": ["FastAPI Official Docs (fastapi.tiangolo.com)", "FastAPI Course on freeCodeCamp", "TestDriven.io FastAPI tutorials"],
        "project": "Build a RESTful Task Management API with user authentication and database persistence."
    },
    "Docker": {
        "topics": ["Docker Core Architecture", "Writing custom Dockerfiles", "Image Layer Optimization", "Docker Volumes & Networks", "Multi-container configurations using Docker Compose"],
        "resources": ["Docker Get Started Guide", "Docker Handbook on freeCodeCamp", "Katacoda Docker Playgrounds"],
        "project": "Containerize a web app with PostgreSQL database backend and run them together via Docker Compose."
    },
    "Kubernetes": {
        "topics": ["K8s Architecture (Control Plane, Worker Nodes)", "Pod & Deployment Manifests", "Services (ClusterIP, NodePort, LoadBalancer)", "ConfigMaps & Secrets", "Ingress Controllers"],
        "resources": ["Kubernetes.io Interactive Tutorials", "KubeAcademy by VMware", "Nana's K8s Bootcamp on YouTube"],
        "project": "Deploy a multi-service web app into a local Minikube cluster with environment configuration and ingress routing."
    },
    "React": {
        "topics": ["JSX syntax & Component Structure", "State & Props management", "React Hooks (useState, useEffect, useContext)", "React Router for Navigation", "State management (Redux Toolkit or Context API)"],
        "resources": ["React.dev documentation & tutorial", "Epic React by Kent C. Dodds", "React Tutorial on freeCodeCamp"],
        "project": "Create a fully responsive Weather & Activity Dashboard fetching live data from public APIs."
    },
    "PostgreSQL": {
        "topics": ["Relational Schema Design & Constraints", "SQL Joins, Aggregations & Subqueries", "Indexes & Performance Tuning", "Transactions & ACID principles", "JSONB and Array data types in Postgres"],
        "resources": ["PostgreSQL Tutorial (postgresqltutorial.com)", "SQLBolt Interactive Lessons", "PG Casts screencasts"],
        "project": "Design a relational schema for a multi-vendor E-commerce platform and optimize query performance using Indexes."
    },
    "Git": {
        "topics": ["Git configuration & local workflow", "Branching, Merging & Merge Conflicts", "Rebasing vs Merging", "Interactive Rebase & Cherry-picking", "Collaboration via Pull Requests on GitHub"],
        "resources": ["Git Immersion tutorial", "Pro Git book (git-scm.com)", "GitHub Learning Lab"],
        "project": "Set up a repository with branch protection rules, collaborate on code branches, and practice merge conflict resolution."
    },
    "AWS": {
        "topics": ["IAM (Identity & Access Management)", "EC2 Virtual Servers & Auto Scaling", "S3 Simple Storage Service", "RDS Relational Database Service", "Serverless architecture with AWS Lambda"],
        "resources": ["AWS Cloud Practitioner learning path", "AWS official documentation", "A Cloud Guru courses"],
        "project": "Deploy a secure serverless API using AWS Lambda, API Gateway, and store file uploads in an S3 Bucket."
    },
    "Python": {
        "topics": ["Python Syntax, Data Structures (Lists, Dicts, Sets)", "Object-Oriented Programming (OOP) in Python", "Generators, Decorators, and Context Managers", "Virtual Environments (venv/pip)", "Asynchronous programming (async/await)"],
        "resources": ["Python.org Tutorial", "Real Python (realpython.com)", "Automate the Boring Stuff with Python"],
        "project": "Create an object-oriented CLI web scraper that parses data from multiple pages and outputs formatted JSON files."
    },
    "Terraform": {
        "topics": ["Infrastructure as Code (IaC) principles", "Terraform Providers & Resources", "Variables, Outputs & Locals", "State Management & Backends", "Terraform Modules creation"],
        "resources": ["HashiCorp Learn Terraform path", "Terraform Up & Running book"],
        "project": "Provision an AWS VPC containing an EC2 instance and an RDS database completely using Terraform code."
    },
    "Redis": {
        "topics": ["Redis Data Types (Strings, Hashes, Lists, Sets)", "Cache Invalidation & TTL (Time To Live)", "Redis as a Message Broker (Pub/Sub)", "Redis Persistence (RDB/AOF)"],
        "resources": ["Redis University (university.redis.com)", "Redis Crash Course"],
        "project": "Implement a caching layer in a web app to store slow API queries with automatic cache invalidation."
    }
}

class RoadmapService:
    @staticmethod
    def generate_roadmap(db: Session, user_id: int, job_id: int) -> dict:
        """
        Generates a structured career roadmap based on missing skills for a job.
        """
        # Fetch resume
        resume = ResumeRepository.get_by_user_id(db, user_id)
        if not resume:
            raise ValueError("No resume uploaded yet. Please upload a resume first.")

        # Fetch job
        job = JobRepository.get_by_id(db, job_id)
        if not job:
            raise ValueError("Job not found.")

        # Skills analysis
        resume_skills = [s.skill_name for s in resume.skills]
        job_skills = [s.skill_name for s in job.skills]
        missing_skills = RecommenderEngine.analyze_skill_gap(resume_skills, job_skills)

        learning_path = []
        for skill in missing_skills:
            # Check if skill details are defined in database, else use generic template
            skill_info = SKILL_ROADMAP_DATABASE.get(skill)
            if skill_info:
                learning_path.append({
                    "skill": skill,
                    "topics": skill_info["topics"],
                    "resources": skill_info["resources"],
                    "project": skill_info["project"]
                })
            else:
                learning_path.append({
                    "skill": skill,
                    "topics": [
                        f"Learn {skill} fundamentals and core syntax",
                        f"Understand {skill} best practices and design patterns",
                        f"Explore advanced capabilities of {skill}"
                    ],
                    "resources": [
                        f"Official {skill} Documentation",
                        f"Online developer tutorials and community guides for {skill}"
                    ],
                    "project": f"Build a prototype application integrating {skill} to solve a real-world task."
                })

        return {
            "job_title": job.title,
            "company": job.company,
            "current_skills": resume_skills,
            "missing_skills": missing_skills,
            "learning_path": learning_path
        }
