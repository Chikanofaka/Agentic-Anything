# Thirty portable PRD operators

The following instructions are portable writing rules. They are **not** prescriptions to implement the original projects. Each operator is triggered by a pattern in the new Need and may become N/A with an explicit rationale.

## PR00 — Document positioning and editorial contract

**Trigger examples:** 定位|文档用途|输出对象|管理层|供应商|对外口径|使用说明|AGENDA|目录

**Generative rule:** 先定义文档的决策用户、用途、决策权、约束与版本；区分内部执行视图、外部采购视图及尚未确认的信息。

**Questions to ask / variables:** 目标决策人、需作出的决定、文档口径、依据材料、假设状态

**Artifact to generate:** 文档控制卡：版本、依据、受众、决策、边界、术语

**Quality gate:** All claims are labeled as fact, stakeholder assertion, hypothesis, estimate, or decision. Include at least one negative or counterfactual check. In a new domain, replace original names, vendors, amounts, timeframes and regulations by substantiated case inputs.

**Meta-paragraph function:** “Given [user/Need and context], identify [目标决策人、需作出的决定、文档口径、依据材料、假设状态]; apply [先定义文档的决策用户、用途、决策权、约束与版本；区分内部执行视图、外部采购视图及尚未确认的信息。]; produce [文档控制卡：版本、依据、受众、决策、边界、术语]; verify via [observable evidence / human gate] and mark unknowns TO_VALIDATE.”

## PR01 — Demand evidence and primary pain

**Trigger examples:** 为什么|痛点|问题描述|瓶颈|挑战|现状|为什么现在|问题|需求

**Generative rule:** 把情境描述转成可验证的因果需求：谁在什么流程下遭遇何种阻碍、目前如何替代、发生频率、后果和佐证；不以技术方案取代问题定义。

**Questions to ask / variables:** 用户、触发场景、现在的做法、频率、损失、来源/反例

**Artifact to generate:** Need Statement + Evidence Ledger + 可证伪假设

**Quality gate:** All claims are labeled as fact, stakeholder assertion, hypothesis, estimate, or decision. Include at least one negative or counterfactual check. In a new domain, replace original names, vendors, amounts, timeframes and regulations by substantiated case inputs.

**Meta-paragraph function:** “Given [user/Need and context], identify [用户、触发场景、现在的做法、频率、损失、来源/反例]; apply [把情境描述转成可验证的因果需求：谁在什么流程下遭遇何种阻碍、目前如何替代、发生频率、后果和佐证；不以技术方案取代问题定义。]; produce [Need Statement + Evidence Ledger + 可证伪假设]; verify via [observable evidence / human gate] and mark unknowns TO_VALIDATE.”

## PR02 — Strategic positioning and goals

**Trigger examples:** 战略|定位|方向|愿景|目的|赋能|价值主张|模式|生态

**Generative rule:** 从上位战略明确竞争目标及非目标；将愿景拆为业务可达成状态，明确这是工具、能力系统还是基础设施，以及应保留的组织控制权。

**Questions to ask / variables:** 战略目标、角色、优势、边界、业务因果

**Artifact to generate:** 定位声明 + 战略一致性表

**Quality gate:** All claims are labeled as fact, stakeholder assertion, hypothesis, estimate, or decision. Include at least one negative or counterfactual check. In a new domain, replace original names, vendors, amounts, timeframes and regulations by substantiated case inputs.

**Meta-paragraph function:** “Given [user/Need and context], identify [战略目标、角色、优势、边界、业务因果]; apply [从上位战略明确竞争目标及非目标；将愿景拆为业务可达成状态，明确这是工具、能力系统还是基础设施，以及应保留的组织控制权。]; produce [定位声明 + 战略一致性表]; verify via [observable evidence / human gate] and mark unknowns TO_VALIDATE.”

## PR03 — Scope and staged delivery

**Trigger examples:** 一期|二期|阶段|边界|范围|先做|后做|MVP|最小闭环|迭代|分期|优先试点

**Generative rule:** 将完整终局分解为最小可验证价值链；按用户价值、依赖、风险、周期安排本期/下期/排除项，明确为何这样切割及扩展条件。

**Questions to ask / variables:** 终局能力、价值关键路径、约束、待验证假设

**Artifact to generate:** 范围矩阵+阶段目标+明确非目标

**Quality gate:** All claims are labeled as fact, stakeholder assertion, hypothesis, estimate, or decision. Include at least one negative or counterfactual check. In a new domain, replace original names, vendors, amounts, timeframes and regulations by substantiated case inputs.

