"use strict";

// This entry point is loaded only by the standalone audio lab. No fetch, Web
// Speech, provider credentials, interview worker or browser persistence exists.
(() => {
  const $ = id => document.getElementById(id);
  const pending = new Map();
  const encoder = new TextEncoder();
  let sequence = 0, state = null, busy = false, manualRevision = 0;
  let eventSignature = "", turnSignature = "";
  const feedbackNodes = new Map();
  const cases = [
    ["permissions", "Permissions & startup", "Begin on this Mac. If macOS asks, allow Microphone and Speech Recognition. After both dialogs, automatic send stays on. The native timeline identifies permission or capability failures. Existing grants may mean no dialog appears."],
    ["input_frames", "Microphone signal", "Say a short sentence. Check for input-frame telemetry and candidate speech activity in the timeline. An active engine without frames or speech is a failure to record here. Test the microphone and output device you actually use."],
    ["transcription", "Words arrive", "Say: ‘I will explain my plan before writing code.’ The companion should show a partial transcript, then the completed words. Record missing, garbled or stale text."],
    ["silence_seal", "Five seconds, one delivery", "Speak one sentence, then remain silent. No send should occur before five uninterrupted seconds. After five seconds there should be exactly one candidate message and one scripted reply. Silence alone must not create a message."],
    ["silence_reset", "Resumed speech resets silence", "Speak, pause for roughly three seconds, and continue speaking. The two parts stay in one turn. The five-second wait starts again from the resumed speech, including when the recognizer finalizes a segment early."],
    ["barge_in", "Interrupt interviewer audio", "While the scripted reply is speaking, say ‘Skip the introduction and read the question.’ Playback should stop promptly, and your words should appear and send after silence. This must not skip a question or change an interview."],
    ["echo_rejection", "Speaker echo is not candidate speech", "Use the Mac speakers at your usual volume and remain silent through a reply. Its own audio must not become candidate text or trigger another turn. Repeat with headphones if available; record the device and volume qualitatively."],
    ["manual_edit", "Editable candidate input", "While listening, click Edit draft in the companion and type a correction. Capture pauses and the text becomes editable. Send manually, then use Listen to resume. Also try the separate Candidate text input box on this page."],
    ["pause_resume", "Pause and resume capture", "Pause the mic halfway through a sentence. Speak while paused; those words must not appear or send. The existing draft remains editable. Clear or send it, then Listen again."],
    ["mute_replay", "Mute and replay", "Mute interviewer voice, send a message and confirm that a reply caption appears without sound. Unmute and Replay the reply. Muting playback should not silently disable candidate input."],
    ["language_speed", "Language and speaking speed", "Pause capture, open Voice settings and switch speed between Slower, Normal and Faster. Faster is the default. Test an installed English or Chinese recognition language; unavailable local assets must produce a clear recovery state, never cloud audio."],
    ["drag_collapse", "Drag and collapse", "Move the companion using its grip, then collapse and reopen it. The transcript, automatic-send setting and mic controls stay consistent. Keyboard: focus the grip, use arrows, Shift+arrow or Home."],
    ["focus_recovery", "App interruption", "Switch to another app while listening or speaking. Audio should stop safely. Return and use Listen explicitly to resume. Permission sheets during initial startup must not turn automatic send off."],
    ["recognition_recovery", "Failure and text fallback", "If the recognizer or microphone fails, record the native error and recovery hint. Confirm text remains editable. Use Retry local speech after fixing the device, permission or installed language. Do not deny existing production permissions just to force this case."],
    ["stop_isolation", "Stop and isolation", "Press Stop audio. No more capture, words, replies or stale sends may arrive. Export the report. Existing interview sessions and their state remain untouched. Begin again only if you want another isolated run."],
  ];
  const make = (tag, text = "", className = "") => {
    const node = document.createElement(tag); node.textContent = text;
    if (className) node.className = className;
    return node;
  };
  function showError(error) {
    const code = typeof error === "string" ? error : error?.code || error?.message || "AUDIO_UAT_ACTION_FAILED";
    $("audioError").textContent = String(code).slice(0, 240); $("audioError").hidden = false;
  }
  function command(action, payload = {}) {
    return new Promise((resolve, reject) => {
      if (!window.webkit?.messageHandlers?.audioUAT) { reject(new Error("AUDIO_UAT_NATIVE_HOST_REQUIRED")); return; }
      const id = `audio-uat-${++sequence}`;
      const timer = window.setTimeout(() => { pending.delete(id); reject(new Error("AUDIO_UAT_BRIDGE_TIMEOUT")); }, 15000);
      pending.set(id, {resolve, reject, timer});
      window.webkit.messageHandlers.audioUAT.postMessage({id, action, payload});
    });
  }
  function receive(reply) {
    if (!reply || typeof reply.id !== "string") return;
    const operation = pending.get(reply.id); if (!operation) return;
    clearTimeout(operation.timer); pending.delete(reply.id);
    if (reply.ok === true) operation.resolve(reply);
    else operation.reject(new Error(typeof reply.error === "string" ? reply.error : "AUDIO_UAT_ACTION_FAILED"));
  }
  async function perform(action, payload = {}) {
    if (busy) return;
    busy = true; $("audioError").hidden = true; paintControls();
    try { return await command(action, payload); }
    catch (error) { showError(error); }
    finally { busy = false; paintControls(); }
  }
  function paintControls() {
    const running = state?.running === true;
    $("audioBegin").disabled = !state || busy || running;
    $("audioStop").disabled = !running;
    $("audioExport").disabled = !state || busy;
    const length = encoder.encode($("audioManualDraft").value).length;
    $("audioManualBytes").textContent = `${length} / 4096 UTF-8 bytes`;
    $("audioManualSend").disabled = !running || busy || state?.voice?.submitting === true || !$("audioManualDraft").value.trim() || length > 4096;
  }
  function renderSignals() {
    const voice = state.voice || {};
    const rows = [
      ["Native state", voice.status || "OFF"],
      ["Input enabled", voice.candidate_input_enabled === true ? "YES" : "NO"],
      ["Capture active", voice.listening === true ? "YES" : "NO"],
      ["Input operational", voice.candidate_input_operational === true ? "YES" : "NO / NOT YET OBSERVED"],
      ["Automatic send", voice.handsfree === true ? "ON" : "OFF"],
      ["Interviewer playback", voice.speaking === true ? "SPEAKING" : voice.muted === true ? "MUTED" : "IDLE"],
      ["Recognition language", voice.language || "en-US"],
      ["Speaking speed", String(voice.rate ?? 1.2)],
      ["Failure stage", voice.failure_stage || "NONE"],
      ["Native error", voice.error || "NONE"],
    ];
    $("audioSignals").replaceChildren(...rows.flatMap(([label, value]) => [make("dt", label), make("dd", String(value))]));
    $("audioRecovery").hidden = !voice.error;
    $("audioRecovery").textContent = voice.error ? `Recovery: ${voice.recovery_action || "PAUSE_EDIT_OR_RETRY_LISTENING"}. Use the editable text input if speech is unavailable; check the timeline before retrying.` : "";
  }
  function renderEvents() {
    const events = Array.isArray(state.events) ? state.events : [];
    const last = events[events.length - 1];
    const signature = `${events.length}:${last?.sequence}:${last?.event}`;
    if (signature === eventSignature) return;
    eventSignature = signature;
    $("audioEventCount").textContent = `${events.length} retained events · latest 150 shown`;
    const nodes = events.slice(-150).reverse().map(event => {
      const item = make("li"); const heading = make("div", "", "event-head");
      const elapsed = Number.isFinite(event.elapsed_seconds) ? `${event.elapsed_seconds.toFixed(3)}s` : "—";
      heading.append(make("time", `#${event.sequence ?? "?"} · ${elapsed}`), make("strong", String(event.event || "UNKNOWN")));
      item.append(heading);
      if (event.details && typeof event.details === "object") item.append(make("code", JSON.stringify(event.details).slice(0, 3000)));
      return item;
    });
    $("audioTimeline").replaceChildren(...(nodes.length ? nodes : [make("li", "No native events yet.", "empty")]));
  }
  function renderTurns() {
    const turns = Array.isArray(state.turns) ? state.turns : [];
    const signature = JSON.stringify(turns);
    if (signature === turnSignature) return;
    turnSignature = signature;
    const nodes = turns.map(turn => {
      const isCandidate = turn.role === "candidate" || turn.role === "user";
      const node = make("li", "", isCandidate ? "candidate" : "interviewer");
      node.append(make("span", isCandidate ? `Candidate · ${turn.kind || "speech"}` : "Scripted local interviewer", "speaker"), make("span", String(turn.text || ""), "utterance"));
      return node;
    });
    $("audioTurns").replaceChildren(...(nodes.length ? nodes : [make("li", "Begin the test to hear the opening.", "empty")]));
    $("audioTurns").scrollTop = $("audioTurns").scrollHeight;
  }
  function createChecklist() {
    cases.forEach(([id, title, instruction], index) => {
      const item = make("details", "", "case"); item.id = `audioCase-${id}`;
      const summary = make("summary", `${index + 1}. ${title}`), badge = make("span", "Not run", "result"); badge.dataset.result = "NOT_RUN"; summary.append(badge);
      const selectLabel = make("label", "Result"); selectLabel.htmlFor = `audioResult-${id}`;
      const select = make("select"); select.id = selectLabel.htmlFor;
      for (const [value, label] of [["NOT_RUN", "Not run"], ["PASS", "Pass · observed"], ["FAIL", "Fail · observed"], ["BLOCKED", "Blocked / unavailable"]]) {
        const option = make("option", label); option.value = value; select.append(option);
      }
      const noteLabel = make("label", "What happened / feedback"); noteLabel.htmlFor = `audioNote-${id}`;
      const note = make("textarea"); note.id = noteLabel.htmlFor; note.rows = 2; note.maxLength = 1000; note.placeholder = "Expected vs observed; stage or error code; no personal information.";
      const save = make("button", "Save result"), saved = make("span", "", "saved"); save.type = "button";
      let dirty = false;
      for (const input of [select, note]) input.addEventListener("input", () => { dirty = true; saved.textContent = "Unsaved"; });
      save.addEventListener("click", async () => {
        save.disabled = true; saved.textContent = "Saving…";
        try {
          await command("feedback", {case_id: id, result: select.value, note: note.value});
          dirty = false; saved.textContent = "Saved locally"; badge.textContent = select.options[select.selectedIndex].textContent; badge.dataset.result = select.value;
        } catch (error) { showError(error); saved.textContent = "Not saved"; }
        finally { save.disabled = false; }
      });
      feedbackNodes.set(id, {select, note, badge, saved, isDirty: () => dirty});
      item.append(summary, make("p", instruction), selectLabel, select, noteLabel, note, save, saved); $("audioFeedback").append(item);
    });
  }
  function update(next) {
    if (!next || typeof next !== "object" || Array.isArray(next)) return;
    state = next;
    const synthetic = next.mode === "SYNTHETIC";
    $("audioMode").textContent = synthetic ? "Synthetic audio · no microphone capture" : "Real local audio · scripted replies";
    $("audioRunStatus").textContent = next.running ? synthetic ? "Synthetic test active. This does not certify microphone, recognition or speakers." : "Audio test active. Expand the companion to inspect transcription and controls." : "Audio stopped. Begin starts a separate test; no interview state is loaded.";
    $("audioReportPath").hidden = !next.report_path;
    $("audioReportPath").textContent = next.report_path ? `Diagnostic report: ${next.report_path}` : "";
    window.TIAVoice.update({screen: "AUDIO_UAT", language: "en", audio_uat: {active: next.running === true, can_send: next.voice?.eligible === true && next.voice?.submitting !== true, pending: next.voice?.submitting === true, turns: (next.turns || []).filter(turn => turn.role === "candidate" || turn.role === "user").length, session_id: next.session_id || "local-audio-uat"}});
    window.TIAVoice.receive(next.voice || {});
    renderSignals(); renderEvents(); renderTurns(); paintControls();
    for (const record of Array.isArray(next.feedback) ? next.feedback : []) {
      const refs = feedbackNodes.get(record.case_id);
      if (!refs || refs.isDirty()) continue;
      refs.select.value = record.result; refs.note.value = record.note || "";
      refs.badge.textContent = record.result; refs.badge.dataset.result = record.result;
    }
    if (next.error) showError(next.error);
  }
  createChecklist();
  window.TIAVoice.mount({send: command, localAudioUAT: true});
  $("audioBegin").addEventListener("click", () => perform("begin"));
  $("audioStop").addEventListener("click", () => { command("stop").catch(showError); });
  $("audioExport").addEventListener("click", () => perform("export_report"));
  $("audioManualDraft").addEventListener("focus", () => {
    if (state?.running && (state.voice?.listening || state.voice?.listening_requested)) command("voice_pause").catch(showError);
  });
  $("audioManualDraft").addEventListener("input", () => { manualRevision += 1; paintControls(); });
  $("audioManualSend").addEventListener("click", async () => {
    if ($("audioManualSend").disabled) return;
    const draft = $("audioManualDraft").value, revision = manualRevision;
    busy = true; $("audioError").hidden = true; paintControls();
    try {
      await command("voice_pause"); await command("voice_draft", {text: draft}); await command("voice_send");
      if (manualRevision === revision) $("audioManualDraft").value = "";
    } catch (error) { showError(error); }
    finally { busy = false; paintControls(); }
  });
  window.TIAAudioUAT = Object.freeze({receive, update, command, get snapshot() { return state; }});
})();
