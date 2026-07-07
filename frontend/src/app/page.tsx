"use client";

import { AuthForm } from "@/components/AuthForm";
import { Dashboard } from "@/components/Dashboard";
import { useAuth } from "@/context/AuthContext";

export default function HomePage() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="text-sm text-slate-400">Loading…</p>
      </main>
    );
  }

  return user ? <Dashboard /> : <AuthForm />;
}
