/**
 * RepoBrain VS Code / Cursor / Windsurf Extension
 * Surfaces zero-bloat AST memory, live static blast radius,
 * autonomous CI test self-healing, and LangGraph multi-agent swarms.
 */

import * as vscode from 'vscode';
import * as child_process from 'child_process';
import * as path from 'path';

let outputChannel: vscode.OutputChannel;
let statusBarItem: vscode.StatusBarItem;

export function activate(context: vscode.ExtensionContext) {
  outputChannel = vscode.window.createOutputChannel('RepoBrain Engine');
  context.subscriptions.push(outputChannel);

  outputChannel.appendLine('[+] RepoBrain Engine Extension activated.');

  // 1. Create Status Bar Item
  statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
  statusBarItem.command = 'repobrain.openWorkbench';
  statusBarItem.text = '$(chip) RepoBrain: Active';
  statusBarItem.tooltip = 'RepoBrain Autonomous Codebase Memory • Click to Open Workbench';
  statusBarItem.show();
  context.subscriptions.push(statusBarItem);

  // 2. Register Blast Radius CodeLens Provider
  const codeLensProvider = new BlastRadiusCodeLensProvider();
  const supportedSelector: vscode.DocumentSelector = [
    { language: 'python', scheme: 'file' },
    { language: 'typescript', scheme: 'file' },
    { language: 'javascript', scheme: 'file' },
    { language: 'typescriptreact', scheme: 'file' },
    { language: 'javascriptreact', scheme: 'file' },
  ];
  context.subscriptions.push(
    vscode.languages.registerCodeLensProvider(supportedSelector, codeLensProvider)
  );

  // 3. Register Commands
  context.subscriptions.push(
    vscode.commands.registerCommand('repobrain.openWorkbench', () => {
      const config = vscode.workspace.getConfiguration('repobrain');
      const url = config.get<string>('workbenchUrl', 'http://localhost:5173');
      vscode.env.openExternal(vscode.Uri.parse(url));
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('repobrain.analyzeBlastRadius', async (symbol?: string, filePath?: string) => {
      let targetSymbol = symbol;
      if (!targetSymbol) {
        targetSymbol = await vscode.window.showInputBox({
          prompt: 'Enter function or class symbol to compute blast radius',
          placeHolder: 'e.g. settleInvoiceById, compute_git_blob_sha',
        });
      }
      if (!targetSymbol) return;

      runCliCommand(['blast-radius', targetSymbol], `Computing Blast Radius for '${targetSymbol}'...`);
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('repobrain.healTest', async (uri?: vscode.Uri) => {
      let testPath: string | undefined = uri ? getWorkspaceRelativePath(uri.fsPath) : undefined;

      if (!testPath && vscode.window.activeTextEditor) {
        const activeFile = vscode.window.activeTextEditor.document.fileName;
        if (activeFile.includes('test')) {
          testPath = getWorkspaceRelativePath(activeFile);
        }
      }

      if (!testPath) {
        testPath = await vscode.window.showInputBox({
          prompt: 'Path to failing test suite to heal autonomously',
          placeHolder: 'e.g. tests/test_service.py',
        });
      }
      if (!testPath) return;

      runCliCommand(['heal', testPath], `Autonomous CI Self-Healing on '${testPath}'...`);
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('repobrain.searchCodebase', async () => {
      const query = await vscode.window.showInputBox({
        prompt: 'Search Codebase via Two-Stage Hybrid RRF (k=60)',
        placeHolder: 'Symbol name or natural language query...',
      });
      if (!query) return;

      runCliCommand(['search', query], `Searching AST memory for '${query}'...`);
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('repobrain.swarmTask', async () => {
      const task = await vscode.window.showInputBox({
        prompt: 'Enter objective for RepoBrain Multi-Agent Swarm (LangGraph Native)',
        placeHolder: 'e.g. Fix calculation bug and verify against tests',
      });
      if (!task) return;

      runCliCommand(['swarm', task], `Dispatching Multi-Agent Swarm on '${task}'...`);
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('repobrain.runGates', () => {
      runCliCommand(['verify'], 'Running 4-Gate Deterministic Verification Stress Test...');
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('repobrain.toggleWatcher', () => {
      runCliCommand(['watch', '--once'], 'Running single incremental AST sync sweep...');
    })
  );
}

export function deactivate() {
  if (statusBarItem) statusBarItem.dispose();
  if (outputChannel) outputChannel.dispose();
}

/**
 * CodeLens Provider displaying Blast Radius actions above function and class definitions.
 */
class BlastRadiusCodeLensProvider implements vscode.CodeLensProvider {
  provideCodeLenses(
    document: vscode.TextDocument,
    token: vscode.CancellationToken
  ): vscode.CodeLens[] | Promise<vscode.CodeLens[]> {
    const config = vscode.workspace.getConfiguration('repobrain');
    if (!config.get<boolean>('enableCodeLens', true)) return [];

    const lenses: vscode.CodeLens[] = [];
    const text = document.getText();
    const lines = text.split(/\r?\n/);

    // Regex matchers for Python and TS/JS symbols
    const pyFnPattern = /^\s*(?:async\s+)?def\s+([a-zA-Z0-9_]+)\s*\(/;
    const pyClsPattern = /^\s*class\s+([a-zA-Z0-9_]+)\s*(?:\(|$|:)/;
    const tsFnPattern = /^\s*(?:export\s+)?(?:async\s+)?function\s+([a-zA-Z0-9_]+)\s*\(/;
    const tsConstPattern = /^\s*(?:export\s+)?const\s+([a-zA-Z0-9_]+)\s*=\s*(?:async\s*)?\(/;
    const tsClsPattern = /^\s*(?:export\s+)?class\s+([a-zA-Z0-9_]+)\s*/;

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      let match =
        line.match(pyFnPattern) ||
        line.match(pyClsPattern) ||
        line.match(tsFnPattern) ||
        line.match(tsConstPattern) ||
        line.match(tsClsPattern);

      if (match && match[1]) {
        const symbol = match[1];
        if (symbol.startsWith('__') && symbol.endsWith('__')) continue;

        const range = new vscode.Range(i, 0, i, line.length);
        const cmd: vscode.Command = {
          title: `⚡ Blast Radius: ${symbol}`,
          tooltip: `Inspect callers and static blast radius for ${symbol}`,
          command: 'repobrain.analyzeBlastRadius',
          arguments: [symbol, document.uri.fsPath],
        };
        lenses.push(new vscode.CodeLens(range, cmd));
      }
    }

    return lenses;
  }
}

/**
 * Executes a repobrain CLI command asynchronously and streams output.
 */
function runCliCommand(args: string[], progressTitle: string) {
  const root = getWorkspaceRoot();
  const config = vscode.workspace.getConfiguration('repobrain');
  const pythonPath = config.get<string>('pythonPath', 'python');

  outputChannel.show(true);
  outputChannel.appendLine(`\n------------------------------------------------------------`);
  outputChannel.appendLine(`[${new Date().toLocaleTimeString()}] [*] ${progressTitle}`);
  outputChannel.appendLine(`Command: ${pythonPath} -m repobrain.cli ${args.join(' ')}`);
  outputChannel.appendLine(`Directory: ${root}`);
  outputChannel.appendLine(`------------------------------------------------------------`);

  vscode.window.withProgress(
    {
      location: vscode.ProgressLocation.Notification,
      title: `RepoBrain: ${progressTitle}`,
      cancellable: false,
    },
    () => {
      return new Promise<void>((resolve) => {
        const env = { ...process.env, PYTHONPATH: path.join(root, 'src') };
        const proc = child_process.spawn(pythonPath, ['-m', 'repobrain.cli', ...args], {
          cwd: root,
          env,
          shell: process.platform === 'win32',
        });

        proc.stdout.on('data', (data) => {
          outputChannel.append(data.toString());
        });

        proc.stderr.on('data', (data) => {
          outputChannel.append(data.toString());
        });

        proc.on('close', (code) => {
          outputChannel.appendLine(`\n[+] Process finished with exit code ${code}.`);
          if (code === 0) {
            vscode.window.showInformationMessage(`RepoBrain: ${progressTitle} finished successfully.`);
          } else {
            vscode.window.showWarningMessage(`RepoBrain: Process exited with code ${code}. See Output panel.`);
          }
          resolve();
        });

        proc.on('error', (err) => {
          outputChannel.appendLine(`\n[!] Process error: ${err.message}`);
          vscode.window.showErrorMessage(`RepoBrain error: ${err.message}`);
          resolve();
        });
      });
    }
  );
}

function getWorkspaceRoot(): string {
  if (vscode.workspace.workspaceFolders && vscode.workspace.workspaceFolders.length > 0) {
    return vscode.workspace.workspaceFolders[0].uri.fsPath;
  }
  return process.cwd();
}

function getWorkspaceRelativePath(fullPath: string): string {
  const root = getWorkspaceRoot();
  return path.relative(root, fullPath).replace(/\\/g, '/');
}
