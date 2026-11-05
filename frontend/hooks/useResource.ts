'use client';
import {useState,useEffect,useCallback} from 'react';
import {api,errorMessage} from '@/services/api';
export function useResource<T>(path:string){const [data,setData]=useState<T|null>(null);const [error,setError]=useState('');const [loading,setLoading]=useState(true);const refresh=useCallback(async()=>{setLoading(true);setError('');try{setData((await api.get<T>(path)).data);}catch(e){setError(errorMessage(e));}finally{setLoading(false);}},[path]);useEffect(()=>{void refresh();},[refresh]);return {data,error,loading,refresh};}
