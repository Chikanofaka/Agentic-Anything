# Source Atlas — Ten Historical Inputs → Universal PRD Writing Rules

> This file describes the transferable structure of each reference. Old case facts are historical evidence, never new-project defaults. Full page/paragraph/slide/cell coverage is indexed by source ID in `ledger/paragraph_to_template_ledger.csv`.

## Inputs and editorial roles

| ID | Original source | Located textual units | Reusable role in PRD |
|---|---|---:|---|
| S01 | 智体产品需求书PRD(1).pdf | 332 | Decision-facing PRD table of contents; positioning, roles, cost/value, security, three-layer architecture, acceptance, supplier response. |
| S02 | 梦工场AI转型.pptx | 823 | Presentation narrative: executive summary, parallel schedules, stage-by-stage implementation, value accounting, next actions. |
| S03 | 梦工场AI转型项目.pdf | 383 | Alternative slide-based project timeline and decision communication; overlapping project claims should not count twice. |
| S04 | 架构求解_Final.pdf | 829 | Architectural deliberation: Need vs technical hypothesis, fixed domain methodology vs generative skills, viable MVP boundaries, expert-vendor communication and iteration. |
| S05 | 产品体系&技术架构.pdf | 45 | Graphic-heavy capability/role/data/interaction/architecture/UI maps, many texts embedded in images. |
| S06 | PRD估价完善定稿.docx | 27 | Granular raw stakeholder answers about acceptance, role permissions, supplier APIs, effort assumptions and workload usage; requires verification and conflict handling. |
| S07 | Mockup_Script.docx | 19 | Mockup intent and script: modes, localized interface, memory, interaction, provenance, multi-role flow and simulated security UX. |
| S08 | 虎翼计划——综合意见书——终稿.pdf | 391 | Formal evolving management opinion: phase approval, budget, procurement negotiations, value claims, governance and written signoff. Includes internal access data; never copy credential/password. |
| S09 | “虎翼计划”方案 初稿.pdf | 738 | Earlier Need proposal, operating principles, wide scope, security, domain-knowledge flows, costs and aspiration; distinguish early draft from later revisions. |
| S10 | 6条线计划矩阵.xlsx | 168 | Two versions of week × workstream priority/action matrices, with release gates and dependencies. Do not mix earlier and revised dates as one plan. |

## Recovered decision-grade layout (not domain-specific content)

1. Front matter: purpose, decision owner, version, what is fixed versus under discussion.
2. Need evidence: business constraint, user friction, why-now reasoning and observed substitutes.
3. Positioning: strategic asset to build and outcomes sought; do not assume a chatbot is the goal.
4. Scope: safety/nonnegotiables, Phase One value loop, Phase Two add-ons, deliberate exclusions.
5. Roles and security: user types, account graph, confidentiality classes and allowable actions.
6. Product system: capability mind map, interactions and feature-by-scenario table.
7. Quantitative dual columns: cost drivers on the left, value metrics on the right, assumptions labelled.
8. Three-layer architecture: source data → governed logic and domain methods → interactive applications.
9. Domain workflow: actors, specialized roles, data/tool ports, human gates, outputs and feedback.
10. Testing/approval: observable end-to-end acceptance and negative-security cases.
11. Delivery: resources, phases and parallel workstreams, vendor response and ownership.
12. MVM/UX and operations: direct experience, scenario, recovery, runtime and postlaunch monitoring.

## Cross-document revision distinctions

- **Early ambition vs phased reality**: some source sections envision a broad enterprise deployment, whereas later decision material frames a bounded first-phase MVP. Generic rule: stage must be selected by the CURRENT decision and tracked as a versioned scope choice.
- **Procurement vs solution feasibility**: supplier capability described or advertised is not necessarily purchased, licensed, tested or deployable. Generic rule: create a status and evidence field per external dependency.
- **Budget unit conflicts**: historical reference documents contain different ranges and currency expressions. Generic rule: estimate using work packages and verified unit prices, retain version/source/currency, never transplant a total.
- **Security location boundary**: the case was enterprise confidential; generic rule is risk-based, not an unconditional mandate that every project must build an enterprise secure database.
- **A presentation is not a PRD**: charts articulate relationships and sequencing; convert these to editable data schemas, requirement IDs and test conditions.

## How to use the ledger

Join CSV rows by `source_id` plus `location`. A source text atom has a SHA256 fingerprint but the confidential original paragraph is not copied. `rule_primary` and `rule_secondary` point to the 30 generalized writing operators; `quality_flag=LOW_REVIEW` requests human semantic adjudication. Where a figure is rendered but its lettering is not extractable, use the visual conversion map.

## S01 · Per-location transformation index

