import os

from langchain.embeddings import OpenAIEmbeddings
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain import FewShotPromptTemplate
from langchain.prompts.example_selector import SemanticSimilarityExampleSelector
from langchain.vectorstores import Chroma

from chains.local_doc_qa import generate_few_shot_prompt
from configs.model_config import PROMPT_TEMPLATE_EXAMPLES

os.environ["OPENAI_API_KEY"] = "sk-kcfJcDXKztSEuMxaSqVjvuniMFIlz8HSr2xApuxivkNINiEc" #当前key为内测key，内测结束后会失效，在群里会针对性的发放新key
os.environ["OPENAI_API_BASE"] = "https://key.langchain.com.cn/v1"
os.environ["OPENAI_API_PREFIX"] = "https://key.langchain.com.cn"

wryl = [
    {
        "query": "迈瑞医疗现在能不能买？",
        "answer": "\
          1、国内医疗器械行业龙头，开始竞争全球市场份额。公司总部设在中国深圳，在北美、欧洲、亚洲、非洲、拉美等地区的约 40 个国家设有 51 家境外子公司；在国内设有 21 家子公司、30 余家分支机构。公司主要产品覆盖三大领域：生命信息与支持、体外诊断以及医学影像，拥有国内同行业中最全的产品线，以安全、高效、易用的“一站式”产品和 IT 解决方案满足临床需求。公司已经成为全球领先的医疗器械以及解决方案供应商。从全球市场排名来看，根据医疗器械行业网站 Medical Design & Outsourcing 历年发布的全球医疗器械公司 100 强排行榜，公司在 2020 年、2021 年和 2022 年的排名分别为第 43 位、第 36 位和第 32 位，名次逐年提升。公司产品覆盖中国近 11 万家医疗机构和 99%以上的三甲医院，产品渗透率进一步提升。生命信息与支持领域的大部分子产品如监护仪、呼吸机、除颤仪、麻醉机、输注泵、灯床塔和体外诊断领域的血球业务等市场占有率均成为国内第一。在国际市场，迈瑞受益于过去 22 年的长期市场耕耘和品牌建设，通过在北美、西欧等全球最顶尖的医院引入公司产品，在全球最领先的客户需求的检验下，打磨出最好的产品，奠定坚实的客户基础和品牌影响力。过去三年，凭借优质的产品质量和完善的服务体系，公司获取了大量的订单，加快了在各国公立市场及高端客户群的突破。据公司统计，监护仪、麻醉机、呼吸机、血球去年在全球的市场占有率已实现市场前三的地位。\
          2、长期受益于中国医疗事业发展的政策红利。政府财政专项支持：根据 2023 年的《政府工作报告》，2023 年拟安排地方政府专项债券 38,000 亿元，预计医疗领域的专项预算规模将达到 3800 亿元，这将为未来医疗卫生领域建设带来更大的资金保障。财政预算补贴：2023 年可用于卫生健康领域的补助资金高达 962.3 亿元，包括 80 亿元公立医院综合改革补助资金、39.86 亿元医疗卫生机构能力建设补助资金、69.99 亿元卫生健康人才培养补助资金、616.05 亿元支撑基本公共卫生服务的补助资金、156.4 亿元支撑重大传染病防控的经费。后疫情时代医疗基建投资：“十四五”102 项重大工程和《“十四五”优质高效医疗卫生服务体系建设实施方案》等任务落地，每年医疗基建项目投资拉动医疗器械需求。在国际上，过去三年各国医疗卫生体系均面临了巨大挑战，部分欧洲国家已经开始规划和实施了医疗补短板的举措，而发展中国家暴露的医疗短板更加严重，各国已普遍意识到卫生体系的完善程度对国家政治和经济稳定的重要性，也纷纷加大医疗投入。我们认为，未来中国经济持续增长过程中，医疗事业发展必然成为政策红利释放最彻底、最明确的领域。\
          3、相对估值低，长期投资价值显著。截至2023年7月中旬，公司动态市盈率35.40，为上市以来最低水平。2023-2025年券商机构一致预期公司净利润116.3亿、140.3亿、169.3亿，同比分别增长21%、20%、21%。随着公司盈利持续增长，公司长期投资价值更加突出，建议战略配置。"
    },
    {
        "query": "迈瑞医疗上涨空间有多大？",
        "answer": "\
          1、长期增长潜力巨大。医疗器械行业与人类生命健康息息相关，是医疗卫生体系建设的重要组成部分，具有高度的战略地位。医疗器械行业的需求属于刚性需求，行业抗风险能力较强，同时在人口老龄化的趋势下，新的需求不断增加，进而激发新的技术层出不穷。作为现代临床医疗、防控、公共卫生和健康保障体系中重要的组成部分之一，医疗器械行业无论是供给端或是需求端都维持均衡稳定的增长。公立医院绩效考核、DRG/DIP、集中带量采购等一系列政策，有助于提升医院的服务质量和运营效率，合理地利用医保资金，减轻人民群众就医负担。同时，也为掌握核心技术、提供高性价比产品的优质国产企业加速进入公立医疗机构提供了机遇。集采也有助于推动医疗器械国产化进程加速，具备核心竞争力的国产企业迎来空前的发展机遇。集采也将充分激活医疗器械行业的创新能力。国家医保局明确创新医疗器械豁免集采、纳入医保支付，将为创新医疗器械的临床使用和进一步发展奠定良好的基础。长期来看，集采政策有望加速国产医疗器械行业的发展，从中将会跑出一批具有全球竞争力的中国企业。目前，我国医疗器械企业依然呈现“小而散”的局面。从市场集中度来看，2019 年～2021 年，全球医疗器械营收 TOP100 的公司占全球整体市场的比例分别为 88.90%、89.20%、90.70%，而同期我国医疗器械营收 TOP100 的上市公司占中国整体市场的比例分别为 20.90%、19.00%、20.00%，无论是从自身数据还是从全球市场的对比数据来看，中国医疗器械企业的市场集中度依然很低，还有很大的提升空间。\
          2、公司作为国内医疗器械的龙头公司，在长期历史沉淀中有望进一步扩大国内市场公司作为国内医疗器械的龙头公司，在长期历史沉淀中有望进一步扩大国内市场份额，应享有估值溢价。公司上市以来年均净资产收益率增速为33.53%；收入和净利润年复合增长率分别为22.13%和29.98%，保持持续快速增长趋势。按照公司未来今年增长速度，二级市场股价估值修复的空间应高于盈利增长空间，考虑到公司作为医疗器械行业龙头，可给予更高估值溢价。"
    },
    {
        "query": "迈瑞医疗下跌风险有多大？",
        "answer": "\
          1、经济增速低于预期，政策红利释放较为缓慢。医疗事业支出不达标，影响国内医疗基建投入，公司增速会受到抑制。\
          2、参与全球竞争中，不可避免存在专利技术、市场竞争中的诸多冲突和风险，建议投资者做好相应风险应对方案。"
    }
]

