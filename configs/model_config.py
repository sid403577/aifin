import torch.cuda
import torch.backends
import os
import logging
import uuid

LOG_FORMAT = "%(levelname) -5s %(asctime)s" "-1d: %(message)s"
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logging.basicConfig(format=LOG_FORMAT)

# 在以下字典中修改属性值，以指定本地embedding模型存储位置
# 如将 "text2vec": "GanymedeNil/text2vec-large-chinese" 修改为 "text2vec": "User/Downloads/text2vec-large-chinese"
# 此处请写绝对路径
embedding_model_dict = {
    "ernie-tiny": "nghuyong/ernie-3.0-nano-zh",
    "ernie-base": "nghuyong/ernie-3.0-base-zh",
    "text2vec-base": "shibing624/text2vec-base-chinese",
    "text2vec": "huggingface/GanymedeNil/text2vec-large-chinese",
    "m3e-small": "moka-ai/m3e-small",
    "m3e-base": "moka-ai/m3e-base",
}

# Embedding model name
EMBEDDING_MODEL = "text2vec"

# Embedding running device
EMBEDDING_DEVICE = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"

# supported LLM models
# llm_model_dict 处理了loader的一些预设行为，如加载位置，模型名称，模型处理器实例
# 在以下字典中修改属性值，以指定本地 LLM 模型存储位置
# 如将 "chatglm-6b" 的 "local_model_path" 由 None 修改为 "User/Downloads/chatglm-6b"
# 此处请写绝对路径
llm_model_dict = {
    "chatglm-6b-int4-qe": {
        "name": "chatglm-6b-int4-qe",
        "pretrained_model_name": "THUDM/chatglm-6b-int4-qe",
        "local_model_path": None,
        "provides": "ChatGLM"
    },
    "chatglm-6b-int4": {
        "name": "chatglm-6b-int4",
        "pretrained_model_name": "THUDM/chatglm-6b-int4",
        "local_model_path": None,
        "provides": "ChatGLM"
    },
    "chatglm-6b-int8": {
        "name": "chatglm-6b-int8",
        "pretrained_model_name": "THUDM/chatglm-6b-int8",
        "local_model_path": None,
        "provides": "ChatGLM"
    },
    "chatglm-6b": {
        "name": "chatglm-6b",
        "pretrained_model_name": "THUDM/chatglm-6b",
        "local_model_path": "huggingface/THUDM/chatglm2-6b",
        "provides": "ChatGLM"
    },
    "chatglm2-6b": {
        "name": "chatglm2-6b",
        "pretrained_model_name": "THUDM/chatglm2-6b",
        "local_model_path": "huggingface/THUDM/chatglm2-6b",
        "provides": "ChatGLM"
    },

    "chatyuan": {
        "name": "chatyuan",
        "pretrained_model_name": "ClueAI/ChatYuan-large-v2",
        "local_model_path": None,
        "provides": None
    },
    "moss": {
        "name": "moss",
        "pretrained_model_name": "fnlp/moss-moon-003-sft",
        "local_model_path": None,
        "provides": "MOSSLLM"
    },
    "vicuna-13b-hf": {
        "name": "vicuna-13b-hf",
        "pretrained_model_name": "vicuna-13b-hf",
        "local_model_path": None,
        "provides": "LLamaLLM"
    },
    "ChatGPT-3.5": {
        "name": "gpt-3.5-turbo",  # "name"修改为fastchat服务中的"model_name"
        "pretrained_model_name": "gpt-3.5-turbo",
        "local_model_path": None,
        "provides": "FastChatOpenAILLM",  # 使用fastchat api时，需保证"provides"为"FastChatOpenAILLM"
        "api_key": None,
        "api_base_url": ""  # "name"修改为fastchat服务中的"api_base_url"
    },
    # 通过 fastchat 调用的模型请参考如下格式
    "fastchat-chatglm-6b": {
        "name": "chatglm-6b",  # "name"修改为fastchat服务中的"model_name"
        "pretrained_model_name": "chatglm-6b",
        "local_model_path": None,
        "provides": "FastChatOpenAILLM",  # 使用fastchat api时，需保证"provides"为"FastChatOpenAILLM"
        "api_base_url": "http://localhost:8000/v1"  # "name"修改为fastchat服务中的"api_base_url"
    },
    "fastchat-chatglm2-6b": {
        "name": "chatglm2-6b",  # "name"修改为fastchat服务中的"model_name"
        "pretrained_model_name": "chatglm2-6b",
        "local_model_path": None,
        "provides": "FastChatOpenAILLM",  # 使用fastchat api时，需保证"provides"为"FastChatOpenAILLM"
        "api_base_url": "http://43.163.215.8:8000/v1"  # "name"修改为fastchat服务中的"api_base_url"
    },

    # 通过 fastchat 调用的模型请参考如下格式
    "fastchat-vicuna-13b-hf": {
        "name": "vicuna-13b-hf",  # "name"修改为fastchat服务中的"model_name"
        "pretrained_model_name": "vicuna-13b-hf",
        "local_model_path": None,
        "provides": "FastChatOpenAILLM",  # 使用fastchat api时，需保证"provides"为"FastChatOpenAILLM"
        "api_base_url": "http://localhost:8000/v1"  # "name"修改为fastchat服务中的"api_base_url"
    },
}

