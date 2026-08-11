const NAV_ITEMS = ["Dashboard", "Documents", "Agents", "Settings"] as const;

export function Sidebar() {
  return (
    <aside className="flex h-full w-56 flex-col gap-1 border-r border-white/10 bg-white/5 p-4 backdrop-blur-xl">
      <div className="mb-4 px-2 text-lg font-semibold text-white">OpsNexus</div>
      <nav className="flex flex-col gap-1">
        {NAV_ITEMS.map((item) => (
          <span
            key={item}
            className="cursor-pointer rounded-lg px-3 py-2 text-sm text-white/70 transition-colors hover:bg-white/10 hover:text-white"
          >
            {item}
          </span>
        ))}
      </nav>
    </aside>
  );
}
