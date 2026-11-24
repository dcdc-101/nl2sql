from typing import TypedDict

from app.models.es.value_info_es import ValueInfoES
from app.models.qdrant.column_info_qdrant import ColumnInfoQdrant
from app.models.qdrant.metric_info_qdrant import MetricInfoQdrant
class DateInfoState(TypedDict):
    date: str # 年月日
    weekday: str # 星期
    quarter: str # 季度  Q1-Q4

# 数据库信息
class DBInfoState(TypedDict):
    version: str # 版本号
    dialect: str # 数据库名称



class ColumnInfoState(TypedDict):
    name: str
    type:str
    role: str
    examples:list
    description:str
    alias: list

class TableInfoState(TypedDict):
    name:str
    role:str
    description:str
    columns: list[ColumnInfoState]

class MetricInfoState(TypedDict):
    name:str
    description:str
    relevant_columns:list
    alias:list


class DataAgentState(TypedDict):
    query:str
    keywords:str
    sql:str
    error:str
    recall_columns:list[ColumnInfoQdrant]
    recall_metrics:list[MetricInfoQdrant]
    recall_values:list[ValueInfoES]
    table_infos:list[TableInfoState]
    metric_infos:list[MetricInfoState]
    date_info:DateInfoState
    db_info:DBInfoState