**Meta-paragraph function:** “Given [user/Need and context], identify [终局能力、价值关键路径、约束、待验证假设]; apply [将完整终局分解为最小可验证价值链；按用户价值、依赖、风险、周期安排本期/下期/排除项，明确为何这样切割及扩展条件。]; produce [范围矩阵+阶段目标+明确非目标]; verify via [observable evidence / human gate] and mark unknowns TO_VALIDATE.”

## PR04 — Stakeholder and role system

**Trigger examples:** 角色|部门|人员|用户|账号|权限箱|供应商角色|负责|负责人|基金经理

**Generative rule:** 从具体组织名称抽象出角色/责任/权限/对象；定义谁使用、谁批准、谁拥有数据、谁支持、谁担责，并建立角色到功能与数据的映射。

**Questions to ask / variables:** 角色、人数/规模、核心任务、操作、责任人

**Artifact to generate:** Persona JTBD + RACI + 角色功能矩阵

**Quality gate:** All claims are labeled as fact, stakeholder assertion, hypothesis, estimate, or decision. Include at least one negative or counterfactual check. In a new domain, replace original names, vendors, amounts, timeframes and regulations by substantiated case inputs.

**Meta-paragraph function:** “Given [user/Need and context], identify [角色、人数/规模、核心任务、操作、责任人]; apply [从具体组织名称抽象出角色/责任/权限/对象；定义谁使用、谁批准、谁拥有数据、谁支持、谁担责，并建立角色到功能与数据的映射。]; produce [Persona JTBD + RACI + 角色功能矩阵]; verify via [observable evidence / human gate] and mark unknowns TO_VALIDATE.”

## PR05 — Security classification and least privilege

**Trigger examples:** 安全|机密|保密|隔离|敏感|权限|审计|授权|加密|客户信息|外泄|风控|水印

**Generative rule:** 先列数据敏感度和资产权属，再用身份×资源×动作×场景确定默认拒绝权限；补充审批、日志、保留期、撤销、跨边界传输的规则与负面测试。

**Questions to ask / variables:** 敏感级别、主体、资源、动作、政策、审计

**Artifact to generate:** 分级分权矩阵+威胁模型+授权测试

**Quality gate:** All claims are labeled as fact, stakeholder assertion, hypothesis, estimate, or decision. Include at least one negative or counterfactual check. In a new domain, replace original names, vendors, amounts, timeframes and regulations by substantiated case inputs.

**Meta-paragraph function:** “Given [user/Need and context], identify [敏感级别、主体、资源、动作、政策、审计]; apply [先列数据敏感度和资产权属，再用身份×资源×动作×场景确定默认拒绝权限；补充审批、日志、保留期、撤销、跨边界传输的规则与负面测试。]; produce [分级分权矩阵+威胁模型+授权测试]; verify via [observable evidence / human gate] and mark unknowns TO_VALIDATE.”

## PR06 — Data inventory, provenance, refresh

**Trigger examples:** 底层|知识库|数据治理|资料|数据库|文件夹|文件|来源|字段|清洗|上传|更新|入库|存量|RAG

**Generative rule:** 将原始材料按来源、业务用途、粒度、质量、敏感度、授权、更新频率、追溯能力归类；先形成数据目录，再定义ETL/RAG/检索路径和纠错机制。

**Questions to ask / variables:** 数据源、格式、结构、权属、频率、可用性、缺失项

**Artifact to generate:** 数据资产目录 + 流转图 + 数据契约

**Quality gate:** All claims are labeled as fact, stakeholder assertion, hypothesis, estimate, or decision. Include at least one negative or counterfactual check. In a new domain, replace original names, vendors, amounts, timeframes and regulations by substantiated case inputs.

**Meta-paragraph function:** “Given [user/Need and context], identify [数据源、格式、结构、权属、频率、可用性、缺失项]; apply [将原始材料按来源、业务用途、粒度、质量、敏感度、授权、更新频率、追溯能力归类；先形成数据目录，再定义ETL/RAG/检索路径和纠错机制。]; produce [数据资产目录 + 流转图 + 数据契约]; verify via [observable evidence / human gate] and mark unknowns TO_VALIDATE.”

## PR07 — Functional inventory and scenarios

**Trigger examples:** 功能|模块|筛选|分析|看板|报告|模板|问答|研究|推荐|查询|推送|支持

**Generative rule:** 每项功能按照触发、输入、执行规则、界面状态、输出、异常、验收七元组定义；以用户场景为分组，不用抽象技术名替代功能。

**Questions to ask / variables:** 用户故事、优先级、输入/动作/输出、边界

