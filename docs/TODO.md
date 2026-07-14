# ✅ TODO — Image Agent

> Danh sách việc cần làm, sắp xếp theo mức độ ưu tiên. Đánh dấu `[x]` khi hoàn thành, `[/]` khi đang làm.

---

## Phase Progress

> Use the checkboxes on each task and the legend below as the single source of truth. Do not add additional summary notes here.


## Legend

- `[ ]` — Chưa bắt đầu
- `[/]` — Đang tiến hành
- `[x]` — Hoàn thành
- 🔴 Critical — Không thể bỏ qua, phải hoàn thành trước khi tiếp tục
- 🟡 High — Quan trọng, nên hoàn thành sớm
- 🟢 Medium — Cần thiết nhưng không gấp
- 🔵 Low — Nice-to-have, làm khi có thời gian

---

## 📋 Phase 0: Documentation & Planning

### Documentation
- [x] 🔴 README.md — Giới thiệu dự án, roadmap, hướng dẫn
- [x] 🔴 PROJECT_SUMMARY.md — Tổng quan dự án chi tiết
- [x] 🔴 DEVELOPMENT_PLAN.md — Kế hoạch phát triển theo phase
- [x] 🔴 TECH_STACK.md — Phân tích công nghệ
- [x] 🔴 ARCHITECTURE.md — Thiết kế kiến trúc tổng thể
- [x] 🔴 CODING_STANDARD.md — Quy chuẩn viết code
- [x] 🔴 FUTURE_FEATURES.md — Tính năng tương lai
- [x] 🔴 TODO.md — Danh sách việc cần làm (file này)

---

## 📋 Phase 1: Foundation (v0.1.0)

### 1.1 Project Setup & Infrastructure

- [x] 🔴 Tạo cấu trúc thư mục monorepo (backend/, frontend/, shared/, docs/)
- [x] 🔴 Setup Python environment (venv, requirements.txt, pyproject.toml)
- [x] 🔴 Setup Ruff (linter + formatter) cho Python
- [x] 🔴 Setup Node.js environment (package.json, tsconfig.json)
- [x] 🔴 Setup ESLint + Prettier cho TypeScript
- [x] 🔴 Tạo .gitignore toàn diện
- [x] 🔴 Tạo .editorconfig
- [x] 🔴 Tạo .env.example
- [x] 🟡 Setup Git hooks (pre-commit: lint, format)

### 1.2 Backend Foundation

- [x] 🔴 FastAPI app factory (main.py)
- [x] 🔴 Pydantic settings (app config, GPU config, paths)
- [x] 🔴 Logging system (structured logging, file rotation)
- [x] 🔴 Dependency Injection container
- [x] 🔴 Custom exception hierarchy
- [x] 🔴 Global error handler middleware
- [x] 🔴 CORS middleware
- [x] 🟡 Request logging middleware

### 1.3 Database

- [x] 🔴 SQLAlchemy 2.x setup (async engine, session factory)
- [x] 🔴 Database models (generations, models, images, settings, queue_items)
- [x] 🔴 Alembic setup + initial migration
- [x] 🔴 Base repository class
- [x] 🔴 Generation repository
- [x] 🔴 Model repository
- [x] 🔴 Image repository
- [x] 🔴 Settings repository
- [x] 🟡 Auto-migration on startup

### 1.4 Core Layer

- [x] 🔴 Domain entities (GenerationEntity, ModelEntity, ImageEntity, etc.)
- [x] 🔴 Interfaces (IAIEngine, IModelLoader, IQueueManager, IStorage, IEventBus)
- [x] 🔴 Enums (GenerationType, ModelType, GenerationStatus, SchedulerType)
- [x] 🔴 Constants (default values, limits, paths)
- [x] 🔴 Custom exceptions (EngineError, ValidationError, etc.)

### 1.5 Event System

