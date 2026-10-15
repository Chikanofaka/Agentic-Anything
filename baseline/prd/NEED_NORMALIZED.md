# HAL-P2D-001 · Need Normalization · v2.0

> INPUT = 本轮用户明确指令 + 本会话已经确立的 HAL 两路径 Need；旧 PRD/MVM 仅作 BASELINE。来源状态：USER_STATED、BASELINE_DOCUMENT、PROPOSAL、ASSUMPTION、OPEN；不把前一版产品假设当成独立市场需求证据。

## 需求原子化（原话→推导）
| Need ID | Actor/trigger | Pain/current substitute | Desired outcome | Boundary/evidence |
|---|---|---|---|---|
| N01 | 技术人员发现 GitHub 专项 harness | README、IDE 配置、独立分析依赖门槛高 | 用户能检查、下载并自行在已有开发环境使用完备开发包 | 用户本轮与前序陈述；未做外部市场抽样 |
| N02 | 普通用户希望使用专项业务能力 | 未理解 Skills/代码或 API | 一次性教育→接入自己有权使用的模型→使用真实领域 UI | 用户陈述；仅对兼容模型和功能有效 |
| N03 | 开发者维护第二个不同项目 | 重复写 onboarding/credentials/模型逻辑 | 用同一个 HAL Shell 装载领域包，避免复制通用层 | 产品假设，跨域复用未真实验证 |
| N04 | 产品安全审查者管理授权 | 密钥泄露、工具越权、混淆“AI 已接入” | 原生密钥托管、能力预检、工具授权、可审计 receipts | 工程约束；静态 MVM 不输入真密钥 |
| N05 | Product Owner 审查 Ready | PRD 与 Mockup 可能各讲各话、Mockup 伪装为工程成果 | Need→FR→界面→测试→Human Gate 溯源、现实标签 | 当前明确请求 |
| N06 | PRD Skill 复用同一需求 | 参考模板可能机械替换或虚构事实 | 九步推导、32 章产出、自我评估与修订候选 | 来源：PRD v2 Skill 主文件 |

## Means vs Ends
- END：更低上手阻力、更高领域任务成功率、更低二次集成成本、更可控授权。
- PROPOSED MEANS：local-first HAL Shell、package manifest、两个入口、模型适配器、Key Academy。都不是已证实的市场唯一解。
- MUST NOT ASSUME：任意 ZIP 开箱即用；所有 API key 同一种格式；浏览器 HTML 安全保存 key；一个模型 key 自动提供工具/数据库/Manus 托管 Agent；配套持久运行不需要本地常驻程序。

## JTBD
1. When I find a specialized harness, help me understand its dependencies and take a genuine developer package into my coding environment.
2. When I need the domain product rather than code, guide me to authorize compatible intelligence and produce a real result with visible status.
3. When I publish the next harness, let me declare domain actions once and inherit the shared onboarding and safe runtime.

## Counterfactual / alternatives
A0: Plain GitHub repository and IDE README; A1: A single domain-specific desktop app; A2: Generic chat frontend + backend API; A3 [recommended experiment]: shared HAL Shell + domain manifest + typed port contract. Need compare with A0/A1 on quality, setup time, code duplication, trust.

## Evidence and unknowns
- OBSERVED IN ARTIFACT: baseline v1 static HTML, simulated provider checks, deterministic finance calculator, README and source ZIP flows exist; this is NOT verified field adoption.
- USER-STATED: dual-path product intent and recursive PRD request.
- PROPOSAL: local-first execution and two illustrative domain packages.
- OPEN: target OS/OS versions, customer cohort, package licensing/ownership, actual provider/region, model pricing, budgets, baseline user timings, expected existing GitHub harnesses, required real data authority, app signing, metrics telemetry permission.

## Decision objective now
Deliver revised, decision-grade PRD and **direct-fidelity, interactive Ready MVM** with truthful deterministic proof of dual-domain reuse; human chooses DOING/MODIFY/PARKED/BLOCKED. No real key and no public release now.
