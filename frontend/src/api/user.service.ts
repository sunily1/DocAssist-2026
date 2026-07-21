import api from './axios';

export type SatisfactionRating = 'satisfied' | 'neutral' | 'dissatisfied';

export default {
  updatePresence() {
    return api.post('/users/me/presence');
  },
  getFeedback() {
    return api.get('/users/me/feedback');
  },
  updateFeedback(rating: SatisfactionRating) {
    return api.put('/users/me/feedback', { rating });
  },
  createInquiry(payload: { type: string; content: string; reply_email: string }) {
    return api.post('/users/me/inquiries', payload);
  },
  getInquiries() {
    return api.get('/users/me/inquiries');
  },
};