- [x] 🟡 Event Bus implementation (in-memory, async)
- [x] 🟡 Event type definitions
- [x] 🟡 Event handler registration
- [x] 🟡 Error isolation (handler failure doesn't affect others)
- [x] 🟢 Event logging middleware

### 1.6 AI Engine Core

- [x] 🔴 Engine manager (pipeline registry, lifecycle)
- [x] 🔴 Base pipeline abstract class
- [x] 🔴 Model loader (safetensors, ckpt support)
- [x] 🔴 Model info extraction (name, type, architecture, size)
- [x] 🔴 Text-to-Image pipeline (SD 1.5 via Diffusers)
- [x] 🔴 Image-to-Image pipeline (SD 1.5 via Diffusers)
- [x] 🟡 Scheduler factory (Euler, Euler_A, DPM++, DDIM)
- [x] 🔴 VRAM Manager (monitoring, basic strategy)
- [x] 🟡 xformers / SDP attention optimization
- [x] 🟡 VAE slicing for large images
- [x] 🟡 Seed management (random, reproducible)
- [x] 🟢 Generation step callback (for progress reporting)

### 1.7 Backend API (REST)

- [x] 🔴 API router setup (v1 prefix, tags)
- [x] 🔴 DTO schemas (request/response Pydantic models)
- [x] 🔴 POST /api/v1/generate — Create generation
- [x] 🔴 GET /api/v1/generate/{id} — Get generation status
- [x] 🔴 DELETE /api/v1/generate/{id} — Cancel generation
- [x] 🔴 GET /api/v1/models — List available models
- [x] 🔴 POST /api/v1/models/load — Load model into GPU
- [x] 🔴 POST /api/v1/models/unload — Unload current model
- [x] 🔴 GET /api/v1/models/loaded — Get loaded model info
- [x] 🟡 GET /api/v1/queue — Get queue status
- [x] 🟡 POST /api/v1/queue/{id}/cancel — Cancel queue item
- [x] 🟡 DELETE /api/v1/queue — Clear queue
- [x] 🟢 GET /api/v1/settings — Get settings
- [x] 🟢 PUT /api/v1/settings — Update settings
- [x] 🟡 GET /api/v1/system/info — System info
- [x] 🟡 GET /api/v1/system/gpu — GPU info

### 1.8 Backend API (WebSocket)

- [x] 🔴 WebSocket connection manager
- [x] 🔴 /ws/progress — Generation progress (step, preview)
- [x] 🟡 /ws/monitor — System monitoring (VRAM, GPU temp, 3s interval)
- [x] 🟡 /ws/events — General event stream

### 1.9 Service Layer

- [x] 🔴 GenerationService (create, execute, cancel)
- [x] 🔴 ModelService (load, unload, list, scan)
- [x] 🟡 QueueService (add, cancel, clear, get status)
- [x] 🟡 HistoryService (log generation, query history)
- [x] 🟢 SettingsService (get, set, defaults)
- [x] 🟡 SystemService (GPU info, VRAM, health check)

### 1.10 Queue System

- [x] 🟡 In-memory queue with priority
- [x] 🟡 Queue worker (async processing)
- [x] 🟡 Queue item status tracking
- [x] 🟢 Queue persistence (save to DB)

### 1.11 File Storage

- [x] 🔴 Local file storage implementation
- [x] 🔴 Image saving (PNG, JPEG, WebP)
- [x] 🟡 Thumbnail generation
- [x] 🟡 Directory management (outputs/, thumbnails/)

### 1.12 Frontend — Electron Setup

- [x] 🔴 Electron main process setup
- [x] 🔴 Window management (create, resize, min/max)
- [x] 🔴 IPC bridge (main ↔ renderer)
- [x] 🔴 Backend process manager (start/stop Python)
- [x] 🟡 System tray icon (reserved)
- [x] 🟢 Auto-hide menu bar

### 1.13 Frontend — React Setup

- [x] 🔴 Vite + React + TypeScript setup (via electron-vite)
- [x] 🔴 TailwindCSS setup
- [x] 🔴 shadcn/ui setup (button, input, slider, select, dialog, toast, etc.)
- [x] 🔴 React Router setup
- [x] 🔴 Zustand stores (generation, model, queue, ui, system)
- [x] 🔴 TanStack Query setup (provider, default config)
- [x] 🔴 Framer Motion setup
- [x] 🔴 API service layer (fetch wrapper, error handling)
- [x] 🟡 WebSocket hooks (useWebSocket, auto-reconnect)

### 1.14 Frontend — Design System

- [x] 🔴 Dark theme as default
- [x] 🔴 Color palette (primary, secondary, accent, semantic colors)
- [x] 🔴 Typography (font family, sizes, weights)
- [x] 🔴 Spacing scale (consistent padding/margin)
- [x] 🟡 Icon set (Lucide)
- [x] 🟡 Animation tokens (duration, easing)

### 1.15 Frontend — Layout & Navigation

- [x] 🔴 MainLayout component (sidebar + header + content + statusbar)
- [x] 🔴 Sidebar navigation
- [x] 🔴 Header with breadcrumb
- [x] 🔴 Status bar (VRAM, connection, queue count)
- [x] 🟡 Resizable panels
- [x] 🟡 Responsive layout

### 1.16 Frontend — Generate Page

- [x] 🔴 Prompt input (positive prompt, textarea)
- [x] 🔴 Negative prompt input
- [x] 🔴 Generate button (with loading state)
- [x] 🔴 Image preview area (show generated image)
- [x] 🔴 Progress bar (step progress, percentage)
- [x] 🟡 Parameter panel:
  - [x] 🟡 Sampler/Scheduler select
  - [x] 🟡 Steps slider (1-150)
  - [x] 🟡 CFG scale slider (1-30)
  - [x] 🟡 Width/Height inputs
  - [x] 🟡 Seed input (with random button)
  - [x] 🟡 Batch count input (reserved)
- [x] 🟡 Model selector dropdown
- [x] 🟢 Size presets (512x512, 768x768, 1024x1024)
- [x] 🟢 Advanced options toggle

### 1.17 Frontend — Models Page

- [x] 🟡 Model list (grid/list view)
- [x] 🟡 Model card (name, type, size, thumbnail)
- [x] 🟡 Load/Unload model button
- [x] 🟡 Currently loaded model indicator
- [x] 🟢 Model details panel

### 1.18 Frontend — Queue & History

- [x] 🟡 Queue list (items, status, position)
- [x] 🟡 Cancel queue item button
- [x] 🟡 Clear queue button
- [x] 🟢 History list (generated images with metadata)
- [x] 🟢 History detail view (all parameters)

### 1.19 Frontend — Settings Page

- [x] 🟢 Output directory setting
- [x] 🟢 Model directory setting
- [x] 🟢 Default generation parameters
- [x] 🟢 Theme toggle
- [x] 🟢 Save settings button

### 1.20 Frontend — System Monitor

- [x] 🟡 VRAM usage bar (real-time)
- [x] 🟡 GPU temperature (reserved)
- [x] 🟡 GPU utilization percentage (reserved)
- [x] 🟢 CPU/RAM usage
- [x] 🟢 Disk space

### 1.21 Integration

- [x] 🔴 Electron starts Python backend automatically
- [x] 🔴 Frontend connects to backend API
- [x] 🔴 End-to-end: Type prompt → Generate → Show image
- [x] 🔴 WebSocket progress during generation
- [x] 🟡 Error handling across stack (backend error → frontend toast)
- [x] 🟡 Graceful shutdown (stop backend when closing app)

### 1.22 Testing

- [x] 🟡 Backend unit tests (services, engine logic)
- [x] 🟡 Backend integration tests (API endpoints)
- [x] 🟢 Frontend unit tests (stores, hooks)
- [x] 🟢 Frontend component tests
- [x] 🟡 VRAM stress test (50+ sequential generations)
- [x] 🟢 Performance benchmark (generation time)
- [x] 🟡 pytest.ini configuration
- [x] 🟢 vitest configuration

### 1.23 Documentation

- [ ] 🟡 API documentation (OpenAPI/Swagger)
- [ ] 🟡 Setup guide (step-by-step)
- [ ] 🟢 Architecture decision records
- [ ] 🟢 Development troubleshooting guide

---

## 📋 Phase 2: Core Features (v0.2.0)

### 2.1 Advanced Generation

- [ ] 🔴 Inpainting pipeline
- [ ] 🔴 Canvas/mask editor (brush, eraser, clear)
- [ ] 🟡 Outpainting pipeline
- [ ] 🔴 ControlNet integration (Canny, Depth, OpenPose)
- [ ] 🟡 ControlNet preprocessors UI
- [ ] 🔴 LoRA support (load, merge, multi-LoRA)
- [ ] 🟡 LoRA weight sliders
- [ ] 🟡 Batch generation (multiple images)
- [ ] 🟢 Batch parameter sweep

### 2.2 Gallery & Media

- [ ] 🟡 Gallery page (grid view, infinite scroll)
- [ ] 🟡 Image detail view (full-size + metadata)
- [ ] 🟡 Search & filter (by prompt, model, date)
- [ ] 🟢 Favorite images
- [ ] 🟢 Image tags
- [ ] 🟢 Export (with/without metadata)

### 2.3 Download Manager

- [ ] 🟡 Download engine (multi-thread, resume)
- [ ] 🟡 HuggingFace integration
- [ ] 🟡 CivitAI integration
- [ ] 🟡 Download progress UI
- [ ] 🟢 Model auto-detection after download

### 2.4 Queue Improvements

- [ ] 🟡 Priority queue
- [ ] 🟡 Pause/resume generation
- [ ] 🟡 Queue persistence (survive restart)
- [ ] 🟡 Queue reordering

### 2.5 UX Improvements

- [ ] 🟡 Keyboard shortcuts (generate, cancel, navigate)
- [ ] 🟢 Drag & drop image for img2img/inpaint
- [ ] 🟢 Context menus
- [ ] 🟢 Toast notifications

---

## 📋 Phase 3: Advanced (v0.3.0)

### 3.1 Post-Processing

- [ ] 🟡 Upscale (ESRGAN, RealESRGAN)
- [ ] 🟡 Face Restore (GFPGAN, CodeFormer)
- [ ] 🟢 Chained processing (generate → face restore → upscale)
- [ ] 🟢 Auto post-process option

### 3.2 Prompt System

- [ ] 🟡 Prompt templates
- [ ] 🟡 Style presets
- [ ] 🟢 Prompt history & autocomplete
- [ ] 🟢 Token counter
- [ ] 🟡 Local LLM prompt enhancement

### 3.3 SDXL

- [ ] 🔴 SDXL pipeline (txt2img, img2img)
- [ ] 🔴 SDXL VRAM optimization for 8GB
- [ ] 🟡 SDXL LoRA support
- [ ] 🟡 SDXL ControlNet support
- [ ] 🟢 SDXL resolution presets

### 3.4 Plugin System

- [ ] 🔴 Plugin architecture (API, lifecycle, permissions)
- [ ] 🔴 Plugin loader & discovery
- [ ] 🔴 Plugin API (backend hooks, service access)
- [ ] 🟡 Plugin API (frontend UI extension)
- [ ] 🟡 Plugin sandbox (isolation)
- [ ] 🟡 Plugin manager UI
- [ ] 🟡 Plugin SDK & documentation
- [ ] 🟢 2-3 sample plugins

### 3.5 Workflow Builder

- [ ] 🟡 Workflow data model (nodes, connections)
- [ ] 🟡 Visual workflow editor
- [ ] 🟡 Built-in nodes (generate, upscale, save)
- [ ] 🟡 Workflow execution engine
- [ ] 🟢 Workflow save/load

### 3.6 Performance

- [ ] 🔴 Advanced VRAM management
- [ ] 🟡 Performance profiler
- [ ] 🟡 Memory leak detection

---

## 📋 Phase 4: Platform (v0.5.0)

- [ ] 🟡 Plugin Marketplace UI
- [ ] 🔴 Flux model support
- [ ] 🟡 SD3 model support
- [ ] 🔴 Model architecture abstraction (unified interface)
- [ ] 🟡 ONNX Runtime support
- [ ] 🟢 Multi-language UI (EN, VI)
- [ ] 🟡 Windows installer/packager
- [ ] 🟢 App auto-updater

---

## 📋 Phase 5: Next Generation (v1.0.0)

- [ ] 🟡 Video generation (AnimateDiff, SVD)
- [ ] 🟡 3D generation (image-to-3D)
- [ ] 🟡 Local LLM integration
- [ ] 🟢 Pony Diffusion support
- [ ] 🟢 Illustrious support
- [ ] 🟢 TensorRT optimization
- [ ] 🟢 Multi-GPU support

---

## 📋 Ongoing / Cross-Phase

### Code Quality

- [ ] 🟡 Maintain test coverage >= 70% (Phase 1), >= 80% (Phase 3+)
- [ ] 🟡 Regular dependency updates
- [ ] 🟡 Performance benchmarks after each phase
- [ ] 🟢 Code complexity monitoring
- [ ] 🟢 Security audit per phase

### Documentation

- [ ] 🟡 Keep API docs up-to-date
- [ ] 🟡 Update architecture docs after major changes
- [ ] 🟢 User guide (for end users)
- [ ] 🟢 Plugin developer guide
- [ ] 🟢 FAQ / Troubleshooting guide

### DevOps

- [ ] 🟢 CI pipeline (lint, test, build)
- [ ] 🟢 Automated test runs on PR
- [ ] 🟢 Release process documentation
- [ ] 🔵 Automated performance regression tests
- [ ] 🔵 Crash analytics

---

## 📊 Progress Summary

| Phase | Total Tasks | Completed | In Progress | Remaining |
|---|---|---|---|---|
| Phase 0 | 8 | 8 | 0 | 0 |
| Phase 1 | ~95 | 4 | 3 | ~88 |
| Phase 2 | ~28 | 0 | 0 | ~28 |
| Phase 3 | ~25 | 0 | 0 | ~25 |
| Phase 4 | ~8 | 0 | 0 | ~8 |
| Phase 5 | ~7 | 0 | 0 | ~7 |
| Ongoing | ~12 | 0 | 0 | ~12 |
| **Total** | **~183** | **8** | **0** | **~175** |

---

> 📝 **Cập nhật lần cuối**: Sau khi hoàn thành Phase 0 (Documentation)
>
> 📌 **Bước tiếp theo**: Bắt đầu Phase 1 — Project Setup & Infrastructure

## Developer Conventions

- **Git commit message format**: Use conventional short messages describing the changed feature or bugfix.
  - Format: `<type>(<scope>): short description`
  - Types: `feat` (new feature), `fix` (bug fix), `chore` (maintenance), `docs` (documentation), `test` (tests), `refactor`.
  - Examples:
    - `fix(engine): guard float16 usage on CPU in txt2img/img2img`
    - `feat(frontend): map sampler labels to scheduler keys`
    - `chore(repo): add get_by_path to model repository`

- **Commit message body** (optional): one-line explanation of why the change was made and any follow-up tasks.

Follow this format when committing and pushing so `TODO.md` progress and commit history remain easy to audit.
