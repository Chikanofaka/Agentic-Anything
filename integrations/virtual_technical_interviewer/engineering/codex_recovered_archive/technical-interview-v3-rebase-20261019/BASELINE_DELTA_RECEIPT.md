# TIA v3 需求基线迁移回执

日期：2026-10-19（Asia/Shanghai）。状态：**文档与设计基线已迁移；应用实现及新增验收尚未执行。** 本文的 rebase 指需求和交付物对齐，不是 Git 历史重写。

## 1. 本轮范围和版本

当前用户指示将 `integrations/virtual_technical_interviewer/TIA_FULL_PRD_v3/` 设为完整 PRD 中枢。本轮延续既有架构研究、需求映射、MVP 工作包、安全本地原型设计和验收矩阵，保留经核验且兼容的工作。未修改原始 PRD、Atlas、原仓库或远端分支，未实现新应用、公开发布或使用付费 API。

| 项目 | 实际版本 / 状态 |
|---|---|
| 新产品基线 | `Chikanofaka/Agentic-Anything@53188034400be6c534d2ded56a9386ea55d6ad0e` |
| 完整主文件 | [TIA_FULL_BASELINE_PRD_v3.md](sources/TIA_FULL_PRD_v3/TIA_FULL_BASELINE_PRD_v3.md)，895 行，127155 bytes |
| 主文件 SHA-256 | `620c7c313d248a9e1bc43a220c8ab79c82e743cb5d3269ebe6150e476d5e2fb4` |
| 上一轮审计快照 | `79656f5988bf861068052951d402fb6d8b2fd491`，209 个文件核验 |
| 本机原 checkout | `[LOCAL_PATH_REDACTED]`，HEAD `6898e563b6cab76517dad13919f7d3c172881f7c`；本轮只读 |
| 配置工作路径 | `/Chikanofaka/Agentic-Anything` 在本机不存在；交付物置于本地隔离目录，未据此创建另一份同名仓库 |
| 新交付目录 | `[LOCAL_PATH_REDACTED]` |
| 旧交付目录 | `[LOCAL_PATH_REDACTED]`，保留作历史证据，不再作为现行需求 |
| 新工程分支 / 提交 | 无；没有执行 Git rebase、reset、commit 或 push |

