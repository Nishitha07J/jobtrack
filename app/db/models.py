from datetime import datetime

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Index, String, Text,
    UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    google_sub: Mapped[str] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    token: Mapped["OAuthToken"] = relationship(back_populates="user", uselist=False)


class OAuthToken(Base):
    __tablename__ = "oauth_tokens"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    access_token_enc: Mapped[str] = mapped_column(Text)
    refresh_token_enc: Mapped[str] = mapped_column(Text)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="token")


class Email(Base):
    __tablename__ = "emails"
    __table_args__ = (
        UniqueConstraint("user_id", "gmail_message_id", name="uq_user_gmail_msg"),
        Index("ix_emails_user_received", "user_id", "received_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    gmail_message_id: Mapped[str] = mapped_column(String(64))
    thread_id: Mapped[str] = mapped_column(String(64))
    sender: Mapped[str] = mapped_column(String(320))
    subject: Mapped[str] = mapped_column(Text)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    snippet: Mapped[str] = mapped_column(Text, default="")
    classified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint("user_id", "company_norm", "role_norm", name="uq_user_company_role"),
        Index("ix_applications_user_status", "user_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    company: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(255))
    company_norm: Mapped[str] = mapped_column(String(255))
    role_norm: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default="applied")
    applied_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_event_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    events: Mapped[list["ApplicationEvent"]] = relationship(back_populates="application")


class ApplicationEvent(Base):
    __tablename__ = "application_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE")
    )
    email_id: Mapped[int | None] = mapped_column(
        ForeignKey("emails.id", ondelete="SET NULL"), nullable=True
    )
    event_type: Mapped[str] = mapped_column(String(32))
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    source: Mapped[str] = mapped_column(String(16))  # rule | llm | manual
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    application: Mapped["Application"] = relationship(back_populates="events")