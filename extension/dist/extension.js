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
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const DebugSessionManager_1 = require("./debugger/DebugSessionManager");
const PythonVisualizationBackend_1 = require("./visualization/PythonVisualizationBackend");
const WebviewManager_1 = require("./webview/WebviewManager");
const WebviewServer_1 = require("./webview/WebviewServer");
const config_1 = require("./config");
let extension;
function activate(context) {
    console.log('Python Debug Visualizer is now active');
    extension = new PythonDebugVisualizerExtension(context);
    context.subscriptions.push(extension);
}
function deactivate() {
    if (extension) {
        extension.dispose();
        extension = undefined;
    }
}
class PythonDebugVisualizerExtension {
    constructor(context) {
        this.context = context;
        this.disposables = [];
        this.config = new config_1.Config();
        this.debugSessionManager = new DebugSessionManager_1.DebugSessionManager();
        this.visualizationBackend = new PythonVisualizationBackend_1.PythonVisualizationBackend(this.debugSessionManager, this.config);
        this.server = new WebviewServer_1.WebviewServer(this.visualizationBackend, this.config, this.debugSessionManager);
        this.webviewManager = new WebviewManager_1.WebviewManager(this.context, this.server, this.config);
        this.registerCommands();
        this.registerDebugListeners();
    }
    registerCommands() {
        this.disposables.push(vscode.commands.registerCommand('pythonDebugVisualizer.newView', () => this.createNewView()));
        this.disposables.push(vscode.commands.registerCommand('pythonDebugVisualizer.visualizeSelection', () => this.visualizeSelection()));
    }
    registerDebugListeners() {
        // Listen for debug session changes to auto-refresh
        this.disposables.push(vscode.debug.onDidChangeActiveDebugSession((session) => {
            if (session && this.isPythonSession(session)) {
                this.debugSessionManager.setActiveSession(session);
            }
        }));
        this.disposables.push(vscode.debug.onDidStartDebugSession((session) => {
            if (this.isPythonSession(session)) {
                this.debugSessionManager.addSession(session);
            }
        }));
        this.disposables.push(vscode.debug.onDidTerminateDebugSession((session) => {
            this.debugSessionManager.removeSession(session);
        }));
    }
    isPythonSession(session) {
        return ['python', 'debugpy'].includes(session.type);
    }
    async createNewView(expression) {
        await this.webviewManager.createView(expression);
    }
    async visualizeSelection() {
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
        }
        else {
            vscode.window.showWarningMessage('No text selected');
        }
    }
    dispose() {
        this.webviewManager.dispose();
        this.server.dispose();
        this.visualizationBackend.dispose();
        this.debugSessionManager.dispose();
        for (const disposable of this.disposables) {
            disposable.dispose();
        }
    }
}
//# sourceMappingURL=extension.js.map