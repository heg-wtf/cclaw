import { NextRequest } from "next/server";

const CHAT_SERVER_PORT = process.env.ABYSS_CHAT_PORT || "3849";
const CHAT_SERVER_BASE = `http://127.0.0.1:${CHAT_SERVER_PORT}`;

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ name: string }> },
) {
  const { name } = await params;
  const body = await request.json();

  const upstream = await fetch(`${CHAT_SERVER_BASE}/bots/${name}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!upstream.ok || !upstream.body) {
    return new Response(
      JSON.stringify({ error: "Chat server error" }),
      { status: upstream.status, headers: { "Content-Type": "application/json" } },
    );
  }

  return new Response(upstream.body, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      "X-Accel-Buffering": "no",
    },
  });
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ name: string }> },
) {
  const { name } = await params;
  const { searchParams } = new URL(request.url);

  // /api/bots/{name}/chat?history=1 returns conversation history JSON
  if (searchParams.get("history") === "1") {
    try {
      const upstream = await fetch(`${CHAT_SERVER_BASE}/bots/${name}/history`);
      const data = await upstream.json();
      return Response.json(data);
    } catch {
      return Response.json({ history: "" });
    }
  }

  // Default: persistent SSE stream of real-time events
  const upstream = await fetch(`${CHAT_SERVER_BASE}/bots/${name}/stream`, {
    headers: { Accept: "text/event-stream" },
    // @ts-expect-error -- Node fetch supports duplex
    duplex: "half",
  });

  if (!upstream.ok || !upstream.body) {
    return new Response(null, { status: 502 });
  }

  return new Response(upstream.body, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      "X-Accel-Buffering": "no",
    },
  });
}
