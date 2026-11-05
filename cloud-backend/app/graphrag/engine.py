import math
import os
import re
import threading
from collections import Counter
import networkx as nx
import numpy as np
try:
    from sklearn.feature_extraction.text import HashingVectorizer
except ImportError:
    HashingVectorizer = None
from .. import database as db
from ..config import DATA

def tokens(text):
    return re.findall(r'[a-z0-9]+', text.lower())

def understand(query):
    q=query.lower(); requirements={}
    for pattern,key in [(r'(\d+)\s*gb\s*(?:of\s*)?(?:ram|memory)','ram_gb'),(r'(\d+)\s*gb\s*(?:ssd|storage)','storage_gb'),(r'(\d+)\s*(?:hours|hour)','battery_hours'),(r'(\d+)\s*gb\s*(?:vram|gpu)','gpu_vram_gb')]:
        match=re.search(pattern,q)
        if match: requirements[key]=int(match.group(1))
    if 'ssd' in q: requirements['storage_type']='SSD'
    if 'machine learning' in q: requirements['gpu_vram_gb']=max(requirements.get('gpu_vram_gb',0),8)
    budget=re.search(r'(?:under|below|less than|budget)\s*\$?\s*(\d+(?:\.\d+)?)',q)
    if budget: requirements['max_price']=float(budget.group(1))
    category=next((name for word,name in [('laptop','Laptops'),('headphone','Headphones'),('phone','Smartphones'),('appliance','Home Appliances'),('smart device','Smart Devices'),('accessor','Accessories'),('electronics','Electronics')] if word in q),None)
    ids=re.findall(r'\bP\d{4}\b',query.upper())
    return {'original_query':query,'normalized_query':' '.join(tokens(query)),'intent':'compare' if any(x in q for x in ['compare','versus',' vs ']) else 'recommend' if any(x in q for x in ['find','recommend','suitable']) else 'lookup','category':category,'entities':ids,'requirements':requirements,'inferences':['Machine learning suitability uses a disclosed heuristic: at least 8 GB GPU VRAM; no benchmark guarantee.'] if 'machine learning' in q else []}

def meets(product, requirements):
    missing=[]
    for key,expected in requirements.items():
        value=product.get('price') if key=='max_price' else product['specifications'].get(key)
        if value is None: missing.append(key); continue
        if isinstance(expected,(int,float)):
            try:
                if (float(value)>expected if key=='max_price' else float(value)<expected): return False,missing
            except (ValueError,TypeError): missing.append(key)
        elif str(value).lower()!=str(expected).lower(): return False,missing
    return not missing,missing

