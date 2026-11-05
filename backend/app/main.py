import logging
import os
import threading
from contextlib import asynccontextmanager
from collections import Counter, defaultdict
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query as Param, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from . import database as db
from .config import API_KEY,CORS_ORIGINS,MAX_UPLOAD,LLM_KEY,LLM_MODEL,SERVERLESS
from .schemas import Product, Query, Compare, Settings
from .services.seed import seed
from .services.ingestion import ingest, sync_product_source
from .graphrag.engine import RetrievalEngine
from .agents.workflow import AgentWorkflow, AGENTS
from .evaluation.runner import benchmark
from .services import auth
from starlette.concurrency import run_in_threadpool

log=logging.getLogger('productgraph')
logging.basicConfig(level=logging.INFO)
engine=None; workflow=None
mutation_lock=threading.RLock()
index_revision=None

@asynccontextmanager
async def lifespan(app):
    global engine,workflow
    global index_revision
    with db.exclusive():
        seed()
        # Authentication and relational reads do not need retrieval indexes.
        if not SERVERLESS:
            engine=RetrievalEngine(); workflow=AgentWorkflow(engine)
        index_revision=db.get('system','index_revision')
    yield
    if engine and engine.neo: engine.neo.close()

def needs_index(path,method):
    return (
        path.startswith('/api/graph/')
        or path in ['/api/system/status','/api/settings','/api/analytics/overview',
                    '/api/graphrag/query','/api/graphrag/search','/api/agents/execute','/api/evaluation/run']
        or (method in ['POST','PUT','DELETE'] and path.startswith(('/api/products','/api/documents')))
    )

def consistent_index(request:Request):
    global index_revision,engine,workflow
    index_required=needs_index(request.url.path,request.method)
    mutation=request.method in ['POST','PUT','DELETE']
    if not SERVERLESS or (not index_required and not mutation):
        yield
        return
    with db.exclusive():
        if index_required:
            revision=db.get('system','index_revision')
            with mutation_lock:
                if engine is None:
                    engine=RetrievalEngine(); workflow=AgentWorkflow(engine)
                elif revision!=index_revision:
                    engine.rebuild()
            index_revision=revision
        try:
            yield
        finally:
            if request.method in ['POST','PUT','DELETE'] and request.url.path.startswith(('/api/products','/api/documents','/api/graph/build')):
                import uuid
                index_revision={'value':uuid.uuid4().hex}
                db.put('system','index_revision',index_revision)

app=FastAPI(title='ProductGraph Intelligence',version='1.0.0',lifespan=lifespan,dependencies=[Depends(consistent_index)],description='Explainable retrieval over explicitly synthetic samples and user-provided sources.')
app.add_middleware(CORSMiddleware,allow_origins=CORS_ORIGINS,allow_methods=['GET','POST','PUT','DELETE'],allow_headers=['Content-Type','X-API-Key'])

@app.middleware('http')
async def guard(request:Request,call_next):
    public=request.url.path in ['/api/health','/api/auth/status','/api/auth/me','/api/auth/login','/api/auth/setup','/api/auth/logout']
    if request.method not in ['GET','HEAD','OPTIONS']:
        origin=request.headers.get('origin')
        if origin:
            from urllib.parse import urlsplit
            host=request.headers.get('x-forwarded-host') or request.headers.get('host')
            if urlsplit(origin).netloc!=host and origin not in CORS_ORIGINS:
                return JSONResponse({'detail':'Request origin is not allowed'},status_code=403)
    if auth.required() and request.url.path.startswith('/api/') and not public:
        user=await run_in_threadpool(auth.current_user,request)
        if not user: return JSONResponse({'detail':'Sign in to access this workspace'},status_code=401)
        request.state.user=user
    if API_KEY and request.url.path.startswith('/api/') and request.url.path!='/api/health' and request.headers.get('X-API-Key')!=API_KEY:
        return JSONResponse({'detail':'API key required'},status_code=401)
    try: return await call_next(request)
    except Exception:
        log.exception('Unhandled API error: %s %s',request.method,request.url.path)
        return JSONResponse({'detail':'Internal error. Check server logs.'},status_code=500)

def require(kind,id):
    item=db.get(kind,id)
    if not item: raise HTTPException(404,f'{kind} not found')
    return item

def page(rows,offset=0,limit=20): return {'items':rows[offset:offset+limit],'total':len(rows),'offset':offset,'limit':limit}

app.include_router(auth.router)

@app.get('/api/health')
def health(): return {'status':'ok','service':'ProductGraph Intelligence'}

