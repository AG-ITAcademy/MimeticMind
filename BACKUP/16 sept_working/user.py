# user.py

from dataclasses import dataclass
from sqlalchemy.orm import Session
from user_model import UserModel

@dataclass
class User:
    session: Session
    google_id: str
    email: str
    full_name: Optional[str] = None
    profile_picture: Optional[str] = None
    profile_id: Optional[int] = None

    def save_to_db(self):
        user_record = UserModel(
            google_id=self.google_id,
            email=self.email,
            full_name=self.full_name,
            profile_picture=self.profile_picture,
            profile_id=self.profile_id
        )
        self.session.add(user_record)
        self.session.commit()
        return user_record.id

    @classmethod
    def get_by_google_id(cls, session: Session, google_id: str):
        user_record = session.query(UserModel).filter_by(google_id=google_id).first()
        if user_record:
            return cls.from_model(session, user_record)
        return None

    @classmethod
    def from_model(cls, session: Session, model: UserModel):
        return cls(
            session=session,
            google_id=model.google_id,
            email=model.email,
            full_name=model.full_name,
            profile_picture=model.profile_picture,
            profile_id=model.profile_id
        )
    