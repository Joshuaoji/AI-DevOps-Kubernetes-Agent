import { InvestigateButton } from "@/components/InvestigateButton";

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-6">
      <div className="w-full max-w-xl rounded-2xl border border-slate-200 bg-white p-10 text-center shadow-sm">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">
          AI Kubernetes Agent
        </h1>
        <p className="mt-2 text-slate-500">Troubleshoot Kubernetes with AI</p>

        <div className="mt-8 flex justify-center">
          <InvestigateButton />
        </div>

        <div className="mt-8 flex items-center justify-center gap-2 text-sm text-slate-600">
          <span
            className="inline-block h-2.5 w-2.5 rounded-full bg-green-500"
            aria-hidden="true"
          />
          <span>
            System Status: <span className="font-medium text-slate-900">Ready</span>
          </span>
        </div>
      </div>
    </main>
  );
}
