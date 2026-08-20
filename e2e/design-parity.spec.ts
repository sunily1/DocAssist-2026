import { expect, test, type Page } from '@playwright/test';

const docs = [
  { id: 'doc-1', title: '임대차계약서.pdf', file_type: 'PDF', status: 'DONE', created_at: '2026-07-15T09:00:00Z', user_id: 'user-1' },
  { id: 'doc-2', title: '업무 협약서.docx', file_type: 'DOCX', status: 'DONE', created_at: '2026-07-14T09:00:00Z', user_id: 'user-1' },
  { id: 'doc-3', title: '회의 메모.txt', file_type: 'TXT', status: 'PROCESSING', created_at: '2026-07-13T09:00:00Z', user_id: 'user-1' },
];

function makePdf(text: string) {
  const stream = `BT /F1 18 Tf 72 700 Td (${text.replace(/[()\\]/g, '\\$&')}) Tj ET`;
  const objects = [
    '<< /Type /Catalog /Pages 2 0 R >>',
    '<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
    '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>',
    `<< /Length ${Buffer.byteLength(stream)} >>\nstream\n${stream}\nendstream`,
    '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
  ];
  let pdf = '%PDF-1.4\n';
  const offsets = [0];
  objects.forEach((object, index) => {
    offsets.push(Buffer.byteLength(pdf));
    pdf += `${index + 1} 0 obj\n${object}\nendobj\n`;
  });
  const xrefOffset = Buffer.byteLength(pdf);
  pdf += `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`;
  for (const offset of offsets.slice(1)) pdf += `${String(offset).padStart(10, '0')} 00000 n \n`;
  pdf += `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xrefOffset}\n%%EOF`;
  return Buffer.from(pdf);
}

const originalPdf = makePdf('Tenant shall pay the remaining balance by tomorrow. The above terms apply.');
const convertedPdf = makePdf('Renter must pay the money left by the next day. These terms apply.');

