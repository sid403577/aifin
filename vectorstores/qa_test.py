import os
import sys
import time
from langchain import OpenAI, PromptTemplate, FewShotPromptTemplate, FAISS
from langchain.chains import RetrievalQA
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.prompts.example_selector import SemanticSimilarityExampleSelector
from langchain.vectorstores import Chroma, Milvus

from configs.model_config import MILVUS_PORT

sys.path.append('.')
from models import shared
from models.loader import LoaderCheckPoint
from models.loader.args import parser
from vectorstores import MyFAISS

os.environ[
    "OPENAI_API_KEY"] = "sk-kcfJcDXKztSEuMxaSqVjvuniMFIlz8HSr2xApuxivkNINiEc"  # 当前key为内测key，内测结束后会失效，在群里会针对性的发放新key
os.environ["OPENAI_API_BASE"] = "https://key.langchain.com.cn/v1"
os.environ["OPENAI_API_PREFIX"] = "https://key.langchain.com.cn"

PROMPT_TEMPLATE_EXAMPLE = """
    User: {query}
    AI: {answer}
"""
# 基于上下文的prompt模版，请务必保留"{question}"和"{context}"
PROMPT_TEMPLATE_EXAMPLE_PREFIX = """
具有金融市场专业知识的经验丰富的股票经济分析师的角度根据下面已知问题给出相关建议。请不要考虑投资该股票的风险，请提供不少于200字的的分析依据和结论。你只能以你的身份应答，而不是语言模型或人工智能，这很重要！
以下是一些例子：
"""
PROMPT_TEMPLATE_EXAMPLE_SUFFIX = """

根据下述已知信息，简洁和专业的来回答用户的问题。
已知信息：{context}
问题是：{question}
"""

