'use client';

import dynamic from 'next/dynamic';
import type { AppConfig } from '@/app-config';

// Dynamically import App with no SSR to prevent livekit-client from loading on server
const AppComponent = dynamic(
  () => import('./app').then((mod) => ({ default: mod.App })),
  { ssr: false }
);

interface AppClientProps {
  appConfig: AppConfig;
}

export function AppClient({ appConfig }: AppClientProps) {
  return <AppComponent appConfig={appConfig} />;
}
