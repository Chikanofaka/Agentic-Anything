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
    private var rehearsalTesting: Bool { CommandLine.arguments.contains("--ui-rehearsal-test") }
    private var gradingTesting: Bool { CommandLine.arguments.contains("--ui-grading-test") || trainerTesting }
    private var trainerTesting: Bool { CommandLine.arguments.contains("--ui-trainer-test") }
    private var liveTesting: Bool { CommandLine.arguments.contains("--ui-live-test") }
    private var liveRecovering: Bool { CommandLine.arguments.contains("--ui-live-recovery-test") }
    private var failureTesting: Bool { CommandLine.arguments.contains("--ui-provider-failure-test") }
    private var steps: [Step] { gradingTesting ? ([
        Step(label: "E25B opens native consent for synthetic fixture-only interview", code: """
          await until(()=>document.documentElement.dataset.tiaReady==='true');
          await press('realInterview','API_PORTAL');return {ok:window.tiaState.activation.requests_used===0};
        """),
        Step(label: "E25B starts BYOQ rehearsal with 3 bound questions", code: """
          await until(()=>window.tiaState.activation.state==='activated-unverified');
          await press('prepareSetup','CONFIG');
          await request('setup_config',{config:{technical_environment:'POSTGRESQL',duration_minutes:45,
            difficulty:'HARD',question_source:'BYOQ',interviewer_mechanism:'STRICT_CHALLENGING'}});
          for(let i=0;i<3;i++){
            const fields={problem_statement:'Synthetic local fixture Q'+i,task:'Count rows by customer '+i,
              schema:'Items'+i+'(id INTEGER, customer_id INTEGER)',example_input:'(1,2)',expected_output:'(2,1)',
              environment:'POSTGRESQL',source:'OWNER',constraints:'Only test fixtures, not hidden tests',source_reference:''};
            const r=await request('setup_question_set',{index:i,source:'OWNER',raw_text:JSON.stringify(fields)});
            await request('setup_question_confirm',{index:i,fields:r.setup_questions[i].fields,raw_sha256:r.setup_questions[i].raw_sha256});
          }
          await press('startRehearsal','API_PORTAL');
          await press('verifyPreview','LIVE_PREVIEW');
          const s=await snap();return {ok:s.rehearsal.current_index===0&&s.live_preview.candidate_turn_limit===4};
        """),
        Step(label: "E25B native bridge records candidate raw SQL and rejects mismatched fixture", code: """
          el('previewKind').value='implement';
          const input=el('previewResponse');input.value='SELECT customer_id, COUNT(*) AS total FROM Items0 GROUP BY customer_id';
          input.dispatchEvent(new Event('input',{bubbles:true}));await press('sendPreview');
          await until(()=>window.tiaState?.live_preview?.candidate_turns_used===1 && !document.querySelector('[aria-busy="true"]'));
          const bad={schema:'tia-postgres-fixture/v1',fixture_id:'SYNTHETIC-UI-Q0',question_sha256:'a'.repeat(64),
            environment:'POSTGRESQL',tables:[{name:'Items0',columns:[{name:'id',type:'INTEGER'},{name:'customer_id',type:'INTEGER'}],rows:[[1,2]]}],
            expected:{columns:['customer_id','total'],rows:[[2,1]],order_sensitive:false}};
          try{await request('grade_inspect',{fixture_json:JSON.stringify(bad)});return {ok:false};}
          catch(e){if(e.message!=='FIXTURE_QUESTION_MISMATCH')return {ok:false};}
          const s=await snap();return {ok:s.live_preview.sql_accuracy===null&&!s.grading_review&&s.activation.requests_used===2};
        """),
        Step(label: "E25B WebKit fixture review displays exact current question hash", code: """
          const s=await snap(), qhash=s.live_preview.question.content_sha256;
          const f={schema:'tia-postgres-fixture/v1',fixture_id:'SYNTHETIC-UI-Q0',question_sha256:qhash,
            environment:'POSTGRESQL',tables:[{name:'Items0',columns:[{name:'id',type:'INTEGER'},{name:'customer_id',type:'INTEGER'}],rows:[[1,2]]}],
            expected:{columns:['customer_id','total'],rows:[[2,1]],order_sensitive:false}};
          const box=el('gradeFixture');if(!box)return {ok:false};
          box.value=JSON.stringify(f);box.dispatchEvent(new Event('input',{bubbles:true}));
          await press('inspectFixture');await until(()=>!!window.tiaState?.grading_review);
          const r=(await snap()).grading_review;
          return {ok:r.question_sha256===qhash&&r.status==='AWAITING_NATIVE_HUMAN_APPROVAL'&&r.fixture_id==='SYNTHETIC-UI-Q0'
            &&!!el('executeGrade')&&el('executeGrade').disabled===true};
        """),
        Step(label: "E25B native consent + real ephemeral PostgreSQL returns verified fixture PASS", code: """
          const check=el('gradeApprove');if(!check)return {ok:false};check.click();
          const button=el('executeGrade');if(!button||button.disabled)return {ok:false};button.click();
          let s=null;for(let i=0;i<240;i++){
            await pause(500);s=window.tiaState;
            if(s?.live_preview?.sql_accuracy&&(!document.querySelector('[aria-busy="true"]')) )break;
          }
          const g=s?.live_preview?.sql_accuracy;
          return {ok:!!g&&g.correctness==='VERIFIED_LOCAL_FIXTURE'&&g.result.status==='PASSED'
            &&g.passed_fixtures===1&&g.question_sha256===s.live_preview.question.content_sha256
            &&g.approval_kind==='NATIVE_HUMAN_CONFIRMATION'&&s.activation.requests_used===2};
        """),
        Step(label: "E25B frozen Q1 receipt does not award grades to skipped Q2/Q3", code: """
          await press('finishRehearsalQuestion','API_PORTAL');await request('rehearsal_skip');
          await request('rehearsal_skip');const s=await snap();
          return {ok:s.rehearsal.status==='COMPLETE'&&s.rehearsal.results.length===3
            &&s.rehearsal.results[0].sql_accuracy.result.status==='PASSED'
            &&s.rehearsal.results[1].execution_status==='NOT_RUN'
            &&s.rehearsal.results[2].execution_status==='NOT_RUN'
            &&s.rehearsal.technical==='NOT_SCORED'};
        """),
        Step(label: "E3A completed rehearsal renders source-bound scorecard with no fabricated capability score", code: """
          await screen('REHEARSAL_COMPLETE');const s=await snap(),card=s.evidence_scorecard;
          const panel=el('evidenceScorecard'),text=panel?.textContent||'';
          return {ok:!!panel&&card?.schema==='tia-evidence-scorecard/v1'
            &&card?.summary?.latest_sql_locally_verified_questions===1
            &&card?.summary?.latest_sql_passed_local_fixtures===1
            &&card?.summary?.questions_without_current_sql_verification===2
            &&card?.summary?.overall_grade==='NOT_SCORED'
            &&card?.questions?.[0]?.accuracy?.status==='PASSED'
            &&card?.questions?.[1]?.accuracy?.status==='NOT_VERIFIED'
            &&card?.questions?.[2]?.accuracy?.status==='NOT_VERIFIED'
            &&panel.querySelectorAll('details').length===3
            &&text.includes('NOT_SCORED')&&!text.includes('100%')};
        """),
        Step(label: "E3B shows six C01–C06 dimensions for each closed question and never fabricates ratings", code: """
          await screen('REHEARSAL_COMPLETE');const s=await snap(),r=s.communication_evidence;
          const panel=el('communicationEvidence');const dims=r?.questions?.[0]?.dimensions||[];
          return {ok:!!panel&&r?.schema==='tia-communication-evidence/v1'
            &&r.summary.communication_competency==='NOT_SCORED'
            &&r.summary.evaluated_dimensions===0&&r.questions.length===3
            &&dims.map(x=>x.id).join(',')==='C01,C02,C03,C04,C05,C06'
            &&r.questions[1].dimensions.every(x=>x.anchor_0_to_4===null)
            &&panel.querySelectorAll('details').length===3
            &&panel.textContent.includes('NOT_OBSERVED')};
        """),
        Step(label: "E3C offline trainer binds practice to real receipt with no invented score or paid call", code: """
          await screen('REHEARSAL_COMPLETE'); const s=await snap(),t=s.grounded_trainer;
          const panel=el('groundedTrainer');const first=t?.drills?.[0];
          return {ok:!!panel&&t?.schema==='tia-grounded-trainer/v1'
            &&t.status==='READY_FOR_HUMAN_REVIEW'&&t.model_assessment==='NOT_REQUESTED'
            &&t.numeric_scores==='NOT_SCORED'&&t.sources.technical_sha256===s.evidence_scorecard.sha256
            &&t.sources.communication_sha256===s.communication_evidence.sha256
            &&t.drills.length>0&&first?.evidence?.question_sha256===s.evidence_scorecard.questions[0].question_sha256
            &&panel.textContent.includes(first.id)&&panel.textContent.includes('NOT_SCORED')
            &&s.activation.requests_used===2};
        """),
    ] + (trainerTesting ? [
        Step(label: "E3CB native mock paid Trainer uses approved citations and exposes only human-review feedback", code: """
          await screen('REHEARSAL_COMPLETE');
          const original=await snap();const requests=original.activation.requests_used;
          if(original.native_trainer_feedback!==null||!el('requestTrainer')||el('requestTrainer').disabled)return {ok:false};
          await press('requestTrainer');
          await until(()=>window.tiaState?.native_trainer_feedback?.status==='PENDING_HUMAN_REVIEW'
             && !document.querySelector('[aria-busy=\"true\"]'));
          const s=await snap(),f=s.native_trainer_feedback,panel=el('nativeTrainerPanel');
          return {ok:!!panel&&f.provenance==='LIVE_OPENAI_NATIVE_BYOK'&&f.authority==='NONE'
            &&f.technical_score==='NOT_SCORED'&&f.communication_score==='NOT_SCORED'
            &&f.drill_id===s.grounded_trainer.drills[0].id
            &&f.proposal.cited_candidate_events.join(',')===s.grounded_trainer.drills[0].evidence.candidate_event_ids.join(',')
            &&f.status==='PENDING_HUMAN_REVIEW'&&s.activation.requests_used===requests+1
            &&s.transport_mode==='MOCK_HTTP'&&panel.textContent.includes('PENDING_HUMAN_REVIEW')
            &&s.evidence_scorecard.summary.overall_grade==='NOT_SCORED'
            &&!el('requestTrainer')};
        """),
    ] : [])) : rehearsalTesting ? [
        Step(label: "E1 native rehearsal portal uses synthetic consent only", code: """
          await until(()=>document.documentElement.dataset.tiaReady==='true');
          await press('realInterview','API_PORTAL');return {ok:window.tiaState.activation.requests_used===0};
        """),
        Step(label: "E1 three distinct question imports and confirmations render start action", code: """
          await until(()=>window.tiaState.activation.state==='activated-unverified');
          await press('prepareSetup','CONFIG');
          await request('setup_config',{config:{technical_environment:'POSTGRESQL',duration_minutes:45,
            difficulty:'HARD',question_source:'BYOQ',interviewer_mechanism:'STRICT_CHALLENGING'}});
          for(let i=0;i<3;i++){
            const fields={problem_statement:'Find the total per customer for example '+i,task:'Aggregate rows for exercise '+i,
              schema:'Items'+i+'(id INT, customer_id INT)',example_input:'(1, 2)',expected_output:'(2)',
              environment:'POSTGRESQL',source:'OWNER',constraints:'One row per key',source_reference:''};
            const response=await request('setup_question_set',{index:i,source:'OWNER',raw_text:JSON.stringify(fields)});
            const review=response.setup_questions[i];
            await request('setup_question_confirm',{index:i,fields:review.fields,raw_sha256:review.raw_sha256});
          }
          const s=await snap();return {ok:s.screen==='QUESTION_SOURCE'&&!!el('startRehearsal')&&!el('startRehearsal').disabled&&s.setup_questions.every(q=>q.human_confirmed)};
        """),
        Step(label: "E1 start through WebKit and verify first native mocked question", code: """
          await press('startRehearsal','API_PORTAL');
          let s=await snap();if(s.rehearsal.status!=='ACTIVE'||s.rehearsal.current_index!==0)return {ok:false};
          await press('verifyPreview','LIVE_PREVIEW');s=await snap();
          return {ok:s.rehearsal.current_index===0&&s.activation.requests_used===1&&s.live_preview.candidate_turn_limit===4&&s.transport_mode==='MOCK_HTTP'};
        """),
        Step(label: "E2 timer starts on first presented question, exposes local-only clock", code: """
          const s=await snap();const t=s.rehearsal?.timing;
          return {ok:!!t&&t.started===true&&t.limit_seconds===2700
            &&document.getElementById('rehearsalClock')!==null
            &&document.getElementById('hostClockElapsed')!==null
            &&s.rehearsal.technical==='NOT_SCORED'
            &&t.events.some(e=>e.kind==='FIRST_QUESTION_PRESENTED')};
        """),
        Step(label: "E1 two successive turns use guarded mocked native requests", code: """
          for(let turn=0;turn<2;turn++){
            const box=el('previewResponse');box.value='Synthetic follow-up '+turn;
            box.dispatchEvent(new Event('input',{bubbles:true}));await press('sendPreview');
            await until(()=>window.tiaState?.live_preview?.candidate_turns_used===turn+1 &&
              window.tiaState.activation.requests_used===turn+2 && !document.querySelector('[aria-busy="true"]'));
          }
          const s=await snap();return {ok:s.live_preview.can_send===true&&s.live_preview.candidate_turns_used===2&&s.activation.requests_used===3};
        """),
        Step(label: "E1 finish Q1, skip Q2, open Q3 without extra calls", code: """
          await press('finishRehearsalQuestion','API_PORTAL');let s=await snap();
          if(s.rehearsal.results[0].outcome!=='DISCUSSION_ONLY'||s.rehearsal.current_index!==1)return {ok:false};
          await request('rehearsal_skip');s=await snap();
          return {ok:s.rehearsal.current_index===2&&s.rehearsal.results[1].outcome==='SKIPPED'&&s.activation.requests_used===3};
        """),
        Step(label: "E1 Q3 uses original question context and freezes unscored three-question outcome", code: """
          await press('verifyPreview','LIVE_PREVIEW');
          const input=el('previewResponse');input.value='My final explanation for question three.';
          input.dispatchEvent(new Event('input',{bubbles:true}));await press('sendPreview');
          await until(()=>window.tiaState?.activation?.requests_used===5&&!document.querySelector('[aria-busy="true"]'));
          await press('finishRehearsalQuestion','REHEARSAL_COMPLETE');
          const s=await snap();return {ok:s.rehearsal.status==='COMPLETE'&&s.rehearsal.results.length===3
            &&s.rehearsal.results[2].session.receipt.live_model_used===true&&s.rehearsal.execution==='NOT_RUN'
            &&s.rehearsal.technical==='NOT_SCORED'&&s.activation.requests_used===5};
        """),
        Step(label: "E2 score-free three-question time ledger remains exportable", code: """
          const s=await snap();const t=s.rehearsal?.timing;
          return {ok:!!t&&s.rehearsal.status==='COMPLETE'&&t.questions.length===3
            &&t.questions.every(q=>q.ended===true)
            &&t.model_wait_seconds<=t.elapsed_seconds
            &&s.rehearsal.results.every(r=>r.time_metrics!==undefined)
            &&document.getElementById('rehearsalClock')!==null};
        """),
    ] : failureTesting ? [
        Step(label: "failure journey opens synthetic native consent", code: """
          await until(()=>document.documentElement.dataset.tiaReady==='true');await press('realInterview','API_PORTAL');return {ok:true};
        """),
        Step(label: "401 is visible and commits no false interviewer event", code: """
          await until(()=>window.tiaState.activation.state==='activated-unverified');
          try{await request('preview_verify');return {ok:false};}catch(e){if(e.message!=='INVALID_CREDENTIALS')return {ok:false};}
          const s=await snap();return {ok:s.screen==='API_PORTAL'&&s.activation.state==='unavailable'&&!s.activation.authenticated&&s.activation.requests_total===1
          &&s.live_preview.verified_response_count===0&&!s.live_preview.pending};
        """),
        Step(label: "failure journey reopens synthetic native consent", code: """
          el('openPortal').click();await pause(100);return {ok:true};
        """),
        Step(label: "native timeout creates no response and never automatically retries", code: """
          await until(()=>window.tiaState.activation.state==='activated-unverified');
          try{await request('preview_verify');return {ok:false};}catch(e){if(e.message!=='PROVIDER_TIMEOUT')return {ok:false};}
          await pause(200);const s=await snap();return {ok:s.activation.requests_total===2&&s.live_preview.verified_response_count===0&&!s.live_preview.pending};
        """),
        Step(label: "explicit retry can verify via actual mocked transport", code: """
          await press('verifyPreview','LIVE_PREVIEW');const s=await snap();
          return {ok:s.activation.authenticated===true&&s.activation.requests_total===3&&s.live_preview.verified_response_count===1};
        """),
        Step(label: "pending cancellation crosses native and controller without late commit", code: """
          el('previewKind').value='help';el('previewResponse').value='Synthetic candidate diagnosis retained after cancellation.';
          el('previewResponse').dispatchEvent(new Event('input',{bubbles:true}));el('sendPreview').click();
          await until(()=>window.tiaState.activation.state==='connecting');
          if(el('cancelPreview').disabled||el('cancelPreview').closest('[hidden]'))return {ok:false};
          el('cancelPreview').click();await until(()=>!document.querySelector('[aria-busy="true"]'));await pause(1200);
          const s=await snap();return {ok:s.activation.requests_total===4&&s.live_preview.verified_response_count===1&&!s.live_preview.pending
          &&s.live_preview.session.events.filter(e=>e.actor==='candidate').length===1&&!!s.live_preview.retry_input};
        """),
        Step(label: "explicit retry reuses recorded candidate evidence then freezes receipt", code: """
          await press('sendPreview');await until(()=>window.tiaState.live_preview.verified_response_count===2);await press('closePreview');
          const s=await snap();return {ok:s.activation.requests_total===5&&s.live_preview.closed&&s.live_preview.session.events.filter(e=>e.actor==='candidate').length===1
          &&s.live_preview.session.receipt.live_model_used===true};
        """)
    ] : liveRecovering ? [
        Step(label: "live receipt reopens without credentials or automatic provider requests", code: """
          await until(()=>document.documentElement.dataset.tiaReady==='true');const s=await snap();
          return {ok:s.activation.state==='offline'&&s.activation.requests_used===0&&s.live_preview.closed===true&&s.live_preview.session.receipt.live_model_used===true};
        """),
        Step(label: "recovered live evidence and independent unscored fields remain intact", code: """
          const s=await snap(),p=s.live_preview;
          return {ok:p.session.receipt.sha256.length===64&&p.session.receipt.assessment.technical.status==='NOT_SCORED'&&p.session.receipt.assessment.communication.status==='NOT_SCORED'
          &&p.session.events.some(e=>e.provenance==='LIVE_MODEL')&&p.execution_status==='NOT_RUN'&&!!p.session.review};
        """)
    ] : liveTesting ? [
        Step(label: "mock live journey opens actual native paid-consent sheet", code: """
          await until(()=>document.documentElement.dataset.tiaReady==='true');await press('realInterview','API_PORTAL');
          return {ok:!!el('prepareSetup')&&window.tiaState.activation.requests_used===0&&document.querySelectorAll('input[type=password]').length===0};
        """),
        Step(label: "explicit activation alone remains unverified with zero requests", code: """
          await until(()=>window.tiaState.activation.state==='activated-unverified');const s=await snap();
          return {ok:s.activation.live_enabled===true&&s.activation.authenticated===false&&s.activation.requests_used===0&&!!el('verifyPreview')};
        """),
        Step(label: "native mock HTTP response crosses Python commit and verifies preview", code: """
          await press('verifyPreview','LIVE_PREVIEW');const s=await snap(),p=s.live_preview;
          return {ok:s.activation.state==='live-verified'&&s.activation.requests_used===1&&p.session.events.some(e=>e.actor==='interviewer'&&e.provenance==='LIVE_MODEL')
          &&p.execution_status==='NOT_RUN'&&p.technical==='NOT_SCORED'&&p.communication==='NOT_SCORED'&&s.transport_mode==='MOCK_HTTP'};
        """),
        Step(label: "candidate help and real native transport keep model output unscored", code: """
          el('previewKind').value='help';el('previewResponse').value='Synthetic: I identified timestamp ties. May I have a hint? <script>window.liveInjection=true</script>';
          el('previewResponse').dispatchEvent(new Event('input',{bubbles:true}));await press('sendPreview');
          await until(()=>window.tiaState.activation.requests_used===2&&window.tiaState.activation.state==='live-verified');const s=await snap(),p=s.live_preview;
          return {ok:p.session.events.some(e=>e.actor==='candidate'&&e.payload.text.includes('<script>'))&&!window.liveInjection
          &&p.session.events.filter(e=>e.provenance==='LIVE_MODEL').length===2&&p.execution_status==='NOT_RUN'&&s.activation.usage.total_tokens===312};
        """),
        Step(label: "preview uses compiled instruction provenance and compact accessible controls", code: """
          await pause(200);const s=await snap();
          return {ok:s.live_preview.prompt_provenance.sha256.length===64&&document.documentElement.scrollWidth<=innerWidth+1&&!!el('closePreview')&&!JSON.stringify(s).includes('synthetic-ui-fixture')};
        """, compact: true),
        Step(label: "host closure freezes LIVE_MODEL evidence with no SQL or scores", code: """
          await press('closePreview');const s=await snap(),p=s.live_preview;window.liveFrozen=p.session.receipt.sha256;
          return {ok:p.closed&&p.session.receipt.live_model_used===true&&p.session.receipt.sql_executed===false&&p.session.review
          &&p.session.receipt.assessment.technical.status==='NOT_SCORED'&&p.session.receipt.assessment.communication.status==='NOT_SCORED'};
        """),
        Step(label: "closed preview rejects a late turn without new HTTP or receipt edits", code: """
          try{await request('preview_send',{kind:'plan',text:'late attempt'});return {ok:false};}catch(e){}
          const s=await snap();return {ok:s.activation.requests_used===2&&s.live_preview.session.receipt.sha256===window.liveFrozen};
        """),
        Step(label: "disconnect clears authentication and retains truthful usage history", code: """
          await request('disconnect');const s=await snap();
          return {ok:s.activation.state==='offline'&&s.activation.authenticated===false&&s.activation.requests_total===2&&s.live_preview.session.receipt.sha256===window.liveFrozen};
        """)
    ] : recovering ? [
        Step(label: "reopened native App restores saved screen and completed S02 session", code: """
          await until(()=>document.documentElement.dataset.tiaReady==='true');
          const s=await snap();return {ok:s.screen==='API_PORTAL'&&s.language==='zh'&&s.session.phase==='COMPLETE'&&s.saved_locally===true&&s.activation.state==='offline'};
        """),
        Step(label: "reopened App retains candidate SQL and immutable reviewed Trainer evidence", code: """
          const s=await snap();return {ok:s.session.events.some(e=>e.kind==='implement'&&e.payload.text==='SELECT * FROM Orders;')
          &&s.session.receipt.sha256.length===64&&s.session.review&&s.trainer_preview.evidence_ids.length===3&&s.api_requests===0};
        """)
    ] : setupTesting ? [
        Step(label: "configuration still requires the API Portal entry step", code: """
          await until(()=>document.documentElement.dataset.tiaReady==='true');
          try {await request('setup_continue');return {ok:false};}catch(e){}
          return {ok:window.tiaState.screen==='ENTRY'&&window.tiaState.activation.state==='offline'};
        """),
        Step(label: "keyless setup can cancel the mandatory first API Portal", code: """
          await press('realInterview','API_PORTAL');return {ok:!!el('prepareSetup')&&document.querySelectorAll('input[type=password]').length===0};
        """),
        Step(label: "keyless Wizard reaches review and full launch stays blocked with zero requests", code: """
          await press('prepareSetup','CONFIG');await press('nextSetup','QUESTION_SOURCE');
          await request('setup_config',{config:{technical_environment:'POSTGRESQL',duration_minutes:45,difficulty:'HARD',question_source:'RANDOM_GENERATED',interviewer_mechanism:'STRICT_CHALLENGING'}});
          await press('reviewQuestions','MECHANISM');await press('reviewSetup','REVIEW');
          try{await request('setup_launch');return {ok:false};}catch(e){if(e.message!=='LAUNCH_BLOCKED')return {ok:false};}
          const s=await snap();if(s.activation.authenticated||s.activation.requests_used!==0||s.setup_config.question_count!==3)return {ok:false};
          await request('setup_back');await request('setup_back');await request('setup_back');
          await request('setup_config',{config:{technical_environment:'POSTGRESQL',duration_minutes:45,difficulty:'HARD',question_source:'BYOQ',interviewer_mechanism:'STRICT_CHALLENGING'}});
          await request('setup_back');await request('setup_back');return {ok:window.tiaState.screen==='API_PORTAL'};
        """),
        Step(label: "setup begins with actual native secure credential sheet", code: """
          el('openPortal').click();await pause(100);return {ok:document.querySelectorAll('input[type=password]').length===0};
        """),
        Step(label: "synthetic native credential is only locally configured and unverified", code: """
          await until(()=>window.tiaState.activation.state==='activated-unverified');
          await press('prepareSetup','CONFIG');const s=await snap();
          return {ok:s.activation.authenticated===false&&s.activation.live_enabled===true&&s.activation.requests_used===0&&s.session===null};
        """),
        Step(label: "60 minutes derives four and 45 derives three Hard questions", code: """
          el('durationMinutes').value='60';el('durationMinutes').dispatchEvent(new Event('change'));
          if(el('derivedQuestionCount').textContent!=='4')return {ok:false};
          el('durationMinutes').value='45';el('durationMinutes').dispatchEvent(new Event('change'));
          if(el('derivedQuestionCount').textContent!=='3')return {ok:false};
          await press('nextSetup','QUESTION_SOURCE');const s=await snap();
          return {ok:s.setup_config.question_count===3&&s.setup_config.difficulty==='HARD'&&s.setup_config.status==='DRAFT'&&!!el('byoqQuestion2')&&!el('byoqQuestion3')};
        """),
        Step(label: "S03-D freeform LeetCode original can extract, review and confirm through real bridge", code: """
          const raw='3521. Synthetic Product Pairs\\nMedium\\nTable: Purchases\\n|user_id|product_id|\\n|1|101|\\nWrite a solution to count the pairs bought together.\\nExample:\\nInput:\\n|1|101|\\nOutput:\\n|101|102|3|';
          const box=el('byoqQuestion0');box.value=raw;box.dispatchEvent(new Event('input',{bubbles:true}));
          el('byoqSource0').value='LEETCODE';await press('extractQuestion0');
          await until(()=>window.tiaState.setup_questions?.length===1);
          let s=await snap();const r=s.setup_questions[0];
          if(!r.extraction||r.extraction.title.id!=='3521'||!r.fields.schema.includes('Purchases')||!el('confirmQuestion0'))return {ok:false};
          await press('confirmQuestion0');s=await snap();
          if(!s.setup_questions[0].practice_eligible||!el('practiceQuestion0')||s.setup_allocation.launch_authorized)return {ok:false};
          try{await request('setup_questions',{questions:[]});}catch(e){if(e.message!=='QUESTION_REVIEW_REQUIRED')return {ok:false};}
          const remaining=el('byoqQuestion0');remaining.value='';remaining.dispatchEvent(new Event('input',{bubbles:true}));
          s=await snap();return {ok:s.screen==='QUESTION_SOURCE'&&s.setup_questions.length===0};
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
        Step(label: "disconnect keeps full launch blocked while keyless draft remains usable", code: """
          await request('disconnect');
          try {await request('setup_launch');return {ok:false};}catch(e){}
          await request('setup_back');
          const s=await snap();
          return {ok:s.screen==='MECHANISM'&&s.activation.state==='offline'&&s.activation.authenticated===false&&s.activation.requests_used===0&&!JSON.stringify(s).includes('synthetic-ui-fixture')};
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
          const before={disabled:el('openPortal').disabled,busy:document.querySelector('[aria-busy="true"]')!==null};el('openPortal').click();await pause(21000);
          return {ok:el('error').hidden&&document.querySelector('[aria-busy="true"]')!==null&&window.tiaState.activation.requests_used===0,
            before,error:el('error').textContent,busy:document.querySelector('[aria-busy="true"]')!==null,requests:window.tiaState.activation.requests_used};
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
        guard next < steps.count else { end(true, "\(steps.count) real UI checks; \(TIATestHTTPProtocol.calls) mocked HTTP requests; zero real provider requests"); return }
        let step = steps[next]
        if step.compact { app.window.setContentSize(NSSize(width: 720, height: 600)) }
        app.webView.callAsyncJavaScript(helper + "\n" + step.code, arguments: [:], in: nil, in: .page) { [weak self] result in
            guard let self = self, !self.done else { return }
            guard case .success(let value) = result, let object = value as? [String: Any], object["ok"] as? Bool == true else {
                print("UI check detail: \(result)")
                print("Native portal visible: \(app.portalIsVisible)")
                self.end(false, step.label); return
            }
            if step.label == "real AI immediately enters native API Portal ahead of config" ||
                step.label == "keyless setup can cancel the mandatory first API Portal" ||
                step.label == "native human decision stays pending beyond twenty seconds without false timeout" {
                guard app.portalIsVisible else { self.end(false, "Native API sheet not visible"); return }
                app.cancelPortalForTest()
            }
            if step.label == "E25B opens native consent for synthetic fixture-only interview" || step.label == "E1 native rehearsal portal uses synthetic consent only" || step.label == "setup begins with actual native secure credential sheet" || step.label == "mock live journey opens actual native paid-consent sheet" || step.label == "failure journey opens synthetic native consent" || step.label == "failure journey reopens synthetic native consent" {
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
                    do { try png.write(to: self.directory.appendingPathComponent((self.failureTesting ? "failure-" : self.gradingTesting ? "grading-" : self.rehearsalTesting ? "rehearsal-" : self.liveRecovering ? "live-recovery-" : self.liveTesting ? "live-" : self.recovering ? "recovery-" : self.setupTesting ? "setup-" : "") + String(format: "%02d.png", number))) }
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
            "api_requests": 0, "mock_http_requests": TIATestHTTPProtocol.calls, "transport": "MOCK_HTTP", "real_credentials_used": false, "synthetic_credential_fixture_used": setupTesting || liveTesting || failureTesting || rehearsalTesting || gradingTesting, "human_uat": "NOT_RUN"]
        if let data = try? JSONSerialization.data(withJSONObject: receipt, options: [.prettyPrinted, .sortedKeys]) {
            try? data.write(to: directory.appendingPathComponent(failureTesting ? "ui-provider-failure-receipt.json" : gradingTesting ? "ui-grading-receipt.json" : rehearsalTesting ? "ui-rehearsal-receipt.json" : liveRecovering ? "ui-live-recovery-receipt.json" : liveTesting ? "ui-live-receipt.json" : recovering ? "ui-recovery-receipt.json" : setupTesting ? "ui-setup-receipt.json" : "ui-test-receipt.json"))
        }
        print("Native UI smoke: \(success ? "PASS" : "FAIL") — \(message)")
        finish(success ? 0 : 1)
    }
}
