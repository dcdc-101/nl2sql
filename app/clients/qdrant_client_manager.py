import asyncio
import random
from typing import Optional

from qdrant_client import AsyncQdrantClient,models

from app.conf.app_config import QdrantConfig,app_config


class QdrantClientManager:
    def __init__(self,config:QdrantConfig):
        self.config = config
        self.client:Optional[AsyncQdrantClient] = None

    def _get_url(self):
        return f"http://{self.config.host}:{self.config.port}"

    def init(self):
        self.client = AsyncQdrantClient(self._get_url())

    async def close(self):
        await self.client.close()

qdrant_client_manager = QdrantClientManager(app_config.qdrant)

if __name__ == "__main__":
    async def test():
        qdrant_client_manager.init()
        client=qdrant_client_manager.client
        collection_name="test_collection"
        if  not await client.collection_exists(collection_name=collection_name):
            await client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=10,
                    distance=models.Distance.COSINE
                ),
            )
        await client.upsert(
            collection_name=collection_name,
            points=[
                models.PointStruct(
                    id=i,
                    payload={
                        "偶数": "1" if i%2==0 else "0",
                    },
                    vector=[random.random() for _ in range(10)],
                ) for i in range(100)
            ],
        )

        result=await  client.query_points(
            collection_name=collection_name,
            query=[0.5]*10,
            limit=10,
            score_threshold=0.5,
            query_filter=models.Filter(
                must=[models.FieldCondition(key="偶数",match=models.MatchValue(value="1"))]
            )
        )
        print(result)
        print(result.points)

        await qdrant_client_manager.close()

    asyncio.run(test())