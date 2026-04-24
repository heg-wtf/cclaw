import { NextRequest, NextResponse } from "next/server";
import {
  listLogFiles,
  getLogContent,
  deleteLogFiles,
  getDaemonLogInfo,
  truncateDaemonLogs,
} from "@/lib/abyss";

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const file = searchParams.get("file");

  if (file) {
    const offset = parseInt(searchParams.get("offset") || "0", 10);
    const limit = parseInt(searchParams.get("limit") || "500", 10);
    const result = getLogContent(file, offset, limit);
    return NextResponse.json(result);
  }

  const files = listLogFiles();
  const daemonLogs = getDaemonLogInfo();
  return NextResponse.json({ files, daemonLogs });
}

export async function DELETE(request: NextRequest) {
  const body = await request.json();

  if (body.action === "truncate-daemon") {
    const truncated = truncateDaemonLogs();
    return NextResponse.json({ truncated });
  }

  const { files } = body;
  if (!Array.isArray(files) || files.length === 0) {
    return NextResponse.json(
      { error: "files array is required" },
      { status: 400 },
    );
  }

  const deleted = deleteLogFiles(files);
  return NextResponse.json({ deleted });
}
