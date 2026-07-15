// 인수인계용: 프론트 라우팅 정의 및 인증/권한 가드
import { createRouter, createWebHistory, RouteRecordRaw } from "vue-router";

import DashboardHome from "@/pages/DashboardHome.vue";
import UploadPage from "@/pages/UploadPage.vue";
import DocComparePage from "@/pages/DocComparePage.vue";
import DrivePage from "@/pages/DrivePage.vue";
import LoginPage from "@/pages/LoginPage.vue";
import SignupPage from "@/pages/SignupPage.vue";
import ForgotPasswordPage from "@/pages/ForgotPasswordPage.vue";
import ResetPasswordPage from "@/pages/ResetPasswordPage.vue";
import TermsPage from "@/pages/TermsPage.vue";
import QaPage from "@/pages/QaPage.vue";
import ProfilePage from "@/pages/ProfilePage.vue";
import AdminPage from "@/pages/AdminPage.vue";
import ChangePasswordPage from "@/pages/ChangePasswordPage.vue";

type Role = "USER" | "ADMIN";

/**
 * 🔐 인증 정보 읽기 (데모 기준)
 */
function getAuth() {
  const token = localStorage.getItem("token");
  // role이 없으면 빈 문자열 또는 null로 처리
  // AdminPage 접근 시 requiresAdmin 체크에서 role === 'ADMIN'을 엄격하게 비교하므로
  // role 저장 로직이 확실해야 함.
  const role = localStorage.getItem("role") as Role | null;

  return {
    isAuthed: !!token,
    role: role || "USER", // 기본값 USER
  };
}

const routes: RouteRecordRaw[] = [
  /* =======================
     로그인 필요 페이지
     ======================= */
  { path: "/", name: "home", component: DashboardHome, meta: { requiresAuth: true } },
  { path: "/upload", name: "upload", component: UploadPage, meta: { requiresAuth: true } },
  { path: "/drive", name: "drive", component: DrivePage, meta: { requiresAuth: true } },
  { path: "/docs/:id", name: "documentView", component: DocComparePage, meta: { requiresAuth: true } },
  { path: "/qa", name: "qa", component: QaPage, meta: { requiresAuth: true } },
  { path: "/terms", name: "terms", component: TermsPage, meta: { requiresAuth: true } },
  { path: "/profile", name: "profile", component: ProfilePage, meta: { requiresAuth: true } },
  { path: "/profile/change-password", name: "changePassword", component: ChangePasswordPage, meta: { requiresAuth: true } },

  /* =======================
     관리자 전용
     ======================= */
  {
    path: "/admin",
    name: "admin",
    component: AdminPage,
    meta: { requiresAdmin: true },
  },

  /* =======================
     게스트 전용
     ======================= */
  { path: "/login", name: "login", component: LoginPage, meta: { requiresGuest: true } },
  { path: "/signup", name: "signup", component: SignupPage, meta: { requiresGuest: true } },
  { path: "/forgot-password", name: "forgotPassword", component: ForgotPasswordPage, meta: { requiresGuest: true } },
  { path: "/reset-password", name: "resetPassword", component: ResetPasswordPage, meta: { requiresGuest: true } },

];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

/**
 * 🛡️ Global Guard
 */
router.beforeEach((to) => {
  const { isAuthed, role } = getAuth();

  const requiresAuth = Boolean(to.meta.requiresAuth);
  const requiresAdmin = Boolean(to.meta.requiresAdmin);
  const requiresGuest = Boolean(to.meta.requiresGuest);

  // 1️⃣ 로그인 필요
  if (requiresAuth && !isAuthed) {
    return { name: "login", query: { redirect: to.fullPath } };
  }

  // 2️⃣ 게스트 전용
  if (requiresGuest && isAuthed) {
    return { name: "home" };
  }

  // 3️⃣ 관리자 전용
  if (requiresAdmin && role !== "ADMIN") {
    return { name: "home" }; // 또는 403 페이지
  }

  return true;
});

export default router;
