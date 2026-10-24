import AppKit
import WebKit

// Exercises the bundled renderer, native voice companion and actual Python
// controller. Speech input and HTTP are synthetic and fail closed. This suite
// never requests microphone/Speech permissions or contacts a provider.
final class TIAVoiceUISmoke {
    private weak var app: TIAApp?
    private let directory: URL
    private let voiceState: () -> [String: Any]
    private let injectTranscript: (String, Bool) -> Void
    private let finish: (Int32) -> Void
    private var next = 0
    private var done = false
    private var receipts = [[String: Any]]()

    private enum NativeAction {
        case none, credential, cancelPortal, transcript(String, Bool), key(String, UInt16), drag
    }
    private struct Step {
        let label: String
        let code: String
        var action: NativeAction = .none
        var compact = false
    }
    private let helper = """
      const el=id=>document.getElementById(id);
      const pause=ms=>new Promise(r=>setTimeout(r,ms));
      async function until(f){for(let i=0;i<250;i++){if(f())return;await pause(30);}throw Error('Voice UI timeout');}
      async function screen(s){await until(()=>window.tiaState?.screen===s);await until(()=>!document.querySelector('[aria-busy="true"]'));}
      async function press(id,s){if(!el(id))throw Error('Missing '+id);el(id).click();if(s)await screen(s);else await pause(200);}
      async function snap(){return await window.request('snapshot');}
      function input(id,value){const n=el(id);if(!n)throw Error('Missing '+id);n.value=value;n.dispatchEvent(new Event('input',{bubbles:true}));}
      async function choose(id,value){const n=el(id);if(!n)throw Error('Missing '+id);n.value=value;n.dispatchEvent(new Event('change',{bubbles:true}));await pause(200);}
      function visible(n){return !!n&&!n.hidden&&n.getClientRects().length>0;}
      async function panel(){if(!visible(el('voicePanel')))await press('voiceToggle');await until(()=>visible(el('voicePanel')));}
    """

