import AppKit
import WebKit

// Runs the actual bundled renderer, bridge and S02-backed Python process.
// All text and data are synthetic. No credentials and no network activation.
final class TIAUISmoke {
    private weak var app: TIAApp?
    private let directory: URL
    private let finish: (Int32) -> Void
    private var next = 0
    private var done = false
    private var receipts = [[String: Any]]()
    private struct Step {
        let label: String
        let code: String
        var compact = false
    }
    private let helper = """
      const el=id=>document.getElementById(id);
      const pause=ms=>new Promise(r=>setTimeout(r,ms));
      async function until(f){for(let i=0;i<200;i++){if(f())return;await pause(30);}throw Error('UI timeout');}
      async function screen(s){await until(()=>window.tiaState?.screen===s); await until(()=>!document.querySelector('[aria-busy="true"]'));}
      async function press(id,s){if(!el(id))throw Error('Missing '+id);el(id).click();if(s)await screen(s);else await pause(150);}
      async function snap(){return await window.request('snapshot');}
    """
    private var recovering: Bool { CommandLine.arguments.contains("--ui-recovery-test") }
    private var setupTesting: Bool { CommandLine.arguments.contains("--ui-setup-test") }
    private var steps: [Step] { recovering ? [
        Step(label: "reopened native App restores saved screen and completed S02 session", code: """
          await until(()=>document.documentElement.dataset.tiaReady==='true');
          const s=await snap();return {ok:s.screen==='API_PORTAL'&&s.language==='zh'&&s.session.phase==='COMPLETE'&&s.saved_locally===true&&s.activation.state==='offline'};
        """),
        Step(label: "reopened App retains candidate SQL and immutable reviewed Trainer evidence", code: """
          const s=await snap();return {ok:s.session.events.some(e=>e.kind==='implement'&&e.payload.text==='SELECT * FROM Orders;')
          &&s.session.receipt.sha256.length===64&&s.session.review&&s.trainer_preview.evidence_ids.length===3&&s.api_requests===0};
        """)
    ] : setupTesting ? [
        Step(label: "empty/offline activation cannot enter setup through native bridge", code: """
          await until(()=>document.documentElement.dataset.tiaReady==='true');
          try {await request('setup_continue');return {ok:false};}catch(e){}
          return {ok:window.tiaState.screen==='ENTRY'&&window.tiaState.activation.state==='offline'};
        """),
        Step(label: "setup begins with actual native secure credential sheet", code: """
          await press('realInterview','API_PORTAL');return {ok:!el('prepareSetup')&&document.querySelectorAll('input[type=password]').length===0};
        """),
        Step(label: "synthetic native credential is only locally configured and unverified", code: """
          await until(()=>window.tiaState.activation.state==='activated-unverified');
          await press('prepareSetup','CONFIG');const s=await snap();
          return {ok:s.activation.authenticated===false&&s.activation.live_enabled===false&&s.activation.requests_used===0&&s.session===null};
        """),
        Step(label: "60 minutes derives four and 45 derives three Hard questions", code: """
          el('durationMinutes').value='60';el('durationMinutes').dispatchEvent(new Event('change'));
          if(el('derivedQuestionCount').textContent!=='4')return {ok:false};
          el('durationMinutes').value='45';el('durationMinutes').dispatchEvent(new Event('change'));
          if(el('derivedQuestionCount').textContent!=='3')return {ok:false};
          await press('nextSetup','QUESTION_SOURCE');const s=await snap();
          return {ok:s.setup_config.question_count===3&&s.setup_config.difficulty==='HARD'&&s.setup_config.status==='DRAFT'&&!!el('byoqQuestion2')&&!el('byoqQuestion3')};
        """),
        Step(label: "incomplete BYOQ remains editable and never fabricates validated questions", code: """
          await press('reviewQuestions');const s=await snap();
          return {ok:s.screen==='QUESTION_SOURCE'&&s.setup_questions.length===3&&s.setup_questions.every(q=>q.structure_status==='NEEDS_REVIEW')&&s.setup_allocation.launch_authorized===false};
        """),
        Step(label: "three distinct structured synthetic questions cross the real bridge", code: """
          for(let i=0;i<3;i++){
            const q={problem_statement:'Synthetic question '+i,task:'Return id for task '+i,schema:'Items(id INT)',example_input:'[{"id":1}]',expected_output:'[{"id":1}]',environment:'POSTGRESQL',source:'OWNER'};
            const box=el('byoqQuestion'+i);box.value=JSON.stringify(q);box.dispatchEvent(new Event('input',{bubbles:true}));
          }
          await press('reviewQuestions','MECHANISM');const s=await snap();
          return {ok:s.setup_questions.every(q=>q.structure_status==='STRUCTURALLY_COMPLETE'&&q.execution_status==='UNVERIFIED')&&s.setup_allocation.grading_authorized===false};
        """),
        Step(label: "supportive mechanism loads compiled source and configuration digests", code: """
          el('interviewerMechanism').value='PROFESSIONAL_SUPPORTIVE';
          await press('reviewSetup','REVIEW');const s=await snap();window.supportiveDigest=s.setup_profiles.interviewer.sha256;
          return {ok:s.setup_config.interviewer_mechanism==='PROFESSIONAL_SUPPORTIVE'&&window.supportiveDigest.length===64&&!JSON.stringify(s.setup_profiles).includes('TIA effective role instructions')};
        """),
        Step(label: "launch remains blocked on authentication and independent execution", code: """
          await press('launchPreflight');const s=await snap();
          return {ok:s.screen==='REVIEW'&&s.session===null&&s.setup_blockers.includes('PROVIDER_AUTHENTICATION_REQUIRED')&&s.setup_allocation.launch_authorized===false&&s.activation.requests_used===0};
        """),
        Step(label: "strict mechanism changes effective instructions without expanding authority", code: """
          await press('setupBack','MECHANISM');el('interviewerMechanism').value='STRICT_CHALLENGING';
          await press('reviewSetup','REVIEW');const s=await snap();
          return {ok:s.setup_profiles.interviewer.sha256!==window.supportiveDigest&&s.setup_profiles.interviewer.forbidden_authorities.includes('scoring')};
        """),
        Step(label: "disconnect clears credential and native gate reblocks draft commands", code: """
          await request('disconnect');
          try {await request('setup_launch');return {ok:false};}catch(e){}
          const s=await snap();
          return {ok:s.activation.state==='offline'&&s.activation.authenticated===false&&s.activation.requests_used===0&&!JSON.stringify(s).includes('synthetic-ui-fixture')};
        """)
    ] : [
        Step(label: "entry offers exactly two experience choices and zero API requests", code: """
          await until(()=>document.documentElement.dataset.tiaReady==='true');
          const s=await snap();return {ok:s.screen==='ENTRY'&&!!el('startTutorial')&&!!el('realInterview')&&s.activation.requests_used===0};
        """),
        Step(label: "keyboard focus reaches tutorial and real Next reaches rules", code: """
          document.querySelector('.skip-link').click();await pause(50);
          el('startTutorial').focus();if(document.activeElement!==el('startTutorial'))return {ok:false};
          await press('startTutorial','WELCOME');await press('next','RULES');
          const s=await snap();return {ok:s.tutorial_step===2};
        """),
        Step(label: "rules acknowledged before fixed Medium PostgreSQL question", code: """
          await press('next','QUESTION');const s=await snap();
          return {ok:s.question.difficulty==='MEDIUM'&&s.question.environment==='POSTGRESQL'&&s.tutorial_step===3};
        """),
        Step(label: "interactive room starts original S02 controller", code: """
          await press('next','ROOM');const s=await snap();
          return {ok:s.session.phase==='INTERVIEWING'&&s.execution_status==='NOT_RUN'&&s.tutorial_step===4};
        """),
        Step(label: "clarification crosses WebKit native Python and stays literal", code: """
          el('responseKind').value='clarify';el('response').value='Synthetic clarification: exclude NULL dates? <script>window.injection=true</script>';
          await press('submitResponse');await until(()=>window.tiaState.session.events.some(e=>e.actor==='candidate'));
          const s=await snap();return {ok:s.session.events.some(e=>e.actor==='candidate'&&e.kind==='clarify'&&e.payload.text.includes('<script>'))&&!window.injection};
        """),
        Step(label: "plan and SQL are separate unexecuted candidate evidence", code: """
          el('responseKind').value='plan';el('response').value='Synthetic plan: explain one row per customer and test ties.';
          await press('submitResponse');
          el('responseKind').value='implement';el('response').value='SELECT * FROM Orders;';
          await press('submitResponse');const s=await snap();
          return {ok:s.session.events.some(e=>e.kind==='plan')&&s.session.events.some(e=>e.kind==='implement'&&e.payload.execution==='NOT_EXECUTED')&&s.api_requests===0};
        """),
        Step(label: "compact interview room has no horizontal clipping", code: """
          await pause(300);return {ok:document.documentElement.scrollWidth<=innerWidth+1&&el('response').getBoundingClientRect().width<innerWidth};
        """, compact: true),
        Step(label: "completion freezes receipt and authorizes separate Trainer", code: """
          await press('finishTutorial','COMPLETE');const s=await snap();window.frozenDigest=s.session.receipt.sha256;
          return {ok:s.session.phase==='COMPLETE'&&s.session.receipt.assessment.technical.status==='NOT_SCORED'
            &&s.session.receipt.assessment.communication.status==='NOT_SCORED'&&s.session.review
            &&s.session.events.some(e=>e.actor==='trainer')&&s.trainer_preview.provenance==='SIMULATED'};
        """),
        Step(label: "language preference is host-owned and receipt immutable", code: """
          await request('language',{language:'zh'});const s=await snap();
          return {ok:s.language==='zh'&&document.documentElement.lang.startsWith('zh')&&s.session.receipt.sha256===window.frozenDigest};
        """),
        Step(label: "prepare real keyboard focus at Replay", code: """
          el('replayTutorial').focus();return {ok:document.activeElement===el('replayTutorial')};
        """),
        Step(label: "native Tab reaches Real AI choice", code: """
          await until(()=>document.activeElement===el('realInterview'));return {ok:true};
        """),
        Step(label: "real AI immediately enters native API Portal ahead of config", code: """
          await screen('API_PORTAL');const s=window.tiaState;
          return {ok:s.screen==='API_PORTAL'&&s.activation.authenticated===false&&s.activation.requests_used===0&&document.querySelectorAll('input[type=password]').length===0};
        """),
        Step(label: "cancelled native credential entry cannot activate real AI", code: """
          await pause(150);const s=await snap();
          return {ok:s.activation.state==='offline'&&s.activation.authenticated===false&&s.activation.requests_used===0&&s.session.receipt.sha256===window.frozenDigest};
        """),
        Step(label: "native human decision stays pending beyond twenty seconds without false timeout", code: """
          el('openPortal').click();await pause(21000);
          return {ok:el('error').hidden&&document.querySelector('[aria-busy="true"]')!==null&&window.tiaState.activation.requests_used===0};
        """),
        Step(label: "delayed native cancel resolves the original request and keeps zero usage", code: """
          await until(()=>!document.querySelector('[aria-busy="true"]'));
          const s=await snap();return {ok:s.activation.state==='offline'&&s.activation.requests_used===0&&el('error').hidden};
        """),
        Step(label: "local resource isolation and no renderer network privileges", code: """
          const c=document.querySelector('meta[http-equiv="Content-Security-Policy"]').content;
          return {ok:c.includes("connect-src 'none'")&&Array.from(document.scripts).every(x=>x.src.startsWith('file:'))};
        """)
    ] }
    init(app: TIAApp, directory: URL, finish: @escaping (Int32) -> Void) {
        self.app = app; self.directory = directory; self.finish = finish
    }
    func run() {
        do { try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true) }
        catch { end(false, "Cannot create synthetic test directory"); return }
        DispatchQueue.main.asyncAfter(deadline: .now() + 90) { [weak self] in self?.end(false, "UI watchdog timeout") }
        step()
    }
    private func step() {
        guard !done, let app = app else { return }
        guard next < steps.count else { end(true, "\(steps.count) real UI checks; zero API requests"); return }
        let step = steps[next]
        if step.compact { app.window.setContentSize(NSSize(width: 720, height: 600)) }
        app.webView.callAsyncJavaScript(helper + "\n" + step.code, arguments: [:], in: nil, in: .page) { [weak self] result in
            guard let self = self, !self.done else { return }
            guard case .success(let value) = result, let object = value as? [String: Any], object["ok"] as? Bool == true else {
                print("UI check detail: \(result)")
                self.end(false, step.label); return
            }
            if step.label == "real AI immediately enters native API Portal ahead of config" ||
                step.label == "native human decision stays pending beyond twenty seconds without false timeout" {
                guard app.portalIsVisible else { self.end(false, "Native API sheet not visible"); return }
                app.cancelPortalForTest()
            }
            if step.label == "setup begins with actual native secure credential sheet" {
                guard app.enterSyntheticCredentialForTest() else { self.end(false, "Synthetic native input failed"); return }
            }
            self.receipts.append(["test": step.label, "status": "PASSED"])
            print("PASS \(step.label)")
            if step.label == "prepare real keyboard focus at Replay" { self.key("\t", code: 48) }
            if step.label == "native Tab reaches Real AI choice" { self.key("\r", code: 36) }
            let number = self.next
            self.next += 1
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.15) {
                app.webView.takeSnapshot(with: nil) { image, error in
                    guard error == nil, let tiff = image?.tiffRepresentation,
                          let bitmap = NSBitmapImageRep(data: tiff), let png = bitmap.representation(using: .png, properties: [:])
                    else { self.end(false, "Snapshot failed"); return }
                    do { try png.write(to: self.directory.appendingPathComponent((self.recovering ? "recovery-" : self.setupTesting ? "setup-" : "") + String(format: "%02d.png", number))) }
                    catch { self.end(false, "Snapshot write failed"); return }
                    self.step()
                }
            }
        }
    }
    private func key(_ characters: String, code: UInt16) {
        guard let app = app else { return }
        for type in [NSEvent.EventType.keyDown, .keyUp] {
            if let event = NSEvent.keyEvent(with: type, location: .zero, modifierFlags: [],
                timestamp: ProcessInfo.processInfo.systemUptime, windowNumber: app.window.windowNumber,
                context: nil, characters: characters, charactersIgnoringModifiers: characters,
                isARepeat: false, keyCode: code) { app.window.sendEvent(event) }
        }
    }
    private func end(_ success: Bool, _ message: String) {
        guard !done else { return }; done = true
        let receipt: [String: Any] = ["schema": "tia-native-ui-test/v1", "passed": receipts.count,
            "failed": success ? 0 : 1, "tests": receipts, "summary": message,
            "api_requests": 0, "real_credentials_used": false, "synthetic_credential_fixture_used": setupTesting, "human_uat": "NOT_RUN"]
        if let data = try? JSONSerialization.data(withJSONObject: receipt, options: [.prettyPrinted, .sortedKeys]) {
            try? data.write(to: directory.appendingPathComponent(recovering ? "ui-recovery-receipt.json" : setupTesting ? "ui-setup-receipt.json" : "ui-test-receipt.json"))
        }
        print("Native UI smoke: \(success ? "PASS" : "FAIL") — \(message)")
        finish(success ? 0 : 1)
    }
}
