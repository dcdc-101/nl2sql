import uuid
from elasticsearch import Elasticsearch
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from loguru import logger

from app.models.mysql.column_metric_mysql import ColumnMetricMySQL
from app.conf.meta_config import MetaConfig, TableConfig, MetricConfig
from app.models.es.value_info_es import ValueInfoES
from app.models.mysql.column_info_mysql import ColumnInfoMySQL
from app.models.mysql.metric_info_mysql import MetricInfoMySQL
from app.models.mysql.table_info_mysql import TableInfoMySQL
from app.models.qdrant import column_info_qdrant
from app.models.qdrant.metric_info_qdrant import MetricInfoQdrant
from app.repositories.es.value_es_repository import ValueEsRepository
from app.repositories.mysql.dw_mysql_repository import DWMysqlRepository
from app.repositories.mysql.meta_mysql_repository import MetaMysqlRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository
from app.models.qdrant.column_info_qdrant import ColumnInfoQdrant

class MetaKnowledgeService:
    def __init__(self,
                 dw_mysql_repository:DWMysqlRepository,
                 meta_mysql_repository:MetaMysqlRepository,
                 value_es_repository:ValueEsRepository,
                 column_qdrant_repository:ColumnQdrantRepository,
                 metric_qdrant_repository:MetricQdrantRepository,
                 embedding_client:HuggingFaceEndpointEmbeddings
                 ):
        self.dw_mysql_repository = dw_mysql_repository
        self.meta_mysql_repository = meta_mysql_repository
        self.value_es_repository = value_es_repository
        self.column_qdrant_repository = column_qdrant_repository
        self.metric_qdrant_repository = metric_qdrant_repository
        self.embedding_client = embedding_client

    async def build(self,config:MetaConfig):
        logger.info("开始构建业务")

        if config.tables:
            # 重新构建前先清空旧数据,避免残留和重复
            await self.meta_mysql_repository.clear_table_infos()
            await self.column_qdrant_repository.clear()
            await self.value_es_repository.clear()
            logger.info("已清空旧的表/字段数据")

            column_infos:list[ColumnInfoMySQL]=await self._save_table_infos_to_meta_db(config.tables)
            logger.info("成功保存表信息和字段信息到meta")
            #对字段信息建立向量索引
            await self._save_column_values_to_qdrant(column_infos,config.tables)
            logger.info("保存字段信息到qdrant向量库")

            await self._save_column_values_to_es(column_infos,config.tables)
            logger.info("保存字段信息到es全文库索引成功")

        if config.metrics:
            await self.meta_mysql_repository.clear_metric_infos()
            await self.metric_qdrant_repository.clear()
            logger.info("已清空旧的指标数据")

            metric_infos:list[MetricInfoMySQL]=await self._save_metric_info_to_meta_db(config.metrics)
            logger.info("保存指标信息到meta库成功")

            await self._save_metric_infos_to_qdrant(metric_infos)

            logger.info("保存指标信息到qdrant库成功")

    async def _save_table_infos_to_meta_db(self, tables)->list[ColumnInfoMySQL]:
        talbe_infos:list[TableInfoMySQL]=[]
        column_infos:list[ColumnInfoMySQL]=[]
        for table in tables:
            table_info=TableInfoMySQL(
                id=table.name,
                name=table.name,
                role=table.role,
                description=table.description,
            )
            talbe_infos.append(table_info)
            column_type_dict:dict[str,str]=await self.dw_mysql_repository.get_column_types(table_info.name)
            for column in table.columns:
                examples:list=await self.dw_mysql_repository.get_column_values(table_info.name, column.name)
                column_info=ColumnInfoMySQL(
                    id=f"{table.name}.{column.name}",
                    name=column.name,
                    type=column_type_dict[column.name],  # 需要检查表中字段类型
                    role=column.role,
                    examples=examples,  # 需要查表
                    description=column.description,
                    alias=column.alias,
                    table_id=table_info.id
                )
                column_infos.append(column_info)
        await self.meta_mysql_repository.save_table_infos(talbe_infos)
        await self.meta_mysql_repository.save_column_infos(column_infos)
        return column_infos

    async def _save_column_values_to_qdrant(self, column_infos, tables):
        data_dict_list:list[dict]=[]
        for column_info in column_infos:
            column_info_qdrant=ColumnInfoQdrant(
                id=column_info.id,
                name=column_info.name,
                type=column_info.type,
                role=column_info.role,
                examples=column_info.examples,
                description=column_info.description,
                alias=column_info.alias,
                table_id=column_info.table_id
            )
            data_dict_list.append({
                "id":uuid.uuid4(),
                "embedding_text":column_info.name,
                "payload":column_info_qdrant
            })
            data_dict_list.append({
                "id": uuid.uuid4(),
                "embedding_text": column_info.description,
                "payload": column_info_qdrant
            })
            # alias
            for alia in column_info.alias:
                data_dict_list.append({
                    "id": uuid.uuid4(),
                    "embedding_text": alia,
                    "payload": column_info_qdrant
                })
        embedded_text=[data_dict["embedding_text"] for data_dict in data_dict_list]
        batch_size=4
        vectors:list[list[float]]=[]
        for i in range(0,len(embedded_text),batch_size):
            batch_embedded_text=embedded_text[i:i+batch_size]
            batch_vectors:list[list[float]]=await self.embedding_client.aembed_documents(batch_embedded_text)
            vectors.extend(batch_vectors)
        ids:list[str]=[data_dict["id"] for data_dict in data_dict_list]
        payloads:list[dict]=[data_dict["payload"] for data_dict in data_dict_list]

        await self.column_qdrant_repository.upsert_column_vectors(vectors,payloads,ids)

    async def _save_column_values_to_es(self, column_infos:list[ColumnInfoMySQL], tables:list[TableConfig]):
        column_sync_dict:dict[str,bool]={}
        for table in tables:
            for column in table.columns:
                column_sync_dict[f"{table.name}.{column.name}"]=column.sync

        value_infos:list[ValueInfoES]=[]
        for column_info in column_infos:
            sync=column_sync_dict[column_info.id]
            if sync:
                values=await self.dw_mysql_repository.get_column_values(column_info.table_id, column_info.name,100000)
                for value in values:
                    value_info=ValueInfoES(
                    id=f"{column_info.id}.{value}",
                    value=value,
                    type=column_info.type,
                    column_id=column_info.id,
                    column_name=column_info.name,
                    table_id=column_info.table_id,
                    table_name=column_info.table_id
                )
                    value_infos.append(value_info)



        await self.value_es_repository.insert_values(value_infos)

    async def _save_metric_info_to_meta_db(self, metrics:list[MetricConfig])->list[MetricInfoMySQL]:
        metric_infos: list[MetricInfoMySQL] = []

        column_metrics: list[ColumnMetricMySQL] = []

        for metric in metrics:
            metric_infos.append(MetricInfoMySQL(
                id=metric.name,
                name=metric.name,
                description=metric.description,
                relevant_columns=metric.relevant_columns,
                alias=metric.alias
            ))
            for column_id in metric.relevant_columns:
                column_metrics.append(ColumnMetricMySQL(
                    column_id=column_id,
                    metric_id=metric.name
                ))
        await self.meta_mysql_repository.save_metric_infos(metric_infos)
        await self.meta_mysql_repository.save_column_metric(column_metrics)
        return metric_infos

    async def _save_metric_infos_to_qdrant(self, metric_infos:list[MetricInfoMySQL]):
        data_dict_list: list[dict] = []
        for metric_info in metric_infos:
            metric_info_qdrant = MetricInfoQdrant(
                id=metric_info.id,
                name=metric_info.name,
                description=metric_info.description,
                alias=metric_info.alias,
                relevant_columns=metric_info.relevant_columns,

            )
            data_dict_list.append({
                "id": uuid.uuid4(),
                "embedding_text": metric_info.name,
                "payload": metric_info_qdrant
            })
            data_dict_list.append({
                "id": uuid.uuid4(),
                "embedding_text": metric_info.description,
                "payload": metric_info_qdrant
            })
            # alias
            for alia in metric_info.alias:
                data_dict_list.append({
                    "id": uuid.uuid4(),
                    "embedding_text": alia,
                    "payload": metric_info_qdrant
                })
        embedded_text = [data_dict["embedding_text"] for data_dict in data_dict_list]
        batch_size = 4
        vectors: list[list[float]] = []
        for i in range(0, len(embedded_text), batch_size):
            batch_embedded_text = embedded_text[i:i + batch_size]
            batch_vectors: list[list[float]] = await self.embedding_client.aembed_documents(batch_embedded_text)
            vectors.extend(batch_vectors)
        ids: list[str] = [data_dict["id"] for data_dict in data_dict_list]
        payloads: list[dict] = [data_dict["payload"] for data_dict in data_dict_list]

        await self.metric_qdrant_repository.upsert_column_vectors(vectors, payloads, ids)

