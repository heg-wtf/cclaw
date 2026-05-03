"use client";

import * as React from "react";
import { Bot } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
} from "@/components/ui/select";
import { BotAvatar } from "@/components/bot-avatar";
import type { BotSummary } from "@/lib/abyss-api";

interface Props {
  bots: BotSummary[];
  value: string | null;
  onChange: (botName: string) => void;
  disabled?: boolean;
}

export function BotSelector({ bots, value, onChange, disabled }: Props) {
  // shadcn's <SelectValue> renders the option's `value` prop verbatim, which
  // is the internal bot name (e.g. "cclawlifebot"). Look up the matching
  // BotSummary and render its display_name in the trigger ourselves so the
  // user sees the human-readable name, not the slug.
  const selected = bots.find((bot) => bot.name === value) ?? null;
  return (
    <Select
      value={value ?? undefined}
      onValueChange={(next) => {
        if (next) onChange(next);
      }}
      disabled={disabled || bots.length === 0}
    >
      <SelectTrigger className="w-[260px]">
        {selected ? (
          <BotAvatar
            botName={selected.name}
            displayName={selected.display_name}
            size="xs"
          />
        ) : (
          <Bot className="size-4 text-muted-foreground" />
        )}
        <span className="truncate text-sm">
          {selected ? selected.display_name : "Pick a bot to chat with"}
        </span>
      </SelectTrigger>
      <SelectContent>
        {bots.map((bot) => (
          <SelectItem key={bot.name} value={bot.name}>
            <div className="flex items-center gap-2">
              <BotAvatar
                botName={bot.name}
                displayName={bot.display_name}
                size="xs"
              />
              <div className="flex flex-col items-start">
                <span className="font-medium">{bot.display_name}</span>
                <span className="text-xs text-muted-foreground">{bot.type}</span>
              </div>
            </div>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
