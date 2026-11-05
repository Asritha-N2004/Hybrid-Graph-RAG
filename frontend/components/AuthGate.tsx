'use client';
import {useEffect,useState,type ReactNode} from 'react';
import {useRouter} from 'next/navigation';
import {Loader2,LogOut} from 'lucide-react';
import {api,errorMessage} from '@/services/api';
export default function AuthGate({children}:{children:ReactNode}){
 const router=useRouter();const [ready,setReady]=useState(false);const [name,setName]=useState('');const [error,setError]=useState('');
 useEffect(()=>{api.get('/auth/me').then(({data})=>{if(data.auth_required&&!data.authenticated){router.replace('/login');return;}setName(data.user?.name||'');setReady(true)}).catch(e=>setError(errorMessage(e)));},[router]);
 async function logout(){try{await api.post('/auth/logout');router.replace('/login');router.refresh()}catch(e){setError(errorMessage(e))}}
 if(error)return <div className="auth-wait"><p role="alert">{error}</p><button className="button" onClick={()=>location.reload()}>Retry connection</button></div>;
 if(!ready)return <div className="auth-wait"><Loader2 className="spin" size={23}/><p>Opening your workspace…</p></div>;
 return <>{children}{name&&<div className="session-control"><span>{name}</span><button onClick={()=>void logout()} aria-label="Sign out"><LogOut size={14}/> Sign out</button></div>}</>;
}
