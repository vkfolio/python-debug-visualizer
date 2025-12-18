import * as vscode from 'vscode';

/**
 * Configuration manager for Python Debug Visualizer.
 */
export class Config {
    private readonly configSection = 'pythonDebugVisualizer';

    /**
     * Get maximum number of items to display in collections.
     */
    get maxItems(): number {
        return this.get<number>('maxItems', 1000);
    }

    /**
     * Get maximum depth for nested structure visualization.
     */
    get maxDepth(): number {
        return this.get<number>('maxDepth', 10);
    }

    /**
     * Get whether to auto-refresh on debug step.
     */
    get autoRefresh(): boolean {
        return this.get<boolean>('autoRefresh', true);
    }

    /**
     * Get the current VS Code theme kind.
     */
    get theme(): 'light' | 'dark' {
        const kind = vscode.window.activeColorTheme.kind;
        return kind === vscode.ColorThemeKind.Light || kind === vscode.ColorThemeKind.HighContrastLight
            ? 'light'
            : 'dark';
    }

    /**
     * Get a configuration value.
     */
    private get<T>(key: string, defaultValue: T): T {
        const config = vscode.workspace.getConfiguration(this.configSection);
        return config.get<T>(key, defaultValue);
    }

    /**
     * Listen for configuration changes.
     */
    onConfigChange(callback: () => void): vscode.Disposable {
        return vscode.workspace.onDidChangeConfiguration((e) => {
            if (e.affectsConfiguration(this.configSection)) {
                callback();
            }
        });
    }
}
