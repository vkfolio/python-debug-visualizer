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
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.WebviewServer = void 0;
const http = __importStar(require("http"));
const path = __importStar(require("path"));
const ws_1 = require("ws");
const express_1 = __importDefault(require("express"));
/**
 * WebSocket server for communication between extension and webview.
 */
class WebviewServer {
    constructor(backend, config, sessionManager) {
        this.backend = backend;
        this.config = config;
        this.sessionManager = sessionManager;
        this.port = 0;
        this.connections = new Set();
        this.currentExpression = '';
        this.currentPointers = [];
        this.currentWatches = [];
        this.autoRefreshEnabled = true; // Default to enabled
        this.app = (0, express_1.default)();
        this.server = http.createServer(this.app);
        this.wss = new ws_1.WebSocketServer({ server: this.server });
        this.setupRoutes();
        this.setupWebSocket();
        this.setupDebugStepListener();
    }
    /**
     * Setup listener for debug step events (auto-refresh).
     */
    setupDebugStepListener() {
        if (this.sessionManager) {
            this.debugStepDisposable = this.sessionManager.onDebugStep(() => {
                console.log('[PDV-DEBUG] onDebugStep fired - autoRefresh:', this.autoRefreshEnabled, 'expression:', this.currentExpression);
                if (this.autoRefreshEnabled && this.currentExpression) {
                    console.log('[PDV-DEBUG] Triggering auto-refresh');
                    this.refreshVisualization();
                }
            });
        }
    }
    /**
     * Start the server and return the URL.
     */
    async start() {
        return new Promise((resolve) => {
            this.server.listen(0, '127.0.0.1', () => {
                const addr = this.server.address();
                if (addr && typeof addr === 'object') {
                    this.port = addr.port;
                    resolve(`http://127.0.0.1:${this.port}`);
                }
            });
        });
    }
    /**
     * Get the server URL.
     */
    getUrl() {
        return `http://127.0.0.1:${this.port}`;
    }
    /**
     * Setup Express routes.
     */
    setupRoutes() {
        // Serve static webview files
        const webviewPath = path.join(__dirname, '..', '..', 'webview');
        this.app.use(express_1.default.static(webviewPath));
        // Serve the main HTML page
        this.app.get('/', (req, res) => {
            res.send(this.getHtml());
        });
    }
    /**
     * Setup WebSocket handlers.
     */
    setupWebSocket() {
        this.wss.on('connection', (ws) => {
            this.connections.add(ws);
            // Send initial state
            this.sendState(ws);
            this.sendTheme(ws);
            ws.on('message', async (data) => {
                try {
                    const message = JSON.parse(data.toString());
                    await this.handleMessage(ws, message);
                }
                catch (error) {
                    console.error('Error handling message:', error);
                }
            });
            ws.on('close', () => {
                this.connections.delete(ws);
            });
        });
    }
    /**
     * Handle incoming WebSocket messages.
     */
    async handleMessage(ws, message) {
        switch (message.type) {
            case 'setExpression':
                if (message.expression !== undefined) {
                    this.currentExpression = message.expression;
                    await this.refreshVisualization();
                }
                break;
            case 'setPreferredExtractor':
                this.currentExtractorId = message.extractorId;
                await this.refreshVisualization();
                break;
            case 'refresh':
                await this.refreshVisualization();
                break;
            case 'getCompletions':
                if (message.text !== undefined && message.column !== undefined) {
                    const completions = await this.backend.getCompletions(message.text, message.column);
                    const response = {
                        type: 'completions',
                        completions,
                        requestId: message.requestId
                    };
                    ws.send(JSON.stringify(response));
                }
                break;
            case 'setPointers':
                if (message.pointers) {
                    this.currentPointers = message.pointers.filter(p => p.expression.trim() !== '');
                    await this.refreshVisualization();
                }
                break;
            case 'setAutoRefresh':
                this.autoRefreshEnabled = message.autoRefresh ?? false;
                break;
            case 'setWatches':
                if (message.watches) {
                    this.currentWatches = message.watches.filter(w => w.trim() !== '');
                    await this.refreshVisualization();
                }
                break;
        }
    }
    /**
     * Refresh the visualization and broadcast to all connections.
     */
    async refreshVisualization() {
        if (!this.currentExpression) {
            const state = {
                kind: 'error',
                message: 'Enter an expression to visualize'
            };
            this.broadcastState(state);
            return;
        }
        // Parse comma-separated expressions for side-by-side visualization
        const expressions = this.currentExpression.split(',').map(e => e.trim()).filter(e => e);
        if (expressions.length === 0) {
            const state = {
                kind: 'error',
                message: 'Enter an expression to visualize'
            };
            this.broadcastState(state);
            return;
        }
        // Multiple expressions - evaluate each separately
        if (expressions.length > 1) {
            const results = [];
            for (const expr of expressions) {
                let result;
                // Use pointer tracking if pointers are configured
                if (this.currentPointers.length > 0) {
                    result = await this.backend.getVisualizationWithPointers(expr, this.currentPointers, this.currentExtractorId);
                }
                else {
                    result = await this.backend.getVisualizationData(expr, this.currentExtractorId);
                }
                results.push({ expression: expr, result });
            }
            // Evaluate watch variables
            const watchValues = await this.evaluateWatches();
            // Broadcast multiple results
            this.broadcastMultipleStates(results, watchValues);
            return;
        }
        // Single expression - use original logic
        let result;
        // Use pointer tracking if pointers are configured
        if (this.currentPointers.length > 0) {
            result = await this.backend.getVisualizationWithPointers(this.currentExpression, this.currentPointers, this.currentExtractorId);
        }
        else {
            result = await this.backend.getVisualizationData(this.currentExpression, this.currentExtractorId);
        }
        // Evaluate watch variables
        const watchValues = await this.evaluateWatches();
        // Add watch values to the result
        this.broadcastState(result, watchValues);
    }
    /**
     * Evaluate all watch expressions.
     */
    async evaluateWatches() {
        if (this.currentWatches.length === 0 || !this.sessionManager) {
            return [];
        }
        const watchValues = [];
        for (const watch of this.currentWatches) {
            try {
                const value = await this.sessionManager.evaluate(watch, 'watch');
                watchValues.push({
                    name: watch,
                    value: value || 'undefined'
                });
            }
            catch (error) {
                watchValues.push({
                    name: watch,
                    value: '<error>'
                });
            }
        }
        return watchValues;
    }
    /**
     * Send state to a specific connection.
     */
    sendState(ws) {
        const message = {
            type: 'state',
            state: {
                kind: 'error',
                message: 'Enter an expression to visualize'
            }
        };
        ws.send(JSON.stringify(message));
    }
    /**
     * Send theme to a specific connection.
     */
    sendTheme(ws) {
        const message = {
            type: 'theme',
            theme: this.config.theme
        };
        ws.send(JSON.stringify(message));
    }
    /**
     * Broadcast state to all connections.
     */
    broadcastState(state, watchValues) {
        // Add watch values to the state
        const stateWithWatches = watchValues && watchValues.length > 0
            ? { ...state, watchValues }
            : state;
        const message = {
            type: 'state',
            state: stateWithWatches
        };
        const data = JSON.stringify(message);
        for (const ws of this.connections) {
            if (ws.readyState === ws_1.WebSocket.OPEN) {
                ws.send(data);
            }
        }
    }
    /**
     * Broadcast multiple states for side-by-side visualization.
     */
    broadcastMultipleStates(results, watchValues) {
        const message = {
            type: 'state',
            states: results,
            state: watchValues && watchValues.length > 0 ? { kind: 'data', watchValues } : undefined
        };
        const data = JSON.stringify(message);
        for (const ws of this.connections) {
            if (ws.readyState === ws_1.WebSocket.OPEN) {
                ws.send(data);
            }
        }
    }
    /**
     * Set the expression to visualize.
     */
    setExpression(expression) {
        this.currentExpression = expression;
        this.refreshVisualization();
    }
    /**
     * Get the HTML for the webview.
     */
    getHtml() {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Python Debug Visualizer</title>
    <!-- Visualization Libraries -->
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <script src="https://unpkg.com/vis-network@9.1.6/standalone/umd/vis-network.min.js"></script>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            padding: 0;
            background: var(--bg-color);
            color: var(--text-color);
            min-height: 100vh;
        }
        body.dark {
            --bg-color: #1e1e1e;
            --bg-secondary: #252526;
            --bg-tertiary: #2d2d2d;
            --text-color: #cccccc;
            --text-muted: #858585;
            --border-color: #3c3c3c;
            --input-bg: #3c3c3c;
            --input-focus: #094771;
            --button-bg: #0e639c;
            --button-hover: #1177bb;
            --button-secondary: #3c3c3c;
            --accent-color: #0078d4;
            --success-color: #4ec9b0;
            --warning-color: #dcdcaa;
            --error-color: #f14c4c;
            --node-color: #4a9eff;
            --node-highlight: #7ab8ff;
            --edge-color: #666666;
            --tree-line: #555555;
            --table-header-bg: #2d2d2d;
            --table-row-alt: #252525;
            --shadow: 0 2px 8px rgba(0,0,0,0.3);
        }
        body.light {
            --bg-color: #f3f3f3;
            --bg-secondary: #ffffff;
            --bg-tertiary: #f8f8f8;
            --text-color: #333333;
            --text-muted: #6e6e6e;
            --border-color: #e0e0e0;
            --input-bg: #ffffff;
            --input-focus: #0078d4;
            --button-bg: #0078d4;
            --button-hover: #106ebe;
            --button-secondary: #e0e0e0;
            --accent-color: #0078d4;
            --success-color: #16825d;
            --warning-color: #c19c00;
            --error-color: #d32f2f;
            --node-color: #0078d4;
            --node-highlight: #2080e0;
            --edge-color: #999999;
            --tree-line: #cccccc;
            --table-header-bg: #f0f0f0;
            --table-row-alt: #f8f8f8;
            --shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        /* Main Layout */
        .app-container {
            display: flex;
            flex-direction: column;
            height: 100vh;
        }

        /* Toolbar */
        .toolbar {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 12px;
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border-color);
            flex-shrink: 0;
        }
        .toolbar-group {
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .toolbar-divider {
            width: 1px;
            height: 24px;
            background: var(--border-color);
            margin: 0 6px;
        }

        /* Expression Input */
        .expression-input {
            flex: 1;
            min-width: 200px;
            padding: 6px 12px;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            background: var(--input-bg);
            color: var(--text-color);
            font-family: 'Fira Code', 'Cascadia Code', 'Consolas', monospace;
            font-size: 13px;
            transition: border-color 0.15s, box-shadow 0.15s;
        }
        .expression-input:focus {
            outline: none;
            border-color: var(--accent-color);
            box-shadow: 0 0 0 1px var(--accent-color);
        }
        .expression-input::placeholder {
            color: var(--text-muted);
        }

        /* Buttons */
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 4px;
            padding: 6px 12px;
            border: none;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            transition: background 0.15s, opacity 0.15s;
            white-space: nowrap;
        }
        .btn-primary {
            background: var(--button-bg);
            color: white;
        }
        .btn-primary:hover {
            background: var(--button-hover);
        }
        .btn-secondary {
            background: var(--button-secondary);
            color: var(--text-color);
        }
        .btn-secondary:hover {
            opacity: 0.8;
        }
        .btn-icon {
            padding: 6px 8px;
            min-width: 32px;
        }
        .btn-danger {
            background: var(--error-color);
            color: white;
        }
        .btn-danger:hover {
            opacity: 0.9;
        }