async function mockApi(page: Page) {
  await page.addInitScript(() => {
    localStorage.setItem('token', 'visual-test-token');
    localStorage.setItem('role', 'ADMIN');
    localStorage.setItem('theme', 'light');
    localStorage.setItem('font_size', 'md');
    localStorage.setItem('custom_font_size', '16.5');
  });

  await page.route('**/api/v1/**', async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname.replace('/api/v1', '');
    const method = request.method();
    const user = {
      id: 'user-1', email: 'doq@example.com', name: '김도큐', role: 'ADMIN',
      created_at: '2026-01-05T09:00:00Z', last_login_at: '2026-07-16T08:30:00Z',
      profile_settings: { ui: { theme: 'light', fontSize: 'md', customFontSize: 16.5, sentenceMode: true }, assist: { level: 'easy', termDepth: 3, evidenceMode: 'panel' } },
    };

    if (path === '/users/me' && (method === 'GET' || method === 'PATCH')) return route.fulfill({ json: user });
    if (path === '/users/me/presence') return route.fulfill({ json: { ok: true } });
    if (path === '/users/me/feedback') return route.fulfill({ json: { rating: 'satisfied' } });
    if (path === '/documents/convert-text' && method === 'POST' && request.postData()?.includes('이미 쉬운 문장')) return route.fulfill({ json: {
      summary: '이미 쉬운 문장입니다.', converted_text: '이미 쉬운 문장입니다.',
      paragraphs: [{ original: '이미 쉬운 문장입니다.', easy: '이미 쉬운 문장입니다.', changed_terms: [] }],
      rules: [], terms: [],
    } });
    if (path === '/documents/convert-text' && method === 'POST') return route.fulfill({ json: {
      summary: '계약 종료 통보 기한과 위약금 계산 방법을 설명한 내용입니다.',
      converted_text: '',
      paragraphs: [
        { original: '본 계약을 해지하려면, 종료 30일 전까지 서면 통보하여야 한다.', easy: '이 계약을 그만두려면, 끝나는 날 30일 전까지 글로 알려 주셔야 해요.', changed_terms: [{ from: '해지', to: '그만두기', definition: '계약을 중간에 끝내는 것' }, { from: '서면 통보', to: '글로 알림', definition: '문서나 글로 상대에게 알리는 것' }] },
        { original: '통보하지 않으면 동일 조건으로 자동 갱신된다.', easy: '알려 주지 않으면 같은 조건으로 저절로 연장돼요.', changed_terms: [{ from: '자동 갱신', to: '저절로 연장', definition: '별도 절차 없이 계약이 이어지는 것' }] },
        { original: '위약금은 잔여 기간에 비례하여 산정한다.', easy: '위약금은 남은 기간에 맞춰 계산해요.', changed_terms: [{ from: '비례하여 산정', to: '맞춰 계산', definition: '기간에 따라 금액을 정하는 것' }] },
      ],
      rules: [], terms: [{ term: '위약금', definition: '약속을 지키지 못했을 때 내는 돈' }],
    } });
    if (path === '/documents/' && method === 'GET') return route.fulfill({ json: docs });
    if (path === '/documents/glossary/terms') return route.fulfill({ json: [
      { id: 'term-1', document_id: 'doc-1', document_title: '임대차계약서.pdf', term: '명시', definition: '내용을 분명하게 적어 알림', evidence: ['계약서에 명시합니다.'], primary_tag: 'legal', frequency: 9, is_pinned: false, created_at: '2026-07-15T09:00:00Z' },
      { id: 'term-2', document_id: 'doc-2', document_title: '업무 협약서.docx', term: '잔여', definition: '쓰고 남은 나머지', evidence: ['잔여 금액을 지급합니다.'], primary_tag: 'finance', frequency: 6, is_pinned: true, created_at: '2026-07-14T09:00:00Z' },
    ] });
    if (path === '/documents/doc-1') return route.fulfill({ json: {
      ...docs[0], analysis: { summary: '계약 기간과 보증금, 계약 당사자의 의무를 정한 문서입니다.', paragraphs: [
        { original: '임차인은 잔여 금액을 익일까지 납부하여야 한다.', easy: '세입자는 남은 금액을 다음 날까지 내야 합니다.', changed_terms: [{ from: '임차인', to: '세입자', definition: '집을 빌린 사람' }, { from: '익일', to: '다음 날', definition: '바로 다음 날' }] },
        { original: '상기 내용은 계약서에 명시한다.', easy: '위 내용은 계약서에 분명히 적습니다.', changed_terms: [{ from: '상기', to: '위', definition: '앞에서 말한 내용' }] },
      ] }, meta_data: { converted_text: '' }, glossary_terms: [{ term: '임차인', definition: '집을 빌린 사람' }, { term: '익일', definition: '다음 날' }],
    } });
    if (/^\/documents\/doc-1\/(original|converted-original)$/.test(path)) return route.fulfill({
      status: 200,
      contentType: 'application/pdf',
      body: path.endsWith('/original') ? originalPdf : convertedPdf,
    });
    if (path === '/documents/doc-1/annotations') return route.fulfill({ json: {
      mode: url.searchParams.get('mode') || 'converted',
      annotations: [
        { id: '0-0-임차인-세입자', segment: 0, page: 1, page_width: 612, page_height: 792, x: 72, y: 76, width: 49, height: 19, original: '임차인', easy: '세입자', definition: '집을 빌린 사람', approximate: false },
        { id: '0-1-익일-다음 날', segment: 0, page: 1, page_width: 612, page_height: 792, x: 255, y: 76, width: 62, height: 19, original: '익일', easy: '다음 날', definition: '바로 다음 날', approximate: false },
        { id: '1-0-상기-위', segment: 0, page: 1, page_width: 612, page_height: 792, x: 430, y: 76, width: 38, height: 19, original: '상기', easy: '위', definition: '앞에서 말한 내용', approximate: true },
      ],
    } });
    if (path === '/chat/sessions' && method === 'GET') return route.fulfill({ json: [] });
    if (path === '/chat/sessions' && method === 'POST') return route.fulfill({ json: { id: 'session-1' } });
    if (path === '/chat/sessions/session-1/messages') return route.fulfill({ json: [] });
    if (path === '/admin/metrics') return route.fulfill({ json: {
      users: 128, docs: 346, queue: 2, qaToday: 57, signups: 8, loginsToday: 62, activeUsers: 14, uploadsToday: 31,
      glossaryTerms: 96, glossaryTermsToday: 12, glossaryPinned: 24,
      serviceUsage: [{ label: '텍스트 변환', value: 82 }, { label: '파일 변환', value: 64 }, { label: '챗봇', value: 53 }, { label: '용어집', value: 39 }],
      satisfaction: [{ label: '만족', value: 74, color: '#5b8cff' }, { label: '보통', value: 19, color: '#21c7b7' }, { label: '불만', value: 7, color: '#fb7185' }],
      devices: [{ label: '데스크톱', value: 68, color: '#5b8cff' }, { label: '모바일', value: 25, color: '#21c7b7' }, { label: '태블릿', value: 7, color: '#fbbf24' }],
      apiStatus: { backend: { status: 'ok', label: '백엔드', message: '정상' }, db: { status: 'ok', label: 'DB', message: '정상' }, openai: { status: 'warn', label: 'LLM', message: '확인 필요' }, dictionary: { status: 'ok', label: '국어사전', message: '정상' } },
    } });
    if (path === '/admin/users') return route.fulfill({ json: [user] });
    if (path === '/admin/documents') return route.fulfill({ json: docs });
    return route.fulfill({ json: {} });
  });
}

