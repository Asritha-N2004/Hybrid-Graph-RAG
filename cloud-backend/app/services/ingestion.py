import csv
import hashlib
import io
import json
import re
import uuid
from pathlib import Path
from .. import database as db
from ..schemas import Product

ALLOWED={'.txt','.csv','.json','.pdf','.docx'}

def parse(filename,data):
    suffix=Path(filename).suffix.lower()
    if suffix not in ALLOWED: raise ValueError('Supported formats: TXT, CSV, JSON, PDF, DOCX')
    if suffix=='.pdf':
        import fitz
        with fitz.open(stream=data,filetype='pdf') as pdf:
            if len(pdf)>500: raise ValueError('PDF page limit is 500')
            return [{'page':i+1,'text':page.get_text()} for i,page in enumerate(pdf)],[]
    if suffix=='.docx':
        import zipfile
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            if sum(f.file_size for f in z.infolist())>50*1024*1024: raise ValueError('Expanded DOCX exceeds 50 MB')
        from docx import Document
        doc=Document(io.BytesIO(data))
        text='\n'.join([p.text for p in doc.paragraphs]+[' | '.join(c.text for c in r.cells) for t in doc.tables for r in t.rows])
        # DOCX has no reliable source pagination. Never invent page numbers.
        return [{'page':0,'text':text}],[]
    text=data.decode('utf-8-sig')
    rows=[]
    if suffix=='.json':
        obj=json.loads(text)
        candidate=obj if isinstance(obj,list) else obj.get('products',[]) if isinstance(obj,dict) else []
        if candidate and all(isinstance(x,dict) and 'specifications' in x and 'brand_id' in x for x in candidate): rows=candidate
        text=json.dumps(obj,ensure_ascii=False,indent=2)
    elif suffix=='.csv':
        candidate=list(csv.DictReader(io.StringIO(text)))
        if candidate and 'specifications' in candidate[0] and 'brand_id' in candidate[0]:
            for row in candidate:
                for field in ['specifications','features','compatibility']: row[field]=json.loads(row.get(field) or ('{}' if field=='specifications' else '[]'))
                row['synthetic']=str(row.get('synthetic','false')).lower()=='true'
            rows=candidate
    validated=[Product.model_validate(row).model_dump() for row in rows]
    return [{'page':1,'text':text}],validated

def ingest(filename,data,synthetic=False):
    digest=hashlib.sha256(data).hexdigest()
    existing=next((d for d in db.all_records('document') if d.get('hash')==digest),None)
    if existing: return {**existing,'duplicate':True}
    id='DOC-'+uuid.uuid4().hex[:12]
    d={'id':id,'filename':Path(filename.replace('\\','/')).name,'size':len(data),'status':'processing','hash':digest,'synthetic':synthetic,'product_ids':[],'pages':[],'chunks':[],'origin':'upload','error':None}
    db.put('document',id,d)
    try:
        pages,products=parse(filename,data)
        if not any(p['text'].strip() for p in pages): raise ValueError('No extractable text; scanned PDFs require OCR before upload')
        known=db.all_records('product'); ids={p['id'] for p in products}
        for page in pages:
            page['text']=re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]','',page['text']).strip()
            for p in known:
                if re.search(r'\b'+re.escape(p['id'])+r'\b',page['text'],re.I) or p['name'].lower() in page['text'].lower(): ids.add(p['id'])
            for offset in range(0,len(page['text']),900):
                d['chunks'].append({'id':f'{id}-p{page["page"]}-c{offset//900+1}','text':page['text'][offset:offset+1100],'page':page['page']})
        for p in products:
            p['synthetic']=bool(p['synthetic'] or synthetic)
            db.put('product',p['id'],p)
            # A canonical structured source is replaced when an imported product changes.
            sync_product_source(p)
        d.update(pages=pages,product_ids=sorted(ids),status='ready',extracted_entities=sorted(ids),extracted_relationships=[{'source':pid,'relationship':'MENTIONED_IN','target':id} for pid in sorted(ids)])
    except Exception as e:
        d.update(status='error',error=str(e)[:500])
    db.put('document',id,d)
    return d

def sync_product_source(p):
    id='SRC-'+p['id']; text=p['name']+'\n'+p['description']+'\nStructured specifications: '+json.dumps(p['specifications'])+'\nFeatures: '+', '.join(p['features'])
    db.put('document',id,{'id':id,'filename':p['id']+'.json','size':len(text),'status':'ready','synthetic':p['synthetic'],'product_ids':[p['id']],'hash':hashlib.sha256(text.encode()).hexdigest(),'pages':[{'page':1,'text':text}],'chunks':[{'id':id+'-1','text':text,'page':1}],'origin':'structured product'})
