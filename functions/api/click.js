/**
 * POST /api/click —— 出站点击埋点(Preply / Facebook)。
 *
 * 前端用 navigator.sendBeacon 发,不阻塞跳转;失败了就当没发生,绝不影响用户点击。
 * 只落"从哪个页面的哪个位置点去了哪儿"+ 国家码 + 设备粗类型:
 * 不存 IP、不存 UA、不存 referrer,也不下任何 cookie —— 回答"哪个海报位有效"
 * 不需要认人。
 *
 * 绑定: Pages 项目 learn-chinese → D1 binding CLICKS → readmandarin-clicks
 * 没绑定时静默返回 204,不报 500(部署顺序先后不影响线上)。
 */

const DESTS = new Set(["preply", "facebook"]);
const PLACEMENT = /^[a-z0-9-]{1,40}$/;
const MAX_BODY = 512;

const noContent = () => new Response(null, { status: 204 });

export async function onRequestPost({ request, env }) {
	// 同源才收 —— 别人拿这个端点往库里灌数据没有意义
	const origin = request.headers.get("origin");
	if (origin) {
		let ok = false;
		try {
			ok = new URL(origin).hostname === new URL(request.url).hostname;
		} catch (err) {
			ok = false;
		}
		if (!ok) return new Response(null, { status: 403 });
	}

	let body;
	try {
		const text = (await request.text()).slice(0, MAX_BODY);
		body = JSON.parse(text);
	} catch (err) {
		return noContent();
	}
	if (!body || typeof body !== "object") return noContent();

	const dest = String(body.dest || "");
	const placement = String(body.placement || "");
	if (!DESTS.has(dest) || !PLACEMENT.test(placement)) return noContent();

	let path = String(body.path || "/").slice(0, 120);
	if (path[0] !== "/") path = "/" + path;
	const level = /^[1-6]$/.test(String(body.level || "")) ? String(body.level) : null;
	const device = body.device === "m" ? "m" : "d";
	const country = (request.cf && request.cf.country) || null;

	if (!env.CLICKS) return noContent();   // 绑定还没配上,别炸

	const now = new Date().toISOString();
	try {
		await env.CLICKS.prepare(
			`INSERT INTO clicks (ts, day, dest, placement, path, level, country, device)
			 VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)`,
		)
			.bind(now, now.slice(0, 10), dest, placement, path, level, country, device)
			.run();
	} catch (err) {
		return noContent();   // 写不进去也不要让浏览器看见错误
	}
	return noContent();
}

/** GET /api/click —— 只用来确认 Function 和绑定都活着,不返回任何数据。 */
export async function onRequestGet({ env }) {
	return new Response(JSON.stringify({ ok: true, bound: !!env.CLICKS }), {
		headers: { "content-type": "application/json" },
	});
}
