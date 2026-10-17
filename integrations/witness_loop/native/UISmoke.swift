import AppKit
import WebKit

// Opt-in, offline, actual WKWebView -> native -> private Core integration.
// Every run has a fresh save directory, no provider activation and unique PNGs.
final class OfflineUISmoke {
    private struct Step {
        let label: String
        let script: String
        var screenshot: String? = nil
        var width: CGFloat? = nil
    }
    private let webView: WKWebView
    private let screenshotURL: URL
    private let finish: (Int32) -> Void
    private var finished = false
    private var next = 0
    private var passed = 0
    private let helpers = """
      const el=id=>document.getElementById(id);
      const pause=ms=>new Promise(r=>setTimeout(r,ms));
      async function until(test) { for(let i=0;i<100;i++){if(test())return;await pause(40);}throw Error('DOM condition timeout'); }
      async function snap(){const r=await window.request('snapshot');if(r.activation.state!=='OFFLINE'||r.activation.requests_used!==0)throw Error('Provider boundary');return r;}
      function phase(){return el('platform-stage').dataset.phase;}
      async function clickPhase(id,expected){el(id).click();await until(()=>phase()===expected);return await snap();}
      async function inspect(id){document.querySelector('[data-inspect="'+id+'"]').click();await until(()=>el('inspectDialog').open);await until(()=>el('inspectImage').complete&&el('inspectImage').naturalWidth>0);return await snap();}
      function closeInspect(){el('closeInspect').click();}
      async function submit(text,caseAction){el('ask').value=text;el('ask').dispatchEvent(new Event('input',{bubbles:true}));el('send').click();if(caseAction){await until(()=>el('caseConfirm').open);el('confirmSend').click();}await until(()=>phase()==='NPC_LINE');return await snap();}
    """
    private let steps: [Step] = [
        Step(label: "fresh case brief precedes character and evidence", script: """
          await until(()=>el('platform-image').naturalWidth>1000);
          const r=await snap();
          return {ok:r.state.phase==='CASE_BRIEF'&&r.state.clues.length===0&&el('linwu').hidden&&!el('caseBrief').hidden&&Object.values(r.state.evidence).every(x=>!x.inspected)};
          """, screenshot: "01-case-brief.png"),
        Step(label: "profile and preferred English persist", script: """
          const r=await request('start',{player:'<b>HAL Detective</b>',style:'empathetic',language:'en'});
          return {ok:r.state.language==='en'&&r.state.phase==='CASE_BRIEF'};
          """),
        Step(label: "narrator interrupted call is separate before arrival", script: """
          const r=await request('continue');
          return {ok:r.state.phase==='NARRATOR'&&el('linwu').hidden&&el('ask').disabled&&el('captionText').textContent.includes('call')&&!el('captionText').textContent.includes('00:17')};
          """),
        Step(label: "empty platform exposes four focusable hotspots without discoveries", script: """
          const r=await clickPhase('continue','OBSERVE');
          const buttons=Array.from(document.querySelectorAll('#hotspots [data-inspect]'));
          buttons[0].focus();
          return {ok:el('linwu').hidden&&!el('hotspots').hidden&&buttons.length===4&&buttons.every(x=>!x.disabled&&x.getBoundingClientRect().width>0)&&document.activeElement===buttons[0]&&r.state.clues.length===0&&Object.values(r.state.evidence).every(x=>!x.inspected)};
          """, screenshot: "02-empty-platform.png"),
        Step(label: "clock click opens exact 00:17 close-up and only its ledger entry", script: """
          const r=await inspect('clock');
          return {ok:r.state.evidence.clock.inspected&&!r.state.evidence.clock.interpreted&&!r.state.evidence.ticket.inspected&&el('inspectImage').getAttribute('src').endsWith('clock_detail.svg')&&el('inspectText').textContent.includes('00:17')};
          """, screenshot: "03-clock-inspection.png"),
        Step(label: "red fabric hotspot opens matching observation", script: """
          closeInspect();const r=await inspect('red_fabric');
          return {ok:r.state.evidence.red_fabric.inspected&&!r.state.evidence.red_fabric.authenticated&&el('inspectImage').getAttribute('src').endsWith('red_fabric_detail.svg')};
          """, screenshot: "03b-red-fabric.png"),
        Step(label: "ticket hotspot reveals Zhou Xu without proving he never boarded", script: """
          closeInspect();const r=await inspect('ticket');
          return {ok:r.state.evidence.ticket.inspected&&el('inspectImage').getAttribute('src').endsWith('ticket_detail.svg')&&el('inspectText').textContent.includes('Zhou Xu')&&el('inspectLimit').textContent.length>10};
          """, screenshot: "03c-ticket.png"),
        Step(label: "train trace hotspot has its own bounded observation", script: """
          closeInspect();const r=await inspect('tail_light');
          return {ok:r.state.evidence.tail_light.inspected&&el('inspectImage').getAttribute('src').endsWith('train_departure_detail.svg')&&r.state.case_turns===0};
          """, screenshot: "03d-train-trace.png"),
        Step(label: "anxious Lin Wu enters unchanged station before player input", script: """
          closeInspect();const background=el('platform-image').src;
          const r=await clickPhase('approach','NPC_INTRO');await pause(800);
          const hitTargets=Array.from(document.querySelectorAll('#hotspots [data-inspect]')).every(button=>{const b=button.getBoundingClientRect();return button.contains(document.elementFromPoint(b.x+b.width/2,b.y+b.height/2));});
          return {ok:hitTargets&&!el('linwu').hidden&&el('linwu').naturalWidth>100&&el('platform-image').src===background&&el('ask').disabled&&el('captionText').textContent.includes('earlier')&&r.state.case_turns===0};
          """, screenshot: "04-linwu-arrival.png"),
        Step(label: "Continue reveals one player input turn", script: """
          const r=await clickPhase('continue','PLAYER_INPUT');
          return {ok:!el('ask').disabled&&!el('composer').hidden&&el('continue').hidden&&r.state.case_turns===0};
          """),
        Step(label: "free English conversation yields NPC caption without case or API cost", script: """
          const r=await submit('How are you feeling?',false);
          return {ok:r.state.case_turns===0&&r.state.language==='en'&&el('ask').disabled&&!el('continue').hidden&&el('captionText').textContent.includes('listening')&&r.state.transcript.some(x=>x.who==='<b>HAL Detective</b>')};
          """, screenshot: "05-npc-caption.png"),
        Step(label: "history and notebook remain accessible together with literal player text", script: """
          el('historyBtn').click();el('notebookBtn').click();
          const r=await snap();
          return {ok:!el('historyDrawer').hidden&&!el('notebookDrawer').hidden&&el('dialogue').textContent.includes('<b>HAL Detective</b>')&&!el('dialogue').querySelector('script,iframe')&&!el('dialogue').innerHTML.includes('<b>HAL Detective</b>')&&el('cards').children.length>=4&&r.state.case_turns===0};
          """, screenshot: "06-history-and-notebook.png"),
        Step(label: "responsive Mac window retains scene and avoids horizontal clipping", script: """
          await pause(300);
          return {ok:document.documentElement.scrollWidth<=innerWidth+1&&el('platform-stage').getBoundingClientRect().width<=innerWidth+1,viewport:innerWidth,documentWidth:document.documentElement.scrollWidth,stage:el('platform-stage').getBoundingClientRect().width,overflow:Array.from(document.querySelectorAll('body *')).filter(e=>{const r=e.getBoundingClientRect();return r.width&&r.right>innerWidth+1}).map(e=>({id:e.id,tag:e.tagName,right:e.getBoundingClientRect().right,width:e.getBoundingClientRect().width})).slice(0,20)};
          """, screenshot: "07-compact-window.png", width: 820),
        Step(label: "return to player turn with no hidden action cost", script: """
          await pause(200);toggleDrawer('historyDrawer',false);toggleDrawer('notebookDrawer',false);
          const r=await clickPhase('continue','PLAYER_INPUT');return {ok:r.state.case_turns===0};
          """, width: 1180),
        Step(label: "case preview requests explicit confirmation before pledge", script: """
          const r=await submit('I promise to protect you.',true);
          return {ok:r.state.promise&&r.state.case_turns===1&&r.state.phase==='NPC_LINE'};
          """),
        Step(label: "historical incoming call follows promise gate and stays distinct", script: """
          await clickPhase('continue','PLAYER_INPUT');
          const r=await submit('Who called you at 00:17?',true);
          return {ok:r.state.case_turns===2&&r.state.clues.includes('call')&&el('captionText').textContent.includes('Lin Yu')&&el('captionText').textContent.includes('separate')};
          """),
        Step(label: "authoritative evidence link and three-scene truth verdict", script: """
          await clickPhase('continue','PLAYER_INPUT');await request('advance');await request('link',{clues:['clock','call']});await request('advance');
          const r=await request('verdict');
          return {ok:r.state.ending==='truth'&&r.state.phase==='RESOLVED'&&!el('ending').hidden&&r.state.case_turns===2};
          """, screenshot: "08-truth-verdict.png"),
        Step(label: "developer path, local assets, CSP and native-only credential boundary", script: """
          const d=await request('developer');const r=await snap();
          const images=Array.from(document.images);
          return {ok:!!d.developer.readme&&d.developer.skills.length>0&&images.every(x=>x.src.startsWith('file:'))&&document.querySelectorAll('input[type=password]').length===0&&document.querySelector('meta[http-equiv="Content-Security-Policy"]').content.includes("connect-src 'none'")&&r.activation.requests_used===0};
          """
        ),
        Step(label: "partial resolution remains playable through native host", script: """
          await request('start',{player:'Partial path',style:'direct',language:'en'});
          await request('continue');await request('continue');
          await request('inspect',{id:'clock'});await request('inspect',{id:'ticket'});
          await request('approach');await request('continue');
          await submit('When did the train leave?',true);await request('continue');
          await submit('What about the station clock?',true);await request('continue');
          await request('link',{clues:['clock','call']});await request('advance');await request('advance');
          const r=await request('verdict');
          return {ok:r.state.ending==='partial'&&!r.state.promise&&r.state.case_turns===2&&!el('ending').hidden};
          """, screenshot: "09-partial-verdict.png"),
        Step(label: "false accusation remains playable without model authority", script: """
          await request('start',{player:'False path',style:'direct',language:'en'});
          await request('continue');await request('continue');
          await request('inspect',{id:'clock'});await request('inspect',{id:'ticket'});
          await request('approach');await request('continue');
          await request('advance');await request('advance');const r=await request('verdict');
          return {ok:r.state.ending==='false_accusation'&&r.state.case_turns===0&&!el('ending').hidden&&r.activation.requests_used===0};
          """, screenshot: "10-false-verdict.png"),
        Step(label: "verdict freezes discovery while known evidence remains reviewable", script: """
          const before=(await snap()).state;
          const r=await request('inspect',{id:'clock'});
          return {ok:JSON.stringify(before)===JSON.stringify(r.state)&&el('hotspot-red_fabric').disabled&&!el('hotspot-clock').disabled};
          """
        )
    ]
    init(webView: WKWebView, screenshotURL: URL, finish: @escaping (Int32) -> Void) { self.webView = webView; self.screenshotURL = screenshotURL; self.finish = finish }
    func run() {
        do { try FileManager.default.createDirectory(at: screenshotURL, withIntermediateDirectories: true) }
        catch { end(false, "Cannot create isolated screenshot directory"); return }
        DispatchQueue.main.asyncAfter(deadline: .now() + 100) { [weak self] in self?.end(false, "UI integration check timed out") }
        step()
    }
    private func step() {
        guard !finished else { return }
        guard next < steps.count else { end(true, "\(passed) checks passed; no provider requests or real credentials. Screenshots: \(screenshotURL.path)"); return }
        let current = steps[next]
        if let width = current.width { webView.window?.setContentSize(NSSize(width: width, height: width < 900 ? 700 : 820)) }
        webView.callAsyncJavaScript(helpers + "\n" + current.script, arguments: [:], in: nil, in: .page) { [weak self] response in
            guard let self = self, !self.finished else { return }
            guard case .success(let value) = response, let result = value as? [String: Any], result["ok"] as? Bool == true else {
                print("UI step details: \(response)")
                self.capture("failure-\(self.next).png") { self.end(false, current.label) }; return
            }
            self.passed += 1; print("PASS \(current.label)"); self.next += 1
            if let screenshot = current.screenshot { DispatchQueue.main.asyncAfter(deadline: .now() + 0.25) { self.capture(screenshot) { self.step() } } }
            else { self.step() }
        }
    }
    private func capture(_ name: String, completion: @escaping () -> Void) {
        webView.takeSnapshot(with: nil) { [weak self] image, error in
            guard let self = self, !self.finished else { return }
            guard error == nil, let image = image, let tiff = image.tiffRepresentation, let bitmap = NSBitmapImageRep(data: tiff), let png = bitmap.representation(using: .png, properties: [:]) else { self.end(false, "UI screenshot could not be captured"); return }
            do { let path = self.screenshotURL.appendingPathComponent(name); try png.write(to: path, options: [.withoutOverwriting]); print("Actual app screenshot: \(path.path)"); completion() }
            catch { self.end(false, "UI screenshot could not be saved") }
        }
    }
    private func end(_ success: Bool, _ message: String) {
        guard !finished else { return }; finished = true
        print("Native UI smoke: \(success ? "PASS" : "FAIL") — \(message)"); finish(success ? 0 : 1)
    }
}