test('major screens preserve the DOQ desktop geometry', async ({ page }) => {
  await mockApi(page);
  await page.setViewportSize({ width: 1440, height: 1000 });
  const paths = ['/', '/upload', '/drive', '/docs/doc-1', '/qa', '/terms', '/profile', '/admin'];

  for (const path of paths) {
    await page.goto(`http://localhost:3000${path}`);
    await page.waitForLoadState('networkidle');
    await expect(page.locator('.sidebar')).toHaveCSS('width', '244px');
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(overflow, `${path} has horizontal overflow`).toBeLessThanOrEqual(0);
    await page.screenshot({ path: `/tmp/doq-parity-${path === '/' ? 'home' : path.slice(1).replaceAll('/', '-')}.png`, fullPage: true });
  }

  await page.goto('http://localhost:3000/qa');
  await page.locator('.doq-doc-picker').click();
  await expect(page.locator('.doq-doc-menu')).toBeVisible();
  await page.locator('.doq-doc-menu input').fill('임대차');
  await expect(page.locator('.doq-doc-options button')).toHaveCount(1);
  await page.locator('.doq-doc-options button').first().click();
  await expect(page.locator('.doq-doc-picker')).toContainText('임대차계약서.pdf');
});

test('core screens fit a mobile viewport', async ({ page }) => {
  await mockApi(page);
  await page.setViewportSize({ width: 390, height: 844 });
  for (const path of ['/upload', '/drive', '/qa', '/profile']) {
    await page.goto(`http://localhost:3000${path}`);
    await page.waitForLoadState('networkidle');
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(overflow, `${path} has horizontal overflow on mobile`).toBeLessThanOrEqual(0);
    await page.screenshot({ path: `/tmp/doq-parity-mobile-${path.slice(1)}.png`, fullPage: true });
  }
});

test('dark screens keep readable contrast and geometry', async ({ page }) => {
  await mockApi(page);
  await page.setViewportSize({ width: 1440, height: 1000 });
  const targets = [
    ['/drive', '.doq-drive-head p', 'drive'],
    ['/terms', '.doq-terms-head p', 'terms'],
    ['/profile', '.doq-profile-copy > span', 'profile'],
    ['/admin', '.doq-admin-head p', 'admin'],
  ];

  for (const [path, textSelector, name] of targets) {
    await page.goto(`http://localhost:3000${path}`);
    await page.evaluate(() => {
      localStorage.setItem('theme', 'dark');
      document.documentElement.setAttribute('data-theme', 'dark');
      document.body.setAttribute('data-theme', 'dark');
    });
    const colors = await page.locator(textSelector).evaluate((element) => {
      const text = getComputedStyle(element).color;
      const surface = getComputedStyle(document.body).backgroundColor;
      return { text, surface };
    });
    expect(colors.text).not.toBe(colors.surface);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(overflow, `${path} has horizontal overflow in dark mode`).toBeLessThanOrEqual(0);
    await page.screenshot({ path: `/tmp/doq-parity-dark-${name}.png`, fullPage: true });
  }
});

