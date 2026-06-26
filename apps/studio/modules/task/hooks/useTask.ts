import { useTaskContext } from "../contexts/task-context";

export function useTask() {
  const { sendMessage, answerAsk, stop, retry, clearError, toggleThinkingPanel, state, isStreaming } =
    useTaskContext();
  return {
    sendMessage,
    answerAsk,
    stop,
    retry,
    clearError,
    toggleThinkingPanel,
    streamingText: state.streamingText,
    thinkingText: state.thinkingText,
    toolCalls: state.toolCalls,
    agentBlocks: state.agentBlocks,
    thinkingPanelCollapsed: state.thinkingPanelCollapsed,
    artifacts: state.artifacts,
    currentTurnArtifactIds: state.currentTurnArtifactIds,
    taskMeta: state.taskMeta,
    streamError: state.error,
    streamStatus: state.streamStatus,
    pendingAsk: state.pendingAsk,
    isStreaming,
  };
}
