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

    async def get_db_infos(self)->dict[str,str]:
        result=await self.session.execute(text("select version"))
        version=result.scalar()
        dialect=self.session.get_bind().dialect.name
        return {"version":version,"dialect":dialect}

    async def validate_sql(self, sql):
        """校验SQL"""
        # 它利用真实数据库的解析器，能发现表不存在、字段名拼写错误、JOIN 语法错误等实际问题
        # 不会执行SQL
        await self.session.execute(text(f"explain {sql}"))
    async def execute_sql(self, sql):
        """执行一条查询的SQL"""
        result = await self.session.execute(text(sql))
        # return result.mappings().all()   #rowMapping对象  不能直接序列化
        return [dict(row) for row in result.mappings().all()]

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
