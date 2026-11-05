import io
import json
import os
import tempfile
from pathlib import Path
os.environ.pop('NEO4J_URI',None)
os.environ.pop('OPENAI_API_KEY',None)
os.environ['EMBEDDING_PROVIDER']='hash'
os.environ['PG_REQUIRE_AUTH']='0'
from fastapi.testclient import TestClient
from app.main import app
import pytest

@pytest.fixture(scope='module')
def client():
    with TestClient(app) as c: yield c

def test_seed_integrity(client):
    from app import database as db
    products=db.all_records('product'); brands=db.all_records('brand'); categories=db.all_records('category')
    assert len(products)==500 and len(brands)==50 and len(categories)==100
    assert len(db.all_records('faq'))==100
    assert len([d for d in db.all_records('document') if d['origin']=='sample manual'])==50
    assert sum(len(p['specifications']) for p in products)>=1000
    assert all(p['brand_id'] in {b['id'] for b in brands} and p['category_id'] in {c['id'] for c in categories} for p in products)
    assert all(p['synthetic'] for p in products)

def test_requirements_citations_and_agents(client):
    r=client.post('/api/graphrag/query',json={'query':'Find laptops suitable for machine learning with 16GB RAM and SSD'}); assert r.status_code==200,r.text
    result=r.json(); assert result['validation']['passed'],result['validation']
    assert result['validation']['evidence_coverage']==1
    assert len(set(t['agent'] for t in result['traces']))==10
    from app.agents.workflow import AGENTS
    assert set(t['agent'] for t in result['traces'])==set(AGENTS)
    assert result['attempts']==1
    from app.main import engine
    raw_vectors=engine.vector_search(result['interpreted']['normalized_query'])
    max_vector=max(raw_vectors.values())
    evidence={e['id']:e for e in result['evidence']}
    for claim in result['claims']:
        assert all(id in evidence for id in claim['evidence_ids'])
    for e in result['evidence']:
        assert sum(e['contributions'].values())==pytest.approx(e['hybrid_score'])
        assert e['scores']['vector']==pytest.approx(raw_vectors[e['id']]/max_vector)
        for p in e['products']:
            assert p['domain']=='Laptops' and p['specifications']['ram_gb']>=16 and p['specifications']['gpu_vram_gb']>=8
    trace=client.get('/api/agents/traces/'+result['id']).json()
    assert trace['id']==result['id']

def test_abstention_and_bounded_retry(client):
    r=client.post('/api/graphrag/query',json={'query':'zzzzquuxxyy nonsensicalquerynotpresent'}).json()
    assert r['validation']['abstained'] and not r['evidence']
    assert r['attempts']==2 and 'No supporting information' in r['answer']

def test_settings_validation(client):
    assert client.put('/api/settings',json={'vector_weight':1,'graph_weight':1}).status_code==422
    assert client.post('/api/graphrag/query',json={'query':'a','top_k':100}).status_code==422
    assert client.get('/api/products?offset=-1').status_code==422
    assert client.get('/api/products/nonexistent').status_code==404

def test_upload_duplicate_preview_delete(client):
    content=b'User supplied field note on P0001. ram_gb: 16. Follow document evidence.'
    r=client.post('/api/documents/upload',files={'file':('field.txt',content,'text/plain')}).json()
    assert r['status']=='ready' and 'P0001' in r['product_ids'] and not r['synthetic']
    again=client.post('/api/documents/upload',files={'file':('same.txt',content,'text/plain')}).json()
    assert again['duplicate'] and again['id']==r['id']
    assert client.get('/api/documents/'+r['id']).json()['chunks'][0]['page']==1
    assert client.post('/api/documents/'+r['id']+'/process').status_code==200
    assert client.delete('/api/documents/'+r['id']).status_code==200
    assert client.get('/api/documents/'+r['id']).status_code==404