ksd300663 = [
    {
        "query": "科士达现在能不能买入？",
        "answer": " \
          1、数据中心业务受益于AIGC和国家算力网络建设。在全球AI产业浪潮下，对于数据中心处理能力提出了更高要求。公司专注于数据中心(IDC)，研发生产的数据中心关键基础设施产品。在全国算力网络国家枢纽节点建设和“东数西算”工程中将发挥重要作用。公司数据中心业务收入占比近50%，毛利率高达35.9%，盈利能力突出。\
          2、光伏和储能逆变器业务加速发展。公司在光伏逆变器和储能逆变器两大领域全面发展，收入占比提升到40%，盈利能力突出。\
          3、新能源汽车充电桩行业前景广阔。新基建依旧是国家拉动经济增长的重要手段，也是实现现代化国家的必由之路，随着新能源汽车渗透率加速提升。充电桩业务也将成倍增长，公司具备了提升市场份额必备技术和市场条件。\
          4、盈利能力和成长能力突出。过去10年公司ROE复合增长超过10%。最近3年、5年、10年公司收入和归母净利润增幅分别为19.02%、10.02%、16.76%和26.97%、12.06%、21.77%，公司表现出非常优秀的成长性。\
          5、截至2023年7月10日，卖方机构2023-2025年一致预期估值水平分别为22.29倍、15.70倍、11.22倍，公司估值吸引力非常突出，具备中长期投资价值。"
    },
    {
        "query": "科士达上涨空间有多大？",
        "answer": " \
          1、2023年半年度业绩超越去年前三季度水平。公司预计2023年上半年盈利45,000万元-55,000万元，比上年同期增长106.47%-152.35%。报告期内，公司凭借全球渠道业务优势，数据中心、新能源光伏及储能业务板块均呈现出快速增长态势，从而带动公司整体业绩增长。\
          2、上涨预期空间较大。过去2年、5年公司股票的年化收益率水平分别为85.60%、48.10%，结合公司成长性分析，未来股价预期上涨空间较大。"
    },
    {
        "query": "科士达公司下跌风险有多大？",
        "answer": " \
        1、最近2年、5年公司股价波动率水平分别是92%、67%。整体处于震荡上涨趋势，历史最大回调幅度60%。\
        2、最近半年公司年化波动30%以上，处于下跌趋势，若遭遇重大系统性风险，公司股价存在继续调整的可能。"
    }
]

