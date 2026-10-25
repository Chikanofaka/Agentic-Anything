#!/usr/bin/env node
/* Deterministic E4 closeout view-model tests; no browser, network or secrets. */
'use strict';
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const path = require('node:path');
const app = fs.readFileSync(path.resolve(__dirname, '../ui/app.js'),'utf8');
const from = app.indexOf('  function evaluatorCloseoutModel(snapshot) {');
const to = app.indexOf('  function evaluatorCloseoutPanel()', from);
assert.ok(from >= 0 && to > from, 'closeout module installed and ordered');
const isolated = vm.runInNewContext(app.slice(from,to) + '\nevaluatorCloseoutModel;',{});
const base = {
  rehearsal:{status:'COMPLETE',results:[{},{},{}]},
  evaluator_report:{full_scheme:{schema:'tia-evaluator-full-scheme/v1',evaluations_current:3,evaluations_legacy:0,final_overall_score:'NOT_SCORED'}},
  smart_plan:{schema:'tia-smart-improvement-plan/v1',status:'READY_TO_START'},
  smart_progress_summary:{recorded_attempts:2},grounded_trainer:{drills:[{id:'d1'}]}
};
let tests=0;
function check(name,fn){fn();tests++;console.log('PASS '+name)}
check('complete session recognized',()=>{assert.equal(isolated(base).evidenceStatus,'FROZEN')});
check('provisional proposals never promoted',()=>{assert.equal(isolated(base).grade,'NOT_SCORED')});
check('practice explicitly self-reported',()=>{assert.equal(isolated(base).practiceStatus,'SELF_REPORTED_ACTIVITY_ONLY')});
check('export never claimed archived',()=>{assert.equal(isolated(base).archiveStatus,'USER_EXPORT_REQUIRED_UNATTESTED')});
check('retest remains separate session',()=>{assert.equal(isolated(base).retestStatus,'AWAITING_INDEPENDENT_NEXT_SESSION')});
check('older assessment acknowledged without promotion',()=>{const b=structuredClone(base);b.evaluator_report.full_scheme.evaluations_current=0;b.evaluator_report.full_scheme.evaluations_legacy=3;assert.equal(isolated(b).evaluationStatus,'PENDING_OR_LEGACY_ONLY')});
check('incomplete history not frozen',()=>{assert.equal(isolated({rehearsal:{status:'ACTIVE',results:[{}]}}).locked,false)});
check('no grade or automatic model request in UI',()=>{const fragment=app.slice(to,app.indexOf('  function rehearsalComplete(main)',to));assert.ok(!/act\("(?:evaluator_generate|trainer_request|grade_execute)"/.test(fragment));assert.ok(fragment.includes('act("export")'))});
check('closeout wired into completed page',()=>{assert.ok(app.includes('smartPlanPanel(), evaluatorCloseoutPanel()'))});
console.log(`TIA_E4_CLOSEOUT_TESTS=${tests}/${tests} PASS`);