| Location | Units | Dominant generalized operators | Instruction for new Need |
|---|---:|---|---|
| page/slide 1 | 15 | PR29, PR01, PR28 | 完整目录骨架和导航锚点 |
| page/slide 2 | 13 | PR16, PR01, PR28 | 六线/多线矩阵+关键路径+版本闸门 |
| page/slide 3 | 16 | PR28, PR05, PR13 | 流程节点模板+状态机 |
| page/slide 4 | 18 | PR28, PR04, PR29 | 流程节点模板+状态机 |
| page/slide 5 | 15 | PR05, PR06, PR29 | 分级分权矩阵+威胁模型+授权测试 |
| page/slide 6 | 24 | PR28, PR07, PR29 | 流程节点模板+状态机 |
| page/slide 7 | 24 | PR07, PR29, PR06 | 功能矩阵 + 用户故事 + Given/When/Then |
| page/slide 10 | 4 | PR11, PR08, PR29 | 供应商对比矩阵 + 依赖台账 + Preflight |
| page/slide 13 | 7 | PR29, PR08, PR10 | 完整目录骨架和导航锚点 |
| page/slide 15 | 32 | PR13, PR11, PR14 | 左成本右价值双栏+低基高情景+报价表 |
| page/slide 16 | 22 | PR11, PR07, PR28 | 供应商对比矩阵 + 依赖台账 + Preflight |
| page/slide 17 | 23 | PR06, PR11, PR29 | 数据资产目录 + 流转图 + 数据契约 |
| page/slide 18 | 6 | PR07, PR06, PR10 | 功能矩阵 + 用户故事 + Given/When/Then |
| page/slide 20 | 6 | PR29, PR22, PR10 | 完整目录骨架和导航锚点 |
| page/slide 21 | 21 | PR29, PR11, PR09 | 完整目录骨架和导航锚点 |
| page/slide 22 | 7 | PR08, PR09, PR10 | 信息架构+关键用户旅程+页面状态清单 |
| page/slide 23 | 10 | PR28, PR06, PR15 | 流程节点模板+状态机 |
| page/slide 24 | 10 | PR15, PR07, PR08 | 验收矩阵+测试用例+失败恢复 |
| page/slide 25 | 16 | PR03, PR11, PR08 | 范围矩阵+阶段目标+明确非目标 |
| page/slide 26 | 2 | PR18, PR24 | 供应商回标模板+对比评分+排除项清单 |
| page/slide 27 | 13 | PR29, PR19, PR22 | 完整目录骨架和导航锚点 |
| page/slide 29 | 15 | PR29, PR19, PR28 | 完整目录骨架和导航锚点 |
| page/slide 31 | 13 | PR29, PR19, PR22 | 完整目录骨架和导航锚点 |

## S02 · Per-location transformation index

| Location | Units | Dominant generalized operators | Instruction for new Need |
|---|---:|---|---|
| page/slide 1 | 2 | PR16, PR22 | 六线/多线矩阵+关键路径+版本闸门 |
| page/slide 2 | 10 | PR22, PR16, PR14 | PRD视觉页版式规则+图表字段合同 |
| page/slide 3 | 7 | PR16, PR14, PR22 | 六线/多线矩阵+关键路径+版本闸门 |
| page/slide 4 | 19 | PR22, PR05, PR02 | PRD视觉页版式规则+图表字段合同 |
| page/slide 5 | 10 | PR22, PR16, PR14 | PRD视觉页版式规则+图表字段合同 |
| page/slide 6 | 10 | PR22, PR16, PR14 | PRD视觉页版式规则+图表字段合同 |
| page/slide 7 | 60 | PR22, PR17, PR15 | PRD视觉页版式规则+图表字段合同 |
| page/slide 8 | 60 | PR22, PR17, PR08 | PRD视觉页版式规则+图表字段合同 |
| page/slide 9 | 10 | PR22, PR16, PR14 | PRD视觉页版式规则+图表字段合同 |
| page/slide 10 | 60 | PR22, PR08, PR15 | PRD视觉页版式规则+图表字段合同 |
| page/slide 11 | 10 | PR22, PR16, PR14 | PRD视觉页版式规则+图表字段合同 |
| page/slide 12 | 17 | PR02, PR14, PR01 | 定位声明 + 战略一致性表 |
| page/slide 13 | 64 | PR22, PR15, PR04 | PRD视觉页版式规则+图表字段合同 |
| page/slide 14 | 7 | PR16, PR14, PR22 | 六线/多线矩阵+关键路径+版本闸门 |
| page/slide 15 | 46 | PR22, PR24, PR17 | PRD视觉页版式规则+图表字段合同 |
| page/slide 16 | 41 | PR22, PR06, PR23 | PRD视觉页版式规则+图表字段合同 |
| page/slide 17 | 32 | PR22, PR23, PR29 | PRD视觉页版式规则+图表字段合同 |
| page/slide 18 | 57 | PR22, PR29, PR15 | PRD视觉页版式规则+图表字段合同 |
| page/slide 19 | 36 | PR22, PR23, PR29 | PRD视觉页版式规则+图表字段合同 |
| page/slide 20 | 32 | PR22, PR15, PR29 | PRD视觉页版式规则+图表字段合同 |
| page/slide 21 | 56 | PR22, PR08, PR17 | PRD视觉页版式规则+图表字段合同 |
| page/slide 22 | 53 | PR22, PR29, PR15 | PRD视觉页版式规则+图表字段合同 |
| page/slide 23 | 6 | PR22, PR29, PR14 | PRD视觉页版式规则+图表字段合同 |
| page/slide 24 | 43 | PR22, PR15, PR12 | PRD视觉页版式规则+图表字段合同 |
| page/slide 25 | 33 | PR22, PR15, PR29 | PRD视觉页版式规则+图表字段合同 |
| page/slide 26 | 7 | PR16, PR14, PR22 | 六线/多线矩阵+关键路径+版本闸门 |
| page/slide 27 | 2 | PR16, PR13 | 六线/多线矩阵+关键路径+版本闸门 |
| page/slide 28 | 7 | PR16, PR14, PR22 | 六线/多线矩阵+关键路径+版本闸门 |
| page/slide 29 | 7 | PR22, PR06, PR04 | PRD视觉页版式规则+图表字段合同 |
| page/slide 30 | 7 | PR16, PR14, PR22 | 六线/多线矩阵+关键路径+版本闸门 |
| page/slide 31 | 6 | PR16, PR14, PR22 | 六线/多线矩阵+关键路径+版本闸门 |
| page/slide 32 | 6 | PR16, PR05, PR18 | 六线/多线矩阵+关键路径+版本闸门 |

