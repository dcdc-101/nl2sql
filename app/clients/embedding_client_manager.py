import asyncio
from typing import Optional

from langchain_huggingface import HuggingFaceEndpointEmbeddings

from app.conf.app_config import EmbeddingConfig,app_config


class EmbeddingClientManager():

    def __init__(self,config:EmbeddingConfig):
        self.config = config
        self.client :Optional[HuggingFaceEndpointEmbeddings]=None

    def _get_url(self):
        return f"http://{self.config.host}:{self.config.port}"

    def init_client(self):
        self.client=HuggingFaceEndpointEmbeddings(model=self._get_url())


embedding_client_manager=EmbeddingClientManager(app_config.embedding)

if __name__ == "__main__":
    async def test():
        embedding_client_manager.init_client()

        text="你好"
        result=embedding_client_manager.client.embed_query(text)
        print(result)
    asyncio.run(test())