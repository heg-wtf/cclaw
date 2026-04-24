import { NextRequest, NextResponse } from "next/server";
import { getGlobalMemory, updateGlobalMemory } from "@/lib/abyss";

export async function GET() {
  const content = getGlobalMemory();
  return NextResponse.json({ content });
}

export async function PUT(request: NextRequest) {
  const { content } = await request.json();
  updateGlobalMemory(content);
  return NextResponse.json({ success: true });
}