## S03 · Per-location transformation index

| Location | Units | Dominant generalized operators | Instruction for new Need |
|---|---:|---|---|
| page/slide 1 | 2 | PR16, PR29 | 六线/多线矩阵+关键路径+版本闸门 |
| page/slide 2 | 12 | PR16, PR14, PR22 | 六线/多线矩阵+关键路径+版本闸门 |
| page/slide 3 | 21 | PR04, PR28, PR17 | Persona JTBD + RACI + 角色功能矩阵 |
| page/slide 4 | 12 | PR16, PR14, PR29 | 六线/多线矩阵+关键路径+版本闸门 |
| page/slide 5 | 39 | PR29, PR28, PR17 | 完整目录骨架和导航锚点 |
| page/slide 6 | 39 | PR29, PR28, PR17 | 完整目录骨架和导航锚点 |
| page/slide 7 | 40 | PR29, PR28, PR15 | 完整目录骨架和导航锚点 |
| page/slide 8 | 12 | PR16, PR14, PR29 | 六线/多线矩阵+关键路径+版本闸门 |
| page/slide 9 | 27 | PR29, PR24, PR28 | 完整目录骨架和导航锚点 |
| page/slide 10 | 20 | PR29, PR06, PR28 | 完整目录骨架和导航锚点 |
| page/slide 11 | 29 | PR29, PR28, PR24 | 完整目录骨架和导航锚点 |
| page/slide 12 | 16 | PR29, PR28, PR06 | 完整目录骨架和导航锚点 |
| page/slide 13 | 35 | PR29, PR28, PR08 | 完整目录骨架和导航锚点 |
| page/slide 14 | 21 | PR29, PR28, PR15 | 完整目录骨架和导航锚点 |
| page/slide 15 | 12 | PR16, PR14, PR29 | 六线/多线矩阵+关键路径+版本闸门 |
| page/slide 16 | 1 | PR16 | 六线/多线矩阵+关键路径+版本闸门 |
| page/slide 17 | 12 | PR16, PR14, PR29 | 六线/多线矩阵+关键路径+版本闸门 |
| page/slide 18 | 9 | PR28, PR29, PR06 | 流程节点模板+状态机 |
| page/slide 19 | 12 | PR16, PR14, PR29 | 六线/多线矩阵+关键路径+版本闸门 |
| page/slide 20 | 6 | PR16, PR14, PR28 | 六线/多线矩阵+关键路径+版本闸门 |
| page/slide 21 | 6 | PR16, PR05, PR18 | 六线/多线矩阵+关键路径+版本闸门 |

## S04 · Per-location transformation index