**Artifact to generate:** 功能矩阵 + 用户故事 + Given/When/Then

**Quality gate:** All claims are labeled as fact, stakeholder assertion, hypothesis, estimate, or decision. Include at least one negative or counterfactual check. In a new domain, replace original names, vendors, amounts, timeframes and regulations by substantiated case inputs.

**Meta-paragraph function:** “Given [user/Need and context], identify [用户故事、优先级、输入/动作/输出、边界]; apply [每项功能按照触发、输入、执行规则、界面状态、输出、异常、验收七元组定义；以用户场景为分组，不用抽象技术名替代功能。]; produce [功能矩阵 + 用户故事 + Given/When/Then]; verify via [observable evidence / human gate] and mark unknowns TO_VALIDATE.”

## PR08 — Interaction and onboarding design

**Trigger examples:** 交互|界面|Web|APP|UI|前端|聊天|语音|Canvas|画布|引用|截图|Mockup|页面|原型

**Generative rule:** 把需求翻译为屏幕状态与行动路径：首次进入、任务选择、加载、成功、错误、恢复、撤销、历史、可访问性；至少展示一条真实闭环并标明模拟部分。

**Questions to ask / variables:** 设备、入口、控件、场景、任务状态、错误、输出动作

**Artifact to generate:** 信息架构+关键用户旅程+页面状态清单

**Quality gate:** All claims are labeled as fact, stakeholder assertion, hypothesis, estimate, or decision. Include at least one negative or counterfactual check. In a new domain, replace original names, vendors, amounts, timeframes and regulations by substantiated case inputs.

**Meta-paragraph function:** “Given [user/Need and context], identify [设备、入口、控件、场景、任务状态、错误、输出动作]; apply [把需求翻译为屏幕状态与行动路径：首次进入、任务选择、加载、成功、错误、恢复、撤销、历史、可访问性；至少展示一条真实闭环并标明模拟部分。]; produce [信息架构+关键用户旅程+页面状态清单]; verify via [observable evidence / human gate] and mark unknowns TO_VALIDATE.”

## PR09 — Three-layer architecture and boundaries

**Trigger examples:** 三层|架构图|技术架构|底层|中间层|应用层|前后端|Client|Agent|API|部署|本地化|逻辑层

**Generative rule:** 定义数据/逻辑/应用逻辑分层并明确每层责任、输入输出契约和安全信任边界；区分方案假设与已验证实现；对关键依赖给出替代路径。

**Questions to ask / variables:** 数据接口、计算单元、UI渠道、边界、部署约束

**Artifact to generate:** 分层架构+模块边界+连接契约+部署方案

**Quality gate:** All claims are labeled as fact, stakeholder assertion, hypothesis, estimate, or decision. Include at least one negative or counterfactual check. In a new domain, replace original names, vendors, amounts, timeframes and regulations by substantiated case inputs.

**Meta-paragraph function:** “Given [user/Need and context], identify [数据接口、计算单元、UI渠道、边界、部署约束]; apply [定义数据/逻辑/应用逻辑分层并明确每层责任、输入输出契约和安全信任边界；区分方案假设与已验证实现；对关键依赖给出替代路径。]; produce [分层架构+模块边界+连接契约+部署方案]; verify via [observable evidence / human gate] and mark unknowns TO_VALIDATE.”

## PR10 — Workflow orchestration, gates and agents

**Trigger examples:** Agent|多智能体|多Agent|红蓝|研究总监|CIO|调度|workflow|CoT|PK|循环|门控|步骤

**Generative rule:** 从领域工作拆出有明确输入输出的节点：路由、工具、复核、反证、人工决策；规定状态转移、失败重试及中间工件，不把复杂角色数量当目标。

**Questions to ask / variables:** 角色节点、状态、接口、证据、退出条件

**Artifact to generate:** 工作流状态机 + 工件流 + 质量门

**Quality gate:** All claims are labeled as fact, stakeholder assertion, hypothesis, estimate, or decision. Include at least one negative or counterfactual check. In a new domain, replace original names, vendors, amounts, timeframes and regulations by substantiated case inputs.

**Meta-paragraph function:** “Given [user/Need and context], identify [角色节点、状态、接口、证据、退出条件]; apply [从领域工作拆出有明确输入输出的节点：路由、工具、复核、反证、人工决策；规定状态转移、失败重试及中间工件，不把复杂角色数量当目标。]; produce [工作流状态机 + 工件流 + 质量门]; verify via [observable evidence / human gate] and mark unknowns TO_VALIDATE.”

## PR11 — Model, vendor and tool integration

