"""
ORM-модели кулинарной книги.

Recipe (рецепт) -- один-ко-многим -- Ingredient (ингредиент). Ингредиенты
вынесены в отдельную таблицу (а не хранятся строкой через запятую), чтобы
у каждого ингредиента было собственное имя как отдельная сущность --
это соответствует тому, как мы моделировали связи в предыдущих модулях.
"""

from typing import List

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    cooking_time_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # Растёт на 1 каждый раз, когда открывают детальную страницу рецепта --
    # именно по этому полю сортируется список рецептов (задание).
    views_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    ingredients: Mapped[List["Ingredient"]] = relationship(
        back_populates="recipe",
        cascade="all, delete-orphan",
        order_by="Ingredient.id",
    )


class Ingredient(Base):
    __tablename__ = "ingredients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"),
        nullable=False,
    )

    recipe: Mapped["Recipe"] = relationship(back_populates="ingredients")
