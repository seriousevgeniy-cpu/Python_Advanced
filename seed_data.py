"""Наполняет БД несколькими рецептами для ручной проверки API."""

import asyncio
from typing import Any, Dict, List

from database import async_session_factory, init_models
from models import Ingredient, Recipe

RECIPES: List[Dict[str, Any]] = [
    {
        "title": "Омлет с сыром",
        "cooking_time_minutes": 15,
        "description": (
            "Взбить яйца, добавить тёртый сыр, жарить 5 минут на среднем огне."
        ),
        "ingredients": ["яйца", "сыр", "соль", "масло"],
        "views_count": 5,
    },
    {
        "title": "Борщ",
        "cooking_time_minutes": 90,
        "description": (
            "Сварить бульон, добавить свёклу, капусту и другие овощи, "
            "варить до готовности."
        ),
        "ingredients": ["свёкла", "капуста", "картофель", "мясо", "морковь", "лук"],
        "views_count": 12,
    },
    {
        "title": "Салат Цезарь",
        "cooking_time_minutes": 20,
        "description": (
            "Смешать листья салата, курицу, гренки и соус, посыпать пармезаном."
        ),
        "ingredients": ["салат", "курица", "гренки", "соус цезарь", "пармезан"],
        "views_count": 12,
    },
    {
        "title": "Овсянка на воде",
        "cooking_time_minutes": 10,
        "description": "Залить овсяные хлопья кипятком, дать настояться 5 минут.",
        "ingredients": ["овсяные хлопья", "вода", "соль"],
        "views_count": 1,
    },
]


async def seed() -> None:
    await init_models()
    async with async_session_factory() as session:
        existing = await session.execute(Recipe.__table__.select())
        if existing.first() is not None:
            print("База уже наполнена, ничего не делаю.")
            return

        for recipe_data in RECIPES:
            recipe = Recipe(
                title=recipe_data["title"],
                cooking_time_minutes=recipe_data["cooking_time_minutes"],
                description=recipe_data["description"],
                views_count=recipe_data["views_count"],
                ingredients=[
                    Ingredient(name=name) for name in recipe_data["ingredients"]
                ],
            )
            session.add(recipe)
        await session.commit()
    print(f"Добавлено {len(RECIPES)} рецептов.")


if __name__ == "__main__":
    asyncio.run(seed())