**Trigger examples:** 第三方|平台|Wind|Alpha|DeepSeek|GPT|模型|Token|MCP|采购|接口|云|供应商|服务商|认证|比选

**Generative rule:** 区分模型推理、托管Agent任务、数据源、执行工具和嵌入SDK；逐一核对API/授权/费率/频控/限额/兼容性和不可用时的回退。

**Questions to ask / variables:** 供应类型、商业状态、技术协议、数据权限、限额

**Artifact to generate:** 供应商对比矩阵 + 依赖台账 + Preflight

**Quality gate:** All claims are labeled as fact, stakeholder assertion, hypothesis, estimate, or decision. Include at least one negative or counterfactual check. In a new domain, replace original names, vendors, amounts, timeframes and regulations by substantiated case inputs.

**Meta-paragraph function:** “Given [user/Need and context], identify [供应类型、商业状态、技术协议、数据权限、限额]; apply [区分模型推理、托管Agent任务、数据源、执行工具和嵌入SDK；逐一核对API/授权/费率/频控/限额/兼容性和不可用时的回退。]; produce [供应商对比矩阵 + 依赖台账 + Preflight]; verify via [observable evidence / human gate] and mark unknowns TO_VALIDATE.”

## PR12 — Memory, versioning and feedback

**Trigger examples:** 记忆|反馈|偏好|历史|刷新|追问|版本|学习|迭代|修正|跟踪

**Generative rule:** 说明什么需要记、如何更新/纠错、保存多久、哪些不能持久化；用户反馈如何影响后续工件与决策，并保留版本差异与撤销机制。

**Questions to ask / variables:** 会话事实、长期偏好、业务知识、更新触发、删除权

**Artifact to generate:** 记忆模型 + 版本追踪 + Feedback Loop

**Quality gate:** All claims are labeled as fact, stakeholder assertion, hypothesis, estimate, or decision. Include at least one negative or counterfactual check. In a new domain, replace original names, vendors, amounts, timeframes and regulations by substantiated case inputs.

**Meta-paragraph function:** “Given [user/Need and context], identify [会话事实、长期偏好、业务知识、更新触发、删除权]; apply [说明什么需要记、如何更新/纠错、保存多久、哪些不能持久化；用户反馈如何影响后续工件与决策，并保留版本差异与撤销机制。]; produce [记忆模型 + 版本追踪 + Feedback Loop]; verify via [observable evidence / human gate] and mark unknowns TO_VALIDATE.”

## PR13 — Cost, resource and commercial model

**Trigger examples:** 费用|成本|薪酬|报价|估价|预算|定价|人民币|美元|人天|采购费|算力|capex|opex|利率

**Generative rule:** 将预算拆为人天、模型使用、数据/工具采购、基础设施、合规安全、测试运维和预备金；所有数字标币种/周期/来源/报价状态，情景测算不能伪装真实成本。

**Questions to ask / variables:** 工作包、人天/单价、tokens、供应费用、时间、区间

**Artifact to generate:** 左成本右价值双栏+低基高情景+报价表

**Quality gate:** All claims are labeled as fact, stakeholder assertion, hypothesis, estimate, or decision. Include at least one negative or counterfactual check. In a new domain, replace original names, vendors, amounts, timeframes and regulations by substantiated case inputs.

**Meta-paragraph function:** “Given [user/Need and context], identify [工作包、人天/单价、tokens、供应费用、时间、区间]; apply [将预算拆为人天、模型使用、数据/工具采购、基础设施、合规安全、测试运维和预备金；所有数字标币种/周期/来源/报价状态，情景测算不能伪装真实成本。]; produce [左成本右价值双栏+低基高情景+报价表]; verify via [observable evidence / human gate] and mark unknowns TO_VALIDATE.”

## PR14 — Business value, metrics and ROI

**Trigger examples:** 效益|价值|成果|节省|提升|效率|转化率|增长|收益|替代|等效|指标|35亿|50%|定量

**Generative rule:** 将业务愿景拆成可测价值假设：现状基线→预期改善→测量频率→归因→反证，区分减少成本、提升吞吐、质量/风险改善与战略期权。

**Questions to ask / variables:** 基线、目标、分母、时间、方法、归因

**Artifact to generate:** 价值树+KPI契约+ROI模型（含不确定性）

**Quality gate:** All claims are labeled as fact, stakeholder assertion, hypothesis, estimate, or decision. Include at least one negative or counterfactual check. In a new domain, replace original names, vendors, amounts, timeframes and regulations by substantiated case inputs.

