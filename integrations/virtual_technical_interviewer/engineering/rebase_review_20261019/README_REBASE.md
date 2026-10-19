# TIA v3 基线迁移交付包

日期：2026-10-19。固定版本：`Chikanofaka/Agentic-Anything@53188034400be6c534d2ded56a9386ea55d6ad0e`。

已将先前的 Rapid 工程发现迁移到完整 v3。此包是可审阅的架构、需求、实施和验收设计；没有实现 TIA 应用或修改原仓库。

| 文件 | 用途 |
|---|---|
| [BASELINE_DELTA_RECEIPT.md](BASELINE_DELTA_RECEIPT.md) | 从这里开始：范围、实际版本、保留/替换项、来源冲突、测试证据 |
| [ARCHITECTURE_READINESS_V3.md](ARCHITECTURE_READINESS_V3.md) | HAL 实际能力与接口约束；最小新域接入方案 |
| [SOURCE_AUDIT_V3.md](SOURCE_AUDIT_V3.md) | 来源完整性、历史评审缺口、标识命名空间及图覆盖限制 |
| [REBASED_SOURCE_TRACEABILITY.csv](REBASED_SOURCE_TRACEABILITY.csv) | v3 的 28 FR、12 COM-FR、观察/评分项与原来源、流程、agent 职责的映射 |
| [MVP_IMPLEMENTATION_PLAN_V3.md](MVP_IMPLEMENTATION_PLAN_V3.md) | 工作包、依赖、真实 M0 条件与完整后续范围 |
| [LOCAL_PROTOTYPE_DESIGN_V3.md](LOCAL_PROTOTYPE_DESIGN_V3.md) | 本地真实 SQL、完整反馈、独立双评分、复核与留出题训练设计 |
| [ACCEPTANCE_TEST_MATRIX_V3.csv](ACCEPTANCE_TEST_MATRIX_V3.csv) | 202 个计划场景，均为 NOT_RUN；各含失败条件、验证方法与所需证据 |
| [RULE_PROVENANCE_V3.json](RULE_PROVENANCE_V3.json) | 25 条规则/假设的来源、配置与验证状态；不是激活中的 runtime 配置 |
| [DECISIONS_REQUIRED_V3.md](DECISIONS_REQUIRED_V3.md) | 下一阶段需要选择的内容与本轮可撤销处理 |
| [receipts/rebase_validation.json](receipts/rebase_validation.json) | 本次文档与来源一致性检查；不能替代产品验收 |

核心结论：HAL 的包契约、可信注册和隔离传输模式可以复用；Witness 的交互控制器和完整 state 导出不能直接当面试系统使用。新的 interview controller、受限 SQL evaluator、沟通证据与训练交接仍需实现。

Communication 保持一等行为要求，和 Technical 各自评分。60/40 是当前用户假设；子权重仍未批准；10–15 bonus 假设默认禁用。旧四因素权重和 Rapid 的 +10 上限不再作为现行规则。

既有 287 项 HAL 与 52 项 Witness mock 通过记录属于上一快照；本轮核验相关代码未变化后沿用，未声称在新 SHA 重跑。所有新 TIA 场景仍未执行。10 个 v3 文本的 Git blob 均已核验；PDF/DOCX 内容未核验，PDF 的清单大小存在冲突。

本地源副本仅含 v3 的公开文本资料；不随交付包复制原始私人转录、旧 Atlas 内嵌原文或完整旧仓库。`receipts/carried_forward/` 中旧日志保留原版本与时间，不改写为新结果。重跑完整来源核验脚本需要本机旧隔离快照路径；交付包不含那个快照。

所有文件当前位于临时目录，适合审阅与下载归档，不应把 `/private/tmp` 当长期项目存储。本轮没有提交、推送、发布、付费调用或破坏性修改。
