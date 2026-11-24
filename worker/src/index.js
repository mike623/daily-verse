const UPSTREAM_ORIGIN = "https://mike623.github.io";
const UPSTREAM_BASE = "/daily-verse";
const PUBLIC_ORIGIN = "https://verse.namike.me";
const FORWARDED_HEADERS = [
  "accept",
  "accept-encoding",
  "accept-language",
  "if-none-match",
  "if-modified-since"
];

function rewriteLocation(location) {
  for (const scheme of ["https://", "http://"]) {
    const fullPrefix = `${scheme}mike623.github.io${UPSTREAM_BASE}`;
    if (location.startsWith(fullPrefix)) {
      const rest = location.slice(fullPrefix.length);
      return `${PUBLIC_ORIGIN}${rest || "/"}`;
    }
  }
  if (location.startsWith(UPSTREAM_BASE)) {
    const rest = location.slice(UPSTREAM_BASE.length);
    return rest || "/";
  }
  return location;
}

export default {
  async fetch(request) {
    if (request.method !== "GET" && request.method !== "HEAD") {
      return new Response("Method Not Allowed", {
        status: 405,
        headers: { Allow: "GET, HEAD" }
      });
    }

    const reqUrl = new URL(request.url);
    const upstreamUrl = new URL(
      `${UPSTREAM_ORIGIN}${UPSTREAM_BASE}${reqUrl.pathname}${reqUrl.search}`
    );

    const headers = new Headers();
    for (const name of FORWARDED_HEADERS) {
      const val = request.headers.get(name);
      if (val !== null) {
        headers.set(name, val);
      }
    }

    const upstream = await fetch(upstreamUrl.toString(), {
      method: request.method,
      headers,
      redirect: "manual"
    });

    const respHeaders = new Headers(upstream.headers);
    const location = respHeaders.get("location");
    if (location) {
      respHeaders.set("location", rewriteLocation(location));
    }

    return new Response(request.method === "HEAD" ? null : upstream.body, {
      status: upstream.status,
      statusText: upstream.statusText,
      headers: respHeaders
    });
  }
};