test('text conversion opens the full document result design', async ({ page }) => {
  await mockApi(page);
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto('http://localhost:3000/upload');
  await page.locator('.doq-editor textarea').fill('본 계약을 해지하려면 종료 30일 전까지 서면 통보하여야 한다.');
  await page.getByRole('button', { name: /쉬운말로 검사하기/ }).click();

  await expect(page.locator('.doq-text-result-head')).toBeVisible();
  await expect(page.locator('.doq-result-tabs button')).toHaveCount(3);
  await expect(page.locator('.doq-reading mark')).toHaveCount(4);
  await expect(page.locator('.morph-paragraph').first().locator('.morph-layer')).toHaveCount(2);
  await expect(page.locator('.morph-easy.active')).toHaveCount(3);
  const wordMotion = await page.locator('.morph-easy-word').nth(1).evaluate((element) => {
    const style = getComputedStyle(element);
    return { duration: style.animationDuration, delay: style.animationDelay };
  });
  expect(wordMotion).toEqual({ duration: '0.55s', delay: '0.1s' });
  await expect(page.locator('.doq-changes > button')).toHaveCount(4);
  await expect(page.locator('.doq-easy-meter')).toContainText('4개 표현을 쉬운말로 바꿨어요');
  await expect(page.locator('.sidebar')).not.toContainText('문서 보기');
  await page.screenshot({ path: '/tmp/doq-text-result.png', fullPage: true });

  await page.getByRole('button', { name: '나란히 비교' }).click();
  await expect(page.locator('.doq-side-compare > div')).toHaveCount(3);
  await page.getByRole('button', { name: '요약·용어' }).click();
  await expect(page.locator('.doq-summary-box')).toContainText('계약 종료 통보 기한');
  await expect(page.locator('.doq-term-chips')).toContainText('위약금');

  await page.getByRole('button', { name: '쉬운말 보기' }).first().click();
  await page.locator('.doq-original-toggle').click();
  await expect(page.locator('.morph-original.active')).toHaveCount(3);
  await expect(page.locator('.morph-easy.active')).toHaveCount(0);

  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole('button', { name: '쉬운말 보기' }).first().click();
  const mobileOverflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(mobileOverflow).toBeLessThanOrEqual(0);
  await page.screenshot({ path: '/tmp/doq-text-result-mobile.png', fullPage: true });
});

test('text conversion with no changes keeps the easy meter at zero', async ({ page }) => {
  await mockApi(page);
  await page.goto('http://localhost:3000/upload');
  await page.locator('.doq-editor textarea').fill('이미 쉬운 문장입니다.');
  await page.getByRole('button', { name: /쉬운말로 검사하기/ }).click();

  await expect(page.locator('.doq-changes > button')).toHaveCount(0);
  await expect(page.locator('.doq-easy-meter > div span')).toHaveCSS('width', '0px');
  await expect(page.locator('.doq-easy-meter')).toContainText('원문을 유지했어요');
});

