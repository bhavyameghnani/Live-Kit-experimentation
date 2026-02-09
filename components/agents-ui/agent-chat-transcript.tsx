'use client';

import { useMemo } from 'react';
import { AnimatePresence } from 'motion/react';
import { type AgentState, type ReceivedMessage } from '@livekit/components-react';
import { AgentChatIndicator } from '@/components/agents-ui/agent-chat-indicator';
import {
  Conversation,
  ConversationContent,
  ConversationScrollButton,
} from '@/components/ai-elements/conversation';
import { Message, MessageContent, MessageResponse } from '@/components/ai-elements/message';

/**
 * Filter out function call syntax that some LLMs output as text.
 * Patterns like <function>name</function>, transfer_to_advisor, ({"reason":...}), etc.
 */
function filterFunctionSyntax(text: string): string {
  if (!text) return text;
  
  return text
    // <function>...</function> or <function=name>...</function>
    .replace(/<function[^>]*>.*?<\/function>/gi, '')
    // <function=name/> or <function=name>
    .replace(/<function=[^>]*\/?>/gi, '')
    // Standalone <function> or </function> tags
    .replace(/<\/?function[^>]*>/gi, '')
    // Plain function names (transfer_to_advisor, transfer_to_real_estate)
    .replace(/\btransfer_to_\w+\b/gi, '')
    // JSON in parentheses like ({"reason": "..."})
    .replace(/\(\s*\{[^}]*\}\s*\)/gi, '')
    // Parentheses with "function" inside like (function transfer...)
    .replace(/\(\s*function[^)]*\)/gi, '')
    // Empty parentheses ()
    .replace(/\(\s*\)/g, '')
    // [function call: ...]
    .replace(/\[function\s*call[^\]]*\]/gi, '')
    // {"function": ...}
    .replace(/\{\s*"?function"?\s*:.*?\}/gi, '')
    // Standalone JSON objects {"reason": ...}
    .replace(/\{\s*"reason"\s*:[^}]*\}/gi, '')
    .trim();
}

type AgentType = 'wealth' | 'realestate';

interface MessageWithAgent {
  id: string;
  timestamp: number;
  from: ReceivedMessage['from'];
  message: string;
  detectedAgent?: AgentType;
}

/**
 * Detect handoff messages and determine which agent is active.
 * Tracks agent state across the conversation based on handoff phrases.
 */
function detectAgentFromMessage(message: string): AgentType | null {
  const lowerMessage = message.toLowerCase();
  
  // Detect handoff to Real Estate Expert
  if (
    lowerMessage.includes('real estate expert') ||
    lowerMessage.includes('real estate specialist') ||
    lowerMessage.includes('property expert')
  ) {
    return 'realestate';
  }
  
  // Detect handoff back to Wealth Advisor
  if (
    (lowerMessage.includes("i'm back") && lowerMessage.includes('nomura-san')) ||
    lowerMessage.includes('wealth advisor') ||
    lowerMessage.includes('portfolio strategy')
  ) {
    return 'wealth';
  }
  
  return null;
}

/**
 * Process messages and tag each with the active agent at that point in time.
 * Starts with Wealth Advisor, switches on handoff messages.
 */
function tagMessagesWithAgent(messages: ReceivedMessage[]): MessageWithAgent[] {
  let currentAgent: AgentType = 'wealth'; // Default starting agent
  
  return messages.map((msg) => {
    const agentForThisMessage = currentAgent; // Save current agent BEFORE switching
    
    // Skip user messages for agent detection
    if (!msg.from?.isLocal) {
      const detectedSwitch = detectAgentFromMessage(msg.message);
      if (detectedSwitch) {
        currentAgent = detectedSwitch; // Switch for NEXT message, not this one
      }
    }
    
    return {
      id: msg.id,
      timestamp: msg.timestamp,
      from: msg.from,
      message: msg.message,
      detectedAgent: msg.from?.isLocal ? undefined : agentForThisMessage, // Use saved agent
    };
  });
}

/**
 * Get agent display name for label.
 */