def test_invalid_formats_and_parsing(client):
    assert client.post('/api/documents/upload',files={'file':('run.exe',b'no')}).status_code==415
    assert client.post('/api/documents/upload',files={'file':('data.json',b'{broken')}).json()['status']=='error'
    assert client.post('/api/documents/upload',files={'file':('empty.txt',b'')}).status_code==422

def test_pdf_docx_parsers():
    from app.services.ingestion import parse
    import fitz
    pdf=fitz.open(); p=pdf.new_page(); p.insert_text((72,72),'P0001 source on page one')
    p=pdf.new_page(); p.insert_text((72,72),'source on page two')
    pages,_=parse('source.pdf',pdf.tobytes()); assert len(pages)==2 and pages[1]['page']==2
    from docx import Document
    doc=Document(); doc.add_paragraph('Example DOCX text'); buf=io.BytesIO(); doc.save(buf)
    pages,_=parse('source.docx',buf.getvalue()); assert pages[0]['page']==0 and 'Example DOCX' in pages[0]['text']

def test_product_crud_index_and_comparison(client):
    p=client.get('/api/products/P0001').json(); p.update(id='CUSTOM1',name='Unique Nebula Device',synthetic=False)
    assert client.post('/api/products',json=p).status_code==201
    assert client.post('/api/products',json=p).status_code==409
    p['specifications']['ram_gb']=128
    assert client.put('/api/products/CUSTOM1',json=p).status_code==200
    result=client.post('/api/graphrag/query',json={'query':'CUSTOM1 Unique Nebula Device'}).json()
    assert any(e['product_ids']==['CUSTOM1'] for e in result['evidence'])
    c=client.post('/api/products/compare',json={'product_ids':['CUSTOM1','P0001']}).json()
    assert 'ram_gb' in c['differences'] and all(e['source_available'] for e in c['evidence'])
    assert client.delete('/api/products/CUSTOM1').status_code==200
    assert client.get('/api/graph/product/CUSTOM1').status_code==404

def test_graph_paths_and_fallback(client):
    result=client.get('/api/graph/product/P0001').json()
    assert result['backend']=='NetworkX fallback'
    ids={n['id'] for n in result['nodes']}
    assert all(e['source'] in ids and e['target'] in ids for e in result['edges'])
    assert any(e['type']=='MANUFACTURED_BY' for e in result['edges'])
    assert 'hashing' in client.get('/api/system/status').json()['embedding_model']

def test_evaluation_computes_real_metrics(client):
    r=client.post('/api/evaluation/run'); assert r.status_code==200,r.text
    data=r.json(); assert len(data['cases'])==20 and len(data['metrics'])==4
    assert data['ragas']['status']=='not_run'
    assert all(0<=m['precision_at_k']<=1 and 0<=m['recall_at_k']<=1 for m in data['metrics'])
    assert all(m['faithfulness'] is None for m in data['metrics'])
    assert all(len(c['retrieved_ids'])>0 for c in data['cases'])
    assert client.get('/api/evaluation/results').json()[0]['id']==data['id']

def test_conflicting_uploaded_specification_is_flagged(client):
    content=b'P0001 field report. ram_gb: 999. This conflicts with the canonical product record.'
    d=client.post('/api/documents/upload',files={'file':('conflict.txt',content,'text/plain')}).json()
    result=client.post('/api/graphrag/query',json={'query':'P0001 specifications'}).json()
    assert not result['validation']['passed'] and result['validation']['contradictions']
    assert result['attempts']==1
    client.delete('/api/documents/'+d['id'])

def test_api_key_guard(client,monkeypatch):
    import app.main as main
    monkeypatch.setattr(main,'API_KEY','test-session-key')
    assert client.get('/api/health').status_code==200
    assert client.get('/api/system/status').status_code==401
    assert client.get('/api/system/status',headers={'X-API-Key':'test-session-key'}).status_code==200

def test_headphones_do_not_resolve_as_smartphones():
    from app.graphrag.engine import understand
    assert understand('Find headphones with 24 hours battery')['category']=='Headphones'
    assert understand('Find smartphones with 12GB RAM')['category']=='Smartphones'
