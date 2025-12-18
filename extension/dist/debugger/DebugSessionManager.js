"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.DebugSessionManager = void 0;
const vscode = __importStar(require("vscode"));
/**
 * Manages debug sessions and provides access to the active Python debug session.
 */
class DebugSessionManager {
    constructor() {
        this.sessions = new Map();
        this.onSessionChangeEmitter = new vscode.EventEmitter();
        this.onDebugStepEmitter = new vscode.EventEmitter();
        this.disposables = [];
        /**
         * Event fired when the active session changes.
         */
        this.onSessionChange = this.onSessionChangeEmitter.event;
        /**
         * Event fired when the debugger stops (step, breakpoint, etc.).
         * Useful for auto-refreshing visualizations.
         */
        this.onDebugStep = this.onDebugStepEmitter.event;
        // Register debug adapter tracker to get frame information
        this.disposables.push(vscode.debug.registerDebugAdapterTrackerFactory('*', {
            createDebugAdapterTracker: (session) => {
                if (this.isPythonSession(session)) {
                    return new DebugAdapterTracker(this, session);
                }
                return undefined;
            }
        }));
    }
    /**
     * Check if a session is a Python debug session.
     */
    isPythonSession(session) {
        return ['python', 'debugpy'].includes(session.type);
    }
    /**
     * Add a debug session.
     */
    addSession(session) {
        this.sessions.set(session.id, session);
        if (!this.activeSession) {
            this.setActiveSession(session);
        }
    }
    /**
     * Remove a debug session.
     */
    removeSession(session) {
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
    setActiveSession(session) {
        this.activeSession = session;
        this.activeFrameId = undefined;
        this.onSessionChangeEmitter.fire(session);
    }
    /**
     * Get the current active session.
     */
    getActiveSession() {
        return this.activeSession;
    }
    /**
     * Set the active stack frame ID (called by tracker on stopped event).
     */
    setActiveFrameId(frameId) {
        this.activeFrameId = frameId;
    }
    /**
     * Fire the debug step event (called by tracker when debugger stops).
     */
    fireDebugStep() {
        this.onDebugStepEmitter.fire();
    }
    /**
     * Get the active stack frame ID.
     */
    getActiveFrameId() {
        return this.activeFrameId;
    }
    /**
     * Evaluate an expression in the current debug context.
     */
    async evaluate(expression, context = 'repl') {
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
        }
        catch (error) {
            const err = error;
            throw new Error(`Evaluation failed: ${err.message}`);
        }
    }
    /**
     * Get completions for an expression.
     */
    async getCompletions(text, column) {
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
            return (response.targets || []).map((target) => ({
                label: String(target.label),
                kind: this.mapCompletionType(target.type)
            }));
        }
        catch {
            return [];
        }
    }
    mapCompletionType(type) {
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
    dispose() {
        this.sessions.clear();
        this.activeSession = undefined;
        this.onSessionChangeEmitter.dispose();
        this.onDebugStepEmitter.dispose();
        for (const disposable of this.disposables) {
            disposable.dispose();
        }
    }
}
exports.DebugSessionManager = DebugSessionManager;
/**
 * Debug adapter tracker to capture stopped events and frame information.
 */
class DebugAdapterTracker {
    constructor(manager, session) {
        this.manager = manager;
        this.session = session;
    }
    onDidSendMessage(message) {
        // Capture stopped events to track the current frame
        if (message.type === 'event' && message.event === 'stopped') {
            // When stopped, get the top frame
            this.updateActiveFrame();
        }
    }
    async updateActiveFrame() {
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
        }
        catch {
            // Ignore errors
        }
    }
}
//# sourceMappingURL=DebugSessionManager.js.map