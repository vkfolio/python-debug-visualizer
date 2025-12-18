import * as vscode from 'vscode';
import { DebugSessionManager } from './debugger/DebugSessionManager';
import { PythonVisualizationBackend } from './visualization/PythonVisualizationBackend';
import { WebviewManager } from './webview/WebviewManager';
import { WebviewServer } from './webview/WebviewServer';
import { Config } from './config';

let extension: PythonDebugVisualizerExtension | undefined;

export function activate(context: vscode.ExtensionContext) {
    console.log('Python Debug Visualizer is now active');

    extension = new PythonDebugVisualizerExtension(context);
    context.subscriptions.push(extension);
}

export function deactivate() {
    if (extension) {
        extension.dispose();
        extension = undefined;
    }
}

class PythonDebugVisualizerExtension implements vscode.Disposable {
    private readonly config: Config;
    private readonly debugSessionManager: DebugSessionManager;
    private readonly visualizationBackend: PythonVisualizationBackend;
    private readonly server: WebviewServer;
    private readonly webviewManager: WebviewManager;
    private readonly disposables: vscode.Disposable[] = [];

    constructor(private readonly context: vscode.ExtensionContext) {
        this.config = new Config();
        this.debugSessionManager = new DebugSessionManager();
        this.visualizationBackend = new PythonVisualizationBackend(
            this.debugSessionManager,
            this.config
        );
        this.server = new WebviewServer(this.visualizationBackend, this.config, this.debugSessionManager);
        this.webviewManager = new WebviewManager(this.context, this.server, this.config);

        this.registerCommands();
        this.registerDebugListeners();
    }

    private registerCommands(): void {
        this.disposables.push(
            vscode.commands.registerCommand(
                'pythonDebugVisualizer.newView',
                () => this.createNewView()
            )
        );

        this.disposables.push(
            vscode.commands.registerCommand(
                'pythonDebugVisualizer.visualizeSelection',
                () => this.visualizeSelection()
            )
        );
    }

    private registerDebugListeners(): void {
        // Listen for debug session changes to auto-refresh
        this.disposables.push(
            vscode.debug.onDidChangeActiveDebugSession((session) => {
                if (session && this.isPythonSession(session)) {
                    this.debugSessionManager.setActiveSession(session);
                }
            })
        );

        this.disposables.push(
            vscode.debug.onDidStartDebugSession((session) => {
                if (this.isPythonSession(session)) {
                    this.debugSessionManager.addSession(session);
                }
            })
        );

        this.disposables.push(
            vscode.debug.onDidTerminateDebugSession((session) => {
                this.debugSessionManager.removeSession(session);
            })
        );
    }

    private isPythonSession(session: vscode.DebugSession): boolean {
        return ['python', 'debugpy'].includes(session.type);
    }

    private async createNewView(expression?: string): Promise<void> {
        await this.webviewManager.createView(expression);
    }

    private async visualizeSelection(): Promise<void> {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showWarningMessage('No active editor');
            return;
        }

        const selection = editor.selection;
        let selectedText = editor.document.getText(selection);

        // If no selection, try to get word under cursor
        if (!selectedText) {
            const wordRange = editor.document.getWordRangeAtPosition(selection.active);
            if (wordRange) {
                selectedText = editor.document.getText(wordRange);
            }
        }

        if (selectedText) {
            await this.createNewView(selectedText);
        } else {
            vscode.window.showWarningMessage('No text selected');
        }
    }

    dispose(): void {
        this.webviewManager.dispose();
        this.server.dispose();
        this.visualizationBackend.dispose();
        this.debugSessionManager.dispose();

        for (const disposable of this.disposables) {
            disposable.dispose();
        }
    }
}
