/* The desktop is a transient text filesystem, not a Linux kernel. Runtime code
 * executes in opaque-origin data URL workers, never in the document itself. */
(() => {
    "use strict";
    const $ = id => document.getElementById(id);
    if (!$('workspace'))
        return;
    const MAX_FILE = 256 * 1024;
    const MAX_TOTAL = 2 * 1024 * 1024;
    const MAX_FILES = 200;
    const encoder = new TextEncoder();
    const bytes = text => encoder.encode(text).length;
    const initial = () => new Map([
        ['/notes.txt', 'Bienvenue dans ton atelier.\nÉcris ici, puis enregistre ou exporte tes notes.\n'],
        ['/hello.py', 'print("Hello, Terminal!")\nprint(sum(range(10)))\n'],
        ['/hello.js', 'console.log("Hello, Terminal!");\nconsole.log(6 * 7);\n']
    ]);
    let files = initial(), folders = new Set(['/']), trash = new Map();
    let cwd = '/', fileDir = '/', history = [], historyIndex = 0;
    let python = null, javascript = null, busy = false, timer = null;
    let outputCount = 0;
    const status = message => { $('workspace-status').textContent = message; };
    const output = message => {
        if (busy && ++outputCount > 500) {
            stop();
            return;
        }
        const line = document.createElement('p');
        line.textContent = String(message).slice(0, 12000);
        $('shell-output').append(line);
        while ($('shell-output').children.length > 200)
            $('shell-output').firstChild.remove();
        $('shell-output').scrollTop = $('shell-output').scrollHeight;
    };
    function path(value, base = cwd) {
        if (!value || value.length > 240 || /[\u0000-\u001f\\]/.test(value))
            throw Error('Chemin invalide.');
        const parts = [];
        for (const part of (value.startsWith('/') ? value : base + '/' + value).split('/')) {
            if (!part || part === '.')
                continue;
            if (part === '..')
                parts.pop();
            else
                parts.push(part);
        }
        return '/' + parts.join('/');
    }
    const parent = value => value.slice(0, value.lastIndexOf('/')) || '/';
    const name = value => value.split('/').at(-1);
    function store(target, text) {
        if (target === '/' || folders.has(target) || !folders.has(parent(target)))
            throw Error('Dossier parent inexistant ou chemin réservé.');
        const total = [...files].reduce((n, [p, value]) => n + (p === target ? 0 : bytes(value)), 0);
        const trashSize = [...trash.values()].reduce((n, value) => n + bytes(value), 0);
        if (bytes(text) > MAX_FILE || total + trashSize + bytes(text) > MAX_TOTAL || (!files.has(target) && files.size + trash.size >= MAX_FILES))
            throw Error('Limite de session : 200 fichiers, 256 Kio par fichier, 2 Mio au total.');
        files.set(target, text);
    }
    function directory(target) {
        if (target === '/' || files.has(target) || folders.has(target) || !folders.has(parent(target)))
            throw Error('Impossible de créer ce dossier.');
        if (folders.size >= MAX_FILES)
            throw Error('Limite de dossiers atteinte.');
        folders.add(target);
    }
    function remove(target) {
        if (!files.has(target))
            throw Error('Fichier introuvable.');
        if (trash.has(target))
            throw Error('Un fichier de ce nom est déjà dans la corbeille.');
        trash.set(target, files.get(target));
        files.delete(target);
    }
    function download(filename, content, type = 'text/plain;charset=utf-8') {
        const url = URL.createObjectURL(new Blob([content], { type }));
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.append(a);
        a.click();
        a.remove();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
    }
    function button(label, action) {
        const el = document.createElement('button');
        el.type = 'button';
        el.textContent = label;
        el.addEventListener('click', () => attempt(action));
        return el;
    }
    function attempt(action) {
        try {
            action();
        }
        catch (error) {
            status(error.message);
        }
    }
    function listRow(container, label, buttons) {
        const row = document.createElement('div');
        row.className = 'file-row';
        const title = document.createElement('span');
        title.textContent = label;
        row.append(title, ...buttons);
        container.append(row);
    }
    function refresh() {
        $('shell-prompt').textContent = `guest:${cwd}$`;
        $('file-path').textContent = fileDir;
        $('file-list').replaceChildren();
        $('trash-list').replaceChildren();
        const entries = [...folders].filter(p => p !== '/' && parent(p) === fileDir).sort();
        for (const p of entries)
            listRow($('file-list'), `${name(p)}/`, [button('Ouvrir', () => { fileDir = p; refresh(); }), button('Supprimer', () => {
                    if ([...folders, ...files.keys()].some(x => x.startsWith(p + '/')))
                        throw Error('Dossier non vide.');
                    if (cwd === p)
                        cwd = '/';
                    folders.delete(p);
                    refresh();
                })]);
        for (const p of [...files.keys()].filter(p => parent(p) === fileDir).sort())
            listRow($('file-list'), `${name(p)} · ${bytes(files.get(p))} o`, [
                button('Ouvrir', () => openFile(p)), button('Exporter', () => download(name(p), files.get(p))), button('Corbeille', () => { remove(p); refresh(); })
            ]);
        for (const p of [...trash.keys()].sort())
            listRow($('trash-list'), p, [button('Restaurer', () => {
                    if (files.has(p) || folders.has(p) || !folders.has(parent(p)))
                        throw Error('Chemin indisponible.');
                    const value = trash.get(p);
                    trash.delete(p);
                    try {
                        store(p, value);
                    }
                    catch (error) {
                        trash.set(p, value);
                        throw error;
                    }
                    refresh();
                })]);
        if (!$('file-list').children.length)
            $('file-list').textContent = 'Dossier vide.';
        if (!$('trash-list').children.length)
            $('trash-list').textContent = 'Corbeille vide.';
    }
    function switchApp(app) {
        for (const el of document.querySelectorAll('[data-app]'))
            el.setAttribute('aria-pressed', String(el.dataset.app === app));
        for (const el of document.querySelectorAll('[data-window]'))
            el.hidden = el.dataset.window !== app;
        refresh();
    }
    function openFile(p) {
        const app = /\.(py|js|html|css|json|ts)$/i.test(p) ? 'code' : 'notes';
        const prefix = app === 'code' ? 'code' : 'note';
        $(prefix + '-path').value = p;
        $(prefix + '-editor').value = files.get(p) || '';
        updateLines();
        switchApp(app);
    }
    function updateLines() {
        $('line-numbers').textContent = Array.from({ length: $('code-editor').value.split('\n').length }, (_, i) => i + 1).join('\n');
        $('line-numbers').scrollTop = $('code-editor').scrollTop;
    }
    function saveEditor(prefix) {
        const p = path($(prefix + '-path').value, '/');
        store(p, $(prefix + '-editor').value);
        refresh();
        status('Enregistré en mémoire : ' + p);
        return p;
    }
    // Python runs in an opaque-origin worker. Imports and installation are real.
    // User files are copied to/from a dedicated MEMFS subtree; packages remain in the worker.
    function pythonWorker() {
        const CDN = 'https://cdn.jsdelivr.net/pyodide/v0.27.5/full/';
        let runtime;
        const emit = text => postMessage({ kind: 'output', text: String(text).slice(0, 12000) });
        const valid = p => typeof p === 'string' && /^\/(?!\/)(?!.*(?:^|\/)\.\.?($|\/))[^\u0000-\u001f\\]{1,239}$/.test(p);
        onmessage = async ({ data }) => {
            try {
                if (!runtime) {
                    emit('Chargement de Python WebAssembly…');
                    importScripts(CDN + 'pyodide.js');
                    runtime = await loadPyodide({ indexURL: CDN });
                    runtime.setStdout({ batched: emit });
                    runtime.setStderr({ batched: emit });
                    runtime.FS.mkdirTree('/workspace');
                }
                const FS = runtime.FS;
                // Replace only the workspace snapshot, not installed packages.
                FS.chdir('/');
                function clean(dir) {
                    for (const entry of FS.readdir(dir)) {
                        if (entry === '.' || entry === '..')
                            continue;
                        const full = dir + '/' + entry;
                        if (FS.isDir(FS.lstat(full).mode)) {
                            clean(full);
                            FS.rmdir(full);
                        }
                        else
                            FS.unlink(full);
                    }
                }
                clean('/workspace');
                for (const p of data.folders)
                    if (p !== '/' && valid(p))
                        FS.mkdirTree('/workspace' + p);
                for (const [p, value] of data.files)
                    if (valid(p)) {
                        FS.mkdirTree('/workspace' + p.slice(0, p.lastIndexOf('/')));
                        FS.writeFile('/workspace' + p, value);
                    }
                FS.chdir('/workspace' + (data.cwd === '/' ? '' : data.cwd));
                let error = '';
                try {
                    if (data.action === 'install') {
                        await runtime.loadPackage('micropip');
                        runtime.globals.set('_terminal_package', data.code);
                        await runtime.runPythonAsync('import micropip\nawait micropip.install(_terminal_package)');
                        emit('Installation terminée : ' + data.code);
                    }
                    else {
                        const result = await runtime.runPythonAsync(data.code);
                        if (result !== undefined) {
                            emit(String(result));
                            if (result && typeof result.destroy === 'function')
                                result.destroy();
                        }
                    }
                }
                catch (e) {
                    error = String(e);
                    emit(error);
                }
                // Synchronize text files only. Symlinks are deliberately excluded.
                const exported = [], dirs = ['/'];
                let size = 0;
                function walk(dir, relative) {
                    for (const entry of FS.readdir(dir)) {
                        if (entry === '.' || entry === '..')
                            continue;
                        const p = relative + '/' + entry, full = dir + '/' + entry;
                        if (!valid(p))
                            throw Error('Nom de fichier non compatible.');
                        const info = FS.lstat(full);
                        if (FS.isDir(info.mode)) {
                            if (dirs.length >= 200)
                                throw Error('Trop de dossiers.');
                            dirs.push(p);
                            walk(full, p);
                        }
                        else if (FS.isFile(info.mode)) {
                            size += info.size;
                            if (info.size > 262144 || size > 2097152 || exported.length >= 200)
                                throw Error('Limite de fichiers dépassée.');
                            const raw = FS.readFile(full);
                            const text = new TextDecoder('utf-8', { fatal: true }).decode(raw);
                            exported.push([p, text]);
                        }
                    }
                }
                walk('/workspace', '');
                postMessage({ kind: 'done', files: exported, folders: dirs, error });
            }
            catch (e) {
                postMessage({ kind: 'error', text: String(e) });
            }
        };
    }
    function workerFrom(source) {
        return new Worker('data:text/javascript;charset=utf-8,' + encodeURIComponent(source));
    }
    function finish(message) { clearTimeout(timer); busy = false; status(message); }
    function stop() {
        if (python)
            python.terminate();
        if (javascript)
            javascript.terminate();
        python = javascript = null;
        finish('Calcul arrêté. Runtime Python réinitialisé.');
        output('Runtime arrêté. Les fichiers enregistrés sont conservés.');
    }
    function startTimeout() { outputCount = 0; clearTimeout(timer); timer = setTimeout(() => { stop(); output('Délai maximal de 120 secondes atteint.'); }, 120000); }
    function applyPythonFiles(data) {
        if (!Array.isArray(data.files) || !Array.isArray(data.folders))
            throw Error('Réponse runtime invalide.');
        const previous = files, previousDirs = folders;
        files = new Map();
        folders = new Set(['/']);
        try {
            for (const p of data.folders.sort((a, b) => a.length - b.length))
                if (p !== '/')
                    directory(path(p, '/'));
            for (const [p, value] of data.files) {
                if (typeof value !== 'string')
                    throw Error('Fichier invalide.');
                store(path(p, '/'), value);
            }
        }
        catch (e) {
            files = previous;
            folders = previousDirs;
            throw e;
        }
        if (!folders.has(cwd))
            cwd = '/';
        if (!folders.has(fileDir))
            fileDir = '/';
        refresh();
    }
    function runPython(code, action = 'run') {
        if (busy)
            throw Error('Un calcul est déjà en cours.');
        if (!python) {
            python = workerFrom(`(${pythonWorker.toString()})();`);
            python.onmessage = ({ data }) => {
                if (data.kind === 'output') {
                    output(data.text);
                    return;
                }
                if (data.kind === 'done') {
                    try {
                        applyPythonFiles(data);
                        finish(data.error ? 'Python : erreur' : 'Python : terminé');
                    }
                    catch (e) {
                        output(e.message);
                        stop();
                    }
                    return;
                }
                if (data.kind === 'error') {
                    output(data.text);
                    stop();
                }
            };
            python.onerror = e => { output('Python indisponible : ' + (e.message || 'chargement bloqué')); stop(); };
        }
        busy = true;
        status('Python en cours…');
        startTimeout();
        python.postMessage({ code, action, files: [...files], folders: [...folders], cwd });
    }
    function runJS(code) {
        if (busy)
            throw Error('Un calcul est déjà en cours.');
        // Compile source inside a separate opaque worker, without eval in the document.
        const source = `const send=(...v)=>postMessage({kind:'output',text:v.map(x=>typeof x==='string'?x:JSON.stringify(x)??String(x)).join(' ')});\nconsole.log=console.info=console.warn=console.error=send;\n(async()=>{\n${code}\n})().then(()=>postMessage({kind:'done'}),e=>postMessage({kind:'error',text:String(e)}));`;
        javascript = workerFrom(source);
        busy = true;
        status('JavaScript en cours…');
        startTimeout();
        javascript.onmessage = ({ data }) => { if (data.kind === 'output')
            output(data.text);
        else if (['done', 'error'].includes(data.kind)) {
            if (data.kind === 'error')
                output(data.text);
            javascript.terminate();
            javascript = null;
            finish('JavaScript : terminé');
        } };
        javascript.onerror = e => { output(e.message || 'Erreur JavaScript'); javascript.terminate(); javascript = null; finish('JavaScript : erreur'); };
    }
    function command(raw) {
        const [cmd, ...args] = raw.trim().split(/\s+/), rest = raw.trim().slice(cmd.length).trim();
        const target = () => path(rest);
        if (busy && !['help', 'pwd', 'ls', 'cat', 'clear'].includes(cmd))
            throw Error('Attends la fin du calcul.');
        switch (cmd) {
            case 'help':
                output('help, pwd, ls [dossier], cd dossier, mkdir dossier, touch fichier, cat fichier, echo texte [> fichier], rm fichier, clear, python <code|fichier.py>, pip install <paquet>, js <code|fichier.js>');
                break;
            case 'pwd':
                output(cwd);
                break;
            case 'ls': {
                const dir = rest ? target() : cwd;
                if (!folders.has(dir))
                    throw Error('Dossier introuvable.');
                output([...folders].filter(p => p !== '/' && parent(p) === dir).map(p => name(p) + '/').concat([...files.keys()].filter(p => parent(p) === dir).map(name)).sort().join('\n') || '(vide)');
                break;
            }
            case 'cd': {
                const dir = rest ? target() : '/';
                if (!folders.has(dir))
                    throw Error('Dossier introuvable.');
                cwd = dir;
                break;
            }
            case 'mkdir':
                directory(target());
                break;
            case 'touch': {
                const p = target();
                if (!files.has(p))
                    store(p, '');
                break;
            }
            case 'cat': {
                const p = target();
                if (!files.has(p))
                    throw Error('Fichier introuvable.');
                output(files.get(p));
                break;
            }
            case 'rm':
                remove(target());
                break;
            case 'echo': {
                const redirect = rest.match(/^(.*?)\s+>\s+(.+)$/);
                if (redirect)
                    store(path(redirect[2]), redirect[1] + '\n');
                else
                    output(rest);
                break;
            }
            case 'clear':
                $('shell-output').replaceChildren();
                break;
            case 'python':
            case 'js': {
                if (!rest)
                    throw Error('Indique du code ou un fichier.');
                let source = rest;
                if (/^[\w./-]+\.(py|js)$/.test(rest)) {
                    const p = target();
                    if (!files.has(p))
                        throw Error('Fichier introuvable.');
                    source = files.get(p);
                }
                if (cmd === 'python')
                    runPython(source);
                else
                    runJS(source);
                break;
            }
            case 'pip':
                if (args.length === 2 && args[0] === 'install' && /^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}(==[A-Za-z0-9_.-]{1,40})?$/.test(args[1]))
                    runPython(args[1], 'install');
                else
                    throw Error('Usage : pip install nom-du-paquet[==version]');
                break;
            default: throw Error('Commande inconnue : ' + cmd + '. Tape help.');
        }
        refresh();
    }
    // UI events and session lifecycle. No localStorage, IndexedDB or service worker.
    for (const el of document.querySelectorAll('[data-app]'))
        el.addEventListener('click', () => switchApp(el.dataset.app));
    $('shell-form').addEventListener('submit', event => { event.preventDefault(); const input = $('shell-command'), raw = input.value.trim(); if (!raw)
        return; history.push(raw); if (history.length > 100)
        history.shift(); historyIndex = history.length; input.value = ''; output(`guest:${cwd}$ ${raw}`); try {
        command(raw);
    }
    catch (e) {
        output(e.message);
    } });
    $('shell-command').addEventListener('keydown', e => { if (!['ArrowUp', 'ArrowDown'].includes(e.key))
        return; e.preventDefault(); historyIndex = Math.max(0, Math.min(history.length, historyIndex + (e.key === 'ArrowUp' ? -1 : 1))); e.target.value = history[historyIndex] || ''; });
    $('stop-run').onclick = stop;
    $('clear-shell').onclick = () => $('shell-output').replaceChildren();
    $('parent-dir').onclick = () => { fileDir = parent(fileDir); refresh(); };
    const askName = label => { const value = window.prompt(label); return value === null ? null : path(value, fileDir); };
    $('new-file').onclick = () => attempt(() => { const p = askName('Nom du fichier'); if (p && !files.has(p)) {
        if (busy)
            throw Error('Calcul en cours.');
        store(p, '');
        refresh();
    } });
    $('new-folder').onclick = () => attempt(() => { const p = askName('Nom du dossier'); if (p) {
        if (busy)
            throw Error('Calcul en cours.');
        directory(p);
        refresh();
    } });
    $('file-import').onchange = async (e) => { if (busy) {
        status('Calcul en cours.');
        e.target.value = '';
        return;
    } for (const file of e.target.files) {
        try {
            if (file.size > MAX_FILE)
                throw Error('Fichier trop grand.');
            const text = new TextDecoder('utf-8', { fatal: true }).decode(await file.arrayBuffer());
            const p = path(file.name, fileDir);
            if (busy || files.has(p))
                throw Error('Calcul en cours ou fichier existant.');
            store(p, text);
        }
        catch (error) {
            status(error.message);
        }
    } e.target.value = ''; refresh(); };
    $('export-all').onclick = () => download('terminal-session.json', JSON.stringify({ folders: [...folders], files: Object.fromEntries(files) }, null, 2), 'application/json');
    $('empty-trash').onclick = () => { if (confirm('Vider définitivement la corbeille virtuelle ?')) {
        trash.clear();
        refresh();
    } };
    for (const prefix of ['note', 'code']) {
        $(prefix + '-editor').value = files.get($(prefix + '-path').value) || '';
        $('save-' + prefix).onclick = () => attempt(() => { if (busy)
            throw Error('Calcul en cours.'); saveEditor(prefix); });
        $('download-' + prefix).onclick = () => attempt(() => download(name(path($(prefix + '-path').value, '/')), $(prefix + '-editor').value));
        $(prefix + '-editor').addEventListener('keydown', e => { if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
            e.preventDefault();
            $('save-' + prefix).click();
        } });
    }
    $('code-editor').addEventListener('input', updateLines);
    $('code-editor').addEventListener('scroll', updateLines);
    let escapeTab = false;
    $('code-editor').addEventListener('keydown', e => { if (e.key === 'Escape') {
        escapeTab = true;
        return;
    } if (e.key === 'Tab' && !e.shiftKey && !escapeTab) {
        e.preventDefault();
        e.target.setRangeText('  ', e.target.selectionStart, e.target.selectionEnd, 'end');
        updateLines();
    } escapeTab = false; });
    $('run-code').onclick = () => attempt(() => { if (busy)
        throw Error('Calcul en cours.'); const p = saveEditor('code'); if (!/\.(py|js)$/.test(p))
        throw Error('Choisis un fichier .py ou .js.'); switchApp('shell'); output('Exécution : ' + p); if (p.endsWith('.py'))
        runPython(files.get(p));
    else
        runJS(files.get(p)); });
    $('web-form').onsubmit = e => { e.preventDefault(); const raw = $('web-query').value.trim(); if (!raw)
        return; let url; try {
        url = new URL(raw);
        if (!['https:', 'http:'].includes(url.protocol))
            throw Error();
    }
    catch (_) {
        url = new URL('https://duckduckgo.com/');
        url.searchParams.set('q', raw);
    } window.open(url.href, '_blank', 'noopener,noreferrer'); };
    $('wiki-form').onsubmit = async (e) => { e.preventDefault(); const q = $('wiki-query').value.trim(), panel = $('web-results'); if (!q)
        return; panel.textContent = 'Recherche…'; try {
        const url = new URL('https://fr.wikipedia.org/w/api.php');
        url.search = new URLSearchParams({ action: 'query', list: 'search', srsearch: q, srlimit: '8', format: 'json', origin: '*' });
        const response = await fetch(url, { credentials: 'omit', signal: AbortSignal.timeout(15000) });
        if (!response.ok)
            throw Error();
        const data = await response.json();
        panel.replaceChildren();
        for (const result of data.query.search) {
            const link = document.createElement('a');
            link.textContent = result.title;
            link.href = 'https://fr.wikipedia.org/?curid=' + encodeURIComponent(result.pageid);
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            panel.append(link);
        }
        if (!panel.children.length)
            panel.textContent = 'Aucun résultat.';
    }
    catch (_) {
        panel.textContent = 'Recherche indisponible. Utilise la recherche Web dans un nouvel onglet.';
    } };
    $('reset-session').onclick = () => { if (!confirm('Effacer tous les fichiers et paquets de cette session ?'))
        return; stop(); files = initial(); folders = new Set(['/']); trash = new Map(); cwd = fileDir = '/'; history = []; historyIndex = 0; $('note-path').value = '/notes.txt'; $('code-path').value = '/hello.py'; $('note-editor').value = files.get('/notes.txt'); $('code-editor').value = files.get('/hello.py'); $('shell-output').replaceChildren(); output('Nouvelle session. Tape help.'); updateLines(); switchApp('shell'); status('Session prête'); };
    // BFCache may preserve a page on navigation. Terminate runtimes and discard the
    // ephemeral state when leaving, even if the browser restores its document.
    window.addEventListener('pagehide', () => { if (python)
        python.terminate(); if (javascript)
        javascript.terminate(); });
    window.addEventListener('pageshow', e => { if (e.persisted)
        location.reload(); });
    // Block destructive file operations while a Python snapshot is in flight.
    $('workspace').addEventListener('click', e => { if (busy && e.target.closest('#file-list, #trash-list, #empty-trash')) {
        e.stopImmediatePropagation();
        status('Calcul en cours.');
    } }, true);
    updateLines();
    refresh();
    output('Atelier local. Les fichiers sont temporaires. Tape help pour les commandes.');
    $('workspace').hidden = false;
})();
