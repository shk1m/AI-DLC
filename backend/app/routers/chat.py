"""챗봇 WebSocket 라우터 (/ws/chat)

WebSocket 기반 실시간 챗봇 통신.
Unit 3 (AI/Data)에서 LangChain Agent 연동 구현.
Unit 2에서는 WebSocket 서버 인프라만 제공.
"""

import uuid
from typing import Dict

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = structlog.get_logger()

router = APIRouter()


class WebSocketManager:
    """WebSocket 연결 관리자

    세션별 WebSocket 연결을 추적하고 메시지를 전송합니다.
    """

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        """WebSocket 연결 수립"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info("websocket_connected", session_id=session_id)

    async def disconnect(self, session_id: str) -> None:
        """WebSocket 연결 해제"""
        self.active_connections.pop(session_id, None)
        logger.info("websocket_disconnected", session_id=session_id)

    async def send_token(self, session_id: str, token: str) -> None:
        """토큰 단위 스트리밍 전송"""
        ws = self.active_connections.get(session_id)
        if ws:
            await ws.send_json({"type": "token", "content": token})

    async def send_done(
        self, session_id: str, sources: list[str] | None = None
    ) -> None:
        """응답 완료 신호 전송"""
        ws = self.active_connections.get(session_id)
        if ws:
            await ws.send_json({
                "type": "done",
                "sources": sources or [],
            })


# 싱글톤 인스턴스
ws_manager = WebSocketManager()


@router.websocket("/ws/chat/{session_id}")
async def chat_websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
):
    """챗봇 WebSocket 엔드포인트

    프로토콜:
    - 클라이언트 → 서버: {"type": "message", "content": "질문"}
    - 서버 → 클라이언트: {"type": "token", "content": "응답 토큰"}
    - 서버 → 클라이언트: {"type": "done", "sources": [...]}
    """
    await ws_manager.connect(session_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "")
            content = data.get("content", "")

            if msg_type == "message" and content:
                logger.info(
                    "chat_message_received",
                    session_id=session_id,
                    content_length=len(content),
                )

                # Unit 3에서 LangChain Agent 연동 구현
                # 현재는 에코 응답 (placeholder)
                placeholder_response = (
                    f"[시스템] 메시지를 수신했습니다: '{content[:50]}...'\n"
                    "AI Agent 연동은 Unit 3에서 구현됩니다."
                )

                # 토큰 단위 스트리밍 시뮬레이션
                for token in placeholder_response.split():
                    await ws_manager.send_token(session_id, token + " ")

                await ws_manager.send_done(session_id, sources=["placeholder"])

    except WebSocketDisconnect:
        await ws_manager.disconnect(session_id)
    except Exception as e:
        logger.error(
            "websocket_error",
            session_id=session_id,
            error=str(e),
        )
        await ws_manager.disconnect(session_id)
