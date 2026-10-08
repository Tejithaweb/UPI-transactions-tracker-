const $ = id => document.getElementById(id);
const money = n => '₹' + Number(n || 0).toLocaleString('en-IN', {maximumFractionDigits: 2});
let monthlyChart, categoryChart;
function notice(message, error=false) { const el=$('notice'); el.textContent=message; el.className='notice show'+(error?' error':''); }
function addTextCell(row, value) { const td=document.createElement('td'); td.textContent=value ?? ''; row.appendChild(td); }
async function refresh() {
  const sr=await fetch('/api/summary'); const s=await sr.json();
  $('count').textContent=Number(s.count).toLocaleString('en-IN'); $('debit').textContent=money(s.debit); $('credit').textContent=money(s.credit); $('avg').textContent=money(s.average);
  $('ratio').textContent=s.credit_debit_ratio === null ? 'N/A' : `${s.credit_debit_ratio.toFixed(2)} (${s.debit ? (s.credit/s.debit).toFixed(2)+':1' : 'N/A'})`;
  $('dataMode').textContent=s.using_uploaded_data?'Uploaded CSV data':'Demo data';
  const old=$('cat').value; $('cat').innerHTML='<option value="">All categories</option>';
  Object.keys(s.categories).forEach(x=>{const o=document.createElement('option');o.value=x;o.textContent=x;$('cat').appendChild(o)}); if ([...$('cat').options].some(o=>o.value===old)) $('cat').value=old;
  if(monthlyChart) monthlyChart.destroy(); if(categoryChart) categoryChart.destroy();
  monthlyChart=new Chart($('m'),{type:'bar',data:{labels:Object.keys(s.monthly),datasets:[{label:'Debit',data:Object.values(s.monthly)}]},options:{responsive:true}});
  categoryChart=new Chart($('c'),{type:'doughnut',data:{labels:Object.keys(s.categories),datasets:[{data:Object.values(s.categories)}]},options:{responsive:true}});
  await load();
}
async function load(){
  const url=`/api/transactions?q=${encodeURIComponent($('q').value)}&type=${encodeURIComponent($('type').value)}&category=${encodeURIComponent($('cat').value)}`;
  const response=await fetch(url); const rows=await response.json(); const tbody=$('body'); tbody.replaceChildren();
  rows.slice(0,250).forEach(r=>{const tr=document.createElement('tr');['date','time','merchant'].forEach(k=>addTextCell(tr,r[k]));addTextCell(tr,money(r.amount));addTextCell(tr,r.type);addTextCell(tr,r.purpose);tr.addEventListener('click',()=>{const d=$('details');d.replaceChildren();Object.entries(r).forEach(([k,v])=>{const item=document.createElement('div'),small=document.createElement('small'),b=document.createElement('b');small.textContent=k.replaceAll('_',' ');b.textContent=v;item.append(small,b);d.appendChild(item)})});tbody.appendChild(tr)});
  $('rowCount').textContent=`Showing ${Math.min(rows.length,250)} of ${rows.length} matching transactions.`;
}
$('file').addEventListener('change',async e=>{const file=e.target.files[0];if(!file)return;const form=new FormData();form.append('file',file);notice('Importing and validating CSV…');try{const res=await fetch('/api/upload',{method:'POST',body:form});const result=await res.json();if(!res.ok){notice(result.error||'Upload failed.',true);return}notice(result.message);await refresh()}catch(err){notice('Could not upload the file. Check that the app is running.',true)}finally{e.target.value=''}});
$('resetDemo').addEventListener('click',async()=>{if(!confirm('Restore demo data? This replaces the currently active uploaded dataset in this local app.'))return;const res=await fetch('/api/reset-demo',{method:'POST'});const result=await res.json();notice(result.message);await refresh()});
['q','type','cat'].forEach(id=>$(id).addEventListener(id==='q'?'input':'change',load));
refresh().catch(()=>notice('Could not load dashboard. Check the Command Prompt window.',true));