| Location | Units | Dominant generalized operators | Instruction for new Need |
|---|---:|---|---|
| page/slide 1 | 10 | PR29, PR28, PR01 | 完整目录骨架和导航锚点 |
| page/slide 2 | 6 | PR26, PR01, PR17 | Domain Contract + 固定/生成分界表 |
| page/slide 3 | 10 | PR21, PR26, PR10 | 证据链+假设门+对抗验证和裁决 |
| page/slide 4 | 2 | PR21, PR16 | 证据链+假设门+对抗验证和裁决 |
| page/slide 5 | 9 | PR28, PR14, PR29 | 流程节点模板+状态机 |
| page/slide 6 | 9 | PR28, PR23, PR02 | 流程节点模板+状态机 |
| page/slide 7 | 6 | PR07, PR01, PR14 | 功能矩阵 + 用户故事 + Given/When/Then |
| page/slide 8 | 6 | PR07, PR17, PR15 | 功能矩阵 + 用户故事 + Given/When/Then |
| page/slide 9 | 10 | PR19, PR28, PR26 | 可体验样稿脚本+现实标签+Human UAT |
| page/slide 10 | 8 | PR26, PR07, PR02 | Domain Contract + 固定/生成分界表 |
| page/slide 11 | 7 | PR26, PR16, PR15 | Domain Contract + 固定/生成分界表 |
| page/slide 12 | 6 | PR26, PR10 | Domain Contract + 固定/生成分界表 |
| page/slide 13 | 9 | PR28, PR03, PR26 | 流程节点模板+状态机 |
| page/slide 14 | 7 | PR16, PR24, PR05 | 六线/多线矩阵+关键路径+版本闸门 |
| page/slide 15 | 6 | PR26, PR15, PR10 | Domain Contract + 固定/生成分界表 |
| page/slide 16 | 7 | PR26, PR11, PR12 | Domain Contract + 固定/生成分界表 |
| page/slide 17 | 8 | PR28, PR20, PR15 | 流程节点模板+状态机 |
| page/slide 18 | 10 | PR28, PR24, PR11 | 流程节点模板+状态机 |
| page/slide 19 | 8 | PR28, PR01, PR26 | 流程节点模板+状态机 |
| page/slide 20 | 7 | PR26, PR11, PR14 | Domain Contract + 固定/生成分界表 |
| page/slide 21 | 7 | PR26, PR28, PR06 | Domain Contract + 固定/生成分界表 |
| page/slide 22 | 7 | PR26, PR10, PR28 | Domain Contract + 固定/生成分界表 |
| page/slide 23 | 7 | PR10, PR26, PR29 | 工作流状态机 + 工件流 + 质量门 |
| page/slide 24 | 9 | PR28, PR21, PR07 | 流程节点模板+状态机 |
| page/slide 25 | 9 | PR17, PR02, PR28 | 决策台账+RACI+启动签署页 |
| page/slide 26 | 9 | PR28, PR21, PR11 | 流程节点模板+状态机 |
| page/slide 27 | 10 | PR28, PR21, PR26 | 流程节点模板+状态机 |
| page/slide 28 | 8 | PR28, PR21, PR26 | 流程节点模板+状态机 |
| page/slide 29 | 7 | PR14, PR26, PR01 | 价值树+KPI契约+ROI模型（含不确定性） |
| page/slide 30 | 7 | PR28, PR27, PR14 | 流程节点模板+状态机 |
| page/slide 31 | 9 | PR26, PR17, PR15 | Domain Contract + 固定/生成分界表 |
| page/slide 32 | 10 | PR28, PR26, PR08 | 流程节点模板+状态机 |
| page/slide 33 | 8 | PR26, PR29, PR09 | Domain Contract + 固定/生成分界表 |
| page/slide 34 | 7 | PR28, PR26, PR02 | 流程节点模板+状态机 |
| page/slide 35 | 7 | PR26, PR16, PR28 | Domain Contract + 固定/生成分界表 |
| page/slide 36 | 9 | PR26, PR28, PR03 | Domain Contract + 固定/生成分界表 |
| page/slide 37 | 7 | PR26, PR16, PR09 | Domain Contract + 固定/生成分界表 |
| page/slide 38 | 7 | PR26, PR11, PR28 | Domain Contract + 固定/生成分界表 |
| page/slide 39 | 10 | PR01, PR05, PR14 | Need Statement + Evidence Ledger + 可证伪假设 |
| page/slide 40 | 11 | PR28, PR16, PR15 | 流程节点模板+状态机 |
| page/slide 41 | 6 | PR28, PR16, PR01 | 流程节点模板+状态机 |
| page/slide 42 | 8 | PR14, PR28, PR17 | 价值树+KPI契约+ROI模型（含不确定性） |
| page/slide 43 | 6 | PR17, PR20, PR04 | 决策台账+RACI+启动签署页 |
| page/slide 44 | 6 | PR26, PR28, PR11 | Domain Contract + 固定/生成分界表 |
| page/slide 45 | 8 | PR26, PR28, PR10 | Domain Contract + 固定/生成分界表 |
| page/slide 46 | 10 | PR28, PR07, PR14 | 流程节点模板+状态机 |
| page/slide 47 | 8 | PR28, PR26, PR15 | 流程节点模板+状态机 |
| page/slide 48 | 6 | PR26, PR14, PR27 | Domain Contract + 固定/生成分界表 |
| page/slide 49 | 7 | PR28, PR20, PR14 | 流程节点模板+状态机 |
| page/slide 50 | 8 | PR26, PR12, PR10 | Domain Contract + 固定/生成分界表 |
| page/slide 51 | 8 | PR28, PR01, PR26 | 流程节点模板+状态机 |
| page/slide 52 | 8 | PR28, PR26, PR01 | 流程节点模板+状态机 |
| page/slide 53 | 9 | PR15, PR29, PR28 | 验收矩阵+测试用例+失败恢复 |
| page/slide 54 | 8 | PR28, PR26, PR29 | 流程节点模板+状态机 |
| page/slide 55 | 8 | PR28, PR22, PR04 | 流程节点模板+状态机 |
| page/slide 56 | 7 | PR28, PR11, PR20 | 流程节点模板+状态机 |
| page/slide 57 | 8 | PR11, PR28, PR09 | 供应商对比矩阵 + 依赖台账 + Preflight |
| page/slide 58 | 10 | PR26, PR28, PR16 | Domain Contract + 固定/生成分界表 |
| page/slide 59 | 7 | PR28, PR11, PR01 | 流程节点模板+状态机 |
| page/slide 60 | 10 | PR28, PR15, PR26 | 流程节点模板+状态机 |
| page/slide 61 | 9 | PR28, PR11, PR29 | 流程节点模板+状态机 |
| page/slide 62 | 9 | PR28, PR29, PR11 | 流程节点模板+状态机 |
| page/slide 63 | 9 | PR28, PR17, PR07 | 流程节点模板+状态机 |
| page/slide 64 | 9 | PR01, PR26, PR28 | Need Statement + Evidence Ledger + 可证伪假设 |
| page/slide 65 | 8 | PR28, PR09, PR01 | 流程节点模板+状态机 |
| page/slide 66 | 7 | PR04, PR28, PR20 | Persona JTBD + RACI + 角色功能矩阵 |
| page/slide 67 | 9 | PR16, PR03, PR01 | 六线/多线矩阵+关键路径+版本闸门 |
| page/slide 68 | 9 | PR28, PR01, PR15 | 流程节点模板+状态机 |
| page/slide 69 | 10 | PR28, PR01, PR14 | 流程节点模板+状态机 |
| page/slide 70 | 8 | PR28, PR26, PR03 | 流程节点模板+状态机 |
| page/slide 71 | 9 | PR26, PR28, PR18 | Domain Contract + 固定/生成分界表 |
| page/slide 72 | 7 | PR26, PR07, PR15 | Domain Contract + 固定/生成分界表 |
| page/slide 73 | 11 | PR28, PR14, PR26 | 流程节点模板+状态机 |
| page/slide 74 | 9 | PR28, PR20, PR26 | 流程节点模板+状态机 |
| page/slide 75 | 9 | PR26, PR28, PR07 | Domain Contract + 固定/生成分界表 |
| page/slide 76 | 9 | PR26, PR02, PR28 | Domain Contract + 固定/生成分界表 |
| page/slide 77 | 8 | PR28, PR26, PR11 | 流程节点模板+状态机 |
| page/slide 78 | 7 | PR01, PR02, PR07 | Need Statement + Evidence Ledger + 可证伪假设 |
| page/slide 79 | 9 | PR28, PR07, PR21 | 流程节点模板+状态机 |
| page/slide 80 | 10 | PR28, PR02, PR01 | 流程节点模板+状态机 |
| page/slide 81 | 9 | PR28, PR26, PR03 | 流程节点模板+状态机 |
| page/slide 82 | 9 | PR28, PR26, PR24 | 流程节点模板+状态机 |
| page/slide 83 | 8 | PR01, PR21, PR28 | Need Statement + Evidence Ledger + 可证伪假设 |
| page/slide 84 | 8 | PR28, PR26, PR19 | 流程节点模板+状态机 |
| page/slide 85 | 7 | PR28, PR20, PR15 | 流程节点模板+状态机 |
| page/slide 86 | 7 | PR28, PR26, PR27 | 流程节点模板+状态机 |
| page/slide 87 | 7 | PR01, PR28, PR03 | Need Statement + Evidence Ledger + 可证伪假设 |
| page/slide 88 | 9 | PR26, PR28, PR07 | Domain Contract + 固定/生成分界表 |
| page/slide 89 | 8 | PR28, PR26, PR13 | 流程节点模板+状态机 |
| page/slide 90 | 8 | PR28, PR13, PR26 | 流程节点模板+状态机 |
| page/slide 91 | 10 | PR28, PR04, PR20 | 流程节点模板+状态机 |
| page/slide 92 | 11 | PR28, PR16, PR26 | 流程节点模板+状态机 |
| page/slide 93 | 14 | PR28, PR07, PR11 | 流程节点模板+状态机 |
| page/slide 94 | 10 | PR28, PR26, PR10 | 流程节点模板+状态机 |
| page/slide 95 | 10 | PR28, PR26, PR16 | 流程节点模板+状态机 |
| page/slide 96 | 10 | PR28, PR10, PR26 | 流程节点模板+状态机 |
| page/slide 97 | 11 | PR28, PR03, PR01 | 流程节点模板+状态机 |
| page/slide 98 | 12 | PR28, PR16, PR07 | 流程节点模板+状态机 |
| page/slide 99 | 13 | PR28 | 流程节点模板+状态机 |
| page/slide 100 | 1 | PR28 | 流程节点模板+状态机 |

