'use client';

/**
 * FE-06 — ChatBot (Floating, Streaming)
 * ────────────────────────────────────────────────────────────────────────────
 * - 우측 하단 플로팅 버튼 + 슬라이드-업 패널 (framer-motion)
 * - lib/chatStream.streamMockChat 으로 토큰 스트리밍 (Bedrock 시뮬레이션)
 * - 타이핑 cursor + 인라인 태그(식자재/레시피 칩) + 인용 풋노트
 * - 인라인 태그 클릭 → Zustand selection 변경 (대시보드와 양방향 연동)
 * ────────────────────────────────────────────────────────────────────────────
 */

import { AnimatePresence, motion } from 'framer-motion';
import {
  BookOpen,
  ChefHat,
  MessageCircle,
  Newspaper,
  Send,
  Sparkles,
  Tag,
  X,
} from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

import { streamMockChat } from '@/lib/chatStream';
import { useDashboardStore } from '@/lib/store';
import { cn } from '@/lib/utils';
import type { ChatInlineTag, ChatMessage } from '@/types';

const SUGGESTED_PROMPTS = [
  '양파 가격이 왜 올랐어?',
  '김치찌개 200인분 원가 계산해줘',
  '한우 등심 대체 재료 알려줘',
];

export function ChatBot() {
  const isChatOpen = useDashboardStore((s) => s.isChatOpen);
  const isChatStreaming = useDashboardStore((s) => s.isChatStreaming);
  const chatMessages = useDashboardStore((s) => s.chatMessages);
  const toggleChat = useDashboardStore((s) => s.toggleChat);
  const appendChatMessage = useDashboardStore((s) => s.appendChatMessage);
  const appendChatToken = useDashboardStore((s) => s.appendChatToken);
  const appendChatInlineTag = useDashboardStore((s) => s.appendChatInlineTag);
  const appendChatCitation = useDashboardStore((s) => s.appendChatCitation);
  const finishChatStreaming = useDashboardStore((s) => s.finishChatStreaming);
  const setChatStreaming = useDashboardStore((s) => s.setChatStreaming);
  const setIngredient = useDashboardStore((s) => s.setIngredient);
  const setActiveRecipe = useDashboardStore((s) => s.setActiveRecipe);

  const [input, setInput] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // 새 메시지/스트리밍 진행 시 스크롤 하단 고정
  useEffect(() => {
    if (!scrollRef.current) return;
    scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [chatMessages, isChatStreaming]);

  // 패널 열릴 때 인풋 포커스
  useEffect(() => {
    if (isChatOpen) {
      const t = setTimeout(() => inputRef.current?.focus(), 250);
      return () => clearTimeout(t);
    }
  }, [isChatOpen]);

  async function handleSend(text?: string) {
    const userText = (text ?? input).trim();
    if (!userText || isChatStreaming) return;

    const userMsgId = `msg-u-${Date.now()}`;
    const assistantMsgId = `msg-a-${Date.now()}`;

    const userMsg: ChatMessage = {
      id: userMsgId,
      role: 'user',
      content: userText,
      createdAt: new Date().toISOString(),
    };
    const assistantMsg: ChatMessage = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      createdAt: new Date().toISOString(),
      isStreaming: true,
      inlineTags: [],
      citations: [],
    };

    appendChatMessage(userMsg);
    appendChatMessage(assistantMsg);
    setChatStreaming(true);
    setInput('');

    try {
      for await (const chunk of streamMockChat({ messageId: assistantMsgId, userText })) {
        if (chunk.kind === 'token') {
          appendChatToken(assistantMsgId, chunk.delta);
        } else if (chunk.kind === 'inline_tag') {
          appendChatInlineTag(assistantMsgId, chunk.tag);
        } else if (chunk.kind === 'citation') {
          appendChatCitation(assistantMsgId, chunk.citation);
        } else if (chunk.kind === 'done') {
          finishChatStreaming(assistantMsgId);
        }
      }
    } catch {
      finishChatStreaming(assistantMsgId);
    }
  }

  function handleInlineTagClick(tag: ChatInlineTag) {
    if (tag.type === 'ingredient') setIngredient(tag.refId);
    else if (tag.type === 'recipe') setActiveRecipe(tag.refId);
  }

  return (
    <>
      {/* 플로팅 버튼 */}
      <AnimatePresence>
        {!isChatOpen && (
          <motion.button
            type="button"
            onClick={() => toggleChat(true)}
            initial={{ opacity: 0, y: 10, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.9 }}
            transition={{ duration: 0.18 }}
            className="fixed bottom-6 right-6 z-50 flex items-center gap-2 rounded-full bg-gradient-to-br from-brand-500 to-brand-700 px-5 py-3 text-sm font-semibold text-white shadow-lg hover:scale-[1.03] active:scale-[0.98]"
            aria-label="AI 챗봇 열기"
          >
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-brand-200 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-white" />
            </span>
            <MessageCircle className="h-4 w-4" />
            AI 어시스턴트
          </motion.button>
        )}
      </AnimatePresence>

      {/* 채팅 패널 */}
      <AnimatePresence>
        {isChatOpen && (
          <motion.div
            key="chat-panel"
            initial={{ opacity: 0, y: 24, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 24, scale: 0.96 }}
            transition={{ type: 'spring', stiffness: 320, damping: 28 }}
            className="fixed bottom-6 right-6 z-50 flex h-[560px] w-[400px] max-w-[calc(100vw-2rem)] flex-col overflow-hidden rounded-bento border border-ink-100 bg-white shadow-bento-hover"
          >
            {/* 헤더 */}
            <div className="flex items-center justify-between border-b border-ink-100 bg-gradient-to-r from-brand-50 via-white to-brand-50/40 px-4 py-3">
              <div className="flex items-center gap-2.5">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 text-white shadow-sm">
                  <Sparkles className="h-4 w-4" />
                </div>
                <div className="leading-tight">
                  <p className="text-sm font-semibold text-ink-900">AI 어시스턴트</p>
                  <p className="text-[11px] text-ink-500">
                    Bedrock · 온톨로지 RAG · 시세·뉴스 결합
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => toggleChat(false)}
                className="rounded-md p-1 text-ink-400 hover:bg-ink-100 hover:text-ink-700"
                aria-label="닫기"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* 메시지 목록 */}
            <div
              ref={scrollRef}
              className="flex-1 space-y-3 overflow-y-auto bg-gradient-to-b from-white to-ink-50/40 px-4 py-4"
            >
              {chatMessages.map((m) => (
                <ChatBubble
                  key={m.id}
                  message={m}
                  onInlineTagClick={handleInlineTagClick}
                />
              ))}
            </div>

            {/* 추천 프롬프트 (히스토리 짧을 때만) */}
            {chatMessages.length <= 1 && (
              <div className="flex flex-wrap gap-1.5 border-t border-ink-100 bg-white px-3 py-2">
                {SUGGESTED_PROMPTS.map((p) => (
                  <button
                    key={p}
                    type="button"
                    onClick={() => handleSend(p)}
                    disabled={isChatStreaming}
                    className="rounded-full border border-ink-200 bg-white px-2.5 py-1 text-[11px] font-medium text-ink-600 hover:border-brand-300 hover:text-brand-700 disabled:opacity-50"
                  >
                    {p}
                  </button>
                ))}
              </div>
            )}

            {/* 입력창 */}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSend();
              }}
              className="flex items-center gap-2 border-t border-ink-100 bg-white px-3 py-3"
            >
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={
                  isChatStreaming ? 'AI가 답변 중입니다…' : '예: 양파 가격이 왜 올랐어?'
                }
                disabled={isChatStreaming}
                className="flex-1 rounded-lg border border-ink-200 bg-white px-3 py-2 text-sm text-ink-800 outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100 disabled:bg-ink-50 disabled:text-ink-400"
              />
              <button
                type="submit"
                disabled={!input.trim() || isChatStreaming}
                className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-600 text-white transition-all hover:bg-brand-700 disabled:bg-ink-200 disabled:text-ink-400"
                aria-label="보내기"
              >
                <Send className="h-4 w-4" />
              </button>
            </form>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 메시지 버블
