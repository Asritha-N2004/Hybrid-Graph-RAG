"""Server-only configuration. Environment variables are never returned to clients."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SERVERLESS = os.getenv('PG_SERVERLESS') == '1'
DATA = Path(os.getenv('PG_DATA_DIR', '/tmp/productgraph' if SERVERLESS else str(ROOT / 'backend' / 'storage')))
DATA.mkdir(parents=True, exist_ok=True)
DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{DATA / "productgraph.db"}')
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql+psycopg://', 1)
elif DATABASE_URL.startswith('postgresql://'):
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg://', 1)
if SERVERLESS and not DATABASE_URL.startswith('postgresql+psycopg://'):
    raise RuntimeError('Serverless deployment requires durable PostgreSQL DATABASE_URL')
API_KEY = os.getenv('PG_API_KEY', '')
LLM_KEY = os.getenv('OPENAI_API_KEY', '')
LLM_URL = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
LLM_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4.1-mini')
CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000').split(',')
MAX_UPLOAD = (3 if SERVERLESS else 10) * 1024 * 1024