## S05 · Per-location transformation index

| Location | Units | Dominant generalized operators | Instruction for new Need |
|---|---:|---|---|
| page/slide 3 | 4 | PR11, PR08, PR29 | 供应商对比矩阵 + 依赖台账 + Preflight |
| page/slide 6 | 7 | PR29, PR08, PR09 | 完整目录骨架和导航锚点 |
| page/slide 9 | 6 | PR29, PR22, PR10 | 完整目录骨架和导航锚点 |
| page/slide 10 | 21 | PR29, PR11, PR09 | 完整目录骨架和导航锚点 |
| page/slide 11 | 7 | PR09, PR08 | 分层架构+模块边界+连接契约+部署方案 |

## S06 · Per-location transformation index

| Location | Units | Dominant generalized operators | Instruction for new Need |
|---|---:|---|---|
| paragraph0001 | 1 | PR15 | 验收矩阵+测试用例+失败恢复 |
| paragraph0002 | 1 | PR07 | 功能矩阵 + 用户故事 + Given/When/Then |
| paragraph0004 | 1 | PR05 | 分级分权矩阵+威胁模型+授权测试 |
| paragraph0005 | 1 | PR04 | Persona JTBD + RACI + 角色功能矩阵 |
| paragraph0006 | 1 | PR04 | Persona JTBD + RACI + 角色功能矩阵 |
| paragraph0007 | 1 | PR23 | 来源追踪表+冲突台账+未知项问卷 |
| paragraph0008 | 1 | PR07 | 功能矩阵 + 用户故事 + Given/When/Then |
| paragraph0009 | 1 | PR06 | 数据资产目录 + 流转图 + 数据契约 |
| paragraph0010 | 1 | PR24 | 运维验收+handoff清单+Runbook |
| paragraph0012 | 1 | PR11 | 供应商对比矩阵 + 依赖台账 + Preflight |
| paragraph0013 | 1 | PR11 | 供应商对比矩阵 + 依赖台账 + Preflight |
| paragraph0014 | 1 | PR11 | 供应商对比矩阵 + 依赖台账 + Preflight |
| paragraph0015 | 1 | PR04 | Persona JTBD + RACI + 角色功能矩阵 |
| paragraph0016 | 1 | PR15 | 验收矩阵+测试用例+失败恢复 |
| paragraph0017 | 1 | PR11 | 供应商对比矩阵 + 依赖台账 + Preflight |
| paragraph0018 | 1 | PR11 | 供应商对比矩阵 + 依赖台账 + Preflight |
| paragraph0019 | 1 | PR11 | 供应商对比矩阵 + 依赖台账 + Preflight |
| paragraph0020 | 1 | PR13 | 左成本右价值双栏+低基高情景+报价表 |
| paragraph0021 | 1 | PR13 | 左成本右价值双栏+低基高情景+报价表 |
| paragraph0022 | 1 | PR07 | 功能矩阵 + 用户故事 + Given/When/Then |
| paragraph0023 | 1 | PR05 | 分级分权矩阵+威胁模型+授权测试 |
| paragraph0024 | 1 | PR06 | 数据资产目录 + 流转图 + 数据契约 |
| paragraph0025 | 1 | PR28 | 流程节点模板+状态机 |
| paragraph0026 | 1 | PR11 | 供应商对比矩阵 + 依赖台账 + Preflight |
| paragraph0027 | 1 | PR04 | Persona JTBD + RACI + 角色功能矩阵 |
| paragraph0028 | 1 | PR24 | 运维验收+handoff清单+Runbook |
| paragraph0029 | 1 | PR11 | 供应商对比矩阵 + 依赖台账 + Preflight |

