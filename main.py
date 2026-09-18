"""
API кулинарной книги.

* GET  /recipes           -- таблица со списком всех рецептов
                              (название, просмотры, время готовки),
                              отсортированная по популярности.
* GET  /recipes/{id}       -- детальная страница рецепта (название, время
                              готовки, ингредиенты, описание). Каждый
                              успешный вызов увеличивает счётчик просмотров.
* POST /recipes           -- создать новый рецепт.

Собрано на FastAPI + асинхронной SQLAlchemy (SQLAlchemy 2.0, aiosqlite).
Полная интерактивная документация доступна на /docs (Swagger UI) и /redoc.
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator, List

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

import crud
from database import get_session, init_models
from schemas import RecipeCreate, RecipeDetail, RecipeListItem


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await init_models()
    yield


app = FastAPI(
    title="Cookbook API",
    description=(
        "Бэкенд кулинарной книги: список рецептов, отсортированный по "
        "популярности, детальная страница с ингредиентами и создание "
        "новых рецептов."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


@app.get(
    "/recipes",
    response_model=List[RecipeListItem],
    summary="Список всех рецептов",
    description=(
        "Возвращает все рецепты для главного экрана: название, количество "
        "просмотров и время готовки. Отсортированы по количеству просмотров "
        "(популярности) по убыванию; при равном числе просмотров -- по "
        "времени готовки по возрастанию."
    ),
)
async def list_recipes(
    session: AsyncSession = Depends(get_session),
) -> List[RecipeListItem]:
    recipes = await crud.get_all_recipes(session)
    return [RecipeListItem.model_validate(recipe) for recipe in recipes]


@app.get(
    "/recipes/{recipe_id}",
    response_model=RecipeDetail,
    summary="Детальная информация о рецепте",
    description=(
        "Возвращает название, время готовки, список ингредиентов и текстовое "
        "описание рецепта. Каждый успешный вызов увеличивает счётчик "
        "просмотров этого рецепта на 1 -- он же используется для сортировки "
        "на экране со списком рецептов."
    ),
    responses={404: {"description": "Рецепт с таким id не найден."}},
)
async def get_recipe(
    recipe_id: int, session: AsyncSession = Depends(get_session)
) -> RecipeDetail:
    recipe = await crud.get_recipe_by_id(session, recipe_id)
    if recipe is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found"
        )

    await crud.increment_recipe_views(session, recipe)
    return RecipeDetail.model_validate(recipe)


@app.post(
    "/recipes",
    response_model=RecipeDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новый рецепт",
    description=(
        "Создаёт новый рецепт со списком ингредиентов. "
        "Счётчик просмотров у нового рецепта равен 0."
    ),
)
async def create_recipe(
    payload: RecipeCreate,
    session: AsyncSession = Depends(get_session),
) -> RecipeDetail:
    recipe = await crud.create_recipe(
        session,
        title=payload.title,
        cooking_time_minutes=payload.cooking_time_minutes,
        description=payload.description,
        ingredient_names=payload.ingredients,
    )
    return RecipeDetail.model_validate(recipe)