**Meta-paragraph function:** “Given [user/Need and context], identify [基线、目标、分母、时间、方法、归因]; apply [将业务愿景拆成可测价值假设：现状基线→预期改善→测量频率→归因→反证，区分减少成本、提升吞吐、质量/风险改善与战略期权。]; produce [价值树+KPI契约+ROI模型（含不确定性）]; verify via [observable evidence / human gate] and mark unknowns TO_VALIDATE.”

## PR15 — Acceptance and quality tests

**Trigger examples:** 验收|通过|测试|内测|试跑|评估|准确率|异常|回退|checklist|核对|验证|门槛

**Generative rule:** 每个需求定义客观验收：前置条件、输入数据、执行动作、可观察结果、失败负例、责任人、证据链接；不得以“页面能点”代替业务闭环。

**Questions to ask / variables:** 验收对象、测试数据、阈值、否定路径、签字人

**Artifact to generate:** 验收矩阵+测试用例+失败恢复

**Quality gate:** All claims are labeled as fact, stakeholder assertion, hypothesis, estimate, or decision. Include at least one negative or counterfactual check. In a new domain, replace original names, vendors, amounts, timeframes and regulations by substantiated case inputs.

**Meta-paragraph function:** “Given [user/Need and context], identify [验收对象、测试数据、阈值、否定路径、签字人]; apply [每个需求定义客观验收：前置条件、输入数据、执行动作、可观察结果、失败负例、责任人、证据链接；不得以“页面能点”代替业务闭环。]; produce [验收矩阵+测试用例+失败恢复]; verify via [observable evidence / human gate] and mark unknowns TO_VALIDATE.”

## PR16 — Roadmap, workstreams and dependency matrix

**Trigger examples:** 周|W1|W2|W3|W4|W5|W6|里程碑|日程|甘特|计划|时间|阶段明细|优先级|P1|P2|收口

**Generative rule:** 将需求拆成可归责交付包，再标注前置依赖、负责角色、预计工时、风险缓冲、阶段出口和验收点；以关键路径驱动优先级，避免多个赛道互相挤占。

**Questions to ask / variables:** 工作流、起止周、owner、依赖、风险、交付物

**Artifact to generate:** 六线/多线矩阵+关键路径+版本闸门

**Quality gate:** All claims are labeled as fact, stakeholder assertion, hypothesis, estimate, or decision. Include at least one negative or counterfactual check. In a new domain, replace original names, vendors, amounts, timeframes and regulations by substantiated case inputs.

**Meta-paragraph function:** “Given [user/Need and context], identify [工作流、起止周、owner、依赖、风险、交付物]; apply [将需求拆成可归责交付包，再标注前置依赖、负责角色、预计工时、风险缓冲、阶段出口和验收点；以关键路径驱动优先级，避免多个赛道互相挤占。]; produce [六线/多线矩阵+关键路径+版本闸门]; verify via [observable evidence / human gate] and mark unknowns TO_VALIDATE.”

## PR17 — Governance, decisions and signoff

**Trigger examples:** 决策|审批|拍板|签字|立项|启动|owner|共识|机制|管理层|人力|职责

**Generative rule:** 明确谁有权批准范围、预算、敏感数据接入、验收和发布；记录待决策事项、替代方案、决策期限、变更规则与签字格式。

**Questions to ask / variables:** 决策层级、治理结构、会议节奏、门槛

**Artifact to generate:** 决策台账+RACI+启动签署页

**Quality gate:** All claims are labeled as fact, stakeholder assertion, hypothesis, estimate, or decision. Include at least one negative or counterfactual check. In a new domain, replace original names, vendors, amounts, timeframes and regulations by substantiated case inputs.

**Meta-paragraph function:** “Given [user/Need and context], identify [决策层级、治理结构、会议节奏、门槛]; apply [明确谁有权批准范围、预算、敏感数据接入、验收和发布；记录待决策事项、替代方案、决策期限、变更规则与签字格式。]; produce [决策台账+RACI+启动签署页]; verify via [observable evidence / human gate] and mark unknowns TO_VALIDATE.”

## PR18 — Supplier tender and evaluation

**Trigger examples:** 招标|回标|询价|供应商|选型|报价|外包|资源供应商|竞争方案

**Generative rule:** 统一招标输入和验收口径；供应商必须逐条回应范围、接口、人员、人天、排除项、知识产权、安全、SLA和交付证据；按事先定义的权重评估。

**Questions to ask / variables:** 商业模型、技术标准、报价拆分、评分权重

**Artifact to generate:** 供应商回标模板+对比评分+排除项清单

