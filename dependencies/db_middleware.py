from sqlmodel import create_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.orm import sessionmaker

from maxapi.filters.middleware import BaseMiddleware

from settings import get_db_url

engine = AsyncEngine(create_engine(get_db_url()))
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

#db
class DBSessionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        async with async_session() as session:
            data['session'] = session
            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()