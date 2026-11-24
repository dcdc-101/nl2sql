from elasticsearch import AsyncElasticsearch
from loguru import logger

from app.models.es.value_info_es import ValueInfoES


class ValueEsRepository:
    index_name = "value_index"
    mappings={
            "dynamic": False,
            "properties": {
                "id": {"type": "keyword"},
                "value": {"type": "text", "analyzer": "ik_max_word", "search_analyzer": "ik_max_word"},
                "type": {"type": "keyword"},
                "column_id": {"type": "keyword"},
                "column_name": {"type": "keyword"},
                "table_id": {"type": "keyword"},
                "table_name": {"type": "keyword"},
        }
    }
    def __init__(self,client:AsyncElasticsearch):

        self.client = client

    async def _ensure_indexes(self):
        client = self.client
        index_name=self.index_name
        if not await client.indices.exists(index=index_name):
            await client.indices.create(index=index_name,
                                  mappings=self.mappings)
        else:
            logger.info(f"Index {index_name} already exists")
    async def clear(self):
        """删除整个索引,下次insert时会按mapping重建"""
        if await self.client.indices.exists(index=self.index_name):
            await self.client.indices.delete(index=self.index_name)
            logger.info(f"Index {self.index_name} deleted")

    async def insert_values(self, values:list[ValueInfoES]):
        await self._ensure_indexes()
        index_dict={
            "index": {
                "_index":self.index_name,
            }
        }

        operations=[]

        for value in values:
            operations.append(index_dict)
            operations.append(value)
        batch_size=10
        for i in range(0,len(operations),batch_size):
            batch_operations=operations[i:i+batch_size]
            await self.client.bulk(operations=batch_operations)

    async def search(self,keyword:str)->list[ValueInfoES]:
        result=await self.client.search(
            index=self.index_name,
            query={
                "match":{
                    "value":keyword
                }
            }
        )
        return [ValueInfoES(**item["_source"]) for item in result["hits"]["hits"]]
