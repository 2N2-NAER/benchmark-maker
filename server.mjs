import http from 'node:http';
import {readFile,stat} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const root=fileURLToPath(new URL('./public/',import.meta.url));
const port=Number(process.env.PORT||4173),host=process.env.HOST||'0.0.0.0';
const types={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json; charset=utf-8'};
export function createServer(){return http.createServer(async(req,res)=>{
  const headers={'X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','Cache-Control':'no-store'};
  if(!['GET','HEAD'].includes(req.method)){res.writeHead(405,{...headers,Allow:'GET, HEAD'});return res.end('Method not allowed');}
  try{
    const pathname=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
    if(pathname==='/healthz'){res.writeHead(200,{...headers,'Content-Type':'application/json'});return res.end(req.method==='HEAD'?undefined:JSON.stringify({status:'ok',version:'1.0.0'}));}
    const name=pathname==='/'?'index.html':pathname.slice(1);
    const target=path.resolve(root,name);
    if(!target.startsWith(root)||name.split('/').some(p=>p.startsWith('.'))){res.writeHead(403,headers);return res.end('Forbidden');}
    const info=await stat(target);if(!info.isFile())throw Object.assign(Error('Not found'),{code:'ENOENT'});
    const data=await readFile(target);res.writeHead(200,{...headers,'Content-Type':types[path.extname(target)]||'application/octet-stream','Content-Length':data.length});res.end(req.method==='HEAD'?undefined:data);
  }catch(error){let status=error instanceof URIError?400:error.code==='ENOENT'?404:500;res.writeHead(status,headers);res.end(status===404?'Not found':status===400?'Bad request':'Internal server error');}
})}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  const server=createServer();server.listen(port,host,()=>console.log(`Benchmark Foundry listening on http://${host}:${port}`));
  for(const signal of ['SIGINT','SIGTERM'])process.on(signal,()=>server.close(()=>process.exit(0)));
}