    private var steps: [Step] { [
        Step(label: "Voice is unavailable before provider verification", code: """
          await until(()=>document.documentElement.dataset.tiaReady==='true');
          const c=el('voiceCompanion');
          return {ok:!visible(c)&&window.tiaState.activation.requests_used===0};
        """),
        Step(label: "Native synthetic consent is isolated from the renderer", code: """
          await press('realInterview','API_PORTAL');
          return {ok:window.tiaState.activation.requests_used===0
            &&document.querySelectorAll('input[type=password]').length===0&&!visible(el('voiceCompanion'))};
        """, action: .credential),
        Step(label: "Three reviewed questions enter a real multi-turn controller session", code: """
          await until(()=>window.tiaState.activation.state==='activated-unverified');
          await press('prepareSetup','CONFIG');
          await request('setup_config',{config:{technical_environment:'POSTGRESQL',duration_minutes:45,
            difficulty:'HARD',question_source:'BYOQ',interviewer_mechanism:'STRICT_CHALLENGING'}});
          for(let i=0;i<3;i++){
            const fields={problem_statement:'Synthetic voice exercise '+i,task:'Return one total per customer for exercise '+i,
              schema:'VoiceItems'+i+'(id INT, customer_id INT)',example_input:'(1,2)',expected_output:'(2,1)',
              environment:'POSTGRESQL',source:'OWNER',constraints:'One row per customer',source_reference:''};
            const r=await request('setup_question_set',{index:i,source:'OWNER',raw_text:JSON.stringify(fields)});
            const q=r.setup_questions[i];
            await request('setup_question_confirm',{index:i,fields:q.fields,raw_sha256:q.raw_sha256});
          }
          await press('startRehearsal','API_PORTAL');const s=await snap();
          return {ok:s.rehearsal.status==='ACTIVE'&&s.rehearsal.current_index===0
            &&s.activation.requests_used===0&&!visible(el('voiceCompanion'))};
        """),
        Step(label: "Verified committed interviewer response makes the voice companion available", code: """
          await press('verifyPreview','LIVE_PREVIEW');await until(()=>visible(el('voiceCompanion')));
          if(el('voiceCompanion').getBoundingClientRect().width>220||visible(el('voicePanel')))return {ok:false};
          await panel();
          const s=await snap(),p=s.live_preview;
          return {ok:s.activation.state==='live-verified'&&s.transport_mode==='MOCK_HTTP'
            &&s.activation.requests_used===1&&p.candidate_turn_limit===4
            &&p.execution_status==='NOT_RUN'&&p.technical==='NOT_SCORED'&&p.communication==='NOT_SCORED'
            &&el('voiceHandsfree')?.checked===true&&s.voice.listening===true&&el('voiceCaption')?.textContent.trim().length>0};
        """),
        Step(label: "Chinese interface and local voice settings require no new model request", code: """
          // Select manual mode explicitly to retain the existing draft/edit journey.
          await press('voiceMic');
          await request('language',{language:'zh'});await panel();
          el('voiceLanguage').closest('details').open=true;
          await choose('voiceLanguage','zh-CN');await choose('voiceRate','0.8');
          const s=await snap();const ok=el('voiceMic').textContent.includes('听取')
            &&s.voice.language==='zh-CN'&&s.voice.rate===0.8&&s.activation.requests_used===1;
          await choose('voiceLanguage','en-US');await choose('voiceRate','1');
          await request('language',{language:'en'});el('voiceLanguage').closest('details').open=false;
          input('previewResponse','SELECT customer_id, COUNT(*) FROM VoiceItems0 GROUP BY customer_id;');
          return {ok};
        """),
        Step(label: "Explicit listen begins mock recognition without a provider request", code: """
          await press('voiceMic');return {ok:window.tiaState.activation.requests_used===1};
        """, action: .transcript("Synthetic unfinished clarification", false)),
        Step(label: "Partial recognition remains an unsubmitted caption", code: """
          await until(()=>el('voicePartial')?.textContent.includes('Synthetic unfinished clarification'));
          const s=await snap();return {ok:s.activation.requests_used===1&&s.live_preview.candidate_turns_used===0
            &&!s.live_preview.session.events.some(e=>e.actor==='candidate')&&el('voiceHandsfree').checked===false
            &&el('previewResponse').value==='SELECT customer_id, COUNT(*) FROM VoiceItems0 GROUP BY customer_id;'};
        """, action: .transcript("Synthetic clarification from local speech", true)),
        Step(label: "Manual-mode final recognition is editable and never silently submitted", code: """
          await until(()=>el('voiceDraft')?.value==='Synthetic clarification from local speech');await pause(450);
          const s=await snap();return {ok:s.activation.requests_used===1&&s.live_preview.candidate_turns_used===0
            &&!el('voiceDraft').readOnly&&!s.live_preview.session.events.some(e=>e.actor==='candidate')};
        """),
        Step(label: "Edited voice draft crosses the same guarded candidate and model path", code: """
          await choose('voiceKind','clarify');input('voiceDraft','Edited clarification: should each customer appear exactly once?');
          await press('voiceSend');await until(()=>window.tiaState.live_preview.candidate_turns_used===1
            &&window.tiaState.activation.requests_used===2&&!document.querySelector('[aria-busy="true"]'));
          const s=await snap(),events=s.live_preview.session.events,c=events.filter(e=>e.actor==='candidate');
          return {ok:c.length===1&&c[0].kind==='clarify'
            &&c[0].payload.text==='Edited clarification: should each customer appear exactly once?'
            &&events.filter(e=>e.actor==='interviewer'&&e.provenance==='LIVE_MODEL').length===2
            &&s.live_preview.execution_status==='NOT_RUN'&&s.live_preview.technical==='NOT_SCORED'
            &&!JSON.stringify(s).includes('Synthetic unfinished clarification')
            &&el('previewResponse').value==='SELECT customer_id, COUNT(*) FROM VoiceItems0 GROUP BY customer_id;'};
        """),
        Step(label: "Pause stops recognition before a delayed final transcript", code: """
          await panel();await press('voiceMic');await press('voiceMic');
          return {ok:window.tiaState.activation.requests_used===2};
        """, action: .transcript("STALE PAUSED TRANSCRIPT MUST NOT SEND", true)),
        Step(label: "Late speech after pause cannot mutate the draft or committed dialogue", code: """
          await pause(250);const s=await snap();
          return {ok:s.activation.requests_used===2&&s.live_preview.candidate_turns_used===1
            &&!el('voiceDraft').value.includes('STALE PAUSED')&&!JSON.stringify(s).includes('STALE PAUSED')};
        """),
        Step(label: "Mute affects local speech playback without inventing a conversation turn", code: """
          await press('voiceMute');return {ok:window.tiaState.activation.requests_used===2};
        """),
        Step(label: "A second manual speech turn remains available while output is muted", code: """
          await choose('voiceKind','plan');await press('voiceMic');return {ok:window.tiaState.live_preview.can_send===true};
        """, action: .transcript("I will group by customer and check the row grain before implementation.", true)),
        Step(label: "Second spoken plan is committed with independent unscored evidence", code: """
          await until(()=>el('voiceDraft')?.value.includes('check the row grain'));
          await press('voiceSend');await until(()=>window.tiaState.live_preview.candidate_turns_used===2
            &&window.tiaState.activation.requests_used===3&&!document.querySelector('[aria-busy="true"]'));
          const s=await snap(),c=s.live_preview.session.events.filter(e=>e.actor==='candidate');
          return {ok:c.length===2&&c[1].kind==='plan'&&c[1].payload.text.includes('check the row grain')
            &&s.live_preview.communication==='NOT_SCORED'&&s.live_preview.technical==='NOT_SCORED'
            &&s.live_preview.execution_status==='NOT_RUN'};
        """),
        Step(label: "Companion remains usable at compact window size", code: """
          await pause(250);await panel();const c=el('voiceCompanion'),r=c.getBoundingClientRect();
          const focusables=[...c.querySelectorAll('button,textarea,select,input')].filter(n=>!n.disabled&&visible(n));
          el('voiceDragHandle').focus();window.voiceKeyboardBefore=r.toJSON();
          return {ok:document.documentElement.scrollWidth<=innerWidth+1&&r.left>=-1&&r.right<=innerWidth+1
            &&r.top>=-1&&r.bottom<=innerHeight+1&&focusables.length>=6
            &&document.activeElement===el('voiceDragHandle'),before:{left:r.left,top:r.top}};
        """, action: .key("\u{F702}", 123), compact: true),
        Step(label: "Native keyboard movement and focus work without scrolling the dialogue", code: """
          const r=el('voiceCompanion').getBoundingClientRect();
          return {ok:document.activeElement===el('voiceDragHandle')&&r.left>=-1&&r.right<=innerWidth+1
            &&r.left<window.voiceKeyboardBefore.left-1};
        """, action: .key("\t", 48)),
        Step(label: "Native Tab reaches a companion control and native mouse drag is armed", code: """
          const c=el('voiceCompanion'),h=el('voiceDragHandle'),r=h.getBoundingClientRect();
          window.voiceDragBefore=c.getBoundingClientRect().toJSON();
          window.voicePointerSeen=[];for(const type of ['pointerdown','pointermove','pointerup'])h.addEventListener(type,e=>window.voicePointerSeen.push({type,x:e.clientX,y:e.clientY}),{once:true});
          return {ok:c.contains(document.activeElement)&&document.activeElement!==h,
            drag:{x:r.left+r.width/2,y:r.top+r.height/2}};
        """, action: .drag),
        Step(label: "Native mouse drag keeps the companion inside the compact window", code: """
          await pause(200);const r=el('voiceCompanion').getBoundingClientRect(),before=window.voiceDragBefore;
          return {ok:r.left>=-1&&r.right<=innerWidth+1&&r.top>=-1&&r.bottom<=innerHeight+1
            &&(Math.abs(r.left-before.left)>1||Math.abs(r.top-before.top)>1),before,after:r.toJSON(),pointer:window.voicePointerSeen};
        """),
        Step(label: "Hands-free mode is an explicit opt-in before a third candidate turn", code: """
          await panel();await choose('voiceKind','help');
          const h=el('voiceHandsfree');if(h.checked)return {ok:false};h.click();await until(()=>h.checked&&!document.querySelector('[aria-busy="true"]'));
          await press('voiceMic');
          return {ok:window.tiaState.activation.requests_used===3};
        """, action: .transcript("I identified duplicate customer rows. Which assumption should I explain before asking for help?", true)),
        Step(label: "Opted-in final speech submits once within existing model and turn budgets", code: """
          await until(()=>window.tiaState.live_preview.candidate_turns_used===3
            &&window.tiaState.activation.requests_used===4&&!document.querySelector('[aria-busy="true"]'));
          await pause(350);const s=await snap(),p=s.live_preview,c=p.session.events.filter(e=>e.actor==='candidate');
          return {ok:c.length===3&&c[2].kind==='help'&&s.activation.requests_total===4
            &&p.technical==='NOT_SCORED'&&p.communication==='NOT_SCORED'&&p.execution_status==='NOT_RUN'
            &&s.voice.handsfree===true&&s.voice.listening===true
            &&!JSON.stringify(s).includes('synthetic-ui-fixture-not-a-real-key')};
        """),
        Step(label: "Native credential sheet stops capture and rejects a renderer request to restart it", code: """
          window.request('api_portal').catch(()=>{});
          await until(()=>el('voiceMic')?.getAttribute('aria-pressed')==='false');
          let rejected=false;try{await window.request('voice_listen');}catch(e){rejected=e.message==='VOICE_NATIVE_SHEET_ACTIVE';}
          return {ok:rejected&&window.tiaState.activation.requests_total===4};
        """, action: .cancelPortal),
        Step(label: "Cancelling the credential sheet requires explicit microphone restart", code: """
          await until(()=>!document.querySelector('[aria-busy="true"]'));const s=await snap();
          return {ok:s.voice.listening===false&&s.voice.handsfree===false&&s.voice.draft===''
            &&s.activation.requests_total===4};
        """),
        Step(label: "Leaving the question freezes dialogue and disables voice", code: """
          await press('finishRehearsalQuestion','API_PORTAL');const s=await snap();
          window.voiceFrozen=s.rehearsal.results[0].session.receipt.sha256;
          return {ok:s.rehearsal.current_index===1&&s.rehearsal.results[0].outcome==='DISCUSSION_ONLY'
            &&s.rehearsal.results[0].session.receipt.live_model_used===true
            &&!visible(el('voiceCompanion'))&&s.activation.requests_total===4};
        """, action: .transcript("STALE CLOSED QUESTION TRANSCRIPT MUST NOT SEND", true)),
        Step(label: "Disconnect clears local audio state without late speech or paid requests", code: """
          await request('disconnect');await pause(200);const s=await snap();
          return {ok:s.activation.state==='offline'&&s.activation.authenticated===false
            &&s.activation.requests_total===4&&s.rehearsal.results[0].session.receipt.sha256===window.voiceFrozen
            &&!visible(el('voiceCompanion'))&&!JSON.stringify(s).includes('STALE CLOSED QUESTION')};
        """)
    ] }

