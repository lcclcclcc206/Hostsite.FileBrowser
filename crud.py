from sqlalchemy.orm import Session
import models
import schemas

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()
