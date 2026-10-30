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
  let evaluatorQuestionIndex = 0;
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
      gradeTitle: "Local PostgreSQL fixture validation · unscored",
      gradeNote: "Review an independent local test fixture before executing the submitted PostgreSQL query. This is not an official LeetCode hidden test.",
      gradeResultDisclaimer: "Passing a local fixture does not certify all hidden tests or establish a competency score.",
      gradeCurrentQuestion: "Current question · SHA-256",
      gradeRequiresSQL: "Submit a PostgreSQL SQL implementation to enable reviewed local fixture validation.",
      gradeStatus: "Local fixture execution result",
      gradeInspect: "Inspect fixture (no execution)",
      gradeExpected: "I reviewed the test inputs and expected result and authorize one execution of this exact fixture against my latest SQL.",
      gradeExecute: "Run approved local PostgreSQL fixture",
      gradePending: "Nothing executes without a separate fixture inspection and your explicit approval.",
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
      setupPending: "Confirm three distinct user-provided questions to run a genuine 45-minute Live AI rehearsal. Practice accepts Easy, Medium, Hard or unspecified difficulty. Formal graded launch remains separate and unavailable.",
      configuration: "Interview configuration", environment: "Technical environment",
      duration: "Session duration", minutes: "minutes", questionCount: "Questions · derived from duration",
      hardOnly: "Formal exam profile: HARD (practice accepts any difficulty)", configNote: "45 minutes requires 3 questions; 60 minutes requires 4. The host validates this contract.",
      continueSetup: "Next →", sourceTitle: "Select question source", sourceLabel: "Question source",
      byoq: "Bring your own question · LeetCode / HackerRank", randomized: "Randomized · approved dataset pool",
      sourceInstructions: "Paste the original LeetCode/HackerRank question without rewriting it into JSON. Choose its source, then Extract → Review/Edit → Confirm. JSON import remains available in Advanced mode.",
      sourceSafety: "Structural review is not SQL execution or hidden-test validation. Missing or conflicting information blocks progression; remaining slots are never silently filled.",
      questionNumber: "Question", emptyTemplate: "Advanced: insert JSON template", bytes: "UTF-8 bytes",
      extractQuestion: "Extract question", confirmQuestion: "Confirm reviewed fields",
      practiceQuestion: "Practise this question with Live AI (unscored)",
      rehearsalStart: "Start LIVE 3-question interview practice (unscored)",
      rehearsalSubmit: "Finish question → Next", rehearsalSkip: "Skip question → Next",
      rehearsalFinish: "Finish interview & freeze record", rehearsalComplete: "Three-question rehearsal complete",
      rehearsalNote: "Three confirmed questions. New interviews allow continuous conversation within each 15-minute question window. PostgreSQL SQL can be tested only against separately approved local fixtures; Pandas and competency grading remain unavailable.",
      evidenceHeading: "Evidence-based technical scorecard · no competency grade",
      evidenceNotice: "Host-derived observations only. Approved local fixtures are not official hidden tests or technical ability percentages.",
      evidenceCovered: "Latest SQL locally verified", evidencePassed: "Latest SQL passed local fixture",
      evidenceClosed: "Questions closed", evidenceActions: "Observed candidate actions",
      evidenceQuestion: "Question evidence", evidenceRuntime: "Elapsed / model wait",
      evidenceUnknown: "No current verified SQL result", evidenceSource: "Source evidence and checksums",
      evidenceCert: "Uncertified local time; Technical / Communication / Overall: NOT_SCORED",
      evidenceTurns: "turns", evidenceClarify: "clarifications", evidenceHelp: "help requests", evidenceSQL: "SQL submissions",
      evidenceTestedPrior: "Prior SQL was tested, but final SQL differs. Current submission: NOT_VERIFIED.",
      evidenceSaved: "Derived from saved Host records; opening this report does not run SQL or call AI.",
      trainerEvidenceHeading: "Trainer Lab · source-linked practice (offline)",
      trainerEvidenceNotice: "These offline drills were generated without a model, and are not diagnoses or employment scores. A separately authorized Native AI Trainer proposal may involve a paid call.",
      trainerEvidencePrimary: "Primary practice task", trainerEvidenceSource: "Observed evidence", trainerEvidenceAcceptance: "Completion check", trainerEvidenceLimit: "Skill level remains NOT_SCORED; historical interview evidence cannot change.",
      trainerEvidenceWaiting: "Finish and lock all three questions to prepare practice tasks.",
      evaluatorHeading: "Independent AI Evaluator · evidence review",
      evaluatorNotice: "Review one frozen question at a time. Technical and Communication are separate provisional, uncalibrated model proposals; they are not final grades. The verified SQL ledger above remains authoritative for actual execution.",
      evaluatorPrivacy: "Each request sends the selected question and bounded frozen evidence to your approved provider. Review the native consent sheet before authorizing one paid request; there are no automatic retries.",
      evaluatorQuestion: "Question to evaluate", evaluatorGenerate: "Evaluate this question · native consent required",
      evaluatorEmpty: "No evaluator proposal has been committed for this question.",
      evaluatorNoEvidence: "No eligible frozen candidate evidence is available for this question.",
      evaluatorReview: "PENDING_HUMAN_REVIEW · Check each rationale and cited event against the frozen record.",
      evaluatorPoints: "Proposed observed points", evaluatorCoverage: "Observed coverage",
      evaluatorNotObserved: "NOT_OBSERVED · missing evidence, not zero",
      evaluatorAnchor: "Proposed anchor", evaluatorWeight: "Provisional criterion weight",
      evaluatorRationale: "Evidence-based rationale", evaluatorUncertainty: "Uncertainty / missing evidence",
      evaluatorExcerptMissing: "The exact cited excerpt is unavailable in this view. Review the exported frozen record.",
      evaluatorExcerptPartial: "Partial excerpt; remaining context was not included in this citation.",
      evaluatorFinal: "Final Technical, Communication and Overall grades: NOT_SCORED. No combined 60/40 grade is assigned.",
      evaluatorBudget: "A private provider session with remaining approved requests is required. Reopen the API Portal to activate or review your request cap.",
      evaluatorConfidence: "Review status", evaluatorSources: "Policy, prompt and source provenance", evaluatorMissing: "Criteria without sufficient evidence remain unobserved; points are never extrapolated to missing criteria.",
      evaluatorAwaitClosure: "Evaluator review becomes available only after the interview is closed and its evidence is frozen.",
      evaluatorUnavailable: "Evaluator unavailable: its installed sources or frozen evidence could not be verified. Rebuild and reopen the App from the reviewed repository version. Your interview evidence remains available; evaluation is disabled until this is resolved.",
      nativeTrainerHeading: "Native BYOK · AI Trainer proposal",
      nativeTrainerNote: "Optional paid OpenAI request. Only the chosen evidence-linked drill and excerpts up to 280 characters per cited candidate event leave your Mac; a short SQL submission may be included in full. A native consent sheet is required for each request. Feedback is an unverified model proposal, not a skill grade.",
      nativeTrainerRequest: "Ask AI Trainer (requires native consent)",
      nativeTrainerConnect: "Activate a private OpenAI session…",
      nativeTrainerPending: "Native request in flight; do not close the App. A restart never resends it automatically.",
      nativeTrainerInterrupted: "A previous request was interrupted. It may have been billed. No automatic retry occurred.",
      nativeTrainerReview: "PENDING_HUMAN_REVIEW — assess this advice against the original candidate evidence before using it.",
      nativeTrainerModel: "Model-proposed hypothesis", nativeTrainerAction: "Suggested training action",
      nativeTrainerAcceptance: "Suggested completion check", nativeTrainerUncertainty: "Important uncertainties",
      smartHeading: "Seven-day SMART practice sprint", smartNotice: "Goals are derived from frozen evidence; logging practice is self-reported and cannot certify improvement.",
      smartStart: "Start seven-day practice sprint", smartLog: "Record activity (self-report)",
      smartNote: "Describe what you actually tried (3–500 UTF-8 bytes)", smartEvidence: "External retest artifact SHA-256 (self-reported; not independently checked)",
      smartKind: "Activity type", smartPractice: "Practice attempt", smartBlocked: "Blocked", smartRetest: "External retest attempt",
      smartDeadline: "Deadline", smartNoProgress: "Not started; deadlines are relative until you begin.",
      smartNoProof: "No independently verified improvement. Fresh authorized retesting is required.",
      commHeading: "Communication evidence · C01–C06 (unrated)",
      commNotice: "Speech labels and sequence are evidence candidates, not proof of quality. No rating is assigned. Proposed 60/40 weights are not applied.",
      commRecorded: "Candidate events", commReplies: "Interviewer replies",
      commPotential: "Potential evidence · semantic review needed", commNotObserved: "NOT_OBSERVED (not zero)",
      commPreview: "Exact candidate excerpt", commRefs: "Event IDs",
      commPrompt: "Communication checkpoints (strategy, not scoring)",
      commPromptText: "Clarify scope → explain plan → separate verified from unknown → diagnose a gap and request bounded help → act on feedback → honestly summarize.",
      commNoClose: "Closing speech has no dedicated event in this app; C06 cannot be inferred from the Finish button.",
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
      blockers: "Formal graded exam · not implemented", launchPreflight: "Show formal exam limitations",
      questionReviewStatus: "Question review", policyProposal: "Versioned policy · scoring remains provisional",
      setupStep: "Real AI setup", preflightNote: "These restrictions apply to formal graded launch only. The 3-question Live AI practice above accepts reviewed Pandas/SQL questions regardless of difficulty; actual paid calls still need native consent. Pandas execution and competency scores remain unverified.",
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
      gradeTitle: "本地 PostgreSQL 测试验证 · 不评定能力分数",
      gradeNote: "执行已提交的 PostgreSQL SQL 前，必须单独审阅本地测试数据。这不是 LeetCode 官方隐藏测试。",
      gradeResultDisclaimer: "通过单个本地测试不代表通过全部隐藏测试，也不能据此推断综合能力分数。",
      gradeCurrentQuestion: "当前题目 · SHA-256",
      gradeRequiresSQL: "先提交 PostgreSQL SQL 答案，才能申请审阅本地测试数据。",
      gradeStatus: "本地测试执行结果",
      gradeInspect: "检查测试数据（不运行 SQL）",
      gradeExpected: "我已经审阅测试输入、预期输出和最新提交的 SQL，同意对此测试数据进行一次本地执行。",
      gradeExecute: "执行已批准的本地 PostgreSQL 测试",
      gradePending: "只有单独检查测试数据并明确批准后才会执行；不会自动运行 SQL。",
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
      setupPending: "确认三道不同的自带题目后，可启动真实 AI 45 分钟模拟面试；练习允许 Easy / Medium / Hard 或未知难度。正式判分考试尚未开放。",
      configuration: "面试配置", environment: "技术环境", duration: "会话时长", minutes: "分钟",
      questionCount: "题目数量 · 根据时长推导", hardOnly: "正式考试配置：HARD（练习不限难度）",
      configNote: "45 分钟必须为 3 题，60 分钟必须为 4 题。此约束由宿主验证。",
      continueSetup: "下一步 →", sourceTitle: "选择题目来源", sourceLabel: "题目来源",
      byoq: "自带题目 · LeetCode / HackerRank", randomized: "随机面试 · 已批准的数据集题库",
      sourceInstructions: "直接粘贴 LeetCode/HackerRank 原始题目，无需改写 JSON。选择来源后点击提取 → 审阅/编辑 → 确认。高级用户仍可使用 JSON。",
      sourceSafety: "结构审查不代表 SQL 执行或隐藏测试验证。缺失或冲突的信息会阻止继续；剩余题目不会被静默补齐。",
      questionNumber: "题目", emptyTemplate: "高级：插入 JSON 模板", bytes: "UTF-8 字节",
      extractQuestion: "提取题目", confirmQuestion: "确认已审阅字段",
      practiceQuestion: "用真实 AI 练习此题（不评分）",
      rehearsalStart: "开始真实 AI 三题模拟面试（不评分）",
      rehearsalSubmit: "结束本题并进入下一题", rehearsalSkip: "跳过本题并进入下一题",
      rehearsalFinish: "完成面试并冻结记录", rehearsalComplete: "三题模拟面试已完成",
      rehearsalNote: "三道确认题。新面试每题 15 分钟，可持续交互。SQL 可单独批准本地 PostgreSQL Fixture 执行；Pandas 及综合能力评分仍未开放。",
      evidenceHeading: "技术面试证据成绩单 · 不生成能力分数",
      evidenceNotice: "仅根据 Host 记录生成。审核过的本地 Fixture 不等于官方隐藏测试，也不代表能力百分比。",
      evidenceCovered: "最终 SQL 已经本地验证的题目", evidencePassed: "最终 SQL 通过本地 Fixture 的题目",
      evidenceClosed: "已关闭题目", evidenceActions: "已记录候选人行为",
      evidenceQuestion: "逐题证据", evidenceRuntime: "已用时间 / 模型等待",
      evidenceUnknown: "最终 SQL 尚无可信执行结果", evidenceSource: "来源事件与校验摘要",
      evidenceCert: "本地计时未认证；技术 / 沟通 / 总评均为 NOT_SCORED",
      evidenceTurns: "交互次数", evidenceClarify: "澄清次数", evidenceHelp: "求助次数", evidenceSQL: "SQL 提交次数",
      evidenceTestedPrior: "此前 SQL 经过测试，但最终提交发生变化；当前 SQL 为 NOT_VERIFIED。",
      evidenceSaved: "仅从 Host 存档派生；打开报告不会执行 SQL，也不会调用 AI。",
      trainerEvidenceHeading: "训练实验室 · 有来源的离线练习",
      trainerEvidenceNotice: "这些离线练习无需调用模型，不是 AI 诊断或招聘评分；另行授权的原生 AI Trainer 建议可能产生付费请求。",
      trainerEvidencePrimary: "第一优先练习", trainerEvidenceSource: "证据来源", trainerEvidenceAcceptance: "完成标准", trainerEvidenceLimit: "能力仍为 NOT_SCORED；不得修改历史面试证据。",
      trainerEvidenceWaiting: "请先结束并锁定三道题，才能生成练习任务。",
      evaluatorHeading: "独立 AI Evaluator · 面试证据评审",
      evaluatorNotice: "逐题评审冻结记录。技术与沟通分别生成暂定、未校准的模型建议，不是最终成绩。上方 SQL 证据账本仍是实际执行结果的依据。",
      evaluatorPrivacy: "每次请求会将所选题目及有界冻结证据发送给已授权的服务商。请在原生窗口审核后批准一次付费请求；不会自动重试。",
      evaluatorQuestion: "选择评审题目", evaluatorGenerate: "评审此题 · 需原生窗口授权",
      evaluatorEmpty: "此题尚无已提交的评估建议。",
      evaluatorNoEvidence: "此题没有符合评审条件的冻结候选人证据。",
      evaluatorReview: "PENDING_HUMAN_REVIEW · 请逐项核对依据与引用事件是否符合冻结记录。",
      evaluatorPoints: "已观察项目的建议分值", evaluatorCoverage: "证据覆盖范围",
      evaluatorNotObserved: "NOT_OBSERVED · 证据缺失，非零分",
      evaluatorAnchor: "建议等级锚点", evaluatorWeight: "暂定项目权重",
      evaluatorRationale: "证据依据", evaluatorUncertainty: "不确定性 / 缺失证据",
      evaluatorExcerptMissing: "当前视图无法显示准确的引用片段，请审阅导出的冻结记录。",
      evaluatorExcerptPartial: "此处仅显示引用片段；其余上下文不包含在该引用中。",
      evaluatorFinal: "技术、沟通及综合最终成绩：NOT_SCORED。不会生成 60/40 合成总分。",
      evaluatorBudget: "需要已激活的私有服务商会话及剩余授权请求。请重新打开 API Portal 激活或审阅请求上限。",
      evaluatorConfidence: "审核状态", evaluatorSources: "规则、提示词与来源记录", evaluatorMissing: "证据不足的项目保留未观察状态；不会将已观察分值外推到缺失项目。",
      evaluatorAwaitClosure: "只有面试关闭、证据冻结后，才能申请评估。",
      evaluatorUnavailable: "评估器暂不可用：无法验证已安装来源或冻结证据。请从已审核的仓库版本重新构建并打开 App。面试证据仍可查看；问题解决前无法申请评估。",
      nativeTrainerHeading: "原生 BYOK · AI Trainer 反馈提案",
      nativeTrainerNote: "可选付费 OpenAI 请求。只发送所选训练任务及每条引用事件最多 280 字符的短片段（短 SQL 可能被完整包含）。每次请求需 macOS 原生弹窗确认。模型输出是未获事实认证的建议，不是能力评分。",
      nativeTrainerRequest: "申请 AI Trainer 建议（原生授权）",
      nativeTrainerConnect: "激活私有 OpenAI 凭证…",
      nativeTrainerPending: "原生请求进行中；请勿关闭 App。重启不会自动再次收费调用。",
      nativeTrainerInterrupted: "上一请求曾被中断，可能已产生费用。没有自动重试。",
      nativeTrainerReview: "PENDING_HUMAN_REVIEW — 请核对原始证据后再采纳。",
      nativeTrainerModel: "模型提出的假设", nativeTrainerAction: "建议训练行动",
      nativeTrainerAcceptance: "建议完成标准", nativeTrainerUncertainty: "局限与不确定性",
      smartHeading: "七天 SMART 练习冲刺", smartNotice: "目标来自冻结证据；练习日志仅为自我申报，不能证明能力提升。",
      smartStart: "启动七天训练计划", smartLog: "记录练习（自报）",
      smartNote: "记录实际做过的事（UTF-8 最多 500 字节）", smartEvidence: "外部复测文件 SHA-256（仅自报，未独立核验）",
      smartKind: "记录类型", smartPractice: "练习尝试", smartBlocked: "遇到阻碍", smartRetest: "外部复测尝试",
      smartDeadline: "截止时间", smartNoProgress: "尚未启动，截止时间从正式启动算起。",
      smartNoProof: "能力改善尚未获得独立验证。需要全新且获授权的复测。",
      commHeading: "沟通证据账本 · C01–C06（不评分）",
      commNotice: "事件类别与先后顺序只是候选证据，并非沟通质量的证明。60/40 为待校准假设，当前不计算分数。",
      commRecorded: "候选人事件", commReplies: "面试官回复",
      commPotential: "候选证据 · 待语义审核", commNotObserved: "NOT_OBSERVED（非零分）",
      commPreview: "候选人原文片段", commRefs: "来源事件 ID",
      commPrompt: "面试沟通检查点（策略提醒，不评分）",
      commPromptText: "澄清目标 → 解释方案 → 区分已验证与未知 → 定位卡点并有边界地求助 → 将反馈转为行动 → 如实总结。",
      commNoClose: "当前 App 尚无专用收尾发言事件，不能从点击结束按钮推断 C06。",
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
      blockers: "正式评分考试 · 尚未实现", launchPreflight: "查看正式考试限制",
      questionReviewStatus: "题目审查", policyProposal: "版本化策略 · 评分仍为暂定",
      setupStep: "真实 AI 配置", preflightNote: "这些要求只针对正式判分考试。上方的三题真实 AI 练习支持不同难度的 Pandas/SQL 已审阅题目；付费模型调用仍需原生授权。Pandas 执行与能力分数尚未验证。",
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
  const liveRequestActions = new Set(["preview_verify", "preview_send", "voice_send", "grade_execute", "trainer_request", "evaluator_generate", "post_sql_execute", "preparer_request", "preparer_verify"]);
  const interruptActions = new Set(["preview_cancel", "post_sql_cancel", "disconnect"]);
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
    if (code === "EVALUATOR_UNCITED_OR_CROSS_QUESTION_EVIDENCE") return state.language === "zh"
      ? "评估回复的证据引用未通过校验，因此没有保存分数。原始对话仍完整保留；再次评估需要一次新的明确授权。"
      : "The evaluator reply failed citation validation, so no assessment was saved. Your transcript is preserved. Re-evaluation requires a new explicit authorization.";
    if (code === "POSTGRES_SERVER_NOT_AVAILABLE") return state.language === "zh"
      ? "此 Mac 未找到本地 PostgreSQL 执行器。SQL 尚未运行；模型审查不能替代执行结果。"
      : "No local PostgreSQL executor was found on this Mac. SQL has not run; model review cannot substitute for execution.";
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
      const awaitsHuman = ["api_portal", "reset", "tutorial_replay", "export", "voice_handsfree", "voice_listen"].includes(action);
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
  window.TIAVoice?.mount({send: request});
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
        if (item.action === "reset") { questionDrafts = []; questionSources = []; questionFieldDrafts = []; liveDraft = ""; liveKind = "clarify"; evaluatorQuestionIndex = 0; }
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
  // S03-E4 examples: display-only projection; never modifies confirmed questions,
  // the trusted controller, journal, model context, or grading authority.
  function displaySourceText(value) {
    if (typeof value !== "string") return "";
    const named = {amp: "&", lt: "<", gt: ">", quot: '"', apos: "'", nbsp: " "};
    return value.replace(/&#(?:x([\da-fA-F]{1,6})|(\d{1,7}));/gi, (match, hex, dec) => {
        const point = parseInt(hex || dec, hex ? 16 : 10);
        return point > 0 && point <= 0x10ffff && !(point >= 0xd800 && point <= 0xdfff)
          ? String.fromCodePoint(point) : match;
      })
      .replace(/&(?:amp|lt|gt|quot|apos|nbsp);/gi, match => named[match.slice(1, -1).toLowerCase()] || match)
      .replace(/\\([|*_])/g, "$1")
      .replace(/\*\*/g, "")
      .replace(/\u00a0/g, " ")
      .replace(/\r\n?/g, "\n");
  }
  function parseLeetCodeExamples(raw) {
    // Bound display extraction. Not a verifier, source oracle, or hidden-test set.
    const source = displaySourceText(raw).split("\n");
    const examples = [];
    let active = null, section = null;
    const finish = () => {
      if (!active) return;
      for (const name of ["input", "output", "explanation"]) {
        active[name] = active[name].join("\n").trim();
      }
      if (active.input || active.output || active.explanation) examples.push(active);
    };
    for (const untrimmed of source) {
      const line = untrimmed.trim().replace(/^#{1,6}\s*/, "");
      const heading = /^Example(?:\s+(\d{1,2}))?\s*:\s*$/i.exec(line);
      if (heading) {
        finish();
        if (examples.length >= 8) break;
        active = {number: heading[1] || String(examples.length + 1), input: [], output: [], explanation: []};
        section = null;
        continue;
      }
      if (!active) continue;
      if (/^(?:Constraints|Follow[ -]?up|Notes?)\s*:/i.test(line)) {
        finish(); active = null; section = null;
        break;
      }
      const label = /^(Input|Output|Explanation)\s*:\s*(.*)$/i.exec(line);
      if (label) {
        section = label[1].toLowerCase();
        if (label[2]) active[section].push(label[2]);
      } else if (section) {
        active[section].push(untrimmed);
      }
    }
    finish();
    return examples.slice(0, 8);
  }
  function splitReviewedExampleBlocks(value) {
    // Imported editable fields may concatenate several "Example N:" blocks.
    const text = displaySourceText(value).trim();
    if (!text) return [];
    const lines = text.split("\n");
    const blocks = []; let current = null;
    for (const line of lines) {
      const m = /^Example\s+(\d{1,2})\s*:\s*$/i.exec(line.trim());
      if (m) {
        current = {number: m[1], lines: []}; blocks.push(current);
      } else if (!current) {
        current = {number: "1", lines: []}; blocks.push(current);
        current.lines.push(line);
      } else current.lines.push(line);
    }
    return blocks.slice(0, 8).map(item => ({number: item.number, text: item.lines.join("\n").trim()}));
  }
  function reviewedQuestionExamples(previewQuestion) {
    const hash = previewQuestion?.content_sha256;
    if (typeof hash !== "string" || !/^[0-9a-f]{64}$/.test(hash)) return [];
    const index = state.rehearsal?.current_index;
    const reviews = Array.isArray(state.setup_questions) ? state.setup_questions : [];
    const preferred = Number.isInteger(index) ? reviews[index] : null;
    const review = preferred?.content_sha256 === hash ? preferred : reviews.find(item => item?.content_sha256 === hash);
    // Never pair examples from a different question or an unconfirmed source.
    if (!review?.human_confirmed || !review.fields) return [];
    const originals = parseLeetCodeExamples(review.raw_input || "");
    const inputs = splitReviewedExampleBlocks(review.fields.example_input);
    const outputs = splitReviewedExampleBlocks(review.fields.expected_output);
    const numbers = [...new Set([...originals.map(x => x.number), ...inputs.map(x => x.number), ...outputs.map(x => x.number)])].slice(0, 8);
    return numbers.map(number => {
      const original = originals.find(x => x.number === number);
      const confirmedInput = inputs.find(x => x.number === number)?.text || "";
      const confirmedOutput = outputs.find(x => x.number === number)?.text || "";
      return {number,
        input: confirmedInput || original?.input || "",
        output: confirmedOutput || original?.output || "",
        explanation: original?.explanation || "",
        source: "REVIEWED_FIELDS_WITH_ORIGINAL_EXPLANATION",
      };
    });
  }
  function exampleCardsForQuestion(previewQuestion) {
    const examples = reviewedQuestionExamples(previewQuestion);
    if (!examples.length) return null;
    const zh = state.language === "zh";
    const section = node("section", null, "question-examples");
    section.id = "questionExamples";
    add(section, node("h3", zh ? "题目示例 · 输入、输出与解释" : "Examples · Input, Output & Explanation"),
      node("p", zh ? "来源为已确认的题目字段及保留的原文；示例不是已执行的测试，也不是官方隐藏测试。" :
        "Shown from reviewed question fields and original source text. Examples are not executed or official hidden tests.", "field-help"));
    examples.forEach((example, index) => {
      const card = node("section", null, "example-display-card");
      card.id = `questionExample${index}`;
      const number = example.number;
      add(card, node("h4", `${zh ? "示例" : "Example"} ${number}`));
      const pieces = [
        ["input", zh ? "输入 · Input" : "Input", example.input],
        ["output", zh ? "期望输出 · Output" : "Expected Output", example.output],
      ];
      pieces.forEach(([key, label, value]) => {
        add(card, node("h5", label));
        const content = value || (zh ? "来源缺失：请返回题目审阅补充" : "Missing from reviewed source: edit question before testing");
        const code = add(node("pre", null, "code-block"), node("code", content));
        code.id = `questionExample${index}_${key}`;
        add(card, code);
      });
      if (example.explanation) {
        const explanation = node("details", null, "question-review");
        explanation.open = true;
        const content = add(node("pre", null, "code-block"), node("code", example.explanation));
        content.id = `questionExample${index}_explanation`;
        add(explanation, node("summary", zh ? "解析与中间计算表 · Explanation" : "Explanation & intermediate tables"), content);
        add(card, explanation);
      }
      if (!example.input || !example.output) {
        add(card, node("p", zh ? "示例信息不完整，不能用于判题。" : "Incomplete example: not usable as a verification fixture.", "notice"));
      }
      add(section, card);
    });
    return section;
  }

  function questionCard(compact = false, previewQuestion = null) {
    const q = previewQuestion || state.question || {};
    const card = node("section", null, `question-card${compact ? " compact" : ""}`);
    add(card, badge(t(previewQuestion ? "previewQuestion" : "medium")), node(compact ? "h3" : "h2", q.title || "First Order per Customer"),
      node("p", q.statement || "", "question-statement"), node("h3", t("schema")),
      add(node("pre", null, "code-block"), node("code", q.schema || "")));
    if (previewQuestion) {
      const examples = exampleCardsForQuestion(previewQuestion);
      if (examples) add(card, examples);
    }
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
    // This is a Host-derived heuristic after submission, not a code verdict.
    const issue = state.language_reviews?.active;
    if (issue?.status === "LANGUAGE_MISMATCH_REVIEW_REQUIRED") {
      const warning = node("p", state.language === "zh"
        ? `语言不匹配：题目环境是 ${issue.expected_environment}，提交内容看起来是 ${issue.observed_style}。请人工确认语言；未执行代码或评分。`
        : `Language mismatch: expected ${issue.expected_environment}; submission appears ${issue.observed_style}. Review language before proceeding. No execution or grading occurred in this check.`, "notice");
      warning.id = "languageMismatchLive";
      add(main, warning);
    }
    add(main, add(node("div", null, "title-row"), heading(t("livePreview")), badge(modelLabel(), "accent")),
      node("p", t("livePreviewNote"), "lead"), providerDetails());
    const columns = node("div", null, "room-grid");
    add(columns, add(node("aside", null, "question-side"), questionCard(true, preview.question || {}),
      node("p", preview.sql_accuracy?.correctness === "VERIFIED_LOCAL_FIXTURE" ? t("gradeResultDisclaimer")
        : (preview.question?.environment || state.setup_config?.technical_environment) === "PANDAS"
          ? (state.language === "zh" ? "尚未运行 Pandas 执行器；模型回复及已提交代码均不等于通过测试。" : "No Pandas evaluator has run. Neither a submitted answer nor an AI reply is a passing test.")
          : t("noTests"), "notice")));
    const work = node("section", null, "work-side");
    add(work, node("h2", t("senior")),
      node("p", t(preview.mechanism === "PROFESSIONAL_SUPPORTIVE" ? "supportive" : "strict"), "muted"));
    if (preview.closed) {
      add(work, node("h2", t("previewClosed")), node("p", t("previewFrozen")));
    } else if (preview.can_send || preview.pending || preview.retry_input) {
      const retry = preview.retry_input;
      const isPandasPreview = (preview.question?.environment || state.setup_config?.technical_environment) === "PANDAS";
      const kind = selectField("previewKind", t("kind"),
        ["clarify", "plan", "help", "implement", "test"].map(value => [value, value === "implement" && isPandasPreview
          ? (state.language === "zh" ? "提交 Python / Pandas 代码" : "Python / Pandas submission") : t(value)]), retry?.kind || liveKind);
      kind.select.addEventListener("change", () => { liveKind = kind.select.value; });
      kind.select.dataset.unavailable = String(Boolean(retry));
      const label = node("label", t("previewInput")); label.htmlFor = "previewResponse";
      const input = node("textarea"); input.id = "previewResponse"; input.rows = 8;
      input.maxLength = 4096; input.spellcheck = false; input.autocapitalize = "off";
      input.value = retry?.text ?? liveDraft;
      input.placeholder = isPandasPreview
        ? (state.language === "zh" ? "解释思路、澄清问题，或编写 Python / Pandas 代码…" : "Explain your plan, clarify, or write your Python / Pandas code…")
        : t("placeholder");
      input.readOnly = Boolean(retry);
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
      add(main, node("p", `Question ${rs.current_index + 1} / ${rs.question_count} · ${preview.candidate_turns_used} candidate turns · host-controlled handoff only`, "notice"));
      const elapsedQ = rs.timing?.questions?.[rs.current_index]?.elapsed_seconds;
      if (typeof elapsedQ === "number" && rs.timing?.question_limit_seconds === 900) {
        add(main, node("p", `${state.language === "zh" ? "本题剩余" : "Question time remaining"}: ${formatElapsed(Math.max(0, 900 - elapsedQ))} · ${state.language === "zh" ? "仅最终提交 / 跳过 / 计时归零可转场" : "Only final submit / skip / timeout advances"}`, "notice"));
      }
    }
    add(main, columns, communicationPlaybook(), conversation(preview.session, true), gradingPanel(), scores(), previewProvenance(preview.prompt_provenance));
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
      const candidateEvents = (preview.session?.events || []).filter(e => e.actor === "candidate");
      const policy = state.rehearsal?.continuity_policy;
      const hasSubmittedCode = policy === "tia-continuity/v3"
        ? candidateEvents.some(e => e.kind === "implement")
        : candidateEvents.at(-1)?.kind === "implement";
      const canFinalize = (!["tia-continuity/v2", "tia-continuity/v3"].includes(policy) || hasSubmittedCode) && !preview.pending;
      const finish = button("finishRehearsalQuestion", t(final ? "rehearsalFinish" : "rehearsalSubmit"),
        () => act("rehearsal_submit"), "primary");
      finish.disabled = busy || !canFinalize;
      finish.dataset.unavailable = String(!canFinalize);
      add(main, actions(finish,
        button("skipRehearsalQuestion", t("rehearsalSkip"), () => act("rehearsal_skip"), "secondary")));
      if (!canFinalize) add(main, node("p", state.language === "zh"
        ? "请先选择提交代码（implement）并发送最终 SQL / Pandas 代码；澄清和计划不会自动结束本题。"
        : "Send your final SQL / Pandas code using implement before finishing. Clarification and planning do not close this question.", "field-help"));
    }
    add(main, actions(button("openPortal", t("portal"), () => act("api_portal")),
      interruptButton("disconnect", t("disconnected"), "disconnect")),
      state.rehearsal?.status === "ACTIVE" ? null :
      actions(preview.closed ? button("realInterview", t("portalStep"), () => act("choose_real")) :
        button("closePreview", t("closePreview"), () => act("preview_close"), "primary")));
  }
  function communicationPlaybook() {
    if (state.rehearsal?.status !== "ACTIVE") return null;
    const detail = node("details", null, "question-review");
    detail.id = "communicationPlaybook";
    add(detail, node("summary", t("commPrompt")), node("p", t("commPromptText"), "field-help"),
      node("p", t("commNotice"), "notice"));
    return detail;
  }
  function communicationEvidence() {
    const report = state.communication_evidence;
    if (!report || report.schema !== "tia-communication-evidence/v1") return null;
    const section = node("section", null, "receipt-card");
    section.id = "communicationEvidence";
    add(section, node("h2", t("commHeading")), node("p", t("commNotice"), "notice"),
      node("p", `${t("evidenceClosed")}: ${report.summary?.closed_questions || 0} / 3 · ` +
        `Communication: ${report.summary?.communication_competency || "NOT_SCORED"}`, "field-help"),
      node("p", t("commNoClose"), "field-help"));
    for (const question of report.questions || []) {
      const outer = node("details", null, "question-review");
      add(outer, node("summary", `Q${question.index + 1} · ${t("commRecorded")}: ${question.candidate_event_count} · ` +
        `${t("commReplies")}: ${question.interviewer_reply_count}`));
      for (const d of question.dimensions || []) {
        const item = node("div", null, "field-help");
        add(item, node("strong", `${d.id} · ${d.title}`),
          node("p", d.status === "NOT_OBSERVED" ? t("commNotObserved") : t("commPotential")),
          node("p", `Anchor: NOT_EVALUATED · ${t("commRefs")}: ` +
            (d.evidence || []).map(x => x.event_id).join(", ")));
        for (const e of (d.evidence || []).slice(0, 2))
          add(item, node("p", `${t("commPreview")}: ${e.preview}` +
            (e.elapsed_seconds === null ? "" : ` · +${e.elapsed_seconds}s`), "field-help"));
        if (d.followup_sequences?.length)
          add(item, node("p", `Reply → action: ` +
            d.followup_sequences.map(x => `${x.interviewer_event_id} → ${x.candidate_event_id}`).join(", "), "field-help"));
        outer.appendChild(item);
      }
      section.appendChild(outer);
    }
    add(section, node("code", report.sha256 || "", "digest"));
    return section;
  }
  function groundedTrainer() {
    const tplan = state.grounded_trainer;
    if (!tplan || tplan.schema !== "tia-grounded-trainer/v1") return null;
    const section = node("section", null, "receipt-card"); section.id = "groundedTrainer";
    add(section, node("h2", t("trainerEvidenceHeading")), node("p", t("trainerEvidenceNotice"), "notice"),
      node("p", `${tplan.status} · ${tplan.mode} · ${tplan.numeric_scores}`, "field-help"));
    if (tplan.status !== "READY_FOR_HUMAN_REVIEW") {
      add(section, node("p", t("trainerEvidenceWaiting"), "field-help"));
      return section;
    }
    for (const drill of tplan.drills || []) {
      const detail = node("details", null, "question-review");
      if (drill.id === tplan.primary_drill_id) detail.open = true;
      add(detail, node("summary", `${drill.id === tplan.primary_drill_id ? t("trainerEvidencePrimary") + " · " : ""}${drill.id} · P${drill.priority}`),
        node("p", drill.rationale, "field-help"), node("p", drill.task),
        node("p", `${t("trainerEvidenceAcceptance")}: ${drill.acceptance}`, "field-help"),
        node("p", `${t("trainerEvidenceSource")}: ${drill.trigger} · ${drill.evidence.observed_local_status}`,
          "field-help"), node("p", `Event IDs: ${(drill.evidence.candidate_event_ids || []).join(", ") || "NONE"}`, "field-help"));
      if (drill.evidence.fixture_sha256) add(detail, node("code", drill.evidence.fixture_sha256, "digest"));
      section.appendChild(detail);
    }
    add(section, node("p", t("trainerEvidenceLimit"), "notice"), node("code", tplan.sha256, "digest"));
    return section;
  }
  function evaluatorV1MvmPanel() {
    const result = state.evaluator_v1_readout;
    if (state.screen !== "REHEARSAL_COMPLETE" || result?.schema !== "tia-evaluator-v1-mvm-readout/v1") return null;
    const section = node("section", null, "receipt-card"); section.id = "evaluatorV1MvmPanel";
    add(section, node("h2", "Evaluator v1.0 · Offline scoring MVM"),
      node("p", "Separate experimental 12-metric policy (70/20/10). Not a verified ability grade.", "notice"));
    if (result.status !== "DEMO_READY") {
      add(section, node("p", "Score waits for interview closure", "field-help"));
      return section;
    }
    add(section, badge("PURE_PLACEHOLDER · NOT A CANDIDATE SCORE", "accent"),
      node("h3", `Arithmetic placeholder: ${result.score} / 100`),
      node("p", `Rating coverage: ${result.rating_coverage_pct}% · Missing-ratings range: ${result.sensitivity_min}–${result.sensitivity_max}`, "field-help"),
      node("p", `Core gate: ${result.core_gate} · Industry percentile: ${result.industry_percentile}`, "field-help"));
    const detail = node("details", null, "question-review"); detail.id = "evaluatorV1Breakdown";
    add(detail, node("summary", "Show all 12 dimensions and missing evidence"));
    for (const [id, metric] of Object.entries(result.metrics || {})) {
      add(detail, node("p", `${id} · ${metric.status} · weight ${metric.max_points} · imputed ${metric.imputed_points}`, "field-help"));
    }
    add(section, detail,
      node("p", "The historical 60/40 evaluator is shown separately below; no automatic migration of its proposed ratings.", "notice"),
      node("code", `${result.policy_version} · ${result.provisional_interview_id}`, "digest"));
    return section;
  }
  function evaluatorV1MockPanel() {
    const mock = state.evaluator_v1_mock_readout;
    if (state.screen !== "REHEARSAL_COMPLETE" || mock?.schema !== "tia-evaluator-v1-mock-readout/v1") return null;
    const section = node("section", null, "receipt-card"); section.id = "evaluatorV1MockPanel";
    add(section, node("h2", "Evaluator v1.0 · Event-bound OFFLINE Mock"),
      node("p", "SYNTHETIC DEMONSTRATION ONLY: fixed fictional anchors, NOT real AI judgment, a SQL grade or your interview score.", "notice"));
    if (mock.status !== "SYNTHETIC_DEMO_ONLY") {
      add(section, badge("MOCK_NOT_AVAILABLE", "accent"), node("p", "The existing interview record cannot be represented by this constrained mock protocol."));
      return section;
    }
    add(section, badge("SYNTHETIC_DEMO · HUMAN_REVIEW_NOT_APPLICABLE", "accent"),
      node("h3", `Mock arithmetic: ${mock.score} / 100`),
      node("p", `Mock-rated weight: ${mock.rating_coverage_pct}% · imputed ${mock.imputed_points} points · range ${mock.sensitivity_min}–${mock.sensitivity_max}`, "field-help"),
      node("p", `Core gate: ${mock.core_gate}; industry percentile: ${mock.industry_percentile}; paid model calls: ${mock.mock_model_calls}`, "field-help"));
    const detail = node("details", null, "question-review"); detail.id = "evaluatorV1MockEvidence";
    add(detail, node("summary", "Inspect mock 12-metric ratings and source event IDs"));
    for (const [metric, row] of Object.entries(mock.ratings || {})) {
      const label = row.anchor === null ? "NOT_OBSERVED (imputed)" : `MOCK anchor ${row.anchor}/4 (NOT ASSESSED)`;
      const cited = (row.evidence_event_ids || []).join(", ") || "NONE";
      add(detail, node("p", `${metric} · ${label} · events: ${cited}`, "field-help"));
      if (mock.mock_rationale?.[metric]) add(detail, node("p", mock.mock_rationale[metric], "field-help"));
    }
    add(section, detail, node("p", "This test confirms evidence-ID binding and arithmetic only. No training history is updated. A real Evaluator will require separately reviewed model responses.", "notice"),
      node("code", `source sha256: ${mock.source_digest}`, "digest"));
    return section;
  }
  function evaluatorExcerpt(questionIndex, citation) {
    // Presentation only: the Host has already checked citation/source digests.
    // Resolve solely within this question's original candidate events; never
    // display a model-supplied quotation as if it came from the frozen record.
    if (!Number.isInteger(questionIndex) || questionIndex < 0 || questionIndex >= 3) return null;
    const events = state.rehearsal?.results?.[questionIndex]?.session?.events;
    const span = citation.span;
    if (!Array.isArray(events) || typeof citation.event_id !== "string" || !span ||
        span.unit !== "UTF8_BYTES" || !Number.isInteger(span.start) || !Number.isInteger(span.end) ||
        span.start < 0 || span.end <= span.start) return null;
    const matches = events.filter(event => event.id === citation.event_id);
    if (matches.length !== 1 || matches[0].actor !== "candidate" || matches[0].kind !== citation.kind ||
        typeof matches[0].payload?.text !== "string") return null;
    const bytes = new TextEncoder().encode(matches[0].payload.text);
    if (span.end > bytes.length) return null;
    try {
      return {text: new TextDecoder("utf-8", {fatal: true}).decode(bytes.slice(span.start, span.end)),
        partial: span.start > 0 || span.end < bytes.length};
    } catch (_) { return null; }
  }
  function evaluatorPanel() {
    const report = state.evaluator_report;
    if (state.screen !== "REHEARSAL_COMPLETE" || report?.schema !== "tia-evaluator-report/v1") return null;
    const section = node("section", null, "receipt-card"); section.id = "evaluatorPanel";
    add(section, node("h2", t("evaluatorHeading")), node("p", t("evaluatorNotice"), "notice"),
      node("p", t("evaluatorFinal"), "notice"));
    if (report.status === "UNAVAILABLE" || !Array.isArray(report.questions)) {
      const notice = node("p", t("evaluatorUnavailable"), "setup-warning"); notice.id = "evaluatorUnavailable";
      add(section, notice);
      return section;
    }
    if (report.status !== "READY") {
      add(section, node("p", t("evaluatorAwaitClosure"), "field-help"));
      return section;
    }
    const questions = report.questions.filter(q => Number.isInteger(q.index) && q.index >= 0 && q.index < 3);
    if (!questions.length) return section;
    if (!questions.some(q => q.index === evaluatorQuestionIndex)) evaluatorQuestionIndex = questions[0].index;
    const field = selectField("evaluatorQuestion", t("evaluatorQuestion"),
      questions.map(q => [String(q.index), `${q.index + 1}. ${q.title}`]), String(evaluatorQuestionIndex));
    field.select.addEventListener("change", () => {
      evaluatorQuestionIndex = Number(field.select.value);
      render();
    });
    add(section, field.field);
    const question = questions.find(q => q.index === evaluatorQuestionIndex);
    const assessment = question.assessment;
    const practice = communicationPracticeView(question);
    add(section, postInterviewSQLPanel(question));
    if (assessment) {
      const summary = node("div"); summary.id = "evaluatorAssessment";
      add(summary, badge(`${assessment.provenance} · ${assessment.status}`, "accent"),
        node("p", t("evaluatorReview"), "notice"),
        node("p", assessment.model_identifier, "field-help"));
      add(section, summary);
    } else {
      add(section, node("p", t("evaluatorEmpty"), "field-help"));
    }
    const axes = node("div", null, "setup-grid");
    for (const [axis, title] of [["technical", t("technical")], ["communication", t("communication")]]) {
      const summary = question[axis];
      if (!summary) continue;
      const card = node("section", null, "setup-stat");
      card.id = axis === "technical" ? "evaluatorTechnical" : "evaluatorCommunication";
      const observed = Number.isFinite(summary.proposed_observed_points);
      const recordedZero = axis === "communication" && practice;
      add(card, node("h3", title),
        node("p", recordedZero ? (state.language === "zh" ? "本次记录中的沟通展示：0 / 40" : "Recorded communication demonstration: 0 / 40") : `${t("evaluatorPoints")}: ` + (observed
          ? `${summary.proposed_observed_points} / ${summary.covered_maximum_points}`
          : (assessment ? t("evaluatorNotObserved") : "NOT_EVALUATED"))),
        node("p", `${t("evaluatorCoverage")}: ${summary.observed_dimensions} / ${summary.total_dimensions} · ` +
          `${t("evaluatorWeight")}: ${summary.covered_maximum_points} / ${summary.proposed_maximum_points}`, "field-help"));
      if (recordedZero) add(card, node("p", state.language === "zh"
        ? "此题只记录了代码或纯求助，没有解释性沟通。按练习规则记为零；这不证明沟通能力为零，也不能评估未录入的语音。"
        : "Only code or a bare help request was recorded. No explanatory communication was demonstrated, so the practice value is zero. This does not measure ability or speech that was never captured.", "notice"));
      if (summary.missing_dimensions?.length && !recordedZero)
        add(card, node("p", `${t("evaluatorUncertainty")}: ${summary.missing_dimensions.join(", ")}`, "field-help"));
      add(axes, card);
    }
    add(section, axes, node("p", t("evaluatorMissing"), "field-help"));
    for (const criterion of question.dimensions || []) {
      const item = node("details", null, "question-review"); item.id = `evaluatorCriterion-${criterion.id}`;
      const practiceRow = practice?.dimensions.find(d => d.id === criterion.id);
      add(item, node("summary", `${criterion.id} · ${criterion.title} · ${practiceRow?.status || criterion.status}`),
        node("p", `${t("evaluatorWeight")}: ${criterion.proposed_max_points}`, "field-help"));
      if (practiceRow) add(item, node("p", `${state.language === "zh" ? "本次记录中的练习点数" : "Recorded practice points"}: 0 / ${practiceRow.maximum_points}`, "notice"),
        node("p", `${state.language === "zh" ? "保留原模型状态" : "Original model status retained"}: ${criterion.status}`, "field-help"));
      if (Number.isInteger(criterion.anchor_0_to_4) && Number.isFinite(criterion.provisional_points)) {
        add(item, node("p", `${t("evaluatorAnchor")}: ${criterion.anchor_0_to_4} / 4 · ` +
          `${t("evaluatorPoints")}: ${criterion.provisional_points} / ${criterion.proposed_max_points}`, "field-help"));
      } else if (!practiceRow) add(item, node("p", criterion.status === "NOT_EVALUATED" ? "NOT_EVALUATED" : t("evaluatorNotObserved"), "field-help"));
      add(item, node("p", `${t("evaluatorRationale")}: ${criterion.reason || ""}`, "field-help"),
        node("p", `${t("evaluatorConfidence")}: ${criterion.confidence}`, "field-help"));
      for (const evidence of criterion.evidence || []) {
        const citation = node("div", null, "field-help");
        add(citation, node("p", `${t("commRefs")}: ${evidence.event_id} · ${evidence.kind} · ${evidence.alias}`));
        if (evidence.span) add(citation, node("p", `${evidence.span.unit}: ${evidence.span.start}–${evidence.span.end}`));
        const original = evaluatorExcerpt(question.index, evidence);
        if (original) {
          add(citation, node("p", t("commPreview")), node("blockquote", original.text, "transcript-text"));
          if (original.partial) add(citation, node("p", t("evaluatorExcerptPartial"), "field-help"));
        } else add(citation, node("p", t("evaluatorExcerptMissing"), "field-help"));
        if (original && typeof evidence.event_id === "string") {
          const jump = node("button", state.language === "zh" ? "查看完整对话上下文" : "View full conversation context", "button text");
          jump.type = "button";
          jump.addEventListener("click", () => scrollToTranscriptEvent(question.index, evidence.event_id));
          add(citation, jump);
        }
        add(citation, node("code", evidence.text_sha256, "digest"));
        add(item, citation);
      }
      add(section, item);
    }
    if (state.native_evaluator_error_code) add(section, node("p", errorText(state.native_evaluator_error_code), "notice"));
    else if (state.native_evaluator_interrupted)
      add(section, node("p", t("nativeTrainerInterrupted"), "notice"));
    if (state.native_evaluator_pending) {
      add(section, node("p", t("nativeTrainerPending"), "notice"));
    } else if (!assessment) {
      const activation = state.activation || {};
      const available = activation.live_enabled === true && Number.isInteger(activation.request_limit) &&
        Number.isInteger(activation.requests_used) && activation.requests_used < activation.request_limit;
      add(section, node("p", t("evaluatorPrivacy"), "notice"));
      if (!available) add(section, node("p", t("evaluatorBudget"), "notice"),
        button("evaluatorConnect", t("portal"), () => act("api_portal"), "secondary"));
      if (!question.eligible) add(section, node("p", t("evaluatorNoEvidence"), "field-help"));
      const generate = button("evaluatorGenerate", t("evaluatorGenerate"),
        () => act("evaluator_generate", {question_index: evaluatorQuestionIndex}), "primary");
      generate.dataset.unavailable = String(!available || !question.eligible);
      generate.disabled = busy || generate.dataset.unavailable === "true";
      add(section, generate);
    }
    const provenance = node("details", null, "question-review"); provenance.id = "evaluatorProvenance";
    add(provenance, node("summary", t("evaluatorSources")),
      node("p", `${report.rubric_version} · ${JSON.stringify(report.proposed_weight_policy)}`, "field-help"),
      node("p", "Prompt SHA-256", "field-help"), node("code", report.prompt_sha256, "digest"));
    if (report.source_sha256 && typeof report.source_sha256 === "object") {
      for (const [source, hash] of Object.entries(report.source_sha256))
        add(provenance, node("p", source, "field-help"), node("code", hash, "digest"));
    }
    if (assessment) add(provenance, node("p", "Frozen context SHA-256", "field-help"),
      node("code", assessment.context_input_sha256, "digest"),
      node("p", "Assessment SHA-256", "field-help"), node("code", assessment.sha256, "digest"));
    add(provenance, node("p", "Report SHA-256", "field-help"), node("code", report.sha256, "digest"));
    add(section, provenance);
    return section;
  }

  // A separate, source-bound practice observation; saved model ratings stay intact.
  function communicationPracticeView(question) {
    const value = question?.practice_communication;
    if (value?.policy !== "tia-recorded-communication/v1" ||
        value.status !== "NO_RECORDED_DEMONSTRATION" || value.points !== 0 ||
        value.maximum_points !== 40 || !Array.isArray(value.dimensions) || value.dimensions.length !== 6) return null;
    return value;
  }

  function postInterviewSQLPanel(question) {
    const data = state.post_interview_sql;
    if (!data || state.screen !== "REHEARSAL_COMPLETE") return null;
    const zh = state.language === "zh", index = question.index;
    const panel = node("section", null, "receipt-card"); panel.id = "postInterviewSQL";
    add(panel, node("h3", zh ? "实际运行此题 SQL · 本地测试" : "Run this question’s SQL · local tests"),
      node("p", zh ? "使用已冻结的最后一次 SQL 提交，在临时 PostgreSQL 中与预期结果逐例比较。结果标为面试后验证；不会修改原始对话，也不代表覆盖官方隐藏测试或全部边界。"
        : "Compare the frozen final SQL submission with expected results in temporary PostgreSQL. Results are marked as post-interview verification. They do not change your transcript or establish coverage of official hidden tests or every edge case.", "notice"));
    const selected = data.results?.[String(index)];
    if (selected) {
      add(panel, node("p", `${selected.status} · ${selected.passed} / ${selected.total} · AFTER_INTERVIEW`, "notice"));
      for (const item of selected.cases || []) add(panel, node("p", `${item.label || item.id || "Case"}: ${item.status || item.result?.status || "NOT_RUN"} · ${item.reason || item.result?.reason || item.result?.error_code || ""}`, "field-help"));
      add(panel, node("p", zh ? "本次本地测试记录独立保存。若需要 AI 结合新结果重新评估，请使用下方评估按钮并明确授权。"
        : "This local test record is saved separately. To have AI review the new results, explicitly authorize a new evaluation below.", "field-help"));
    }
    if (data.pending) {
      add(panel, node("p", zh ? "本地 SQL 测试进行中…" : "Local SQL tests are running…", "notice"));
      const cancel = button("postSQLCancel", zh ? "取消本地测试" : "Cancel local tests", () => act("post_sql_cancel"));
      cancel.dataset.interrupt = "true"; add(panel, cancel);
      return panel;
    }
    const suites = Array.isArray(data.suites) ? data.suites : [];
    const options = suites.map(x => [x.id || x.suite_id, x.title || x.label || x.id || x.suite_id]);
    if (!options.length) return panel;
    const reviewed = data.review?.question_index === index ? data.review : null;
    const field = selectField("postSQLSuite", zh ? "选择并核对与题目匹配的测试集" : "Select and review the suite matching your question", options,
      reviewed?.suite_id || options[0][0]);
    add(panel, field.field, button("postSQLReview", zh ? "查看用例与预期结果" : "Review cases and expected results",
      () => act("post_sql_review", {question_index:index, suite_id:field.select.value}), "secondary"));
    if (reviewed) {
      const cases = node("details", null, "question-review"); cases.id = "postSQLCases"; cases.open = true;
      add(cases, node("summary", `${reviewed.title || reviewed.suite_id} · ${reviewed.case_count} ${zh ? "个本地用例" : "local cases"}`));
      for (const assumption of [reviewed.assumptions].flat().filter(Boolean)) add(cases, node("p", assumption, "notice"));
      for (const item of reviewed.cases || []) {
        const detail = node("details", null, "question-review");
        add(detail, node("summary", item.label || "Case"),
          node("pre", JSON.stringify(item.fixture, null, 2), "transcript-text")); add(cases, detail);
      }
      add(cases, node("code", reviewed.review_sha256, "digest"));
      const label = node("label", null, "field-help"), checkbox = node("input"); checkbox.type="checkbox"; checkbox.id="postSQLMatches";
      add(label, checkbox, document.createTextNode(zh ? " 我已核对题意、假设与预期结果；此测试集适用于该题。"
        : " I reviewed the question, assumptions and expected results; this suite matches the task."));
      const execute = button("postSQLExecute", zh ? "运行已核对用例 · 无 AI 请求" : "Run reviewed cases · no AI request",
        () => act("post_sql_execute", {review_sha256:reviewed.review_sha256}), "primary");
      execute.dataset.unavailable="true"; execute.disabled=true;
      checkbox.addEventListener("change", () => {
        const ready = checkbox.checked && field.select.value === reviewed.suite_id;
        execute.dataset.unavailable=String(!ready); execute.disabled=busy || !ready;
      });
      field.select.addEventListener("change", () => {checkbox.checked=false; execute.dataset.unavailable="true"; execute.disabled=true;});
      add(panel, cases, label, execute);
    }
    return panel;
  }

  function nativeTrainerPanel() {
    const tplan = state.grounded_trainer;
    if (!tplan || tplan.status !== "READY_FOR_HUMAN_REVIEW") return null;
    const section = node("section", null, "receipt-card"); section.id = "nativeTrainerPanel";
    add(section, node("h2", t("nativeTrainerHeading")),
      node("p", t("nativeTrainerNote"), "notice"));
    const feedback = state.native_trainer_feedback;
    if (feedback?.schema === "tia-native-trainer-feedback/v1") {
      const p = feedback.proposal || {};
      add(section, badge("LIVE_OPENAI_NATIVE_BYOK · PENDING_HUMAN_REVIEW", "accent"),
        node("p", t("nativeTrainerReview"), "notice"),
        node("p", `${feedback.model_identifier} · ${feedback.drill_id} · NOT_SCORED`, "field-help"),
        node("h3", t("nativeTrainerModel")), node("p", p.hypothesis || ""),
        node("h3", t("nativeTrainerAction")), node("p", p.training_action || ""),
        node("h3", t("nativeTrainerAcceptance")), node("p", p.acceptance || ""),
        node("h3", t("nativeTrainerUncertainty")), node("p", p.uncertainty || ""),
        node("p", `Event IDs: ${(p.cited_candidate_events || []).join(", ") || "NONE"}`, "field-help"),
        node("code", feedback.sha256 || "", "digest"));
      return section;
    }
    if (state.native_trainer_interrupted)
      add(section, node("p", t("nativeTrainerInterrupted"), "notice"));
    if (state.native_trainer_pending)
      add(section, node("p", t("nativeTrainerPending"), "notice"));
    else {
      if (!state.activation?.live_enabled)
        add(section, button("connectTrainer", t("nativeTrainerConnect"), () => act("api_portal"), "secondary"));
      const buttonAsk = button("requestTrainer", t("nativeTrainerRequest"), () => act("trainer_request"), "primary");
      buttonAsk.dataset.unavailable = String(!state.activation?.live_enabled);
      buttonAsk.disabled = busy || !state.activation?.live_enabled;
      add(section, buttonAsk);
    }
    return section;
  }

  function smartPlanPanel() {
    const plan = state.smart_plan;
    if (!plan || plan.schema !== "tia-smart-improvement-plan/v1") return null;
    const section = node("section", null, "receipt-card"); section.id = "smartPlanPanel";
    add(section, node("h2", t("smartHeading")), node("p", t("smartNotice"), "notice"),
      node("p", `SMART · ${plan.days_in_sprint} days · ${plan.improvement_certification} · ${plan.numeric_competency_score}`, "field-help"));
    if (plan.status !== "READY_TO_START") return section;
    const progress = state.smart_progress;
    if (!progress) {
      add(section, node("p", t("smartNoProgress"), "field-help"),
          button("startSmart", t("smartStart"), () => act("smart_start"), "primary"));
    }
    const summary = state.smart_progress_summary || {};
    for (const goal of plan.goals || []) {
      const info = (summary.goals || []).find(x => x.id === goal.id);
      const detail = node("details", null, "question-review");
      if (goal.id === plan.goals?.[0]?.id) detail.open = true;
      const due = info ? new Date(info.due_wall_seconds * 1000).toLocaleString() :
        `Day ${goal.time_bound.days_after_explicit_start} after start`;
      add(detail, node("summary", `${goal.id} · ${goal.skill_tag} · ${due}`),
        node("p", goal.specific),
        node("p", `S: ${goal.specific}`, "field-help"),
        node("p", `M: ${goal.measurable}`, "field-help"),
        node("p", `A: ${goal.achievable}`, "field-help"),
        node("p", `R: ${goal.relevant}`, "field-help"),
        node("p", `T: ${goal.time_bound.duration_minutes_suggested} min; ${t("smartDeadline")}: ${due}`, "field-help"),
        node("p", `Evidence IDs: ${(goal.source.candidate_event_ids || []).join(", ") || "NONE"}`, "field-help"),
        node("p", `${info?.attempts || 0} recorded · ${info?.latest_activity || "NOT_ATTEMPTED"} · AWAITING_INDEPENDENT_RETEST`, "notice"));
      if (progress) {
        const kindLabel = node("label", t("smartKind"));
        const kind = node("select"); kind.id = `smartKind-${goal.id}`;
        for (const [value, title] of [["PRACTICED", t("smartPractice")], ["BLOCKED", t("smartBlocked")], ["RETEST_RECORDED", t("smartRetest")]]) {
          const opt = node("option", title); opt.value = value; kind.appendChild(opt);
        }
        const noteLabel = node("label", t("smartNote"));
        const note = node("textarea"); note.id = `smartNote-${goal.id}`; note.rows = 2;
        const artifactLabel = node("label", t("smartEvidence"));
        const artifact = node("input"); artifact.id = `smartArtifact-${goal.id}`; artifact.placeholder = "64 lowercase hex";
        const save = button(`smartSave-${goal.id}`, t("smartLog"), () => {
          const hash = kind.value === "RETEST_RECORDED" ? artifact.value.trim() : null;
          act("smart_record", {task_id:goal.id,kind:kind.value,note:note.value,artifact_sha256:hash});
        }, "secondary");
        const validate = () => {
          const noteOK = note.value.trim().length >= 3 && new TextEncoder().encode(note.value).length <= 500;
          const artifactOK = kind.value !== "RETEST_RECORDED" || /^[0-9a-f]{64}$/.test(artifact.value.trim());
          const un = !(noteOK && artifactOK);
          save.dataset.unavailable = String(un); save.disabled = busy || un;
          artifact.disabled = kind.value !== "RETEST_RECORDED";
        };
        note.addEventListener("input", validate); artifact.addEventListener("input", validate);
        kind.addEventListener("change", validate); validate();
        add(detail, kindLabel, kind, noteLabel, note, artifactLabel, artifact, save);
      }
      section.appendChild(detail);
    }
    if (progress) {
      add(section, node("p", `${summary.recorded_attempts || 0} recorded activity/activities · SELF_REPORTED_UNVERIFIED`, "field-help"));
      for (const e of progress.entries || [])
        add(section, node("p", `#${e.ordinal} · ${e.task_id} · ${e.kind} · ${e.note} · ${e.verification}`, "field-help"));
    }
    add(section, node("p", t("smartNoProof"), "notice"), node("code", plan.sha256, "digest"));
    return section;
  }

  function evidenceScorecard() {
    const card = state.evidence_scorecard;
    if (!card || card.schema !== "tia-evidence-scorecard/v1") return null;
    const totals = card.summary || {};
    const section = node("section", null, "receipt-card");
    section.id = "evidenceScorecard";
    add(section, node("h2", t("evidenceHeading")), node("p", t("evidenceNotice"), "notice"),
      node("p", t("evidenceSaved"), "field-help"),
      node("p", `${t("evidenceClosed")}: ${totals.closed_questions || 0} / ${totals.total_questions || 3}`, "field-help"),
      node("p", `${t("evidenceCovered")}: ${totals.latest_sql_locally_verified_questions || 0} / ${totals.total_questions || 3}`, "field-help"),
      node("p", `${t("evidencePassed")}: ${totals.latest_sql_passed_local_fixtures || 0}`, "field-help"));
    const acts = totals.observed_closed_question_actions || {};
    add(section, node("p", `${t("evidenceActions")}: ${acts.candidate_turns || 0} ${t("evidenceTurns")}, ` +
      `${acts.clarifications || 0} ${t("evidenceClarify")}, ${acts.help_requests || 0} ${t("evidenceHelp")}, ` +
      `${acts.sql_submissions || 0} ${t("evidenceSQL")}`, "field-help"),
      node("p", t("evidenceCert"), "notice"));
    // Deliberately no percentage, weighted grade, AI evaluation or claim that
    // one local example represents LeetCode official hidden-test coverage.
    for (const question of card.questions || []) {
      const accuracy = question.accuracy || {};
      const detail = node("details", null, "question-review");
      add(detail, node("summary", `${question.index + 1}. ${question.title} · ${accuracy.status || "NOT_VERIFIED"}`),
        node("p", `${question.outcome || question.state} · ${accuracy.reason || "NOT_VERIFIED"}`, "field-help"));
      if (accuracy.reason === "TESTED_PRIOR_SQL_VERSION")
        add(detail, node("p", t("evidenceTestedPrior"), "notice"));
      if (accuracy.fixture_total !== null && accuracy.fixture_total !== undefined)
        add(detail, node("p", `${accuracy.fixture_passed} / ${accuracy.fixture_total} approved local fixture(s)`, "field-help"));
      else add(detail, node("p", t("evidenceUnknown"), "field-help"));
      if (question.behavior) {
        const b = question.behavior;
        add(detail, node("p", `${b.candidate_turns} ${t("evidenceTurns")}, ${b.clarifications} ${t("evidenceClarify")}, ` +
          `${b.help_requests} ${t("evidenceHelp")}, ${b.sql_submissions} ${t("evidenceSQL")}`, "field-help"),
          node("p", `${t("evidenceSource")}: ${(b.evidence_event_ids || []).join(", ")}`, "field-help"));
      }
      if (question.time && question.time.elapsed_seconds !== null)
        add(detail, node("p", `${t("evidenceRuntime")}: ${formatElapsed(question.time.elapsed_seconds)} / ` +
          `${question.time.model_wait_seconds === null ? "NOT_AVAILABLE" : formatElapsed(question.time.model_wait_seconds)}`, "field-help"));
      if (accuracy.fixture_sha256) add(detail, node("code", accuracy.fixture_sha256, "digest"));
      if (accuracy.candidate_sql_sha256) add(detail, node("code", accuracy.candidate_sql_sha256, "digest"));
      section.appendChild(detail);
    }
    add(section, node("p", `${t("evidenceSource")}: ${card.source}`, "field-help"),
      node("code", card.sha256 || "", "digest"));
    return section;
  }
  // Read-only replay of the original saved candidate/interviewer turns.
  // The Host already sealed each result.session.events when its question closed.
  function fullInterviewTranscript() {
    const section = node("section", null, "receipt-card");
    section.id = "interviewTranscript";
    const chinese = state.language === "zh";
    add(section,
      node("h2", chinese ? "完整面试对话 · 证据回放" : "Full interview transcript · evidence replay"),
      node("p", chinese
        ? "按每题冻结的 Host 事件顺序展示候选人与面试官完整原文。可用 Event ID 对照下方 AI Evaluator 的逐项评估；展示记录不会运行 SQL、重新请求 AI 或更改评分。"
        : "Complete Candidate/Interviewer messages in frozen Host event order. Match Event IDs with each AI Evaluator criterion below. Viewing this archive does not execute SQL, call AI or change scoring.", "notice"));
    const results = state.rehearsal?.results || [];
    const questions = state.rehearsal?.questions || [];
    for (let i = 0; i < results.length; i++) {
      const result = results[i] || {};
      const all = result.session?.events;
      const events = Array.isArray(all) ? all.filter(event =>
        (event?.actor === "candidate" || (event?.actor === "interviewer" && event?.kind === "reply")) &&
        typeof event?.payload?.text === "string" && event.payload.text.length > 0) : [];
      const detail = node("details", null, "question-review");
      detail.id = `interviewTranscriptQ${i + 1}`;
      detail.open = i === 0;
      const title = questions[i]?.title || (chinese ? "题目" : "Question");
      add(detail, node("summary", `Q${i + 1} · ${title} · ${events.length} ${chinese ? "条消息" : "messages"}`));
      if (!Array.isArray(all)) {
        add(detail, node("p", chinese
          ? "该题冻结记录中没有可回放的 session.events；不能从评分引用推断不存在的对话。"
          : "No replayable session.events in this frozen question record; do not infer missing dialogue from scoring citations.", "field-help"));
      } else if (!events.length) {
        add(detail, node("p", chinese ? "此题没有已记录的双方消息。" : "No recorded dialogue for this question.", "field-help"));
      }
      for (let n = 0; n < events.length; n++) {
        const event = events[n];
        const candidate = event.actor === "candidate";
        const entry = node("div", null, `transcript-entry ${candidate ? "candidate" : "interviewer"}`);
        entry.id = `interviewTranscriptQ${i + 1}Event${n + 1}`;
        entry.dataset.eventId = typeof event.id === "string" ? event.id : "";
        entry.tabIndex = -1;
        const elapsed = Number.isFinite(event.elapsed_seconds)
          ? ` · ${formatElapsed(event.elapsed_seconds)}` : "";
        const speaker = candidate ? (chinese ? "候选人" : "Candidate")
          : (chinese ? "面试官" : "Senior Interviewer");
        const metadata = `${speaker} · ${event.kind || "unknown"}${elapsed} · ${event.provenance || "UNKNOWN"}`;
        const body = node(event.kind === "implement" ? "pre" : "p", event.payload.text, "transcript-text");
        add(entry, node("div", metadata, "transcript-speaker"), body,
          node("div", `Event ID: ${event.id || "UNAVAILABLE"}`, "field-help"));
        add(detail, entry);
      }
      add(section, detail);
    }
    if (!results.length) add(section, node("p", chinese
      ? "尚无冻结题目记录。" : "No frozen question records available.", "field-help"));
    return section;
  }

  // Navigate only to a real event already present in the frozen transcript.
  function scrollToTranscriptEvent(questionIndex, eventId) {
    const group = document.getElementById(`interviewTranscriptQ${questionIndex + 1}`);
    if (!group || typeof eventId !== "string") return false;
    const target = Array.from(group.querySelectorAll("[data-event-id]"))
      .find(item => item.dataset.eventId === eventId);
    if (!target) return false;
    group.open = true;
    target.scrollIntoView({block: "center", behavior: "smooth"});
    target.focus({preventScroll: true});
    return true;
  }

  // Deterministic E3 read-only full-interview scheme. No provider calls or scoring authority.
  function fullEvaluatorSchemePanel() {
    const report = state.evaluator_report;
    const scheme = report?.full_scheme;
    if (state.screen !== "REHEARSAL_COMPLETE" || scheme?.schema !== "tia-evaluator-full-scheme/v1") return null;
    const zh = state.language === "zh";
    const section = node("section", null, "receipt-card");
    section.id = "evaluatorFullScheme";
    add(section,
      node("h2", zh ? "完整面试评估总览 · 三题十一维" : "Full interview evaluation · three questions, eleven criteria"),
      node("p", zh
        ? "只汇总 Host 已记录且通过证据资格门槛的 AI 建议。未观察不是零分；未校准规则不生成正式总分。"
        : "Host-derived provisional observations only. Missing evidence is not zero; uncalibrated weights do not produce final grades.", "notice"),
      node("p", `${scheme.status} · ${scheme.formal_authority} · Overall: NOT_SCORED`, "field-help"));
    const overview = node("div", null, "setup-grid");
    for (const [key, title] of [["technical", zh ? "技术能力" : "Technical"],
                                ["communication", zh ? "沟通能力" : "Communication"]]) {
      const a = scheme[key] || {};
      const tile = node("section", null, "setup-stat");
      const pts = Number.isFinite(a.observed_provisional_points) ? a.observed_provisional_points : "NOT_EVALUATED";
      add(tile, node("h3", title),
        node("p", `${zh ? "已有证据建议点数" : "Evidence-backed proposed points"}: ${pts} / ${a.covered_weight || 0}`),
        node("p", `${zh ? "三题权重覆盖" : "Three-question evidence coverage"}: ${a.covered_weight || 0} / ${a.maximum_weight || 0} (${a.coverage_percent || 0}%)`, "field-help"),
        node("p", `${zh ? "未观察权重" : "Unobserved weight"}: ${a.unobserved_weight ?? "?"} · Grade: NOT_SCORED`, "notice"));
      add(overview, tile);
    }
    add(section, overview,
      node("p", `${zh ? "当前模型评估" : "Current assessments"}: ${scheme.evaluations_current}/3 · ` +
        `${zh ? "历史版" : "Legacy"}: ${scheme.evaluations_legacy} · ` +
        `${zh ? "拦截的不合格指标" : "Blocked criterion proposals"}: ${scheme.blocked_proposal_dimensions}`, "field-help"));
    for (const question of scheme.questions || []) {
      const group = node("details", null, "question-review");
      group.id = `evaluatorFullSchemeQ${question.index + 1}`;
      add(group, node("summary", `Q${question.index + 1} · ${question.title} · ${question.evaluation_status}`));
      for (const axis of ["technical", "communication"]) {
        const item = question[axis] || {};
        add(group, node("p", `${axis}: ${item.observed_provisional_points ?? "NOT_EVALUATED"} / ${item.covered_weight ?? 0} ` +
          `(${item.observed_dimensions || 0}/${item.total_dimensions || 0} dimensions) · NOT_SCORED`, "field-help"));
      }
      const practice = question.practice_communication;
      if (practice?.status === "NO_RECORDED_DEMONSTRATION") add(group, node("p", zh
        ? "本次记录中的沟通展示：0 / 40（没有解释性沟通记录；保留原模型评估）"
        : "Recorded communication demonstration: 0 / 40 (no explanation recorded; original model review retained)", "notice"));
      const sql = question.sql || {};
      add(group, node("p", `${zh ? "SQL执行" : "SQL execution"}: ${sql.local_execution || "NOT_VERIFIED"} · ` +
        `${zh ? "静态审查" : "Static SQL review"}: ${sql.static_review || "UNAVAILABLE"} · ` +
        `T01: ${sql.correctness_grade || "NOT_SCORED"}`, "notice"));
      if (sql.dialect_note) add(group, node("p", sql.dialect_note, "field-help"));
      if (question.blocked_criterion_ids?.length)
        add(group, node("p", `${zh ? "已拦截" : "Blocked"}: ${question.blocked_criterion_ids.join(", ")}`, "notice"));
      const criterionDetails = node("details", null, "question-review");
      add(criterionDetails, node("summary", zh ? "查看全部11项指标与证据入口" : "Inspect all 11 criteria and source links"));
      for (const criterion of question.dimensions || []) {
        const v = node("div", null, "field-help");
        add(v, node("p", `${criterion.id} · ${criterion.status} · ` +
          `${criterion.eligible_provisional_points ?? "UNOBSERVED"}/${criterion.max_points} · ${criterion.admissibility}`));
        if (criterion.citations?.length) {
          const jump = node("button", zh ? "查看评分原文" : "Open criterion & citations", "button text");
          jump.type="button";
          jump.addEventListener("click", () => {
            evaluatorQuestionIndex = question.index;
            render();
            const item = document.getElementById(`evaluatorCriterion-${criterion.id}`);
            if (item) {item.open=true; item.scrollIntoView({block:"center"});}
          });
          add(v, jump);
        }
        add(criterionDetails, v);
      }
      add(group, criterionDetails);
      add(section, group);
    }
    if (scheme.drill_candidates?.length) {
      const drills = node("details", null, "question-review");
      add(drills, node("summary", zh ? "根据已有弱项证据生成的练习候选" : "Evidence-linked practice candidates"));
      for (const drill of scheme.drill_candidates)
        add(drills, node("p", `Q${drill.question_index+1} · ${drill.criterion_id} · ${drill.kind} · ` +
           (drill.evidence_event_ids || []).join(", "), "field-help"));
      add(drills, node("p", zh ? "这些是练习线索，不是已验证能力缺陷。" : "Drills are suggestions, not certified competency gaps.", "notice"));
      add(section, drills);
    }
    const trace = node("details", null, "question-review");
    add(trace, node("summary", zh ? "审计哈希与发布限制" : "Audit digest and release constraints"),
      node("code", scheme.sha256 || "", "digest"),
      node("p", `${(scheme.release_blockers || []).join(" · ")}`, "field-help"));
    add(section, trace);
    return section;
  }
  // E4: read-only closed-loop navigator. All source records remain Host-owned.
  // Export and SMART actions use existing Native commands; nothing is auto-approved.
  function evaluatorCloseoutModel(snapshot) {
    const rehearsal = snapshot?.rehearsal || {};
    const scheme = snapshot?.evaluator_report?.full_scheme || {};
    const smart = snapshot?.smart_plan || {};
    const progress = snapshot?.smart_progress_summary || {};
    const trainer = snapshot?.grounded_trainer || {};
    const locked = rehearsal.status === "COMPLETE" && Array.isArray(rehearsal.results) && rehearsal.results.length === 3;
    const assessmentCount = Number.isInteger(scheme.evaluations_current) ? scheme.evaluations_current : 0;
    const legacyCount = Number.isInteger(scheme.evaluations_legacy) ? scheme.evaluations_legacy : 0;
    const entries = Number.isInteger(progress.recorded_attempts) ? progress.recorded_attempts : 0;
    const drills = Array.isArray(trainer.drills) ? trainer.drills.length : 0;
    return {
      schema: "tia-evaluator-closeout-view/v1",
      locked, assessmentCount, legacyCount, entries, drills,
      schemeReady: scheme.schema === "tia-evaluator-full-scheme/v1",
      smartReady: smart.schema === "tia-smart-improvement-plan/v1" && smart.status === "READY_TO_START",
      evidenceStatus: locked ? "FROZEN" : "INCOMPLETE",
      evaluationStatus: assessmentCount === 3 ? "THREE_PROVISIONAL_PROPOSALS" : "PENDING_OR_LEGACY_ONLY",
      trainerStatus: drills ? "EVIDENCE_LINKED_DRILLS_AVAILABLE" : "NO_EVIDENCED_DRILL_YET",
      practiceStatus: entries ? "SELF_REPORTED_ACTIVITY_ONLY" : "NO_RECORDED_PRACTICE",
      archiveStatus: "USER_EXPORT_REQUIRED_UNATTESTED",
      retestStatus: "AWAITING_INDEPENDENT_NEXT_SESSION",
      grade: "NOT_SCORED",
    };
  }

  function evaluatorCloseoutPanel() {
    if (state.screen !== "REHEARSAL_COMPLETE") return null;
    const model = evaluatorCloseoutModel(state);
    const zh = state.language === "zh";
    const section = node("section", null, "receipt-card");
    section.id = "evaluatorCloseoutPanel";
    add(section,
      node("h2", zh ? "面试后行动闭环 · 证据 → 训练 → 归档 → 复测" : "Post-interview closeout · evidence → practice → archive → retest"),
      node("p", zh ? "这个导航不改变评分和面试记录；训练是自报，导出需要用户主动保存，复测必须产生新会话。" :
        "This navigator never alters an assessment. Practice is self-reported, archive requires your export, and retest requires a new session.", "notice"));
    const stages = [
      ["01", zh ? "冻结证据" : "Evidence locked", model.evidenceStatus, "interviewTranscript"],
      ["02", zh ? "评估与审计" : "Evaluation and audit", model.evaluationStatus, "evaluatorFullScheme"],
      ["03", zh ? "有来源的训练" : "Evidence-linked Trainer", model.trainerStatus, "groundedTrainer"],
      ["04", zh ? "SMART 活动" : "SMART practice ledger", model.practiceStatus, "smartPlanPanel"],
      ["05", zh ? "私人归档与下一次复测" : "Private archive and next retest", model.archiveStatus, null],
    ];
    for (const [number, label, status, target] of stages) {
      const line = node("div", null, "field-help");
      add(line, node("p", `${number} · ${label}: ${status}`));
      if (target) {
        const link = button(`closeoutStep${number}`, zh ? "定位到该环节" : "Open section", () => {
          const item = document.getElementById(target);
          if (item) item.scrollIntoView({block:"start"});
        }, "secondary");
        add(line, link);
      }
      add(section, line);
    }
    add(section, node("p", `${zh ? "待审核模型提案" : "Current model proposals"}: ${model.assessmentCount}/3 · ` +
      `${zh ? "历史版" : "Legacy"}: ${model.legacyCount} · ` +
      `${zh ? "训练活动" : "Self-reported activity"}: ${model.entries} · Overall: ${model.grade}`, "field-help"));
    const archive = button("closeoutExport", zh ? "导出私有完整回执" : "Export private session receipt", () => act("export"), "primary");
    add(section, archive,
      node("p", zh ? "导出后可用随附的本地 History Ledger 命令只记录最小摘要，随后开始新会话进行独立复测。导出动作本身不代表已成功归档。" :
        "After exporting, use the local History Ledger helper to store a minimal timeline entry, then begin a separately recorded retest. Clicking export does not attest successful archiving.", "notice"),
      node("p", zh ? "无人工UAT；没有实际执行核验或规则校准时不能发布正式招聘能力分数。" :
        "No human UAT. Without verified execution and calibrated scoring, formal hiring grades remain unavailable.", "field-help"));
    return section;
  }

  function rehearsalComplete(main) {
    const rs = state.rehearsal || {};
    const finalTitle = rs.status === "TIMED_OUT" ? "rehearsalTimeout" :
      rs.status === "CLOCK_INTEGRITY_HOLD" ? "rehearsalClockHold" : "rehearsalComplete";
    add(main, heading(t(finalTitle)), node("p", t("rehearsalNote"), "notice"));
    if (rs.timing) add(main, rehearsalClock());
    add(main, fullInterviewTranscript());
    add(main, evidenceScorecard(), communicationEvidence(), evaluatorPanel(), fullEvaluatorSchemePanel(), groundedTrainer(), nativeTrainerPanel(), smartPlanPanel(), evaluatorCloseoutPanel());
    const offlineDemos = [evaluatorV1MvmPanel(), evaluatorV1MockPanel()].filter(Boolean);
    if (offlineDemos.length) {
      const demos = node("details", null, "question-review"); demos.id = "evaluatorOfflineDemos";
      add(demos, node("summary", state.language === "zh" ? "离线工程演示" : "Offline engineering demonstrations"),
        node("p", state.language === "zh"
          ? "下方示例仅用于验证实验规则与算术，不是此次面试的评估或候选人成绩。真实模型评审位于上方独立 AI Evaluator 面板。"
          : "These examples verify experimental policy and arithmetic only. They are not this interview's assessment or candidate score. The independent AI Evaluator panel above contains the model review.", "notice"),
        ...offlineDemos);
      add(main, demos);
    }
    // Saved interview evidence is immutable. Show only derived, unscored warnings.
    for (const review of state.language_reviews?.completed || []) {
      if (review.status !== "LANGUAGE_MISMATCH_REVIEW_REQUIRED") continue;
      const warning = node("p", state.language === "zh"
        ? `问题 ${review.question_index + 1}：预期 ${review.expected_environment}，提交内容疑似 ${review.observed_style}。需要人工确认；没有执行或判分。`
        : `Question ${review.question_index + 1}: expected ${review.expected_environment}; submission appears ${review.observed_style}. Human review required; no execution or correctness assessment.`, "notice");
      warning.id = `languageMismatchQ${review.question_index + 1}`;
      add(main, warning);
    }
    // Old raw receipts are preserved, including prior SQL versions. For current
    // correctness refer to the source-bound E3 scorecard above instead.
    (rs.results || []).forEach((r, i) => {
      const question = rs.questions?.[i] || {};
      const verified = state.evidence_scorecard?.questions?.[i]?.accuracy?.status || "NOT_VERIFIED";
      add(main, add(node("section", null, "receipt-card"),
        node("h2", `${i + 1}. ${question.title || "Question"}`),
        node("p", `${r.outcome} · ${verified} · NOT_SCORED`),
        r.session?.receipt?.sha256 ? node("code", r.session.receipt.sha256, "digest") : null));
    });
    // Source-bound examples remain available in the frozen final report.
    (rs.questions || []).forEach((q, i) => {
      const examples = exampleCardsForQuestion(q);
      if (!examples) return;
      const detail = node("details", null, "question-review");
      add(detail, node("summary", `${i + 1}. ${q.title || "Question"} · ${state.language === "zh" ? "查看输入、输出与解析" : "View examples & explanations"}`), examples);
      add(main, detail);
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
  // S03-E3D-P1: secondary, reviewable decoder for pasted LeetCode screen chrome.
  // Crucially, the Host raw_input and saved journal are never rewritten.
  function cleanSourceDraft(fields) {
    const output = {...fields};
    const chrome = /^(?:Solved|Attempted|Topics|Companies|Premium|Discussion|Pandas Schema|SQL Schema|premium lock icon)$/i;
    for (const key of ["problem_statement", "schema", "constraints"]) {
      if (typeof output[key] === "string") {
        output[key] = output[key].split(/\r?\n/)
          .filter(line => !chrome.test(line.trim())).join("\n").trim();
      }
    }
    return output;
  }
  const REVIEW_FIELDS = ["problem_statement", "task", "schema", "example_input", "expected_output",
    "environment", "source", "constraints", "source_reference"];
  function editableQuestion(section, review, index) {
    if (!review) return;
    const sha = review.raw_sha256;
    if (!questionFieldDrafts[index] || questionFieldDrafts[index].raw_sha256 !== sha) {
      questionFieldDrafts[index] = {raw_sha256: sha, fields: cleanSourceDraft(review.fields)};
    }
    const edit = questionFieldDrafts[index].fields;
    const form = node("div", null, "review-editor");
    add(form, node("p", t("reviewGuidance"), "field-help"));
    if (JSON.stringify(edit) !== JSON.stringify(review.fields)) {
      add(form, node("p", state.language === "zh"
        ? "已从可编辑草稿去除部分 LeetCode 页面标签；原文及来源仍保存。确认前请检查全部字段。"
        : "LeetCode page labels were removed from the editable draft only. Original source is preserved; review all fields before confirming.", "notice"));
    }
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
    const start = button("startRehearsal", t("rehearsalStart"), () => act("rehearsal_start", {continuity_policy: "tia-continuity/v3"}), "primary full-width");
    start.dataset.unavailable = String(!eligible);
    start.disabled = busy || !eligible;
    return add(node("section", null, "preview-start-card"),
      node("h2", t("rehearsalStart")), node("p", t("rehearsalNote"), "field-help"),
      node("p", state.language === "zh"
        ? "先逐题提取并人工确认。点击开始后进入原生 API Portal；验证模型访问才会触发明确授权的付费请求。"
        : "Extract and confirm every question first. Start opens the native API Portal; a paid model request requires separate explicit consent.", "notice"), start);
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
        const label = node("label", `${t("questionNumber")} ${index + 1} / ${count} · ${state.language === "zh" ? "练习不限难度" : "practice: any difficulty"}`);
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
    // E4-C0: purely derived readiness. No solving, model or SQL execution.
    const pf = state.preflight_readiness;
    if (pf?.schema === "tia-preflight-readiness/v1") {
      const zh = state.language === "zh";
      const section = node("section", null, "receipt-card");
      section.id = "preflightReadiness";
      add(section, node("h2", zh ? "面试备课就绪检查 · E4-C0" : "Pre-interview readiness · E4-C0"),
        node("p", zh
          ? "仅核对已确认的题目及来源校验。尚未生成参考解法、运行代码或调用模型。"
          : "Checks confirmed question provenance only. No solutions generated, code run or paid model calls.", "notice"),
        node("p", `${pf.confirmed_count}/${pf.required_count ?? "?"} ${zh ? "道题已确认" : "questions confirmed"} · ${pf.status}`, "field-help"));
      for (const q of pf.questions || []) {
        add(section, node("p", `Q${q.question_index + 1} · ${q.environment} · ${q.status} · ${q.reference_status}`, "field-help"));
      }
      if (pf.required_count === 4) add(section, node("p", zh
        ? "四题备课结构可检查，但目前四题 Live 面试尚未实现。"
        : "Four-question source review supported; four-question LIVE launch not implemented.", "notice"));
      if (pf.status === "READY_FOR_FUTURE_PRIVATE_PREPARATION") {
        const prep = state.native_private_preparer;
        const completed = ["REFERENCE_UNVERIFIED_AI_PROPOSAL", "REFERENCE_VERIFIED_LOCAL_FIXTURE"].includes(prep?.status);
        add(section, node("p", `${zh ? "原生私有备课" : "Native private preparation"} · ${prep?.status || "NOT_PREPARED"}`, "field-help"));
        if (!completed) add(section, button("preparerRequest", zh ? "私有备课全部题目 · 1 次付费请求" : "Prepare all questions privately · 1 paid request", () => act("preparer_request", {}), "secondary"));
        if (completed) {
          for (const q of prep.questions || []) {
            add(section, node("p", `Q${q.index + 1} · ${q.status}`, "field-help"));
            const binding = node("details", null, "question-review");
            add(binding, node("summary", zh ? "本地测试题目绑定" : "Local test question binding"), node("code", q.question_sha256, "digest"));
            add(section, binding);
            if (q.environment === "POSTGRESQL") add(section, button(`verifyOracle${q.index}`,
              zh ? `核验第 ${q.index + 1} 题参考方案 · 本地测试` : `Verify Q${q.index + 1} reference · local tests`,
              () => act("preparer_verify", {question_index: q.index}), "secondary"));
          }
          if (prep.verification_pending) add(section, node("p", zh ? "正在本地核验私有参考方案…" : "Verifying private references locally…"),
            interruptButton("cancelOracle", zh ? "取消核验" : "Cancel verification", "preview_cancel"));
          add(section, node("p", zh
            ? "三道题参考方案已准备。每题验证状态见上方；只有独立本地测试通过的方案才标记为已验证。面试官只读取公开题目。"
            : "References prepared for all three questions. Verification status is shown per question; only independently tested proposals are verified. The interviewer sees public questions only.", "notice"));
          if (pf.required_count === 3 && (prep?.question_count == null || prep.question_count === 3)) {
            add(section, node("h3", zh ? "候场室 · 面试官已就绪" : "Waiting room · Interviewer ready"),
              node("p", zh ? "进入后按题目顺序开始；每题 15 分钟，需明确提交、跳过或计时归零才能转场。" : "Enter in question order. Each question lasts 15 minutes; only final submission, skip or timeout advances.", "field-help"),
              button("enterPreparedInterview", zh ? "进入面试室 →" : "Enter interview room →", () => act("rehearsal_start", {continuity_policy: "tia-continuity/v3"}), "primary"));
          }
        }
      }
      add(main, section);
    }
    const table = node("table", null, "review-table");
    const body = node("tbody");
    const rows = [
      [t("environment"), config.technical_environment], [t("duration"), `${config.duration_minutes} ${t("minutes")}`],
      [t("questionCount"), `${config.question_count} × ${state.language === "zh" ? "自带练习题（不限难度）" : "reviewed BYOQ practice (any difficulty)"}`],
      [t("sourceLabel"), config.question_source === "BYOQ" ? t("byoq") : t("randomized")],
      [t("mechanismLabel"), config.interviewer_mechanism === "STRICT_CHALLENGING" ? t("strict") : t("supportive")],
      [t("configDigest"), config.sha256 || "UNVERIFIED"],
    ];
    rows.forEach(([label, value]) => {
      const th = node("th", label); th.scope = "row";
      add(body, add(node("tr"), th, node("td", value)));
    });
    add(table, body); add(main, table);
    // Put the actual working path BEFORE long question reviews and provenance.
    if (config.question_source === "BYOQ" && config.duration_minutes === 45) {
      if (!["REFERENCE_UNVERIFIED_AI_PROPOSAL", "REFERENCE_VERIFIED_LOCAL_FIXTURE"].includes(state.native_private_preparer?.status)) {
        add(main, rehearsalStartButton());
      }
    }
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
    // Formal grading still fails closed. Show limitations on demand, rather than
    // making a guaranteed-failing host command the user's primary CTA.
    const blockers = node("details", null, "launch-blockers");
    blockers.id = "formalLaunchLimits";
    add(blockers, node("summary", t("blockers")), issueList(state.setup_blockers || []),
      node("p", t("preflightNote"), "muted"));
    add(main, blockers, node("p", t("rubricNote"), "notice"), scores(true),
      setupNav(button("launchPreflight", t("launchPreflight"), () => {
        blockers.open = true;
        blockers.scrollIntoView({block: "nearest"});
      }, "secondary")), previewStartCard());
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
      state.screen === "LIVE_PREVIEW" ? t("livePreview") : state.screen === "REHEARSAL_COMPLETE" ? t("rehearsalComplete") : `${t("tutorialStep")} ${step} / 5`;
    const meter = node("progress");
    meter.max = setupStep ? 4 : 5;
    meter.value = state.screen === "REHEARSAL_COMPLETE" ? 5 : state.screen === "LIVE_PREVIEW" ? (state.live_preview?.closed ? 5 : 3) : setupStep || step;
    meter.setAttribute("aria-label", label);
    add(progress, add(node("div", null, "progress-label"), badge(label),
      node("span", ["API_PORTAL", "LIVE_PREVIEW", "REHEARSAL_COMPLETE"].includes(state.screen) || setupStep ? modelLabel() : t("simulated"), "muted")), meter);
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
    window.TIAVoice?.update(state, state.activation);
    window.TIAVoice?.receive(state.voice || {});
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
