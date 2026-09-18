"""
Тесты на API кулинарной книги (по мотивам
https://fastapi.tiangolo.com/tutorial/testing/).

Реальная (файловая) БД приложения не используется: зависимость get_session
подменена на сессию к отдельной in-memory SQLite, которая создаётся заново
для каждого теста (fixture prepare_database).
"""

import asyncio
import sys
from pathlib import Path
from typing import AsyncIterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import main  # noqa: E402
from database import Base, get_session  # noqa: E402

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionFactory = async_sessionmaker(
    test_engine, expire_on_commit=False, class_=AsyncSession
)


async def _override_get_session() -> AsyncIterator[AsyncSession]:
    async with TestSessionFactory() as session:
        yield session


main.app.dependency_overrides[get_session] = _override_get_session

# Без `with` -- чтобы не срабатывали startup/shutdown события приложения
# (они трогают файловую БД cookbook.db, а не тестовую in-memory).
client = TestClient(main.app)


async def _create_tables() -> None:
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def _drop_tables() -> None:
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


@pytest.fixture(autouse=True)
def prepare_database():
    asyncio.run(_create_tables())
    yield
    asyncio.run(_drop_tables())


def _create_sample_recipe(
    title: str = "Тестовый рецепт", cooking_time_minutes: int = 10
) -> dict:
    response = client.post(
        "/recipes",
        json={
            "title": title,
            "cooking_time_minutes": cooking_time_minutes,
            "description": "Описание тестового рецепта.",
            "ingredients": ["ингредиент 1", "ингредиент 2"],
        },
    )
    assert response.status_code == 201
    return response.json()


def test_list_recipes_is_empty_initially():
    response = client.get("/recipes")
    assert response.status_code == 200
    assert response.json() == []


def test_create_recipe_returns_full_detail():
    recipe = _create_sample_recipe()

    assert recipe["title"] == "Тестовый рецепт"
    assert recipe["cooking_time_minutes"] == 10
    assert recipe["views_count"] == 0
    assert recipe["description"] == "Описание тестового рецепта."
    assert [ingredient["name"] for ingredient in recipe["ingredients"]] == [
        "ингредиент 1",
        "ингредиент 2",
    ]


def test_get_recipe_by_id_increments_views_count():
    recipe = _create_sample_recipe()
    recipe_id = recipe["id"]

    first_response = client.get(f"/recipes/{recipe_id}")
    assert first_response.status_code == 200
    assert first_response.json()["views_count"] == 1

    second_response = client.get(f"/recipes/{recipe_id}")
    assert second_response.status_code == 200
    assert second_response.json()["views_count"] == 2


def test_get_unknown_recipe_returns_404():
    response = client.get("/recipes/424242")
    assert response.status_code == 404


def test_list_recipes_sorted_by_views_then_by_cooking_time():
    slow_favorite = _create_sample_recipe(
        "Любимый долгий рецепт", cooking_time_minutes=90
    )
    fast_favorite = _create_sample_recipe(
        "Любимый быстрый рецепт", cooking_time_minutes=15
    )
    _create_sample_recipe("Непопулярный рецепт", cooking_time_minutes=5)

    # Оба "любимых" рецепта получают по 2 просмотра (равные views_count),
    # непопулярный -- ни одного.
    client.get(f'/recipes/{slow_favorite["id"]}')
    client.get(f'/recipes/{slow_favorite["id"]}')
    client.get(f'/recipes/{fast_favorite["id"]}')
    client.get(f'/recipes/{fast_favorite["id"]}')

    response = client.get("/recipes")
    assert response.status_code == 200
    titles_in_order = [item["title"] for item in response.json()]

    # При равном числе просмотров быстрый рецепт должен идти раньше
    # медленного, а непопулярный (0 просмотров) -- последним.
    assert titles_in_order == [
        "Любимый быстрый рецепт",
        "Любимый долгий рецепт",
        "Непопулярный рецепт",
    ]