# LLM 名称
LLM_MODEL = "fastchat-chatglm2-6b"
# 量化加载8bit 模型
LOAD_IN_8BIT = False
# Load the model with bfloat16 precision. Requires NVIDIA Ampere GPU.
BF16 = False
# 本地lora存放的位置
LORA_DIR = "loras/"

# LLM lora path，默认为空，如果有请直接指定文件夹路径
LLM_LORA_PATH = ""
USE_LORA = True if LLM_LORA_PATH else False

# LLM streaming reponse
STREAMING = True

# Use p-tuning-v2 PrefixEncoder
USE_PTUNING_V2 = False

# LLM running device
LLM_DEVICE = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"

# 知识库默认存储路径
KB_ROOT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "knowledge_base")

CONDENSE_QUESTION_PROMPT = """根据以下聊天记录和后续问题，请使用中文将后续问题改写为一个独立的问题。

聊天记录：
{chat_history}
后续问题：{question}
独立问题："""

CONDENSE_QUESTION_PROMPT_KEYWORDS = """根据以下聊天记录和后续问题，首先使用中文将后续问题改写为一个独立的问题, 然后提取该问题的搜索查询关键词。
格式如下：
问题：
关键词：

聊天记录：
{chat_history}
后续问题：{question}
"""


# 基于上下文的prompt模版，请务必保留"{question}"和"{context}"
PROMPT_TEMPLATE = """
我会提供已知数据，以专业的股票经济分析师的角度给出问题的相关优势和风险建议，
帮助分析解决问题。
需要引用提供的已知数据内容不少于三段，输出问题答案的相关背景\判读依据\长远趋势，给出针对问题的总结，分析尽量丰满，要有依据和结论。
最后给出关键总结和尽可能明确的回答，总结内容100字左右。
已知信息：{context} 
问题是：{question}"""

PROMPT_TEMPLATE_EXAMPLE = """
    User: {query}
    AI: {answer}
"""
# 基于上下文的prompt模版，请务必保留"{question}"和"{context}"
PROMPT_TEMPLATE_EXAMPLE_PREFIX = """
假设你是股票投资专家，我希望能够对该股票有更深入的了解。请不要考虑投资该股票的风险，请提供不少于200字的的分析依据和结论。以下是一些例子：

"""
PROMPT_TEMPLATE_EXAMPLE_SUFFIX="""
已知信息：{context}
根据上述已知信息，简洁和专业的来回答用户的问题。问题是：{question}
"""

