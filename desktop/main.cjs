const { app, BrowserWindow, dialog } = require('electron');
const { spawn } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

const HOST = '127.0.0.1';
const PORT = 8765;
const BASE_URL = `http://${HOST}:${PORT}`;
let backendProcess = null;
let backendLog = null;
let mainWindow = null;
let ownsBackend = false;

function resourcePath(...parts) {
  return app.isPackaged
    ? path.join(process.resourcesPath, ...parts)
    : path.join(__dirname, '..', ...parts);
}

function launchBackend() {
  const userData = app.getPath('userData');
  fs.mkdirSync(userData, { recursive: true });
  const env = {
    ...process.env,
    DATABASE_PATH: path.join(userData, 'learning.db'),
    UDAAN_FRONTEND_DIR: resourcePath('frontend', 'dist'),
    PYTHONUTF8: '1',
  };

  if (app.isPackaged) {
    const exe = resourcePath('backend', 'UdaanBackend.exe');
    if (!fs.existsSync(exe)) throw new Error(`Bundled backend was not found: ${exe}`);
    backendLog = fs.createWriteStream(path.join(userData, 'backend.log'), { flags: 'a' });
    backendProcess = spawn(exe, [], { cwd: path.dirname(exe), env, windowsHide: true, stdio: ['ignore', 'pipe', 'pipe'] });
  } else {
    const backendDir = path.join(__dirname, '..', 'backend');
    const python = process.env.PYTHON || 'python';
    env.UDAAN_FRONTEND_DIR = path.resolve(__dirname, '..', 'frontend', 'dist');
    backendLog = fs.createWriteStream(path.join(userData, 'backend.log'), { flags: 'a' });
    backendProcess = spawn(python, ['-m', 'uvicorn', 'app:app', '--host', HOST, '--port', String(PORT)], {
      cwd: backendDir,
      env,
      windowsHide: true,
      stdio: ['ignore', 'pipe', 'pipe'],
    });
  }

  ownsBackend = true;
  backendProcess.stdout?.on('data', (data) => backendLog?.write(data));
  backendProcess.stderr?.on('data', (data) => backendLog?.write(data));
  backendProcess.on('error', (err) => backendLog?.write(`\nBackend process error: ${err.stack || err}\n`));
  backendProcess.on('exit', (code, signal) => {
    backendLog?.write(`\nBackend exited: code=${code}, signal=${signal}\n`);
  });
}

async function waitForBackend(timeoutMs = 60000) {
  const start = Date.now();
  let lastError = 'not started';
  while (Date.now() - start < timeoutMs) {
    if (backendProcess && backendProcess.exitCode !== null) {
      throw new Error('The Udaan backend stopped during startup. Open the backend log for details.');
    }
    try {
      const response = await fetch(`${BASE_URL}/api/health`, { signal: AbortSignal.timeout(1800) });
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'ok') return;
      }
      lastError = `HTTP ${response.status}`;
    } catch (err) {
      lastError = err.message || String(err);
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  throw new Error(`Udaan backend did not become ready within ${timeoutMs / 1000}s. Last check: ${lastError}`);
}

async function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 940,
    minWidth: 1024,
    minHeight: 700,
    title: 'Udaan Learning',
    backgroundColor: '#10152d',
    autoHideMenuBar: true,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });
  await mainWindow.loadURL(BASE_URL);
  mainWindow.on('closed', () => { mainWindow = null; });
}

app.whenReady().then(async () => {
  try {
    // If a locally running Udaan backend is already available, reuse it in development.
    try {
      const r = await fetch(`${BASE_URL}/api/health`, { signal: AbortSignal.timeout(700) });
      if (!r.ok) launchBackend();
    } catch {
      launchBackend();
    }
    await waitForBackend();
    await createWindow();
  } catch (err) {
    const logPath = path.join(app.getPath('userData'), 'backend.log');
    dialog.showErrorBox('Udaan could not start', `${err.message}\n\nBackend log: ${logPath}\n\nCheck that the app files are complete and that port ${PORT} is available.`);
    app.quit();
  }
});

app.on('before-quit', () => {
  if (ownsBackend && backendProcess && backendProcess.exitCode === null) {
    try { backendProcess.kill(); } catch { /* app is already closing */ }
  }
  backendLog?.end();
});

app.on('window-all-closed', () => app.quit());
