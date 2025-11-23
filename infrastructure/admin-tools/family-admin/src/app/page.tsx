import { redirect } from 'next/navigation';

export default function Home() {
  // Server-side redirect directly to dashboard
  redirect('/dashboard');
}