import json
import os
import sys
import time

from langchain import OpenAI
from langchain.agents import load_tools, initialize_agent, AgentType

from chains.local_doc_qa import LocalDocQA
from configs.model_config import EMBEDDING_MODEL, EMBEDDING_DEVICE, VECTOR_SEARCH_TOP_K, embedding_model_dict, GOOGLE_CSE_ID, GOOGLE_API_KEY

sys.path.append('.')
from models import shared
from models.loader import LoaderCheckPoint
from models.loader.args import parser

if __name__ == "__main__":
    question = "比亚迪表现"
    if len(sys.argv) > 1:
        question = sys.argv[1]
    args = None
    args = parser.parse_args()
    args_dict = vars(args)
    shared.loaderCheckPoint = LoaderCheckPoint(args_dict)
    llm_model_ins = shared.loaderLLM()
    local_doc_qa = LocalDocQA()
    embedding_model_dict["text2vec"] = "../huggingface/GanymedeNil/text2vec-large-chinese"
    local_doc_qa.init_cfg(llm_model=llm_model_ins,
                          embedding_model=EMBEDDING_MODEL,
                          embedding_device=EMBEDDING_DEVICE,
                          top_k=VECTOR_SEARCH_TOP_K)

    os.environ["OPENAI_API_KEY"] = "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"  # 当前key为内测key，内测结束后会失效，在群里会针对性的发放新key
    # os.environ["OPENAI_API_BASE"] = "https://key.langchain.com.cn/v1"
    # os.environ["OPENAI_API_PREFIX"] = "https://key.langchain.com.cn"
    llm = OpenAI(temperature=0, model_name='gpt-4')

    tools = load_tools(["google-search", "llm-math"], llm=llm, google_api_key=GOOGLE_API_KEY, google_cse_id=GOOGLE_CSE_ID)
    agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True)
    agent.run("比亚迪估值及股价")

    # for result, history in local_doc_qa.get_knowledge_based_answer_stuff(
    #         query=question, vs_path="aifin", chat_history=[], streaming=False):
    #     print(result['result'])

    # for result, history in local_doc_qa.get_knowledge_based_answer_map_reduce(
    #         query=question, vs_path="aifin", chat_history=[], streaming=False):
    #     print(result['result'])