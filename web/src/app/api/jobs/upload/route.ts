import { NextRequest } from "next/server";

const BACKEND = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8010";

export async function POST(request: NextRequest) {
  const contentType = request.headers.get("content-type") || "";

  const response = await fetch(`${BACKEND}/api/jobs/upload`, {
    method: "POST",
    headers: { "content-type": contentType },
    body: request.body,
    // @ts-expect-error duplex needed for streaming request body in Node.js
    duplex: "half",
  });

  return new Response(response.body, {
    status: response.status,
    headers: { "content-type": response.headers.get("content-type") || "application/json" },
  });
}
