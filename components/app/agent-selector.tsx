'use client';

import { useCallback } from 'react';
import { Button } from '@/components/ui/button';

interface Agent {
  id: string;
  name: string;
  description: string;
  icon: string;
}

// Your investment advisor cartridges
const AVAILABLE_AGENTS: Agent[] = [
  {
    id: 'wealth-advisor',
    name: 'Wealth Advisor',
    description: 'Wealth advisor helping you manage and grow your capital responsibly.',
    icon: '💼',
  },
];

interface AgentSelectorProps {
  onSelectAgent: (agentId: string) => void;
  defaultAgent?: string;
  disabled?: boolean;
}

export function AgentSelector({
  onSelectAgent,
  defaultAgent = 'wealth-advisor',
  disabled = false,
}: AgentSelectorProps) {
  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      onSelectAgent(e.target.value);
    },
    [onSelectAgent]
  );

  return (
    <div className="w-full space-y-3">
      <div className="space-y-1">
        <label htmlFor="agent-select" className="text-sm font-medium text-foreground">Select Your Advisor</label>
        <p className="text-xs text-muted-foreground">
          Choose which advisor profile to consult with. Each has different expertise and approach.
        </p>
      </div>

      <select
        id="agent-select"
        defaultValue={defaultAgent}
        onChange={handleChange}
        disabled={disabled}
        className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
      >
        <option value="" disabled>Choose an advisor...</option>
        {AVAILABLE_AGENTS.map((agent) => (
          <option key={agent.id} value={agent.id}>
            {agent.icon} {agent.name}
          </option>
        ))}
      </select>

      {/* Display selected agent details */}
      {defaultAgent && (
        <div className="rounded-lg border border-border bg-card p-3">
          {AVAILABLE_AGENTS.find((a) => a.id === defaultAgent) && (
            <div className="space-y-1">
              <p className="text-xs font-medium text-muted-foreground">
                {AVAILABLE_AGENTS.find((a) => a.id === defaultAgent)?.description}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