class RetrievalEngine:
    def __init__(self):
        self.lock=threading.RLock(); self.graph=nx.MultiDiGraph(); self.graph_backend='NetworkX fallback'
        self.vector_backend='NumPy cosine fallback'; self.embedding_provider=os.getenv('EMBEDDING_PROVIDER','hash')
        self.embedding_name=os.getenv('EMBEDDING_MODEL','sentence-transformers/all-MiniLM-L6-v2') if self.embedding_provider=='sentence-transformers' else os.getenv('API_EMBEDDING_MODEL','text-embedding-3-small') if self.embedding_provider=='api' else 'hashing-1024 (lexical; no learned semantics)'
        self.hasher=HashingVectorizer(n_features=1024,alternate_sign=False,norm='l2') if HashingVectorizer else None
        if self.embedding_provider=='hash' and not self.hasher:
            self.embedding_name='sha256-hashing-1024 (lexical; no learned semantics)'
        self.neo=None; self.collection=None; self.warnings=[]
        self.rebuild()

    def embed(self,texts):
        if self.embedding_provider=='sentence-transformers':
            from sentence_transformers import SentenceTransformer
            if not hasattr(self,'model'): self.model=SentenceTransformer(self.embedding_name)
            return np.asarray(self.model.encode(texts,normalize_embeddings=True),dtype=np.float32)
        if self.embedding_provider=='api':
            import httpx
            from ..config import LLM_KEY, LLM_URL
            with httpx.Client(timeout=60) as client:
                response=client.post(LLM_URL+'/embeddings',headers={'Authorization':'Bearer '+LLM_KEY},json={'model':self.embedding_name,'input':texts})
                response.raise_for_status()
                vectors=np.asarray([r['embedding'] for r in sorted(response.json()['data'],key=lambda x:x['index'])],dtype=np.float32)
                return vectors/np.maximum(np.linalg.norm(vectors,axis=1,keepdims=True),1e-12)
        if self.hasher:
            return self.hasher.transform(texts).toarray().astype(np.float32)
        import hashlib
        vectors=np.zeros((len(texts),1024),dtype=np.float32)
        for index,value in enumerate(texts):
            for token in tokens(value):
                bucket=int.from_bytes(hashlib.sha256(token.encode()).digest()[:4],'little')%1024
                vectors[index,bucket]+=1
        return vectors/np.maximum(np.linalg.norm(vectors,axis=1,keepdims=True),1e-12)

    def rebuild(self):
        with self.lock:
            self.products={p['id']:p for p in db.all_records('product')}
            self.documents={d['id']:d for d in db.all_records('document') if d['status']=='ready'}
            self.chunks=[]; self.graph.clear()
            for d in self.documents.values():
                self.graph.add_node(d['id'],type='Document',label=d['filename'])
                for c in d['chunks']:
                    self.chunks.append({**c,'document_id':d['id'],'filename':d['filename'],'synthetic':d['synthetic'],'product_ids':d['product_ids']})
            for p in self.products.values():
                self.graph.add_node(p['id'],type='Product',label=p['name'])
                def link(id,type,label,relation):
                    self.graph.add_node(id,type=type,label=str(label)); self.graph.add_edge(p['id'],id,type=relation)
                link(p['brand_id'],'Brand',p['brand'],'MANUFACTURED_BY'); link(p['category_id'],'Category',p['category'],'BELONGS_TO')
                for key,value in p['specifications'].items(): link(f'SPEC:{key}:{value}','Specification',f'{key}: {value}','HAS_SPECIFICATION')
                for f in p['features']: link('FEAT:'+f,'Feature',f,'HAS_FEATURE')
                for c in p.get('compatibility',[]): link('COMP:'+c,'Compatibility',c,'COMPATIBLE_WITH')
                if p.get('price') is not None: link('PRICE:'+p['id'],'Price',f'{p["price"]} {p["currency"]}','HAS_PRICE')
                for d in self.documents.values():
                    if p['id'] in d['product_ids']:
                        self.graph.add_edge(p['id'],d['id'],type='SUPPORTED_BY')
            # Similarity edges are explicit and reproducible, never invented by the answer model.
            groups={}
            for p in self.products.values(): groups.setdefault(p['category_id'],[]).append(p['id'])
            for ids in groups.values():
                for a,b in zip(ids,ids[1:]): self.graph.add_edge(a,b,type='SIMILAR_TO')
            texts=[c['text'] for c in self.chunks]
            self.matrix=self.embed(texts) if texts else np.zeros((0,1024),dtype=np.float32)
            self.bags=[Counter(tokens(t)) for t in texts]; self.df=Counter()
            for bag in self.bags: self.df.update(bag.keys())
            self.avg_len=sum(sum(b.values()) for b in self.bags)/max(len(self.bags),1)
            self._sync_vectors(); self._sync_neo4j()

    def _sync_vectors(self):
        if os.getenv('PG_VECTOR_BACKEND')=='numpy':
            self.collection=None
            self.vector_backend='NumPy cosine cache (rebuilt from durable records)'
            return
        try:
            import chromadb
            import hashlib
            if not hasattr(self,'chroma'): self.chroma=chromadb.PersistentClient(path=str(DATA/'chroma'))
            identity=hashlib.sha256((self.embedding_provider+self.embedding_name+str(self.matrix.shape[1])).encode()).hexdigest()[:16]
            self.collection=self.chroma.get_or_create_collection('pg-'+identity,metadata={'hnsw:space':'cosine','embedding_model':self.embedding_name})
            existing=set(self.collection.get(include=[])['ids']); current={c['id'] for c in self.chunks}
            stale=list(existing-current)
            if stale: self.collection.delete(ids=stale)
            for start in range(0,len(self.chunks),100):
                batch=self.chunks[start:start+100]
                self.collection.upsert(ids=[c['id'] for c in batch],embeddings=self.matrix[start:start+len(batch)].tolist(),documents=[c['text'] for c in batch],metadatas=[{'document_id':c['document_id'],'page':c['page'],'filename':c['filename'],'synthetic':c['synthetic']} for c in batch])
            self.vector_backend='ChromaDB persistent'
        except Exception as e:
            self.collection=None
            try:
                import faiss
                self.faiss=faiss.IndexFlatIP(self.matrix.shape[1]); self.faiss.add(self.matrix)
                self.vector_backend='FAISS fallback'
            except ImportError: self.vector_backend='NumPy cosine fallback'
            self.warnings.append('ChromaDB unavailable: '+type(e).__name__)

    def _sync_neo4j(self):
        uri=os.getenv('NEO4J_URI')
        if not uri: return
        try:
            from neo4j import GraphDatabase
            if not self.neo:
                self.neo=GraphDatabase.driver(uri,auth=(os.getenv('NEO4J_USER','neo4j'),os.getenv('NEO4J_PASSWORD','')))
            self.neo.verify_connectivity()
            with self.neo.session() as session:
                session.run('CREATE CONSTRAINT pg_id IF NOT EXISTS FOR (n:PGEntity) REQUIRE n.id IS UNIQUE').consume()
                session.run('CREATE INDEX pg_type IF NOT EXISTS FOR (n:PGEntity) ON (n.type)').consume()
                # Only this application's namespace is replaced. Do not use a shared namespace.
                session.execute_write(lambda tx: tx.run('MATCH (n:PGEntity {namespace:"productgraph"}) DETACH DELETE n').consume())
                nodes=[{'id':id,**attrs} for id,attrs in self.graph.nodes(data=True)]
                edges=[{'source':a,'target':b,'type':attrs['type']} for a,b,attrs in self.graph.edges(data=True)]
                session.run('UNWIND $rows AS r CREATE (n:PGEntity {id:r.id, namespace:"productgraph", type:r.type, label:r.label})',rows=nodes).consume()
                session.run('UNWIND $rows AS r MATCH (a:PGEntity {id:r.source}), (b:PGEntity {id:r.target}) CREATE (a)-[:PG_REL {type:r.type}]->(b)',rows=edges).consume()
            self.graph_backend='Neo4j'
        except Exception as e:
            self.graph_backend='NetworkX fallback'; self.warnings.append('Neo4j unavailable: '+type(e).__name__)

    def graph_view(self,product_id=None,limit=80):
        with self.lock:
            ids=([product_id]+list(self.graph.successors(product_id))) if product_id in self.graph else list(self.graph.nodes)[:limit] if not product_id else []
            ids=set(ids[:limit])
            return {'backend':self.graph_backend,'nodes':[{'id':id,**self.graph.nodes[id]} for id in ids], 'edges':[{'id':f'{a}-{b}-{k}','source':a,'target':b,**v} for a,b,k,v in self.graph.edges(keys=True,data=True) if a in ids and b in ids]}

    def graph_search(self,interpreted):
        scores={}; paths={}
        with self.lock:
            for id,p in self.products.items():
                if interpreted['category'] and p['domain']!=interpreted['category']: continue
                if interpreted['entities'] and id not in interpreted['entities']: continue
                ok,_=meets(p,interpreted['requirements'])
                if not ok: continue
                overlap=len(set(tokens(interpreted['original_query'])) & set(tokens(p['name']+' '+p['description'])))
                if not interpreted['category'] and not interpreted['entities'] and not overlap: continue
                edges=[{'source':id,'relationship':attrs['type'],'target':target,'label':self.graph.nodes[target]['label']} for _,target,attrs in self.graph.edges(id,data=True)]
                if self.graph_backend=='Neo4j':
                    try:
                        with self.neo.session() as session:
                            edges=[{'source':id,'relationship':r['relationship'],'target':r['target'],'label':r['label']} for r in session.run('MATCH (p:PGEntity {id:$id,namespace:"productgraph"})-[r:PG_REL]->(n) RETURN r.type AS relationship,n.id AS target,n.label AS label',id=id)]
                    except Exception:
                        self.graph_backend='NetworkX fallback'
                scores[id]=min(1,.4+.1*overlap+.1*len(interpreted['requirements'])); paths[id]=edges
        return scores,paths

    def vector_search(self,query):
        if not self.chunks: return {}
        v=self.embed([query])[0]
        with self.lock:
            if self.collection:
                results=self.collection.query(query_embeddings=[v.tolist()],n_results=len(self.chunks),include=['distances'])
                return dict(zip(results['ids'][0],[max(0,1-d) for d in results['distances'][0]]))
            if self.vector_backend=='FAISS fallback':
                values,indices=self.faiss.search(v.reshape(1,-1),len(self.chunks))
                return {self.chunks[i]['id']:max(0,float(value)) for i,value in zip(indices[0],values[0])}
            return {c['id']:max(0,float(s)) for c,s in zip(self.chunks,self.matrix@v)}

    def keyword_search(self,query):
        result={}; n=len(self.bags)
        for c,bag in zip(self.chunks,self.bags):
            score=0; length=sum(bag.values())
            for word in set(tokens(query)):
                tf=bag.get(word,0); idf=math.log(1+(n-self.df[word]+.5)/(self.df[word]+.5))
                score+=idf*tf*2.5/(tf+1.5*(.25+.75*length/max(self.avg_len,1)))
            result[c['id']]=score
        return result

    def hybrid(self,state,settings,top_k,method='hybrid'):
        def normalized(scores):
            mx=max(scores.values(),default=0)
            return {k:v/mx if mx else 0 for k,v in scores.items()}
        v=normalized(state['vector_scores']); k=normalized(state['keyword_scores']); g=normalized(state['graph_scores'])
        rows=[]; interpreted=state['interpreted']
        for c in self.chunks:
            products=[self.products[id] for id in c['product_ids'] if id in self.products]
            if interpreted['category'] and products and not any(p['domain']==interpreted['category'] for p in products): continue
            if interpreted['entities'] and not set(interpreted['entities'])&set(c['product_ids']): continue
            if interpreted['requirements'] and products and not any(meets(p,interpreted['requirements'])[0] for p in products): continue
            if interpreted['requirements'] and not products: continue
            graph=max((g.get(p['id'],0) for p in products),default=0)
            meta=float(bool(interpreted['category'] and any(p['domain']==interpreted['category'] for p in products)))
            components={'vector':v.get(c['id'],0),'keyword':k.get(c['id'],0),'graph':graph,'metadata':meta}
            weights={key:settings[key+'_weight'] for key in components}
            contributions={key:components[key]*weights[key] for key in components}
            score=sum(contributions.values()) if method=='hybrid' else components[method]
            if self.embedding_provider=='hash' and k.get(c['id'],0)==0 and graph==0: continue
            if max(components['keyword'],components['vector'],components['graph'])<.04: continue
            if method!='hybrid' and components[method]<=0: continue
            rows.append({**c,'evidence_id':c['id'],'scores':components,'contributions':contributions,'hybrid_score':score,'graph_paths':[path for p in products for path in state['graph_paths'].get(p['id'],[])],'products':products})
        rows.sort(key=lambda x:(-x['hybrid_score'],x['id']))
        # Rerank with explicit requirement coverage; retain base score for auditing.
        for row in rows:
            row['rerank_score']=row['hybrid_score']*(1.1 if interpreted['requirements'] and row['products'] else 1)
        rows.sort(key=lambda x:-x['rerank_score'])
        seen=set(); selected=[]
        for row in rows:
            key=tuple(row['product_ids']) or (row['id'],)
            if key in seen: continue
            seen.add(key); selected.append(row)
            if len(selected)>=top_k: break
        return selected
