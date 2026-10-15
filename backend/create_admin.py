"""Create or promote an ADMIN user:  python create_admin.py <username> <password>"""
import sys

from app.database import SessionLocal
from app.models import User
from app.security import hash_password


def main():
    if len(sys.argv) != 3:
        sys.exit("Usage: python create_admin.py <username> <password>")
    username, password = sys.argv[1], sys.argv[2]
    if len(password) < 8:
        sys.exit("Password must be at least 8 characters")
    with SessionLocal() as db:
        user = db.query(User).filter(User.username == username).first()
        if user:
            user.role = "ADMIN"
            user.password = hash_password(password)
            action = "promoted/updated"
        else:
            db.add(User(username=username, password=hash_password(password), role="ADMIN"))
            action = "created"
        db.commit()
    print(f"Admin '{username}' {action}.")


if __name__ == "__main__":
    main()
