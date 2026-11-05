import Workspace from '@/components/Workspace';
import {notFound} from 'next/navigation';
import AuthGate from '@/components/AuthGate';
const sections=['dashboard','products','graph','chat','agents','explainability','comparison','documents','evaluation','settings'];
export default async function Page({params}:{params:Promise<{section:string}>}){const {section}=await params;if(!sections.includes(section))notFound();return <AuthGate><Workspace section={section}/></AuthGate>}
