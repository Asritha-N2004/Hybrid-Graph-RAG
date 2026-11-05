import Workspace from '@/components/Workspace';
import AuthGate from '@/components/AuthGate';
export default function Page(){return <AuthGate><Workspace section="dashboard"/></AuthGate>}
