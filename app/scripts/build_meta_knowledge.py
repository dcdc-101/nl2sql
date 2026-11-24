import asyncio

from loguru import logger

from app.clients.embedding_client_manager import embedding_client_manager
from app.clients.es_client_manager import es_client_manager
from app.clients.mysql_client_manager import dw_mysql_client_manager, meta_mysql_client_manager
from app.clients.qdrant_client_manager import qdrant_client_manager
from app.conf.meta_config import meta_config
from app.repositories.es.value_es_repository import ValueEsRepository
from app.repositories.mysql.dw_mysql_repository import DWMysqlRepository
from app.repositories.mysql.meta_mysql_repository import MetaMysqlRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository
from app.services.meta_knowledge_service import MetaKnowledgeService


async def start_build():
    embedding_client_manager.init_client()
    dw_mysql_client_manager.init_client()
    meta_mysql_client_manager.init_client()
    qdrant_client_manager.init_client()
    es_client_manager.init_client()
    try:
        async with (dw_mysql_client_manager.session_factory() as dw_session,
                    meta_mysql_client_manager.session_factory() as meta_session,
                    ):
            service=MetaKnowledgeService(
                dw_mysql_repository=DWMysqlRepository(dw_session),
                meta_mysql_repository=MetaMysqlRepository(meta_session),
                value_es_repository=ValueEsRepository(es_client_manager.client),
                column_qdrant_repository=ColumnQdrantRepository(qdrant_client_manager.client),
                metric_qdrant_repository=MetricQdrantRepository(qdrant_client_manager.client),
                embedding_client=embedding_client_manager.client,
            )

            await service.build(meta_config)
            await dw_session.commit()
            await meta_session.commit()
            logger.info("构建成功")

    except Exception as err:
        await dw_session.rollback()
        await meta_session.rollback()
        logger.error("构建知识库失败")
        raise

    finally:
        await dw_mysql_client_manager.close()
        await meta_mysql_client_manager.close()
        await qdrant_client_manager.close()
        await es_client_manager.close()

if __name__ == "__main__":
    asyncio.run(start_build())