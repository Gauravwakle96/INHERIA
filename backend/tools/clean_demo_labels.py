"""Rename only the UI test's own demo transition labels; preserve evidence text."""

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Project, Transition


def main():
    count = 0
    with SessionLocal() as db:
        project_ids = list(db.scalars(select(Project.id).where(Project.is_demo.is_(True))))
        records = db.scalars(
            select(Transition).where(
                Transition.project_id.in_(project_ids),
                Transition.title.startswith("Synthetic UI transfer validation"),
            )
        )
        for record in records:
            record.title = record.title.replace(
                "Synthetic UI transfer validation", "Demo UI transfer validation", 1
            )
            count += 1
        db.commit()
    print(f"Demo transition labels updated: {count}")


if __name__ == "__main__":
    main()
