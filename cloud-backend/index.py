import os
os.environ["PG_SERVERLESS"]="1"
os.environ["PG_VECTOR_BACKEND"]="numpy"
from app.main import app
