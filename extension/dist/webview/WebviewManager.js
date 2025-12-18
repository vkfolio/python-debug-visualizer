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
exports.WebviewManager = void 0;
const vscode = __importStar(require("vscode"));
/**
 * Manages webview panels for the Python Debug Visualizer.
 */
class WebviewManager {
    constructor(context, server, config) {
        this.context = context;
        this.server = server;
        this.config = config;
        this.panels = new Set();
        this.serverStarted = false;
        this.serverUrl = '';
    }
    /**
     * Create a new webview panel.
     */
    async createView(expression) {
        // Start server if not already started
        if (!this.serverStarted) {
            this.serverUrl = await this.server.start();
            this.serverStarted = true;
        }
        // Create the webview panel
        const panel = vscode.window.createWebviewPanel('pythonDebugVisualizer', 'Python Debug Visualizer', vscode.ViewColumn.Beside, {
            enableScripts: true,
            retainContextWhenHidden: true,
            localResourceRoots: []
        });
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
    getWebviewContent(expression) {
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
    dispose() {
        for (const panel of this.panels) {
            panel.dispose();
        }
        this.panels.clear();
    }
}
exports.WebviewManager = WebviewManager;
//# sourceMappingURL=WebviewManager.js.map