**Quality gate:** All claims are labeled as fact, stakeholder assertion, hypothesis, estimate, or decision. Include at least one negative or counterfactual check. In a new domain, replace original names, vendors, amounts, timeframes and regulations by substantiated case inputs.

**Meta-paragraph function:** “Given [user/Need and context], identify [商业模型、技术标准、报价拆分、评分权重]; apply [统一招标输入和验收口径；供应商必须逐条回应范围、接口、人员、人天、排除项、知识产权、安全、SLA和交付证据；按事先定义的权重评估。]; produce [供应商回标模板+对比评分+排除项清单]; verify via [observable evidence / human gate] and mark unknowns TO_VALIDATE.”

## PR19 — MVM / Prototype as learning instrument

**Trigger examples:** 原型|demo|演示|mockup|MVM|prototype|游戏|稿|页面|视觉

**Generative rule:** MVM 直接模拟或实现未来产品的核心行为而非隐喻；场景脚本包含问题、操作、预期、错误恢复与用户反馈，且清楚区分真实和模拟。

**Questions to ask / variables:** 价值机制、关键时刻、场景、操作者、反馈

**Artifact to generate:** 可体验样稿脚本+现实标签+Human UAT

**Quality gate:** All claims are labeled as fact, stakeholder assertion, hypothesis, estimate, or decision. Include at least one negative or counterfactual check. In a new domain, replace original names, vendors, amounts, timeframes and regulations by substantiated case inputs.

**Meta-paragraph function:** “Given [user/Need and context], identify [价值机制、关键时刻、场景、操作者、反馈]; apply [MVM 直接模拟或实现未来产品的核心行为而非隐喻；场景脚本包含问题、操作、预期、错误恢复与用户反馈，且清楚区分真实和模拟。]; produce [可体验样稿脚本+现实标签+Human UAT]; verify via [observable evidence / human gate] and mark unknowns TO_VALIDATE.”

## PR20 — Risk, counterfactual and alternatives

**Trigger examples:** 风险|依赖|无法|不能|不确定|回退|障碍|漏洞|问题清单|替代方案|挑战

**Generative rule:** 识别使项目失败的关键假设：技术、安全、商业、采用、数据、流程；给每个假设设反证、最便宜验证、停损点、责任人及回退方案。

**Questions to ask / variables:** 风险概率、影响、触发、反证、恢复

**Artifact to generate:** 风险台账+失败模式分析+No-build对照

**Quality gate:** All claims are labeled as fact, stakeholder assertion, hypothesis, estimate, or decision. Include at least one negative or counterfactual check. In a new domain, replace original names, vendors, amounts, timeframes and regulations by substantiated case inputs.

**Meta-paragraph function:** “Given [user/Need and context], identify [风险概率、影响、触发、反证、恢复]; apply [识别使项目失败的关键假设：技术、安全、商业、采用、数据、流程；给每个假设设反证、最便宜验证、停损点、责任人及回退方案。]; produce [风险台账+失败模式分析+No-build对照]; verify via [observable evidence / human gate] and mark unknowns TO_VALIDATE.”

## PR21 — Research discipline, evidence and red/blue review

**Trigger examples:** 假设|证据|来源|可信|置信度|红军|蓝军|竞争|交叉验证|对抗|辩论

**Generative rule:** 在关键结论前锁定可证伪假设；要求正反证据、版本化来源、独立复核和人类裁定，避免领域智能体以流畅文本冒充可靠判断。

**Questions to ask / variables:** 命题、前提、证据等级、反证、裁定

**Artifact to generate:** 证据链+假设门+对抗验证和裁决

**Quality gate:** All claims are labeled as fact, stakeholder assertion, hypothesis, estimate, or decision. Include at least one negative or counterfactual check. In a new domain, replace original names, vendors, amounts, timeframes and regulations by substantiated case inputs.

**Meta-paragraph function:** “Given [user/Need and context], identify [命题、前提、证据等级、反证、裁定]; apply [在关键结论前锁定可证伪假设；要求正反证据、版本化来源、独立复核和人类裁定，避免领域智能体以流畅文本冒充可靠判断。]; produce [证据链+假设门+对抗验证和裁决]; verify via [observable evidence / human gate] and mark unknowns TO_VALIDATE.”

## PR22 — UI visual rhetoric and decision-ready presentation

**Trigger examples:** PPT|slide|AGENDA|封面|脑图|图示|视觉|截图|颜色|Layout|屏幕|图表

