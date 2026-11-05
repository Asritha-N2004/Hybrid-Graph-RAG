import './globals.css';
import type { Metadata } from 'next';
export const metadata:Metadata={title:'ProductGraph Intelligence',description:'Evidence-backed product knowledge, connected.'};
export default function Layout({children}:{children:React.ReactNode}){return <html lang="en"><body>{children}</body></html>}
