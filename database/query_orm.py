from sqlalchemy.future import select
from database.models import User, Group
from database.engine import async_session

async def get_user_by_user_id(user_id: str):
    """ Получить объект пользователя по его Telegram ID """
    async with async_session() as session:
        result = await session.execute(select(User).where(User.user_id == user_id))
        return result.scalars().first()

async def create_user(user_id: str, full_name: str, username: str, is_premium: bool = None):
    """ Создать объект пользователя """
    async with async_session() as session:
        user = User(user_id=user_id, full_name=full_name, username=username, is_premium=is_premium)
        session.add(user)
        await session.commit()
        return user

async def get_group_by_group_id(group_id: str):
    """ Запросить Telegram группу по ее ID """
    async with async_session() as session:
        result = await session.execute(select(Group).where(Group.group_id == group_id))
        return result.scalars().first()

async def create_group(group_id: str, title: str, description: str = None, bio: str = None,
                       invite_link: str = None, location: str = None, username: str = None):
    """ Функция для создания объекта группы """
    async with async_session() as session:
        group = Group(
            group_id=group_id,
            title=title,
            description=description,
            bio=bio,
            invite_link=invite_link,
            location=location,
            username=username
        )
        session.add(group)
        await session.commit()
        return group

async def get_all_users():
    """ Функция для получения кверисета всех юзеров """
    async with async_session() as session:
        result = await session.execute(select(User))
        return result.scalars().all()

async def update_user_invoice(user_id: str, invoice_path: str):
    """ Функция для обновления invoice path """
    async with async_session() as session:
        result = await session.execute(select(User).where(User.user_id == user_id))
        user = result.scalars().first()
        if user:
            user.path_to_invoice = invoice_path
            await session.commit()
        return user
