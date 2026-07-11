import { app, shell, BrowserWindow, ipcMain, dialog } from 'electron'
import { join, dirname } from 'path'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import icon from '../../resources/icon.png?asset'
import { spawn, ChildProcess } from 'child_process'
import * as fs from 'fs'

let pythonProcess: ChildProcess | null = null

function startPythonBackend(): void {
  // Locate paths relative to dev environment or package directory
  const possiblePaths = [
    join(app.getAppPath(), '..', 'backend', 'venv', 'Scripts', 'python.exe'),
    join(process.cwd(), 'backend', 'venv', 'Scripts', 'python.exe'),
    join(app.getAppPath(), 'backend', 'venv', 'Scripts', 'python.exe'),
    'python'
  ]

  let pythonExe = 'python'
  for (const p of possiblePaths) {
    if (fs.existsSync(p)) {
      pythonExe = p
      break
    }
  }

  const possibleScripts = [
    join(app.getAppPath(), '..', 'backend', 'app', 'main.py'),
    join(process.cwd(), 'backend', 'app', 'main.py'),
    join(app.getAppPath(), 'backend', 'app', 'main.py')
  ]

  let scriptPath = ''
  for (const s of possibleScripts) {
    if (fs.existsSync(s)) {
      scriptPath = s
      break
    }
  }

  if (!scriptPath) {
    console.error('Python backend main.py script not found!')
    return
  }

  const backendDir = dirname(dirname(scriptPath))
  console.log(`Launching Python Backend from folder: ${backendDir} using: ${pythonExe}`)

  pythonProcess = spawn(pythonExe, ['app/main.py'], {
    cwd: backendDir,
    env: { ...process.env, PYTHONPATH: backendDir }
  })

  pythonProcess.stdout?.on('data', (data) => {
    console.log(`[Python Backend]: ${data}`)
  })

  pythonProcess.stderr?.on('data', (data) => {
    console.error(`[Python Backend Error]: ${data}`)
  })

  pythonProcess.on('close', (code) => {
    console.log(`Python Backend exited with code ${code}`)
    pythonProcess = null
  })
}

function killPythonBackend(): void {
  if (pythonProcess) {
    console.log('Terminating Python backend process...')
    pythonProcess.kill('SIGINT')
    pythonProcess = null
  }
}

function createWindow(): void {
  // Create the browser window with rich premium sizing
  const mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 1024,
    minHeight: 768,
    show: false,
    autoHideMenuBar: true,
    ...(process.platform === 'linux' ? { icon } : {}),
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false
    }
  })

  mainWindow.on('ready-to-show', () => {
    mainWindow.show()
  })

  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url)
    return { action: 'deny' }
  })

  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

app.whenReady().then(() => {
  electronApp.setAppUserModelId('com.electron')

  app.on('browser-window-created', (_, window) => {
    optimizer.watchWindowShortcuts(window)
  })

  // Register IPC Handlers
  ipcMain.handle('select-directory', async () => {
    const result = await dialog.showOpenDialog({
      properties: ['openDirectory']
    })
    if (result.canceled || result.filePaths.length === 0) {
      return null
    }
    return result.filePaths[0]
  })

  ipcMain.handle('get-backend-status', async () => {
    return {
      running: pythonProcess !== null,
      pid: pythonProcess?.pid
    }
  })

  // Start Python Process
  startPythonBackend()

  createWindow()

  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  killPythonBackend()
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('quit', () => {
  killPythonBackend()
})
