"use strict";

// The renderer holds only presentation state and unsent drafts. All session
// commands, tutorial transitions, recorded inputs and receipts belong to the host.
(() => {
  const app = document.getElementById("app");
  const errors = document.getElementById("error");
  const announcement = document.getElementById("announcement");
  const pending = new Map();
  let serial = 0;
  let state = null;
  let busy = false;
  let draft = "";
  let draftKind = "clarify";
  let liveDraft = "";
  let gradeFixtureDraft = "";
  let gradeFixtureApproved = false;
  let gradeApprovalBinding = "";
  let gradeQuestionHash = "";
  let liveKind = "clarify";
  let questionDrafts = [];
  let questionSources = [];
  let questionFieldDrafts = [];
  let previousScreen = null;
  const strings = {
    en: {
      livePreview: "Live Conversational Preview", livePreviewNote: "A bounded conversation with a Senior Interviewer; technical capability and communication remain NOT_SCORED. Separately approved PostgreSQL local fixture runs may verify an individual submitted SQL answer.",
      previewQuestion: "Approved conversation case · no grading", verifyPreview: "Verify access & open preview · 1 paid request",
      previewSelected: "Selected mechanism", previewSource: "Choose the mechanism in the configuration preview; it controls the approved instructions used here.",
      previewSend: "Send to Senior Interviewer · 1 paid request", previewRetry: "Retry recorded response · 1 paid request",
      retryRecorded: "Your input was recorded, but no model reply was committed. A retry sends the same recorded text and uses one additional request. There are no automatic retries.",
      rehearsalTimeout: "Interview time expired · frozen record", rehearsalClockHold: "Interview paused by local clock anomaly",
      rehearsalClock: "⏱ Show / hide interview time", rehearsalElapsed: "Elapsed",
      rehearsalLimit: "Session hard limit", rehearsalQuestionTime: "Current question",
      rehearsalWaitTime: "Waiting for model", localTimeUncertified: "Host-owned local clock. Device time is not certified; changing system time may interrupt the interview.",
      previewComplete: "The preview exchange is complete. Close it to freeze the record; no score is assigned.",
      previewClosed: "Preview closed · record frozen", closePreview: "Close preview & freeze record", cancelRequest: "Cancel pending request",
      pendingRequest: "Waiting for the native provider. Cancellation prevents a late reply from being committed; a request already sent may still be billed.",
      liveResponse: "Senior Interviewer · LIVE_MODEL", noLiveResponse: "No model reply has been committed.",
      previewRecorded: "Model reply committed by the trusted controller.", previewInput: "Your preview response", previewPrivacy: "Submitted text and the approved question are sent to the selected provider only after native paid-request consent. The local transcript includes your submitted text.",
      requestsTotal: "Requests in this App process", unmeasuredRequests: "Requests without measured usage", model: "Model", requestLimit: "Request limit", tokenUsage: "Reported tokens", usageUnknown: "Not supplied by provider", usageScope: "Usage is provider-reported, not a cost estimate.",
      previewFrozen: "The frozen record preserves response provenance and submitted text. Technical and Communication are not scored; no SQL was executed.",
      providerConsentRequired: "Open the native API Portal to authorize paid requests before verifying access.",
      invalidCredential: "The provider rejected the credential. Reopen the native API Portal to replace it.",
      modelUnavailable: "The selected model is unavailable for this credential. Choose an accessible model in the native API Portal.",
      rateLimited: "The provider rate limit was reached. Nothing was retried automatically.",
      usageLimited: "The approved request limit or provider usage limit was reached. No automatic request was made.",
      providerTimeout: "The provider request timed out. No model reply was committed.",
      providerRefused: "The provider refused this request. No model reply was committed.",
      invalidProviderResponse: "The provider response failed validation. No model reply was committed.",
      networkFailure: "The provider could not be reached. Your text remains available; retry only when you choose.",
      providerCancelled: "The pending request was cancelled. A late response cannot be committed.",
      title: "TECHNICAL INTERVIEW LAB", subtitle: "A thoughtful rehearsal. A stronger next interview.",
      language: "中文", languageLabel: "Switch interface to Chinese", reset: "Restart / delete local session",
      entry: "Choose your experience", entryBody: "Learn the interview flow, then prepare for a real technical interview.",
      tutorial: "Guided Onboarding", tutorialBody: "One fixed Medium PostgreSQL question. A guided rehearsal with simulated feedback.",
      tutorialMeta: "No API key · No network · No grades", start: "Start tutorial →",
      real: "Real AI Interview", realBody: "Prepare a 45 or 60 minute interview, with 3 or 4 Hard questions and a Senior Interviewer.",
      realMeta: "Native API Portal first · Live activation required", configure: "Configure →",
      privacy: "Starting the tutorial saves your progress and submitted responses on this Mac. Restart deletes the local session. Export only when you choose.",
      welcome: "Welcome, candidate.", welcomeBody: "Your first interview is a guided rehearsal. No model calls, no grades, no payment.",
      welcomeDetail: "Practise clarification, explain your plan, record SQL and explore the separate Trainer handoff.",
      rules: "Interview rules", ruleClock: "The trusted host controls the session clock and transitions.",
      ruleHelp: "You can clarify requirements and request permitted help. Assistance is never guaranteed.",
      ruleAnswer: "Protected answers and hidden tests remain outside the interviewer’s authority.",
      simulation: "Tutorial feedback is scripted. SQL is not executed, and neither Technical Capability nor Communication is scored.",
      next: "Got it · Next →", understand: "I understand →", back: "Back", skip: "Skip tutorial · Real AI →",
      question: "Your practice case", medium: "Medium · PostgreSQL · 1 question", schema: "Schema",
      questionNote: "This fixed tutorial question demonstrates the flow. It has no running database or validated test fixture.",
      enterRoom: "Enter interview room →", room: "Interview room", simulated: "SIMULATED",
      senior: "Senior Technical Interviewer", prompt: "Before writing SQL, clarify the task and explain how you will handle tied dates and NULL timestamps.",
      kind: "Response type", clarify: "Clarification", plan: "Plan", implement: "SQL submission", test: "Test idea / SQL", help: "Help request",
      response: "Your response", placeholder: "Type a clarification, explain your plan, or write your SQL…",
      shortcut: "⌘ Enter to record · Your text is recorded by the host, never executed here.",
      submit: "Record practice response", finish: "Finish tutorial →", recorded: "Recorded conversation",
      emptyHistory: "Your submitted responses will appear here.", candidate: "You", feedback: "Simulated interviewer",
      technical: "Technical Capability", communication: "Communication", notScored: "NOT_SCORED",
      execution: "SQL execution", notRun: "NOT_RUN", noTests: "No SQL evaluator has run. A recorded response is not a passing test.",
      technicalExecution: "Technical execution", unverifiedStatus: "UNVERIFIED",
      complete: "Tutorial complete", completeBody: "You have practised the flow. Technical Capability and Communication remain independently NOT_SCORED.",
      trainer: "Trainer preview", trainerNote: "Scripted coaching illustration based on the permitted frozen record; not an assessed performance result.",
      drill: "Targeted drill", followUp: "Unfamiliar follow-up", evidence: "Linked evidence",
      receipt: "Frozen receipt", receiptNote: "This receipt records the tutorial and submitted text. Export includes your responses; share it only when you choose.",
      digest: "Receipt SHA-256", replay: "Replay tutorial", explore: "Explore Real AI →", export: "Export receipt…",
      api: "Activate Real AI", apiBody: "Credentials are entered in a native secure sheet. They are never sent to this webpage or the Python controller.",
      portal: "Open native API Portal…", disconnected: "Disconnect", apiGate: "Native activation asks for your model, request limit and paid-request consent. Storing a key makes no request and does not verify access. A successful authorized reply verifies the connection; full interview launch remains blocked.",
      requests: "API requests", offline: "Offline", unverified: "Configured locally · unverified", unavailable: "Unavailable",
      connecting: "Connecting", verified: "Live · verified", saved: "Saved locally", notSaved: "Not saved locally",
      tutorialStep: "Tutorial", entryStep: "Choose experience", portalStep: "API Portal",
      hostUnavailable: "The native host is unavailable. Open the built macOS app to continue.",
      requestTimeout: "The host did not respond in time. Reopen the app to recover saved progress.",
      requestFailed: "The action could not be completed. Try again.",
      loading: "Connecting to the local controller…", retry: "Retry connection",
      recordedNotice: "Practice response recorded by the trusted host.",
      waiting: "Working…", noReceipt: "No frozen receipt is available yet.",
      recoveryTitle: "The saved session needs attention",
      recoveryBody: "The host could not safely restore this session. Your saved file has not been replaced. Restart only if you want to delete it and begin again.",
      recoveryReset: "Delete saved session and restart…",
      saveRecoveryBody: "The latest changes are still in memory but could not be saved. Export a recovery copy before deleting or closing this session.",
      recoveryExport: "Export a recovery copy…",
      prepareSetup: "Preview interview configuration · no paid call",
      setupPending: "Configuration preview is available without an API key and makes no model requests. Full interview launch still requires validated questions, execution adapters and host policy guards.",
      configuration: "Interview configuration", environment: "Technical environment",
      duration: "Session duration", minutes: "minutes", questionCount: "Questions · derived from duration",
      hardOnly: "Hard · fixed for real interviews", configNote: "45 minutes requires 3 questions; 60 minutes requires 4. The host validates this contract.",
      continueSetup: "Next →", sourceTitle: "Select question source", sourceLabel: "Question source",
      byoq: "Bring your own question · LeetCode / HackerRank", randomized: "Randomized · approved dataset pool",
      sourceInstructions: "Paste the original LeetCode/HackerRank question without rewriting it into JSON. Choose its source, then Extract → Review/Edit → Confirm. JSON import remains available in Advanced mode.",
      sourceSafety: "Structural review is not SQL execution or hidden-test validation. Missing or conflicting information blocks progression; remaining slots are never silently filled.",
      questionNumber: "Question", emptyTemplate: "Advanced: insert JSON template", bytes: "UTF-8 bytes",
      extractQuestion: "Extract question", confirmQuestion: "Confirm reviewed fields",
      practiceQuestion: "Practise this question with Live AI (unscored)",
      rehearsalStart: "Start 3-question AI rehearsal (unscored)",
      rehearsalSubmit: "Finish question → Next", rehearsalSkip: "Skip question → Next",
      rehearsalFinish: "Finish interview & freeze record", rehearsalComplete: "Three-question rehearsal complete",
      rehearsalNote: "Three confirmed questions, up to four candidate turns each. PostgreSQL SQL can be tested only against separately approved local fixtures; Pandas and competency grading remain unavailable.",
      sourceChoice: "Source", reviewGuidance: "Review and edit extracted fields. Image-only schemas must be entered manually until image import is implemented.",
      reviewIncomplete: "Missing or uncertain fields remain unverified. Final SQL scoring is unavailable.",
      importTooLarge: "This question exceeds the 8192 UTF-8-byte cap. Shorten it before importing.",
      reviewQuestions: "Review questions →", structureReview: "Parsed fields and review issues",
      issues: "Issues", structure: "Structure", executionUnverified: "Execution · UNVERIFIED",
      randomBlocked: "The approved generated-question pool is not available yet. You can review the setup, but question generation, grading and launch remain blocked.",
      mechanismTitle: "Choose interview mechanism", mechanismLabel: "Senior Interviewer mechanism",
      strict: "Strict & Challenging", supportive: "Professional & Supportive",
      strictDetail: "Independent problem-solving first. More restrained intervention, with observed clarification, verified progress and bounded help-seeking.",
      supportiveDetail: "More opportunity to explain reasoning, discuss obstacles and respond to feedback. Correct execution remains mandatory.",
      mechanismGuard: "Both are Senior Technical Interviewers. Neither may reveal protected answers, override the host, manufacture test results or assign final scores.",
      rubricNote: "Technical 60 / Communication 40 is a provisional reference. Evidence remains separate; no numerical score is approved or assigned here.",
      reviewSetup: "Review setup →", reviewTitle: "Review your interview",
      configDigest: "Configuration digest", profileDigest: "Effective instruction provenance",
      blockers: "Launch blockers", launchPreflight: "Check launch requirements",
      questionReviewStatus: "Question review", policyProposal: "Versioned policy · scoring remains provisional",
      setupStep: "Real AI setup", preflightNote: "This check cannot make a paid call. Authentication, independently validated questions and a supported execution adapter are still required.",
    },
    zh: {
      livePreview: "真实模型对话预览", livePreviewNote: "资深面试官多轮交互；技术与沟通能力仍为 NOT_SCORED。经单独审核的 PostgreSQL 本地测试数据可用于验证已提交 SQL。",
      previewQuestion: "已批准的对话题目 · 不评分", verifyPreview: "验证访问并打开预览 · 1 次付费请求",
      previewSelected: "当前面试机制", previewSource: "可在配置预览中选择面试机制；此选项决定实际使用的已批准指令。",
      previewSend: "发送给资深面试官 · 1 次付费请求", previewRetry: "重试已记录的回答 · 1 次付费请求",
      retryRecorded: "你的回答已记录，但尚未提交模型回复。重试会发送同一段已记录文本，并消耗额外 1 次请求；不会自动重试。",
      rehearsalTimeout: "45 分钟已到 · 记录冻结", rehearsalClockHold: "检测到本地时钟异常 · 已停止面试",
      rehearsalClock: "⏱ 显示 / 隐藏面试计时", rehearsalElapsed: "已用时间",
      rehearsalLimit: "总时长硬截止", rehearsalQuestionTime: "当前题耗时",
      rehearsalWaitTime: "等待模型时间", localTimeUncertified: "计时由本机 Host 控制，但本机系统时间不具备第三方防作弊认证；修改系统时间可能中断面试。",
      previewComplete: "预览对话已完成。关闭预览即可冻结记录，不会生成分数。",
      previewClosed: "预览已关闭 · 记录已冻结", closePreview: "关闭预览并冻结记录", cancelRequest: "取消当前请求",
      pendingRequest: "正在等待原生模型请求。取消后，迟到的回复不会被提交；已经发出的请求仍可能产生费用。",
      liveResponse: "资深面试官 · LIVE_MODEL", noLiveResponse: "尚未提交模型回复。",
      previewRecorded: "可信控制器已提交模型回复。", previewInput: "你的预览回答", previewPrivacy: "仅在原生窗口明确同意付费请求后，已提交文本和已批准题目才会发送给所选服务商。本地记录包含你提交的文本。",
      requestsTotal: "本次 App 进程的请求总数", unmeasuredRequests: "用量未知的请求", model: "模型", requestLimit: "请求上限", tokenUsage: "已报告 Token", usageUnknown: "服务商未提供", usageScope: "用量来自服务商报告，不代表费用估算。",
      previewFrozen: "冻结记录保留回复来源和已提交文本。技术能力与沟通未评分；未执行 SQL。",
      providerConsentRequired: "请在原生 API Portal 中授权付费请求后，再验证访问。",
      invalidCredential: "服务商拒绝了此凭证。请重新打开原生 API Portal 更换凭证。",
      modelUnavailable: "此凭证无法访问所选模型。请在原生 API Portal 中选择可用模型。",
      rateLimited: "服务商请求频率达到上限，没有自动重试。",
      usageLimited: "已达到授权请求上限或服务商用量上限，没有自动发起请求。",
      providerTimeout: "模型请求超时，没有提交模型回复。",
      providerRefused: "服务商拒绝了此请求，没有提交模型回复。",
      invalidProviderResponse: "模型回复未通过验证，没有提交模型回复。",
      networkFailure: "无法连接服务商。你的文本仍然保留，仅在你选择后才重试。",
      providerCancelled: "当前请求已取消，迟到的回复无法提交。",
      title: "TECHNICAL INTERVIEW LAB", subtitle: "认真练习，让下一次面试更从容。",
      language: "English", languageLabel: "Switch interface to English", reset: "重新开始 / 删除本地会话",
      entry: "选择你的体验", entryBody: "先熟悉面试流程，再准备真实技术面试。",
      tutorial: "引导教程", tutorialBody: "一道固定的 Medium PostgreSQL 题目，通过模拟反馈熟悉面试。",
      tutorialMeta: "无需 API Key · 无网络请求 · 不评分", start: "开始教程 →",
      real: "真实 AI 面试", realBody: "准备 45 或 60 分钟的面试，由资深面试官主持，包含 3 或 4 道 Hard 题目。",
      realMeta: "先打开原生 API Portal · 需完成真实激活", configure: "开始配置 →",
      privacy: "开始教程后，进度与已提交回答会保存在本机。重新开始将删除本地会话；仅在你选择导出时生成导出文件。",
      welcome: "欢迎，候选人。", welcomeBody: "第一次面试是引导演练。不调用模型，不评分，不付费。",
      welcomeDetail: "练习澄清需求、解释计划、记录 SQL，并体验独立 Trainer 的复盘流程。",
      rules: "面试规则", ruleClock: "可信宿主控制会话时钟与状态流转。",
      ruleHelp: "你可以澄清需求并请求允许范围内的帮助，但不保证获得提示。",
      ruleAnswer: "受保护的答案与隐藏测试不属于面试官可披露的内容。",
      simulation: "教程反馈来自预设脚本，不执行 SQL；Technical Capability 与 Communication 均不评分。",
      next: "明白了 · 下一步 →", understand: "我已了解 →", back: "上一步", skip: "跳过教程 · 真实 AI →",
      question: "你的练习题", medium: "Medium · PostgreSQL · 1 题", schema: "数据表结构",
      questionNote: "此固定教程题用于熟悉流程，没有正在运行的数据库或已验证测试数据。",
      enterRoom: "进入面试室 →", room: "面试室", simulated: "模拟反馈",
      senior: "资深技术面试官", prompt: "编写 SQL 前，请澄清题目要求，并解释如何处理相同日期与 NULL 时间戳。",
      kind: "回答类型", clarify: "澄清问题", plan: "解题计划", implement: "提交 SQL", test: "测试思路 / SQL", help: "请求帮助",
      response: "你的回答", placeholder: "输入澄清问题、解释解题计划，或编写 SQL…",
      shortcut: "⌘ Enter 记录 · 文本由宿主记录，不会在此执行。",
      submit: "记录练习回答", finish: "完成教程 →", recorded: "已记录的对话",
      emptyHistory: "提交后的回答将显示在这里。", candidate: "你", feedback: "模拟面试官",
      technical: "Technical Capability · 技术能力", communication: "Communication · 沟通",
      notScored: "NOT_SCORED · 未评分", execution: "SQL 执行", notRun: "NOT_RUN · 未运行",
      technicalExecution: "技术执行", unverifiedStatus: "UNVERIFIED · 未验证",
      noTests: "SQL 评估器尚未运行。回答被记录不代表测试通过。",
      complete: "教程已完成", completeBody: "你已体验面试流程。技术能力与沟通仍分别保持 NOT_SCORED。",
      trainer: "Trainer 预览", trainerNote: "基于允许读取的冻结记录展示预设辅导，不代表已完成独立能力评估。",
      drill: "针对性练习", followUp: "陌生情境迁移练习", evidence: "关联证据",
      receipt: "冻结回执", receiptNote: "回执记录教程过程和已提交文本。导出内容包含你的回答，请自行决定是否分享。",
      digest: "回执 SHA-256", replay: "重玩教程", explore: "探索真实 AI →", export: "导出回执…",
      api: "激活真实 AI", apiBody: "凭证通过原生安全窗口输入，绝不会传给此网页或 Python 控制器。",
      portal: "打开原生 API Portal…", disconnected: "断开连接", apiGate: "原生激活窗口会要求选择模型、请求上限并明确同意付费请求。保存 Key 不会发起请求，也不代表已验证访问权限。授权请求成功后才会验证连接；完整面试仍禁止启动。",
      requests: "API 请求数", offline: "离线", unverified: "已配置 · 未验证", unavailable: "不可用",
      connecting: "连接中", verified: "已验证 · 在线", saved: "已保存在本机", notSaved: "未保存在本机",
      tutorialStep: "教程", entryStep: "选择体验", portalStep: "API Portal",
      hostUnavailable: "原生宿主不可用。请打开构建后的 macOS App。",
      requestTimeout: "宿主未及时响应。请重新打开 App，恢复已保存的进度。",
      requestFailed: "操作未完成，请重试。", loading: "正在连接本地控制器…", retry: "重新连接",
      recordedNotice: "可信宿主已记录练习回答。",
      waiting: "处理中…", noReceipt: "尚无冻结回执。",
      recoveryTitle: "已保存的会话需要处理",
      recoveryBody: "宿主无法安全恢复此会话，原有文件尚未被覆盖。仅当你希望删除该会话并重新开始时，选择重新开始。",
      recoveryReset: "删除已保存会话并重新开始…",
      saveRecoveryBody: "最新变更仍保留在内存中，但尚未成功保存。请先导出恢复副本，再删除或关闭此会话。",
      recoveryExport: "导出恢复副本…",
      prepareSetup: "预览面试配置 · 不调用付费 API",
      setupPending: "无需 API Key 即可预览配置，此流程不会调用模型。完整面试仍需通过题目验证、执行适配器及宿主策略检查。",
      configuration: "面试配置", environment: "技术环境", duration: "会话时长", minutes: "分钟",
      questionCount: "题目数量 · 根据时长推导", hardOnly: "Hard · 真实面试固定难度",
      configNote: "45 分钟必须为 3 题，60 分钟必须为 4 题。此约束由宿主验证。",
      continueSetup: "下一步 →", sourceTitle: "选择题目来源", sourceLabel: "题目来源",
      byoq: "自带题目 · LeetCode / HackerRank", randomized: "随机面试 · 已批准的数据集题库",
      sourceInstructions: "直接粘贴 LeetCode/HackerRank 原始题目，无需改写 JSON。选择来源后点击提取 → 审阅/编辑 → 确认。高级用户仍可使用 JSON。",
      sourceSafety: "结构审查不代表 SQL 执行或隐藏测试验证。缺失或冲突的信息会阻止继续；剩余题目不会被静默补齐。",
      questionNumber: "题目", emptyTemplate: "高级：插入 JSON 模板", bytes: "UTF-8 字节",
      extractQuestion: "提取题目", confirmQuestion: "确认已审阅字段",
      practiceQuestion: "用真实 AI 练习此题（不评分）",
      rehearsalStart: "开始三题 AI 模拟面试（不评分）",
      rehearsalSubmit: "结束本题并进入下一题", rehearsalSkip: "跳过本题并进入下一题",
      rehearsalFinish: "完成面试并冻结记录", rehearsalComplete: "三题模拟面试已完成",
      rehearsalNote: "三道确认题，每题最多四次交互。SQL 可单独批准本地 PostgreSQL Fixture 执行；Pandas 及综合能力评分仍未开放。",
      sourceChoice: "来源", reviewGuidance: "请核对并修改提取字段。纯图片表结构在图片导入上线前需手动填写。",
      reviewIncomplete: "缺失或不确定字段仍未验证。正式 SQL 评分尚不可用。",
      importTooLarge: "此题超过 8192 UTF-8 字节上限，请缩短后再导入。",
      reviewQuestions: "审查题目 →", structureReview: "已解析字段与审查问题",
      issues: "问题", structure: "结构", executionUnverified: "执行 · UNVERIFIED",
      randomBlocked: "已批准的生成题库尚不可用。可以继续审阅配置，但生成题目、评分与启动仍被阻止。",
      mechanismTitle: "选择面试机制", mechanismLabel: "资深面试官机制",
      strict: "Strict & Challenging · 严格挑战型", supportive: "Professional & Supportive · 专业支持型",
      strictDetail: "优先独立解决问题，面试官更克制地介入；同时观察澄清需求、已验证进展与有边界的求助。",
      supportiveDetail: "提供更多解释推理、讨论障碍并根据反馈采取行动的机会，但正确执行仍是必要条件。",
      mechanismGuard: "两种机制均为资深技术面试官，均不得泄露受保护答案、覆盖宿主决定、捏造测试结果或赋予最终分数。",
      rubricNote: "Technical 60 / Communication 40 仅为暂定参考。证据分别记录；此处不批准或生成数值评分。",
      reviewSetup: "审阅配置 →", reviewTitle: "审阅你的面试",
      configDigest: "配置摘要", profileDigest: "有效指令来源",
      blockers: "启动阻碍", launchPreflight: "检查启动条件",
      questionReviewStatus: "题目审查", policyProposal: "版本化策略 · 评分仍为暂定",
      setupStep: "真实 AI 配置", preflightNote: "此检查不会调用付费 API。仍需完成服务商验证、独立题目验证，并提供受支持的执行适配器。",
    },
  };
  const t = key => (strings[state?.language === "zh" ? "zh" : "en"][key] || key);
  const node = (tag, text, className) => {
    const element = document.createElement(tag);
    if (text !== null && text !== undefined) element.textContent = String(text);
    if (className) element.className = className;
    return element;
  };
  const add = (parent, ...children) => {
    for (const child of children) if (child) parent.appendChild(child);
    return parent;
  };
  function showError(message) {
    errors.textContent = message;
    errors.hidden = false;
  }
  function clearError() {
    errors.hidden = true;
    errors.textContent = "";
  }
  // Display clock is presentation-only. Every 15 seconds the renderer asks the
  // trusted Host for a persisted time checkpoint; no renderer timestamp is sent.
  let clockVisualBaseMs = Date.now();
  let clockDetailsExpanded = false;
  const liveRequestActions = new Set(["preview_verify", "preview_send", "grade_execute"]);
  const interruptActions = new Set(["preview_cancel", "disconnect"]);
  const hasLiveRequest = () => [...pending.values()].some(item => liveRequestActions.has(item.action));
  function setBusy(value) {
    busy = value;
    app.setAttribute("aria-busy", String(value));
    const livePending = hasLiveRequest();
    const interruptPending = [...pending.values()].some(item => interruptActions.has(item.action));
    for (const element of app.querySelectorAll("button, select, textarea")) {
      const mayInterrupt = livePending && !interruptPending && element.dataset.interrupt === "true";
      element.disabled = (value && !mayInterrupt) || element.dataset.unavailable === "true";
    }
    for (const element of app.querySelectorAll("[data-live-pending]")) element.hidden = !livePending;
  }
  function errorText(code) {
    const mapping = {
      INVALID_CREDENTIALS: "invalidCredential", INVALID_CREDENTIAL: "invalidCredential", UNAUTHORIZED: "invalidCredential",
      MODEL_UNAVAILABLE: "modelUnavailable", RATE_LIMIT: "rateLimited", RATE_LIMITED: "rateLimited",
      REQUEST_LIMIT: "usageLimited", REQUEST_BUDGET_EXHAUSTED: "usageLimited", USAGE_LIMIT: "usageLimited",
      TIMEOUT: "providerTimeout", PROVIDER_TIMEOUT: "providerTimeout", REFUSED: "providerRefused",
      INVALID_RESPONSE: "invalidProviderResponse", OVERSIZED_RESPONSE: "invalidProviderResponse",
      REDIRECT_REJECTED: "invalidProviderResponse", NETWORK_ERROR: "networkFailure", TRANSPORT_ERROR: "networkFailure",
      CANCELLED: "providerCancelled", REQUEST_CANCELLED: "providerCancelled",
      PROVIDER_RATE_LIMIT: "rateLimited", PROVIDER_USAGE_LIMIT: "usageLimited", REQUEST_LIMIT_REACHED: "usageLimited",
      PROVIDER_REFUSED: "providerRefused", INVALID_PROVIDER_RESPONSE: "invalidProviderResponse",
      PROVIDER_RESPONSE_TOO_LARGE: "invalidProviderResponse", INCOMPLETE_PROVIDER_RESPONSE: "invalidProviderResponse",
      PROVIDER_REDIRECT_REJECTED: "invalidProviderResponse", PROVIDER_NETWORK_ERROR: "networkFailure",
      PROVIDER_CANCELLED: "providerCancelled", PAID_CONSENT_REQUIRED: "providerConsentRequired",
      LOCAL_CONTROLLER_UNAVAILABLE: "requestTimeout",
      PRACTICE_REQUIRED_FIELDS_MISSING: "reviewGuidance", PRACTICE_REVIEW_REQUIRED: "reviewGuidance",
      QUESTION_REVIEW_REQUIRED: "reviewIncomplete", QUESTION_SLOT_ORDER: "reviewGuidance",
    };
    return t(mapping[code] || "requestFailed");
  }
  function request(action, params = {}) {
    clearError();
    return new Promise((resolve, reject) => {
      const bridge = window.webkit?.messageHandlers?.tia;
      if (!bridge) {
        showError(t("hostUnavailable"));
        reject(new Error("NATIVE_HOST_UNAVAILABLE"));
        return;
      }
      const id = `ui-${++serial}`;
      // Native confirmation and file/credential sheets await the user's decision.
      // Their lifetime is not a provider/worker timeout.
      const awaitsHuman = ["api_portal", "reset", "tutorial_replay", "export"].includes(action);
      // Native code bounds prepare, HTTP and commit individually. A renderer timer
      // must not abandon a paid request while native code may still commit it.
      const timer = awaitsHuman || liveRequestActions.has(action) ? null : setTimeout(() => {
        pending.delete(id);
        setBusy(pending.size > 0);
        showError(t("requestTimeout"));
        reject(new Error("HOST_TIMEOUT"));
      }, 20000);
      pending.set(id, {resolve, reject, timer, action});
      setBusy(true);
      try {
        bridge.postMessage({id, action, params});
      } catch (_) {
        if (timer !== null) clearTimeout(timer);
        pending.delete(id);
        setBusy(pending.size > 0);
        showError(t("hostUnavailable"));
        reject(new Error("NATIVE_HOST_UNAVAILABLE"));
      }
    });
  }
  window.request = request;
  window.tiaReceive = response => {
    if (!response || typeof response !== "object") return;
    const item = pending.get(response.id);
    const unsolicited = response.id === undefined || response.id === null;
    if (!item && !unsolicited) return;
    if (item) {
      if (item.timer !== null) clearTimeout(item.timer);
      pending.delete(response.id);
    }
    const hasState = response.state && typeof response.state === "object" && !Array.isArray(response.state);
    if (hasState) {
      if (response.ok === true && (item?.action === "tutorial_replay" || item?.action === "reset")) {
        draft = "";
        if (item.action === "reset") { questionDrafts = []; questionSources = []; questionFieldDrafts = []; liveDraft = ""; liveKind = "clarify"; }
      }
      if (response.ok === true && item?.action === "preview_verify" && state?.screen !== "LIVE_PREVIEW") { liveDraft = ""; liveKind = "clarify"; }
      state = response.state;
      clockVisualBaseMs = Date.now();
      // Read-only diagnostic copy for native UI tests. It is never submitted as authority.
      window.tiaState = JSON.parse(JSON.stringify(state));
      render();
      document.documentElement.dataset.tiaReady = "true";
    }
    if (response.ok === true && hasState) {
      if (item?.action === "tutorial_submit") announcement.textContent = t("recordedNotice");
      if (item?.action === "preview_send") announcement.textContent = t("previewRecorded");
      item?.resolve(state);
    } else {
      const code = typeof response.error === "string" ? response.error :
        (typeof response.error?.code === "string" ? response.error.code : "HOST_ERROR");
      showError(`${errorText(code)} (${code.slice(0, 100)})`);
      item?.reject(new Error(code));
    }
    setBusy(pending.size > 0);
  };
  function act(action, params = {}) {
    if (busy && (!interruptActions.has(action) || !hasLiveRequest() ||
        [...pending.values()].some(item => interruptActions.has(item.action)))) return;
    request(action, params).catch(() => {});
  }
  function button(id, text, handler, style = "secondary") {
    const result = node("button", text, `button ${style}`);
    result.id = id;
    result.type = "button";
    result.addEventListener("click", handler);
    return result;
  }
  function actions(...buttons) {
    return add(node("div", null, "actions"), ...buttons);
  }
  function badge(text, extra = "") { return node("span", text, `badge ${extra}`); }
  function heading(text) {
    const result = node("h1", text);
    result.id = "screenTitle";
    result.tabIndex = -1;
    return result;
  }
  function nav(nextText) {
    return actions(
      button("back", t("back"), () => act("tutorial_back")),
      nextText ? button("next", nextText, () => act("tutorial_next"), "primary") : null
    );
  }
  function skip() {
    return button("skipTutorial", t("skip"), () => act("choose_real"), "text");
  }
  function entry(main) {
    add(main, heading(t("entry")), node("p", t("entryBody"), "lead"));
    const cards = node("div", null, "choice-grid");
    for (const item of [
      ["GUIDED_ONBOARDING", "tutorial", "tutorialBody", "tutorialMeta", "startTutorial", "start", "tutorial_start", "01"],
      ["REAL_AI_INTERVIEW", "real", "realBody", "realMeta", "realInterview", "configure", "choose_real", "02"],
    ]) {
      const [experience, title, body, meta, id, label, command, numeral] = item;
      const card = node("section", null, "choice-card");
      card.dataset.experience = experience;
      add(card, node("div", numeral, "choice-number"), node("h2", t(title)),
        node("p", t(body), "choice-description"), node("p", t(meta), "muted"),
        button(id, t(label), () => act(command), "primary"));
      cards.appendChild(card);
    }
    add(main, cards, node("p", t("privacy"), "privacy-note"));
  }
  function welcome(main) {
    const cover = node("section", null, "cover");
    add(cover, node("div", "01 / 05", "eyebrow"), heading(t("welcome")),
      node("p", t("welcomeBody"), "lead"), node("p", t("welcomeDetail")));
    add(main, cover, nav(t("next")), skip());
  }
  function rules(main) {
    add(main, badge("02 / 05"), heading(t("rules")));
    const list = node("ul", null, "rule-list");
    ["ruleClock", "ruleHelp", "ruleAnswer"].forEach((key, index) => {
      add(list, add(node("li"), node("span", String(index + 1).padStart(2, "0"), "rule-number"), node("p", t(key))));
    });
    add(main, list, node("p", t("simulation"), "notice"), nav(t("understand")), skip());
  }
  function questionCard(compact = false, previewQuestion = null) {
    const q = previewQuestion || state.question || {};
    const card = node("section", null, `question-card${compact ? " compact" : ""}`);
    add(card, badge(t(previewQuestion ? "previewQuestion" : "medium")), node(compact ? "h3" : "h2", q.title || "First Order per Customer"),
      node("p", q.statement || "", "question-statement"), node("h3", t("schema")),
      add(node("pre", null, "code-block"), node("code", q.schema || "")));
    return card;
  }
  function question(main) {
    add(main, heading(t("question")), questionCard(), node("p", t("questionNote"), "notice"),
      nav(t("enterRoom")), skip());
  }
  function candidateEvents() {
    return (state.session?.events || []).filter(event => event.actor === "candidate");
  }
  function scores(forSetup = false) {
    const grid = node("div", null, "evidence-grid");
    const graded = state.screen === "LIVE_PREVIEW" && state.live_preview?.sql_accuracy?.correctness === "VERIFIED_LOCAL_FIXTURE";
    for (const [name, status] of [["technical", "notScored"], ["communication", "notScored"],
      forSetup ? ["technicalExecution", "unverifiedStatus"] : ["execution", graded ? "localFixtureRun" : "notRun"]]) {
      add(grid, add(node("div", null, "evidence-item"), node("span", t(name), "muted"), node("strong", t(status))));
    }
    return grid;
  }
  function conversation(session = state.session, isLive = false) {
    const box = node("section", null, "conversation");
    add(box, node("h2", t("recorded")));
    const events = (session?.events || []).filter(event =>
      event.actor === "candidate" || (event.actor === "interviewer" && event.kind === "reply"));
    if (!events.length) add(box, node("p", t("emptyHistory"), "muted"));
    for (const event of events) {
      const candidate = event.actor === "candidate";
      const payload = event.payload || {};
      const text = typeof payload.text === "string" ? payload.text : "";
      if (!text) continue;
      const entry = node("div", null, `transcript-entry ${candidate ? "candidate" : "interviewer"}`);
      add(entry, node("div", candidate ? `${t("candidate")} · ${t(event.kind || "response")}` : t(isLive && event.provenance === "LIVE_MODEL" ? "liveResponse" : "feedback"), "transcript-speaker"),
        node("p", text, "transcript-text"));
      box.appendChild(entry);
    }
    return box;
  }
  function room(main) {
    add(main, add(node("div", null, "title-row"), heading(t("room")), badge(t("simulated"), "accent")));
    const columns = node("div", null, "room-grid");
    const questionSide = node("aside", null, "question-side");
    add(questionSide, questionCard(true), node("p", t("noTests"), "notice"));
    const work = node("section", null, "work-side");
    add(work, add(node("div", null, "interviewer-prompt"), node("h2", t("senior")), node("p", state.feedback || t("prompt"))));
    const kindLabel = node("label", t("kind"));
    kindLabel.htmlFor = "responseKind";
    const select = node("select");
    select.id = "responseKind";
    for (const value of ["clarify", "plan", "implement", "test", "help"]) {
      const option = node("option", t(value)); option.value = value; select.appendChild(option);
    }
    select.value = draftKind;
    select.addEventListener("change", () => { draftKind = select.value; });
    const responseLabel = node("label", t("response"));
    responseLabel.htmlFor = "response";
    const input = node("textarea");
    input.id = "response";
    input.rows = 8;
    input.maxLength = 8192;
    input.spellcheck = false;
    input.autocapitalize = "off";
    input.placeholder = t("placeholder");
    input.value = draft;
    input.setAttribute("aria-describedby", "responseHelp");
    input.addEventListener("input", () => { draft = input.value; });
    const helper = node("p", t("shortcut"), "field-help");
    helper.id = "responseHelp";
    const submit = () => act("tutorial_submit", {kind: select.value, text: input.value});
    input.addEventListener("keydown", event => {
      if ((event.metaKey || event.ctrlKey) && event.key === "Enter") { event.preventDefault(); if (!busy) submit(); }
    });
    add(work, kindLabel, select, responseLabel, input, helper,
      button("submitResponse", t("submit"), submit, "primary full-width"));
    add(columns, questionSide, work);
    add(main, columns, conversation(), scores());
    const finish = button("finishTutorial", t("finish"), () => act("tutorial_complete"), "primary");
    if (!candidateEvents().length) {
      finish.disabled = true;
      finish.dataset.unavailable = "true";
    }
    add(main, actions(button("back", t("back"), () => act("tutorial_back")), finish), skip());
  }
  function complete(main) {
    const preview = state.trainer_preview;
    const receipt = state.session?.receipt;
    add(main, add(node("section", null, "cover compact-cover"),
      node("div", "05 / 05", "eyebrow"), heading(t("complete")), node("p", t("completeBody"), "lead")), scores());
    if (preview) {
      const card = node("section", null, "trainer-card");
      add(card, badge(t("simulated"), "accent"), node("h2", t("trainer")), node("h3", t("drill")),
        node("p", preview.text || ""), node("h3", t("followUp")), node("p", preview.follow_up || ""),
        node("p", t("trainerNote"), "muted"));
      if (Array.isArray(preview.evidence_ids) && preview.evidence_ids.length) {
        add(card, node("p", `${t("evidence")}: ${preview.evidence_ids.join(", ")}`, "digest"));
      }
      add(main, card);
    }
    const frozen = node("section", null, "receipt-card");
    add(frozen, node("h2", t("receipt")), node("p", t("receiptNote"), "muted"));
    if (receipt) {
      add(frozen, node("span", t("digest"), "eyebrow"), node("code", receipt.sha256 || "", "digest"),
        button("exportReceipt", t("export"), () => act("export")));
    } else add(frozen, node("p", t("noReceipt")));
    add(main, frozen, actions(button("replayTutorial", t("replay"), () => act("tutorial_replay")),
      button("realInterview", t("explore"), () => act("choose_real"), "primary")));
  }
  function interruptButton(id, label, action) {
    const control = button(id, label, () => act(action));
    control.dataset.interrupt = "true";
    return control;
  }
  function providerDetails() {
    const activation = state.activation || {};
    const detail = node("div", null, "provider-details");
    detail.id = "providerDetails";
    const limit = Number.isInteger(activation.request_limit) ? activation.request_limit : null;
    add(detail, node("p", `${t("requests")}: ${requestCount()}${limit !== null ? ` / ${limit}` : ""}`));
    if (typeof activation.model === "string" && activation.model) add(detail, node("p", `${t("model")}: ${activation.model}`));
    if (Number.isInteger(activation.requests_total)) add(detail, node("p", `${t("requestsTotal")}: ${activation.requests_total}`));
    if (Number.isInteger(activation.requests_without_measured_usage)) add(detail, node("p", `${t("unmeasuredRequests")}: ${activation.requests_without_measured_usage}`));
    const usage = activation.usage;
    const knownUsage = usage && ["input_tokens", "output_tokens", "total_tokens"].every(key => Number.isInteger(usage[key]) && usage[key] >= 0);
    add(detail, node("p", `${t("tokenUsage")}: ${knownUsage ? `${usage.input_tokens} input · ${usage.output_tokens} output · ${usage.total_tokens} total` : t("usageUnknown")}`),
      node("p", t("usageScope"), "field-help"));
    if (activation.error_code) add(detail, node("p", errorText(activation.error_code), "notice"));
    return detail;
  }
  function formatElapsed(seconds) {
    const total = Math.max(0, Math.floor(Number(seconds) || 0));
    return `${String(Math.floor(total / 60)).padStart(2, "0")}:${String(total % 60).padStart(2, "0")}`;
  }
  function rehearsalClock() {
    const rehearsal = state.rehearsal;
    const record = rehearsal?.timing;
    if (!record) return null;
    const detail = node("details", null, "rehearsal-clock");
    detail.id = "rehearsalClock";
    detail.open = clockDetailsExpanded;
    detail.addEventListener("toggle", () => { clockDetailsExpanded = detail.open; });
    add(detail, node("summary", t("rehearsalClock")));
    const active = rehearsal.status === "ACTIVE" && record.started === true;
    const shown = node("strong", "", "rehearsal-elapsed");
    shown.id = "hostClockElapsed";
    shown.dataset.hostElapsed = String(record.elapsed_seconds);
    shown.dataset.limit = String(record.limit_seconds);
    shown.dataset.active = String(active);
    const current = record.questions?.[Math.min(2, record.current_question)] || {};
    add(detail, shown,
      node("p", `${t("rehearsalLimit")}: ${formatElapsed(record.limit_seconds)}`, "field-help"),
      node("p", `${t("rehearsalQuestionTime")}: ${formatElapsed(current.elapsed_seconds || 0)}`, "field-help"),
      node("p", `${t("rehearsalWaitTime")}: ${formatElapsed(record.model_wait_seconds || 0)}`, "field-help"),
      node("p", t("localTimeUncertified"), "field-help"));
    if (record.integrity !== "LOCAL_UNATTESTED") {
      add(detail, node("p", record.integrity, "notice"));
    }
    return detail;
  }
  function updateClockDisplay() {
    const display = document.getElementById("hostClockElapsed");
    if (!display) return;
    const elapsed = Number(display.dataset.hostElapsed) || 0;
    const limit = Number(display.dataset.limit) || 2700;
    const active = display.dataset.active === "true";
    // This interpolation is VISUAL ONLY and has zero Host authority.
    const interpolated = active ? Math.min(limit, elapsed + (Date.now() - clockVisualBaseMs) / 1000) : elapsed;
    display.textContent = `${t("rehearsalElapsed")}: ${formatElapsed(interpolated)}`;
  }
  function previewStartCard() {
    const card = node("section", null, "preview-start-card");
    const mechanism = state.setup_config?.interviewer_mechanism || "STRICT_CHALLENGING";
    add(card, node("h2", t("livePreview")), node("p", t("livePreviewNote")),
      (state.practice_question || (state.rehearsal?.status === "ACTIVE" ? state.rehearsal.questions[state.rehearsal.current_index] : null))
        ? node("p", `${(state.practice_question || state.rehearsal.questions[state.rehearsal.current_index]).title} · ${(state.practice_question || state.rehearsal.questions[state.rehearsal.current_index]).environment}`, "notice") : null,
      node("p", `${t("previewSelected")}: ${t(mechanism === "STRICT_CHALLENGING" ? "strict" : "supportive")}`, "notice"),
      node("p", t("previewSource"), "field-help"));
    const verify = button("verifyPreview", t("verifyPreview"), () => act("preview_verify"), "primary full-width");
    const enabled = state.activation?.live_enabled === true;
    verify.dataset.unavailable = String(!enabled);
    verify.disabled = !enabled;
    add(card, verify);
    if (state.live_preview && !state.live_preview.closed) {
      add(card, button("closeExistingPreview", t("closePreview"), () => act("preview_close")));
    }
    if (!enabled) add(card, node("p", t("providerConsentRequired"), "field-help"));
    return card;
  }
  function apiPortal(main) {
    add(main, badge(t("portalStep")), heading(t("api")), node("p", t("apiBody"), "lead"));
    const card = node("section", null, "portal-card");
    add(card, node("h2", "OpenAI"), badge(modelLabel()), node("p", t("apiGate"), "notice"), providerDetails(),
      actions(button("openPortal", t("portal"), () => act("api_portal"), "primary"),
        interruptButton("disconnect", t("disconnected"), "disconnect")),
      previewStartCard(), node("p", t("setupPending"), "notice"),
      button("prepareSetup", t("prepareSetup"), () => act("setup_continue"), "secondary full-width"));
    if (state.rehearsal?.timing) add(main, rehearsalClock());
    add(main, card, nav());
  }
  function previewProvenance(profile) {
    if (!profile) return null;
    const detail = node("details", null, "question-review");
    add(detail, node("summary", t("profileDigest")), node("code", profile.sha256 || "UNVERIFIED", "digest"),
      node("p", profile.policy_version || "", "digest"));
    const list = node("ul", null, "source-digests");
    for (const [path, hash] of Object.entries(profile.source_sha256 || {})) {
      add(list, add(node("li"), node("span", path), node("code", hash, "digest")));
    }
    add(detail, list);
    return detail;
  }
  function gradingPanel() {
    const rehearsal = state.rehearsal;
    const preview = state.live_preview;
    if (rehearsal?.status !== "ACTIVE" || state.setup_config?.technical_environment !== "POSTGRESQL" || !preview) return null;
    const qhash = preview.question?.content_sha256 || "";
    if (qhash !== gradeQuestionHash) {
      gradeQuestionHash = qhash;
      gradeFixtureDraft = "";
      gradeFixtureApproved = false;
    }
    const area = node("section", null, "receipt-card"); area.id = "gradePanel";
    add(area, node("h2", t("gradeTitle")), node("p", t("gradeNote"), "notice"),
      node("p", t("gradeResultDisclaimer"), "field-help"),
      node("p", t("gradeCurrentQuestion"), "eyebrow"), node("code", qhash, "digest"));
    const impl = (preview.session?.events || []).filter(e => e.actor === "candidate" && e.kind === "implement");
    if (!impl.length) {
      add(area, node("p", t("gradeRequiresSQL"), "notice"));
      return area;
    }
    const last = impl[impl.length - 1];
    add(area, node("p", `Submitted code evidence: ${last.id}`, "field-help"));
    const reviewed = state.grading_review;
    // A new SQL submission, candidate event or Fixture must get fresh consent.
    // Merely re-rendering an unchanged, reviewed Fixture keeps the same choice.
    const approvalBinding = reviewed ? [reviewed.question_sha256, reviewed.candidate_event_id,
      reviewed.candidate_sql_sha256, reviewed.fixture_sha256].join(":") : "";
    if (gradeApprovalBinding !== approvalBinding) {
      gradeApprovalBinding = approvalBinding;
      gradeFixtureApproved = false;
    }
    const receipt = preview.sql_accuracy;
    if (receipt) {
      add(area, node("h3", t("gradeStatus")),
        node("p", `${receipt.result?.status || "NOT_VERIFIED"} · ${receipt.passed_fixtures || 0}/${receipt.total_approved_fixtures || 0} local fixture(s)`),
        node("p", `${receipt.result?.reason || receipt.result?.error_code || ""} · ${receipt.correctness || "NOT_VERIFIED"}`),
        node("code", receipt.candidate_sql_sha256 || "", "digest"));
      if (receipt.correctness === "VERIFIED_LOCAL_FIXTURE") return area;
    }
    const label = node("label", "Human-reviewed Fixture JSON (maximum 12,000 UTF-8 bytes)"); label.htmlFor = "gradeFixture";
    const box = node("textarea"); box.id = "gradeFixture"; box.rows = 8;
    box.value = gradeFixtureDraft; box.spellcheck = false;
    const inspect = button("inspectFixture", t("gradeInspect"), () => act("grade_inspect", {fixture_json: box.value}), "secondary");
    const validate = () => {
      // Preserve the field-level precondition across setBusy(false), which
      // otherwise re-enables every button after a Host snapshot/response.
      const unavailable = !box.value.trim() || new TextEncoder().encode(box.value).length > 12000;
      inspect.dataset.unavailable = String(unavailable);
      inspect.disabled = busy || unavailable;
    };
    box.addEventListener("input", () => { gradeFixtureDraft = box.value; gradeFixtureApproved = false; validate(); });
    validate();
    add(area, label, box, inspect);
    if (reviewed && reviewed.candidate_event_id === last.id && reviewed.question_sha256 === qhash) {
      add(area, node("p", `${reviewed.fixture_id} · ${reviewed.expected_row_count} expected row(s)`, "field-help"),
        node("code", reviewed.fixture_sha256, "digest"),
        node("p", `Tables: ${reviewed.table_summary.map(x => `${x.name} (${x.rows})`).join(", ")}`, "field-help"));
      const approve = node("input"); approve.type = "checkbox"; approve.id = "gradeApprove";
      approve.checked = gradeFixtureApproved;
      const checkLabel = node("label", t("gradeExpected")); checkLabel.htmlFor = "gradeApprove";
      const execute = button("executeGrade", t("gradeExecute"),
        () => act("grade_execute", {fixture_sha256: reviewed.fixture_sha256}), "primary");
      // No execution before explicit approval, including after a snapshot,
      // language change, or any other render/setBusy(false) cycle.
      execute.dataset.unavailable = String(!gradeFixtureApproved);
      execute.disabled = busy || !gradeFixtureApproved;
      approve.addEventListener("change", () => {
        gradeFixtureApproved = approve.checked;
        execute.dataset.unavailable = String(!gradeFixtureApproved);
        execute.disabled = busy || !gradeFixtureApproved;
      });
      add(area, approve, checkLabel, execute, node("p", t("gradePending"), "field-help"));
    }
    return area;
  }

  function livePreview(main) {
    const preview = state.live_preview || {};
    add(main, add(node("div", null, "title-row"), heading(t("livePreview")), badge(modelLabel(), "accent")),
      node("p", t("livePreviewNote"), "lead"), providerDetails());
    const columns = node("div", null, "room-grid");
    add(columns, add(node("aside", null, "question-side"), questionCard(true, preview.question || {}),
      node("p", preview.sql_accuracy?.correctness === "VERIFIED_LOCAL_FIXTURE" ? t("gradeResultDisclaimer") : t("noTests"), "notice")));
    const work = node("section", null, "work-side");
    add(work, node("h2", t("senior")),
      node("p", t(preview.mechanism === "PROFESSIONAL_SUPPORTIVE" ? "supportive" : "strict"), "muted"));
    if (preview.closed) {
      add(work, node("h2", t("previewClosed")), node("p", t("previewFrozen")));
    } else if (preview.can_send || preview.pending || preview.retry_input) {
      const retry = preview.retry_input;
      const kind = selectField("previewKind", t("kind"),
        ["clarify", "plan", "help", "implement"].map(value => [value, t(value)]), retry?.kind || liveKind);
      kind.select.addEventListener("change", () => { liveKind = kind.select.value; });
      kind.select.dataset.unavailable = String(Boolean(retry));
      const label = node("label", t("previewInput")); label.htmlFor = "previewResponse";
      const input = node("textarea"); input.id = "previewResponse"; input.rows = 8;
      input.maxLength = 4096; input.spellcheck = false; input.autocapitalize = "off";
      input.value = retry?.text ?? liveDraft; input.placeholder = t("placeholder"); input.readOnly = Boolean(retry);
      input.setAttribute("aria-describedby", "previewResponseHelp");
      const helper = node("p", retry ? t("retryRecorded") : t("previewPrivacy"), "field-help"); helper.id = "previewResponseHelp";
      const send = () => act("preview_send", {kind: kind.select.value, text: input.value});
      const submit = button("sendPreview", t(retry ? "previewRetry" : "previewSend"), send, "primary full-width");
      const inputSize = node("p", "", "field-help");
      const validateInput = () => {
        const size = new TextEncoder().encode(input.value).length;
        inputSize.textContent = `${size} / 4096 ${t("bytes")}`;
        input.setAttribute("aria-invalid", String(size > 4096));
        const unavailable = !preview.can_send || state.activation?.live_enabled !== true || state.activation?.authenticated !== true || size > 4096 || !input.value.trim();
        submit.dataset.unavailable = String(unavailable);
        submit.disabled = busy || unavailable;
      };
      input.addEventListener("input", () => { liveDraft = input.value; validateInput(); });
      validateInput();
      input.addEventListener("keydown", event => {
        if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
          event.preventDefault(); if (!busy && submit.dataset.unavailable !== "true") send();
        }
      });
      add(work, kind.field, label, input, inputSize, helper, submit);
    } else add(work, node("p", t("previewComplete"), "notice"));
    add(columns, work);
    if (state.rehearsal?.timing) add(main, rehearsalClock());
    if (state.rehearsal?.status === "ACTIVE") {
      const rs = state.rehearsal;
      add(main, node("p", `Question ${rs.current_index + 1} / ${rs.question_count} · ${preview.candidate_turns_used} / ${preview.candidate_turn_limit} candidate turns`, "notice"));
    }
    add(main, columns, conversation(preview.session, true), gradingPanel(), scores(), previewProvenance(preview.prompt_provenance));
    if (preview.session?.receipt) {
      const receipt = preview.session.receipt;
      add(main, add(node("section", null, "receipt-card"), node("h2", t("receipt")), node("p", t("previewFrozen")),
        node("span", t("digest"), "eyebrow"), node("code", receipt.sha256 || "", "digest"),
        button("exportPreview", t("export"), () => act("export"))));
    }
    if (!preview.closed && state.activation?.authenticated !== true) {
      const verify = button("verifyPreview", t("verifyPreview"), () => act("preview_verify"), "primary full-width");
      verify.dataset.unavailable = String(state.activation?.live_enabled !== true);
      add(main, verify);
      if (state.activation?.live_enabled !== true) add(main, node("p", t("providerConsentRequired"), "notice"));
    }
    if (state.rehearsal?.status === "ACTIVE") {
      const final = state.rehearsal.current_index === 2;
      add(main, actions(
        button("finishRehearsalQuestion", t(final ? "rehearsalFinish" : "rehearsalSubmit"),
          () => act("rehearsal_submit"), "primary"),
        button("skipRehearsalQuestion", t("rehearsalSkip"), () => act("rehearsal_skip"), "secondary")));
    }
    add(main, actions(button("openPortal", t("portal"), () => act("api_portal")),
      interruptButton("disconnect", t("disconnected"), "disconnect")),
      state.rehearsal?.status === "ACTIVE" ? null :
      actions(preview.closed ? button("realInterview", t("portalStep"), () => act("choose_real")) :
        button("closePreview", t("closePreview"), () => act("preview_close"), "primary")));
  }
  function rehearsalComplete(main) {
    const rs = state.rehearsal || {};
    const finalTitle = rs.status === "TIMED_OUT" ? "rehearsalTimeout" :
      rs.status === "CLOCK_INTEGRITY_HOLD" ? "rehearsalClockHold" : "rehearsalComplete";
    add(main, heading(t(finalTitle)), node("p", t("rehearsalNote"), "notice"));
    if (rs.timing) add(main, rehearsalClock());
    (rs.results || []).forEach((r, i) => {
      const question = rs.questions?.[i] || {};
      add(main, add(node("section", null, "receipt-card"),
        node("h2", `${i + 1}. ${question.title || "Question"}`),
        node("p", `${r.outcome} · ${r.execution_status || "NOT_RUN"} · NOT_SCORED`),
        r.time_metrics ? node("p", `${t("rehearsalElapsed")}: ${formatElapsed(r.time_metrics.elapsed_seconds)} · ${t("rehearsalWaitTime")}: ${formatElapsed(r.time_metrics.model_wait_seconds)}`, "field-help") : null,
        r.behavior_metrics ? node("p", `${r.behavior_metrics.candidate_turn_count} candidate turns · ${r.behavior_metrics.clarification_requests} clarifications · ${r.behavior_metrics.help_requests} help requests · ${r.behavior_metrics.code_submissions} code submissions · ${r.behavior_metrics.correctness || "NOT_VERIFIED"}`, "field-help") : null,
        node("p", `${r.session?.events?.filter(e => e.actor === "candidate").length || 0} candidate turns`),
        r.sql_accuracy ? node("p", `${t("gradeStatus")}: ${r.sql_accuracy.result?.status || "NOT_VERIFIED"} · ${r.sql_accuracy.passed_fixtures || 0}/${r.sql_accuracy.total_approved_fixtures || 0} local fixture(s)`, "notice") : node("p", t("gradeUnverified"), "field-help"),
        r.session?.receipt?.sha256 ? node("code", r.session.receipt.sha256, "digest") : null));
    });
    add(main, button("exportRehearsal", t("export"), () => act("export"), "primary"));
  }
  function configValues(overrides = {}) {
    const current = state.setup_config || {};
    return {
      technical_environment: current.technical_environment || "POSTGRESQL",
      duration_minutes: current.duration_minutes || 45,
      difficulty: "HARD",
      question_source: current.question_source || "BYOQ",
      interviewer_mechanism: current.interviewer_mechanism || "STRICT_CHALLENGING",
      ...overrides,
    };
  }
  function setupNotice(main) {
    add(main, node("p", t("setupPending"), "setup-warning"));
  }
  function selectField(id, labelText, values, value) {
    const field = node("div", null, "setup-field");
    const label = node("label", labelText); label.htmlFor = id;
    const select = node("select"); select.id = id;
    values.forEach(([key, text]) => {
      const option = node("option", text);
      option.value = String(key);
      select.appendChild(option);
    });
    select.value = String(value);
    add(field, label, select);
    return {field, select};
  }
  function setupNav(nextButton) {
    return actions(button("setupBack", t("back"), () => act("setup_back")), nextButton);
  }
  function configuration(main) {
    const config = configValues();
    add(main, heading(t("configuration")));
    setupNotice(main);
    const grid = node("div", null, "setup-grid");
    const environment = selectField("technicalEnvironment", t("environment"),
      [["POSTGRESQL", "PostgreSQL"], ["PANDAS", "Python / Pandas"]], config.technical_environment);
    const duration = selectField("durationMinutes", t("duration"),
      [[45, `45 ${t("minutes")}`], [60, `60 ${t("minutes")}`]], config.duration_minutes);
    const count = node("strong", config.duration_minutes === 60 ? "4" : "3", "derived-count");
    count.id = "derivedQuestionCount";
    count.setAttribute("aria-live", "polite");
    duration.select.addEventListener("change", () => { count.textContent = duration.select.value === "60" ? "4" : "3"; });
    add(grid, environment.field, duration.field,
      add(node("div", null, "setup-stat"), node("span", t("questionCount"), "muted"), count),
      add(node("div", null, "setup-stat"), node("span", t("hardOnly"), "muted"), node("strong", "HARD", "derived-count")));
    add(main, grid, node("p", t("configNote"), "notice"),
      setupNav(button("nextSetup", t("continueSetup"), () => act("setup_config", {config: configValues({
        technical_environment: environment.select.value, duration_minutes: Number(duration.select.value),
      })}), "primary")));
  }
  function questionReview(review, index) {
    if (!review) return null;
    const detail = node("details", null, "question-review");
    add(detail, node("summary", `${t("structureReview")} · ${index + 1}`),
      node("p", `${t("structure")}: ${review.structure_status || "NEEDS_REVIEW"} · ${t("executionUnverified")}`, "muted"));
    const fields = node("dl", null, "review-fields");
    for (const [key, value] of Object.entries(review.fields || {})) {
      add(fields, node("dt", key), node("dd", typeof value === "string" ? value : JSON.stringify(value)));
    }
    add(detail, fields);
    if (Array.isArray(review.issues) && review.issues.length) {
      const issues = node("ul", null, "issues-list");
      review.issues.forEach(issue => add(issues, node("li", typeof issue === "string" ? issue : `${issue.field}: ${issue.code}`)));
      add(detail, node("h3", t("issues")), issues);
      detail.open = true;
    }
    if (review.provenance) {
      add(detail, node("p", `${review.provenance.kind || "USER_PASTED"} · ${review.provenance.source || "UNSPECIFIED"}`, "digest"));
    }
    return detail;
  }
  const REVIEW_FIELDS = ["problem_statement", "task", "schema", "example_input", "expected_output",
    "environment", "source", "constraints", "source_reference"];
  function editableQuestion(section, review, index) {
    if (!review) return;
    const sha = review.raw_sha256;
    if (!questionFieldDrafts[index] || questionFieldDrafts[index].raw_sha256 !== sha) {
      questionFieldDrafts[index] = {raw_sha256: sha, fields: {...review.fields}};
    }
    const edit = questionFieldDrafts[index].fields;
    const form = node("div", null, "review-editor");
    add(form, node("p", t("reviewGuidance"), "field-help"));
    for (const key of REVIEW_FIELDS) {
      const label = node("label", key); label.htmlFor = `reviewField${index}_${key}`;
      const input = node("textarea"); input.id = label.htmlFor;
      input.rows = key === "problem_statement" || key === "schema" ? 5 : 2;
      input.value = edit[key] || ""; input.spellcheck = false;
      input.addEventListener("input", () => { edit[key] = input.value; });
      add(form, label, input);
    }
    const confirm = button(`confirmQuestion${index}`, t("confirmQuestion"), () =>
      act("setup_question_confirm", {index, fields: {...edit}, raw_sha256: sha}), "primary");
    const buttons = actions(confirm);
    if (review.practice_eligible && review.human_confirmed) {
      add(buttons, button(`practiceQuestion${index}`, t("practiceQuestion"), () =>
        act("practice_start", {index, content_sha256: review.content_sha256}), "secondary"));
    }
    add(section, form, buttons);
  }
  function rehearsalStartButton() {
    const eligible = state.setup_config?.duration_minutes === 45 &&
      state.setup_config?.question_source === "BYOQ" &&
      state.setup_questions?.length === 3 &&
      state.setup_questions.every(q => q.practice_eligible && q.human_confirmed) &&
      new Set(state.setup_questions.map(q => q.content_sha256)).size === 3;
    const start = button("startRehearsal", t("rehearsalStart"), () => act("rehearsal_start"), "secondary full-width");
    start.dataset.unavailable = String(!eligible);
    start.disabled = busy || !eligible;
    return add(node("section", null, "preview-start-card"),
      node("h2", t("rehearsalStart")), node("p", t("rehearsalNote"), "field-help"), start);
  }
  function questionSource(main) {
    const config = configValues();
    const count = state.setup_config?.question_count || (config.duration_minutes === 60 ? 4 : 3);
    add(main, heading(t("sourceTitle")));
    setupNotice(main);
    const source = selectField("questionSource", t("sourceLabel"),
      [["BYOQ", t("byoq")], ["RANDOM_GENERATED", t("randomized")]], config.question_source);
    source.select.addEventListener("change", () => act("setup_config", {config: configValues({question_source: source.select.value})}));
    add(main, source.field);
    const nextButton = button("reviewQuestions", t("reviewQuestions"), () => {
      if (config.question_source !== "BYOQ") {
        act("setup_questions_finish"); return;
      }
      // Preserve the original batch path for already-valid legacy fixtures.
      const all = Array.from({length: count}, (_, index) => questionDrafts[index] || "");
      const legacy = all.every(text => !text.trim() || (new TextEncoder().encode(text).length <= 4096 &&
        (text.trim().startsWith("{") || /^Problem Statement:/i.test(text.trim()))));
      if (legacy && !(state.setup_questions || []).some(review => review.human_confirmed)) {
        act("setup_questions", {questions: all});
      } else {
        act("setup_questions_finish");
      }
    }, "primary");
    if (config.question_source === "BYOQ") {
      add(main, node("p", t("sourceInstructions"), "notice"), node("p", t("sourceSafety"), "notice"));
      const utf8 = value => new TextEncoder().encode(value).length;
      const validateSizes = () => {
        const tooLarge = Array.from({length: count}, (_, index) => utf8(questionDrafts[index] || "")).some(size => size > 8192);
        nextButton.dataset.unavailable = String(tooLarge);
        nextButton.disabled = busy || tooLarge;
      };
      for (let index = 0; index < count; index++) {
        const review = state.setup_questions?.[index];
        if (questionDrafts[index] === undefined) {
          questionDrafts[index] = typeof review?.raw_input === "string" ? review.raw_input :
            review?.fields ? JSON.stringify(review.fields, null, 2) : "";
        }
        const section = node("section", null, "byoq-card");
        const label = node("label", `${t("questionNumber")} ${index + 1} / ${count} · HARD (formal session)`);
        label.htmlFor = `byoqQuestion${index}`;
        const input = node("textarea");
        input.id = `byoqQuestion${index}`;
        input.rows = 10;
        input.spellcheck = false;
        input.autocapitalize = "off";
        input.value = questionDrafts[index];
        const src = selectField(`byoqSource${index}`, t("sourceChoice"),
          [["LEETCODE", "LeetCode"], ["HACKERRANK", "HackerRank"], ["OWNER", "Other / own question"]],
          questionSources[index] || review?.fields?.source || "LEETCODE");
        src.select.addEventListener("change", () => { questionSources[index] = src.select.value; });
        const size = node("p", null, "field-help");
        size.id = `byoqSize${index}`;
        input.setAttribute("aria-describedby", size.id);
        const updateSize = () => {
          const length = utf8(input.value);
          size.textContent = `${length} / 8192 ${t("bytes")}${length > 8192 ? ` · ${t("importTooLarge")}` : ""}`;
          input.setAttribute("aria-invalid", String(length > 8192));
          validateSizes();
          if (typeof extract !== "undefined") extract.disabled = busy || !input.value.trim() || length > 8192;
          if (review && typeof review.raw_input === "string") {
            const changed = review.raw_input !== input.value;
            const confirmation = section.querySelector(`#confirmQuestion${index}`);
            const practice = section.querySelector(`#practiceQuestion${index}`);
            if (confirmation) confirmation.disabled = changed;
            if (practice) practice.disabled = changed;
          }
        };
        input.addEventListener("input", () => { questionDrafts[index] = input.value; updateSize(); });
        const extract = button(`extractQuestion${index}`, t("extractQuestion"), () => {
          questionFieldDrafts[index] = null;
          act("setup_question_set", {index, raw_text: input.value, source: src.select.value});
        }, "primary");
        const template = button(`questionTemplate${index}`, t("emptyTemplate"), () => {
          if (busy) return;
          input.value = JSON.stringify({
            problem_statement: "", task: "", schema: "", example_input: "", expected_output: "",
            environment: config.technical_environment, source: "OWNER", constraints: "", source_reference: "",
          }, null, 2);
          questionDrafts[index] = input.value;
          src.select.value = "OWNER";
          questionSources[index] = "OWNER";
          updateSize();
          input.focus();
        }, "text");
        add(section, label, src.field, input, size, actions(extract, template), questionReview(review, index));
        editableQuestion(section, review, index);
        add(main, section);
        updateSize();
        extract.disabled = busy || !input.value.trim() || utf8(input.value) > 8192;
      }
      validateSizes();
    } else {
      add(main, node("p", t("randomBlocked"), "setup-warning"));
    }
    if (config.question_source === "BYOQ" && config.duration_minutes === 45) {
      add(main, rehearsalStartButton());
    }
    if (state.setup_allocation) {
      const detail = node("p", `${state.setup_allocation.provided_count} / ${state.setup_allocation.required_count} · ${t("executionUnverified")}`, "notice");
      detail.id = "questionAllocation";
      add(main, detail);
      if (state.setup_allocation.issues?.length) add(main, issueList(state.setup_allocation.issues));
    }
    add(main, setupNav(nextButton));
  }
  function mechanism(main) {
    const config = configValues();
    add(main, heading(t("mechanismTitle")));
    setupNotice(main);
    const field = selectField("interviewerMechanism", t("mechanismLabel"),
      [["STRICT_CHALLENGING", t("strict")], ["PROFESSIONAL_SUPPORTIVE", t("supportive")]], config.interviewer_mechanism);
    const choices = node("div", null, "choice-grid mechanism-cards");
    add(choices,
      add(node("section", null, "choice-card"), node("h2", t("strict")), node("p", t("strictDetail"))),
      add(node("section", null, "choice-card"), node("h2", t("supportive")), node("p", t("supportiveDetail"))));
    add(main, field.field, choices, node("p", t("mechanismGuard"), "notice"),
      node("p", t("rubricNote"), "notice"),
      setupNav(button("reviewSetup", t("reviewSetup"), () => act("setup_mechanism", {mechanism: field.select.value}), "primary")));
  }
  function issueList(issues) {
    const list = node("ul", null, "issues-list");
    for (const issue of issues) add(list, node("li", typeof issue === "string" ? issue : JSON.stringify(issue)));
    return list;
  }
  function setupReview(main) {
    const config = state.setup_config || configValues();
    add(main, heading(t("reviewTitle")));
    setupNotice(main);
    const table = node("table", null, "review-table");
    const body = node("tbody");
    const rows = [
      [t("environment"), config.technical_environment], [t("duration"), `${config.duration_minutes} ${t("minutes")}`],
      [t("questionCount"), `${config.question_count} × HARD`],
      [t("sourceLabel"), config.question_source === "BYOQ" ? t("byoq") : t("randomized")],
      [t("mechanismLabel"), config.interviewer_mechanism === "STRICT_CHALLENGING" ? t("strict") : t("supportive")],
      [t("configDigest"), config.sha256 || "UNVERIFIED"],
    ];
    rows.forEach(([label, value]) => {
      const th = node("th", label); th.scope = "row";
      add(body, add(node("tr"), th, node("td", value)));
    });
    add(table, body); add(main, table);
    if (state.setup_profiles) {
      const section = node("details", null, "question-review");
      add(section, node("summary", t("profileDigest")), node("p", t("policyProposal"), "notice"));
      for (const [role, profile] of Object.entries(state.setup_profiles)) {
        add(section, node("h3", role), node("code", profile.sha256 || "UNVERIFIED", "digest"),
          node("p", `${profile.policy_version || ""} · ${profile.review_status || ""}`, "digest"));
        if (profile.source_sha256) {
          const list = node("ul", null, "source-digests");
          Object.entries(profile.source_sha256).forEach(([path, hash]) => {
            add(list, add(node("li"), node("span", path), node("code", hash, "digest")));
          });
          add(section, list);
        }
      }
      add(main, section);
    }
    if (state.setup_questions?.length) {
      add(main, node("h2", t("questionReviewStatus"), "section-title"));
      state.setup_questions.forEach((review, index) => add(main, questionReview(review, index)));
    }
    if (config.question_source === "BYOQ" && config.duration_minutes === 45) {
      add(main, rehearsalStartButton());
    }
    const blockers = node("section", null, "launch-blockers");
    add(blockers, node("h2", t("blockers")), issueList(state.setup_blockers || []),
      node("p", t("preflightNote"), "muted"));
    add(main, blockers, node("p", t("rubricNote"), "notice"), scores(true),
      setupNav(button("launchPreflight", t("launchPreflight"), () => act("setup_launch"), "primary")),
      previewStartCard());
  }
  function requestCount() {
    const count = state.activation?.requests_used ?? state.api_requests;
    return Number.isInteger(count) && count >= 0 ? count : 0;
  }
  function modelLabel() {
    const modelState = state.activation?.state || state.model_state || "offline";
    return t({"activated-unverified": "unverified", "live-verified": "verified"}[modelState] || modelState);
  }
  function render() {
    const focused = document.activeElement;
    const focusId = focused?.id;
    const selection = focused instanceof HTMLTextAreaElement ? [focused.selectionStart, focused.selectionEnd] : null;
    document.documentElement.lang = state.language === "zh" ? "zh-CN" : "en";
    document.title = `${t("title")} · ${state.screen}`;
    const shell = node("div", null, "shell");
    const header = node("header", null, "header");
    const brand = node("div", null, "brand");
    add(brand, node("span", "TI", "brand-mark"), add(node("div"), node("div", t("title"), "brand-title"), node("p", t("subtitle"), "brand-subtitle")));
    const tools = node("div", null, "header-tools");
    const lang = button("language", t("language"), () => act("language", {language: state.language === "zh" ? "en" : "zh"}), "text");
    lang.setAttribute("aria-label", t("languageLabel"));
    add(tools, lang, button("restart", t("reset"), () => act("reset"), "text"));
    add(header, brand, tools);
    const progress = node("div", null, "progress-area");
    const step = Number.isInteger(state.tutorial_step) ? Math.min(5, Math.max(0, state.tutorial_step)) : 0;
    const setupStep = {CONFIG: 1, QUESTION_SOURCE: 2, MECHANISM: 3, REVIEW: 4}[state.screen];
    const label = setupStep ? `${t("setupStep")} ${setupStep} / 4` :
      state.screen === "ENTRY" ? t("entryStep") : state.screen === "API_PORTAL" ? t("portalStep") :
      state.screen === "LIVE_PREVIEW" ? t("livePreview") : `${t("tutorialStep")} ${step} / 5`;
    const meter = node("progress");
    meter.max = setupStep ? 4 : 5;
    meter.value = state.screen === "LIVE_PREVIEW" ? (state.live_preview?.closed ? 5 : 3) : setupStep || step;
    meter.setAttribute("aria-label", label);
    add(progress, add(node("div", null, "progress-label"), badge(label),
      node("span", ["API_PORTAL", "LIVE_PREVIEW"].includes(state.screen) || setupStep ? modelLabel() : t("simulated"), "muted")), meter);
    const main = node("main"); main.id = "main";
    const screens = {
      ENTRY: entry, WELCOME: welcome, RULES: rules, QUESTION: question, ROOM: room, COMPLETE: complete,
      API_PORTAL: apiPortal, LIVE_PREVIEW: livePreview, REHEARSAL_COMPLETE: rehearsalComplete, CONFIG: configuration, QUESTION_SOURCE: questionSource, MECHANISM: mechanism, REVIEW: setupReview,
    };
    if (state.recovery_error) {
      const saveUnavailable = state.recovery_error === "SAVE_UNAVAILABLE" ||
        state.recovery_error?.code === "SAVE_UNAVAILABLE";
      add(main, heading(t("recoveryTitle")),
        node("p", t(saveUnavailable ? "saveRecoveryBody" : "recoveryBody"), "lead"),
        actions(saveUnavailable ? button("exportReceipt", t("recoveryExport"), () => act("export"), "primary") : null,
          button("recoverReset", t("recoveryReset"), () => act("reset"), saveUnavailable ? "secondary" : "primary")));
    } else if (screens[state.screen]) screens[state.screen](main);
    else { add(main, heading(t("requestFailed"))); showError("UNKNOWN_HOST_SCREEN"); }
    const livePending = node("section", null, "live-request-controls");
    livePending.dataset.livePending = "true";
    livePending.setAttribute("role", "status");
    add(livePending, node("p", t("pendingRequest")), actions(
      interruptButton("cancelPreview", t("cancelRequest"), "preview_cancel"),
      interruptButton("disconnectPending", t("disconnected"), "disconnect")));
    livePending.hidden = !hasLiveRequest();
    const footer = node("footer", null, "footer");
    add(footer, node("span", `${modelLabel()} · ${t("requests")}: ${requestCount()}`),
      node("span", state.saved_locally ? t("saved") : t("notSaved")));
    add(shell, header);
    if (state.transport_mode === "MOCK_HTTP") add(shell, node("p", "AUTOMATED TEST · MOCK HTTP · NO REAL PROVIDER CALLS", "setup-warning"));
    add(shell, progress, livePending, main, footer);
    app.replaceChildren(shell);
    updateClockDisplay();
    setBusy(pending.size > 0);
    if (previousScreen !== state.screen) {
      previousScreen = state.screen;
      document.getElementById("screenTitle")?.focus({preventScroll: true});
      window.scrollTo(0, 0);
    } else if (focusId) {
      const restored = document.getElementById(focusId);
      restored?.focus({preventScroll: true});
      if (selection && restored instanceof HTMLTextAreaElement) restored.setSelectionRange(...selection);
    }
  }
  add(app, node("p", strings.en.loading, "loading"),
    button("retryConnection", strings.en.retry, () => act("snapshot")));
  setInterval(updateClockDisplay, 1000);
  setInterval(() => {
    if (state?.rehearsal?.status === "ACTIVE" && pending.size === 0 && !busy) {
      request("rehearsal_tick").catch(() => {});
    }
  }, 15000);
  request("snapshot").catch(() => {});
})();
