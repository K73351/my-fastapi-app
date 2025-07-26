from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import select, update, insert, func
from sqlalchemy.ext.asyncio import AsyncSession
from .auth import get_current_user
from app.backend.db_depends import get_db
from app.models import *
from app.schemas import CreateRating, CreateReview
from typing import Annotated

router = APIRouter(prefix='/reviews', tags=['reviews'])


async def recalculate_product_rating(db: AsyncSession, product_id: int):
    avg_rating = await db.scalar(select(func.avg(Rating.grade)).where(Rating.product_id == product_id, Rating.is_active == True))
    avg_rating = avg_rating or 0.0

    await db.execute(update(Product).where(Product.id == product_id).values(rating=avg_rating))


@router.get('/')
async def all_reviews(db: Annotated[AsyncSession, Depends(get_db)]):
    reviews = await db.scalars(select(Review))
    ratings = await db.scalars(select(Rating))
    return {
        'reviews': reviews.all(),
        'ratings': ratings.all(),
    }


@router.get('/{product_slug}')
async def products_reviews(db: Annotated[AsyncSession, Depends(get_db)], product_slug: str):
    product = await db.scalar(select(Product).where(Product.slug == product_slug))

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There is no product found'
        )
    reviews = await db.scalars(select(Review).where(Review.product_id == product.id))

    if not reviews.all():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There is no review found'
        )

    rating = await db.scalars(select(Rating).where(Rating.product_id == product.id))

    return {
        'product': product,
        'reviews': reviews.all(),
        'rating': rating.all(),
    }


@router.post('/create')
async def add_review(db: Annotated[AsyncSession, Depends(get_db)],get_user: Annotated[dict, Depends(get_current_user)], create_rating: CreateRating, create_review: CreateReview):
    if get_user.get('is_customer'):
        rating_result = await db.execute(insert(Rating).values(grade=create_rating.grade,
                                               user_id=get_user.get('id'),
                                               product_id=create_rating.product_id).returning(Rating.id, Rating.product_id))
        row = rating_result.fetchone()
        rating_id = row.id
        product_id = row.product_id

        await db.execute(insert(Review).values(user_id=get_user.get('id'),
                                               rating_id=rating_id,
                                               comment=create_review.comment,
                                               product_id=product_id))

        await db.flush()

        await recalculate_product_rating(db, product_id)

        await db.commit()

        return {
            'status_code': status.HTTP_201_CREATED,
            'detail': 'The review was successfully created and the product listing was updated'
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='You are not authorized to use this method'
        )


@router.delete('/delete')
async def delete_reviews(db: Annotated[AsyncSession, Depends(get_db)],get_user: Annotated[dict, Depends(get_current_user)] , rating_id: int):
    if get_user.get('is_admin'):
        rating = await db.scalar(select(Rating).where(Rating.id == rating_id))

        if rating is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='There is no rating found'
            )

        await db.execute(update(Rating).where(Rating.id == rating_id).values(is_active=False))

        review = await db.scalar(select(Review).where(Review.rating_id == rating_id))
        if review is not None:
            await db.execute(update(Review).where(Review.rating_id == rating_id).values(is_active=False))

        await db.flush()

        product_id = rating.product_id
        await recalculate_product_rating(db, product_id)

        await db.commit()

        return {
            'status_code': status.HTTP_200_OK,
            'detail': 'Rating delete is successful'
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='You are not authorized to use this method'
        )

