@app.get('/api/system/status')
def status():
    return {'graph':engine.graph_backend,'vector':engine.vector_backend,'embedding_provider':engine.embedding_provider,'embedding_model':engine.embedding_name,'llm':{'configured':bool(LLM_KEY),'model':LLM_MODEL if LLM_KEY else None,'mode':'LLM-assisted claim selection' if LLM_KEY else 'deterministic evidence rendering'},'orchestrator':'LangGraph StateGraph','database':'PostgreSQL' if db.DATABASE_URL.startswith('postgres') else 'SQLite','warnings':list(dict.fromkeys(engine.warnings))[-5:],'authentication':'API key enabled' if API_KEY else 'local development; authentication disabled'}

@app.get('/api/products')
def products(q:str='',domain:str='',brand:str='',offset:int=Param(0,ge=0),limit:int=Param(20,ge=1,le=100)):
    rows=[p for p in db.all_records('product') if q.lower() in (p['name']+' '+p['description']+' '+p['id']).lower() and (not domain or p['domain']==domain) and (not brand or p['brand_id']==brand)]
    return page(rows,offset,limit)

@app.post('/api/products/compare')
def compare(request:Compare):
    items=[require('product',id) for id in dict.fromkeys(request.product_ids)]
    if len(items)<2: raise HTTPException(422,'Choose at least two distinct products')
    fields=sorted({k for p in items for k in p['specifications']})
    return {'products':items,'fields':fields,'similarities':[k for k in fields if len({str(p['specifications'].get(k)) for p in items})==1],'differences':[k for k in fields if len({str(p['specifications'].get(k)) for p in items})>1],'evidence':[{'product_id':p['id'],'document_id':'SRC-'+p['id'],'chunk_id':'SRC-'+p['id']+'-1','source_available':bool(db.get('document','SRC-'+p['id']))} for p in items]}

@app.get('/api/products/{product_id}')
def product(product_id:str): return require('product',product_id)

@app.post('/api/products',status_code=201)
def create_product(p:Product):
    with mutation_lock,engine.lock:
        if db.get('product',p.id): raise HTTPException(409,'Product ID already exists')
        value=p.model_dump(); db.put('product',p.id,value); sync_product_source(value); engine.rebuild(); return value

@app.put('/api/products/{product_id}')
def update_product(product_id:str,p:Product):
    with mutation_lock,engine.lock:
        require('product',product_id)
        if product_id!=p.id: raise HTTPException(422,'Product ID cannot change')
        value=p.model_dump(); db.put('product',p.id,value); sync_product_source(value); engine.rebuild(); return value

@app.delete('/api/products/{product_id}')
def delete_product(product_id:str):
    with mutation_lock,engine.lock:
        require('product',product_id); db.delete('product',product_id); db.delete('document','SRC-'+product_id)
        for d in db.all_records('document'):
            if product_id in d['product_ids']:
                d['product_ids'].remove(product_id); db.put('document',d['id'],d)
        engine.rebuild(); return {'deleted':product_id}

@app.post('/api/documents/upload',status_code=201)
def upload(file:UploadFile=File(...),synthetic:bool=Form(False)):
    content=file.file.read(MAX_UPLOAD+1)
    if len(content)>MAX_UPLOAD: raise HTTPException(413,'Upload limit is 10 MB')
    if not content: raise HTTPException(422,'File is empty')
    from .services.ingestion import ALLOWED
    if Path(file.filename or '').suffix.lower() not in ALLOWED: raise HTTPException(415,'Unsupported format')
    with mutation_lock,engine.lock:
        result=ingest(file.filename or 'upload.txt',content,synthetic)
        if result['status']=='ready': engine.rebuild()
        return result

@app.get('/api/documents')
def documents(offset:int=Param(0,ge=0),limit:int=Param(25,ge=1,le=100),origin:str=''):
    rows=[{k:v for k,v in d.items() if k not in ['pages','chunks']} for d in db.all_records('document') if not origin or d.get('origin')==origin]
    return page(rows[::-1],offset,limit)

@app.get('/api/documents/{document_id}')
def document(document_id:str): return require('document',document_id)

@app.delete('/api/documents/{document_id}')
def delete_document(document_id:str):
    with mutation_lock,engine.lock:
        require('document',document_id); db.delete('document',document_id); engine.rebuild(); return {'deleted':document_id}

@app.post('/api/documents/{document_id}/process')
def reprocess(document_id:str):
    with mutation_lock,engine.lock:
        d=require('document',document_id)
        if not d['pages']: raise HTTPException(422,'No parsed text available. Upload a corrected source file.')
        d['chunks']=[]
        for p in d['pages']:
            for offset in range(0,len(p['text']),900): d['chunks'].append({'id':f'{document_id}-p{p["page"]}-c{offset//900+1}','text':p['text'][offset:offset+1100],'page':p['page']})
        d['status']='ready'; d['error']=None; db.put('document',document_id,d); engine.rebuild(); return d

