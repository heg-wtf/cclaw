import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import fs from "fs";
import { getAbyssHome } from "@/lib/abyss";

export async function POST(request: NextRequest) {
  const { path: targetPath } = await request.json();

  if (!targetPath || typeof targetPath !== "string") {
    return NextResponse.json({ error: "Path is required" }, { status: 400 });
  }

  const abyssHome = getAbyssHome();
  const resolvedPath = targetPath.startsWith("/")
    ? targetPath
    : `${abyssHome}/${targetPath}`;

  if (!resolvedPath.startsWith(abyssHome)) {
    return NextResponse.json(
      { error: "Path must be within abyss home" },
      { status: 403 },
    );
  }

  if (!fs.existsSync(resolvedPath)) {
    return NextResponse.json({ error: "Path not found" }, { status: 404 });
  }

  exec(`open "${resolvedPath}"`, (error) => {
    if (error) console.error("Failed to open Finder:", error.message);
  });
  return NextResponse.json({ ok: true });
}
