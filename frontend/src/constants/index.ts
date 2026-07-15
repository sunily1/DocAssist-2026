// 인수인계용: 프론트 공통 상수(문서 상태/에러 메시지)
export const DOC_STATUS = {
  QUEUED: "QUEUED",
  PROCESSING: "PROCESSING",
  DONE: "DONE",
  FAILED: "FAILED",
} as const;

export const DOC_STATUS_LABEL = {
  [DOC_STATUS.QUEUED]: "대기 중",
  [DOC_STATUS.PROCESSING]: "분석 중",
  [DOC_STATUS.DONE]: "분석 완료",
  [DOC_STATUS.FAILED]: "실패",
};

export const DOC_TYPE = {
  PDF: "PDF",
  JPG: "JPG",
  PNG: "PNG",
  TXT: "TXT",
  UNK: "UNK",
} as const;

export const ERROR_MESSAGES = {
  LOGIN_FAILED: "로그인에 실패했습니다. 이메일과 비밀번호를 확인해주세요.",
  SIGNUP_FAILED: "회원가입에 실패했습니다. 다시 시도해주세요.",
  UPLOAD_FAILED: "문서 업로드에 실패했습니다.",
  LOAD_FAILED: "데이터를 불러오는 중 오류가 발생했습니다.",
  UNKNOWN: "알 수 없는 오류가 발생했습니다.",
};