@app.get('/api/graph/statistics')
def graph_statistics(): return {'backend':engine.graph_backend,'nodes':engine.graph.number_of_nodes(),'relationships':engine.graph.number_of_edges(),'node_types':dict(Counter(a['type'] for _,a in engine.graph.nodes(data=True))),'relationship_types':dict(Counter(a['type'] for _,_,a in engine.graph.edges(data=True)))}

@app.get('/api/graph/nodes')
def graph_nodes(product_id:str|None=None,limit:int=Param(80,ge=1,le=200)): return engine.graph_view(product_id,limit)

@app.get('/api/graph/relationships')
def graph_relationships(product_id:str|None=None,limit:int=Param(80,ge=1,le=200)): return engine.graph_view(product_id,limit)['edges']

@app.get('/api/graph/product/{product_id}')
def product_graph(product_id:str):
    require('product',product_id); return engine.graph_view(product_id,200)

@app.post('/api/graph/build')
def graph_build():
    with mutation_lock: engine.rebuild()
    return graph_statistics()

@app.post('/api/graphrag/query')
@app.post('/api/agents/execute')
def query(request:Query):
    q=request.query
    if request.category: q+=' '+request.category
    with mutation_lock: return workflow.execute(q,request.top_k,request.method)

@app.post('/api/graphrag/search')
def search(request:Query):
    with mutation_lock: result=workflow.execute(request.query,request.top_k,request.method)
    return {k:result[k] for k in ['id','evidence','interpreted','latency_ms']}

@app.get('/api/graphrag/history')
def history(offset:int=Param(0,ge=0),limit:int=Param(20,ge=1,le=100)):
    return page([{k:q[k] for k in ['id','query','created_at','latency_ms','validation','method']} for q in db.all_records('query')][::-1],offset,limit)

@app.get('/api/agents/status')
def agent_status():
    queries=db.all_records('query'); traces=[t for q in queries for t in q['traces']]
    return [{'name':name,'status':'completed' if any(t['agent']==name for t in traces) else 'idle','executions':sum(t['agent']==name for t in traces),'average_ms':round(sum(t['duration_ms'] for t in traces if t['agent']==name)/max(sum(t['agent']==name for t in traces),1),2)} for name in AGENTS]

@app.get('/api/agents/traces/{trace_id}')
def traces(trace_id:str): return require('query',trace_id)

@app.post('/api/explainability/explain')
def explain(payload:dict):
    if not isinstance(payload.get('query_id'),str): raise HTTPException(422,'query_id is required')
    return require('query',payload['query_id'])

@app.get('/api/explainability/evidence/{query_id}')
def evidence(query_id:str): return require('query',query_id)

@app.post('/api/evaluation/run')
def evaluation_run():
    with mutation_lock: return benchmark(workflow)

@app.get('/api/evaluation/results')
def evaluation_results(): return db.all_records('evaluation')[::-1]

@app.get('/api/evaluation/metrics')
def evaluation_metrics():
    results=db.all_records('evaluation'); return results[-1] if results else {'metrics':[],'status':'not_run'}

@app.get('/api/analytics/overview')
def overview():
    queries=db.all_records('query'); docs=db.all_records('document'); products=db.all_records('product')
    avg=lambda key:round(sum(q[key] for q in queries)/len(queries),2) if queries else None
    days=defaultdict(int)
    for q in queries: days[q['created_at'][:10]]+=1
    trace_rows=[t for q in queries for t in q['traces']]+db.all_records('agent_error')
    return {'products':len(products),'documents':len(docs),'graph_nodes':engine.graph.number_of_nodes(),'graph_relationships':engine.graph.number_of_edges(),'queries':len(queries),'average_retrieval_ms':avg('retrieval_ms'),'average_response_ms':avg('latency_ms'),'agent_success_rate':sum(t['status']=='success' for t in trace_rows)/len(trace_rows) if trace_rows else None,'evidence_coverage':sum(q['validation']['evidence_coverage'] for q in queries)/len(queries) if queries else None,'categories':[{'name':name,'count':count} for name,count in Counter(p['domain'] for p in products).items()],'activity':[{'date':day,'queries':count} for day,count in sorted(days.items())],'synthetic_products':sum(p['synthetic'] for p in products)}

@app.get('/api/analytics/retrieval')
def retrieval_analytics():
    queries=db.all_records('query')
    return {'methods':[{'name':name,'count':n} for name,n in Counter(q['method'] for q in queries).items()],'quality':[{'name':q['id'][:6],'coverage':q['validation']['evidence_coverage'],'latency_ms':q['latency_ms']} for q in queries[-20:]]}

@app.get('/api/analytics/agents')
def agents_analytics(): return agent_status()

@app.get('/api/settings')
def settings(): return {'retrieval':workflow.settings(),'system':status(),'secret_management':'Set API keys in server environment variables. Keys are never returned to the browser.'}

@app.put('/api/settings')
def update_settings(s:Settings): return db.put('settings','retrieval',s.model_dump())
