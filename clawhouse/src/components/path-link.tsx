"use client";

interface PathLinkProps {
  path: string;
  displayPath?: string;
}

export function PathLink({ path, displayPath }: PathLinkProps) {
  const handleClick = async () => {
    await fetch("/api/open-finder", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path }),
    });
  };

  return (
    <button
      onClick={handleClick}
      className="text-xs text-blue-600 dark:text-blue-400 font-mono hover:underline cursor-pointer text-left"
      title={path}
    >
      {displayPath || path}
    </button>
  );
}
