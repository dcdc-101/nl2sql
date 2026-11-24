from loguru import logger
from qdrant_client import AsyncQdrantClient,models
from app.conf.app_config import app_config
from app.models.qdrant.metric_info_qdrant import MetricInfoQdrant

class MetricQdrantRepository:
    collection_name = "metric_collection"

    def __init__(self,client:AsyncQdrantClient):
        self.client = client

    async def _ensure_collection(self):
        client = self.client
        collection_name=self.collection_name
        if not await client.collection_exists(collection_name):
            await client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=app_config.qdrant.embedding_size,
                    distance=models.Distance.COSINE,
                )
            )
        else:
            logger.info(f"Index {collection_name} already exists")
    async def clear(self):
        """删除整个collection,下次upsert时会重建"""
        if await self.client.collection_exists(self.collection_name):
            await self.client.delete_collection(self.collection_name)
            logger.info(f"Collection {self.collection_name} deleted")

    async def upsert_column_vectors(self, vectors:list[list[float]], payloads:list[MetricInfoQdrant], ids:list[str]):
        client = self.client
        collection_name = self.collection_name
        await self._ensure_collection()

        batch_size = 10
        for i in range(0, len(vectors), batch_size):
            batch_vectors = vectors[i:i + batch_size]
            batch_payloads = payloads[i:i + batch_size]
            batch_ids = ids[i:i + batch_size]
            await client.upsert(
                collection_name=collection_name,
                points=[
                    models.PointStruct(
                        id=batch_ids[j],
                        payload=batch_payloads[j],
                        vector=batch_vectors[j],
                    )
                    for j in range(len(batch_ids))
                ],
            )
    async def search(self,vector:list[float],score_threshold:float=0.6)->list[MetricInfoQdrant]:
        result=await self.client.query_points(
            collection_name=self.collection_name,
            query=vector,
            search_threshold=score_threshold,
        )

        return [MetricInfoQdrant(**point.payload) for point in result.points]