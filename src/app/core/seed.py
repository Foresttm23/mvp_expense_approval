"""Database seed script to automatically populate default approvers and test users from config."""

from __future__ import annotations

import asyncio

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import ExpenseSettings, get_settings
from app.core.database import close_db, db_session_manager, init_db
from app.core.enums import ExpenseCategory
from app.core.security import hash_password
from app.models.expense import CategoryApprover
from app.models.user import User


async def seed_database() -> None:
    settings = get_settings()
    init_db(settings.DATABASE_URL)

    async with db_session_manager.session() as session:
        await seed_category_approvers(session, settings)
        await seed_test_users(session, settings)

        await session.commit()
        logger.info("Database seeding completed successfully.")

    await close_db()


async def seed_test_users(session: AsyncSession, settings: ExpenseSettings) -> None:
    for test_user in settings.DEFAULT_TEST_USERS:
        email = test_user.email
        name = test_user.name
        plain_password = test_user.password
        roles = test_user.roles

        if isinstance(roles, str):
            roles = [r.strip() for r in roles.split(",")]

        stmt = select(User).where(User.email == email)
        result = await session.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if not existing_user:
            hashed_pw = await hash_password(plain_password)
            user = User(
                email=email,
                full_name=name,
                hashed_password=hashed_pw,
                roles=roles,
                is_active=True,
            )
            session.add(user)
            logger.info(f"Created test user: {email} with roles: {roles}")
        else:
            existing_user.full_name = name
            existing_user.roles = roles
            session.add(existing_user)
            logger.debug(f"Test user already exists, updated details: {email}")

async def seed_category_approvers(session: AsyncSession, settings: ExpenseSettings) -> None:
    for category_name, approver_config in settings.DEFAULT_CATEGORY_APPROVERS.items():
        category_enum = ExpenseCategory(category_name)

        email = approver_config.email
        name = approver_config.name
        plain_password = approver_config.password
        roles = approver_config.roles

        if isinstance(roles, str):
            roles = [r.strip() for r in roles.split(",")]

        stmt = select(User).where(User.email == email)
        result = await session.execute(stmt)
        approver = result.scalar_one_or_none()

        if not approver:
            hashed_pw = await hash_password(plain_password)
            approver = User(
                email=email,
                full_name=name,
                hashed_password=hashed_pw,
                roles=roles,
                is_active=True,
            )
            session.add(approver)
            await session.flush()
            logger.info(f"Created approver user: {email} ({category_name}) with roles: {roles}")
        else:
            approver.full_name = name
            approver.roles = roles
            session.add(approver)
            await session.flush()
            logger.debug(f"Approver user already exists, updated details: {email}")

        map_stmt = select(CategoryApprover).where(
            CategoryApprover.category == category_enum
        )
        map_result = await session.execute(map_stmt)
        mapping = map_result.scalar_one_or_none()

        if not mapping:
            mapping = CategoryApprover(
                category=category_enum,
                approver_id=approver.id,
            )
            session.add(mapping)
            logger.info(f"Mapped category {category_name} -> {email}")
        else:
            mapping.approver_id = approver.id
            session.add(mapping)
            logger.debug(f"Updated category mapping: {category_name} -> {email}")


if __name__ == "__main__":
    asyncio.run(seed_database())
