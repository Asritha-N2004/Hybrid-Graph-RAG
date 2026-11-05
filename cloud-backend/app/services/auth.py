"""Password authentication and revocable, hashed server-side sessions."""
import hashlib
import hmac
import os
import secrets
import time
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field
from .. import database as db
from ..config import SERVERLESS

router=APIRouter(prefix='/api/auth',tags=['Authentication'])
COOKIE='pg_session'
TTL=60*60*12

def required(): return os.getenv('PG_REQUIRE_AUTH','1')=='1'
def user_key(email): return hashlib.sha256(email.strip().lower().encode()).hexdigest()
def password_hash(password,salt): return hashlib.scrypt(password.encode(),salt=bytes.fromhex(salt),n=16384,r=8,p=1,dklen=32).hex()
def safe_user(user): return {'id':user['id'],'name':user['name'],'email':user['email']}

def current_user(request):
    token=request.cookies.get(COOKIE)
    if not token: return None
    key=hashlib.sha256(token.encode()).hexdigest()
    session=db.get('session',key)
    if not session or session['expires']<=time.time(): return None
    user=db.get('user',session['user_id'])
    return safe_user(user) if user else None

def set_session(response,user):
    token=secrets.token_urlsafe(48)
    key=hashlib.sha256(token.encode()).hexdigest()
    db.put('session',key,{'user_id':user['id'],'expires':time.time()+TTL})
    response.set_cookie(COOKIE,token,max_age=TTL,httponly=True,secure=SERVERLESS,samesite='lax',path='/')

class Credentials(BaseModel):
    email:str=Field(min_length=3,max_length=254,pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
    password:str=Field(min_length=10,max_length=128)

class Setup(Credentials):
    name:str=Field(min_length=1,max_length=100)
    setup_token:str=Field(min_length=20,max_length=256)

@router.get('/status')
def status():
    return {'auth_required':required(),'setup_required':not bool(db.all_records('user'))}

@router.get('/me')
def me(request:Request):
    user=current_user(request)
    return {'auth_required':required(),'authenticated':bool(user),'user':user}

@router.post('/setup',status_code=201)
def setup(payload:Setup,response:Response):
    expected=os.getenv('PG_SETUP_TOKEN','')
    if not expected or not hmac.compare_digest(payload.setup_token,expected):
        raise HTTPException(403,'Invalid owner setup link')
    if db.all_records('user'): raise HTTPException(409,'Owner account already exists. Sign in instead.')
    salt=secrets.token_hex(16); email=payload.email.strip().lower(); id=user_key(email)
    user={'id':id,'email':email,'name':payload.name.strip(),'salt':salt,'password_hash':password_hash(payload.password,salt),'created_at':time.time()}
    db.put('user',id,user); set_session(response,user)
    return {'user':safe_user(user)}

@router.post('/login')
def login(payload:Credentials,response:Response):
    id=user_key(payload.email); now=time.time()
    throttle=db.get('login_attempt',id) or {'count':0,'until':0}
    if throttle['until']>now: raise HTTPException(429,'Too many attempts. Please try again in 15 minutes.')
    user=db.get('user',id)
    salt=user['salt'] if user else '00'*16
    candidate=password_hash(payload.password,salt)
    if not user or not hmac.compare_digest(candidate,user['password_hash']):
        count=throttle['count']+1 if throttle.get('last',0)>now-900 else 1
        db.put('login_attempt',id,{'count':count,'last':now,'until':now+900 if count>=5 else 0})
        raise HTTPException(401,'Email or password is incorrect')
    db.delete('login_attempt',id); set_session(response,user)
    return {'user':safe_user(user)}

@router.post('/logout')
def logout(request:Request,response:Response):
    token=request.cookies.get(COOKIE)
    if token: db.delete('session',hashlib.sha256(token.encode()).hexdigest())
    response.delete_cookie(COOKIE,path='/',secure=SERVERLESS,httponly=True,samesite='lax')
    return {'signed_out':True}