test('PDF viewer renders the file and synchronizes coordinate highlights', async ({ page }) => {
  await mockApi(page);
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto('http://localhost:3000/docs/doc-1');

  await expect(page.locator('.pdf-page-shell canvas')).toHaveCount(1);
  await expect(page.locator('.pdf-change-mark')).toHaveCount(3);
  await page.getByLabel('PDF 영역 너비').fill('90');
  await expect(page.locator('.doq-pdf-width-control output')).toHaveText('90%');
  await expect(page.locator('.doq-reader-grid')).toHaveClass(/wide-pdf-layout/);
  const stackedLayout = await page.evaluate(() => {
    const reader = document.querySelector('.doq-reader')?.getBoundingClientRect();
    const side = document.querySelector('.doq-reader-side')?.getBoundingClientRect();
    return { readerBottom: reader?.bottom || 0, sideTop: side?.top || 0 };
  });
  expect(stackedLayout.sideTop).toBeGreaterThan(stackedLayout.readerBottom);
  const initialPageWidth = await page.locator('.pdf-page-shell').evaluate((element) => element.getBoundingClientRect().width);
  await page.getByRole('button', { name: '글자 및 PDF 확대' }).click();
  await expect(page.locator('.doq-font-controls output')).toHaveText('109%');
  await expect.poll(() => page.locator('.pdf-page-shell').evaluate((element) => element.getBoundingClientRect().width))
    .toBeGreaterThan(initialPageWidth + 20);
  await expect(page.locator('.pdf-inline-replacement')).toHaveCount(0);
  await expect(page.locator('.pdf-change-mark.approximate')).toHaveCSS('border-bottom-style', 'solid');
  for (let index = 0; index < 4; index += 1) {
    await page.getByRole('button', { name: '글자 및 PDF 확대' }).click();
  }
  await expect(page.locator('.doq-font-controls output')).toHaveText('145%');
  await expect.poll(() => page.locator('.pdf-document-viewer').evaluate(
    (element) => element.scrollWidth - element.clientWidth,
  )).toBeGreaterThan(0);
  const horizontalScroll = await page.locator('.pdf-document-viewer').evaluate((element) => {
    element.scrollLeft = element.scrollWidth;
    return element.scrollLeft;
  });
  expect(horizontalScroll).toBeGreaterThan(0);
  await page.screenshot({ path: '/tmp/doq-pdf-easy-scroll.png', fullPage: true });
  const markMotion = await page.locator('.pdf-change-mark').nth(1).evaluate((element) => {
    const style = getComputedStyle(element);
    return { duration: style.animationDuration, delay: style.animationDelay };
  });
  expect(markMotion).toEqual({ duration: '0.55s', delay: '0.1s' });
  await expect.poll(() => page.locator('.pdf-page-shell canvas').evaluate((canvas: HTMLCanvasElement) => {
    const context = canvas.getContext('2d');
    if (!context || !canvas.width || !canvas.height) return 0;
    const pixels = context.getImageData(0, 0, canvas.width, canvas.height).data;
    let visible = 0;
    for (let index = 0; index < pixels.length; index += 4) {
      if (pixels[index + 3] > 0 && (pixels[index] < 245 || pixels[index + 1] < 245 || pixels[index + 2] < 245)) visible += 1;
      if (visible > 10) return visible;
    }
    return visible;
  })).toBeGreaterThan(10);

  await page.locator('.doq-change-list button').nth(1).click();
  await expect(page.locator('.pdf-change-mark[data-annotation-id="0-1-익일-다음 날"]')).toHaveClass(/selected/);
  await page.locator('.pdf-change-mark[data-annotation-id="1-0-상기-위"]').click();
  await expect(page.locator('.doq-change-list button').nth(2)).toHaveClass(/active/);

  await page.locator('.doq-reader-head button').click();
  await expect.poll(() => page.locator('.doq-document-stage').first().evaluate((element) => element.getAnimations().length)).toBeGreaterThan(0);
  await expect(page.locator('.doq-reader-head button')).toContainText('쉬운말 보기');
  await expect(page.locator('.doq-document-stage[data-view-mode="original"]')).toBeVisible();
  await expect(page.locator('.doq-document-stage')).toHaveCount(1);
  await expect(page.locator('.pdf-page-shell canvas')).toHaveCount(1);
  await expect(page.locator('.sidebar')).not.toContainText('문서 보기');
  await page.screenshot({ path: '/tmp/doq-pdf-document-viewer.png', fullPage: true });

  await page.setViewportSize({ width: 390, height: 844 });
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(0);
  await page.screenshot({ path: '/tmp/doq-pdf-document-viewer-mobile.png', fullPage: true });
});

test('Q&A starts with direct questions and can clear the current conversation', async ({ page }) => {
  await mockApi(page);
  await page.goto('http://localhost:3000/qa');

  await expect(page.locator('.doq-doc-picker')).toContainText('문서 선택 (선택사항)');
  await page.locator('.doq-doc-picker').click();
  await expect(page.locator('.doq-doc-options')).not.toContainText('문서 없이 질문');

  page.once('dialog', (dialog) => dialog.accept());
  await page.getByRole('button', { name: '대화 지우기' }).click();
  await expect(page.getByRole('status')).toContainText('대화 내용을 지웠습니다.');
});
