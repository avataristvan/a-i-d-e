#!/usr/bin/env node
// Semantic rename locations for TS/JS via the project's own TypeScript language service.
// stdin:  {root, file, line?, symbol, findInStrings, findInComments}
// stdout: {ok, typescript, tsconfig, oldName, locations:[{file,line,character,length,prefix,suffix}], skipped:[file]}
//
// findRenameLocations is asymmetric: from a declaration it does not always reach consumers that
// see the property through derived types (ReturnType<...> & ..., destructuring of a hook result),
// while from the consumer it does reach the declaration. So we ask once per same-named identifier
// occurrence and merge every location group that overlaps the target's group until a fixpoint.
// Same-named identifiers whose group never touches the target belong to other symbols and stay.
'use strict';
const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

function fail(message) {
  process.stdout.write(JSON.stringify({ ok: false, message }));
  process.exit(0);
}

// The project's own typescript first, then a global one. Only versions exposing the JS
// LanguageService API qualify (TypeScript 7, the native port, does not).
function loadTypeScript(root, file) {
  const candidates = [];
  try { candidates.push(require.resolve('typescript', { paths: [path.dirname(file), root] })); } catch (_) { /* none local */ }
  const npmRoot = spawnSync('npm', ['root', '-g'], { encoding: 'utf8' }).stdout?.trim();
  if (npmRoot) {
    candidates.push(path.join(npmRoot, 'typescript'), path.join(npmRoot, 'typescript-language-server', 'node_modules', 'typescript'));
  }
  const unusable = [];
  for (const c of candidates) {
    let ts;
    try { ts = require(c); } catch (_) { continue; }
    if (typeof ts.createLanguageService === 'function') return ts;
    unusable.push(`${c} (${ts.version || 'unknown version'})`);
  }
  fail(`No 'typescript' package with the LanguageService API found for ${root}` +
       (unusable.length ? `; unusable: ${unusable.join(', ')}` : '') + ' (install typescript 5.x in the project: npm i -D typescript@5)');
}

function findConfig(ts, file, root) {
  let dir = path.dirname(file);
  const stop = path.dirname(root);
  while (dir.startsWith(root) && dir !== stop) {
    for (const name of ['tsconfig.json', 'jsconfig.json']) {
      const p = path.join(dir, name);
      if (ts.sys.fileExists(p)) return p;
    }
    const up = path.dirname(dir);
    if (up === dir) break;
    dir = up;
  }
  return null;
}

// Files that must not be touched: inside a nested git repo/worktree (e.g. .claude/worktrees/agent-*),
// gitignored, or under node_modules.
function makeExcluder(root, files) {
  const nestedCache = new Map();
  function inNestedRepo(file) {
    let dir = path.dirname(file);
    const chain = [];
    let hit = false;
    while (dir.length > root.length && dir.startsWith(root)) {
      if (nestedCache.has(dir)) { hit = nestedCache.get(dir); break; }
      chain.push(dir);
      if (fs.existsSync(path.join(dir, '.git'))) { hit = true; break; }
      dir = path.dirname(dir);
    }
    for (const d of chain) nestedCache.set(d, hit);
    return hit;
  }
  const ignored = new Set();
  const git = spawnSync('git', ['-C', root, 'check-ignore', '--stdin'], { input: files.join('\n'), encoding: 'utf8' });
  if (git.status === 0 || git.status === 1) {
    for (const line of (git.stdout || '').split('\n')) if (line) ignored.add(path.resolve(root, line));
  }
  return (file) => file.split(path.sep).includes('node_modules') || ignored.has(file) || inNestedRepo(file);
}

