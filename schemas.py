"""
Pydantic-схемы кулинарной книги.

Разделены по экранам, которые описаны в задании:
* RecipeListItem -- то, что показывает таблица со списком всех рецептов
  (название, просмотры, время готовки);
* RecipeDetail -- то, что показывает страница одного рецепта (плюс список
  ингредиентов и текстовое описание);
* RecipeCreate -- то, что фронтенд присылает в POST /recipes, чтобы
  создать новый рецепт.
"""

from typing import List

from pydantic import BaseModel, ConfigDict, Field


class IngredientOut(BaseModel):
    """Один ингредиент рецепта, как он возвращается клиенту."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Идентификатор ингредиента.")
    name: str = Field(
        ..., description='Название ингредиента, например "мука" или "яйцо".'
    )


class RecipeListItem(BaseModel):
    """
    Одна строка в таблице со списком всех рецептов.

    Список отсортирован по популярности (views_count) по убыванию; при
    равном количестве просмотров -- по возрастанию времени готовки.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(
        ...,
        description="Идентификатор рецепта -- используется для запроса /recipes/{id}.",
    )
    title: str = Field(..., description="Название рецепта.")
    views_count: int = Field(
        ...,
        description="Сколько раз открывали детальную страницу этого рецепта.",
    )
    cooking_time_minutes: int = Field(..., description="Время готовки в минутах.")


class RecipeDetail(BaseModel):
    """Детальная информация об одном рецепте (экран "детали рецепта")."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Идентификатор рецепта.")
    title: str = Field(..., description="Название рецепта.")
    cooking_time_minutes: int = Field(..., description="Время готовки в минутах.")
    views_count: int = Field(
        ...,
        description=(
            "Сколько раз открывали эту страницу. Каждый успешный запрос "
            "GET /recipes/{id} увеличивает это значение на 1 -- включая "
            "запрос, ответом на который пришло это самое число."
        ),
    )
    ingredients: List[IngredientOut] = Field(
        ...,
        description="Список ингредиентов, необходимых для приготовления.",
    )
    description: str = Field(
        ..., description="Текстовое описание/инструкция приготовления рецепта."
    )


class RecipeCreate(BaseModel):
    """Тело запроса POST /recipes для создания нового рецепта."""

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Название рецепта.",
        examples=["Омлет с сыром"],
    )
    cooking_time_minutes: int = Field(
        ...,
        gt=0,
        description="Время готовки в минутах, должно быть больше нуля.",
        examples=[15],
    )
    description: str = Field(
        default="",
        description="Текстовое описание/инструкция приготовления.",
        examples=["Взбить яйца, добавить тёртый сыр, жарить 5 минут на среднем огне."],
    )
    ingredients: List[str] = Field(
        default_factory=list,
        description=(
            "Список названий ингредиентов (хотя бы один рекомендуется, "
            "но не обязателен)."
        ),
        examples=[["яйца", "сыр", "соль"]],
    )
