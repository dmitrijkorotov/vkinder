import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


def create_tables(engine):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


class User(Base):
    __tablename__ = "user"

    user_id = sq.Column(sq.Integer, primary_key=True)

    vk_id = sq.Column(sq.String(length=9), nullable=False, unique=True)
    gender = sq.Column(sq.Integer, nullable=False)
    age = sq.Column(sq.Integer, nullable=False)
    city_id = sq.Column(sq.Integer, nullable=False)


class BlackList(Base):
    __tablename__ = "black_list"

    black_list_id = sq.Column(sq.Integer, primary_key=True)
    user_id = sq.Column(sq.Integer, sq.ForeignKey("user.user_id"),
                        nullable=False)

    block_vk_id = sq.Column(sq.String(length=9), nullable=False)

    user = relationship(User, backref="black_list_users")


class Favorite(Base):
    __tablename__ = "favorite"

    favorite_id = sq.Column(sq.Integer, primary_key=True)
    user_id = sq.Column(sq.Integer, sq.ForeignKey("user.user_id"),
                        nullable=False)

    first_name = sq.Column(sq.String(length=50), nullable=False)
    last_name = sq.Column(sq.String(length=50), nullable=False)
    url_profile = sq.Column(sq.String(length=128), nullable=False)
    favorite_vk_id = sq.Column(sq.String(length=9), nullable=False)

    user = relationship(User, backref="favorite_users")
