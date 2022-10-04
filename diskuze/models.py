from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Discussion(Base):
    __tablename__ = "discussion"

    id = Column(Integer, nullable=False, primary_key=True)
    canonical = Column(String(256), nullable=False, unique=True)
    comments = relationship("Comment", back_populates="discussion")


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, nullable=False, primary_key=True)
    name = Column(String(64), nullable=False, unique=True)
    comments = relationship("Comment", back_populates="user")


class Comment(Base):
    __tablename__ = "comment"

    id = Column(Integer, nullable=False, primary_key=True)
    content = Column(String(2048), nullable=False)
    discussion_id = Column(Integer, ForeignKey(Discussion.id), nullable=False)
    discussion = relationship(Discussion, back_populates="comments")
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    user = relationship(User, back_populates="comments")
