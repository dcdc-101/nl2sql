from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState, MetricInfoState, ColumnInfoState, TableInfoState
from app.core.log import logger
from app.models.es.value_info_es import ValueInfoES
from app.models.mysql.column_info_mysql import ColumnInfoMySQL
from app.models.mysql.table_info_mysql import TableInfoMySQL
from app.models.qdrant.column_info_qdrant import ColumnInfoQdrant
from app.models.qdrant.metric_info_qdrant import MetricInfoQdrant



async def merge_retrieved(state:DataAgentState,runtime:Runtime[DataAgentContext]):
    runtime.stream_writer({"stage":"合并召回"})
    try:
        recall_columns:list[ColumnInfoQdrant]=state["recall_columns"]
        recall_metrics: list[MetricInfoQdrant] = state["recall_metrics"]
        recall_values: list[ValueInfoES] = state["recall_values"]
        meta_mysql_repo = runtime.context["meta_mysql_repo"]

        column_infos_dict:dict[str, ColumnInfoQdrant]={item["id"]:item for item in recall_columns}

        for metric in recall_metrics:
            for relevant_column_id in metric["relevant_columns"]:
                if relevant_column_id not in column_infos_dict:
                    column_info_mysql:ColumnInfoMySQL = await meta_mysql_repo.get_column_info_by_id(relevant_column_id)