固定版本的 [GitHub PRD](https://github.com/Chikanofaka/Agentic-Anything/blob/53188034400be6c534d2ded56a9386ea55d6ad0e/integrations/virtual_technical_interviewer/TIA_FULL_PRD_v3/TIA_FULL_BASELINE_PRD_v3.md) 与 [目录](https://github.com/Chikanofaka/Agentic-Anything/tree/53188034400be6c534d2ded56a9386ea55d6ad0e/integrations/virtual_technical_interviewer/TIA_FULL_PRD_v3) 是本次外部可复查的版本定位，不是对未来 `main` 内容的承诺。

## 2. 来源优先级与完整性

优先级为当前用户明确指示、原始用户材料与明确接受的修正，其次为完整 v3 的汇总约束，再用 Atlas 草案定位流程；Rapid 仅保留历史对照。旧 PRD 与助手建议只可解释设计历史，不能创造现行产品规则。用户批准方向与规则已经验证是两个不同状态。

已完整阅读 v3 主文件和全部配套文本，并按锁定提交验证 10 个文本文件的 Git blob；其中 8 个受包内 SHA256 清单覆盖的文本文件全部相符。Rapid 归档与旧文件内容相同。DOCX/PDF 是展示附件，本轮未下载或视觉核验，不能声称它们与 Markdown 完全一致。清单记录 PDF 为 565250 bytes，而锁定 Git tree 为 590385 bytes，存在明确大小冲突，见 [来源回执](receipts/source_verification.json) 和 [提交差异](receipts/commit_delta.json)。本次以已验证 Markdown 为准，不能把清单部分通过写成整包通过。

旧来源中的原始文字只在本地受限工作资料中核对，不复制到新交付包。原 Atlas 和四项正式 issue 仍支持可追溯的既有语义；新的 v3 并不补造缺失的逐图评审对话。

## 3. 保留、替换与新增

| 主题 | 旧交付中的内容 | v3 处理结果 |
|---|---|---|
| HAL 架构 | 严格数据包、固定可信注册、Witness 专用 controller；需要新 interview adapter | 保留并核验新提交代码未变化；不把文档扩充误作已有 HAL 能力 |
| 完成状态 | 旧计划曾把发现文档称为 M0、情景闭环称为 M1 | 这些里程碑名废止。v3 的 M0 必须包含真实受限 SQL、完整面试到 Trainer 与留出题重试闭环；文档不等于 M0 |
| 产品范围 | Rapid 的十项 FR 和首个小切片 | 迁移到 28 项 `v3:FR-*`、12 项 `v3:COM-FR-*`；保留 M1 与 Future，不因首个试点窄而删去完整产品目标 |
| 需求 ID | 旧 FR01–FR10 | 不与 v3 FR-01–FR-10 当作同义；逐条迁移并保留旧行引用 |
| 双轴评分 | Technical 60 / Communication 40 独立 | 继续使用用户试验假设；不是雇主标准。子权重来自 v3 JSON，仍为 UNAPPROVED，仅可用于明确标记的 fixture 实验 |
| 旧四因素权重 | 40/20/25/15 或 Atlas 历史权重 | 明确排除，不进入默认配置；v3 §31 Q07 的旧问题不恢复它们 |
| Bonus | Rapid 最大 +10 的设计记录 | 被 v3 的可选正向 +10–15 假设替代；默认禁用、无已批准公式，不继续携带旧上限规则 |
| Communication | 全阶段观察与反馈后的行动 | 强化为 COM-FR-001..012、16 个观察情境、独立证据及复核；关键词、自信、口音或礼貌不能自动生成能力分 |
| 第二/三轮 | 理解、能实施、真实进展分别记录 | 补齐 AH/BH/CH/DH/EH、拒绝与独立替代路径；不理解不意味着必须继续升级提示 |
| Trainer | 已关闭会话的只读交接 | 加上 reviewed receipt 条件、独立沟通诊断、留出可比题重试；同题记忆不能作为迁移证明 |
| 本地产品 | 基本回放与配置 | 将历史、恢复、导出/删除、申诉及新手手册纳入 M0；同意后的记忆与无保留模式均须设计 |
| 安全界限 | 私有答案与公开投影、宿主权威 | 保留；新增 v3 的私有原文保护、无保留证据限制、明确模式标记与模型越权负测 |

## 4. P0 缺口与工程影响

当前 HAL 没有已实现的 TIA Communication 评估器，也没有 interview domain、受限 SQL 执行器或完整训练闭环。v3 提供的是更完整的契约，不能据此声称这些缺口已经被代码填补。

P0 实现链条应为：观察机会 → 候选人原话/技术产物 → 有出处的语义判断或弃权 → 宿主验证并记录 → 独立双轴评分 → 人工复核/申诉 → Trainer 针对训练 → 留出题比较。每项材料须能链接来源、带命名空间的流程节点、agent 文档职责、宿主约束、rubric 子项与 Trainer 标签。

技术测试事实由执行器产生；沟通语义由有版本的人工/受审评估流程判定。固定算术不能把主观标签变成客观事实。没有观察、观察到失败、不适用、存在争议必须分开。帮助前后保留独立记录，表述流利不能补回失败的正确性分。

## 5. 实际命令与测试证据

前一轮在隔离快照中实际运行：

```sh
bash scripts/verify_local.sh
bash scripts/build_witness_mac.sh
```

结果为 **287 项 Python 测试及 CLI 断言通过；52 项 Witness native mock 自测通过**。原始日志分别位于旧交付 `receipts/verify_local.log`、`receipts/native_build.log`，机器回执为同名 JSON。本包附未经改写的 [HAL 日志副本](receipts/carried_forward/verify_local.log)、[Witness 日志副本](receipts/carried_forward/native_build.log) 及 [沿用说明](receipts/carried_forward/PROVENANCE.json)。原生构建是既有 Witness，并非新的 TIA 产品。没有运行 GUI 或真实模型验收；当时查询该提交的 GitHub Actions 数量为 0，不能称 CI 绿色。

本轮通过 GitHub 只读接口读取固定提交的 tree/files，使用本地 `rg`、`sed`、Python hash/CSV/JSON 检查，以及 Git 只读状态检查。新旧 tree 差异仅为 v3 目录增加 12 个文件、旧 Rapid 路径移除 1 个文件；**没有任何原有文件被修改**。因此既有 runtime/native/tests 的回归结果可作为“代码未变的沿用证据”，本轮没有重复运行 339 项测试，也不把旧日志改标为在新 SHA 上实跑。

本轮文档一致性检查见 `receipts/rebase_validation.json`。所有新 TIA 接受测试保持 `NOT_RUN`。文档覆盖率与既有 HAL 测试通过均不等于 TIA 工程完成、真实 UAT 完成或训练效果验证。

## 6. 尚未解决的基线差异

1. v3 §26 与 §26A 的 G0–G5 含义不同。本计划给两个来源保留命名空间，并另给建议里程碑名；未替用户改原 PRD。
2. §31 Q07 提及旧四因素选择，与 §14、D-10 的排除相冲突。当前采用明确排除；记录为待文档修订。
3. `contracts/DOMAIN_AND_DATA_CONTRACTS.md`、`tests/UAT_MATRIX.csv`、`engineering/CODEX_MASTER_COMMAND.md` 未包含在当前包中，不能声称已读或已实现；现有 `UAT_MATRIX_v3.csv` 单独保留。
4. 根 issue register 仍只有 F01/F02 四条；v3 对 F03-001/F06-001 的转述无法独立核验。P0 的直接用户要求有效，但不能伪造历史评审通过记录。
5. `F-ADMIN-01` 未定义；D00–D08 与 C01 等标识存在命名冲突。具体映射中的推定与缺口已标出；`exam:C01`、`rubric:C01`、`atlas:02/C01` 不混用。
6. PDF 清单大小不符；Appendix B 残留 “v2” 结束语是编辑残留，不改变 v3 基线。
7. v3 要求私人转录不得公开，但锁定 tree 仍含此前的原始材料路径。新交付包不复制该原文；原仓库的历史发布状态和后续处理需单独核对，本轮不删除远端文件或重写历史。

## 7. 本次可审阅文件

- [架构评估](ARCHITECTURE_READINESS_V3.md)：现有能力、缺口、复用边界与回归证据。
- [需求映射](REBASED_SOURCE_TRACEABILITY.csv) 与 [来源审计](SOURCE_AUDIT_V3.md)：完整来源链及旧成果迁移状态。
- [实施计划](MVP_IMPLEMENTATION_PLAN_V3.md)：范围、工作包、依赖、可验证完成条件。
- [本地原型设计](LOCAL_PROTOTYPE_DESIGN_V3.md)：完整垂直路径、权威边界和安全执行设计。
- [验收矩阵](ACCEPTANCE_TEST_MATRIX_V3.csv)：待执行的场景、预期、失败条件与证据要求。
- [规则来源登记](RULE_PROVENANCE_V3.json) 与 [待确认项](DECISIONS_REQUIRED_V3.md)：假设、未决选择及其影响。

下一阶段需要选择实现范围并补齐工程契约；本次交付不会因尚未选择而停止文档整理，也不把文档中的未来工程指令自动扩展为本轮实施授权。
