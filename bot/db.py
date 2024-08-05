from functools import lru_cache
from typing import List, Optional

from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    sessionmaker,
)


class Base(DeclarativeBase):
    pass


class Admin(Base):
    __tablename__ = "admin"

    tg_id: Mapped[int] = mapped_column(primary_key=True)
    tg_tag: Mapped[Optional[str]]
    can_add_info: Mapped[bool] = mapped_column(default=True)
    can_add_new_admins: Mapped[bool] = mapped_column(default=True)

    added_by_id: Mapped[int] = mapped_column(ForeignKey("admin.tg_id"))
    added_by: Mapped["Admin"] = relationship(foreign_keys=[added_by_id])

    banned_users: Mapped[List["BannedUserOrChat"]] = relationship(
        back_populates="banned_by", cascade="all, delete-orphan"
    )


class BannedUserOrChat(Base):
    __tablename__ = "banned"

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id = Column(
        BigInteger, index=True, unique=True, nullable=False
    )  # can be negative
    is_user: Mapped[bool]

    banned_by_id: Mapped[int] = mapped_column(ForeignKey("admin.tg_id"))
    banned_by: Mapped["Admin"] = relationship(back_populates="banned_users")


@lru_cache(maxsize=1)
def get_db_sessionmaker(conn_string: str) -> sessionmaker:
    engine = create_async_engine(conn_string)
    return sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
