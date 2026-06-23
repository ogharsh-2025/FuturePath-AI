import re

# Comprehensive list of standard tech skills
TECHNICAL_SKILLS = [
    # Programming Languages
    "python", "javascript", "typescript", "java", "c++", "c#", "ruby", "php", "golang", "rust", "swift", "kotlin", "scala", "html", "css", "sql", "bash", "shell",
    # Backend Frameworks
    "fastapi", "django", "flask", "spring boot", "spring", "express", "nestjs", "laravel", "ruby on rails",
    # Frontend Frameworks
    "react", "angular", "vue", "next.js", "nextjs", "svelte", "jquery", "bootstrap", "tailwind",
    # Databases & Cache
    "postgresql", "postgres", "mysql", "mongodb", "sqlite", "redis", "elasticsearch", "cassandra", "dynamodb", "mariadb",
    # Cloud & DevOps
    "docker", "kubernetes", "k8s", "aws", "azure", "gcp", "terraform", "jenkins", "github actions", "gitlab ci", "ansible",
    # AI/ML & Data Science
    "pytorch", "tensorflow", "keras", "scikit-learn", "numpy", "pandas", "sentence-transformers", "nlp", "machine learning", "deep learning",
    # API & Protocols
    "rest api", "graphql", "grpc", "websockets", "microservices", "rabbitmq", "kafka",
    # Tools & Concepts
    "git", "ci/cd", "agile", "scrum", "linux", "unix", "docker compose"
]

# Case-sensitive checks for short ambiguous words
CASE_SENSITIVE_SKILLS = {
    "Go": "golang",
    "R": "r"
}

class SkillExtractor:
    @staticmethod
    def extract_skills(text: str) -> list[str]:
        """
        Scans input text for skills in the predefined technical skills list.
        Uses regex word boundaries to avoid partial matches.
        """
        if not text:
            return []
            
        extracted = set()
        text_lower = text.lower()
        
        # 1. Match case-insensitive skills
        for skill in TECHNICAL_SKILLS:
            # Escape skill for safe regex usage
            pattern = rf'\b{re.escape(skill)}\b'
            # Replace common naming variations e.g. next.js vs nextjs
            if skill == "nextjs":
                pattern = r'\bnext\.?js\b'
            elif skill == "postgres":
                pattern = r'\bpostgres(?:ql)?\b'
            elif skill == "k8s":
                pattern = r'\bk8s\b|\bkubernetes\b'
            
            if re.search(pattern, text_lower):
                # Normalize names
                if skill == "postgres":
                    extracted.add("PostgreSQL")
                elif skill == "k8s":
                    extracted.add("Kubernetes")
                elif skill == "nextjs":
                    extracted.add("Next.js")
                elif skill == "fastapi":
                    extracted.add("FastAPI")
                elif skill == "typescript":
                    extracted.add("TypeScript")
                elif skill == "javascript":
                    extracted.add("JavaScript")
                elif skill == "mongodb":
                    extracted.add("MongoDB")
                elif skill == "mysql":
                    extracted.add("MySQL")
                elif skill == "pytorch":
                    extracted.add("PyTorch")
                elif skill == "tensorflow":
                    extracted.add("TensorFlow")
                elif skill == "github actions":
                    extracted.add("GitHub Actions")
                elif skill == "gitlab ci":
                    extracted.add("GitLab CI")
                elif skill == "docker compose":
                    extracted.add("Docker Compose")
                elif skill == "git":
                    extracted.add("Git")
                elif skill == "rest api":
                    extracted.add("REST API")
                elif skill == "graphql":
                    extracted.add("GraphQL")
                elif skill == "grpc":
                    extracted.add("gRPC")
                elif skill == "ci/cd":
                    extracted.add("CI/CD")
                else:
                    # Title case standard skills
                    extracted.add(skill.title() if len(skill) > 3 else skill.upper())

        # 2. Match case-sensitive skills (like Go, R)
        for skill_key, skill_val in CASE_SENSITIVE_SKILLS.items():
            pattern = rf'\b{re.escape(skill_key)}\b'
            if re.search(pattern, text): # Search raw text without lowering
                extracted.add(skill_key)

        return sorted(list(extracted))