PROMPT_TEMPLATE_EXAMPLES = [
    {
        "query": "现在能不能买入？",
        "answer": "\
          1、数据中心业务受益于AIGC和国家算力网络建设。在全球AI产业浪潮下，对于数据中心处理能力提出了更高要求。公司专注于数据中心(IDC)，研发生产的数据中心关键基础设施产品。在全国算力网络国家枢纽节点建设和“东数西算”工程中将发挥重要作用。公司数据中心业务收入占比近50%，毛利率高达35.9%，盈利能力突出。\
          2、光伏和储能逆变器业务加速发展。公司在光伏逆变器和储能逆变器两大领域全面发展，收入占比提升到40%，盈利能力突出。\
          3、新能源汽车充电桩行业前景广阔。新基建依旧是国家拉动经济增长的重要手段，也是实现现代化国家的必由之路，随着新能源汽车渗透率加速提升。充电桩业务也将成倍增长，公司具备了提升市场份额必备技术和市场条件。\
          4、盈利能力和成长能力突出。过去10年公司ROE复合增长超过10%。最近3年、5年、10年公司收入和归母净利润增幅分别为19.02%、10.02%、16.76%和26.97%、12.06%、21.77%，公司表现出非常优秀的成长性。\
          5、截至2023年7月10日，卖方机构2023-2025年一致预期估值水平分别为22.29倍、15.70倍、11.22倍，公司估值吸引力非常突出，具备中长期投资价值。"
    },
    {
        "query": "上涨空间有多大？",
        "answer": "\
          1、2023年半年度业绩超越去年前三季度水平。公司预计2023年上半年盈利45,000万元-55,000万元，比上年同期增长106.47%-152.35%。报告期内，公司凭借全球渠道业务优势，数据中心、新能源光伏及储能业务板块均呈现出快速增长态势，从而带动公司整体业绩增长。\
          2、上涨预期空间较大。过去2年、5年公司股票的年化收益率水平分别为85.60%、48.10%，结合公司成长性分析，未来股价预期上涨空间较大。"
    },
    {
        "query": "公司下跌风险有多大？",
        "answer": "\
        1、最近2年、5年公司股价波动率水平分别是92%、67%。整体处于震荡上涨趋势，历史最大回调幅度60%。\
        2、最近半年公司年化波动30%以上，处于下跌趋势，若遭遇重大系统性风险，公司股价存在继续调整的可能。"
    },
    {
        "query": "定向增发目的是什么？",
        "answer": "\
       1、通过光伏逆变器、储能变流器产品生产基地建设项目、光储系统集成产品生产基地建设项目、电池模组生产基地（二期）建设项目及福州研发中心建设项目，积极响应国家“双碳”战略目标及相关产业政策的号召，满足光伏、储能产业快速增长及各类新能源功率变换装置和系统技术变革升级的需求，缓解市场供需不平衡的矛盾，推动光伏、储能行业高质量发展，助力早日实现“双碳”战略目标。\
       2、公司目前的产能及之前规划的新增产能已经无法满足日益快速增长的市场需求，为进一步提升公司产能，扩大公司的市场份额和盈利能力，本次募投项目将通过新建自有生产场地，配套引进所需生产、检测、运输设备和仪器，并招聘专业技术及生产人员，突破现有产能瓶颈；同时，将继续引进自动化设备并合理构建空间布局，以提高生产效率，提升项目效益。\
       3、本次向特定对象发行股票募集资金并部分用于补充流动资金，一方面可以直接增强公司资金实力，有效满足公司主营业务经营规模扩大带来的新增营运资金需求，缓解资金需求压力；另一方面有助于优化公司资本结构，提高抗风险能力。\
       4、结论：公司再融资依然是希望顺应中国碳中和发展战略，满足下游市场旺盛需求，扩大公司市场影响力，为股东获取更大回报。"
    },
    {
        "query": "基本面潜在风险是什么？",
        "answer": "\
        1、宏观环境变化风险。国际形势动荡、贸易保护主义、突发的公共卫生事件、国内外大宗商品短缺或价格上涨等因素均可能影响企业的发展。\
        2、法律风险随着公司在海外建设生产经营基地及扩建海外分支机构，全球性业务将持续增长，由于当地法律环境的复杂性，虽然公司力求遵守所有当地适用的法规且无意违反，但仍可能存在各种难以预见的风险。\
        3、政策风险。公司数据中心、新能源板块业务的发展依赖宏观政策，国家大力建设数据中心、重点发展新能源行业和推广新能源汽车充电设施建设成为未来趋势。如果政策落地不及时、扶持效果不及预期，将对公司经营产生影响。为有效控制上述风险，公司将紧密跟踪政策动向和市场变化，采取有效的应对措施，以满足市场需求和抢占市场份额。\
        4、财务风险。公司的财务风险主要体现在应收账款回款方面，随着公司业务规模不断增长，应收账款总额也在不断的扩大，特别是光伏新能源产品回款周期长、回款风险大的问题一直存在。\
        5、汇率波动风险。随着公司海外业务占总营业收入的比重增加，且公司海外业务主要以美元结算。鉴于人民币汇率走势的不确定性，公司存在以外币结算的收入按人民币计量时波动的风险。\
        6、结论：公司面临的风险和大多数行业一样，有国际国内大环境、政策、法律、财务、汇率等诸多风险，需要持续跟踪研究。"
    },
    {
        "query": "公司有什么技术储备？",
        "answer": "\
        1、公司先后被评为国家级高新技术企业、国家技术创新示范企业、广东省诚信示范企业；并依托公司的技术中心组建的广东省太阳能光伏发电企业工程技术研究中心、深圳市企业工程实验室等研发机构，公司的技术中心被国家发改委等五部门认定为国家级企业技术中心。\
        2、截至 2023 年 3 月底，公司已获得授权专利 272 项，其中发明专利 47 项，实用新型 133 项，公司具备较强技术优势，雄厚的研发实力已成为驱动公司在全球市场上业绩持续增长的核心动力。"
    },
    {
        "query": "公司具体是做什么的？",
        "answer": "\
        1、科士达公司成立于 1993 年，是一家专注于数据中心（IDC）及新能源领域的智能网络能源供应服务商。\
        2、数据中心产品。主要包括：不间断电源（UPS）、高压直流电源、精密空调、通信电源、精密配电、蓄电池、网络服务器机柜、动力环境监控等设备和系统，广泛应用于金融、通信、IDC、互联网、政府机构、轨道交通、工业制造、电力、医疗、教育等行业和领域，着力保障数据中心信息安全、维护其稳定可靠持续运行。\
        3、光伏、储能产品包括。集中式光伏逆变器、组串式光伏逆变器、智能汇流箱、监控及家用逆变器、模块化储能变流器、集中式储能变流器、工商业储能系统、户用储能系统、逆变升压一体化集成系统、第二代储能系统能量管理及监控平台、调峰调频系统、大型集装箱式储能集成系统、光储充系统等；户用储能一体机方案集合了公司在电力电子、储能领域的优势，调试安装简单，降低系统成本，提供系统可靠性，解决海外安装服务成本高的痛点，并支持虚拟电站（VPP）模式。\
        4、新能源汽车充电桩产品。主要包括：充电模块、一体式直流快速充电桩、分体式直流快速充电桩、壁挂式直流快速充电桩、交流充电桩、监控系统等。\
        5、结论：作为中国不间断电源产业领航者、行业领先的安全用电环境一体化解决方案提供商，研发生产的数据中心关键基础设施产品、新能源光伏发电系统产品、储能系统产品、新能源汽车充电产品技术处于行业领先水平，一体化解决方案广泛应用于各行业领域。"
    },
    {
        "query": "公司主业发展前景怎么样？",
        "answer": "\
        1、公司主导数据中心建设“新能源+”方案。2022年 2 月，四部委已同意启动涵盖 8 个国家算力枢纽节点、10 个国家数据中心集群的建设，这将较大影响中国数据中心市场的区域布局，带动一线周边及中西部城市市场规模的提升。数据中心建设对于设计、PUE、网络运维等方面都有了更严格要求，数据中心上下游包括网络设备、供配电设备、制冷设备、ICT 设备、数据服务等市场都面临着新的发展机会与技术挑战。未来，数据中心建设“新能源+”方案，高效化、智能化、绿色化、集成化产品将成为数据中心建设发展的主流方向。\
        2、“新能源+储能”方案提升能源利用率。储能技术是构建新型电力系统战略、推动能源革命，实现碳中和目标的重要技术支柱。在发电及输配电侧，储能是解决发电消纳、增强电网稳定性、提高配电系统利用效率的合理解决方案。而面对分时电价差距扩大及高耗能电价上涨政策，工商业及户用储能系统即能有效解决用户对于用电经济性的客观述求。“新能源+储能”方案成为提升能源利用率及使用经济性的优化方案。\
        3、新能源车及充电业务方兴未艾。到“十四五”末，我国将形成适度超前、布局均衡、智能高效的充电基础设施体系，能够满足超过 2000 万辆电动汽车充电需求。新能源车正逐步起量，大功率快充市场的需求更趋明显，充电桩行业正处于高速发展中，特别是以“储充模式”、“光储充模式”等为代表的新集成化的电力解决方案将成为未来新能源汽车充电行业发展方向。\
        4、结论：AI技术加速渗透、东数西算、光储能源替代战略，以及新能源车加速渗透，都会带来深刻的产业变革，公司各条业务均处于时代风口上，发展前景广阔。"
    },
    {
        "query": "公司的商业模式是什么？",
        "answer": "\
        1、研发模式。公司核心产品主要依赖自主知识产权进行产品开发、更新迭代。公司是国家高新技术企业、国家认定企业技术中心、国家技术创新示范企业。\
        2、采购模式。搭建了采购供应链管理平台，保持“以销定产、适当库存”的管理模式。\
        3、生产模式。公司根据“以销定产”为主、“库存式生产”为辅的生产模式。\
        4、销售模式。公司采取以“直销+渠道”相结合的销售模式。司数据中心国内业务以自有品牌为主，海外业务以 ODM 为主；新能源光伏业务主要以品牌直销为主，储能业务以 ODM+品牌为主。\
        5、结论：公司坚持“市场导向+技术驱动”的发展思路，以“客户为本，匠心为质”的市场品牌定位，经营模式先进。"
    },
    {
        "query": "公司有什么核心竞争力？",
        "answer": "\
        1、技术创新优势。公司先后被评为国家级高新技术企业、国家技术创新示范企业、广东省诚信示范企业，依托公司的技术中心组建的广东省太阳能光伏发电企业工程技术研究中心、深圳市企业工程实验室等研发机构，公司的技术中心被国家发改委等五部门认定为国家级企业技术中心。公司累计获得国际国内专利授权 337 件，并累计参与 95 项国家和行业技术标准起草或修订。公司精密空调专用焓差实验室已通过中国合格评定国家认可委员会（CNAS）的审查，并取得国家压缩机制冷设备质量监督检验中心的评定合格证书，三大系列精密空调产品已取得节能认证。\
        2、营销网络优势。公司采用“大渠道+大行业+大客户+大项目”的销售模式，依托遍布全球的客户网，持续强化核心渠道建设，支持有实力的客户做大做强，与科士达共同成长壮大。截至2022年，公司已建立 18 家海外分支机构及分子公司，并根据海外目标市场筹划新增分支机构，为海外业务的持续发展提供重要保障。\
        3、供应链优势。公司三大核心产品包括数据中心关键基础设施产品、新能源光伏及储能系统产品和新能源汽车充电桩。公司供应链平台基于 ISO 质量和环境管理体系，依托 CRM 客户管理系统、ERP 系统、MES 系统，全面导入卓越绩效管理，整个供应链平台实现资源共享；发挥原材料集中采购优势，快速响应，确保产品质量。\
        4、品牌优势。品牌知名度和美誉度辐射全球众多国家和地区。科士达品牌（“科士达 KSTAR” 、“KSTAR”）的影响力不断提升。报告期间，公司荣获 2022 深圳企业 500 强榜单、2022 中国能源企业（集团）500 强榜单、新一代信息技术创新产品奖、新一代信息技术创新企业、用户满意品牌奖、技术创新奖、长三角枢纽数字新基建优秀案例、2022 年度长三角枢纽低碳技术应用创新奖、2022 年度创新解决方案奖、ODCC 优秀合作伙伴奖、云计算中心科技奖卓越奖，同时，科士达品牌荣获：2022 年度中国充电设施行业十大影响力品牌、电源系统新能源系统竞争力十强品牌、影响力光伏逆变器品牌、2022 中国十大智能安全充电桩品牌、影响力光储融合解决方案企业、2022 年度最佳系统集成解决方案供应商奖。\
        5、结论：始终坚持行业深耕，建立了行业领先的以市场需求为导向的营销网络平台、产品研发平台及智能化供应链生产管理平台。在全球化进程中着力开拓布局海外市场，推进全球化公司品牌形象建设，构筑完善的经营管理体系和自主知识产权体系，形成企业可持续发展的核心竞争力。"
    },
    {
        "query": "营收大增的原因是什么？",
        "answer": "\
        1、2022 年公司新能源业务市场需求旺盛，光储业务取得较大突破，订单和出货量大幅增加，以致公司整体业绩增速较快。公司财务费用为-2,253.57 万元，同比减少 1066.19%，主要原因是本期受美元汇率变动影响汇兑收益增加所致；\
        2、光储产品销售量、生产量、库存量较上年同期分别增长 515.43%、529.89%、356.48%，主要系公司新能源业务市场需求旺盛，公司凭借国内外渠道优势，光储业务的订单和出货量快速增加所致。\
        3、充电桩产品销售量、生产量较上年同期分别增长 73.97%、105.33%，主要系国内充电桩建设增量提速，订单量加大，销售量及生产量有所增加。\
        4、结论：国家数据中心建设、光储超常规发展、新能源车及充电设施持续渗透给公司带来重大机遇，且这种发展机遇可持续。"
    },
    {
        "query": "公司未来发展计划是什么？",
        "answer": "\
        1、数据中心：公司将加大对大功率高性能模块化 UPS、新型高效 5G 电源、边缘计算 IDU 和 IDM、预置化数据中心集装箱等产品研发升级，并积极布局和拓宽锂电产品在数据中心的应用，加快光伏、储能与数据中心的系统融合。\
        2、新能源光储。公司将整合数据中心、光伏、储能以及充电桩等多能源类型的智能微网模块化方案，“数据中心+备电系统”、“光伏+储能”项目、“光储充”一体化解决方案等仍是未来业务发展的重点方向。\
        3、充电业务：推出更加稳定、多元化、防护性高、更高性价比的具有市场竞争优势的充电桩产品；加大对大功率充电桩技术的研发，满足市场快充需求；利用公司光伏及储能技术优势，推出多种模式充换电产品；加快开发和认证满足欧标，Chademo 以及北美标准的充电桩产品，为公司全面布局海外充电桩市场奠定基础。\
        4、结论：公司依旧立足当前主业，持续推进国内业务发展，积极开拓国际市场，未来将形成国内国际齐头并进的发展格局。"

    },
    {
        "query": "公司和投资者的关系怎么样？",
        "answer": "\
        1、2022年以来，公司通过线上会议、现场、媒体公开日接待公募、私募、保险、QFII、证券、银行资管等诸多机构投资者调研。\
        2、公司通过深交所互动易平台http://irm.cninfo.com.cn/ircs/search?keyword=002518和投资者保持沟通。\
        3、公司通过官网http://www.ksdups.com.cn/与广大用户和投资者保持沟通。公司也通过“科士达”微信公众号向广大投资者传递经营信息。\
        4、结论：公司与投资者的关系融洽，通过互联网与投资者保持了紧密沟通。"

    },
    {
        "query": "公司市场关注度如何？",
        "answer": "\
        1、2023年以来机构发布的研究报告有21篇，覆盖研究机构较多。\
        2、截至2023年7月14日，公司股东人数7.3万户，人均持股7741股，筹码相对分散。\
        3、截至2023年1季度，有41家基金持有3271万股，比上一季度减少5537万股；\
        4、截至2023年7月14日，公司融资余额55377.5万元，融券余额1873万元。\
        5、结论：公司A股市场关注度相对比较高，属于成长赛道的热门公司。"
    },
    {
        "query": "公司在行业竞争中地位如何？",
        "answer": "\
        1、数据中心UPS。全球龙头企业有伊顿、艾默生、施耐德三强鼎立的格局。中国本土企业中科士达和科华数据领先行业。2022年科士达数据中心相关产品销售189万台，处于行业领先地位。\
        2、光储产品。阳光电源是全球光伏逆变器龙头，固德威、锦浪科技、德业股份等上市公司紧随其后，科士达产销量规模属于第三梯队。\
        3、充电业务：充电模块为充电桩的“心脏”，行业集中度高。2021 年国内市占率前 5 厂商依次为英飞源、特来电、永联科技、英可瑞、中兴通讯，CR5 达 72.0%，快充趋势下，充电模块具备更高的技术壁垒，竞争门槛也因此提升。盛弘股份、科士达、中恒电气、通合科技、奥特迅、许继电气、国电南瑞、动力源、欧陆通等公司也处于竞争中的优势地位。中游充电桩制造行业市场竞争较为激烈，目前国内充电桩制造领域供应商数量已超过 300 家。运营行业马太效应显著，整体呈现强者恒强局面，2023 年 4 月，公共充电桩运营商 CR5 约为 69%。我们认为头部企业将受益于行业增长持续景气。国电南瑞、科士达、盛弘股份、炬华股份、道通科技、绿能慧充、特锐德、和顺电气、科陆电子、易事特、万马股份、中恒电气、奥特迅、平高电气、众业达。科士达处于行业竞争领先地位。\
        4、结论：公司数据中心模块化UPS、5G电源等产品处于行业领先地位。光储逆变器产品处于行业第三梯队。充电模块和充电桩整体上处于行业竞争第一梯队。企业整体实力较强。"
    },
    {
        "query": "公司产品被替代的风险多大？",
        "answer": "\
        1、产品和技术处于国家引导支持阶段。国家层面加强新能源的顶层设计和规划引导，大力支持光伏发电、新型储能等产业发展。政府颁布的一系列支持文件为促进新型储能和新型电力系统发展、加快构建新能源+新型储能上下游一体化协同发展新格局、推动经济社会高质量发展具有重要意义。\
        2、全球光伏产业正处于“风口”，核心部件光伏逆变器产业已呈现出稳定的发展趋势。根据 CPIA 数据，2022-2031 年，全球光伏并网装机容量将以年均 8%的速度增长。光伏逆变器是太阳能光伏发电系统的心脏，它将光伏发电系统产生的直流电通过电力电子变换技术转换为生活所需的交流电，是光伏电站最重要的核心部件之一。光伏逆变器的行业发展情况与全球光伏产业的发展趋势一致，近年来保持较快增长。\
        3、新型储能不断发展壮大，锂离子电池储能仍占主导地位。新型储能不但可以提升电力系统的调节能力，还可以保障电力系统的安全运行。在我国已投产的新型储能装机中，锂离子电池储能仍占主导地位，占比约 94.5%。2022 年，全球储能锂电池总体出货量为 159.3GWh，同比增长 140.3%。其中，中国储能锂电池全年出货量达到 130GWh，占全球出货量的 81.6%，成为全球储能锂电池出货量快速增长的驱动因素。\
        4、总结：公司主导产品属于全球碳中和进程中必不可少的畅销公共品，行业领先企业都将充分分享全球巨大需求的蛋糕。公司产品被替代的可行性不大。"
    },
    {
        "query": "公司技术被替代的风险多大？",
        "answer": "\
        1、数据中心产品技术门槛高。数据中心建设对于设计、PUE、网络运维等方面都有了更严格要求，数据中心上下游包括网络设备、供配电设备、制冷设备、ICT 设备、数据服务等市场都面临着新的发展机会与技术挑战。云计算、以 ChatGPT 为代表的人工智能应用的快速发展，已经成为驱动新一轮云计算基础设施投资景气周期开启的重要力量亦加速推动数据中心等算力基础设施建设需求。针对行业数据中心建设的特殊需求，公司在标准化、模块化的数据中心产品基础上，结合集成机柜系统、密闭冷通道系统、供配电系统、制冷系统、监控系统，通过高集成智能化设计为用户提供一站式数据中心解决方案，主要包括微型数据中心解决方案（IDU）、小微型数据中心解决方案（IDM）、大中型数据中心解决方案（IDR）、一体化户外柜（IDU）以及集装箱预制化数据中心（IDB）。\
        2、光储技术受欢迎。户用储能一体机方案集合了公司在电力电子、储能领域的优势，调试安装简单，降低系统成本，提供系统可靠性，解决海外安装服务成本高的痛点，并支持虚拟电站（VPP）模式，已取得英国、德国、意大利、法国、荷兰，比利时，西班牙，澳大利亚等目标市场国家的认证，更多目标区域国家产品认证正在逐步完善中。公司加大技术研发投入，在更高系统效率、更低系统成本、高安全可靠性、光储融合、主动支撑电网等方面进行更加积极的探索和研究，并在工商业储能系统、户用储能系统、光储充系统、调峰调频系统、箱逆变一体化集成及 1500V 大功率逆变器产品等细分市场推出更具竞争力的产品和解决方案。\
        3、充电模块技术安全为保障。公司新能源汽车充电桩产品具有模块化设计、高智能化、高利用率、高防护性、高安全性、高适应性等优势，搭载智能充电系统、配电系统、储能系统、监控系统、安防系统、运维管理系统形成一体化解决方案，能够满足各类应用场景使用，同时可根据客户的需求提供定制化的解决方案服务。\
        4、结论：公司在几十年的实践中已经沉淀了先进技术，并对各产品方向进行了技术创新。在当前竞争环境下，这些技术水平处于行业主流发展方向，被替代的风险较小。"
    },
    {
        "query": "公司财务风险多大？",
        "answer": "\
        1、盈利能力分析：公司2010年上市以来，净资产收益率年均13.84%，且13年中有9年净资产收益率高于10%。 2022年公司净资产收益率上升到19.94%，为上市以来新高。2010年以来公司总资产报酬率年均9.16%，2022年上升到14.16%的历史较好水平。上市以来公司平均毛利率水平为32%，净利率水平为12%。上述盈利能力都高于以数据中心产品为核心的同类上市公司。\
        2、运营能力分析。公司2010年上市以来，存货周转天数平均为82.34天，存货周转率平均为4.59次，应收账款周转天数为127.95天，应收帐款周转率为2.99次，总资产周转率为0.67次，公司运营能力优秀，在数据中心、光储、充电桩等主业的上市公司中处于领先水平。\
        3、成长能力分析：2010年上市以来，公司营业总收入、归属母公司净利润年均同比分别增长19.34%、23.30%。其中过去13年，公司净利润有9年同比增长都超过10%，表现出非常优秀的成长能力。\
        4、资本结构与偿债能力分析。2010年上市以来，公司年均资产负债率保持在30.22%的水平，近年来负债率略有上行但整体处于较低水平，2023年非公开发行后公司负债率水平有望继续下降。  上市以来公司流动比率、 速动比率平均水平分别为2.92、2.52，显示公司资产流动水平、变现能力非常强。\
        5、现金流分析：2010年上市以来，公司销售商品提供劳务收到的现金／营业收入(%) 平均水平为94.10%，最近3年现金收入比全部高于100%，显示公司销售回款情况良好。上市以来公司经营活动产生的现金流量净额/净利润(%) 平均水平为125.97%，显示公司产品服务行业地位高，产销两旺，创造现金流的能力很强。\
        6、结论：公司财务结构良好，盈利能力、成长能力优秀，运营能力卓越，现金流水平强大。财务风险不大。"
    },
    {
        "query": "公司二级市场技术走势如何？",
        "answer": "\
        1、涨跌幅分析：公司股票自2010年在深交所上市以来，历史最大涨幅超过4400%，是同期深证指涨幅的100倍以上。也跑赢同期行业指数涨幅50倍以上。属于典型的牛股。\
        2、趋势分析：公司股价以前复权计算，自2012年底见底以来，到2023年7月，目前正处于大三浪的上升趋势。其中2018年底为大三浪上涨的起点，当前股价大概率处于三浪（4））的中期调整阶段，后面尚有三浪（5）的上涨趋势。自2012年上涨以来，一浪上涨30个月，二浪调整41个月，三浪上涨至今57个月，大概率三浪主升浪会延长并创出历史新高。\
        3、空间分析：上涨空间，2012-2015年一浪上涨24元，三浪涨幅已经达到一浪涨幅*2.618倍。按照三浪延伸，主升浪涨幅有可能超过一浪涨幅的3倍以上。调整空间，我们以2018年10月上涨起点到2023年1月高点作黄金分割，针对三浪调整幅度0.5-0.618倍对应34-41元区间，该位置也是三浪（1）高点区域，可能是针对主升浪调整的正常水平。\
        4、支撑与阻力分析：连接2012年12月低点和2018年10月低点做支撑连线，并向上移动作平行线，以2015年6月高点做延伸，截至2023年7月该趋势线位于30月移动均线位置，该位置形成了支撑。同时我们以2018年10月低点和2022年4月低点连线，向上移动作平行线，以2021年8月-11月高点做延伸，截至2023年7月该趋势线位于20月移动均线位置，该位置形成了支撑。\
        5、结论：科士达二级市场股价主升浪趋势在延续，当前处于针对主升浪的调整趋势，股价非常接近较强支撑位。中期趋势以看涨为主。"
    },
    {
        "query": "市场热度怎么样？",
        "answer": "\
        1、从资金面看，今天主力资金净流出4100.51万元，两市排名5061/5248，交投明显不活跃，近5日内该股共净流入2370.05万元，略有增加，当增量不明显。\
        2、从市场情绪面看，今天dde散户数量为16.96。说明散户数量占比大，主力介入低。该股在两市中散户数量排名名次为1189该股最后一次龙虎榜在20230426和20230327。\
        3、从消息面看，您可以关注到有以下内容：\
         .科士达：融资净买入414.96万元，融资余额5.54亿元（07-13）\
         .科士达07月13日被深股通减持11.4万股 07-14\
         .科士达：融资净买入475.52万元，融资余额5.5亿元（07-12）  07-13\
        4、结论：科士达股票当前市场热点排名全市场前1/3的水平。"
    }
]
KB_ROOT_PATH = "/Users/chaogaofeng/workspace/src/github.com/hwchase17/aifin/knowledge_base"
if __name__ == "__main__":
    # 初始化消息
    args = None
    args = parser.parse_args()
    args_dict = vars(args)
    shared.loaderCheckPoint = LoaderCheckPoint(args_dict)
    llm_model_ins = shared.loaderLLM()

    llm = OpenAI(temperature=0)
    embeddings = HuggingFaceEmbeddings(
        model_name='/Users/chaogaofeng/workspace/src/github.com/hwchase17/aifin/huggingface/GanymedeNil/text2vec-large-chinese',
        model_kwargs={'device': 'cpu'})

    example_selector = SemanticSimilarityExampleSelector.from_examples(
        # This is the list of examples available to select from.
        PROMPT_TEMPLATE_EXAMPLES,
        # This is the embedding class used to produce embeddings which are used to measure semantic similarity.
        embeddings,
        # This is the VectorStore class that is used to store the embeddings and do a similarity search over.
        Chroma,
        # This is the number of examples to produce.
        k=1
    )
    example_prompt = PromptTemplate(
        input_variables=["query", "answer"],
        template=PROMPT_TEMPLATE_EXAMPLE
    )
    few_shot_prompt_template = FewShotPromptTemplate(
        example_selector=example_selector,
        # examples = examples,
        example_prompt=example_prompt,
        prefix=PROMPT_TEMPLATE_EXAMPLE_PREFIX,
        suffix=PROMPT_TEMPLATE_EXAMPLE_SUFFIX,
        input_variables=["question", "context"],
        example_separator="\n\n"
    )

    code = "002594"
    query = "表现"
    # s = time.perf_counter()
    # print(f"知识库加载 ...")
    # vs_path = os.path.join(KB_ROOT_PATH, "aifin_" + code, "vector_store")
    # vs = FAISS.load_local(vs_path, embeddings)
    # vs.chunk_size = 250
    # vs.chunk_conent = True
    # vs.score_threshold = 1000
    # elapsed = time.perf_counter() - s
    # print(f"知识库加载 结束{elapsed:0.2f} seconds")
    # related_docs = vs.similarity_search_with_score(query, k=1)
    # print(f"知识库搜索 结束{elapsed:0.2f} seconds len:{len(related_docs)}")
    # context = "\n".join([doc[0].page_content for doc in related_docs])
    # print("source={}", context)
    # print("score={}", [doc[1] for doc in related_docs])
    # retriever = vs.as_retriever(search_type="similarity_score_threshold",
    #                             search_kwargs={"k": 5, "score_threshold": 0.1})
    # qa = RetrievalQA.from_chain_type(
    #     llm=llm_model_ins, chain_type="stuff", retriever=retriever, return_source_documents=True)
    # result = qa({"query": query})
    # print("faiss ========", result['query'])
    # print("faiss ========", result['result'])
    # print("faiss ========", [doc.page_content for doc in result['source_documents']])

    s = time.perf_counter()
    print(f"知识库加载 ...")
    vs = Milvus(collection_name="aifin_" + code, connection_args={"host": '8.217.52.63', "port": 19530}, embedding_function=embeddings)
    elapsed = time.perf_counter() - s
    print(f"知识库加载 结束{elapsed:0.2f} seconds")
    related_docs = vs.similarity_search_with_score(query, k=5, expr='date < "2023-01-02"')
    print(f"知识库搜索 结束{elapsed:0.2f} seconds len:{len(related_docs)}")
    context = "\n==".join([doc[0].page_content for doc in related_docs])
    print("source={}", context)
    print("score={}", [doc[1] for doc in related_docs])
    retriever = vs.as_retriever(search_type="similarity", search_kwargs={"k": 5})
    qa = RetrievalQA.from_chain_type(
        llm=llm_model_ins, chain_type="stuff", retriever=retriever, return_source_documents=True)
    result = qa({"query": query})
    print("milvus ========", result['query'])
    print("milvus ========", result['result'])
    print("milvus ========", [doc.page_content for doc in result['source_documents']])
