#操作mysql数据库的客户端管理模块
import optparse
from idlelib import autocomplete
from typing import Optional

from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession, async_sessionmaker
from app.conf.app_config import DBConfig, app_config


class MysqlClientManager:
    def __init__(self,config:DBConfig):
        self.config=config
        self.engine:Optional[AsyncEngine]=None
        self.session_factory:Optional[async_sessionmaker]=None

    def _get_url(self):
        return f"mysql+asyncmy://{self.config.user}:{self.config.password}@{self.config.host}:{self.config.port}/{self.config.database}?charset=utf8mb4"

    def init_client(self):
        self.engine=create_async_engine(
            self._get_url(),
            pool_size=10,
            max_overflow=5,
            pool_pre_ping=True,
        )
        self.session_factory=async_sessionmaker(
            self.engine,
            autobegin=True,
            expire_on_commit=False,
            autoflush=False,
        )

    async def close(self):
        await self.engine.dispose()

dw_mysql_client_manager=MysqlClientManager(app_config.db_dw)

meta_mysql_client_manager=MysqlClientManager(app_config.db_meta)

if __name__=="__main__":
    pass