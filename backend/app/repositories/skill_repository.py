from sqlalchemy.orm import Session
from backend.app.models.skill import Skill

class SkillRepository:
    @staticmethod
    def get_by_id(db: Session, skill_id: int) -> Skill | None:
        return db.query(Skill).filter(Skill.id == skill_id).first()

    @staticmethod
    def get_by_name(db: Session, name: str) -> Skill | None:
        # Case insensitive match
        return db.query(Skill).filter(Skill.skill_name.ilike(name)).first()

    @staticmethod
    def get_all(db: Session) -> list[Skill]:
        return db.query(Skill).order_by(Skill.skill_name.asc()).all()

    @staticmethod
    def get_or_create(db: Session, skill_name: str) -> Skill:
        # Normalize name (clean whitespace)
        name_clean = skill_name.strip()
        db_skill = SkillRepository.get_by_name(db, name_clean)
        if not db_skill:
            db_skill = Skill(skill_name=name_clean)
            db.add(db_skill)
            db.commit()
            db.refresh(db_skill)
        return db_skill

    @staticmethod
    def get_or_create_multiple(db: Session, skill_names: list[str]) -> list[Skill]:
        skills_map = {}
        for name in skill_names:
            skill = SkillRepository.get_or_create(db, name)
            skills_map[skill.id] = skill
        return list(skills_map.values())