**Generative rule:** 将演示视觉抽象为“决策信息顺序”：封面→为何→谁/痛点→方案→业务流→系统图→成本价值→里程碑→风险→行动。保留图形所表达的结构关系，换掉具体品牌/数值。

**Questions to ask / variables:** 受众、决策阶段、信息密度、图元关系

**Artifact to generate:** PRD视觉页版式规则+图表字段合同

**Quality gate:** All claims are labeled as fact, stakeholder assertion, hypothesis, estimate, or decision. Include at least one negative or counterfactual check. In a new domain, replace original names, vendors, amounts, timeframes and regulations by substantiated case inputs.

**Meta-paragraph function:** “Given [user/Need and context], identify [受众、决策阶段、信息密度、图元关系]; apply [将演示视觉抽象为“决策信息顺序”：封面→为何→谁/痛点→方案→业务流→系统图→成本价值→里程碑→风险→行动。保留图形所表达的结构关系，换掉具体品牌/数值。]; produce [PRD视觉页版式规则+图表字段合同]; verify via [observable evidence / human gate] and mark unknowns TO_VALIDATE.”

## PR23 — Source evidence integrity and conflict resolution

**Trigger examples:** 会议|纪要|访谈|引用|来源|原文|资料|记录|总结|SOP|意见书|日志

**Generative rule:** 把原始陈述与推导、提议和外部验证分开；冲突版本并列列示并说明为何采用某版本，不静默调和不同时间的报价和范围。

**Questions to ask / variables:** 来源版本、作者、日期、事实状态、冲突

**Artifact to generate:** 来源追踪表+冲突台账+未知项问卷

**Quality gate:** All claims are labeled as fact, stakeholder assertion, hypothesis, estimate, or decision. Include at least one negative or counterfactual check. In a new domain, replace original names, vendors, amounts, timeframes and regulations by substantiated case inputs.

**Meta-paragraph function:** “Given [user/Need and context], identify [来源版本、作者、日期、事实状态、冲突]; apply [把原始陈述与推导、提议和外部验证分开；冲突版本并列列示并说明为何采用某版本，不静默调和不同时间的报价和范围。]; produce [来源追踪表+冲突台账+未知项问卷]; verify via [observable evidence / human gate] and mark unknowns TO_VALIDATE.”

## PR24 — Execution and operational handoff

**Trigger examples:** 部署|上线|运维|监控|回滚|日志|备份|归档|支持|用户培训|交接

**Generative rule:** 把开发完成之外的上线准备独立为工作流：环境/权限、部署、观测、版本、运行手册、回滚、用户培训与支持责任，确保工程能真实落地。

**Questions to ask / variables:** 运行环境、交付清单、SLA、事故处理、回退条件

**Artifact to generate:** 运维验收+handoff清单+Runbook

**Quality gate:** All claims are labeled as fact, stakeholder assertion, hypothesis, estimate, or decision. Include at least one negative or counterfactual check. In a new domain, replace original names, vendors, amounts, timeframes and regulations by substantiated case inputs.

**Meta-paragraph function:** “Given [user/Need and context], identify [运行环境、交付清单、SLA、事故处理、回退条件]; apply [把开发完成之外的上线准备独立为工作流：环境/权限、部署、观测、版本、运行手册、回滚、用户培训与支持责任，确保工程能真实落地。]; produce [运维验收+handoff清单+Runbook]; verify via [observable evidence / human gate] and mark unknowns TO_VALIDATE.”

## PR25 — Operational plan and prioritization matrix

**Trigger examples:** 计划矩阵|闭环关键|低紧急|高紧急|第三方平台|思想结构化|个人与AI|管理与验收|W1｜|W2｜|W3｜

**Generative rule:** 把多条并行事务映射到周×工作流矩阵；每格必须可见优先级、截止、行动、输出、负责人与阻塞项；区分战略主线和协作支线。

**Questions to ask / variables:** 周、工作流、优先级、里程碑、owner、阻塞

**Artifact to generate:** 运营矩阵+风险/依赖仪表盘

**Quality gate:** All claims are labeled as fact, stakeholder assertion, hypothesis, estimate, or decision. Include at least one negative or counterfactual check. In a new domain, replace original names, vendors, amounts, timeframes and regulations by substantiated case inputs.

**Meta-paragraph function:** “Given [user/Need and context], identify [周、工作流、优先级、里程碑、owner、阻塞]; apply [把多条并行事务映射到周×工作流矩阵；每格必须可见优先级、截止、行动、输出、负责人与阻塞项；区分战略主线和协作支线。]; produce [运营矩阵+风险/依赖仪表盘]; verify via [observable evidence / human gate] and mark unknowns TO_VALIDATE.”