## S07 · Per-location transformation index

| Location | Units | Dominant generalized operators | Instruction for new Need |
|---|---:|---|---|
| paragraph0001 | 1 | PR26 | Domain Contract + 固定/生成分界表 |
| paragraph0002 | 1 | PR08 | 信息架构+关键用户旅程+页面状态清单 |
| paragraph0003 | 1 | PR08 | 信息架构+关键用户旅程+页面状态清单 |
| paragraph0004 | 1 | PR08 | 信息架构+关键用户旅程+页面状态清单 |
| paragraph0005 | 1 | PR11 | 供应商对比矩阵 + 依赖台账 + Preflight |
| paragraph0006 | 1 | PR10 | 工作流状态机 + 工件流 + 质量门 |
| paragraph0007 | 1 | PR11 | 供应商对比矩阵 + 依赖台账 + Preflight |
| paragraph0008 | 1 | PR10 | 工作流状态机 + 工件流 + 质量门 |
| paragraph0009 | 1 | PR06 | 数据资产目录 + 流转图 + 数据契约 |
| paragraph0010 | 1 | PR11 | 供应商对比矩阵 + 依赖台账 + Preflight |
| paragraph0011 | 1 | PR11 | 供应商对比矩阵 + 依赖台账 + Preflight |
| paragraph0012 | 1 | PR11 | 供应商对比矩阵 + 依赖台账 + Preflight |
| paragraph0013 | 1 | PR11 | 供应商对比矩阵 + 依赖台账 + Preflight |
| paragraph0014 | 1 | PR28 | 流程节点模板+状态机 |
| paragraph0015 | 1 | PR21 | 证据链+假设门+对抗验证和裁决 |
| paragraph0016 | 1 | PR12 | 记忆模型 + 版本追踪 + Feedback Loop |
| paragraph0017 | 1 | PR07 | 功能矩阵 + 用户故事 + Given/When/Then |
| paragraph0023 | 1 | PR06 | 数据资产目录 + 流转图 + 数据契约 |
| paragraph0024 | 1 | PR06 | 数据资产目录 + 流转图 + 数据契约 |

