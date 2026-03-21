import { NextRequest, NextResponse } from "next/server";
import { getConversation, deleteConversation } from "@/lib/cclaw";

export async function GET(
  _request: NextRequest,
  {
    params,
  }: { params: Promise<{ name: string; chatId: string; date: string }> },
) {
  const { name, chatId, date } = await params;
  const content = getConversation(name, chatId, date);
  return NextResponse.json({ content });
}

export async function DELETE(
  _request: NextRequest,
  {
    params,
  }: { params: Promise<{ name: string; chatId: string; date: string }> },
) {
  const { name, chatId, date } = await params;
  const deleted = deleteConversation(name, chatId, date);
  if (!deleted) {
    return NextResponse.json({ error: "Not found" }, { status: 404 });
  }
  return NextResponse.json({ success: true });
}
