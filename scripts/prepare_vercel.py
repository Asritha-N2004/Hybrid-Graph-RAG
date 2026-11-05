"""Stage the backend with a small, explicit serverless dependency set."""
from pathlib import Path
import shutil
import json
root=Path(__file__).resolve().parents[1]
destination=root/'cloud-backend'
destination.mkdir(exist_ok=True)
shutil.copytree(root/'backend'/'app',destination/'app',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','tests'))
(destination/'index.py').write_text('import os\nos.environ["PG_SERVERLESS"]="1"\nos.environ["PG_VECTOR_BACKEND"]="numpy"\nfrom app.main import app\n',encoding='utf-8')
(destination/'requirements.txt').write_text('''fastapi==0.141.1
pydantic==2.13.4
sqlalchemy==2.0.57
psycopg[binary]>=3.2,<4
python-multipart>=0.0.20,<1
numpy>=2.2,<3
networkx==3.6.1
langgraph==1.2.11
langchain-core>=1.2.22,<2
httpx==0.28.1
PyMuPDF>=1.25,<2
python-docx>=1.1,<2
''',encoding='utf-8')
dependencies=(destination/'requirements.txt').read_text().splitlines()
(destination/'pyproject.toml').write_text('[project]\nname="productgraph-api"\nversion="1.0.0"\nrequires-python="==3.12.*"\ndependencies='+json.dumps(dependencies)+'\n[tool.vercel]\nentrypoint="index:app"\n',encoding='utf-8')
print('Staged cloud-backend from backend/app')
