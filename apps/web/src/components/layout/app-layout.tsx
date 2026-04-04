export function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <main className="flex min-h-screen flex-1 flex-col p-4 sm:p-8">
      {children}
    </main>
  );
}
