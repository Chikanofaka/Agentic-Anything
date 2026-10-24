"use strict";

// Voice is a presentation plugin. Native Swift owns audio, recognition, consent,
// speaking and sending; the existing controller still owns every interview turn.
// No Web Speech APIs, network requests, storage, SQL submission or host decisions.
(() => {
  const copy = {
    en: {
      title: "Interviewer", companion: "Interviewer voice companion", open: "Expand voice companion", collapse: "Collapse voice companion",
      move: "Move voice companion. Drag, or use arrow keys. Shift moves farther; Home resets position.",
      local: "Local audio · live interviewer", mic: "Listen", pause: "Pause mic", micOn: "Mic is listening", micOff: "Microphone paused",
      mute: "Mute voice", unmute: "Unmute voice", replay: "Replay reply", caption: "Interviewer caption", emptyCaption: "Committed interviewer replies appear here.",
      kind: "Speaking as", clarify: "Clarification", plan: "Plan / think aloud", test: "Test idea", help: "Help request",
      draft: "Your voice draft", placeholder: "Speak, pause, then review your words…", partial: "Hearing…", clear: "Clear", send: "Send · 1 AI request",
      bytes: "UTF-8 bytes", tooLong: "Shorten this draft before sending (4096 UTF-8 bytes maximum).", empty: "Nothing has been sent.",
      handsfree: "Send completed speech automatically", handsfreeNote: "On by default for each new question. Each completed utterance can use one authorized AI request. Pause the mic or turn this off to work at your own pace.",
      helpText: "Think aloud, clarify or ask for help. Submit SQL in the code editor; voice never submits or runs code. The host still decides permitted guidance.",
      settings: "Voice settings & privacy", language: "Speech language", rate: "Speaking speed", normal: "Normal", slow: "Slower", fast: "Faster",
      privacy: "Audio stays on this Mac. On-device speech recognition must be available. Only speech you send becomes interview text sent to the already authorized AI provider. No audio API calls.",
      statusPermission: "Waiting for microphone permission", statusReady: "Ready · mic paused", statusListen: "Listening on this Mac", statusSpeak: "Interviewer speaking", statusWaiting: "Waiting for interviewer", statusPaused: "Mic paused", statusMuted: "Voice muted",
      statusUnavailable: "Local speech unavailable", failed: "Voice action could not finish. You can keep using the text interview.", permission: "Allow microphone and speech recognition in macOS Privacy & Security, then try again.", unavailable: "On-device recognition is unavailable for this language. Choose another installed language or use the text interview.", cancelled: "Voice action cancelled. No new request was sent.", limit: "The approved turn or request limit has been reached. Use the interview controls to continue.",
      count: "Approved AI requests", listeningEdit: "Pause the microphone to edit your draft.",
    },
    zh: {
      title: "面试官", companion: "面试官语音伙伴", open: "展开语音伙伴", collapse: "收起语音伙伴",
      move: "移动语音伙伴。拖动或使用方向键；Shift 加速，Home 恢复位置。",
      local: "本地语音 · 真实 AI 面试官", mic: "开始听取", pause: "暂停麦克风", micOn: "麦克风正在听取", micOff: "麦克风已暂停",
      mute: "静音朗读", unmute: "恢复朗读", replay: "重播回复", caption: "面试官字幕", emptyCaption: "已确认的面试官回复将显示在此处。",
      kind: "发言类型", clarify: "澄清问题", plan: "方案 / 口述思路", test: "测试想法", help: "请求帮助",
      draft: "你的语音草稿", placeholder: "说出想法，暂停后核对文字…", partial: "正在识别…", clear: "清空", send: "发送 · 1 次 AI 请求",
      bytes: "UTF-8 字节", tooLong: "请缩短草稿后再发送（最多 4096 UTF-8 字节）。", empty: "尚未发送任何内容。",
      handsfree: "自动发送已完成的发言", handsfreeNote: "每道新题默认开启，每段发言可消耗一次已授权 AI 请求。可暂停收音或关闭自动发送，按自己的节奏作答。",
      helpText: "口述思路、澄清或求助。SQL 请在代码编辑器中提交；语音不会提交或执行代码。允许提供的提示仍由宿主决定。",
      settings: "语音设置与隐私", language: "识别与朗读语言", rate: "朗读速度", normal: "正常", slow: "较慢", fast: "较快",
      privacy: "音频留在这台 Mac 上，须支持设备端识别。只有你发送的文字会成为面试记录，并交给已授权的 AI 服务。没有音频 API 调用。",
      statusPermission: "等待麦克风授权", statusReady: "已就绪 · 麦克风暂停", statusListen: "正在本机听取", statusSpeak: "面试官正在朗读", statusWaiting: "正在等待面试官", statusPaused: "麦克风已暂停", statusMuted: "朗读已静音",
      statusUnavailable: "本地识别不可用", failed: "语音操作未能完成；你仍可通过文字继续面试。", permission: "请在 macOS“隐私与安全性”中允许麦克风与语音识别后重试。", unavailable: "当前语言的设备端识别不可用。请选择其他已安装语言或通过文字继续。", cancelled: "语音操作已取消，没有发送新请求。", limit: "已达到授权的交互或请求上限，请使用面试控制继续。",
      count: "已授权 AI 请求", listeningEdit: "暂停麦克风后可编辑草稿。",
    },
  };
  let send = null, host = null, voice = {}, refs = null;
  let collapsed = true, moved = false, localDraft = "", draftDirty = false;
  let localError = "", actionPending = false, composing = false, drag = null;
  let draftRevision = 0, lastCaption = "", lastWord = "", lastRoom = null;
  const encoder = new TextEncoder();
  const t = key => copy[host?.language === "zh" ? "zh" : "en"][key];
  const node = (tag, id, className = "") => {
    const result = document.createElement(tag);
    if (id) result.id = id;
    if (className) result.className = className;
    return result;
  };
  const text = (target, value) => { if (target.textContent !== value) target.textContent = value; };
  const button = (id, listener, className = "") => {
    const result = node("button", id, `voice-button ${className}`); result.type = "button";
    result.addEventListener("click", listener); return result;
  };
  const option = (value, label) => { const result = node("option"); result.value = value; result.textContent = label; return result; };
  const string = (value, limit = 8192) => typeof value === "string" ? value.slice(0, limit) : "";
  const roomVisible = () => host?.screen === "LIVE_PREVIEW" && host.live_preview && !host.live_preview.closed && host.activation?.authenticated === true;
  const eligible = () => roomVisible() && voice.eligible === true;
  const hasTurn = () => host?.live_preview?.can_send === true && !host.live_preview.pending;
  const errorMessage = code => {
    if (!code) return "";
    if (/PERMISSION|DENIED|RESTRICTED/.test(code)) return t("permission");
    if (/UNAVAILABLE|ON_DEVICE|RECOGNITION_UNSUPPORTED/.test(code)) return t("unavailable");
    if (/CANCELLED/.test(code)) return t("cancelled");
    if (/LIMIT|BUDGET/.test(code)) return t("limit");
    return t("failed");
  };
  function safeError(error) {
    const value = typeof error === "string" ? error : error?.code || error?.message;
    return typeof value === "string" && /^[A-Z_]{3,80}$/.test(value) ? value : "VOICE_ACTION_FAILED";
  }
  async function command(action, params = {}) {
    if (!send || !eligible()) return;
    try { return await send(action, params); }
    catch (error) { localError = safeError(error); paint(); throw error; }
  }
  // Edits are not sent to the model here. A separate explicit voice_send (or a
  // native-authorized hands-free speech boundary) uses the existing turn path.
  async function flushDraft() {
    if (!draftDirty) return;
    const revision = draftRevision, value = localDraft;
    if (encoder.encode(value).length > 4096) throw new Error("VOICE_DRAFT_TOO_LARGE");
    await command("voice_draft", {text: value});
    if (revision === draftRevision) draftDirty = false;
  }
  async function perform(operation) {
    if (actionPending || !eligible()) return;
    actionPending = true; localError = ""; paint();
    try { await operation(); }
    catch (error) { localError = safeError(error); }
    finally { actionPending = false; paint(); }
  }
  function interrupt(action, params = {}) {
    localError = "";
    command(action, params).catch(() => {});
  }
  function resetDraft() {
    localDraft = ""; draftDirty = false; draftRevision += 1;
    if (refs) refs.draft.value = "";
  }
  function setCollapsed(value) {
    collapsed = value;
    if (refs && value && refs.panel.contains(document.activeElement)) refs.toggle.focus({preventScroll: true});
    paint();
    clampPosition();
  }
  function position(x, y) {
    if (!refs || refs.root.hidden) return;
    const size = refs.root.getBoundingClientRect();
    const margin = 10;
    refs.root.style.left = `${Math.min(Math.max(margin, x), Math.max(margin, innerWidth - size.width - margin))}px`;
    refs.root.style.top = `${Math.min(Math.max(margin, y), Math.max(margin, innerHeight - size.height - margin))}px`;
    refs.root.style.right = "auto"; refs.root.style.bottom = "auto";
  }
  function clampPosition() {
    if (!refs || refs.root.hidden) return;
    const bounds = refs.root.getBoundingClientRect();
    position(moved ? bounds.left : innerWidth - bounds.width - 18, moved ? bounds.top : innerHeight - bounds.height - 18);
  }
  function resetPosition() { moved = false; clampPosition(); }
  function mount(options) {
    if (refs) { if (typeof options?.send === "function") send = options.send; return; }
    if (typeof options?.send !== "function") throw new TypeError("A native voice bridge callback is required");
    send = options.send;
    const root = node("aside", "voiceCompanion", "voice-companion"); root.hidden = true;
    const header = node("div", null, "voice-header");
    const handle = button("voiceDragHandle", () => {}, "voice-drag"); handle.textContent = "⠿";
    const orb = node("span", null, "voice-orb"); orb.setAttribute("aria-hidden", "true");
    for (let i = 0; i < 4; i += 1) orb.append(node("i"));
    const toggle = button("voiceToggle", () => setCollapsed(!collapsed), "voice-toggle");
    const name = node("span", null, "voice-name"); const status = node("span", "voiceStatus", "voice-status");
    status.setAttribute("role", "status"); status.setAttribute("aria-live", "polite");
    toggle.append(orb, (() => { const n = node("span"); n.append(name, status); return n; })());
    toggle.setAttribute("aria-controls", "voicePanel");
    const mic = button("voiceMic", () => {
      if (voice.listening || voice.listening_requested) interrupt("voice_pause");
      else perform(async () => { await flushDraft(); await command("voice_listen"); });
    }, "voice-mic");
    const mute = button("voiceMute", () => interrupt("voice_mute", {muted: voice.muted !== true}), "voice-mute");
    header.append(handle, toggle, mic);
    const panel = node("div", "voicePanel", "voice-panel");
    const local = node("p", null, "voice-local");
    const captionLabel = node("h2", null, "voice-caption-label");
    const caption = node("p", "voiceCaption", "voice-caption"); caption.setAttribute("aria-live", "off");
    const replay = button("voiceReplay", () => perform(() => command("voice_replay")));
    const playback = node("div", null, "voice-row voice-playback"); playback.append(replay, mute);
    const form = node("div", null, "voice-draft-area");
    const kindLabel = node("label"); kindLabel.htmlFor = "voiceKind";
    const kind = node("select", "voiceKind");
    for (const item of ["clarify", "plan", "test", "help"]) kind.append(option(item, item));
    kind.addEventListener("change", () => { const value = kind.value; perform(() => command("voice_kind", {kind: value})); });
    const draftLabel = node("label"); draftLabel.htmlFor = "voiceDraft";
    const draft = node("textarea", "voiceDraft"); draft.rows = 3; draft.maxLength = 4096;
    draft.setAttribute("aria-describedby", "voiceDraftHelp voiceByteCount"); draft.setAttribute("spellcheck", "true");
    draft.addEventListener("compositionstart", () => { composing = true; });
    draft.addEventListener("compositionend", () => { composing = false; draftInput(); });
    const draftInput = () => { localDraft = draft.value; draftDirty = true; draftRevision += 1; localError = ""; paintControls(); };
    draft.addEventListener("input", draftInput);
    draft.addEventListener("keydown", event => {
      if ((event.metaKey || event.ctrlKey) && event.key === "Enter" && !event.isComposing && !composing) {
        event.preventDefault(); if (!refs.submit.disabled) refs.submit.click();
      }
    });
    const partial = node("p", "voicePartial", "voice-partial"); partial.setAttribute("aria-live", "off");
    const byteCount = node("p", "voiceByteCount", "voice-bytes");
    const draftHelp = node("p", "voiceDraftHelp", "voice-help");
    const clear = button("voiceClear", () => perform(async () => { await command("voice_clear"); resetDraft(); }));
    const submit = button("voiceSend", () => perform(async () => {
      await flushDraft(); await command("voice_send");
    }), "voice-primary");
    const draftActions = node("div", null, "voice-row"); draftActions.append(clear, submit);
    form.append(kindLabel, kind, draftLabel, draft, partial, byteCount, draftHelp, draftActions);
    const handsfreeRow = node("label", null, "voice-check");
    const handsfree = node("input", "voiceHandsfree"); handsfree.type = "checkbox";
    const handsfreeText = node("span"); handsfreeRow.append(handsfree, handsfreeText);
    handsfree.addEventListener("change", () => {
      const requested = handsfree.checked;
      perform(async () => { await flushDraft(); await command("voice_handsfree", {enabled: requested}); });
    });
    const handsfreeNote = node("p", null, "voice-help");
    const settings = node("details", null, "voice-settings");
    const summary = node("summary");
    const settingGrid = node("div", null, "voice-setting-grid");
    const languageLabel = node("label"); languageLabel.htmlFor = "voiceLanguage";
    const language = node("select", "voiceLanguage"); language.append(option("en-US", "English"), option("zh-CN", "中文"));
    const rateLabel = node("label"); rateLabel.htmlFor = "voiceRate";
    const rate = node("select", "voiceRate"); for (const item of [0.8, 1, 1.2]) rate.append(option(String(item), String(item)));
    const updateSettings = () => {
      const settings = {language: language.value, rate: Number(rate.value)};
      perform(() => command("voice_settings", settings));
    };
    language.addEventListener("change", updateSettings); rate.addEventListener("change", updateSettings);
    const languageField = node("div"), rateField = node("div"); languageField.append(languageLabel, language); rateField.append(rateLabel, rate); settingGrid.append(languageField, rateField);
    const privacy = node("p", null, "voice-help"); settings.append(summary, settingGrid, privacy);
    const help = node("p", null, "voice-help");
    const budget = node("p", "voiceRequestBudget", "voice-budget");
    const error = node("p", "voiceError", "voice-error"); error.setAttribute("role", "alert"); error.hidden = true;
    panel.append(local, captionLabel, caption, playback, form, handsfreeRow, handsfreeNote, settings, help, budget, error);
    root.append(header, panel); document.body.append(root);
    refs = {root, header, handle, toggle, name, status, mic, mute, panel, local, captionLabel, caption, replay, kindLabel, kind, draftLabel, draft, partial, byteCount, draftHelp, clear, submit, handsfree, handsfreeText, handsfreeNote, summary, languageLabel, language, rateLabel, rate, privacy, help, budget, error};
    handle.addEventListener("pointerdown", event => {
      if (event.button !== 0) return;
      const bounds = root.getBoundingClientRect();
      drag = {id: event.pointerId, x: event.clientX - bounds.left, y: event.clientY - bounds.top};
      moved = true;
      try { handle.setPointerCapture(event.pointerId); } catch (_) { /* Synthetic accessibility/test pointer. */ }
      event.preventDefault(); handle.focus({preventScroll: true});
    });
    handle.addEventListener("pointermove", event => { if (drag?.id === event.pointerId) position(event.clientX - drag.x, event.clientY - drag.y); });
    for (const type of ["pointerup", "pointercancel", "lostpointercapture"]) handle.addEventListener(type, () => { drag = null; });
    handle.addEventListener("keydown", event => {
      if (event.key === "Home") { event.preventDefault(); resetPosition(); return; }
      const delta = {ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1]}[event.key];
      if (!delta) return;
      event.preventDefault(); moved = true;
      const bounds = root.getBoundingClientRect(), step = event.shiftKey ? 40 : 12;
      position(bounds.left + delta[0] * step, bounds.top + delta[1] * step);
    });
    root.addEventListener("keydown", event => { if (event.key === "Escape" && !collapsed) { event.preventDefault(); setCollapsed(true); } });
    window.addEventListener("resize", clampPosition);
    if (typeof ResizeObserver !== "undefined") new ResizeObserver(clampPosition).observe(root);
    paint();
  }
  function captionPaint() {
    const value = string(voice.caption);
    const start = Number.isInteger(voice.word_start) ? voice.word_start : -1;
    const length = Number.isInteger(voice.word_length) ? voice.word_length : 0;
    const word = `${start}:${length}:${voice.speaking === true}`;
    if (value === lastCaption && word === lastWord && refs.caption.childNodes.length) return;
    lastCaption = value; lastWord = word;
    refs.caption.replaceChildren();
    if (!value) { refs.caption.textContent = t("emptyCaption"); return; }
    // Native NSRange indexes and JavaScript string indexes are both UTF-16.
    if (voice.speaking === true && start >= 0 && length > 0 && start + length <= value.length) {
      const highlighted = node("mark"); highlighted.textContent = value.slice(start, start + length);
      refs.caption.append(document.createTextNode(value.slice(0, start)), highlighted, document.createTextNode(value.slice(start + length)));
      const wordBounds = highlighted.getBoundingClientRect(), bounds = refs.caption.getBoundingClientRect();
      if (wordBounds.top < bounds.top) refs.caption.scrollTop -= bounds.top - wordBounds.top + 6;
      else if (wordBounds.bottom > bounds.bottom) refs.caption.scrollTop += wordBounds.bottom - bounds.bottom + 6;
    } else refs.caption.textContent = value;
  }
  function paintControls() {
    if (!refs) return;
    const bytes = encoder.encode(localDraft).length;
    const pending = !!host?.live_preview?.pending;
    const wantsMic = voice.listening === true || voice.listening_requested === true;
    refs.mic.disabled = !eligible() || (!wantsMic && (actionPending || pending || !hasTurn()));
    refs.mic.setAttribute("aria-pressed", String(wantsMic));
    refs.mic.setAttribute("aria-label", t(wantsMic ? "pause" : "mic"));
    refs.mic.title = t(voice.listening ? "micOn" : "micOff");
    text(refs.mic, t(wantsMic ? "pause" : "mic"));
    refs.mute.disabled = !eligible(); refs.mute.setAttribute("aria-pressed", String(voice.muted === true));
    text(refs.mute, t(voice.muted ? "unmute" : "mute"));
    refs.replay.disabled = !eligible() || !voice.caption || actionPending || voice.muted === true;
    refs.draft.readOnly = voice.listening === true || pending || actionPending;
    refs.draft.setAttribute("aria-invalid", String(bytes > 4096));
    text(refs.byteCount, `${bytes} / 4096 ${t("bytes")}`);
    refs.byteCount.classList.toggle("voice-over-limit", bytes > 4096);
    text(refs.draftHelp, bytes > 4096 ? t("tooLong") : voice.listening ? t("listeningEdit") : t("empty"));
    refs.submit.disabled = !eligible() || actionPending || pending || voice.listening === true || !hasTurn() || !localDraft.trim() || bytes > 4096;
    refs.clear.disabled = !eligible() || actionPending || voice.listening === true || pending || (!localDraft && !voice.partial);
    refs.handsfree.disabled = !eligible() || actionPending || pending;
    refs.kind.disabled = !eligible() || actionPending || pending || voice.listening === true;
    refs.language.disabled = refs.rate.disabled = !eligible() || actionPending || pending || voice.listening === true;
  }
  function paint() {
    if (!refs) return;
    const show = eligible();
    if (!show && !refs.root.hidden && refs.root.contains(document.activeElement)) document.getElementById("screenTitle")?.focus({preventScroll: true});
    refs.root.hidden = !show; refs.root.setAttribute("aria-label", t("companion"));
    if (!show) return;
    refs.root.classList.toggle("is-listening", voice.listening === true);
    refs.root.classList.toggle("is-speaking", voice.speaking === true);
    refs.root.classList.toggle("is-collapsed", collapsed);
    refs.panel.hidden = collapsed;
    refs.toggle.setAttribute("aria-expanded", String(!collapsed)); refs.toggle.setAttribute("aria-label", t(collapsed ? "open" : "collapse"));
    refs.handle.setAttribute("aria-label", t("move")); refs.handle.title = t("move");
    text(refs.name, t("title"));
    const status = voice.status === "PERMISSION" ? "statusPermission" : voice.listening ? "statusListen" : voice.speaking ? "statusSpeak" : host?.live_preview?.pending || voice.status === "WAITING" ? "statusWaiting" : voice.error ? "statusUnavailable" : voice.muted ? "statusMuted" : "statusReady";
    text(refs.status, t(status));
    for (const [key, target] of [["local", "local"], ["caption", "captionLabel"], ["replay", "replay"], ["kind", "kindLabel"], ["draft", "draftLabel"], ["clear", "clear"], ["send", "submit"], ["handsfree", "handsfreeText"], ["handsfreeNote", "handsfreeNote"], ["settings", "summary"], ["language", "languageLabel"], ["rate", "rateLabel"], ["privacy", "privacy"], ["helpText", "help"]]) text(refs[target], t(key));
    for (const entry of refs.kind.options) text(entry, t(entry.value));
    for (let i = 0; i < refs.rate.options.length; i += 1) text(refs.rate.options[i], t(["slow", "normal", "fast"][i]));
    refs.kind.value = ["clarify", "plan", "test", "help"].includes(voice.kind) ? voice.kind : "plan";
    refs.language.value = voice.language === "zh-CN" ? "zh-CN" : "en-US";
    refs.rate.value = [0.8, 1, 1.2].includes(voice.rate) ? String(voice.rate) : "1";
    refs.handsfree.checked = voice.handsfree === true;
    refs.draft.placeholder = t("placeholder");
    if (refs.draft.value !== localDraft && !composing) refs.draft.value = localDraft;
    const partial = string(voice.partial, 4096); refs.partial.hidden = !partial;
    text(refs.partial, partial ? `${t("partial")} ${partial}` : "");
    const activation = host.activation || {};
    const used = Number.isInteger(activation.requests_used) ? activation.requests_used : 0;
    const limit = Number.isInteger(activation.request_limit) ? activation.request_limit : "—";
    text(refs.budget, `${t("count")}: ${used} / ${limit} · ${host.language === "zh" ? "本题发言" : "Question turns"}: ${host.live_preview.candidate_turns_used} / ${host.live_preview.candidate_turn_limit}`);
    const error = localError || (voice.error ? safeError(voice.error) : "");
    refs.error.hidden = !error; text(refs.error, errorMessage(error));
    captionPaint(); paintControls(); clampPosition();
  }
  function update(nextHost, provider) {
    const wasVisible = roomVisible();
    const oldLanguage = host?.language;
    host = nextHost && typeof nextHost === "object" ? nextHost : null;
    const room = host?.live_preview ? `${host.live_preview.session?.session_id || ""}:${host.live_preview.question?.content_sha256 || ""}` : null;
    if (!roomVisible() || (lastRoom !== null && room !== lastRoom)) {
      collapsed = true;
      resetDraft(); voice = {}; localError = ""; lastCaption = ""; lastWord = "";
      if (refs) { refs.caption.replaceChildren(); refs.partial.textContent = ""; }
    }
    lastRoom = roomVisible() ? room : null;
    if (oldLanguage !== host?.language) lastCaption = "\u0000";
    if (!wasVisible && roomVisible()) collapsed = true;
    paint();
  }
  function receive(state) {
    if (!state || typeof state !== "object" || Array.isArray(state)) return;
    voice = state;
    if (!roomVisible() || voice.eligible !== true) {
      resetDraft(); localError = "";
      if (refs) { refs.caption.replaceChildren(); refs.partial.textContent = ""; }
    } else if (!draftDirty) localDraft = string(voice.draft, 4096);
    paint();
  }
  window.TIAVoice = Object.freeze({mount, update, receive});
})();
