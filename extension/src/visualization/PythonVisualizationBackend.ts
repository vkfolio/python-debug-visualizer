import { DebugSessionManager } from '../debugger/DebugSessionManager';
import { Config } from '../config';

/**
 * Visualization data extracted from Python.
 */
export interface VisualizationData {
    kind: Record<string, boolean>;
    [key: string]: any;
}

/**
 * Extractor information.
 */
export interface ExtractorInfo {
    id: string;
    name: string;
    priority: number;
}

/**
 * Result of data extraction.
 */
export interface DataExtractionResult {
    data: VisualizationData;
    usedExtractor: ExtractorInfo;
    availableExtractors: ExtractorInfo[];
}

/**
 * A tracked pointer expression for visualization highlighting.
 */
export interface TrackedExpression {
    /** The Python expression (e.g., "slow", "fast") */
    expression: string;
    /** The highlight color (e.g., "#00ff00") */
    color: string;
    /** Display label (e.g., "slow pointer") */
    label: string;
    /** Marker type: 'object' for linked list nodes, 'index' for array indices */
    type: 'object' | 'index';
}

/**
 * Marker information for highlighting nodes in visualizations.
 */
export interface PointerMarker {
    /** The Python object id of the pointed-to node (for object type) - as string to avoid precision loss */
    pythonId?: string;
    /** The array index (for index type) */
    index?: number;
    /** The highlight color */
    color: string;
    /** Display label */
    label: string;
    /** Marker type */
    type: 'object' | 'index';
}

/**
 * Visualization result from the backend.
 */
export type VisualizationResult =
    | { kind: 'data'; result: DataExtractionResult }
    | { kind: 'error'; message: string }
    | { kind: 'noSession'; message: string };

/**
 * Backend for evaluating Python expressions and extracting visualization data.
 */
export class PythonVisualizationBackend {
    constructor(
        private readonly sessionManager: DebugSessionManager,
        private readonly config: Config
    ) {}