function main() {
  const req = JSON.parse(fs.readFileSync(0, 'utf8'));
  const root = path.resolve(req.root);
  const file = path.resolve(root, req.file);
  const ts = loadTypeScript(root, file);

  const configPath = findConfig(ts, file, root);
  let options = { allowJs: true, jsx: ts.JsxEmit.Preserve };
  let fileNames;
  if (configPath) {
    const parsed = ts.getParsedCommandLineOfConfigFile(configPath, {}, { ...ts.sys, onUnRecoverableConfigFileDiagnostic: () => {} });
    if (!parsed) fail(`Could not parse ${configPath}`);
    options = parsed.options;
    fileNames = parsed.fileNames.map((f) => path.resolve(f));
  } else {
    fileNames = ts.sys.readDirectory(root, ['.ts', '.tsx', '.mts', '.cts', '.js', '.jsx', '.mjs', '.cjs'], ['**/node_modules'], undefined)
      .map((f) => path.resolve(f));
  }
  const excluded = makeExcluder(root, fileNames);
  const projectFiles = fileNames.filter((f) => !excluded(f));
  if (!projectFiles.includes(file)) projectFiles.push(file);

  const host = {
    getScriptFileNames: () => projectFiles,
    getScriptVersion: () => '1',
    getScriptSnapshot: (f) => (ts.sys.fileExists(f) ? ts.ScriptSnapshot.fromString(ts.sys.readFile(f)) : undefined),
    getCurrentDirectory: () => root,
    getCompilationSettings: () => options,
    getDefaultLibFileName: (o) => ts.getDefaultLibFilePath(o),
    fileExists: ts.sys.fileExists,
    readFile: ts.sys.readFile,
    readDirectory: ts.sys.readDirectory,
    directoryExists: ts.sys.directoryExists,
    getDirectories: ts.sys.getDirectories,
    realpath: ts.sys.realpath,
  };
  const ls = ts.createLanguageService(host, ts.createDocumentRegistry());
  const program = ls.getProgram();

  const name = req.symbol;
  const wordRe = new RegExp(`(?<![\\w$])${name.replace(/[$]/g, '\\$')}(?![\\w$])`, 'g');

  // Start position: first occurrence of the symbol on the given line (1-based), else in the file.
  const startText = ts.sys.readFile(file);
  if (startText === undefined) fail(`Cannot read ${file}`);
  const startSf = program.getSourceFile(file);
  if (!startSf) fail(`${file} is not part of the TypeScript program`);
  let startPos = -1;
  for (const m of startText.matchAll(wordRe)) {
    const line = startSf.getLineAndCharacterOfPosition(m.index).line + 1;
    if (req.line && line !== req.line) continue;
    const info = ls.getRenameInfo(file, m.index, { allowRenameOfImportPath: false });
    if (info.canRename) { startPos = m.index; break; }
  }
  if (startPos < 0) fail(`No renameable '${name}' found in ${path.relative(root, file)}${req.line ? ` on line ${req.line}` : ''}`);

  const prefs = { providePrefixAndSuffixTextForRename: false };
  const key = (l) => `${l.fileName}:${l.textSpan.start}`;
  const groupAt = (f, pos) => ls.findRenameLocations(f, pos, !!req.findInStrings, !!req.findInComments, prefs) || [];

  const target = new Map(groupAt(file, startPos).map((l) => [key(l), l]));

  // Candidate groups: one per same-named occurrence in project files.
  const groups = [];
  const seen = new Set(target.keys());
  for (const f of projectFiles) {
    const sf = program.getSourceFile(f);
    if (!sf || sf.isDeclarationFile) continue;
    const text = sf.text;
    for (const m of text.matchAll(wordRe)) {
      if (seen.has(`${f}:${m.index}`)) continue;
      const g = groupAt(f, m.index);
      if (!g.length) continue;
      for (const l of g) seen.add(key(l));
      groups.push(g);
    }
  }
  let changed = true;
  while (changed) {
    changed = false;
    for (let i = groups.length - 1; i >= 0; i--) {
      if (groups[i].some((l) => target.has(key(l)))) {
        for (const l of groups[i]) target.set(key(l), l);
        groups.splice(i, 1);
        changed = true;
      }
    }
  }

  const locations = [];
  const skipped = new Set();
  for (const l of target.values()) {
    const f = path.resolve(l.fileName);
    const sf = program.getSourceFile(l.fileName);
    if (!sf || sf.isDeclarationFile || excluded(f) || !f.startsWith(root + path.sep)) { skipped.add(f); continue; }
    const lc = sf.getLineAndCharacterOfPosition(l.textSpan.start);
    locations.push({ file: f, line: lc.line, character: lc.character, length: l.textSpan.length,
                     prefix: l.prefixText || '', suffix: l.suffixText || '' });
  }
  locations.sort((a, b) => a.file.localeCompare(b.file) || a.line - b.line || a.character - b.character);
  process.stdout.write(JSON.stringify({
    ok: true, typescript: ts.version, tsconfig: configPath, oldName: name,
    locations, skipped: [...skipped].sort(),
  }));
}

try { main(); } catch (e) { fail(String(e && e.stack || e)); }
