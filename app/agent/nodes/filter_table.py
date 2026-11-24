import yaml
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.prompt.prompt_loader import load_prompt

async def filter_table(state:DataAgentState,runtime:Runtime[DataAgentContext]):
    runtime.stream_writer({"stage":"过滤表"})
    try:
        query=state["query"]
        table_infos=state["table_infos"]

        prompt_template=PromptTemplate(
            template=load_prompt("filter_table_infos"),
            input_variables=["query","table_infos"],
        )

        output_parser=JsonOutputParser()
        chain=prompt_template | llm | output_parser

        result=await chain.ainvoke({
            "query":query,
            "table_infos":yaml.dump(
                table_infos,
                allow_unicode=True,
                sort_keys=False
            )
        })

        for table_info in table_infos[:]:
            table_name=table_info["name"]
            if table_name in result:
                table_infos.remove(table_info)
            else:
                columns=table_info["columns"]
                for column in columns[:]:
                    column_name=column["name"]
                    if column_name in result["table_name"]:
                        columns.remove(column)
        logger.info(f"过滤表完成：{table_name}")
        return {"table_infos":table_infos}
    except Exception as e:
        logger.error(f"过滤表信息失败：{str(e)}")
        raise
