import { headers } from 'next/headers';
import { getAppConfig } from '@/lib/utils';
import { AppClient } from '@/components/app/app-client';

export default async function Page() {
  const hdrs = await headers();
  const appConfig = await getAppConfig(hdrs);

  return <AppClient appConfig={appConfig} />;
}
