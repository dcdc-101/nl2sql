from langchain_huggingface import HuggingFaceEndpointEmbeddings

from app.repositories.es.value_es_repository import ValueEsRepository
from app.repositories.mysql.dw_mysql_repository import DWMysqlRepository
from app.repositories.mysql.meta_mysql_repository import MetaMysqlRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository


class DataAgentContext:
    def __init__(self):
        embedding_client:HuggingFaceEndpointEmbeddings
        column_qdrant_repo:ColumnQdrantRepository
        metric_qdrant_repo:MetricQdrantRepository
        value_es_repo:ValueEsRepository
        meta_mysql_repo:MetaMysqlRepository
        dw_my_sql_repo:DWMysqlRepository