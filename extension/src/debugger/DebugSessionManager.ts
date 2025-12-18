import * as vscode from 'vscode';

/**
 * Manages debug sessions and provides access to the active Python debug session.
 */
export class DebugSessionManager implements vscode.Disposable {
    private sessions: Map<string, vscode.DebugSession> = new Map();
    private activeSession: vscode.DebugSession | undefined;
    private activeFrameId: number | undefined;
    private readonly onSessionChangeEmitter = new vscode.EventEmitter<vscode.DebugSession | undefined>();
    private readonly onDebugStepEmitter = new vscode.EventEmitter<void>();
    private readonly disposables: vscode.Disposable[] = [];

    /**
     * Event fired when the active session changes.
     */
    readonly onSessionChange = this.onSessionChangeEmitter.event;

    /**
     * Event fired when the debugger stops (step, breakpoint, etc.).
     * Useful for auto-refreshing visualizations.
     */
    readonly onDebugStep = this.onDebugStepEmitter.event;

    constructor() {
        // Register debug adapter tracker to get frame information
        this.disposables.push(
            vscode.debug.registerDebugAdapterTrackerFactory('*', {
                createDebugAdapterTracker: (session) => {
                    if (this.isPythonSession(session)) {
                        return new DebugAdapterTracker(this, session);
                    }
                    return undefined;
                }
            })
        );
    }

    /**
     * Check if a session is a Python debug session.
     */
    private isPythonSession(session: vscode.DebugSession): boolean {
        return ['python', 'debugpy'].includes(session.type);
    }

    /**
     * Add a debug session.
     */
    addSession(session: vscode.DebugSession): void {
        this.sessions.set(session.id, session);
        if (!this.activeSession) {
            this.setActiveSession(session);
        }
    }

    /**
     * Remove a debug session.
     */
    removeSession(session: vscode.DebugSession): void {
        this.sessions.delete(session.id);
        if (this.activeSession?.id === session.id) {
            // Set to another session if available
            const remaining = Array.from(this.sessions.values());
            this.setActiveSession(remaining[0]);
        }
    }

    /**
     * Set the active debug session.
     */
    setActiveSession(session: vscode.DebugSession | undefined): void {
        this.activeSession = session;
        this.activeFrameId = undefined;
        this.onSessionChangeEmitter.fire(session);
    }

    /**
     * Get the current active session.
     */
    getActiveSession(): vscode.DebugSession | undefined {
        return this.activeSession;
    }

    /**
     * Set the active stack frame ID (called by tracker on stopped event).
     */
    setActiveFrameId(frameId: number): void {
        this.activeFrameId = frameId;
    }

    /**
     * Fire the debug step event (called by tracker when debugger stops).
     */
    fireDebugStep(): void {
        this.onDebugStepEmitter.fire();
    }

    /**
     * Get the active stack frame ID.
     */
    getActiveFrameId(): number | undefined {
        return this.activeFrameId;
    }

    /**
     * Evaluate an expression in the current debug context.
     */
    async evaluate(expression: string, context: 'watch' | 'repl' = 'repl'): Promise<string | undefined> {
        const session = this.activeSession;
        if (!session) {
            return undefined;
        }

        console.log('[PDV-DEBUG] evaluate - frameId:', this.activeFrameId, 'context:', context, 'expr:', expression.substring(0, 50));

        try {
            const response = await session.customRequest('evaluate', {
                expression,
                frameId: this.activeFrameId,
                context
            });
            return response.result;
        } catch (error) {
            const err = error as Error;
            throw new Error(`Evaluation failed: ${err.message}`);
        }
    }

    /**
     * Get completions for an expression.
     */
    async getCompletions(text: string, column: number): Promise<{ label: string; kind: number }[]> {
        const session = this.activeSession;
        if (!session) {
            return [];
        }

        try {
            const response = await session.customRequest('completions', {
                text,
                column,
                frameId: this.activeFrameId
            });

            return (response.targets || []).map((target: any) => ({
                label: String(target.label),
                kind: this.mapCompletionType(target.type)
            }));
        } catch {
            return [];
        }
    }

    private mapCompletionType(type: string | undefined): number {
        switch (type) {
            case 'method': return vscode.CompletionItemKind.Method;
            case 'function': return vscode.CompletionItemKind.Function;
            case 'class': return vscode.CompletionItemKind.Class;
            case 'module': return vscode.CompletionItemKind.Module;
            case 'property': return vscode.CompletionItemKind.Property;
            case 'field': return vscode.CompletionItemKind.Field;
            case 'variable': return vscode.CompletionItemKind.Variable;
            default: return vscode.CompletionItemKind.Text;
        }
    }

    dispose(): void {
        this.sessions.clear();
        this.activeSession = undefined;
        this.onSessionChangeEmitter.dispose();
        this.onDebugStepEmitter.dispose();
        for (const disposable of this.disposables) {
            disposable.dispose();
        }
    }
}

/**
 * Debug adapter tracker to capture stopped events and frame information.
 */
class DebugAdapterTracker implements vscode.DebugAdapterTracker {
    constructor(
        private readonly manager: DebugSessionManager,
        private readonly session: vscode.DebugSession
    ) {}

    onDidSendMessage(message: any): void {
        // Capture stopped events to track the current frame
        if (message.type === 'event' && message.event === 'stopped') {
            // When stopped, get the top frame
            this.updateActiveFrame();
        }
    }

    private async updateActiveFrame(): Promise<void> {
        try {
            const response = await this.session.customRequest('stackTrace', {
                threadId: 1,
                startFrame: 0,
                levels: 1
            });

            if (response.stackFrames && response.stackFrames.length > 0) {
                this.manager.setActiveFrameId(response.stackFrames[0].id);
                // Fire debug step event after frame is updated
                this.manager.fireDebugStep();
            }
        } catch {
            // Ignore errors
        }
    }
}
