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
exports.Config = void 0;
const vscode = __importStar(require("vscode"));
/**
 * Configuration manager for Python Debug Visualizer.
 */
class Config {
    constructor() {
        this.configSection = 'pythonDebugVisualizer';
    }
    /**
     * Get maximum number of items to display in collections.
     */
    get maxItems() {
        return this.get('maxItems', 1000);
    }
    /**
     * Get maximum depth for nested structure visualization.
     */
    get maxDepth() {
        return this.get('maxDepth', 10);
    }
    /**
     * Get whether to auto-refresh on debug step.
     */
    get autoRefresh() {
        return this.get('autoRefresh', true);
    }
    /**
     * Get the current VS Code theme kind.
     */
    get theme() {
        const kind = vscode.window.activeColorTheme.kind;
        return kind === vscode.ColorThemeKind.Light || kind === vscode.ColorThemeKind.HighContrastLight
            ? 'light'
            : 'dark';
    }
    /**
     * Get a configuration value.
     */
    get(key, defaultValue) {
        const config = vscode.workspace.getConfiguration(this.configSection);
        return config.get(key, defaultValue);
    }
    /**
     * Listen for configuration changes.
     */
    onConfigChange(callback) {
        return vscode.workspace.onDidChangeConfiguration((e) => {
            if (e.affectsConfiguration(this.configSection)) {
                callback();
            }
        });
    }
}
exports.Config = Config;
//# sourceMappingURL=config.js.map