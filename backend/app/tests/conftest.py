"""Isolate every integration test from developer and hosted databases."""
import os
import tempfile
from pathlib import Path

storage=Path(__file__).resolve().parents[2]/'.test-data'
storage.mkdir(exist_ok=True)
os.environ['PG_DATA_DIR']=tempfile.mkdtemp(prefix='pg-suite-',dir=storage)
os.environ['PG_REQUIRE_AUTH']='0'
os.environ['PG_SERVERLESS']='0'
os.environ['EMBEDDING_PROVIDER']='hash'
for key in ['DATABASE_URL','NEO4J_URI','OPENAI_API_KEY','PG_API_KEY']:
    os.environ.pop(key,None)
