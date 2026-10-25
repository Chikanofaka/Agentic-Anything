'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const crypto=require('node:crypto');
const vm=require('node:vm');
const portal=fs.readFileSync(process.argv[2],'utf8');
const js=portal.match(/<script>([\s\S]*?)<\/script>/)?.[1];
assert.ok(js, 'script must exist');
new vm.Script(js);  // syntax gate
const nodes=new Map();
class Node {
 constructor(tag='div'){this.tag=tag;this.children=[];this.attrs={};this.listeners={};this.value='';this.files=[];this.style={};this.textContent='';this.className='';this.tabIndex=0;}
 setAttribute(k,v){this.attrs[k]=String(v)}
 append(...items){this.children.push(...items)}
 replaceChildren(...items){this.children=items;this.textContent=''}
 addEventListener(event,cb){this.listeners[event]=cb}
 click(){return this.listeners.click?.()}
 focus(){}
 get innerText(){return this.textContent}
}
const document={getElementById(id){if(!nodes.has(id))nodes.set(id,new Node());return nodes.get(id)},createElement(tag){return new Node(tag)},createElementNS(ns,tag){return new Node(tag)}};
const window={isSecureContext:true};
const URL={createObjectURL(){return 'blob://fake'},revokeObjectURL(){}};
const ctx={document,window,URL,Blob,TextDecoder,crypto:crypto.webcrypto,Date,Number,Object,String,Math,Map,Set,Array,JSON,RegExp,Error,console,setTimeout(fn){fn()}};
vm.createContext(ctx);vm.runInContext(js,ctx,{timeout:3000});
const api=window.TIA_E4D04;assert.equal(api.METRICS.length,11);
assert.equal(api.METRICS.filter(x=>x.category==='Technical').reduce((s,x)=>s+x.max,0),60);
assert.equal(api.METRICS.filter(x=>x.category==='Communication').reduce((s,x)=>s+x.max,0),40);
const empty={ratings:{}};
assert.equal(api.compute(empty).Technical.observed,0);
assert.equal(api.compute(empty).Communication.possibleUpper,40);
assert.equal(api.sourceKind('sample note','txt').type,'DAILY_RECORD');
assert.throws(()=>api.sourceKind('{','json'),/INVALID_JSON_SOURCE/);
assert.throws(()=>api.sourceKind('{"schema":"tia-e4d03-session-report/v1"}','json'),/INVALID_E4D03_REPORT/);
assert.equal(api.sourceKind(JSON.stringify({schema:'tia-e4d03-session-report/v1',questions:[{},{},{}],recovered_evaluator_proposals:1,session_final_score_status:'NOT_SCORED'}),'json').proposals,1);
assert.throws(()=>api.validatePortfolio({schema:api.PORTFOLIO_SCHEMA,records:[{sourceHash:'wrong'}]}),/INVALID_PORTFOLIO_ROW/);
const get=id=>document.getElementById(id);
(async()=>{
 get('sourceFile').files=[{name:'daily.txt',size:22,async arrayBuffer(){return Uint8Array.from(Buffer.from('An observed SQL attempt')).buffer.slice(0)}}];
 get('sessionDate').value='2026-10-25';get('domain').value='SQL';get('labelInput').value='SQL day one';get('noteInput').value='Need more testing';
 await get('checkin').click();
 assert.equal(api.getState().rows.length,1);
 assert.equal(api.getState().rows[0].scoreStatus,'NOT_SCORED');
 assert.match(get('flash').textContent,/CHECKIN=PASS/);
 get('metricSelect').value='C01';get('anchorSelect').value='3';get('eventId').value='';get('rationale').value='Candidate asked a clarifying question.';
 get('saveMetric').click();assert.match(get('flash').textContent,/EVIDENCE_REFERENCE_REQUIRED/);
 get('eventId').value='candidate-event1';get('saveMetric').click();assert.match(get('flash').textContent,/ANNOTATION_SAVED/);
 assert.equal(api.compute(api.getState().rows[0]).Communication.observed,1);
 assert.equal(api.getState().rows[0].ratings.C01.origin,'USER_SELF_REPORTED_UNVERIFIED');
 get('sourceFile').files=[{name:'daily.txt',size:22,async arrayBuffer(){return Uint8Array.from(Buffer.from('An observed SQL attempt')).buffer.slice(0)}}];
 await get('checkin').click();assert.match(get('flash').textContent,/DUPLICATE_SOURCE_SHA/);
 get('checkout').click();assert.match(get('flash').textContent,/CHECKOUT=PASS/);
 const record=api.getState().rows[0];
 const valid={schema:api.PORTFOLIO_SCHEMA,records:[JSON.parse(JSON.stringify(record))]};
 assert.equal(api.validatePortfolio(valid).length,1);
 const invalid={schema:api.PORTFOLIO_SCHEMA,records:[{...record,ratings:{T02:{anchor:5,evidence:'test-event',rationale:'Invalid anchor',origin:'USER_SELF_REPORTED_UNVERIFIED'}}}]};
 assert.throws(()=>api.validatePortfolio(invalid),/UNTRUSTED_RATING_CLAIM/);
 console.log('BROWSER_CONTRACT=PASS: metric sum, missingness, source schema, check-in, duplicate, evidence, checkout, private portfolio import contract');
})().catch(e=>{console.error(e);process.exit(1)});
