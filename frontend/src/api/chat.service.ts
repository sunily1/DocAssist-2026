// 인수인계용: 채팅/Q&A API 호출 모듈
import api from './axios';

export default {
  createSession(title: string, documentId?: string) {
    return api.post('/chat/sessions', { title, document_id: documentId });
  },
  getSessions(skip = 0, limit = 50) {
    return api.get('/chat/sessions', { params: { skip, limit } });
  },
  getMessages(sessionId: string, skip = 0, limit = 100) {
    return api.get(`/chat/sessions/${sessionId}/messages`, { params: { skip, limit } });
  },
  askQuestion(sessionId: string, question: string) {
    return api.post(`/chat/sessions/${sessionId}/ask`, { question });
  },
};

