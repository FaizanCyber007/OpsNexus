import { Sidebar } from "@/components/layout/Sidebar";
import { AgentSwarmHubContent } from "@/components/features/AgentSwarmHubContent";

export const metadata = {
  title: "Agent Swarm & MCP — OpsNexus",
  description: "LangGraph hierarchical multi-agent swarm architecture, Model Context Protocol (MCP 2.0) tools, and execution traces.",
};

export default function AgentSwarmPage() {
  return (
    <div className="flex h-screen w-full overflow-hidden bg-[#09090b]">
      <Sidebar />
      <main className="flex flex-1 flex-col overflow-y-auto p-6 sm:p-8">
        <AgentSwarmHubContent />
      </main>
    </div>
  );
}
