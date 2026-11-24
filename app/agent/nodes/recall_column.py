from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime
from loguru import logger

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.models.qdrant.column_info_qdrant import ColumnInfoQdrant
from app.prompt.promptloader import load_prompt


async def recall_column(state:DataAgentState,runtime:Runtime[DataAgentContext]):
    runtime.stream_writer({"stage":"召回字段"})

    try:
        query=state["query"]
        keywords=state["key_words"]
        embedding_client=runtime.context["embedding_client"]
        column_qdrant_repository=runtime.context["column_qdrant_repo"]
        prompt_template=PromptTemplate(
            template=load_prompt("extend_keywords_for_column_recall"),
            input_variables=["query"]
        )
        output_parser=JsonOutputParser()
        chain=prompt_template | llm | output_parser
        result=llm.ainvoke({"query":query})
        logger.info(f"recall_column llm keywords {result}")
        keywords=list(set(keywords+result))

        column_infos_dict:dict[str,ColumnInfoQdrant]={}
        for keyword in keywords:
            vector = await embedding_client.aembed_query(keyword)
            colunm_infos:list[ColumnInfoQdrant]=await column_qdrant_repository.search(vector)
            for column_info in colunm_infos:
                column_id=column_info["id"]
                if column_id not in column_infos_dict:
                    column_infos_dict[column_id]=column_info
        recall_columns:list[ColumnInfoQdrant]=list(column_infos_dict.values())

        logger.info(f"召回字段完成：{recall_columns}")

        return {"recall_columns":recall_columns}
    except Exception as e:
        logger.error(f"召回字段失败，{str(e)}")
        raise


