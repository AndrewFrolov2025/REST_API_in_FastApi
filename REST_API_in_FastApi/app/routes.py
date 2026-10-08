from decimal import Decimal
from typing import Annotated
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Advertisement
from app.database import get_session
from app.schemas import AdvertisementCreate, AdvertisementRead, AdvertisementUpdate

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status



router = APIRouter(prefix="/advertisement", tags=["Advertisements"])

SessionDependency = Annotated[AsyncSession, Depends(get_session)]

async def get_advertisement_or_404(
        advertisement_id: int,
        session: AsyncSession,
) -> Advertisement:
    advertisement = await session.get(Advertisement, advertisement_id)

    if advertisement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Объявление не найдено",
        )

    return advertisement

@router.post(
    "",
    response_model=AdvertisementRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_advertisement(
        data: AdvertisementCreate,
        session: SessionDependency,
) -> Advertisement:
    advertisement = Advertisement(**data.model_dump())

    session.add(advertisement)
    await session.commit()
    await session.refresh(advertisement)

    return advertisement

@router.get(
    "/{advertisement_id}",
    response_model=AdvertisementRead,
)
async def get_advertisement(
        advertisement_id: int,
        session: SessionDependency,
) -> Advertisement:
    return await get_advertisement_or_404(
        advertisement_id=advertisement_id,
        session=session,
    )

@router.patch(
    "/{advertisement_id}",
    response_model=AdvertisementRead,
)
async def update_advertisement(
        advertisement_id: int,
        data: AdvertisementUpdate,
        session: SessionDependency,
) -> Advertisement:
    advertisement = await get_advertisement_or_404(
        advertisement_id=advertisement_id,
        session=session,
    )

    changes = data.model_dump(exclude_unset=True)

    if not changes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Не передано ни одного поля для обновления",
        )

    if any(value is None for value in changes.values()):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Поля объявления не могут иметь значение null",
        )

    for field, value in changes.items():
        setattr(advertisement, field, value)

    await session.commit()
    await session.refresh(advertisement)

    return advertisement

@router.delete(
    "/{advertisement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_advertisement(
        advertisement_id: int,
        session: SessionDependency,
) -> Response:
    advertisement = await get_advertisement_or_404(
        advertisement_id=advertisement_id,
        session=session,
    )

    await session.delete(advertisement)
    await session.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get(
    "",
    response_model=list[AdvertisementRead],
)
async def search_advertisements(
        session: SessionDependency,
        title: Annotated[
            str | None,
            Query(description="Поиск по части заголовка"),
        ] = None,
        description: Annotated[
            str | None,
            Query(description="Поиск по части описания"),
        ] = None,
        author: Annotated[
            str | None,
            Query(description="Поиск по части имени автора"),
        ] = None,
        price: Annotated[
            Decimal | None,
            Query(gt=0, description="Точное значение цены"),
        ] = None,
        min_price: Annotated[
            Decimal | None,
            Query(gt=0, description="Минимальная цена"),
        ] = None,
        max_price: Annotated[
            Decimal | None,
            Query(gt=0, description="Максимальная цена"),
        ] = None,
        created_from: Annotated[
            datetime | None,
            Query(description="Дата создания, начиная с"),
        ] = None,
        created_to: Annotated[
            datetime | None,
            Query(description="Дата создания, заканчивая"),
        ] = None,
        offset: Annotated[int, Query(ge=0)] = 0,
        limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[Advertisement]:
    if (
            min_price is not None
            and max_price is not None
            and min_price > max_price
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="min_price не может быть больше max_price",
        )

    if (
            created_from is not None
            and created_to is not None
            and created_from > created_to
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="created_from не может быть позже created_to",
        )

    query = select(Advertisement)

    if title is not None:
        query = query.where(
            Advertisement.title.contains(title, autoescape=True)
        )

    if description is not None:
        query = query.where(
            Advertisement.description.contains(
                description,
                autoescape=True,
            )
        )

    if author is not None:
        query = query.where(
            Advertisement.author.contains(author, autoescape=True)
        )

    if price is not None:
        query = query.where(Advertisement.price == price)

    if min_price is not None:
        query = query.where(Advertisement.price >= min_price)

    if max_price is not None:
        query = query.where(Advertisement.price <= max_price)

    if created_from is not None:
        query = query.where(
            Advertisement.created_at >= created_from
        )

    if created_to is not None:
        query = query.where(
            Advertisement.created_at <= created_to
        )

    query = (
        query
        .order_by(Advertisement.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    result = await session.scalars(query)
    return list(result.all())