        /* Select */
        .select {
            padding: 6px 28px 6px 10px;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            background: var(--input-bg);
            color: var(--text-color);
            font-size: 12px;
            cursor: pointer;
            appearance: none;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23858585' d='M3 4.5L6 8l3-3.5H3z'/%3E%3C/svg%3E");
            background-repeat: no-repeat;
            background-position: right 8px center;
        }
        .select:focus {
            outline: none;
            border-color: var(--accent-color);
        }

        /* Main Content Area */
        .main-content {
            display: flex;
            flex: 1;
            overflow: hidden;
        }

        /* Sidebar */
        .sidebar {
            width: 280px;
            background: var(--bg-secondary);
            border-right: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            flex-shrink: 0;
            overflow-y: auto;
        }

        /* Collapsible Sections */
        .section {
            border-bottom: 1px solid var(--border-color);
        }
        .section-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 12px;
            cursor: pointer;
            user-select: none;
            transition: background 0.15s;
        }
        .section-header:hover {
            background: var(--bg-tertiary);
        }
        .section-title {
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-muted);
        }
        .section-toggle {
            font-size: 10px;
            color: var(--text-muted);
            transition: transform 0.2s;
        }
        .section.expanded .section-toggle {
            transform: rotate(90deg);
        }
        .section-body {
            display: none;
            padding: 0 12px 12px 12px;
        }
        .section.expanded .section-body {
            display: block;
        }

        /* Form Controls */
        .form-row {
            display: flex;
            gap: 6px;
            margin-bottom: 8px;
            align-items: center;
        }
        .form-input {
            flex: 1;
            padding: 6px 10px;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            background: var(--input-bg);
            color: var(--text-color);
            font-family: 'Fira Code', 'Consolas', monospace;
            font-size: 12px;
        }
        .form-input:focus {
            outline: none;
            border-color: var(--accent-color);
        }
        .form-select {
            padding: 6px 8px;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            background: var(--input-bg);
            color: var(--text-color);
            font-size: 11px;
            cursor: pointer;
        }
        .form-color {
            width: 32px;
            height: 28px;
            padding: 2px;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            cursor: pointer;
            background: var(--input-bg);
        }
        .form-btn-remove {
            padding: 4px 8px;
            border: none;
            border-radius: 4px;
            background: transparent;
            color: var(--text-muted);
            cursor: pointer;
            font-size: 16px;
            line-height: 1;
        }
        .form-btn-remove:hover {
            background: var(--error-color);
            color: white;
        }
        .form-btn-add {
            width: 100%;
            padding: 6px;
            border: 1px dashed var(--border-color);
            border-radius: 4px;
            background: transparent;
            color: var(--text-muted);
            cursor: pointer;
            font-size: 11px;
            transition: all 0.15s;
        }
        .form-btn-add:hover {
            border-color: var(--accent-color);
            color: var(--accent-color);
        }

        /* Checkbox */
        .checkbox-row {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 0;
            border-top: 1px solid var(--border-color);
            margin-top: 8px;
        }
        .checkbox-label {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 12px;
            color: var(--text-color);
            cursor: pointer;
        }
        .checkbox-label input {
            cursor: pointer;
            accent-color: var(--accent-color);
        }

        /* Visualization Panel */
        .vis-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            background: var(--bg-color);
        }

        /* Watch Display */
        .watch-panel {
            padding: 8px 12px;
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border-color);
            display: none;
        }
        .watch-panel.visible {
            display: block;
        }
        .watch-panel-title {
            font-size: 10px;
            text-transform: uppercase;
            color: var(--text-muted);
            margin-bottom: 6px;
        }
        .watch-items {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }
        .watch-item {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            background: var(--bg-tertiary);
            border-radius: 4px;
            font-family: 'Fira Code', 'Consolas', monospace;
            font-size: 12px;
        }
        .watch-name {
            color: var(--success-color);
        }
        .watch-equals {
            color: var(--text-muted);
        }
        .watch-value {
            color: var(--warning-color);
        }

        /* Visualization Area */
        .visualization {
            flex: 1;
            overflow: auto;
            position: relative;
        }
        .visualization-content {
            padding: 16px;
        }
        .error {
            color: var(--error-color);
            white-space: pre-wrap;
            font-family: monospace;
            padding: 16px;
        }
        .message {
            color: var(--text-muted);
            padding: 24px;
            text-align: center;
            font-size: 14px;
        }
        pre {
            white-space: pre-wrap;
            word-wrap: break-word;
            font-family: 'Fira Code', 'Consolas', monospace;
            font-size: 13px;
            line-height: 1.5;
        }

        /* Graph Container */
        #graph-container {
            width: 100%;
            height: 450px;
            background: var(--bg-color);
        }

        /* Plotly Container */
        #plotly-container {
            width: 100%;
            min-height: 400px;
        }

        /* Table Styles */
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }
        th, td {
            border: 1px solid var(--border-color);
            padding: 8px 12px;
            text-align: left;
        }
        th {
            background: var(--table-header-bg);
            font-weight: 600;
            position: sticky;
            top: 0;
        }
        tr:nth-child(even) {
            background: var(--table-row-alt);
        }
        tr:hover {
            background: var(--input-bg);
        }

        /* Tree Styles - Circular nodes with diagonal lines */
        .tree-container {
            padding: 20px;
            overflow: auto;
            display: flex;
            justify-content: center;
        }
        .tree-node {
            display: flex;
            flex-direction: column;
            align-items: center;
            position: relative;
            padding: 0 5px;
        }
        .tree-node-content {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 36px;
            height: 36px;
            border-radius: 50%;
            cursor: pointer;
            background: var(--input-bg);
            border: 2px solid var(--node-color);
            color: var(--node-color);
            font-weight: 600;
            transition: all 0.2s ease;
            z-index: 1;
        }
        .tree-node-content:hover {
            transform: scale(1.1);
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }
        .tree-toggle {
            display: none;
        }
        .tree-node-label {
            font-family: 'Fira Code', 'Consolas', monospace;
            font-size: 14px;
        }
        .tree-children {
            display: flex;
            flex-direction: row;
            justify-content: center;
            margin-top: 30px;
            position: relative;
        }
        /* Diagonal lines using SVG-like approach with pseudo elements */
        .tree-children > .tree-node::before {
            content: '';
            position: absolute;
            top: -30px;
            left: 50%;
            width: 2px;
            height: 30px;
            background: var(--tree-line);
            transform-origin: top center;
        }
        /* Left child - diagonal line */
        .tree-children > .tree-node:first-child:not(:only-child)::before {
            transform: rotate(-25deg);
            left: calc(50% + 10px);
        }
        /* Right child - diagonal line */
        .tree-children > .tree-node:last-child:not(:only-child)::before {
            transform: rotate(25deg);
            left: calc(50% - 10px);
        }
        /* Only child - straight line */
        .tree-children > .tree-node:only-child::before {
            transform: none;
        }
        .tree-children.collapsed {
            display: none;
        }
        .tree-root::before {
            display: none;
        }
        .tree-node-emphasis-style1 {
            color: inherit;
        }
        .tree-node-emphasis-style2 {
            color: inherit;
            opacity: 0.8;
        }
        .tree-node-emphasis-style3 {
            color: var(--text-color);
            opacity: 0.5;
            font-style: italic;
            font-size: 11px;
        }
        /* Null nodes */
        .tree-node-content.null-node {
            background: transparent;
            border-style: dashed;
            border-color: var(--border-color);
            color: var(--text-color);
            opacity: 0.4;
            font-size: 10px;
            width: 28px;
            height: 28px;
        }
        /* Marked/highlighted nodes */
        .tree-node-content.marked {
            border-width: 3px;
            box-shadow: 0 0 12px currentColor;
            transform: scale(1.15);
        }

        /* Grid Styles */
        .grid-container {
            overflow: auto;
        }
        .grid-table {
            border-collapse: collapse;
        }
        .grid-table th,
        .grid-table td {
            min-width: 50px;
            text-align: center;
            padding: 6px 10px;
        }
        .grid-cell-marked {
            background: rgba(255, 200, 0, 0.3) !important;
            font-weight: bold;
        }

        /* Maze Grid Styles */
        .maze-grid {
            border-spacing: 2px;
            border-collapse: separate;
        }
        .maze-grid td {
            min-width: 36px;
            height: 36px;
            padding: 4px;
            border-radius: 4px;
            position: relative;
            transition: all 0.15s ease;
        }
        .maze-cell {
            position: relative;
        }
        .maze-cell .cell-content {
            font-size: 11px;
            font-weight: 600;
        }
        .cell-marker-label {
            position: absolute;
            top: 2px;
            right: 3px;
            font-size: 8px;
            font-weight: bold;
            color: #fff;
            text-shadow: 0 0 2px rgba(0,0,0,0.8);
        }
        .maze-current {
            animation: pulse-current 1s ease-in-out infinite;
        }
        @keyframes pulse-current {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.1); }
        }
        /* Maze cell colors - walls vs paths */
        .maze-wall {
            background: #333333 !important;
            color: #666 !important;
        }
        .maze-path {
            background: #ffffff !important;
            color: #333 !important;
        }
        body.dark .maze-path {
            background: #2d2d2d !important;
            color: #ccc !important;
        }
        .maze-visited {
            background: #90caf9 !important;
        }
        body.dark .maze-visited {
            background: #1565c0 !important;
        }
        .maze-in-path {
            background: #4caf50 !important;
            color: #fff !important;
        }

        /* Pointer Configuration Styles */
        .pointer-config {
            margin-bottom: 12px;
            padding: 12px;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            background: var(--input-bg);
        }
        .pointer-config-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
            cursor: pointer;
        }
        .pointer-config-header h3 {
            font-size: 12px;
            text-transform: uppercase;
            opacity: 0.7;
            margin: 0;
        }
        .pointer-config-toggle {
            font-size: 10px;
            opacity: 0.7;
        }
        .pointer-config-body {
            display: none;
        }
        .pointer-config-body.expanded {
            display: block;
        }
        .pointer-row {
            display: flex;
            gap: 8px;
            margin-bottom: 6px;
            align-items: center;
        }
        .pointer-row input[type="text"] {
            flex: 1;
            padding: 6px 10px;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            background: var(--bg-color);
            color: var(--text-color);
            font-family: 'Fira Code', 'Consolas', monospace;
            font-size: 13px;
        }
        .pointer-row input[type="color"] {
            width: 36px;
            height: 30px;
            padding: 2px;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            cursor: pointer;
        }
        .pointer-row button {
            padding: 6px 10px;
            border: none;
            border-radius: 4px;
            background: var(--border-color);
            color: var(--text-color);
            cursor: pointer;
            font-size: 14px;
        }
        .pointer-row button:hover {
            background: var(--button-bg);
            color: white;
        }
        .add-pointer-btn {
            width: 100%;
            padding: 6px;
            margin-top: 4px;
            border: 1px dashed var(--border-color);
            border-radius: 4px;
            background: transparent;
            color: var(--text-color);
            cursor: pointer;
            font-size: 12px;
            opacity: 0.7;
        }
        .add-pointer-btn:hover {
            opacity: 1;
            border-color: var(--button-bg);
            color: var(--button-bg);
        }
        .auto-refresh-row {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-top: 8px;
            padding-top: 8px;
            border-top: 1px solid var(--border-color);
        }
        .auto-refresh-row label {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 12px;
            cursor: pointer;
        }
        .auto-refresh-row input[type="checkbox"] {
            cursor: pointer;
        }

        /* Marked node styles for graphs */
        .node-marker-label {
            font-size: 10px;
            font-weight: bold;
            padding: 2px 4px;
            border-radius: 2px;
            margin-top: 2px;
        }

        /* Pointer type selector */
        .pointer-row select {
            padding: 6px 8px;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            background: var(--bg-color);
            color: var(--text-color);
            font-size: 12px;
            cursor: pointer;
        }

        /* Watch Variables Styles */
        .watch-config {
            margin-bottom: 12px;
            padding: 12px;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            background: var(--input-bg);
        }
        .watch-config-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
            cursor: pointer;
        }
        .watch-config-header h3 {
            font-size: 12px;
            text-transform: uppercase;
            opacity: 0.7;
            margin: 0;
        }
        .watch-config-toggle {
            font-size: 10px;
            opacity: 0.7;
        }
        .watch-config-body {
            display: none;
        }
        .watch-config-body.expanded {
            display: block;
        }
        .watch-row {
            display: flex;
            gap: 8px;
            margin-bottom: 6px;
            align-items: center;
        }
        .watch-row input[type="text"] {
            flex: 1;
            padding: 6px 10px;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            background: var(--bg-color);
            color: var(--text-color);
            font-family: 'Fira Code', 'Consolas', monospace;
            font-size: 13px;
        }
        .watch-row button {
            padding: 6px 10px;
            border: none;
            border-radius: 4px;
            background: var(--border-color);
            color: var(--text-color);
            cursor: pointer;
            font-size: 14px;
        }
        .watch-row button:hover {
            background: var(--button-bg);
            color: white;
        }
        .add-watch-btn {
            width: 100%;
            padding: 6px;
            margin-top: 4px;
            border: 1px dashed var(--border-color);
            border-radius: 4px;
            background: transparent;
            color: var(--text-color);
            cursor: pointer;
            font-size: 12px;
            opacity: 0.7;
        }
        .add-watch-btn:hover {
            opacity: 1;
            border-color: var(--button-bg);
            color: var(--button-bg);
        }
        .watch-display {
            margin-bottom: 12px;
            padding: 12px;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            background: var(--input-bg);
        }
        .watch-display h4 {
            font-size: 11px;
            text-transform: uppercase;
            opacity: 0.6;
            margin: 0 0 8px 0;
        }
        .watch-values {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
        }
        .watch-item {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            background: var(--bg-color);
            border-radius: 4px;
            font-family: 'Fira Code', 'Consolas', monospace;
            font-size: 13px;
        }
        .watch-item-name {
            color: #9cdcfe;
        }
        .watch-item-value {
            color: #ce9178;
        }

        /* Array Visualization Styles */
        .array-container {
            padding: 16px;
            overflow-x: auto;
        }
        .array-view {
            display: flex;
            flex-direction: column;
            align-items: flex-start;
            gap: 4px;
        }
        .array-indices {
            display: flex;
            gap: 2px;
        }
        .array-index {
            width: 50px;
            text-align: center;
            font-size: 11px;
            color: var(--text-color);
            opacity: 0.6;
        }
        .array-cells {
            display: flex;
            gap: 2px;
        }
        .array-cell {
            width: 50px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 2px solid var(--border-color);
            border-radius: 4px;
            background: var(--input-bg);
            font-family: 'Fira Code', 'Consolas', monospace;
            font-size: 14px;
            transition: all 0.2s ease;
        }
        .array-cell.marked {
            border-width: 3px;
            font-weight: bold;
            box-shadow: 0 0 10px currentColor;
        }
        .array-markers {
            display: flex;
            gap: 2px;
        }
        .array-marker {
            width: 50px;
            text-align: center;
            font-size: 10px;
            font-weight: bold;
            padding: 2px 0;
        }
        .array-info {
            margin-top: 8px;
            font-size: 12px;
            color: var(--text-color);
            opacity: 0.7;
        }

        /* Multi-expression side-by-side layout */
        .multi-vis-container {
            display: flex;
            gap: 16px;
            flex-wrap: wrap;
        }
        .vis-panel {
            flex: 1;
            min-width: 300px;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            overflow: hidden;
        }
        .vis-panel-header {
            padding: 8px 12px;
            background: var(--table-header-bg);
            border-bottom: 1px solid var(--border-color);
            font-family: 'Fira Code', 'Consolas', monospace;
            font-size: 13px;
            font-weight: 600;
        }
        .vis-panel-content {
            min-height: 350px;
            position: relative;
        }
        .vis-panel-content .visualization-content {
            padding: 16px;
        }
        .vis-panel-content #graph-container,
        .vis-panel-content .graph-container {
            height: 350px !important;
        }
    </style>
