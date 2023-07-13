import torch
import re
from urllib.parse import urlparse


def torch_gc():
    if torch.cuda.is_available():
        # with torch.cuda.device(DEVICE):
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()
    elif torch.backends.mps.is_available():
        try:
            from torch.mps import empty_cache
            empty_cache()
        except Exception as e:
            print(e)
            print(
                "如果您使用的是 macOS 建议将 pytorch 版本升级至 2.0.0 或更高版本，以支持及时清理 torch 产生的内存占用。")


def get_root_domain(url: str):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    root_domain = '.'.join(domain.split('.')[-3:])
    return root_domain


def join_array_with_index(arr):
    result = ""
    for i, item in enumerate(arr):
        result += f"{i + 1}. {str(item)}\n"
    return result.strip()

def extract_question_and_keywords(input_string):
    if '关键词：' in input_string:
        # 提取问题
        question_pattern = r'问题：(.+?)\n'
        question_match = re.search(question_pattern, input_string)
        question = question_match.group(1) if question_match else None

        # 提取关键词
        keyword_pattern = r'关键词：(.+)'
        keyword_match = re.search(keyword_pattern, input_string)
        keywords = keyword_match.group(1) if keyword_match else None
        return question, keywords
    else:
        # 提取问题
        question_pattern = r'问题：(.+)'
        question_match = re.search(question_pattern, input_string)
        question = question_match.group(1) if question_match else None
        return question, None

if __name__ == "__main__":
    print(extract_question_and_keywords("""问题：如何评估宁德时代的股价？

关键词：宁德时代、股价、评估、市值、电动汽车、电池制造商、市场份额、领先地位、2021年、市值
"""))

    print(extract_question_and_keywords("""问题：如何评估宁德时代的股价？"""))