    init(app: TIAApp, directory: URL, voiceState: @escaping () -> [String: Any],
         injectTranscript: @escaping (String, Bool) -> Void, finish: @escaping (Int32) -> Void) {
        self.app = app; self.directory = directory; self.voiceState = voiceState
        self.injectTranscript = injectTranscript; self.finish = finish
    }
    func run() {
        guard CommandLine.arguments.contains("--ui-voice-test"), app?.uiTesting == true else {
            end(false, "Voice UI suite requires fail-closed native test mode"); return
        }
        do { try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true) }
        catch { end(false, "Cannot create synthetic voice test directory"); return }
        DispatchQueue.main.asyncAfter(deadline: .now() + 120) { [weak self] in self?.end(false, "Voice UI watchdog timeout") }
        step()
    }
    private func step() {
        guard !done, let app = app else { return }
        guard next < steps.count else {
            let v = voiceState()
            guard v["eligible"] as? Bool == false, v["listening"] as? Bool == false,
                  v["speaking"] as? Bool == false, v["handsfree"] as? Bool == false,
                  (v["draft"] as? String ?? "").isEmpty,
                  (v["partial"] as? String ?? "").isEmpty, TIATestHTTPProtocol.calls == 4 else {
                end(false, "Final native voice cleanup or exact mock HTTP count failed"); return
            }
            end(true, "\(receipts.count) real WebKit/native/controller checks; four mocked HTTP calls; zero real audio or provider calls")
            return
        }
        let item = steps[next]
        if item.compact { app.window.setContentSize(NSSize(width: 720, height: 600)) }
        app.webView.callAsyncJavaScript(helper + "\n" + item.code, arguments: [:], in: nil, in: .page) { [weak self] result in
            guard let self = self, !self.done else { return }
            guard case .success(let value) = result, let object = value as? [String: Any], object["ok"] as? Bool == true else {
                print("Voice UI check detail: \(result)")
                self.end(false, item.label); return
            }
            switch item.action {
            case .none: break
            case .credential:
                guard app.enterSyntheticCredentialForTest() else { self.end(false, "Synthetic native consent failed"); return }
            case .cancelPortal:
                guard let sheet = app.window.attachedSheet else { self.end(false, "Native credential sheet missing"); return }
                app.window.endSheet(sheet, returnCode: .alertSecondButtonReturn)
            case .transcript(let text, let final): self.injectTranscript(text, final)
            case .key(let characters, let code): self.key(characters, code: code)
            case .drag:
                guard let drag = object["drag"] as? [String: Double],
                      let x = drag["x"], let y = drag["y"] else { self.end(false, "Missing native drag coordinates"); return }
                self.drag(x: x, y: y)
            }
            if item.label == "Mute affects local speech playback without inventing a conversation turn" {
                guard self.voiceState()["muted"] as? Bool == true else { self.end(false, "Native mute state did not change"); return }
            }
            self.receipts.append(["test": item.label, "status": "PASSED"])
            print("PASS \(item.label)")
            self.next += 1
            let advance = { DispatchQueue.main.asyncAfter(deadline: .now() + 0.15) { self.step() } }
            let screenshot = item.label == "Verified committed interviewer response makes the voice companion available" ? "voice-room.png" :
                item.label == "Companion remains usable at compact window size" ? "voice-compact.png" : nil
            if let filename = screenshot {
                app.webView.takeSnapshot(with: nil) { image, error in
                    guard error == nil, let tiff = image?.tiffRepresentation,
                          let bitmap = NSBitmapImageRep(data: tiff), let png = bitmap.representation(using: .png, properties: [:])
                    else { self.end(false, "Synthetic voice snapshot failed"); return }
                    do { try png.write(to: self.directory.appendingPathComponent(filename)) }
                    catch { self.end(false, "Synthetic voice snapshot write failed"); return }
                    advance()
                }
            } else { advance() }
        }
    }
    private func key(_ characters: String, code: UInt16) {
        guard let app = app else { return }
        app.window.makeFirstResponder(app.webView)
        for type in [NSEvent.EventType.keyDown, .keyUp] {
            if let event = NSEvent.keyEvent(with: type, location: .zero, modifierFlags: [],
                timestamp: ProcessInfo.processInfo.systemUptime, windowNumber: app.window.windowNumber,
                context: nil, characters: characters, charactersIgnoringModifiers: characters,
                isARepeat: false, keyCode: code) { app.window.sendEvent(event) }
        }
    }
    private func drag(x: Double, y: Double) {
        guard let app = app else { return }
        let view = app.webView!
        let local = NSPoint(x: x, y: view.isFlipped ? y : view.bounds.height - y)
        let start = view.convert(local, to: nil)
        let end = NSPoint(x: start.x - 90, y: start.y + 28)
        for (index, item) in [(NSEvent.EventType.leftMouseDown, start), (.leftMouseDragged, end), (.leftMouseUp, end)].enumerated() {
            DispatchQueue.main.asyncAfter(deadline: .now() + Double(index) * 0.06) {
                if let event = NSEvent.mouseEvent(with: item.0, location: item.1, modifierFlags: [],
                    timestamp: ProcessInfo.processInfo.systemUptime, windowNumber: app.window.windowNumber,
                    context: nil, eventNumber: index + 1, clickCount: 1, pressure: 1) { app.window.sendEvent(event) }
            }
        }
    }
    private func end(_ success: Bool, _ message: String) {
        guard !done else { return }; done = true
        let receipt: [String: Any] = ["schema": "tia-native-voice-ui-test/v1", "passed": receipts.count,
            "failed": success ? 0 : 1, "tests": receipts, "summary": message,
            "api_requests": 0, "mock_http_requests": TIATestHTTPProtocol.calls, "transport": "MOCK_HTTP",
            "speech_transport": "SYNTHETIC_NATIVE_TRANSCRIPTS", "real_microphone_used": false,
            "speech_permissions_requested": false, "real_credentials_used": false,
            "synthetic_credential_fixture_used": true, "human_uat": "NOT_RUN"]
        do {
            let data = try JSONSerialization.data(withJSONObject: receipt, options: [.prettyPrinted, .sortedKeys])
            try data.write(to: directory.appendingPathComponent("ui-voice-receipt.json"))
        } catch { print("FAIL voice receipt write"); finish(1); return }
        print("Native voice UI smoke: \(success ? "PASS" : "FAIL") — \(message)")
        finish(success ? 0 : 1)
    }
}