</head>
<body class="dark">
    <div class="app-container">
        <!-- Toolbar -->
        <div class="toolbar">
            <input type="text" class="expression-input" id="expression" placeholder="Enter expression (e.g., root, nums) — use comma for side-by-side">
            <div class="toolbar-group">
                <select class="select" id="extractor" title="Visualization type">
                    <option value="">Auto</option>
                </select>
                <button class="btn btn-primary" id="refresh" title="Refresh (Enter)">Refresh</button>
                <button class="btn btn-secondary" id="reset" title="Reset all">Reset</button>
            </div>
        </div>

        <!-- Main Content -->
        <div class="main-content">
            <!-- Sidebar -->
            <div class="sidebar">
                <!-- Pointer Tracking Section -->
                <div class="section expanded" id="pointer-section">
                    <div class="section-header" id="pointer-config-header">
                        <span class="section-title">Pointer Tracking</span>
                        <span class="section-toggle">▶</span>
                    </div>
                    <div class="section-body" id="pointer-config-body">
                        <div id="pointer-rows">
                            <div class="form-row" data-index="0">
                                <input type="text" class="form-input" placeholder="e.g., slow" data-field="expression">
                                <select class="form-select" data-field="type" title="Pointer type">
                                    <option value="object">Object</option>
                                    <option value="index">Index</option>
                                </select>
                                <input type="color" class="form-color" value="#22c55e" data-field="color">
                                <button class="form-btn-remove" title="Remove">×</button>
                            </div>
                            <div class="form-row" data-index="1">
                                <input type="text" class="form-input" placeholder="e.g., fast" data-field="expression">
                                <select class="form-select" data-field="type" title="Pointer type">
                                    <option value="object">Object</option>
                                    <option value="index">Index</option>
                                </select>
                                <input type="color" class="form-color" value="#ef4444" data-field="color">
                                <button class="form-btn-remove" title="Remove">×</button>
                            </div>
                        </div>
                        <button class="form-btn-add" id="add-pointer">+ Add Pointer</button>
                        <div class="checkbox-row">
                            <label class="checkbox-label">
                                <input type="checkbox" id="auto-refresh" checked>
                                Auto-refresh on step
                            </label>
                        </div>
                    </div>
                </div>

                <!-- Watch Variables Section -->
                <div class="section expanded" id="watch-section">
                    <div class="section-header" id="watch-config-header">
                        <span class="section-title">Watch Variables</span>
                        <span class="section-toggle">▶</span>
                    </div>
                    <div class="section-body" id="watch-config-body">
                        <div id="watch-rows">
                            <div class="form-row" data-index="0">
                                <input type="text" class="form-input" placeholder="e.g., i, count" data-field="expression">
                                <button class="form-btn-remove" title="Remove">×</button>
                            </div>
                        </div>
                        <button class="form-btn-add" id="add-watch">+ Add Watch</button>
                    </div>
                </div>
            </div>

            <!-- Visualization Container -->
            <div class="vis-container">
                <!-- Watch Panel (shows values) -->
                <div class="watch-panel" id="watch-display">
                    <div class="watch-panel-title">Watch Values</div>
                    <div class="watch-items" id="watch-items"></div>
                </div>

                <!-- Visualization Area -->
                <div class="visualization" id="visualization">
                    <p class="message">Enter an expression to visualize</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        const ws = new WebSocket('ws://' + window.location.host);
        const expressionInput = document.getElementById('expression');
        const extractorSelect = document.getElementById('extractor');
        const refreshButton = document.getElementById('refresh');
        const resetButton = document.getElementById('reset');
        const visualization = document.getElementById('visualization');
        const pointerSection = document.getElementById('pointer-section');
        const pointerConfigHeader = document.getElementById('pointer-config-header');
        const pointerConfigBody = document.getElementById('pointer-config-body');
        const pointerRows = document.getElementById('pointer-rows');
        const addPointerBtn = document.getElementById('add-pointer');
        const autoRefreshCheckbox = document.getElementById('auto-refresh');
        const watchSection = document.getElementById('watch-section');
        const watchConfigHeader = document.getElementById('watch-config-header');
        const watchConfigBody = document.getElementById('watch-config-body');
        const watchRows = document.getElementById('watch-rows');
        const addWatchBtn = document.getElementById('add-watch');
        const watchDisplay = document.getElementById('watch-display');
        const watchItems = document.getElementById('watch-items');

        let currentState = null;
        let currentStates = null;
        let currentNetwork = null;
        let currentNetworks = [];
        let isDarkTheme = true;
        let pointerColors = ['#22c55e', '#ef4444', '#3b82f6', '#f59e0b', '#8b5cf6', '#ec4899'];

        ws.onmessage = (event) => {
            const message = JSON.parse(event.data);

            switch (message.type) {
                case 'state':
                    if (message.states && message.states.length > 0) {
                        currentStates = message.states;
                        currentState = null;
                        renderMultipleStates(message.states);
                        if (message.state && message.state.watchValues) {
                            renderWatchValues(message.state.watchValues);
                        }
                    } else {
                        currentState = message.state;
                        currentStates = null;
                        renderState(message.state);
                        if (message.state && message.state.watchValues) {
                            renderWatchValues(message.state.watchValues);
                        }
                    }
                    break;
                case 'theme':
                    isDarkTheme = message.theme === 'dark';
                    document.body.className = message.theme;
                    if (currentStates && currentStates.length > 0) {
                        renderMultipleStates(currentStates);
                    } else if (currentState && currentState.kind === 'data') {
                        renderData(currentState.result.data);
                    }
                    break;
            }
        };

        expressionInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendExpression();
            }
        });

        refreshButton.addEventListener('click', () => {
            sendExpression();
        });

        // Reset button - clear all settings
        resetButton.addEventListener('click', () => {
            // Clear expression
            expressionInput.value = '';

            // Reset extractor
            extractorSelect.value = '';

            // Clear pointer rows and reset to default two
            pointerRows.innerHTML = \`
                <div class="form-row" data-index="0">
                    <input type="text" class="form-input" placeholder="e.g., slow" data-field="expression">
                    <select class="form-select" data-field="type">
                        <option value="object">Object</option>
                        <option value="index">Index</option>
                    </select>
                    <input type="color" class="form-color" value="#22c55e" data-field="color">
                    <button class="form-btn-remove" title="Remove">×</button>
                </div>
                <div class="form-row" data-index="1">
                    <input type="text" class="form-input" placeholder="e.g., fast" data-field="expression">
                    <select class="form-select" data-field="type">
                        <option value="object">Object</option>
                        <option value="index">Index</option>
                    </select>
                    <input type="color" class="form-color" value="#ef4444" data-field="color">
                    <button class="form-btn-remove" title="Remove">×</button>
                </div>
            \`;
            pointerRows.querySelectorAll('.form-row').forEach(setupPointerRowListeners);

            // Clear watch rows and reset to default one
            watchRows.innerHTML = \`
                <div class="form-row" data-index="0">
                    <input type="text" class="form-input" placeholder="e.g., i, count" data-field="expression">
                    <button class="form-btn-remove" title="Remove">×</button>
                </div>
            \`;
            watchRows.querySelectorAll('.form-row').forEach(setupWatchRowListeners);

            // Hide watch display
            watchDisplay.classList.remove('visible');

            // Clear visualization
            visualization.innerHTML = '<p class="message">Enter an expression to visualize</p>';

            // Send reset to server
            ws.send(JSON.stringify({ type: 'setPointers', pointers: [] }));
            ws.send(JSON.stringify({ type: 'setWatches', watches: [] }));
            ws.send(JSON.stringify({ type: 'setExpression', expression: '' }));
        });

        extractorSelect.addEventListener('change', () => {
            ws.send(JSON.stringify({
                type: 'setPreferredExtractor',
                extractorId: extractorSelect.value || undefined
            }));
        });

        // Section toggle (pointer tracking)
        pointerConfigHeader.addEventListener('click', () => {
            pointerSection.classList.toggle('expanded');
        });

        // Section toggle (watch variables)
        watchConfigHeader.addEventListener('click', () => {
            watchSection.classList.toggle('expanded');
        });

        // Add pointer button
        addPointerBtn.addEventListener('click', () => {
            const rows = pointerRows.querySelectorAll('.form-row');
            const newIndex = rows.length;
            const color = pointerColors[newIndex % pointerColors.length];

            const newRow = document.createElement('div');
            newRow.className = 'form-row';
            newRow.dataset.index = newIndex;
            newRow.innerHTML = \`
                <input type="text" class="form-input" placeholder="Pointer \${newIndex + 1}" data-field="expression">
                <select class="form-select" data-field="type">
                    <option value="object">Object</option>
                    <option value="index">Index</option>
                </select>
                <input type="color" class="form-color" value="\${color}" data-field="color">
                <button class="form-btn-remove" title="Remove">×</button>
            \`;
            pointerRows.appendChild(newRow);
            setupPointerRowListeners(newRow);
        });

        // Setup listeners for pointer rows
        function setupPointerRowListeners(row) {
            const removeBtn = row.querySelector('.form-btn-remove');
            removeBtn.addEventListener('click', () => {
                row.remove();
                sendPointers();
            });

            const inputs = row.querySelectorAll('input');
            inputs.forEach(input => {
                input.addEventListener('change', sendPointers);
                input.addEventListener('blur', sendPointers);
            });

            // Add listener for type select dropdown
            const typeSelect = row.querySelector('[data-field="type"]');
            if (typeSelect) {
                typeSelect.addEventListener('change', sendPointers);
            }
        }

        // Setup existing pointer rows
        pointerRows.querySelectorAll('.form-row').forEach(setupPointerRowListeners);

        // Send pointers to server
        function sendPointers() {
            const pointers = [];
            pointerRows.querySelectorAll('.form-row').forEach((row) => {
                const expr = row.querySelector('[data-field="expression"]').value.trim();
                const color = row.querySelector('[data-field="color"]').value;
                const typeSelect = row.querySelector('[data-field="type"]');
                const pointerType = typeSelect ? typeSelect.value : 'object';
                if (expr) {
                    pointers.push({
                        expression: expr,
                        color: color,
                        label: expr,
                        type: pointerType
                    });
                }
            });
            ws.send(JSON.stringify({
                type: 'setPointers',
                pointers: pointers
            }));
        }

        // Auto-refresh checkbox
        autoRefreshCheckbox.addEventListener('change', () => {
            ws.send(JSON.stringify({
                type: 'setAutoRefresh',
                autoRefresh: autoRefreshCheckbox.checked
            }));
        });

        // Add watch button
        addWatchBtn.addEventListener('click', () => {
            const rows = watchRows.querySelectorAll('.form-row');
            const newIndex = rows.length;

            const newRow = document.createElement('div');
            newRow.className = 'form-row';
            newRow.dataset.index = newIndex;
            newRow.innerHTML = \`
                <input type="text" class="form-input" placeholder="Variable \${newIndex + 1}" data-field="expression">
                <button class="form-btn-remove" title="Remove">×</button>
            \`;
            watchRows.appendChild(newRow);
            setupWatchRowListeners(newRow);
        });

        // Setup listeners for watch rows
        function setupWatchRowListeners(row) {
            const removeBtn = row.querySelector('.form-btn-remove');
            removeBtn.addEventListener('click', () => {
                row.remove();
                sendWatches();
            });

            const input = row.querySelector('input');
            input.addEventListener('change', sendWatches);
            input.addEventListener('blur', sendWatches);
        }

        // Setup existing watch rows
        watchRows.querySelectorAll('.form-row').forEach(setupWatchRowListeners);

        // Send watches to server
        function sendWatches() {
            const watches = [];
            watchRows.querySelectorAll('.form-row').forEach((row) => {
                const expr = row.querySelector('[data-field="expression"]').value.trim();
                if (expr) {
                    watches.push(expr);
                }
            });
            ws.send(JSON.stringify({
                type: 'setWatches',
                watches: watches
            }));
        }

        // Render watch values in the display panel
        function renderWatchValues(watchValues) {
            if (!watchValues || watchValues.length === 0) {
                watchDisplay.classList.remove('visible');
                return;
            }

            watchDisplay.classList.add('visible');
            let html = '';
            for (const wv of watchValues) {
                html += '<div class="watch-item">';
                html += '<span class="watch-name">' + escapeHtml(wv.name) + '</span>';
                html += '<span class="watch-equals">=</span>';
                html += '<span class="watch-value">' + escapeHtml(wv.value) + '</span>';
                html += '</div>';
            }
            watchItems.innerHTML = html;
        }

        function sendExpression() {
            ws.send(JSON.stringify({
                type: 'setExpression',
                expression: expressionInput.value
            }));
        }

        function renderState(state) {
            // Clean up previous visualizations
            if (currentNetwork) {
                currentNetwork.destroy();
                currentNetwork = null;
            }
            for (const net of currentNetworks) {
                if (net) net.destroy();
            }
            currentNetworks = [];

            if (state.kind === 'error' || state.kind === 'noSession') {
                visualization.innerHTML = '<p class="error">' + escapeHtml(state.message) + '</p>';
                return;
            }

            if (state.kind === 'data') {
                const result = state.result;

                // Update extractor dropdown
                updateExtractorDropdown(result.availableExtractors, result.usedExtractor);

                // Render the visualization
                renderData(result.data);
            }
        }

        function renderMultipleStates(states) {
            // Clean up previous visualizations
            if (currentNetwork) {
                currentNetwork.destroy();
                currentNetwork = null;
            }
            for (const net of currentNetworks) {
                if (net) net.destroy();
            }
            currentNetworks = [];

            // Create container for side-by-side visualizations
            let html = '<div class="multi-vis-container">';

            for (let i = 0; i < states.length; i++) {
                const { expression, result } = states[i];
                html += '<div class="vis-panel" data-index="' + i + '">';
                html += '<div class="vis-panel-header">' + escapeHtml(expression) + '</div>';
                html += '<div class="vis-panel-content" id="vis-panel-content-' + i + '"></div>';
                html += '</div>';
            }

            html += '</div>';
            visualization.innerHTML = html;

            // Render each visualization into its panel
            for (let i = 0; i < states.length; i++) {
                const { expression, result } = states[i];
                const panelContent = document.getElementById('vis-panel-content-' + i);

                if (result.kind === 'error' || result.kind === 'noSession') {
                    panelContent.innerHTML = '<p class="error">' + escapeHtml(result.message) + '</p>';
                } else if (result.kind === 'data') {
                    renderDataInPanel(result.result.data, panelContent, i);
                }
            }
        }

        function renderDataInPanel(data, container, panelIndex) {
            console.log('renderDataInPanel called with:', data, 'panelIndex:', panelIndex);

            if (!data || !data.kind) {
                container.innerHTML = '<div class="visualization-content">' +
                    '<p class="error">Invalid visualization data</p></div>';
                return;
            }

            const kind = Object.keys(data.kind)[0];

            switch (kind) {
                case 'text':
                    container.innerHTML = '<div class="visualization-content"><pre>' + escapeHtml(data.text) + '</pre></div>';
                    break;
                case 'table':
                    container.innerHTML = '<div class="visualization-content">' + renderTable(data.rows) + '</div>';
                    break;
                case 'tree':
                    renderTreeGraphInPanel(data, container, panelIndex);
                    break;
                case 'grid':
                    container.innerHTML = '<div class="grid-container">' + renderGrid(data) + '</div>';
                    break;
                case 'array':
                    container.innerHTML = '<div class="array-container">' + renderArray(data) + '</div>';
                    break;
                case 'graph':
                    renderGraphInPanel(data, container, panelIndex);
                    break;
                case 'plotly':
                    renderPlotlyInPanel(data, container, panelIndex);
                    break;
                default:
                    container.innerHTML = '<div class="visualization-content"><pre>' + JSON.stringify(data, null, 2) + '</pre></div>';
            }
        }

        function renderTreeGraphInPanel(data, container, panelIndex) {
            if (!data.root) {
                container.innerHTML = '<div class="visualization-content"><p class="message">Empty tree</p></div>';
                return;
            }

            if (typeof vis === 'undefined' || typeof vis.Network === 'undefined') {
                container.innerHTML = '<div class="visualization-content"><p class="error">vis-network library not loaded.</p></div>';
                return;
            }

            container.innerHTML = '<div class="graph-container" id="graph-container-' + panelIndex + '"></div>';
            const graphContainer = document.getElementById('graph-container-' + panelIndex);

            // Build marker map
            const markerMap = new Map();
            if (data.markers && Array.isArray(data.markers)) {
                for (const marker of data.markers) {
                    if (marker.pythonId !== undefined && marker.pythonId !== null) {
                        const key = String(marker.pythonId);
                        if (!markerMap.has(key)) {
                            markerMap.set(key, []);
                        }
                        markerMap.get(key).push(marker);
                    }
                }
            }

            const nodes = [];
            const edges = [];
            let nodeId = 0;

            function traverse(node, parentId) {
                if (!node) return null;

                const currentId = nodeId++;
                const items = node.items || [];
                let label = items.map(i => i.text || '').join('') || '?';
                const isNull = label.toLowerCase() === 'null' || label === '...';

                const pythonIdKey = node.pythonId !== undefined && node.pythonId !== null ? String(node.pythonId) : null;
                const nodeMarkers = pythonIdKey ? markerMap.get(pythonIdKey) : null;
                const isMarked = nodeMarkers && nodeMarkers.length > 0;
                const markerColor = isMarked ? nodeMarkers[0].color : null;
                const markerLabel = isMarked ? nodeMarkers.map(m => m.label).join(', ') : '';

                if (isMarked && markerLabel) {
                    label = label + '\\n[' + markerLabel + ']';
                }

                const nodeColor = isDarkTheme ? '#4a9eff' : '#4a9eff';

                nodes.push({
                    id: currentId,
                    label: label,
                    shape: 'circle',
                    color: {
                        background: isNull ? 'transparent' : (isMarked ? markerColor : nodeColor),
                        border: isNull ? (isDarkTheme ? '#555' : '#ccc') : (isMarked ? markerColor : nodeColor),
                        highlight: { background: '#7ab8ff', border: '#4a9eff' }
                    },
                    borderWidth: isNull ? 1 : (isMarked ? 4 : 2),
                    borderDashes: isNull ? [4, 4] : false,
                    font: {
                        color: isNull ? (isDarkTheme ? '#666' : '#999') : '#ffffff',
                        size: isNull ? 10 : 14
                    },
                    size: isNull ? 15 : 25,
                    shadow: isMarked ? { enabled: true, color: markerColor, size: 10 } : false
                });

                if (parentId !== null) {
                    edges.push({ from: parentId, to: currentId });
                }

                if (node.children && node.children.length > 0) {
                    for (const child of node.children) {
                        traverse(child, currentId);
                    }
                }

                return currentId;
            }

            try {
                traverse(data.root, null);

                const visNodes = new vis.DataSet(nodes);
                const visEdges = new vis.DataSet(edges);

                const options = {
                    layout: {
                        hierarchical: {
                            enabled: true,
                            direction: 'UD',
                            sortMethod: 'directed',
                            levelSeparation: 60,
                            nodeSpacing: 80,
                            treeSpacing: 100
                        }
                    },
                    physics: { enabled: false },
                    edges: {
                        arrows: { to: false },
                        color: { color: isDarkTheme ? '#666' : '#aaa' },
                        width: 2,
                        smooth: false
                    },
                    interaction: {
                        dragNodes: false,
                        zoomView: true,
                        dragView: true
                    }
                };

                const network = new vis.Network(graphContainer, { nodes: visNodes, edges: visEdges }, options);
                currentNetworks.push(network);
            } catch (err) {
                container.innerHTML = '<div class="visualization-content"><p class="error">Error rendering tree: ' + err.message + '</p></div>';
            }
        }

        function renderGraphInPanel(data, container, panelIndex) {
            if (!data.nodes || !Array.isArray(data.nodes) || data.nodes.length === 0) {
                container.innerHTML = '<div class="visualization-content"><p class="error">Graph data missing nodes array.</p></div>';
                return;
            }

            if (typeof vis === 'undefined' || typeof vis.Network === 'undefined') {
                container.innerHTML = '<div class="visualization-content"><p class="error">vis-network library not loaded.</p></div>';
                return;
            }

            container.innerHTML = '<div class="graph-container" id="graph-container-' + panelIndex + '"></div>';
            const graphContainer = document.getElementById('graph-container-' + panelIndex);

            const markerMap = new Map();
            if (data.markers && Array.isArray(data.markers)) {
                for (const marker of data.markers) {
                    if (marker.pythonId !== undefined && marker.pythonId !== null) {
                        const key = String(marker.pythonId);
                        if (!markerMap.has(key)) {
                            markerMap.set(key, []);
                        }
                        markerMap.get(key).push(marker);
                    }
                }
            }

            try {
                const nodes = new vis.DataSet(data.nodes.map(n => {
                    const pythonIdKey = n.pythonId !== undefined && n.pythonId !== null ? String(n.pythonId) : null;
                    const nodeMarkers = pythonIdKey ? markerMap.get(pythonIdKey) : null;
                    const isMarked = nodeMarkers && nodeMarkers.length > 0;
                    const markerColor = isMarked ? nodeMarkers[0].color : null;

                    return {
                        id: n.id,
                        label: n.label || n.id,
                        color: {
                            background: isMarked ? markerColor : (n.color || (isDarkTheme ? '#4a9eff' : '#4a9eff')),
                            border: isMarked ? markerColor : (n.color || (isDarkTheme ? '#2d7ad6' : '#2d7ad6'))
                        },
                        font: { color: isDarkTheme ? '#ffffff' : '#333333' },
                        shape: n.shape || 'box',
                        borderWidth: isMarked ? 4 : 2,
                        shadow: isMarked ? { enabled: true, color: markerColor, size: 15 } : true
                    };
                }));

                const edges = new vis.DataSet(data.edges.map((e, i) => ({
                    id: i,
                    from: e.from,
                    to: e.to,
                    label: e.label || '',
                    arrows: { to: { enabled: true, scaleFactor: 0.8 } },
                    color: { color: isDarkTheme ? '#666666' : '#999999' },
                    smooth: { type: 'cubicBezier', roundness: 0.4 }
                })));

                const options = {
                    physics: {
                        enabled: true,
                        solver: 'forceAtlas2Based',
                        stabilization: { iterations: 100 }
                    },
                    interaction: { hover: true }
                };

                const network = new vis.Network(graphContainer, { nodes, edges }, options);
                currentNetworks.push(network);
            } catch (err) {
                container.innerHTML = '<div class="visualization-content"><p class="error">Error rendering graph: ' + err.message + '</p></div>';
            }
        }

        function renderPlotlyInPanel(data, container, panelIndex) {
            if (!data.data || !Array.isArray(data.data) || data.data.length === 0) {
                container.innerHTML = '<div class="visualization-content"><p class="error">Plotly data missing data array.</p></div>';
                return;
            }

            if (typeof Plotly === 'undefined') {
                container.innerHTML = '<div class="visualization-content"><p class="error">Plotly library not loaded.</p></div>';
                return;
            }

            try {
                container.innerHTML = '<div id="plotly-container-' + panelIndex + '" style="height: 350px;"></div>';
                const plotlyContainer = document.getElementById('plotly-container-' + panelIndex);

                const layout = Object.assign({}, data.layout || {}, {
                    paper_bgcolor: isDarkTheme ? '#1e1e1e' : '#ffffff',
                    plot_bgcolor: isDarkTheme ? '#1e1e1e' : '#ffffff',
                    font: { color: isDarkTheme ? '#d4d4d4' : '#333333' },
                    margin: { l: 40, r: 20, t: 40, b: 40 }
                });

                Plotly.newPlot(plotlyContainer, data.data, layout, { responsive: true, displayModeBar: false });
            } catch (err) {
                container.innerHTML = '<div class="visualization-content"><p class="error">Error rendering Plotly chart: ' + err.message + '</p></div>';
            }
        }

        function updateExtractorDropdown(extractors, used) {
            extractorSelect.innerHTML = '<option value="">Auto</option>';
            for (const ext of extractors) {
                const option = document.createElement('option');
                option.value = ext.id;
                option.textContent = ext.name;
                if (used && ext.id === used.id) {
                    option.selected = true;
                }
                extractorSelect.appendChild(option);
            }
        }

        function renderData(data) {
            console.log('renderData called with:', data);

            if (!data || !data.kind) {
                visualization.innerHTML = '<div class="visualization-content">' +
                    '<p class="error">Invalid visualization data - missing kind property</p>' +
                    '<pre>' + JSON.stringify(data, null, 2) + '</pre></div>';
                return;
            }

            const kind = Object.keys(data.kind)[0];
            console.log('Detected kind:', kind);

            switch (kind) {
                case 'text':
                    visualization.innerHTML = '<div class="visualization-content"><pre>' + escapeHtml(data.text) + '</pre></div>';
                    break;
                case 'table':
                    visualization.innerHTML = '<div class="visualization-content">' + renderTable(data.rows) + '</div>';
                    break;
                case 'tree':
                    renderTreeGraph(data);
                    break;
                case 'grid':
                    visualization.innerHTML = '<div class="grid-container">' + renderGrid(data) + '</div>';
                    break;
                case 'array':
                    visualization.innerHTML = '<div class="array-container">' + renderArray(data) + '</div>';
                    break;
                case 'graph':
                    renderGraph(data);
                    break;
                case 'plotly':
                    renderPlotly(data);
                    break;
                case 'imagePng':
                    visualization.innerHTML = '<div class="visualization-content"><img src="data:image/png;base64,' + data.base64Data + '" style="max-width: 100%;"></div>';
                    break;
                case 'svg':
                    visualization.innerHTML = '<div class="visualization-content">' + data.text + '</div>';
                    break;
                default:
                    visualization.innerHTML = '<div class="visualization-content"><pre>' + JSON.stringify(data, null, 2) + '</pre></div>';
            }
        }

        function renderGraph(data) {
            // Validate data structure
            if (!data.nodes || !Array.isArray(data.nodes) || data.nodes.length === 0) {
                visualization.innerHTML = '<div class="visualization-content">' +
                    '<p class="error">Graph data missing nodes array.</p>' +
                    '<pre>' + JSON.stringify(data, null, 2) + '</pre></div>';
                return;
            }

            // Check if vis-network library is loaded
            if (typeof vis === 'undefined' || typeof vis.Network === 'undefined') {
                visualization.innerHTML = '<div class="visualization-content">' +
                    '<p class="error">vis-network library not loaded. Showing raw data:</p>' +
                    '<pre>' + JSON.stringify(data, null, 2) + '</pre></div>';
                return;
            }

            visualization.innerHTML = '<div id="graph-container"></div>';
            const container = document.getElementById('graph-container');

            // Build a map from pythonId to markers (use string keys for large integers)
            const markerMap = new Map();
            if (data.markers && Array.isArray(data.markers)) {
                for (const marker of data.markers) {
                    if (marker.pythonId !== undefined && marker.pythonId !== null) {
                        const key = String(marker.pythonId);
                        if (!markerMap.has(key)) {
                            markerMap.set(key, []);
                        }
                        markerMap.get(key).push(marker);
                    }
                }
            }

            try {
            // Convert data to vis-network format with marker highlighting
            const nodes = new vis.DataSet(data.nodes.map(n => {
                const pythonIdKey = n.pythonId !== undefined && n.pythonId !== null ? String(n.pythonId) : null;
                const nodeMarkers = pythonIdKey ? markerMap.get(pythonIdKey) : null;
                const isMarked = nodeMarkers && nodeMarkers.length > 0;
                const markerColor = isMarked ? nodeMarkers[0].color : null;
                const markerLabels = isMarked ? nodeMarkers.map(m => m.label).join(', ') : '';

                let nodeLabel = n.label || n.id;
                if (isMarked && markerLabels) {
                    nodeLabel = nodeLabel + '\\n[' + markerLabels + ']';
                }

                return {
                    id: n.id,
                    label: nodeLabel,
                    color: {
                        background: isMarked ? markerColor : (n.color || (isDarkTheme ? '#4a9eff' : '#4a9eff')),
                        border: isMarked ? markerColor : (n.color || (isDarkTheme ? '#2d7ad6' : '#2d7ad6')),
                        highlight: {
                            background: isDarkTheme ? '#7ab8ff' : '#7ab8ff',
                            border: isDarkTheme ? '#4a9eff' : '#4a9eff'
                        }
                    },
                    font: {
                        color: isDarkTheme ? '#ffffff' : '#333333',
                        multi: 'html'
                    },
                    shape: n.shape || 'box',
                    borderWidth: isMarked ? 4 : 2,
                    shadow: isMarked ? { enabled: true, color: markerColor, size: 15 } : true
                };
            }));

            const edges = new vis.DataSet(data.edges.map((e, i) => ({
                id: i,
                from: e.from,
                to: e.to,
                label: e.label || '',
                arrows: {
                    to: { enabled: true, scaleFactor: 0.8 }
                },
                color: {
                    color: isDarkTheme ? '#666666' : '#999999',
                    highlight: isDarkTheme ? '#999999' : '#666666'
                },
                font: {
                    color: isDarkTheme ? '#cccccc' : '#666666',
                    size: 11,
                    strokeWidth: 2,
                    strokeColor: isDarkTheme ? '#1e1e1e' : '#ffffff'
                },
                smooth: {
                    type: 'cubicBezier',
                    roundness: 0.4
                }
            })));

            const options = {
                nodes: {
                    borderWidth: 2,
                    shadow: true,
                    font: {
                        size: 14
                    }
                },
                edges: {
                    width: 2,
                    shadow: true
                },
                physics: {
                    enabled: true,
                    solver: 'forceAtlas2Based',
                    forceAtlas2Based: {
                        gravitationalConstant: -50,
                        centralGravity: 0.01,
                        springLength: 100,
                        springConstant: 0.08
                    },
                    stabilization: {
                        iterations: 100
                    }
                },
                layout: {
                    improvedLayout: true
                },
                interaction: {
                    hover: true,
                    tooltipDelay: 200
                }
            };

            currentNetwork = new vis.Network(container, { nodes, edges }, options);
            } catch (err) {
                visualization.innerHTML = '<div class="visualization-content">' +
                    '<p class="error">Error rendering graph: ' + err.message + '</p>' +
                    '<pre>' + JSON.stringify(data, null, 2) + '</pre></div>';
            }
        }

        function renderTreeGraph(data) {
            if (!data.root) {
                visualization.innerHTML = '<div class="visualization-content"><p class="message">Empty tree</p></div>';
                return;
            }

            // Check if vis-network library is loaded
            if (typeof vis === 'undefined' || typeof vis.Network === 'undefined') {
                visualization.innerHTML = '<div class="visualization-content">' +
                    '<p class="error">vis-network library not loaded.</p></div>';
                return;
            }

            visualization.innerHTML = '<div id="graph-container"></div>';
            const container = document.getElementById('graph-container');

            // Build marker map (use string keys for large integers)
            console.log('[PDV-DEBUG] renderTreeGraph - data.markers:', JSON.stringify(data.markers));
            const markerMap = new Map();
            if (data.markers && Array.isArray(data.markers)) {
                for (const marker of data.markers) {
                    if (marker.pythonId !== undefined && marker.pythonId !== null) {
                        const key = String(marker.pythonId);
                        if (!markerMap.has(key)) {
                            markerMap.set(key, []);
                        }
                        markerMap.get(key).push(marker);
                    }
                }
            }
            console.log('[PDV-DEBUG] renderTreeGraph - markerMap size:', markerMap.size, 'keys:', Array.from(markerMap.keys()));

            // Convert tree to nodes and edges
            const nodes = [];
            const edges = [];
            let nodeId = 0;

            function traverse(node, parentId) {
                if (!node) return null;

                const currentId = nodeId++;
                const items = node.items || [];
                let label = items.map(i => i.text || '').join('') || '?';
                const isNull = label.toLowerCase() === 'null' || label === '...';

                // Check if marked (use string key for comparison)
                const pythonIdKey = node.pythonId !== undefined && node.pythonId !== null ? String(node.pythonId) : null;
                const nodeMarkers = pythonIdKey ? markerMap.get(pythonIdKey) : null;
                const isMarked = nodeMarkers && nodeMarkers.length > 0;
                console.log('[PDV-DEBUG] traverse - label:', label, 'pythonId:', node.pythonId, 'key:', pythonIdKey, 'isMarked:', isMarked);
                const markerColor = isMarked ? nodeMarkers[0].color : null;
                const markerLabel = isMarked ? nodeMarkers.map(m => m.label).join(', ') : '';

                if (isMarked && markerLabel) {
                    label = label + '\\n[' + markerLabel + ']';
                }

                const nodeColor = isDarkTheme ? '#4a9eff' : '#4a9eff';

                nodes.push({
                    id: currentId,
                    label: label,
                    shape: 'circle',
                    color: {
                        background: isNull ? 'transparent' : (isMarked ? markerColor : nodeColor),
                        border: isNull ? (isDarkTheme ? '#555' : '#ccc') : (isMarked ? markerColor : nodeColor),
                        highlight: { background: '#7ab8ff', border: '#4a9eff' }
                    },
                    borderWidth: isNull ? 1 : (isMarked ? 4 : 2),
                    borderDashes: isNull ? [4, 4] : false,
                    font: {
                        color: isNull ? (isDarkTheme ? '#666' : '#999') : '#ffffff',
                        size: isNull ? 10 : 14
                    },
                    size: isNull ? 15 : 25,
                    shadow: isMarked ? { enabled: true, color: markerColor, size: 10 } : false
                });

                if (parentId !== null) {
                    edges.push({
                        from: parentId,
                        to: currentId
                    });
                }

                // Process children
                if (node.children && node.children.length > 0) {
                    for (const child of node.children) {
                        traverse(child, currentId);
                    }
                }

                return currentId;
            }

            try {
                traverse(data.root, null);

                const visNodes = new vis.DataSet(nodes);
                const visEdges = new vis.DataSet(edges);

                const options = {
                    layout: {
                        hierarchical: {
                            enabled: true,
                            direction: 'UD',
                            sortMethod: 'directed',
                            levelSeparation: 80,
                            nodeSpacing: 100,
                            treeSpacing: 150
                        }
                    },
                    physics: {
                        enabled: false
                    },
                    edges: {
                        arrows: { to: false },
                        color: { color: isDarkTheme ? '#666' : '#aaa' },
                        width: 2,
                        smooth: false  // Straight lines
                    },
                    interaction: {
                        dragNodes: false,
                        zoomView: true,
                        dragView: true
                    }
                };

                currentNetwork = new vis.Network(container, { nodes: visNodes, edges: visEdges }, options);
            } catch (err) {
                visualization.innerHTML = '<div class="visualization-content">' +
                    '<p class="error">Error rendering tree: ' + err.message + '</p></div>';
            }
        }

        function renderPlotly(data) {
            // Validate data structure
            if (!data.data || !Array.isArray(data.data) || data.data.length === 0) {
                visualization.innerHTML = '<div class="visualization-content">' +
                    '<p class="error">Plotly data missing data array.</p>' +
                    '<pre>' + JSON.stringify(data, null, 2) + '</pre></div>';
                return;
            }

            // Check if Plotly library is loaded
            if (typeof Plotly === 'undefined') {
                visualization.innerHTML = '<div class="visualization-content">' +
                    '<p class="error">Plotly library not loaded. Showing raw data:</p>' +
                    '<pre>' + JSON.stringify(data, null, 2) + '</pre></div>';
                return;
            }

            try {
            visualization.innerHTML = '<div id="plotly-container"></div>';
            const container = document.getElementById('plotly-container');

            const layout = Object.assign({}, data.layout || {}, {
                paper_bgcolor: isDarkTheme ? '#1e1e1e' : '#ffffff',
                plot_bgcolor: isDarkTheme ? '#1e1e1e' : '#ffffff',
                font: {
                    color: isDarkTheme ? '#d4d4d4' : '#333333'
                },
                xaxis: Object.assign({}, data.layout?.xaxis || {}, {
                    gridcolor: isDarkTheme ? '#3c3c3c' : '#e0e0e0',
                    zerolinecolor: isDarkTheme ? '#555555' : '#cccccc'
                }),
                yaxis: Object.assign({}, data.layout?.yaxis || {}, {
                    gridcolor: isDarkTheme ? '#3c3c3c' : '#e0e0e0',
                    zerolinecolor: isDarkTheme ? '#555555' : '#cccccc'
                }),
                margin: { l: 50, r: 30, t: 50, b: 50 }
            });

            const config = {
                responsive: true,
                displayModeBar: true,
                displaylogo: false
            };

            Plotly.newPlot(container, data.data, layout, config);
            } catch (err) {
                visualization.innerHTML = '<div class="visualization-content">' +
                    '<p class="error">Error rendering Plotly chart: ' + err.message + '</p>' +
                    '<pre>' + JSON.stringify(data, null, 2) + '</pre></div>';
            }
        }

        function renderTable(rows) {
            if (!rows || rows.length === 0) {
                return '<p class="message">Empty table</p>';
            }

            const columns = Object.keys(rows[0]);
            let html = '<table><thead><tr>';
            for (const col of columns) {
                html += '<th>' + escapeHtml(col) + '</th>';
            }
            html += '</tr></thead><tbody>';

            for (const row of rows) {
                html += '<tr>';
                for (const col of columns) {
                    const value = row[col];
                    const displayValue = value === null ? 'null' :
                                        value === undefined ? '' :
                                        typeof value === 'object' ? JSON.stringify(value) :
                                        String(value);
                    html += '<td>' + escapeHtml(displayValue) + '</td>';
                }
                html += '</tr>';
            }
            html += '</tbody></table>';
            return html;
        }

        function renderTree(node, isRoot = false, markerMap = null) {
            if (!node) return '';

            const items = node.items || [];
            let labelText = '';
            for (const item of items) {
                labelText += item.text || '';
            }

            // Check if this is a null node
            const isNull = labelText.toLowerCase() === 'null' || labelText === '...';

            // Check if this node is marked (use String for consistency with map keys)
            const pythonIdKey = node.pythonId !== undefined && node.pythonId !== null ? String(node.pythonId) : null;
            const nodeMarkers = (markerMap && pythonIdKey) ? markerMap.get(pythonIdKey) : null;
            const isMarked = nodeMarkers && nodeMarkers.length > 0;
            const markerColor = isMarked ? nodeMarkers[0].color : null;
            const markerLabels = isMarked ? nodeMarkers.map(m => m.label).join(', ') : '';

            const hasChildren = node.children && node.children.length > 0;
            const rootClass = isRoot ? ' tree-root' : '';

            let html = '<div class="tree-node' + rootClass + '">';

            // Build node content classes and styles
            let contentClass = 'tree-node-content';
            if (isNull) contentClass += ' null-node';
            if (isMarked) contentClass += ' marked';

            let contentStyle = '';
            if (isMarked && markerColor) {
                contentStyle = ' style="border-color: ' + markerColor + '; box-shadow: 0 0 15px ' + markerColor + ';"';
            }

            html += '<div class="' + contentClass + '"' + contentStyle + '>';
            html += '<span class="tree-node-label">' + escapeHtml(labelText || '?') + '</span>';

            // Show marker label below the value
            if (isMarked && markerLabels) {
                html += '<br><span style="font-size: 9px; color: ' + markerColor + ';">' + escapeHtml(markerLabels) + '</span>';
            }
            html += '</div>';

            if (hasChildren) {
                html += '<div class="tree-children">';
                for (const child of node.children) {
                    html += renderTree(child, false, markerMap);
                }
                html += '</div>';
            }

            html += '</div>';
            return html;
        }

        function setupTreeToggle() {
            visualization.querySelectorAll('.tree-node-content[data-has-children="true"]').forEach(el => {
                el.addEventListener('click', function() {
                    const children = this.parentElement.querySelector('.tree-children');
                    const toggle = this.querySelector('.tree-toggle');
                    if (children) {
                        const isCollapsed = children.classList.toggle('collapsed');
                        toggle.textContent = isCollapsed ? '[+]' : '[-]';
                    }
                });
            });
        }

        function renderGrid(data) {
            let html = '<table class="grid-table maze-grid">';

            // Column headers
            if (data.columnLabels && data.columnLabels.length > 0) {
                html += '<thead><tr><th></th>';
                for (const col of data.columnLabels) {
                    html += '<th>' + escapeHtml(col.label || '') + '</th>';
                }
                html += '</tr></thead>';
            }

            // Build marker map with color and label info
            const markerMap = new Map();
            if (data.markers && Array.isArray(data.markers)) {
                for (const m of data.markers) {
                    const key = m.row + ',' + m.column;
                    if (!markerMap.has(key)) {
                        markerMap.set(key, []);
                    }
                    markerMap.get(key).push(m);
                }
            }

            // Grid rows
            html += '<tbody>';
            for (let rowIdx = 0; rowIdx < data.rows.length; rowIdx++) {
                const row = data.rows[rowIdx];
                html += '<tr>';
                html += '<th>' + escapeHtml(row.label || String(rowIdx)) + '</th>';

                for (let colIdx = 0; colIdx < row.columns.length; colIdx++) {
                    const cell = row.columns[colIdx];
                    const key = rowIdx + ',' + colIdx;
                    const cellMarkers = markerMap.get(key);

                    // Build cell styles
                    let styles = [];
                    let classes = ['maze-cell'];
                    let markerLabel = '';

                    // Apply cell background color
                    if (cell.color) {
                        styles.push('background-color: ' + cell.color);
                    }

                    // Apply text color for contrast
                    if (cell.textColor) {
                        styles.push('color: ' + cell.textColor);
                    }

                    // Apply marker styling (marker takes priority for visual effects)
                    if (cellMarkers && cellMarkers.length > 0) {
                        classes.push('grid-cell-marked');
                        const primaryMarker = cellMarkers[0];
                        if (primaryMarker.color) {
                            // Use marker color as border/highlight
                            styles.push('box-shadow: inset 0 0 0 3px ' + primaryMarker.color);
                        }
                        // Collect all marker labels
                        const labels = cellMarkers.filter(m => m.label).map(m => m.label);
                        if (labels.length > 0) {
                            markerLabel = '<span class="cell-marker-label">' + escapeHtml(labels.join(', ')) + '</span>';
                        }
                        // Special styling for current position
                        if (cellMarkers.some(m => m.id === 'current' || m.label === 'pos')) {
                            classes.push('maze-current');
                        }
                    }

                    const styleAttr = styles.length > 0 ? ' style="' + styles.join('; ') + '"' : '';
                    const classAttr = ' class="' + classes.join(' ') + '"';

                    html += '<td' + classAttr + styleAttr + '>';
                    html += '<span class="cell-content">' + escapeHtml(cell.content || '') + '</span>';
                    html += markerLabel;
                    html += '</td>';
                }
                html += '</tr>';
            }
            html += '</tbody></table>';
            return html;
        }

        function renderArray(data) {
            if (!data.elements || data.elements.length === 0) {
                return '<p class="message">Empty array</p>';
            }

            // Build index marker map
            const indexMarkers = new Map();
            if (data.markers && Array.isArray(data.markers)) {
                for (const marker of data.markers) {
                    if (marker.type === 'index' && marker.index !== undefined) {
                        if (!indexMarkers.has(marker.index)) {
                            indexMarkers.set(marker.index, []);
                        }
                        indexMarkers.get(marker.index).push(marker);
                    }
                }
            }

            let html = '<div class="array-view">';

            // Index labels row
            html += '<div class="array-indices">';
            for (const elem of data.elements) {
                html += '<div class="array-index">' + elem.index + '</div>';
            }
            html += '</div>';

            // Cells row
            html += '<div class="array-cells">';
            for (const elem of data.elements) {
                const markers = indexMarkers.get(elem.index);
                const isMarked = markers && markers.length > 0;
                const markerColor = isMarked ? markers[0].color : null;

                let cellStyle = '';
                let cellClass = 'array-cell';
                if (isMarked) {
                    cellClass += ' marked';
                    cellStyle = ' style="border-color: ' + markerColor + '; color: ' + markerColor + ';"';
                }

                html += '<div class="' + cellClass + '"' + cellStyle + '>' + escapeHtml(String(elem.value)) + '</div>';
            }
            html += '</div>';

            // Marker labels row
            html += '<div class="array-markers">';
            for (const elem of data.elements) {
                const markers = indexMarkers.get(elem.index);
                if (markers && markers.length > 0) {
                    const labels = markers.map(m => m.label).join(', ');
                    const color = markers[0].color;
                    html += '<div class="array-marker" style="color: ' + color + ';">' + escapeHtml(labels) + '</div>';
                } else {
                    html += '<div class="array-marker"></div>';
                }
            }
            html += '</div>';

            // Info
            html += '<div class="array-info">Length: ' + data.length;
            if (data.truncated) {
                html += ' (showing first ' + data.elements.length + ')';
            }
            html += '</div>';

            html += '</div>';
            return html;
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    </script>
</body>
</html>`;
    }
    dispose() {
        if (this.debugStepDisposable) {
            this.debugStepDisposable.dispose();
        }
        for (const ws of this.connections) {
            ws.close();
        }
        this.connections.clear();
        this.wss.close();
        this.server.close();
    }
}
exports.WebviewServer = WebviewServer;
//# sourceMappingURL=WebviewServer.js.map