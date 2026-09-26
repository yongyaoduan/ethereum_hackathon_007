let securityCaseId=null,securityType='all',securityClockStart=0,securityFrameStarted=false,securityHeldAt=0,securityHits=[],securityLastSecond=-1;
const securitySchedule=[
 {id:'reentrancy-benign',at:30,code:'S-001'},
 {id:'faulty_access_control-attack',at:85,code:'S-002'},
 {id:'price_manipulation-benign',at:135,code:'S-003'},
 {id:'reentrancy-attack',at:195,code:'S-004'},
 {id:'faulty_access_control-benign',at:245,code:'S-005'},
 {id:'price_manipulation-attack',at:315,code:'S-006'}
];
const securityTime=t=>'T+'+String(Math.floor(((t%360)+360)%360/60)).padStart(2,'0')+':'+String(Math.floor(((t%360)+360)%60)).padStart(2,'0');
const securitySourceDate=t=>new Date(t).toLocaleString('en-GB',{year:'numeric',month:'short',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',timeZone:'UTC',hour12:false})+' UTC';
const securitySourceURL=g=>'https://hsk.blockscout.com/tx/'+g.source_transaction.hash;
function securityCaseEntry(id){for(const g of securityData.groups){const sample=g.variants.find(s=>s.id===id);if(sample)return {group:g,sample,pattern:securityPatterns[g.id],schedule:securitySchedule.find(s=>s.id===id)}}}
function securityCaseImpact(g,v){
 if(g.id==='reentrancy')return {amount:v.variant==='attack'?'20':'0',unit:'HSK',label:'excess withdrawal'};
 if(g.id==='faulty_access_control')return {amount:v.variant==='attack'?'40':'5',unit:'HSK',label:'transferred'};
 return {amount:v.variant==='attack'?'30,000':'5,000',unit:'USDT',label:'outstanding debt'};
}
async function renderSecurity(){
 try{await loadSecurityData()}catch{$('#security-content').innerHTML='<div class="empty">Unable to load cases. <button id="security-retry">Try again</button></div>';$('#security-retry').onclick=renderSecurity;return}
 if(securityHeldAt){securityClockStart+=performance.now()-securityHeldAt;securityHeldAt=0}
 $('#security-content').innerHTML=`<section class="security-stream-panel"><div class="security-stream-heading"><div><span class="stream-kicker">EVENT TIMELINE</span><h2>Security stream</h2></div><div class="security-clock"><span id="security-cycle">Cycle 01</span><strong id="security-clock">T+03:30</strong><span class="sim-indicator">Simulation</span></div></div><div class="security-stream-stage"><canvas id="security-stream" aria-label="Animated synthetic case timeline; three attack-type lanes, height represents trace event count"></canvas><div id="security-stream-tip" hidden></div></div><div class="security-stream-footer"><span><i class="case-symbol attack"></i>Attack variant <i class="case-symbol baseline"></i>Baseline</span><span>6 cases <b>·</b> 3 patterns <b>·</b> 6-minute cycle<details class="stream-help"><summary aria-label="About simulation time">ⓘ</summary><p>T+ is scenario time, advanced at 6× speed. The six cases repeat each cycle. Height counts authored trace events, not loss or severity. Hover holds the view; select a marker to open its case. Source transaction times are shown in the case list.</p></details></span></div></section><section class="security-case-index"><div class="case-index-heading"><h2>Cases <span>06</span></h2><div class="case-type-tabs" aria-label="Case type filter"><button data-security-type="all" aria-pressed="${securityType==='all'}">All types</button>${Object.entries(securityPatterns).map(([k,p])=>`<button data-security-type="${k}" aria-pressed="${securityType===k}" style="--pattern:${p.color}">${p.name}</button>`).join('')}</div></div><div id="security-case-list"></div></section>`;
 renderSecurityList();
 document.querySelectorAll('[data-security-type]').forEach(b=>b.onclick=()=>{securityType=b.dataset.securityType;document.querySelectorAll('[data-security-type]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));renderSecurityList()});
 const canvas=$('#security-stream');canvas.onpointerenter=()=>securityHeldAt=performance.now();canvas.onpointerleave=()=>{if(securityHeldAt)securityClockStart+=performance.now()-securityHeldAt;securityHeldAt=0;$('#security-stream-tip').hidden=true};canvas.onpointermove=e=>{const hit=securityHit(e),tip=$('#security-stream-tip');canvas.style.cursor=hit?'pointer':'default';tip.hidden=!hit;if(hit){const en=securityCaseEntry(hit.id);tip.textContent=`${en.schedule.code} · ${en.pattern.name} · ${en.sample.variant==='attack'?'Attack variant':'Baseline'} · ${securityTime(en.schedule.at)}`;tip.style.left=Math.max(10,Math.min(e.offsetX+16,canvas.clientWidth-300))+'px';tip.style.top=Math.max(10,e.offsetY-53)+'px'}};canvas.onclick=e=>{const hit=securityHit(e);if(hit)openSecurityCase(hit.id)};
 if(!securityFrameStarted){securityFrameStarted=true;securityClockStart=performance.now()-95000;requestAnimationFrame(drawSecurityStream)}
 if(securityCaseId&&securityCaseEntry(securityCaseId))openSecurityCase(securityCaseId,false);
}
function renderSecurityList(){
 $('#security-case-list').innerHTML=securityData.groups.filter(g=>securityType==='all'||securityType===g.id).map(g=>{const p=securityPatterns[g.id];return `<section class="case-group" style="--pattern:${p.color}"><div class="case-group-heading"><div class="case-group-name"><span class="case-group-icon"><svg viewBox="0 0 30 30" aria-hidden="true"><path d="${p.icon}"/></svg></span><h3>${p.name}</h3><span class="case-group-count">${g.variants.length} cases</span></div><span class="case-group-summary">1 attack variant <b>/</b> 1 baseline</span></div><div class="case-row-labels"><span>Case</span><span>Simulation time</span><span>Source time · UTC</span><span>Impact</span><span></span></div>${g.variants.map(v=>{const sc=securitySchedule.find(s=>s.id===v.id),impact=securityCaseImpact(g,v);return `<button class="security-case-row" data-security-case="${v.id}" aria-label="Open ${p.name} ${v.variant==='attack'?'attack':'baseline'} case ${sc.code}"><span class="case-row-title"><span class="case-id">${sc.code}</span><strong>${p[v.variant].title}</strong><em class="case-variant ${v.variant}">${v.variant==='attack'?'Attack variant':'Baseline'}</em></span><span class="case-row-time">${securityTime(sc.at)}<small>Each cycle</small></span><time class="case-source-time" datetime="${g.source_transaction.timestamp}">${securitySourceDate(g.source_transaction.timestamp).replace(' UTC','').replace(', ','<br>')}<small>Operation template</small></time><span class="case-impact"><strong>${impact.amount}<small>${impact.unit}</small></strong><em>${impact.label}</em></span><span class="case-open">↗</span></button>`}).join('')}</section>`}).join('');
 document.querySelectorAll('[data-security-case]').forEach(b=>b.onclick=()=>openSecurityCase(b.dataset.securityCase));
}
async function openSecurityCase(id,updateURL=true){
 const entry=securityCaseEntry(id);if(!entry)return;
 securityCaseId=id;securityGroup=entry.group.id;securityVariant=entry.sample.variant;securityStep=0;
 $('#security-case-id').textContent=entry.schedule.code+' / '+entry.pattern.name;
 $('#security-case-time').textContent='Synthetic case · '+securityTime(entry.schedule.at);
 await renderSecurityCase();
 const d=$('#security-case-drawer');if(!d.open)d.showModal();d.scrollTop=0;
 if(updateURL)history.replaceState(null,'','#security?case='+encodeURIComponent(id));
}
function closeSecurityCase(){securityCaseId=null;$('#security-case-drawer').close();if(view==='security')history.replaceState(null,'','#security')}
$('#security-case-close').onclick=closeSecurityCase;
$('#security-case-drawer').addEventListener('cancel',e=>{e.preventDefault();closeSecurityCase()});
$('#security-case-drawer').addEventListener('close',()=>{securityCaseId=null;if(view==='security')history.replaceState(null,'','#security')});
function securityHit(e){const r=$('#security-stream').getBoundingClientRect(),x=e.clientX-r.left,y=e.clientY-r.top;return securityHits.find(h=>Math.hypot(h.x-x,h.y-y)<22)}
function drawSecurityStream(now){
 requestAnimationFrame(drawSecurityStream);if(view!=='security'||document.hidden||!securityData)return;
 const canvas=$('#security-stream');if(!canvas)return;const box=canvas.getBoundingClientRect(),W=box.width,H=box.height;if(!W)return;const ctx=canvas.getContext('2d'),dpr=Math.min(devicePixelRatio||1,2);if(canvas.width!==Math.round(W*dpr)||canvas.height!==Math.round(H*dpr)){canvas.width=Math.round(W*dpr);canvas.height=Math.round(H*dpr)}ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,W,H);
 const narrow=W<650,left=narrow?100:194,right=W-45,span=right-left,elapsed=((securityHeldAt||now)-securityClockStart)/1000*6,end=elapsed+20,start=end-360,X=t=>left+(t-start)/360*span,base=(x,z)=>95+z*(narrow?80:91)+(x-left)*.04,maxCount=Math.max(...securitySchedule.map(s=>securityEvents(securityCaseEntry(s.id).sample).length));
 const sec=Math.floor(elapsed);if(sec!==securityLastSecond){securityLastSecond=sec;$('#security-clock').textContent=securityTime(elapsed);$('#security-cycle').textContent='Cycle '+String(Math.floor(elapsed/360)+1).padStart(2,'0')}
 const glow=ctx.createRadialGradient(W*.58,H*.6,10,W*.58,H*.6,W*.54);glow.addColorStop(0,'#d4deed44');glow.addColorStop(1,'#ffffff00');ctx.fillStyle=glow;ctx.fillRect(0,0,W,H);
 ctx.font='12px "DM Sans",sans-serif';for(let t=Math.ceil(start/(narrow?120:60))*(narrow?120:60);t<end;t+=narrow?120:60){const x=X(t);ctx.beginPath();ctx.moveTo(x,47);ctx.lineTo(x,base(x,2)+37);ctx.strokeStyle='#e5eaf180';ctx.lineWidth=1;ctx.stroke();ctx.fillStyle='#97a5b8';ctx.textAlign='center';ctx.fillText(securityTime(t).slice(2),x,base(x,2)+58);if(t%360===0){ctx.fillStyle='#b1bccb';ctx.font='10px \"DM Sans\",sans-serif';ctx.fillText('CYCLE '+String(Math.floor(t/360)+1).padStart(2,'0'),x,base(x,2)+75);ctx.font='12px \"DM Sans\",sans-serif'}}
 securityHits=[];Object.entries(securityPatterns).forEach(([gid,p],z)=>{
  const events=[];for(let cycle=Math.floor(start/360)-1;cycle<=Math.ceil(end/360);cycle++)securitySchedule.forEach(s=>{const en=securityCaseEntry(s.id),t=cycle*360+s.at;if(en.group.id===gid&&t>=start&&t<=end)events.push({...s,t,n:securityEvents(en.sample).length,attack:en.sample.variant==='attack'})});
  ctx.textAlign='right';ctx.fillStyle=p.color;ctx.font='500 '+(narrow?12:14)+'px "DM Sans",sans-serif';if(narrow&&p.name!=='Reentrancy'){ctx.fillText(p.name==='Access control'?'Access':'Price',left-20,base(left,z)-3);ctx.fillText(p.name==='Access control'?'control':'manipulation',left-20,base(left,z)+12)}else ctx.fillText(p.name,left-20,base(left,z)+5);
  ctx.beginPath();ctx.moveTo(left,base(left,z));ctx.lineTo(right,base(right,z));ctx.lineWidth=.8;ctx.strokeStyle=p.color+'30';ctx.stroke();
  const peak=x=>events.reduce((a,e)=>a+(e.n/maxCount)*(narrow?59:73)*Math.exp(-Math.pow((x-X(e.t))/Math.max(7,span*.018),2)),0);
  const ridge=new Path2D();ridge.moveTo(left,base(left,z));for(let x=left;x<=right;x+=2)ridge.lineTo(x,base(x,z)-peak(x));for(let x=right;x>=left;x-=2)ridge.lineTo(x+12,base(x,z)-peak(x)-8);ridge.closePath();ctx.fillStyle=p.color+'1b';ctx.fill(ridge);
  const path=new Path2D();path.moveTo(left,base(left,z));for(let x=left;x<=right;x+=2)path.lineTo(x,base(x,z)-peak(x));path.lineTo(right,base(right,z)+7);path.lineTo(left,base(left,z)+7);path.closePath();const fill=ctx.createLinearGradient(0,base(left,z)-75,0,base(right,z)+9);fill.addColorStop(0,p.color+'75');fill.addColorStop(.6,p.color+'28');fill.addColorStop(1,p.color+'07');ctx.fillStyle=fill;ctx.fill(path);
  ctx.beginPath();for(let x=left;x<=right;x+=2)x===left?ctx.moveTo(x,base(x,z)-peak(x)):ctx.lineTo(x,base(x,z)-peak(x));ctx.strokeStyle=p.color+'bb';ctx.lineWidth=1.7;ctx.stroke();
  events.forEach(e=>{const x=X(e.t),y=base(x,z)-peak(x),age=elapsed-e.t;ctx.save();ctx.shadowColor=p.color+'50';ctx.shadowBlur=14;ctx.beginPath();ctx.arc(x,y,5.5,0,Math.PI*2);ctx.fillStyle=e.attack?p.color:'#fff';ctx.fill();ctx.strokeStyle=p.color;ctx.lineWidth=1.8;ctx.stroke();ctx.restore();if(age>=0&&age<14){ctx.beginPath();ctx.arc(x,y,8+age*1.2,0,Math.PI*2);ctx.strokeStyle=p.color+Math.round(110*(1-age/14)).toString(16).padStart(2,'0');ctx.lineWidth=1;ctx.stroke()}ctx.textAlign='center';ctx.font='12px "DM Sans",sans-serif';ctx.fillStyle='#71829b';ctx.fillText(e.code,x,y-15);securityHits.push({id:e.id,x,y});});
 });
 const scanX=X(elapsed);ctx.beginPath();ctx.moveTo(scanX,26);ctx.lineTo(scanX,base(scanX,2)+37);ctx.strokeStyle='#7a91b84d';ctx.lineWidth=1;ctx.setLineDash([3,5]);ctx.stroke();ctx.setLineDash([]);ctx.fillStyle='#7d91ab';ctx.textAlign='center';ctx.font='11px "DM Sans",sans-serif';ctx.fillText('SCENARIO TIME',scanX-42,19);canvas.dataset.frame=String(Math.floor(elapsed*10));
}
