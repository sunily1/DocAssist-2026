// 인수인계용: 문서 관련 API 호출 모듈
import api from './axios';

export type AssistIntensity = 'close' | 'easy' | 'summary';
export type DownloadMode = 'converted' | 'comparison' | 'summary';

export default {
  convertText(payload: { text: string; intensity: AssistIntensity; title?: string }) {
    return api.post('/documents/convert-text', payload);
  },
  downloadTextDocx(payload: { text: string; intensity: AssistIntensity; title?: string; mode: DownloadMode }) {
    return api.post('/documents/convert-text/download', payload, {
      responseType: 'blob',
    });
  },
  uploadDocument(formData: FormData, intensity: AssistIntensity = 'easy') {
    formData.set('intensity', intensity);
    return api.post('/documents/upload', formData);
  },
  getDocuments(skip = 0, limit = 100) {
    return api.get('/documents/', { params: { skip, limit } });
  },
  getDocument(id: string) {
    return api.get(`/documents/${id}`);
  },
  getGlossaryTerms(documentId?: string) {
    return api.get('/documents/glossary/terms', {
      params: documentId ? { document_id: documentId } : undefined,
    });
  },
  setGlossaryPin(termId: string, isPinned: boolean) {
    return api.patch(`/documents/glossary/terms/${termId}/pin`, {
      is_pinned: isPinned,
    });
  },
  searchDictionary(q: string, limit = 5) {
    return api.get('/dictionary/search', {
      params: { q, limit },
    });
  },
  downloadDocument(id: string, mode: DownloadMode = 'summary') {
    return api.get(`/documents/${id}/download`, {
      params: { mode },
      responseType: 'blob',
    });
  },
  getLayoutPdf(id: string) {
    return api.get(`/documents/${id}/layout-pdf`, {
      responseType: 'blob',
    });
  },
  getOriginalFile(id: string) {
    return api.get(`/documents/${id}/original`, {
      responseType: 'blob',
    });
  },
  getConvertedOriginalFile(id: string) {
    return api.get(`/documents/${id}/converted-original`, {
      responseType: 'blob',
    });
  },
  getDocumentAnnotations(id: string, mode: 'converted' | 'original' = 'converted') {
    return api.get(`/documents/${id}/annotations`, {
      params: { mode },
    });
  },
  deleteDocument(id: string) {
    return api.delete(`/documents/${id}`);
  },
};
