"""Deterministic, fictional records; not real product claims."""
import csv
import json
import random
from pathlib import Path
from ..config import ROOT, DATA, SERVERLESS
from .. import database as db

DOMAINS = ['Laptops','Smartphones','Headphones','Electronics','Home Appliances','Smart Devices','Accessories']

def generate(destination=None):
    out = Path(destination or ROOT / 'datasets')
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(42)
    brands = [{'id':f'B{i:03}', 'name': f'Fictional {name} {i:02}', 'synthetic':True} for i,name in enumerate((['Aster','Novum','Kite','Lumen','Vertex']*10),1)]
    categories = [{'id':f'C{i:03}', 'name':f'{DOMAINS[(i-1)%7]} / Series {(i-1)//7+1}', 'domain':DOMAINS[(i-1)%7]} for i in range(1,101)]
    products, specs, relationships, faqs, docs = [], [], [], [], []
    for i in range(1,501):
        c = categories[(i-1)%100]; b = brands[(i-1)%50]; domain = c['domain']
        if domain == 'Laptops':
            s = {'ram_gb':rng.choice([8,16,32,64]), 'storage_gb':rng.choice([256,512,1024,2048]), 'storage_type':'SSD', 'gpu_vram_gb':rng.choice([0,4,8,12]), 'battery_hours':rng.randint(5,16)}
            features = ['USB-C','Wi-Fi 6'] + (['machine learning','CUDA capable'] if s['gpu_vram_gb']>=8 else ['everyday computing'])
        elif domain == 'Smartphones':
            s = {'ram_gb':rng.choice([6,8,12,16]), 'storage_gb':rng.choice([128,256,512]), 'battery_mah':rng.choice([4000,4500,5000]), 'display_inches':6.4}
            features = ['5G','OLED','USB-C']
        elif domain == 'Headphones':
            s = {'battery_hours':rng.randint(12,60), 'weight_g':rng.randint(180,320), 'noise_cancellation':bool(i%2)}; features=['Bluetooth','wireless audio']
        elif domain == 'Home Appliances':
            s = {'power_watts':rng.choice([600,800,1200]), 'capacity_liters':rng.choice([2,4,8]), 'warranty_years':2}; features=['energy saving','timer']
        elif domain == 'Smart Devices':
            s = {'power_watts':rng.choice([5,10,15]), 'warranty_years':1, 'wifi':True}; features=['smart home','voice control']
        else:
            s = {'power_watts':rng.choice([20,45,65,100]), 'warranty_years':2, 'weight_g':rng.randint(50,400)}; features=['USB-C','portable']
        description = f"SYNTHETIC SAMPLE. {b['name']} {domain} model {i}. " + ', '.join(f'{k}: {v}' for k,v in s.items()) + '. Features: ' + ', '.join(features)+'.'
        p = {'id':f'P{i:04}', 'name':f'{b["name"]} {domain.rstrip("s")} {i:04}', 'brand_id':b['id'], 'brand':b['name'], 'category_id':c['id'], 'category':c['name'], 'domain':domain, 'description':description, 'price':round(rng.uniform(49,2499),2), 'currency':'USD','specifications':s,'features':features,'compatibility':['USB-C'] if 'USB-C' in features else ['Bluetooth'] if 'Bluetooth' in features else [],'synthetic':True}
        products.append(p)
        for key,value in s.items():
            specs.append({'product_id':p['id'],'key':key,'value':value})
            relationships.append({'source':p['id'],'target':f'{key}:{value}','type':'HAS_SPECIFICATION'})
        relationships.extend([{'source':p['id'],'target':b['id'],'type':'MANUFACTURED_BY'}, {'source':p['id'],'target':c['id'],'type':'BELONGS_TO'}])
        if i<=100:
            faqs.append({'id':f'FAQ{i:03}','product_id':p['id'],'question':f'What features does {p["name"]} include?', 'answer':', '.join(features),'synthetic':True})
        if i<=50:
            docs.append({'id':f'MAN{i:03}','product_id':p['id'],'filename':f'{p["id"]}_manual.txt','text':description+'\nThis fictional manual is for demonstration. No independent performance tests are available.','synthetic':True})
    for name,rows in [('products',products),('brands',brands),('categories',categories),('specifications',specs),('relationships',relationships)]:
        csv_rows=[{k:json.dumps(v) if isinstance(v,(dict,list)) else v for k,v in row.items()} for row in rows]
        with (out / f'{name}.csv').open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=csv_rows[0].keys()); w.writeheader(); w.writerows(csv_rows)
    (out/'product_faqs.json').write_text(json.dumps(faqs,indent=2),encoding='utf-8')
    (out/'products.json').write_text(json.dumps(products,indent=2),encoding='utf-8')
    (out/'product_documents').mkdir(exist_ok=True)
    for d in docs:
        (out/'product_documents'/d['filename']).write_text(d['text'],encoding='utf-8')
    return products,brands,categories,faqs,docs

def seed():
    if db.get('system','seeded'):
        return
    products,brands,categories,faqs,docs=generate(DATA/'samples' if SERVERLESS else None)
    records=[]
    def save(kind,id,value): records.append((kind,id,value))
    for kind,rows in [('product',products),('brand',brands),('category',categories),('faq',faqs)]:
        for row in rows: save(kind,row['id'],row)
    for p in products:
        id='SRC-'+p['id']
        text=p['name']+'\n'+p['description']+'\nStructured specifications: '+json.dumps(p['specifications'])
        save('document',id,{'id':id,'filename':p['id']+'.json','status':'ready','synthetic':True,'product_ids':[p['id']],'hash':id,'pages':[{'page':1,'text':text}],'chunks':[{'id':id+'-1','text':text,'page':1}],'size':len(text),'origin':'structured product'})
    for d in docs:
        save('document',d['id'],{'id':d['id'],'filename':d['filename'],'status':'ready','synthetic':True,'product_ids':[d['product_id']],'hash':d['id'],'pages':[{'page':1,'text':d['text']}],'chunks':[{'id':d['id']+'-1','text':d['text'],'page':1}],'size':len(d['text']),'origin':'sample manual'})
    for f in faqs:
        id=f['id']; text=f['question']+' '+f['answer']
        save('document',id,{'id':id,'filename':id+'.json','status':'ready','synthetic':True,'product_ids':[f['product_id']],'hash':id,'pages':[{'page':1,'text':text}],'chunks':[{'id':id+'-1','text':text,'page':1}],'size':len(text),'origin':'FAQ'})
    save('system','seeded',{'version':1})
    db.put_many(records)
