from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mysql.column_info_mysql import ColumnInfoMySQL
from app.models.mysql.column_metric_mysql import ColumnMetricMySQL
from app.models.mysql.metric_info_mysql import MetricInfoMySQL
from app.models.mysql.table_info_mysql import TableInfoMySQL


class MetaMysqlRepository:
    def __init__(self,session:AsyncSession):
        self.session = session

    async def clear_table_infos(self):
        """清空表信息和字段信息(随事务提交)"""
        await self.session.execute(delete(ColumnInfoMySQL))
        await self.session.execute(delete(TableInfoMySQL))

    async def clear_metric_infos(self):
        """清空指标信息和字段-指标关系(随事务提交)"""
        await self.session.execute(delete(ColumnMetricMySQL))
        await self.session.execute(delete(MetricInfoMySQL))

    async def save_table_infos(self,table_infos:list[TableInfoMySQL]):
        for table_info in table_infos:
            await self.session.merge(table_info)

    async def save_column_infos(self,column_infos:list[ColumnInfoMySQL]):
        for column_info in column_infos:
            await self.session.merge(column_info)

    async def save_metric_infos(self, metric_infos):
        for metric_info in metric_infos:
            await self.session.merge(metric_info)

    async def save_column_metric(self, column_metrics):
        for column_metric in column_metrics:
            await self.session.merge(column_metric)