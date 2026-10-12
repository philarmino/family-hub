from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Meal(Base):
    __tablename__ = "meals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    photo_path: Mapped[str | None] = mapped_column(String(500))
    source: Mapped[str] = mapped_column(String(20), default="custom")
    chefkoch_url: Mapped[str | None] = mapped_column(String(500))
    chefkoch_id: Mapped[str | None] = mapped_column(String(50))
    base_servings: Mapped[int] = mapped_column(Integer, default=4)
    instructions: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    ingredients: Mapped[list[Ingredient]] = relationship(
        back_populates="meal",
        cascade="all, delete-orphan",
        order_by="Ingredient.sort_order",
    )


class Ingredient(Base):
    __tablename__ = "ingredients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    meal_id: Mapped[int] = mapped_column(ForeignKey("meals.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    amount: Mapped[float | None] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(String(50))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    meal: Mapped[Meal] = relationship(back_populates="ingredients")


class FamilyMember(Base):
    __tablename__ = "family_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="kid")


class WeekPlan(Base):
    __tablename__ = "week_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    week_start: Mapped[date] = mapped_column(Date, unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="suggesting")
    target_servings: Mapped[int] = mapped_column(Integer, default=4)

    days: Mapped[list[WeekPlanDay]] = relationship(
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="WeekPlanDay.weekday",
    )
    suggestions: Mapped[list[Suggestion]] = relationship(
        back_populates="plan",
        cascade="all, delete-orphan",
    )
    wishes: Mapped[list[Wish]] = relationship(
        back_populates="plan",
        cascade="all, delete-orphan",
    )


class WeekPlanDay(Base):
    __tablename__ = "week_plan_days"
    __table_args__ = (UniqueConstraint("plan_id", "weekday"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("week_plans.id", ondelete="CASCADE"))
    weekday: Mapped[int] = mapped_column(Integer)  # 0=Mon .. 6=Sun
    meal_id: Mapped[int | None] = mapped_column(ForeignKey("meals.id", ondelete="SET NULL"))
    servings: Mapped[int] = mapped_column(Integer, default=4)

    plan: Mapped[WeekPlan] = relationship(back_populates="days")
    meal: Mapped[Meal | None] = relationship()


class Suggestion(Base):
    __tablename__ = "suggestions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("week_plans.id", ondelete="CASCADE"))
    member_id: Mapped[int | None] = mapped_column(ForeignKey("family_members.id", ondelete="SET NULL"))
    meal_id: Mapped[int] = mapped_column(ForeignKey("meals.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    plan: Mapped[WeekPlan] = relationship(back_populates="suggestions")
    member: Mapped[FamilyMember | None] = relationship()
    meal: Mapped[Meal] = relationship()


class Wish(Base):
    __tablename__ = "wishes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("week_plans.id", ondelete="CASCADE"))
    member_id: Mapped[int | None] = mapped_column(ForeignKey("family_members.id", ondelete="SET NULL"))
    text: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    plan: Mapped[WeekPlan] = relationship(back_populates="wishes")
    member: Mapped[FamilyMember | None] = relationship()