## S08 · Per-location transformation index

| Location | Units | Dominant generalized operators | Instruction for new Need |
|---|---:|---|---|
| page/slide 1 | 28 | PR03, PR17, PR29 | 范围矩阵+阶段目标+明确非目标 |
| page/slide 2 | 25 | PR11, PR13, PR28 | 供应商对比矩阵 + 依赖台账 + Preflight |
| page/slide 3 | 19 | PR03, PR27, PR28 | 范围矩阵+阶段目标+明确非目标 |
| page/slide 4 | 15 | PR28, PR29, PR23 | 流程节点模板+状态机 |
| page/slide 5 | 28 | PR28, PR29, PR16 | 流程节点模板+状态机 |
| page/slide 6 | 29 | PR28, PR29, PR23 | 流程节点模板+状态机 |
| page/slide 7 | 32 | PR23, PR29, PR28 | 来源追踪表+冲突台账+未知项问卷 |
| page/slide 8 | 32 | PR23, PR29, PR28 | 来源追踪表+冲突台账+未知项问卷 |
| page/slide 9 | 32 | PR29, PR28, PR07 | 完整目录骨架和导航锚点 |
| page/slide 10 | 31 | PR29, PR28, PR09 | 完整目录骨架和导航锚点 |
| page/slide 11 | 28 | PR29, PR28, PR07 | 完整目录骨架和导航锚点 |
| page/slide 12 | 28 | PR17, PR03, PR28 | 决策台账+RACI+启动签署页 |
| page/slide 13 | 30 | PR17, PR13, PR29 | 决策台账+RACI+启动签署页 |
| page/slide 14 | 29 | PR17, PR28, PR11 | 决策台账+RACI+启动签署页 |
| page/slide 15 | 2 | PR29, PR24 | 完整目录骨架和导航锚点 |
| page/slide 16 | 1 | PR19 | 可体验样稿脚本+现实标签+Human UAT |
| page/slide 17 | 1 | PR28 | 流程节点模板+状态机 |
| page/slide 18 | 1 | PR01 | Need Statement + Evidence Ledger + 可证伪假设 |

## S09 · Per-location transformation index

