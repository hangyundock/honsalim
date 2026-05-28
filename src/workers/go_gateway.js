/**
 * go_gateway.js — Cloudflare Workers: /go/<slug> → 어필리에이트 deep link 302
 *
 * 출처: BACKEND §5 + DB §11 [확정] + POLICY §6 [확정].
 *
 * 동작:
 *   1. URL path에서 slug 추출
 *   2. D1 slug_map lookup → deeplink_url
 *   3. 클릭 로그(D1 clicks) INSERT — ctx.waitUntil (비차단)
 *   4. 302 Redirect → deeplink_url
 *
 * 보안·운영 (BACKEND §5-3):
 *   - 미등록 slug: 홈 302 (404 X, 봇 학습 차단)
 *   - IP 미저장 (PIPA 회피)
 *   - UA 원문 미저장 (SHA-256 첫 16 hex chars만)
 *   - referrer hostname만 (path 제거)
 *   - bot UA는 같은 redirect, D1에 bot_flag=1 (분석용)
 *
 * 배포: wrangler.toml + `wrangler deploy` (사용자 명시 승인 후).
 */

const HOMEPAGE_URL = "https://honsalim.com/";

export default {
  /**
   * @param {Request} request
   * @param {{ DB: D1Database }} env
   * @param {ExecutionContext} ctx
   */
  async fetch(request, env, ctx) {
    let slug;
    try {
      const url = new URL(request.url);
      slug = extractSlug(url.pathname);
    } catch (_e) {
      return Response.redirect(HOMEPAGE_URL, 302);
    }

    if (!slug) {
      return Response.redirect(HOMEPAGE_URL, 302);
    }

    let row = null;
    try {
      row = await env.DB.prepare(
        "SELECT deeplink_url FROM slug_map WHERE slug = ?",
      )
        .bind(slug)
        .first();
    } catch (_e) {
      // D1 장애 시에도 사용자는 홈으로 안전 fallback
      return Response.redirect(HOMEPAGE_URL, 302);
    }

    if (!row || !row.deeplink_url) {
      return Response.redirect(HOMEPAGE_URL, 302);
    }

    // 클릭 로그 — 비차단 (사용자 redirect 지연 X)
    const ua = request.headers.get("User-Agent") || "";
    const country = request.headers.get("CF-IPCountry") || "";
    const referrer = sanitizeReferrer(request.headers.get("Referer") || "");
    const botFlag = detectBot(ua) ? 1 : 0;

    ctx.waitUntil(
      (async () => {
        try {
          const uaHash = await hashUA(ua);
          await env.DB.prepare(
            "INSERT INTO clicks (slug, ts, ua_hash, country, referrer_domain, bot_flag) " +
              "VALUES (?, datetime('now'), ?, ?, ?, ?)",
          )
            .bind(slug, uaHash, country, referrer, botFlag)
            .run();
        } catch (_e) {
          // 로깅 실패는 사용자 경험에 영향 X
        }
      })(),
    );

    return Response.redirect(row.deeplink_url, 302);
  },
};

/**
 * '/go/<slug>' → '<slug>' (trailing slash·query 제거)
 * @param {string} pathname
 * @returns {string}
 */
export function extractSlug(pathname) {
  const idx = pathname.indexOf("/go/");
  if (idx < 0) return "";
  let slug = pathname.slice(idx + 4);
  // trailing slash 제거
  if (slug.endsWith("/")) slug = slug.slice(0, -1);
  // 추가 path segment 제거 (예: /go/abc/extra → 'abc')
  const slashIdx = slug.indexOf("/");
  if (slashIdx >= 0) slug = slug.slice(0, slashIdx);
  return slug;
}

/**
 * UA → SHA-256 첫 16 hex chars (BACKEND §5-3 PII 회피).
 * @param {string} ua
 * @returns {Promise<string>}
 */
export async function hashUA(ua) {
  const buf = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(ua),
  );
  return Array.from(new Uint8Array(buf))
    .slice(0, 8)
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

/**
 * referrer URL → hostname만 (path 제거, PIPA·POLICY §6 정합).
 * @param {string} ref
 * @returns {string}
 */
export function sanitizeReferrer(ref) {
  if (!ref) return "";
  try {
    return new URL(ref).hostname;
  } catch (_e) {
    return "";
  }
}

/**
 * UA 패턴으로 봇 추정 (BACKEND §5-3, 정확도 [관찰]).
 * @param {string} ua
 * @returns {boolean}
 */
export function detectBot(ua) {
  if (!ua) return false;
  return /bot|crawl|spider|slurp|preview|googlebot|bingbot|yandex|baiduspider|duckduck/i.test(
    ua,
  );
}
