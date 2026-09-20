'use strict';
// Public project URL/key. RLS, not secrecy of this key, protects each user's rows.
const cloud = window.supabase.createClient('https://kdzctulwnqzofuxhnbll.supabase.co','sb_publishable_QhHNMH_4AoCaWNOo5D3eog_hma6tvZv');
const nativeFetch=window.fetch.bind(window);
let readyResolve;
const userReady=new Promise(resolve=>{readyResolve=resolve;});
function showSession(session){
  document.body.classList.toggle('signed-in',!!session);
  if(session) readyResolve();
}
cloud.auth.getSession().then(({data,error})=>{if(error)document.getElementById('auth-msg').textContent=error.message;showSession(data.session);});
cloud.auth.onAuthStateChange((event,session)=>{showSession(session);if(event==='SIGNED_OUT')location.reload();});
const localToday = new Date();
const todayText = `${localToday.getFullYear()}-${String(localToday.getMonth()+1).padStart(2,'0')}-${String(localToday.getDate()).padStart(2,'0')}`;
document.body.dataset.today=todayText;
document.getElementById('month').value=todayText.slice(0,7);
async function login(signup){
  const form=document.getElementById('login-form');if(!form.reportValidity())return;
  const buttons=form.querySelectorAll('button');buttons.forEach(b=>b.disabled=true);
  const credentials={email:form.elements.email.value.trim(),password:form.elements.password.value};
  try{
    const {data,error}=signup?await cloud.auth.signUp(credentials):await cloud.auth.signInWithPassword(credentials);
    if(error)throw error;
    document.getElementById('auth-msg').textContent=signup&&!data.session?'Check your email to confirm your account, then return here to sign in.':'';
  }catch(error){document.getElementById('auth-msg').textContent=error.message;}
  finally{buttons.forEach(b=>b.disabled=false);}
}
document.getElementById('login-form').addEventListener('submit',e=>{e.preventDefault();login(false);});
document.getElementById('sign-up').addEventListener('click',()=>login(true));
document.getElementById('sign-out').addEventListener('click',async()=>{await cloud.auth.signOut();});
const cloudCategories=['Food & drinks','Transport','Study','Shopping','Rent & bills','Entertainment','Other'];
function paise(value){const s=String(value);if(!/^\d+(\.\d{1,2})?$/.test(s))throw Error('Enter an amount with up to two decimal places.');const [whole,frac='']=s.split('.');const n=Number(whole)*100+Number(frac.padEnd(2,'0'));if(!Number.isSafeInteger(n)||n<1||n>1000000000)throw Error('Invalid amount.');return n;}
window.fetch=async function(input,options={}){
  const url=new URL(typeof input==='string'?input:input.url,location.origin);
  if(url.origin!==location.origin||!url.pathname.startsWith('/api/'))return nativeFetch(input,options);
  await userReady;
  try{
    const {data:{session}}=await cloud.auth.getSession();if(!session)throw Error('Please sign in again.');
    const method=options.method||'GET',body=options.body?JSON.parse(options.body):{},user=session.user.id;
    const respond=(data,status=200)=>new Response(JSON.stringify(data),{status,headers:{'Content-Type':'application/json'}});
    if(url.pathname==='/api/dashboard'){
      const month=url.searchParams.get('month');if(!/^\d{4}-(0[1-9]|1[0-2])$/.test(month))throw Error('Choose a valid month.');
      const [y,m]=month.split('-').map(Number),days=new Date(y,m,0).getDate();let rows=[],offset=0;
      while(true){const {data,error}=await cloud.from('expenses').select('id,title,amount,category,spent_on,notes').gte('spent_on',month+'-01').lte('spent_on',month+'-'+days).order('spent_on',{ascending:false}).order('id',{ascending:false}).range(offset,offset+999);if(error)throw error;rows.push(...data);if(data.length<1000)break;offset+=1000;}
      const {data:budget,error}=await cloud.from('budgets').select('amount').eq('month',month).maybeSingle();if(error)throw error;
      const daily=Array(days).fill(0),categories=Object.fromEntries(cloudCategories.map(c=>[c,0]));
      rows.forEach(r=>{daily[Number(r.spent_on.slice(-2))-1]+=r.amount;categories[r.category]+=r.amount;});
      return respond({month,expenses:rows,daily,categories,total:daily.reduce((a,b)=>a+b,0),budget:budget?.amount??null});
    }
    if(url.pathname==='/api/budget'&&method==='PUT'){
      const {error}=await cloud.from('budgets').upsert({user_id:user,month:body.month,amount:paise(body.amount)},{onConflict:'user_id,month'});if(error)throw error;return respond({ok:true});
    }
    const match=url.pathname.match(/^\/api\/expenses\/(\d+)$/);
    if(match&&method==='DELETE'){const {data,error}=await cloud.from('expenses').delete().eq('id',match[1]).select('id');if(error)throw error;if(!data.length)throw Error('Expense not found.');return respond({ok:true});}
    if((match&&method==='PUT')||(url.pathname==='/api/expenses'&&method==='POST')){
      const row={title:body.title.trim(),amount:paise(body.amount),category:body.category,spent_on:body.spent_on,notes:(body.notes||'').trim(),user_id:user};
      const query=match?cloud.from('expenses').update(row).eq('id',match[1]):cloud.from('expenses').insert(row);
      const {data,error}=await query.select('id').single();if(error)throw error;return respond({id:data.id},match?200:201);
    }
    return respond({error:'Not found.'},404);
  }catch(error){return new Response(JSON.stringify({error:error.message||'Unable to save. Please retry.'}),{status:400,headers:{'Content-Type':'application/json'}});}
};