function getAgentName(agent?: AgentType): string {
  switch (agent) {
    case 'wealth':
      return 'Wealth Advisor';
    case 'realestate':
      return 'Real Estate Expert';
    default:
      return '';
  }
}

/**
 * Get CSS classes for agent-specific styling.
 * Different colors/styles for each agent, dark mode compatible.
 */
function getAgentStyles(agent?: AgentType): string {
  switch (agent) {
    case 'wealth':
      // Blue theme for Wealth Advisor
      return 'border-l-4 border-blue-500 dark:border-blue-400 bg-blue-50/50 dark:bg-blue-950/20 pl-3';
    case 'realestate':
      // Green theme for Real Estate Expert
      return 'border-l-4 border-green-500 dark:border-green-400 bg-green-50/50 dark:bg-green-950/20 pl-3';
    default:
      // Default assistant styling
      return '';
  }
}

/**
 * Get label color for agent badge.
 */
function getAgentLabelStyles(agent?: AgentType): string {
  switch (agent) {
    case 'wealth':
      return 'text-blue-600 dark:text-blue-400';
    case 'realestate':
      return 'text-green-600 dark:text-green-400';
    default:
      return 'text-gray-600 dark:text-gray-400';
  }
}

/**
 * Props for the AgentChatTranscript component.
 */
export interface AgentChatTranscriptProps {
  /**
   * The current state of the agent. When 'thinking', displays a loading indicator.
   */
  agentState?: AgentState;
  /**
   * Array of messages to display in the transcript.
   * @defaultValue []
   */
  messages?: ReceivedMessage[];
  /**
   * Additional CSS class names to apply to the conversation container.
   */
  className?: string;
}

/**
 * A chat transcript component that displays a conversation between the user and agent.
 * Shows messages with timestamps and origin indicators, plus a thinking indicator
 * when the agent is processing.
 *
 * @extends ComponentProps<'div'>
 *
 * @example
 * ```tsx
 * <AgentChatTranscript
 *   agentState={agentState}
 *   messages={chatMessages}
 * />
 * ```
 */
export function AgentChatTranscript({
  agentState,
  messages = [],
  className,
  ...props
}: AgentChatTranscriptProps) {
  // Tag messages with which agent sent them (tracks agent switches)
  const taggedMessages = useMemo(() => tagMessagesWithAgent(messages), [messages]);
  
  return (
    <Conversation className={className} {...props}>
      <ConversationContent>
        {taggedMessages.map((receivedMessage, index) => {
          const { id, timestamp, from, message, detectedAgent } = receivedMessage;
          const filteredMessage = filterFunctionSyntax(message);
          
          // Skip messages that are only function syntax
          if (!filteredMessage) return null;
          
          const locale = navigator?.language ?? 'en-US';
          const messageOrigin = from?.isLocal ? 'user' : 'assistant';
          const time = new Date(timestamp);
          const title = time.toLocaleTimeString(locale, { timeStyle: 'full' });
          
          // Check if this is the first message from a new agent
          const prevMessage = index > 0 ? taggedMessages[index - 1] : null;
          const isNewAgent = 
            !from?.isLocal && 
            detectedAgent && 
            (!prevMessage || prevMessage.detectedAgent !== detectedAgent || prevMessage.from?.isLocal);
          
          const agentStyles = getAgentStyles(detectedAgent);
          const agentLabelStyles = getAgentLabelStyles(detectedAgent);
          const agentName = getAgentName(detectedAgent);

          return (
            <div key={id} className="flex flex-col gap-1">
              {isNewAgent && agentName && (
                <div className={`text-xs font-semibold ${agentLabelStyles} px-1`}>
                  {agentName}
                </div>
              )}
              <Message title={title} from={messageOrigin}>
                <MessageContent className={agentStyles}>
                  <MessageResponse>{filteredMessage}</MessageResponse>
                </MessageContent>
              </Message>
            </div>
          );
        })}
        <AnimatePresence>
          {agentState === 'thinking' && <AgentChatIndicator size="sm" />}
        </AnimatePresence>
      </ConversationContent>
      <ConversationScrollButton />
    </Conversation>
  );
}
