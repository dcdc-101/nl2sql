import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.mysql_client_manager import dw_mysql_client_manager


class DWMysqlRepository:
    def __init__(self,session:AsyncSession):
        self.session = session

    async def get_column_types(self, talbe_name:str)->dict[str,str]:
        sql=f"show columns from {talbe_name}"
        result=await self.session.execute(text(sql))
        return {row.Field:row.Type for row in result.all()}

    async def get_column_values(self, table_name:str, column_name:str,limit:int=10)->list:
        sql=f"select distinct {column_name} from {table_name} limit {limit}"
        result=await self.session.execute(text(sql))
        return result.scalars().all()


if __name__=="__main__":
    dw_mysql_client_manager.init_client()
    async def test():
        async with dw_mysql_client_manager.session_factory() as session:
            # sql = f"show columns from dim_customer"
            # result=await session.execute(text(sql))
            # result=result.all()
            # print(result)
            # print(type(result))
            # print(result[0])
            # print(result[0].Field)

            sql = f"select distinct product_id from fact_order limit 10"
            result = await session.execute(text(sql))
            print(result)
            print(result.scalars())
            print(result.scalars().all())

        await dw_mysql_client_manager.close()

    asyncio.run(test())
