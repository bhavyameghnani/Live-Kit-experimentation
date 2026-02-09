export interface AppConfig {
  pageTitle: string;
  pageDescription: string;
  companyName: string;

  supportsChatInput: boolean;
  supportsVideoInput: boolean;
  supportsScreenShare: boolean;
  isPreConnectBufferEnabled: boolean;

  logo: string;
  startButtonText: string;
  accent?: string;
  logoDark?: string;
  accentDark?: string;

  // agent dispatch configuration
  agentName?: string;

  // LiveKit Cloud Sandbox configuration
  sandboxId?: string;
}

export const APP_CONFIG_DEFAULTS: AppConfig = {
  companyName: 'Nomura Wealth Partners',
  pageTitle: 'Investment Advisor',
  pageDescription: 'AI-powered wealth preservation and investment strategy consultation',

  supportsChatInput: true,
  supportsVideoInput: false,
  supportsScreenShare: false,
  isPreConnectBufferEnabled: true,

  logo: '/lk-logo.svg',
  accent: '#1a5f3f',
  logoDark: '/lk-logo-dark.svg',
  accentDark: '#2ecc71',
  startButtonText: 'Start Call',

  // agent dispatch configuration - defaults to wealth-advisor cartridge
  agentName: process.env.NEXT_PUBLIC_AGENT_NAME || 'wealth-advisor',

  // LiveKit Cloud Sandbox configuration
  sandboxId: undefined,
};