gsbank = [
    {
        "query": "工商银行现在能不能买？",
        "answer": "\
        1、中国最大的银行。工行连续十年位列英国《银行家》全球银行 1000 强榜单榜首和美国《财富》500 强榜单全球商业银行首位，向全球超 1,000 万公司客户和 7.20 亿个人客户提供丰富的金融产品和优质的金融服务。\
        2022 年末，工行总资产达到 39.6 万亿元，实现净利润 3,610 亿元，比上年增长 3.1%；加权平均净资产收益率 11.43%，保持较优水平；不良贷款率1.38%，保持在稳健区间；资本充足率达到 19.26%。拨备覆盖率 209.47%，稳定在较好水平。\
        2、数字化转型作为发展新动能。近年来，加快数字工行（D-ICBC）建设，推动业务、产品、服务等数字化升级，不断培育新增长引擎。推出手机银行 8.0 和工银e 生活 5.0 版本，搭建开放式财富社区。个人手机银行客户 5.16 亿户，移动端月活超 1.74 亿户，均保持同业第一。\
        3、低估值高股息，股东回报优秀。截至2023年7中旬，公司动态市盈率4.77倍，市净率0.55倍，估值水平处于历史10%的低水位。2022年股息率达到6.28%为历史最好水平，公司对股东的长期回报非常优秀。在金融向实体经济让利的大背景下，未来公司息差水平或保持在较低水平，基本面稳健增长的大趋势不变。\
        4、长期投资价值突出。最近2年、5年工商银行平均年化收益率分别为2.67%和3.90%，上市以来股息率平均5.03%。在全球优质资产稀缺大背景下，优质银行股以低估值高股息的展望，公司长期投资价值非常显著。"
    },
    {
        "query": "工商银行上涨空间有多大？",
        "answer": " \
        1、估值修复空间较大。截至2023年7月中旬，银行业动态市盈率4.77倍，市净率0.47倍，都处于最近10年行业10%估值水位。工商银行动态市盈率和市净率分别为4.76倍和0.55倍，处于行业中等水平。随着中国经济逐渐复苏，银行股整体估值修复空间比较大，工商银行的性价比更好。\
        2、资金长期投资的稳健选择。中国经济结构性调整过程中，低风险股票投资将逐渐成为机构、个人投资者长期加大配置的方向。工商银行作为中国最大的国有银行，其稳定性、可靠性和股东回报都将赢得资金青睐。\
        3、按照固收+的思路投资。如果考虑中国通胀水平、利率水平以及10年期国债等无风险收益率水平，工商银行当前估值有较强吸引力，股息率水平也完全超越各种低风险投资品种，长期看跑赢指数的可能性比较大。"
    },
    {
        "query": "工商银行下跌风险有多大？",
        "answer": " \
      1、过去2年、5年工商银行年化波动率分别是9%和13%，股价波动水平不大，在当前低估值历史背景下，股价继续下跌的风险相对有限。\
      2、中国经济增速放缓，或者出现局部金融风险。投资者低配银行的意愿提升或压制银行股整体行情，公司股票表现也可能低于预期。建议做好相应风险预判和管理。"
    }
]


def fewShotPrompt():
    # create our examples
    llm = OpenAI(temperature=0.9)
    examples = wryl + ksd300663 + gsbank

    # create a example template
    example_template = """User: {query}\nAI: {answer}"""

    # create a prompt example from above template
    example_prompt = PromptTemplate(
        input_variables=["query", "answer"],
        template=example_template
    )

    example_selector = SemanticSimilarityExampleSelector.from_examples(
        # This is the list of examples available to select from.
        PROMPT_TEMPLATE_EXAMPLES,
        # This is the embedding class used to produce embeddings which are used to measure semantic similarity.
        OpenAIEmbeddings(),
        # This is the VectorStore class that is used to store the embeddings and do a similarity search over.
        Chroma,
        # This is the number of examples to produce.
        k=1
    )

    # now break our previous prompt into a prefix and suffix
    # the prefix is our instructions
    prefix = """假设你是股票投资专家，我希望能够对该股票有更深入的了解。请不要考虑投资该股票的风险，请提供你的分析结果。The following are exerpts from conversations with an AI assistant. The assistant is typically sarcastic and witty, producing creative and funny responses to the users questions. Here are some examples: """
    # and the suffix our user input and output indicator
    suffix = """ query: {query} answer: """

    # now create the few shot prompt template
    few_shot_prompt_template = FewShotPromptTemplate(
        example_selector=example_selector,
        # examples = examples,
        example_prompt=example_prompt,
        prefix=prefix,
        suffix=suffix,
        input_variables=["query"],
        example_separator="\n\n"
    )

    # print(few_shot_prompt_template.format(query="What time is it?"))
    chain = LLMChain(llm=llm, prompt=few_shot_prompt_template, verbose=True)
    print(few_shot_prompt_template.format(query="宁德时代董事长？"))
    # result = chain.run(query="宁德时代能不能买？")
    # print(result)

if __name__ == "__main__":
    generate_few_shot_prompt(["sss"], "ddd", OpenAIEmbeddings())