## PR26 — Specialist method vs adaptive generation

**Trigger examples:** 方法论|框架|模板|技能|Skill|prompt|投研逻辑|结构化|死框架|活生成

**Generative rule:** 区分必须固定的领域纪律与可以由模型扩展的自由度；将硬约束、开放参数、资料依赖、复核方式和中间输出写成可复用领域契约。

**Questions to ask / variables:** 领域准则、可变项、模型边界、反例

**Artifact to generate:** Domain Contract + 固定/生成分界表

**Quality gate:** All claims are labeled as fact, stakeholder assertion, hypothesis, estimate, or decision. Include at least one negative or counterfactual check. In a new domain, replace original names, vendors, amounts, timeframes and regulations by substantiated case inputs.

**Meta-paragraph function:** “Given [user/Need and context], identify [领域准则、可变项、模型边界、反例]; apply [区分必须固定的领域纪律与可以由模型扩展的自由度；将硬约束、开放参数、资料依赖、复核方式和中间输出写成可复用领域契约。]; produce [Domain Contract + 固定/生成分界表]; verify via [observable evidence / human gate] and mark unknowns TO_VALIDATE.”

## PR27 — Commercial and partnership terms

**Trigger examples:** 分成|激励|提成|回报|签约|股权|奖金|合作模式|合同|产权

**Generative rule:** 将项目商务结构与技术交付分离：付款节点、收益归属、知识产权、绩效计算口径、终止条件、审批责任；不得将讨论中条款当作生效合同。

**Questions to ask / variables:** 合作主体、收益口径、结算时点、权属、例外

**Artifact to generate:** 商务条款草案+法律复核待办

**Quality gate:** All claims are labeled as fact, stakeholder assertion, hypothesis, estimate, or decision. Include at least one negative or counterfactual check. In a new domain, replace original names, vendors, amounts, timeframes and regulations by substantiated case inputs.

**Meta-paragraph function:** “Given [user/Need and context], identify [合作主体、收益口径、结算时点、权属、例外]; apply [将项目商务结构与技术交付分离：付款节点、收益归属、知识产权、绩效计算口径、终止条件、审批责任；不得将讨论中条款当作生效合同。]; produce [商务条款草案+法律复核待办]; verify via [observable evidence / human gate] and mark unknowns TO_VALIDATE.”

## PR28 — Generic process node, operator and state

**Trigger examples:** 触发|输入|输出|节点|操作|流程|连接|调用|任务|处理|成功|失败

**Generative rule:** 无论来源是否描述技术，提取“行动主体→触发→输入→处理→输出→下一步”，并明确执行条件与失败状态；将领域名词替换为占位变量。

**Questions to ask / variables:** 角色、触发、对象、变换、产物、状态

**Artifact to generate:** 流程节点模板+状态机

**Quality gate:** All claims are labeled as fact, stakeholder assertion, hypothesis, estimate, or decision. Include at least one negative or counterfactual check. In a new domain, replace original names, vendors, amounts, timeframes and regulations by substantiated case inputs.

**Meta-paragraph function:** “Given [user/Need and context], identify [角色、触发、对象、变换、产物、状态]; apply [无论来源是否描述技术，提取“行动主体→触发→输入→处理→输出→下一步”，并明确执行条件与失败状态；将领域名词替换为占位变量。]; produce [流程节点模板+状态机]; verify via [observable evidence / human gate] and mark unknowns TO_VALIDATE.”

## PR29 — Abstract headings and navigation labels

**Trigger examples:** 章|表|图|概览|纲要|小结|结论|日程|功能体系|产品体系|阶段明细

**Generative rule:** 标题/目录/栏目应转成组织逻辑，而不是照抄标题字面；识别章节顺序、层级、首次定义、跨章节引用和缺失栏目。

**Questions to ask / variables:** 受众、章节类型、依赖、阅读路径

**Artifact to generate:** 完整目录骨架和导航锚点

**Quality gate:** All claims are labeled as fact, stakeholder assertion, hypothesis, estimate, or decision. Include at least one negative or counterfactual check. In a new domain, replace original names, vendors, amounts, timeframes and regulations by substantiated case inputs.

**Meta-paragraph function:** “Given [user/Need and context], identify [受众、章节类型、依赖、阅读路径]; apply [标题/目录/栏目应转成组织逻辑，而不是照抄标题字面；识别章节顺序、层级、首次定义、跨章节引用和缺失栏目。]; produce [完整目录骨架和导航锚点]; verify via [observable evidence / human gate] and mark unknowns TO_VALIDATE.”
