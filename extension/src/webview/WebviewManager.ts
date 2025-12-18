import * as vscode from 'vscode';
import { WebviewServer } from './WebviewServer';
import { Config } from '../config';

/**
 * Manages webview panels for the Python Debug Visualizer.
 */
export class WebviewManager implements vscode.Disposable {
    private panels: Set<vscode.WebviewPanel> = new Set();
    private serverStarted = false;
    private serverUrl: string = '';

    constructor(
        private readonly context: vscode.ExtensionContext,
        private readonly server: WebviewServer,
        private readonly config: Config
    ) {}

    /**
     * Create a new webview panel.
     */
    async createView(expression?: string): Promise<vscode.WebviewPanel> {
        // Start server if not already started
        if (!this.serverStarted) {
            this.serverUrl = await this.server.start();
            this.serverStarted = true;
        }

        // Create the webview panel
        const panel = vscode.window.createWebviewPanel(
            'pythonDebugVisualizer',
            'Python Debug Visualizer',
            vscode.ViewColumn.Beside,
            {
                enableScripts: true,
                retainContextWhenHidden: true,
                localResourceRoots: []
            }
        );

        // Set the HTML content
        panel.webview.html = this.getWebviewContent(expression);

        // Handle panel disposal
        panel.onDidDispose(() => {
            this.panels.delete(panel);
        });

        this.panels.add(panel);

        // If expression provided, set it on the server
        if (expression) {
            this.server.setExpression(expression);
        }

        return panel;
    }

    /**
     * Get the HTML content for the webview.
     */
    private getWebviewContent(expression?: string): string {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; frame-src ${this.serverUrl}; style-src 'unsafe-inline';">
    <title>Python Debug Visualizer</title>
    <style>
        html, body, iframe {
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100%;
            border: none;
            overflow: hidden;
        }
    </style>
</head>
<body>
    <iframe src="${this.serverUrl}${expression ? `?expression=${encodeURIComponent(expression)}` : ''}"></iframe>
</body>
</html>`;
    }

    dispose(): void {
        for (const panel of this.panels) {
            panel.dispose();
        }
        this.panels.clear();
    }
}
