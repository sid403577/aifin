import json
import os
import sys
import time

from chains.local_doc_qa import LocalDocQA
from configs.model_config import EMBEDDING_MODEL, EMBEDDING_DEVICE, VECTOR_SEARCH_TOP_K, embedding_model_dict

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

    # for result, history in local_doc_qa.get_knowledge_based_answer_stuff(
    #         query=question, vs_path="aifin", chat_history=[], streaming=False):
    #     print(result['result'])

    for result, history in local_doc_qa.get_knowledge_based_answer_map_reduce(
            query=question, vs_path="aifin", chat_history=[], streaming=False):
        print(result['result'])