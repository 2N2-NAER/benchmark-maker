import json
import tempfile
import unittest
from pathlib import Path
from benchmark_maker.pipeline import *
from benchmark_maker.mcp import handle

class FakeAI:
    model='test-fixture'
    calls=0
    def ask(self, instruction, payload):
        self.calls+=1
        if 'tasks' in instruction:
            return {'summary':'流体','tasks':[{'id':'T1','name':'精华液滴落','ability':'连续性','domain':'电商','mode':'首尾帧','queries':['精华液','serum drop'],'count':1}]}
        return {'cases':[case()]}

def case():
    return {'id':'C1','task_id':'T1','domain':'电商','mode':'首尾帧','duration':8,'aspect':'16:9','prompt':'{pic-01} 为首帧，{pic-02} 为尾帧。精华液自然滴落。','bindings':[{'asset_id':'first','ref':'pic-01','purpose':'首帧'},{'asset_id':'last','ref':'pic-02','purpose':'尾帧'}],'checkpoints':['液滴沿重力方向连续下落']}

def assets():
    return [{'id':ident,'role':role,'caption':'精华液 serum drop','url':'https://example.com/'+ident+'.jpg','groupId':'G','domain':'电商','verified':False} for ident,role in [('first','首帧'),('last','尾帧')]]

class PipelineTests(unittest.TestCase):
    def test_ai_pipeline_resume_and_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp); (p/'problem.md').write_text('流体：精华液突然消失',encoding='utf-8'); write_json(p/'assets.json',assets()); ai=FakeAI()
            result=run(p/'problem.md',p/'assets.json',p/'out',1,['电商'],ai)
            self.assertEqual(result['cases'],1);self.assertEqual(result['blocked'],0);self.assertEqual(ai.calls,2)
            self.assertIn('https://example.com/first.jpg',(p/'out/benchmark.csv').read_text(encoding='utf-8-sig'))
            self.assertFalse(read_json(p/'out/validation.json')['media_urls_checked'])
            self.assertTrue(read_json(p/'out/validation.json')['cases'][0]['warnings'])
            run(p/'problem.md',p/'assets.json',p/'out',1,['电商'],ai,resume=True);self.assertEqual(ai.calls,2)
            with self.assertRaises(ValueError):run(p/'problem.md',p/'assets.json',p/'out',2,['电商'],ai,resume=True)
    def test_missing_media_and_hallucination(self):
        plan=FakeAI().ask(PLAN_PROMPT,{})
        self.assertTrue(validate_cases([case()],plan,[])['blocked'])
        a=assets();a[1]['groupId']='other';self.assertTrue(validate_cases([case()],plan,a)['blocked'])
        c=case();c['prompt']+=' {pic-99}';self.assertTrue(validate_cases([c],plan,assets())['blocked'])
        report=validate_cases([case(),case()],plan,assets());self.assertTrue(report['global_errors']);self.assertTrue(report['blocked'])
    def test_retrieval_english_and_role_coverage(self):
        plan=FakeAI().ask(PLAN_PROMPT,{})
        self.assertEqual(len(retrieve(plan,assets())['results'][0]['hits']),2)
        unrelated=[{**assets()[0],'caption':'a red chair','tags':[]}]
        self.assertEqual(retrieve(plan,unrelated)['results'][0]['hits'],[])
    def test_mcp(self):
        response=handle({'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2024-11-05'}})
        self.assertIn('instructions',response['result'])
        self.assertEqual(len(handle({'id':2,'method':'tools/list'})['result']['tools']),3)
        response=handle({'id':3,'method':'tools/call','params':{'name':'read_problem_document','arguments':{'path':'missing-file'}}})
        self.assertTrue(response['result']['isError'])
    def test_catalog_rejects_duplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'a.json';write_json(p,[assets()[0],assets()[0]])
            with self.assertRaises(ValueError):load_assets(p)

if __name__=='__main__':unittest.main()

class TransportTests(unittest.TestCase):
    def test_real_http_transport_with_mock_model(self):
        from http.server import BaseHTTPRequestHandler, HTTPServer
        from threading import Thread
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                payload=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                self.server.requests.append(payload)
                result=FakeAI().ask(PLAN_PROMPT if len(self.server.requests)==1 else CASE_PROMPT,{})
                body=json.dumps({'choices':[{'message':{'content':json.dumps(result,ensure_ascii=False)}}]}).encode()
                self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(body)
            def log_message(self,*args):pass
        server=HTTPServer(('127.0.0.1',0),Handler);server.requests=[]
        worker=Thread(target=server.serve_forever,daemon=True);worker.start()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp);(p/'problem.md').write_text('精华液流体问题',encoding='utf-8');write_json(p/'assets.json',assets())
                client=LLM(endpoint=f'http://127.0.0.1:{server.server_port}/v1/chat/completions',model='mock-model',api_key='test-only')
                result=run(p/'problem.md',p/'assets.json',p/'out',1,['电商'],client)
                self.assertEqual(result['cases'],1);self.assertEqual(len(server.requests),2)
                self.assertNotIn('test-only',(p/'out/manifest.json').read_text())
        finally:server.shutdown();server.server_close();worker.join()
    def test_stdio_subprocess(self):
        import subprocess
        request='\n'.join(json.dumps(m) for m in [{'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2024-11-05'}},{'jsonrpc':'2.0','method':'notifications/initialized'},{'jsonrpc':'2.0','id':2,'method':'tools/list'}])+'\n'
        r=subprocess.run(['python3','run_mcp.py'],input=request,text=True,capture_output=True,check=True)
        messages=[json.loads(line) for line in r.stdout.splitlines()]
        self.assertEqual(len(messages),2);self.assertEqual(len(messages[1]['result']['tools']),3)
