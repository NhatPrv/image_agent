import { app, shell, BrowserWindow, ipcMain, dialog } from 'electron'
import { join, dirname } from 'path'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import icon from '../../resources/icon.png?asset'
import { spawn, ChildProcess } from 'child_process'
import * as fs from 'fs'

let pythonProcess: ChildProcess | null = null
let mainWindowRef: BrowserWindow | null = null

function startPythonBackend(): void {
  // Locate paths relative to dev environment or package directory.
  // During `npm run dev`, app.getAppPath() is typically `frontend/` and
  // process.cwd() is also `frontend/` (or wherever electron-vite launches from).
  const possiblePyPaths = [
    // Dev: frontend/../backend/venv (project root level)
    join(app.getAppPath(), '..', 'backend', 'venv', 'Scripts', 'python.exe'),
    // Dev: cwd()/../backend/venv (when cwd is frontend/)
    join(process.cwd(), '..', 'backend', 'venv', 'Scripts', 'python.exe'),
    // Packaged: resources/backend/venv
    join(app.getAppPath(), '..', '..', 'backend', 'venv', 'Scripts', 'python.exe'),
    join(process.cwd(), 'backend', 'venv', 'Scripts', 'python.exe'),
    join(app.getAppPath(), 'backend', 'venv', 'Scripts', 'python.exe'),
    'python'
  ]

  let pythonExe = 'python'
  for (const p of possiblePyPaths) {
    if (p !== 'python' && fs.existsSync(p)) {
      pythonExe = p
      break
    }
  }

  const possibleScripts = [
    // Dev: frontend/../backend/app/main.py
    join(app.getAppPath(), '..', 'backend', 'app', 'main.py'),
    // Dev: cwd()/../backend/app/main.py
    join(process.cwd(), '..', 'backend', 'app', 'main.py'),
    join(app.getAppPath(), '..', '..', 'backend', 'app', 'main.py'),
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

  // scriptPath = .../backend/app/main.py → backendDir = .../backend/
  const backendDir = dirname(dirname(scriptPath))
  console.log(`Launching Python Backend: cwd=${backendDir} python=${pythonExe}`)

  // Use -m flag so Python includes backendDir in sys.path, allowing
  // 'from app.xyz import ...' to resolve correctly
  pythonProcess = spawn(pythonExe, ['-m', 'app.main'], {
    cwd: backendDir,
    env: { ...process.env, PYTHONPATH: backendDir },
    windowsHide: true
  })

  pythonProcess.stdout?.on('data', (data) => {
    const text = data.toString()
    console.log(`[Python Backend]: ${text}`)
    if (mainWindowRef) {
      mainWindowRef.webContents.send('backend-log', { type: 'stdout', text })
    }
  })

  pythonProcess.stderr?.on('data', (data) => {
    const text = data.toString()
    console.error(`[Python Backend Error]: ${text}`)
    if (mainWindowRef) {
      mainWindowRef.webContents.send('backend-log', { type: 'stderr', text })
    }
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

  mainWindowRef = mainWindow

  mainWindow.on('ready-to-show', () => {
    mainWindow.show()
  })

  mainWindow.on('closed', () => {
    mainWindowRef = null
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

  ipcMain.handle('select-image', async () => {
    const result = await dialog.showOpenDialog({
      properties: ['openFile'],
      filters: [{ name: 'Images', extensions: ['png', 'jpg', 'jpeg', 'webp'] }]
    })
    if (result.canceled || result.filePaths.length === 0) {
      return null
    }
    return result.filePaths[0]
  })

  ipcMain.handle('read-image-base64', async (_event, filePath: string) => {
    try {
      const data = await fs.promises.readFile(filePath)
      const ext = filePath.split('.').pop() || 'png'
      return `data:image/${ext};base64,${data.toString('base64')}`
    } catch (err) {
      console.error('Failed to read image as base64:', err)
      return null
    }
  })

  ipcMain.handle('save-temp-image', async (_event, base64Data: string, filename: string) => {
    try {
      const base64Clean = base64Data.replace(/^data:image\/\w+;base64,/, '')
      const buffer = Buffer.from(base64Clean, 'base64')
      const tempDir = app.getPath('temp')
      const filePath = join(tempDir, filename)
      await fs.promises.writeFile(filePath, buffer)
      return filePath
    } catch (err) {
      console.error('Failed to save temporary image:', err)
      throw err
    }
  })

  ipcMain.handle('save-image-as', async (_event, sourcePath: string) => {
    try {
      const originalName = sourcePath.split(/[\\/]/).pop() || 'generated_image.png'
      const result = await dialog.showSaveDialog({
        defaultPath: originalName,
        filters: [{ name: 'Images', extensions: ['png', 'jpg', 'jpeg', 'webp'] }]
      })

      if (result.canceled || !result.filePath) {
        return null
      }

      let absoluteSource = sourcePath
      if (!fs.existsSync(absoluteSource)) {
        // Resolve under outputs folder: process.cwd() / '..' / 'outputs'
        absoluteSource = join(process.cwd(), '..', 'outputs', sourcePath)
        if (!fs.existsSync(absoluteSource)) {
          // Fallback: try relative to appGetAppPath / .. / outputs
          absoluteSource = join(app.getAppPath(), '..', 'outputs', sourcePath)
        }
      }

      if (fs.existsSync(absoluteSource)) {
        fs.copyFileSync(absoluteSource, result.filePath)
        return result.filePath
      } else {
        throw new Error(`Source image file not found: ${absoluteSource}`)
      }
    } catch (err) {
      console.error('Failed to export image:', err)
      throw err
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
