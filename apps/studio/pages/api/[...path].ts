import type { NextApiRequest, NextApiResponse } from "next";

import { getApiBackendUrl } from "@/lib/api/config";
import { rewriteProxySetCookie } from "@/lib/api/proxy";

export const config = {
  api: {
    bodyParser: false,
    externalResolver: true,
    responseLimit: false,
  },
};

const HOP_BY_HOP = new Set([
  "connection",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailers",
  "transfer-encoding",
  "upgrade",
  "host",
]);

async function readBody(req: NextApiRequest): Promise<Buffer | undefined> {
  if (req.method === "GET" || req.method === "HEAD") {
    return undefined;
  }
  const chunks: Buffer[] = [];
  for await (const chunk of req) {
    chunks.push(typeof chunk === "string" ? Buffer.from(chunk) : chunk);
  }
  return chunks.length > 0 ? Buffer.concat(chunks) : undefined;
}

/** Pages Router proxy — reliable on Vercel (App Router catch-all returned 404). */
export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse,
): Promise<void> {
  let backendUrl: string;
  try {
    backendUrl = getApiBackendUrl();
  } catch {
    res.status(500).json({
      error: {
        code: "proxy_misconfigured",
        message: "API_BACKEND_URL is not configured",
      },
    });
    return;
  }

  const pathParam = req.query.path;
  const segments = Array.isArray(pathParam)
    ? pathParam
    : pathParam
      ? [pathParam]
      : [];
  const path = segments.join("/");
  const qs = req.url?.includes("?") ? req.url.slice(req.url.indexOf("?")) : "";
  const target = `${backendUrl}/${path}${qs}`;

  const headers = new Headers();
  for (const [key, value] of Object.entries(req.headers)) {
    if (!value || HOP_BY_HOP.has(key.toLowerCase())) {
      continue;
    }
    headers.set(key, Array.isArray(value) ? value.join(", ") : value);
  }

  const body = await readBody(req);

  const upstream = await fetch(target, {
    method: req.method,
    headers,
    body: body ? new Uint8Array(body) : undefined,
    redirect: "manual",
    cache: "no-store",
  });

  res.status(upstream.status);
  upstream.headers.forEach((value, key) => {
    if (key.toLowerCase() === "set-cookie") {
      return;
    }
    res.setHeader(key, value);
  });

  const setCookies =
    typeof upstream.headers.getSetCookie === "function"
      ? upstream.headers.getSetCookie()
      : [];

  if (setCookies.length > 0) {
    for (const cookie of setCookies) {
      res.appendHeader("Set-Cookie", rewriteProxySetCookie(cookie));
    }
  } else {
    const legacy = upstream.headers.get("set-cookie");
    if (legacy) {
      res.appendHeader("Set-Cookie", rewriteProxySetCookie(legacy));
    }
  }

  res.send(Buffer.from(await upstream.arrayBuffer()));
}
