'use client';

import { useEffect } from 'react';
import { Room } from 'livekit-client';
import {
  RoomAudioRenderer,
  type RoomAudioRendererProps,
  SessionProvider,
  type SessionProviderProps,
  type UseSessionReturn,
} from '@livekit/components-react';

/**
 * Props for the AgentSessionProvider component.
 * Combines SessionProviderProps with RoomAudioRendererProps.
 */
export type AgentSessionProviderProps = SessionProviderProps &
  RoomAudioRendererProps & {
    /**
     * The room to provide.
     */
    room?: Room;
    /**
     * The volume to set for the audio renderer.
     */
    volume?: number;
    /**
     * Whether to mute the audio renderer.
     */
    muted?: boolean;
    /**
     * The session to provide.
     */
    session: UseSessionReturn;
    /**
     * The children to render.
     */
    children: React.ReactNode;
  };

/**
 * A provider component for agent sessions that wraps SessionProvider
 * and includes RoomAudioRenderer for audio playback.
 * Also subscribes to data channel messages from the Python agent.
 *
 * @example
 * ```tsx
 * <AgentSessionProvider session={agentSession}>
 *   <AgentControlBar />
 *   <AgentChatTranscript />
 * </AgentSessionProvider>
 * ```
 */
export function AgentSessionProvider({
  session,
  children,
  ...roomAudioRendererProps
}: AgentSessionProviderProps) {
  useEffect(() => {
    const { room } = session;
    if (!room) return;

    // Subscribe to data channel messages from Python agent
    const handleDataReceived = (payload: Uint8Array, topic: string) => {
      if (topic === 'transcript') {
        try {
          const messageText = new TextDecoder().decode(payload);
          const messageData = JSON.parse(messageText);
          console.log('📨 Data Channel Message:', messageData);
        } catch (error) {
          console.error('Failed to parse data channel message:', error);
        }
      }
    };

    const handlePacket = (packet: any) => {
      const payload = new Uint8Array(packet.payload as ArrayBuffer);
      const topic = packet.topic;
      handleDataReceived(payload, topic);
    };

    (room as any).on('dataPacketReceived', handlePacket);

    return () => {
      (room as any).off('dataPacketReceived', handlePacket);
    };
  }, [session]);

  return (
    <SessionProvider session={session}>
      {children}
      <RoomAudioRenderer {...roomAudioRendererProps} />
    </SessionProvider>
  );
}
