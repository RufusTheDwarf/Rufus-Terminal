# Browser workspace

## Architecture

`/lab/` is a static page generated from `src/lab.html`. It loads `src/lab.css` and `src/lab.js` via the generated assets. No server executes visitor code. Text files and directory metadata live in JS memory. Python and JavaScript execute in data URL Web Workers with opaque origins. Python loads on first use from the pinned Pyodide CDN, then micropip installs compatible packages. The Python worker copies the workspace snapshot into MEMFS and synchronizes UTF-8 text files back. JavaScript execution is a separate worker per command and does not provide Node.js or Python's filesystem API.

## Try it

```text
help
mkdir demo
cd demo
echo Hello > readme.txt
cat readme.txt
js console.log(6 * 7)
python print(sum(range(10)))
pip install humanize
python import humanize; print(humanize.intcomma(1234567))
python open('example.txt', 'w').write('Written from Python')
ls
```

The Python examples are integration checks to run after deployment, not recorded successful tests. Packages require a compatible wheel and a network connection. No apt, arbitrary native binaries, raw sockets, or host filesystem. The graphical interface is a web desktop, not an emulated operating system. Wikipedia search requires a live CORS-compatible API; other web pages open in the visitor's normal browser. No embedding bypass is attempted.

## Security and privacy

- No content persistence in localStorage, IndexedDB or a backend. Theme preferences from the main site are independent. Refresh, close, or navigate away to discard the session. Export explicitly to retain files. Browser caches and OS swap are outside the application's control.
- Data URL workers have opaque origins; they cannot read the main site's DOM, cookies or origin storage. The Chromium check verifies origin `null` and rejection of IndexedDB access. No arbitrary source is inserted in the document DOM.
- The lab-specific CSP permits `worker-src data:`, WebAssembly and the pinned CDN host, PyPI, Python package files and Wikipedia. The ordinary site CSP remains strict. The exception is scoped to `/lab/*`. This is not a formal security audit: test live response headers and review third-party code before wider deployment.
- Package code can execute in the worker. Network requests to allowed external endpoints are possible. Do not enter secrets or import confidential files. Third-party services receive requests when used.
- 200 files, 256 KiB per file, 2 MiB total for text data and 200 directories. Calculations have a 120-second timeout and output limit. These are application limits, not a hard cap on browser memory or CPU consumption. Stop terminates the runtime and removes its installed packages while retaining committed virtual files.
- Binary Python-generated files are not exported to the UI; synchronization requires valid UTF-8 text. File exports are explicit downloads.

## Verification

```powershell
py tools/build.py
py tools/check.py
py -m pip install playwright
py -m playwright install chromium
py tools/browser_check.py
py tools/lab_check.py
```

After deployment, inspect DevTools Network and Console, test Python and package installation, run a real Wikipedia query, verify that refresh resets the workspace and inspect headers:

```powershell
curl.exe -I https://terminal.rutsumello.workers.dev/
curl.exe -I https://terminal.rutsumello.workers.dev/lab/
```

The root must retain the original CSP; only the lab should allow its additional sources. If the lab CSP or CDN loading fails, diagnose actual browser messages rather than relaxing the entire site policy.

## Next step: a real PC

A Linux system with apt and a graphical desktop would be a separate experiment, e.g. v86 (x86 emulation) or CheerpX (Linux userspace). It needs a licensed OS image, explicit RAM limits, an ephemeral writable overlay and a reviewed networking strategy. Browsers do not offer unrestricted TCP networking to a WASM guest. Hosting the runtime on a separate origin is preferable for a production sandbox. The current workspace is intentionally not represented as that system.
