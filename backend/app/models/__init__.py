"""인수인계용: ORM 모델 일괄 import (Alembic 등록용)."""

from .user import User, PasswordReset, TermAgreement, ServiceFeedback
from .document import Document, DocumentJob, DocumentAnalysis, GlossaryTerm, DocumentEmbedding
from .chat import ChatSession, ChatMessage, PinnedMessage
from .system import SupportTicket, AccessPolicy, SystemSetting, SystemLog