// ─────────────────────────────────────────────────────────────────────────────

function ChatBubble({
  message,
  onInlineTagClick,
}: {
  message: ChatMessage;
  onInlineTagClick: (tag: ChatInlineTag) => void;
}) {
  const isUser = message.role === 'user';

  return (
    <div className={cn('flex w-full', isUser ? 'justify-end' : 'justify-start')}>
      <div
        className={cn(
          'max-w-[88%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed shadow-sm',
          isUser
            ? 'rounded-br-sm bg-brand-600 text-white'
            : 'rounded-bl-sm border border-ink-100 bg-white text-ink-800',
        )}
      >
        <p className="whitespace-pre-wrap break-words">
          {message.content}
          {message.isStreaming && (
            <span className="ml-0.5 inline-block h-3.5 w-1 translate-y-0.5 animate-pulse-soft bg-current align-middle" />
          )}
        </p>

        {/* 인라인 태그 (식자재 / 레시피 / 뉴스 칩) */}
        {!isUser && message.inlineTags && message.inlineTags.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {message.inlineTags.map((tag, i) => (
              <button
                key={`${tag.type}-${tag.refId}-${i}`}
                type="button"
                onClick={() => onInlineTagClick(tag)}
                className="inline-flex items-center gap-1 rounded-full border border-brand-200 bg-brand-50 px-2 py-0.5 text-[11px] font-semibold text-brand-700 transition-colors hover:bg-brand-100"
              >
                <InlineTagIcon type={tag.type} />
                {tag.label}
              </button>
            ))}
          </div>
        )}

        {/* 인용 (Citations) */}
        {!isUser && message.citations && message.citations.length > 0 && (
          <div className="mt-2 border-t border-ink-100 pt-2">
            <p className="mb-1 text-[10px] font-bold uppercase tracking-wide text-ink-400">
              출처
            </p>
            <ul className="flex flex-col gap-0.5">
              {message.citations.map((c, i) => (
                <li key={i} className="text-[11px] text-ink-500">
                  <span className="font-semibold text-ink-700">{c.title}</span>
                  <span className="ml-1 text-ink-400">— {c.source}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

function InlineTagIcon({ type }: { type: ChatInlineTag['type'] }) {
  if (type === 'recipe') return <ChefHat className="h-3 w-3" />;
  if (type === 'news') return <Newspaper className="h-3 w-3" />;
  if (type === 'category') return <BookOpen className="h-3 w-3" />;
  return <Tag className="h-3 w-3" />;
}
