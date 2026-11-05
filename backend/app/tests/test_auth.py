import time
import pytest
from fastapi.testclient import TestClient
from app import database as db
from app.main import app
from app.services import auth

@pytest.fixture
def secured_client(monkeypatch):
    monkeypatch.setenv('PG_REQUIRE_AUTH','1')
    monkeypatch.setenv('PG_SETUP_TOKEN','local-test-setup-token-1234567890')
    with TestClient(app) as client:
        yield client
    for kind in ['user','session','login_attempt']:
        for row in db.all_records(kind):
            if kind=='user': db.delete(kind,row['id'])
    with db.Session.begin() as session:
        session.query(db.Record).filter(db.Record.kind.in_(['session','login_attempt'])).delete(synchronize_session=False)

def setup(client):
    return client.post('/api/auth/setup',json={'name':'Test Owner','email':'owner@example.test','password':'SyntheticTestPassword!','setup_token':'local-test-setup-token-1234567890'})

def test_login_protection_and_logout(secured_client):
    c=secured_client
    assert c.get('/api/products').status_code==401
    assert c.get('/api/auth/status').json()['setup_required']
    assert c.post('/api/auth/setup',json={'name':'Bad','email':'bad@example.test','password':'BadPassword123','setup_token':'wrong-invalid-token12345'}).status_code==403
    created=setup(c); assert created.status_code==201,created.text
    assert 'httponly' in created.headers['set-cookie'].lower()
    assert 'samesite=lax' in created.headers['set-cookie'].lower()
    assert 'password' not in str(created.json())
    assert c.get('/api/products').status_code==200
    assert c.get('/api/auth/me').json()['user']['name']=='Test Owner'
    assert setup(c).status_code==409
    assert c.post('/api/auth/logout').status_code==200
    assert c.get('/api/products').status_code==401
    assert c.post('/api/auth/login',json={'email':'owner@example.test','password':'WrongPassword!!'}).status_code==401
    assert c.post('/api/auth/login',json={'email':'OWNER@example.test','password':'SyntheticTestPassword!'}).status_code==200
    assert c.get('/api/products').status_code==200
    for user in db.all_records('user'):
        assert user['password_hash']!='SyntheticTestPassword!'
        assert len(user['salt'])==32

def test_login_throttle_expiry_and_csrf(secured_client):
    c=secured_client; assert setup(c).status_code==201
    token=c.cookies.get(auth.COOKIE)
    key=__import__('hashlib').sha256(token.encode()).hexdigest()
    session=db.get('session',key); session['expires']=time.time()-1; db.put('session',key,session)
    assert c.get('/api/products').status_code==401
    assert c.post('/api/auth/login',json={'email':'owner@example.test','password':'SyntheticTestPassword!'},headers={'Origin':'https://attacker.invalid'}).status_code==403
    for _ in range(5):
        assert c.post('/api/auth/login',json={'email':'owner@example.test','password':'WrongPassword!!'}).status_code==401
    assert c.post('/api/auth/login',json={'email':'owner@example.test','password':'SyntheticTestPassword!'}).status_code==429