    /**
     * Get visualization data for a Python expression.
     */
    async getVisualizationData(
        expression: string,
        preferredExtractorId?: string
    ): Promise<VisualizationResult> {
        const session = this.sessionManager.getActiveSession();
        if (!session) {
            return {
                kind: 'noSession',
                message: 'No active Python debug session. Start debugging to visualize data.'
            };
        }

        // First try with pydebugvisualizer package
        try {
            const visualizeExpr = this.buildVisualizationExpression(expression, preferredExtractorId);
            const result = await this.sessionManager.evaluate(visualizeExpr, 'repl');

            if (result) {
                return this.parseVisualizationResult(result);
            }
        } catch (error) {
            // Package not available or error - try fallback
            const msg = error instanceof Error ? error.message : String(error);
            if (!msg.includes('ModuleNotFoundError') && !msg.includes('No module named')) {
                // Some other error, report it
                return this.handleError(error);
            }
        }

        // Fallback: use repr() for basic visualization
        try {
            const reprExpr = `repr(${expression})`;
            const typeExpr = `type(${expression}).__name__`;

            const reprResult = await this.sessionManager.evaluate(reprExpr, 'repl');
            const typeResult = await this.sessionManager.evaluate(typeExpr, 'repl');

            if (reprResult) {
                let text = reprResult;
                // Clean up Python string quotes
                if ((text.startsWith("'") && text.endsWith("'")) ||
                    (text.startsWith('"') && text.endsWith('"'))) {
                    text = text.slice(1, -1);
                }
                text = text.replace(/\\n/g, '\n').replace(/\\'/g, "'").replace(/\\t/g, '\t');

                let typeName = typeResult || 'object';
                if ((typeName.startsWith("'") && typeName.endsWith("'")) ||
                    (typeName.startsWith('"') && typeName.endsWith('"'))) {
                    typeName = typeName.slice(1, -1);
                }

                return {
                    kind: 'data',
                    result: {
                        data: {
                            kind: { text: true },
                            text: `[${typeName}]\n\n${text}`
                        },
                        usedExtractor: {
                            id: 'fallback.repr',
                            name: 'Fallback (repr) - install pydebugvisualizer for better visualization',
                            priority: 0
                        },
                        availableExtractors: []
                    }
                };
            }

            return { kind: 'error', message: 'Could not evaluate expression' };
        } catch (error) {
            return this.handleError(error);
        }
    }

    /**
     * Get visualization data with pointer markers.
     *
     * This method evaluates the main data structure and additional pointer
     * expressions, then adds markers to highlight where pointers point to.
     *
     * @param dataExpression - The main data structure expression (e.g., "head")
     * @param pointerExpressions - Array of pointer expressions to track
     * @param preferredExtractorId - Optional preferred extractor
     * @returns Visualization result with markers
     */
    async getVisualizationWithPointers(
        dataExpression: string,
        pointerExpressions: TrackedExpression[],
        preferredExtractorId?: string
    ): Promise<VisualizationResult> {
        // First get the visualization data for the main expression
        const result = await this.getVisualizationData(dataExpression, preferredExtractorId);

        if (result.kind !== 'data') {
            return result;
        }

        // Evaluate each pointer expression
        const markers: PointerMarker[] = [];

        for (const pointer of pointerExpressions) {
            console.log('[PDV-DEBUG] Processing pointer:', pointer.expression, 'type:', pointer.type);
            try {
                if (pointer.type === 'index') {
                    // For index pointers, evaluate the expression directly as an integer
                    const indexResult = await this.sessionManager.evaluate(pointer.expression, 'repl');

                    if (indexResult) {
                        const index = parseInt(indexResult, 10);
                        if (!isNaN(index) && index >= 0) {
                            markers.push({
                                index,
                                color: pointer.color,
                                label: pointer.label,
                                type: 'index'
                            });
                        }
                    }
                } else {
                    // For object pointers, get the id() of the pointer variable as string
                    // Use 'watch' context to access local variables in the current stack frame
                    const idExpr = `str(id(${pointer.expression})) if ${pointer.expression} is not None else ''`;
                    const idResult = await this.sessionManager.evaluate(idExpr, 'watch');

                    if (idResult) {
                        // Clean up the string result (remove quotes)
                        let pythonId = idResult.trim();
                        if ((pythonId.startsWith("'") && pythonId.endsWith("'")) ||
                            (pythonId.startsWith('"') && pythonId.endsWith('"'))) {
                            pythonId = pythonId.slice(1, -1);
                        }

                        if (pythonId && pythonId !== '') {
                            markers.push({
                                pythonId,
                                color: pointer.color,
                                label: pointer.label,
                                type: 'object'
                            });
                        }
                    }
                }
            } catch (error) {
                // Skip this pointer if evaluation fails (variable might not exist)
                console.log(`Failed to evaluate pointer ${pointer.expression}:`, error);
            }
        }

        // Add markers to the visualization data
        console.log('[PDV-DEBUG] Markers created:', JSON.stringify(markers));

        // Log pythonIds in tree for comparison
        if (result.result.data.root) {
            const treeIds: string[] = [];
            const collectIds = (node: any) => {
                if (!node) return;
                if (node.pythonId) treeIds.push(String(node.pythonId));
                if (node.children) node.children.forEach(collectIds);
            };
            collectIds(result.result.data.root);
            console.log('[PDV-DEBUG] Tree pythonIds:', treeIds);
        }

        if (markers.length > 0) {
            result.result.data.markers = markers;
        }

        return result;
    }

    /**
     * Build the Python expression to visualize a value.
     * Uses __import__ inline - Python caches imports after first call so this is fast.
     */
    private buildVisualizationExpression(
        expression: string,
        preferredExtractorId?: string
    ): string {
        const maxItems = this.config.maxItems;
        const maxDepth = this.config.maxDepth;

        let args = `${expression}`;
        if (preferredExtractorId) {
            args += `, preferred_extractor="${preferredExtractorId}"`;
        }
        args += `, max_depth=${maxDepth}, max_items=${maxItems}`;

        // Use __import__ inline - Python caches modules in sys.modules after first import
        return `__import__('pydebugvisualizer').visualize(${args})`;
    }

    /**
     * Parse the visualization result from Python.
     */
    private parseVisualizationResult(resultStr: string): VisualizationResult {
        // Remove Python string quotes if present
        let cleaned = resultStr;
        if ((cleaned.startsWith("'") && cleaned.endsWith("'")) ||
            (cleaned.startsWith('"') && cleaned.endsWith('"'))) {
            cleaned = cleaned.slice(1, -1);
        }

        // Unescape Python string escapes
        cleaned = cleaned
            .replace(/\\'/g, "'")
            .replace(/\\"/g, '"')
            .replace(/\\\\/g, '\\')
            .replace(/\\n/g, '\n')
            .replace(/\\t/g, '\t');

        try {
            const parsed = JSON.parse(cleaned);

            return {
                kind: 'data',
                result: {
                    data: parsed.data,
                    usedExtractor: parsed.usedExtractor,
                    availableExtractors: parsed.availableExtractors || []
                }
            };
        } catch (e) {
            return {
                kind: 'error',
                message: `Failed to parse visualization result: ${e}\n\nRaw result: ${resultStr.slice(0, 500)}`
            };
        }
    }

    /**
     * Handle errors during visualization.
     */
    private handleError(error: unknown): VisualizationResult {
        const message = error instanceof Error ? error.message : String(error);

        // Check for common errors
        if (message.includes('pydebugvisualizer') && message.includes('not installed')) {
            return {
                kind: 'error',
                message: 'pydebugvisualizer package not found.\n\nInstall with:\n  pip install pydebugvisualizer'
            };
        }

        if (message.includes('NameError')) {
            return {
                kind: 'error',
                message: `Variable not found: ${message}`
            };
        }

        // Handle timeout errors
        if (message.includes('did not finish') || message.includes('timeout') || message.includes('PYDEVD_WARN_EVALUATION_TIMEOUT')) {
            return {
                kind: 'error',
                message: 'Evaluation timeout. The visualization is taking too long.\n\n' +
                    'Try:\n' +
                    '1. Restart debugging (F5)\n' +
                    '2. Set environment variable: PYDEVD_WARN_EVALUATION_TIMEOUT=10\n' +
                    '3. Use simpler data structures'
            };
        }

        return {
            kind: 'error',
            message: `Error evaluating expression:\n${message}`
        };
    }

    /**
     * Get completions for an expression.
     */
    async getCompletions(text: string, column: number): Promise<{ label: string; kind: number }[]> {
        return this.sessionManager.getCompletions(text, column);
    }

    dispose(): void {
        // Cleanup if needed
    }
}
