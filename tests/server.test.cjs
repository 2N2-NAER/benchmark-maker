const {test}=require('node:test');const assert=require('node:assert/strict');
test('standalone server serves app and health without exposing source',async()=>{
 const {createServer}=await import('../server.mjs');const s=createServer();await new Promise(r=>s.listen(0,'127.0.0.1',r));let base='http://127.0.0.1:'+s.address().port;
 try{assert.equal((await fetch(base+'/healthz')).status,200);assert((await (await fetch(base+'/')).text()).includes('Benchmark Foundry'));assert.equal((await fetch(base+'/core.js')).headers.get('content-type'),'text/javascript; charset=utf-8');assert.equal((await fetch(base+'/package.json')).status,404);assert.equal((await fetch(base+'/.git/config')).status,403);assert.equal((await fetch(base+'/',{method:'POST'})).status,405);}finally{await new Promise(r=>s.close(r))}
});
