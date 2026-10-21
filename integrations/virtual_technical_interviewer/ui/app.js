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
  let questionDrafts = [];
  let previousScreen = null;
  const strings = {
    en: {
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
      portal: "Open native API Portal…", disconnected: "Disconnect", apiGate: "Live AI is disabled in this increment. Entering a key does not verify it or authorize a paid request. Real interview launch stays blocked.",
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
      prepareSetup: "Prepare setup · verification pending",
      setupPending: "Local setup only. Provider authentication is pending; no live interview or paid request is authorized.",
      configuration: "Interview configuration", environment: "Technical environment",
      duration: "Session duration", minutes: "minutes", questionCount: "Questions · derived from duration",
      hardOnly: "Hard · fixed for real interviews", configNote: "45 minutes requires 3 questions; 60 minutes requires 4. The host validates this contract.",
      continueSetup: "Next →", sourceTitle: "Select question source", sourceLabel: "Question source",
      byoq: "Bring your own question · LeetCode / HackerRank", randomized: "Randomized · approved dataset pool",
      sourceInstructions: "Provide each question as JSON or explicit English headings. Required: problem statement, task, schema / DataFrame definitions, example input, expected output, environment and source. Constraints and source reference are optional.",
      sourceSafety: "Structural review is not SQL execution or hidden-test validation. Missing or conflicting information blocks progression; remaining slots are never silently filled.",
      questionNumber: "Question", emptyTemplate: "Insert empty template", bytes: "UTF-8 bytes",
      importTooLarge: "This question exceeds the 4096-byte interface limit. Shorten it before review.",
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
      portal: "打开原生 API Portal…", disconnected: "断开连接", apiGate: "此增量尚未启用真实 AI。输入 Key 不代表验证成功，也不授权付费请求。真实面试仍禁止启动。",
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
      prepareSetup: "准备配置 · 待验证",
      setupPending: "仅准备本地配置。服务商身份验证仍待完成；尚未授权真实面试或付费请求。",
      configuration: "面试配置", environment: "技术环境", duration: "会话时长", minutes: "分钟",
      questionCount: "题目数量 · 根据时长推导", hardOnly: "Hard · 真实面试固定难度",
      configNote: "45 分钟必须为 3 题，60 分钟必须为 4 题。此约束由宿主验证。",
      continueSetup: "下一步 →", sourceTitle: "选择题目来源", sourceLabel: "题目来源",
      byoq: "自带题目 · LeetCode / HackerRank", randomized: "随机面试 · 已批准的数据集题库",
      sourceInstructions: "每题使用 JSON 或明确的英文标题字段。必填：problem statement、task、schema / DataFrame definitions、example input、expected output、environment、source。constraints 与 source reference 可选。",
      sourceSafety: "结构审查不代表 SQL 执行或隐藏测试验证。缺失或冲突的信息会阻止继续；剩余题目不会被静默补齐。",
      questionNumber: "题目", emptyTemplate: "插入空白模板", bytes: "UTF-8 字节",
      importTooLarge: "此题超过界面的 4096 字节上限，请精简后再审查。",
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
  function setBusy(value) {
    busy = value;
    app.setAttribute("aria-busy", String(value));
    for (const element of app.querySelectorAll("button, select, textarea")) {
      element.disabled = value || element.dataset.unavailable === "true";
    }
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
      const timer = awaitsHuman ? null : setTimeout(() => {
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
        if (item.action === "reset") questionDrafts = [];
      }
      state = response.state;
      // Read-only diagnostic copy for native UI tests. It is never submitted as authority.
      window.tiaState = JSON.parse(JSON.stringify(state));
      render();
      document.documentElement.dataset.tiaReady = "true";
    }
    if (response.ok === true && hasState) {
      if (item?.action === "tutorial_submit") announcement.textContent = t("recordedNotice");
      item?.resolve(state);
    } else {
      const code = typeof response.error === "string" ? response.error :
        (typeof response.error?.code === "string" ? response.error.code : "HOST_ERROR");
      showError(`${t("requestFailed")} (${code.slice(0, 100)})`);
      item?.reject(new Error(code));
    }
    setBusy(pending.size > 0);
  };
  function act(action, params = {}) {
    if (busy) return;
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
  function questionCard(compact = false) {
    const q = state.question || {};
    const card = node("section", null, `question-card${compact ? " compact" : ""}`);
    add(card, badge(t("medium")), node(compact ? "h3" : "h2", q.title || "First Order per Customer"),
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
    for (const [name, status] of [["technical", "notScored"], ["communication", "notScored"],
      forSetup ? ["technicalExecution", "unverifiedStatus"] : ["execution", "notRun"]]) {
      add(grid, add(node("div", null, "evidence-item"), node("span", t(name), "muted"), node("strong", t(status))));
    }
    return grid;
  }
  function conversation() {
    const box = node("section", null, "conversation");
    add(box, node("h2", t("recorded")));
    const events = (state.session?.events || []).filter(event =>
      event.actor === "candidate" || (event.actor === "interviewer" && event.kind === "reply"));
    if (!events.length) add(box, node("p", t("emptyHistory"), "muted"));
    for (const event of events) {
      const candidate = event.actor === "candidate";
      const payload = event.payload || {};
      const text = typeof payload.text === "string" ? payload.text : "";
      if (!text) continue;
      const entry = node("div", null, `transcript-entry ${candidate ? "candidate" : "interviewer"}`);
      add(entry, node("div", candidate ? `${t("candidate")} · ${t(event.kind || "response")}` : t("feedback"), "transcript-speaker"),
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
  function apiPortal(main) {
    add(main, badge(t("portalStep")), heading(t("api")), node("p", t("apiBody"), "lead"));
    const card = node("section", null, "portal-card");
    add(card, node("h2", "OpenAI"), badge(modelLabel()), node("p", t("apiGate"), "notice"),
      node("p", `${t("requests")}: ${requestCount()}`, "muted"),
      actions(button("openPortal", t("portal"), () => act("api_portal"), "primary"),
        button("disconnect", t("disconnected"), () => act("disconnect"))));
    if (state.activation?.state === "activated-unverified") {
      add(card, node("p", t("setupPending"), "notice"),
        button("prepareSetup", t("prepareSetup"), () => act("setup_continue"), "primary full-width"));
    }
    add(main, card, nav());
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
      act("setup_questions", {questions: config.question_source === "BYOQ" ?
        Array.from({length: count}, (_, index) => questionDrafts[index] || "") : []});
    }, "primary");
    if (config.question_source === "BYOQ") {
      add(main, node("p", t("sourceInstructions"), "notice"), node("p", t("sourceSafety"), "notice"));
      const utf8 = value => new TextEncoder().encode(value).length;
      const validateSizes = () => {
        const tooLarge = Array.from({length: count}, (_, index) => utf8(questionDrafts[index] || "")).some(size => size > 4096);
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
        const label = node("label", `${t("questionNumber")} ${index + 1} / ${count} · HARD`);
        label.htmlFor = `byoqQuestion${index}`;
        const input = node("textarea");
        input.id = `byoqQuestion${index}`;
        input.rows = 10;
        input.spellcheck = false;
        input.autocapitalize = "off";
        input.value = questionDrafts[index];
        const size = node("p", null, "field-help");
        size.id = `byoqSize${index}`;
        input.setAttribute("aria-describedby", size.id);
        const updateSize = () => {
          const length = utf8(input.value);
          size.textContent = `${length} / 4096 ${t("bytes")}${length > 4096 ? ` · ${t("importTooLarge")}` : ""}`;
          input.setAttribute("aria-invalid", String(length > 4096));
          validateSizes();
        };
        input.addEventListener("input", () => { questionDrafts[index] = input.value; updateSize(); });
        const template = button(`questionTemplate${index}`, t("emptyTemplate"), () => {
          if (busy) return;
          input.value = JSON.stringify({
            problem_statement: "", task: "", schema: "", example_input: "", expected_output: "",
            environment: config.technical_environment, source: "OWNER", constraints: "", source_reference: "",
          }, null, 2);
          questionDrafts[index] = input.value;
          template.dataset.unavailable = "true";
          template.disabled = true;
          updateSize();
          input.focus();
        }, "text");
        template.disabled = Boolean(input.value.trim());
        template.dataset.unavailable = String(Boolean(input.value.trim()));
        input.addEventListener("input", () => {
          template.dataset.unavailable = String(Boolean(input.value.trim()));
          template.disabled = busy || Boolean(input.value.trim());
        });
        add(section, label, input, size, template, questionReview(review, index));
        add(main, section);
        updateSize();
      }
      validateSizes();
    } else {
      add(main, node("p", t("randomBlocked"), "setup-warning"));
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
    const blockers = node("section", null, "launch-blockers");
    add(blockers, node("h2", t("blockers")), issueList(state.setup_blockers || []),
      node("p", t("preflightNote"), "muted"));
    add(main, blockers, node("p", t("rubricNote"), "notice"), scores(true),
      setupNav(button("launchPreflight", t("launchPreflight"), () => act("setup_launch"), "primary")));
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
      state.screen === "ENTRY" ? t("entryStep") : state.screen === "API_PORTAL" ? t("portalStep") : `${t("tutorialStep")} ${step} / 5`;
    const meter = node("progress");
    meter.max = setupStep ? 4 : 5;
    meter.value = setupStep || step;
    meter.setAttribute("aria-label", label);
    add(progress, add(node("div", null, "progress-label"), badge(label),
      node("span", state.screen === "API_PORTAL" || setupStep ? modelLabel() : t("simulated"), "muted")), meter);
    const main = node("main"); main.id = "main";
    const screens = {
      ENTRY: entry, WELCOME: welcome, RULES: rules, QUESTION: question, ROOM: room, COMPLETE: complete,
      API_PORTAL: apiPortal, CONFIG: configuration, QUESTION_SOURCE: questionSource, MECHANISM: mechanism, REVIEW: setupReview,
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
    const footer = node("footer", null, "footer");
    add(footer, node("span", `${modelLabel()} · ${t("requests")}: ${requestCount()}`),
      node("span", state.saved_locally ? t("saved") : t("notSaved")));
    add(shell, header, progress, main, footer);
    app.replaceChildren(shell);
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
  request("snapshot").catch(() => {});
})();
