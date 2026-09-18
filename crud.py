"""
Бизнес-логика/доступ к данным, отдельно от FastAPI-роутов (main.py) --
чтобы роуты отвечали только за HTTP, а не за детали работы с БД.
"""

from typing import List, Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import Ingredient, Recipe


async def get_all_recipes(session: AsyncSession) -> Sequence[Recipe]:
    """
    Список всех рецептов, отсортированный по популярности (views_count) по
    убыванию; при равенстве -- по времени готовки по возрастанию.
    """
    query = select(Recipe).order_by(
        Recipe.views_count.desc(),
        Recipe.cooking_time_minutes.asc(),
    )
    result = await session.execute(query)
    return result.scalars().all()


async def get_recipe_by_id(session: AsyncSession, recipe_id: int) -> Optional[Recipe]:
    query = (
        select(Recipe)
        .options(selectinload(Recipe.ingredients))
        .where(Recipe.id == recipe_id)
    )
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def increment_recipe_views(session: AsyncSession, recipe: Recipe) -> None:
    recipe.views_count += 1
    session.add(recipe)
    await session.commit()
    await session.refresh(recipe)


async def create_recipe(
    session: AsyncSession,
    title: str,
    cooking_time_minutes: int,
    description: str,
    ingredient_names: List[str],
) -> Recipe:
    new_recipe = Recipe(
        title=title,
        cooking_time_minutes=cooking_time_minutes,
        description=description,
        ingredients=[Ingredient(name=name) for name in ingredient_names],
    )
    session.add(new_recipe)
    await session.commit()
    await session.refresh(new_recipe, attribute_names=["ingredients"])
    return new_recipe