PROMPT_TEMPLATE_EXAMPLES = [
    {
        "query": "科士达现在能不能买入？",
        "answer": "\
          1、数据中心业务受益于AIGC和国家算力网络建设。在全球AI产业浪潮下，对于数据中心处理能力提出了更高要求。公司专注于数据中心(IDC)，研发生产的数据中心关键基础设施产品。在全国算力网络国家枢纽节点建设和“东数西算”工程中将发挥重要作用。公司数据中心业务收入占比近50%，毛利率高达35.9%，盈利能力突出。\
          2、光伏和储能逆变器业务加速发展。公司在光伏逆变器和储能逆变器两大领域全面发展，收入占比提升到40%，盈利能力突出。\
          3、新能源汽车充电桩行业前景广阔。新基建依旧是国家拉动经济增长的重要手段，也是实现现代化国家的必由之路，随着新能源汽车渗透率加速提升。充电桩业务也将成倍增长，公司具备了提升市场份额必备技术和市场条件。\
          4、盈利能力和成长能力突出。过去10年公司ROE复合增长超过10%。最近3年、5年、10年公司收入和归母净利润增幅分别为19.02%、10.02%、16.76%和26.97%、12.06%、21.77%，公司表现出非常优秀的成长性。\
          5、截至2023年7月10日，卖方机构2023-2025年一致预期估值水平分别为22.29倍、15.70倍、11.22倍，公司估值吸引力非常突出，具备中长期投资价值。"
    },
    {
        "query": "科士达上涨空间有多大？",
        "answer": "\
          1、2023年半年度业绩超越去年前三季度水平。公司预计2023年上半年盈利45,000万元-55,000万元，比上年同期增长106.47%-152.35%。报告期内，公司凭借全球渠道业务优势，数据中心、新能源光伏及储能业务板块均呈现出快速增长态势，从而带动公司整体业绩增长。\
          2、上涨预期空间较大。过去2年、5年公司股票的年化收益率水平分别为85.60%、48.10%，结合公司成长性分析，未来股价预期上涨空间较大。"
    },
    {
        "query": "科士达公司下跌风险有多大？",
        "answer": "\
        1、最近2年、5年公司股价波动率水平分别是92%、67%。整体处于震荡上涨趋势，历史最大回调幅度60%。\
        2、最近半年公司年化波动30%以上，处于下跌趋势，若遭遇重大系统性风险，公司股价存在继续调整的可能。"
    }
]

# 缓存知识库数量
CACHED_VS_NUM = 1

# 文本分句长度
SENTENCE_SIZE = 100

# 匹配后单段上下文长度
CHUNK_SIZE = 250

# 传入LLM的历史记录长度
LLM_HISTORY_LEN = 3

# 知识库检索时返回的匹配内容条数
VECTOR_SEARCH_TOP_K = 10

# 知识检索内容相关度 Score, 数值范围约为0-1100，如果为0，则不生效，经测试设置为小于500时，匹配结果更精准
VECTOR_SEARCH_SCORE_THRESHOLD = 0

NLTK_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "nltk_data")

FLAG_USER_NAME = uuid.uuid4().hex

logger.info(f"""
loading model config
llm device: {LLM_DEVICE}
embedding device: {EMBEDDING_DEVICE}
dir: {os.path.dirname(os.path.dirname(__file__))}
flagging username: {FLAG_USER_NAME}
""")

# 是否开启跨域，默认为False，如果需要开启，请设置为True
# is open cross domain
OPEN_CROSS_DOMAIN = False

# Bing 搜索必备变量
# 使用 Bing 搜索需要使用 Bing Subscription Key,需要在azure port中申请试用bing search
# 具体申请方式请见
# https://learn.microsoft.com/en-us/bing/search-apis/bing-web-search/create-bing-search-service-resource
# 使用python创建bing api 搜索实例详见:
# https://learn.microsoft.com/en-us/bing/search-apis/bing-web-search/quickstarts/rest/python
BING_SEARCH_URL = "https://api.bing.microsoft.com/v7.0/search"
# 注意不是bing Webmaster Tools的api key，

# 此外，如果是在服务器上，报Failed to establish a new connection: [Errno 110] Connection timed out
# 是因为服务器加了防火墙，需要联系管理员加白名单，如果公司的服务器的话，就别想了GG
BING_SUBSCRIPTION_KEY = "b5904d50bfd345ec8b8f6e9fe4bb75e6"

GOOGLE_API_KEY = "AIzaSyACpSZ6gtDOKFadgM651TNu7DdzvtStX6Y"

GOOGLE_CSE_ID = "d4451a0622ff94fc7"

# 是否开启中文标题加强，以及标题增强的相关配置
# 通过增加标题判断，判断哪些文本为标题，并在metadata中进行标记；
# 然后将文本与往上一级的标题进行拼合，实现文本信息的增强。
ZH_TITLE_ENHANCE = False

MILVUS_HOST = "8.217.52.63"

MILVUS_PORT = "19530"

COMPANYS = ['宁德时代', '贵州茅台', '迈瑞医疗']