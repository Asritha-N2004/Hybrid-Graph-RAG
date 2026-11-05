import axios from 'axios';
export const api=axios.create({baseURL:'/api',timeout:180000});
api.interceptors.request.use(config=>{if(typeof window!=='undefined'){const key=sessionStorage.getItem('pg-api-key');if(key)config.headers.set('X-API-Key',key);}return config;});
export function errorMessage(error:unknown):string{if(axios.isAxiosError(error)){const detail=error.response?.data?.detail;return typeof detail==='string'?detail:detail?JSON.stringify(detail):error.message;}return error instanceof Error?error.message:String(error);}
