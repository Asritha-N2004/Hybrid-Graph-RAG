import time
import uuid
from .. import database as db
from ..graphrag.engine import meets

def benchmark(workflow):
    """Deterministic specification-based ground truth, independent of retriever output."""
    cases=[{'query':'Find laptops with 16GB RAM and SSD','domain':'Laptops','requirements':{'ram_gb':16,'storage_type':'SSD'}}, {'query':'Find laptops suitable for machine learning with 32GB RAM','domain':'Laptops','requirements':{'ram_gb':32,'gpu_vram_gb':8}}, {'query':'Find smartphones with 12GB RAM','domain':'Smartphones','requirements':{'ram_gb':12}}, {'query':'Find headphones with 24 hours battery','domain':'Headphones','requirements':{'battery_hours':24}}, {'query':'Find laptops under $1000 with 16GB RAM','domain':'Laptops','requirements':{'max_price':1000,'ram_gb':16}}]
    rows=[]; k=5
    for method in ['keyword','vector','graph','hybrid']:
        for case in cases:
            relevant={p['id'] for p in workflow.engine.products.values() if p['domain']==case['domain'] and meets(p,case['requirements'])[0]}
            start=time.perf_counter(); result=workflow.execute(case['query'],k,method,persist=False)
            retrieved=list(dict.fromkeys(pid for e in result['evidence'] for pid in e['product_ids']))[:k]
            hits=[pid in relevant for pid in retrieved]; count=sum(hits)
            rr=next((1/(i+1) for i,hit in enumerate(hits) if hit),0)
            rows.append({'method':method,'query':case['query'],'k':k,'precision_at_k':count/k,'recall_at_k':count/len(relevant) if relevant else 0,'mrr':rr,'context_precision':count/len(retrieved) if retrieved else 0,'context_recall':count/len(relevant) if relevant else 0,'evidence_coverage':result['validation']['evidence_coverage'],'retrieval_ms':result['retrieval_ms'],'response_ms':round((time.perf_counter()-start)*1000,2),'relevant_count':len(relevant),'retrieved_ids':retrieved})
    metrics=[]
    for method in ['keyword','vector','graph','hybrid']:
        subset=[r for r in rows if r['method']==method]
        avg=lambda key:sum(r[key] for r in subset)/len(subset)
        metrics.append({'method':method,**{key:round(avg(key),4) for key in ['precision_at_k','recall_at_k','mrr','context_precision','context_recall','evidence_coverage','retrieval_ms','response_ms']},'faithfulness':None,'answer_relevance':None})
    result={'id':uuid.uuid4().hex,'created_at':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),'metrics':metrics,'cases':rows,'protocol':'Five deterministic synthetic constraint queries. Ground truth is all products meeting structured requirements. Macro average over queries; distinct product ranking. Recall denominator includes all relevant products, not only top K. Context metrics use product-level relevance, not RAGAS chunk judgments.','ragas':{'status':'not_run','reason':'LLM-judged faithfulness and answer relevance require a separately configured evaluator and human-reviewed reference answers; never substituted with heuristic scores.'}}
    db.put('evaluation',result['id'],result)
    return result