| Location | Units | Dominant generalized operators | Instruction for new Need |
|---|---:|---|---|
| page/slide 1 | 30 | PR05, PR28, PR29 | 分级分权矩阵+威胁模型+授权测试 |
| page/slide 2 | 9 | PR28, PR24, PR05 | 流程节点模板+状态机 |
| page/slide 3 | 24 | PR28, PR07, PR04 | 流程节点模板+状态机 |
| page/slide 4 | 19 | PR29, PR14, PR28 | 完整目录骨架和导航锚点 |
| page/slide 5 | 22 | PR01, PR06, PR29 | Need Statement + Evidence Ledger + 可证伪假设 |
| page/slide 6 | 29 | PR06, PR07, PR23 | 数据资产目录 + 流转图 + 数据契约 |
| page/slide 7 | 15 | PR11, PR26, PR07 | 供应商对比矩阵 + 依赖台账 + Preflight |
| page/slide 8 | 23 | PR05, PR28, PR04 | 分级分权矩阵+威胁模型+授权测试 |
| page/slide 9 | 23 | PR28, PR11, PR29 | 流程节点模板+状态机 |
| page/slide 10 | 26 | PR28, PR07, PR11 | 流程节点模板+状态机 |
| page/slide 11 | 17 | PR11, PR28, PR29 | 供应商对比矩阵 + 依赖台账 + Preflight |
| page/slide 12 | 19 | PR01, PR28, PR29 | Need Statement + Evidence Ledger + 可证伪假设 |
| page/slide 13 | 17 | PR05, PR13, PR11 | 分级分权矩阵+威胁模型+授权测试 |
| page/slide 14 | 20 | PR29, PR28, PR07 | 完整目录骨架和导航锚点 |
| page/slide 15 | 19 | PR05, PR28, PR29 | 分级分权矩阵+威胁模型+授权测试 |
| page/slide 16 | 25 | PR05, PR29, PR06 | 分级分权矩阵+威胁模型+授权测试 |
| page/slide 17 | 22 | PR28, PR06, PR07 | 流程节点模板+状态机 |
| page/slide 18 | 32 | PR07, PR05, PR29 | 功能矩阵 + 用户故事 + Given/When/Then |
| page/slide 19 | 54 | PR29, PR07, PR12 | 完整目录骨架和导航锚点 |
| page/slide 20 | 57 | PR29, PR07, PR05 | 完整目录骨架和导航锚点 |
| page/slide 21 | 34 | PR29, PR13, PR11 | 完整目录骨架和导航锚点 |
| page/slide 22 | 34 | PR29, PR23, PR07 | 完整目录骨架和导航锚点 |
| page/slide 23 | 30 | PR23, PR06, PR07 | 来源追踪表+冲突台账+未知项问卷 |
| page/slide 24 | 14 | PR06, PR09, PR22 | 数据资产目录 + 流转图 + 数据契约 |
| page/slide 25 | 10 | PR05, PR29, PR12 | 分级分权矩阵+威胁模型+授权测试 |
| page/slide 26 | 14 | PR07, PR11, PR28 | 功能矩阵 + 用户故事 + Given/When/Then |
| page/slide 27 | 24 | PR28, PR07, PR06 | 流程节点模板+状态机 |
| page/slide 28 | 23 | PR15, PR28, PR06 | 验收矩阵+测试用例+失败恢复 |
| page/slide 29 | 21 | PR07, PR28, PR08 | 功能矩阵 + 用户故事 + Given/When/Then |
| page/slide 30 | 21 | PR29, PR05, PR18 | 完整目录骨架和导航锚点 |
| page/slide 31 | 11 | PR29, PR28, PR15 | 完整目录骨架和导航锚点 |

## S10 · Per-location transformation index

| Location | Units | Dominant generalized operators | Instruction for new Need |
|---|---:|---|---|
| 初稿!row1 | 7 | PR25 | 运营矩阵+风险/依赖仪表盘 |
| 初稿!row2 | 7 | PR25, PR16 | 运营矩阵+风险/依赖仪表盘 |
| 初稿!row3 | 7 | PR25, PR16 | 运营矩阵+风险/依赖仪表盘 |
| 初稿!row4 | 7 | PR25, PR16 | 运营矩阵+风险/依赖仪表盘 |
| 初稿!row5 | 7 | PR25, PR16 | 运营矩阵+风险/依赖仪表盘 |
| 初稿!row6 | 7 | PR25, PR16 | 运营矩阵+风险/依赖仪表盘 |
| 初稿!row7 | 7 | PR25 | 运营矩阵+风险/依赖仪表盘 |
| 初稿!row8 | 7 | PR25 | 运营矩阵+风险/依赖仪表盘 |
| 审阅后!row1 | 14 | PR25 | 运营矩阵+风险/依赖仪表盘 |
| 审阅后!row2 | 14 | PR25, PR16 | 运营矩阵+风险/依赖仪表盘 |
| 审阅后!row3 | 14 | PR25, PR16 | 运营矩阵+风险/依赖仪表盘 |
| 审阅后!row4 | 14 | PR25, PR09 | 运营矩阵+风险/依赖仪表盘 |
| 审阅后!row5 | 14 | PR25, PR16 | 运营矩阵+风险/依赖仪表盘 |
| 审阅后!row6 | 14 | PR25 | 运营矩阵+风险/依赖仪表盘 |
| 审阅后!row7 | 14 | PR25 | 运营矩阵+风险/依赖仪表盘 |
| 审阅后!row8 | 14 | PR25, PR16 | 运营矩阵+风险/依赖仪表盘 |
