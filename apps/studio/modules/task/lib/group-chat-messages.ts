import { stripAssistantContent } from "@/modules/task/lib/normalize-messages";
import type { DisplayMessage } from "@/modules/task/types/task-state";

export type UserChatItem = {
  kind: "user";
  message: DisplayMessage;
};

export type AssistantGroupChatItem = {
  kind: "assistant-group";
  messages: DisplayMessage[];
  /** Last assistant message in the group — used for actions, feedback, and stable keys. */
  message: DisplayMessage;
  content: string;
};

export type ChatDisplayItem = UserChatItem | AssistantGroupChatItem;

function visibleAssistantText(content: string): string {
  return stripAssistantContent(content).trim();
}

export function groupMessagesForDisplay(messages: DisplayMessage[]): ChatDisplayItem[] {
  const items: ChatDisplayItem[] = [];
  let index = 0;

  while (index < messages.length) {
    const current = messages[index];
    if (current.role === "user") {
      items.push({ kind: "user", message: current });
      index += 1;
      continue;
    }

    const group: DisplayMessage[] = [];
    while (index < messages.length && messages[index].role === "assistant") {
      group.push(messages[index]);
      index += 1;
    }

    const content = group
      .map((message) => visibleAssistantText(message.content))
      .filter(Boolean)
      .join("\n\n");

    const messageWithText =
      [...group].reverse().find((message) => visibleAssistantText(message.content)) ??
      group[group.length - 1];

    items.push({
      kind: "assistant-group",
      messages: group,
      message: messageWithText,
      content,
    });
  }

  return items;
}
