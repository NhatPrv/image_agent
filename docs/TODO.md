# ✅ TODO — Image Agent

> Danh sách việc cần làm, sắp xếp theo mức độ ưu tiên. Đánh dấu `[x]` khi hoàn thành, `[/]` khi đang làm.

---

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

- [ ] 🔴 Tạo cấu trúc thư mục monorepo (backend/, frontend/, shared/, docs/)
- [ ] 🔴 Setup Python environment (venv, requirements.txt, pyproject.toml)
- [ ] 🔴 Setup Ruff (linter + formatter) cho Python
- [ ] 🔴 Setup Node.js environment (package.json, tsconfig.json)
- [ ] 🔴 Setup ESLint + Prettier cho TypeScript
- [ ] 🔴 Tạo .gitignore toàn diện
- [ ] 🔴 Tạo .editorconfig
- [ ] 🔴 Tạo .env.example
- [ ] 🟡 Setup Git hooks (pre-commit: lint, format)

### 1.2 Backend Foundation

- [ ] 🔴 FastAPI app factory (main.py)
- [ ] 🔴 Pydantic settings (app config, GPU config, paths)
- [ ] 🔴 Logging system (structured logging, file rotation)
- [ ] 🔴 Dependency Injection container
- [ ] 🔴 Custom exception hierarchy
- [ ] 🔴 Global error handler middleware
- [ ] 🔴 CORS middleware
- [ ] 🟡 Request logging middleware

### 1.3 Database

- [ ] 🔴 SQLAlchemy 2.x setup (async engine, session factory)
- [ ] 🔴 Database models (generations, models, images, settings, queue_items)
- [ ] 🔴 Alembic setup + initial migration
- [ ] 🔴 Base repository class
- [ ] 🔴 Generation repository
- [ ] 🔴 Model repository
- [ ] 🔴 Image repository
- [ ] 🔴 Settings repository
- [ ] 🟡 Auto-migration on startup

### 1.4 Core Layer

- [ ] 🔴 Domain entities (GenerationEntity, ModelEntity, ImageEntity, etc.)
- [ ] 🔴 Interfaces (IAIEngine, IModelLoader, IQueueManager, IStorage, IEventBus)
- [ ] 🔴 Enums (GenerationType, ModelType, GenerationStatus, SchedulerType)
- [ ] 🔴 Constants (default values, limits, paths)
- [ ] 🔴 Custom exceptions (EngineError, ValidationError, etc.)

### 1.5 Event System

- [ ] 🟡 Event Bus implementation (in-memory, async)
- [ ] 🟡 Event type definitions
- [ ] 🟡 Event handler registration
- [ ] 🟡 Error isolation (handler failure doesn't affect others)
- [ ] 🟢 Event logging middleware

### 1.6 AI Engine Core

- [ ] 🔴 Engine manager (pipeline registry, lifecycle)
- [ ] 🔴 Base pipeline abstract class
- [ ] 🔴 Model loader (safetensors, ckpt support)
- [ ] 🔴 Model info extraction (name, type, architecture, size)
- [ ] 🔴 Text-to-Image pipeline (SD 1.5 via Diffusers)
- [ ] 🔴 Image-to-Image pipeline (SD 1.5 via Diffusers)
- [ ] 🟡 Scheduler factory (Euler, Euler_A, DPM++, DDIM)
- [ ] 🔴 VRAM Manager (monitoring, basic strategy)
- [ ] 🟡 xformers / SDP attention optimization
- [ ] 🟡 VAE slicing for large images
- [ ] 🟡 Seed management (random, reproducible)
- [ ] 🟢 Generation step callback (for progress reporting)

### 1.7 Backend API (REST)

- [ ] 🔴 API router setup (v1 prefix, tags)
- [ ] 🔴 DTO schemas (request/response Pydantic models)
- [ ] 🔴 POST /api/v1/generate — Create generation
- [ ] 🔴 GET /api/v1/generate/{id} — Get generation status
- [ ] 🔴 DELETE /api/v1/generate/{id} — Cancel generation
- [ ] 🔴 GET /api/v1/models — List available models
- [ ] 🔴 POST /api/v1/models/load — Load model into GPU
- [ ] 🔴 POST /api/v1/models/unload — Unload current model
- [ ] 🔴 GET /api/v1/models/loaded — Get loaded model info
- [ ] 🟡 GET /api/v1/queue — Get queue status
- [ ] 🟡 POST /api/v1/queue/{id}/cancel — Cancel queue item
- [ ] 🟡 DELETE /api/v1/queue — Clear queue
- [ ] 🟢 GET /api/v1/settings — Get settings
- [ ] 🟢 PUT /api/v1/settings — Update settings
- [ ] 🟡 GET /api/v1/system/info — System info
- [ ] 🟡 GET /api/v1/system/gpu — GPU info

### 1.8 Backend API (WebSocket)

- [ ] 🔴 WebSocket connection manager
- [ ] 🔴 /ws/progress — Generation progress (step, preview)
- [ ] 🟡 /ws/monitor — System monitoring (VRAM, GPU temp, 1s interval)
- [ ] 🟡 /ws/events — General event stream

### 1.9 Service Layer

- [ ] 🔴 GenerationService (create, execute, cancel)
- [ ] 🔴 ModelService (load, unload, list, scan)
- [ ] 🟡 QueueService (add, cancel, clear, get status)
- [ ] 🟡 HistoryService (log generation, query history)
- [ ] 🟢 SettingsService (get, set, defaults)
- [ ] 🟡 SystemService (GPU info, VRAM, health check)

### 1.10 Queue System

- [ ] 🟡 In-memory queue with priority
- [ ] 🟡 Queue worker (async processing)
- [ ] 🟡 Queue item status tracking
- [ ] 🟢 Queue persistence (save to DB)

### 1.11 File Storage

- [ ] 🔴 Local file storage implementation
- [ ] 🔴 Image saving (PNG, JPEG, WebP)
- [ ] 🟡 Thumbnail generation
- [ ] 🟡 Directory management (outputs/, thumbnails/)

### 1.12 Frontend — Electron Setup

- [ ] 🔴 Electron main process setup
- [ ] 🔴 Window management (create, resize, min/max)
- [ ] 🔴 IPC bridge (main ↔ renderer)
- [ ] 🔴 Backend process manager (start/stop Python)
- [ ] 🟡 System tray icon
- [ ] 🟢 Auto-hide menu bar

### 1.13 Frontend — React Setup

- [ ] 🔴 Vite + React + TypeScript setup (via electron-vite)
- [ ] 🔴 TailwindCSS setup
- [ ] 🔴 shadcn/ui setup (button, input, slider, select, dialog, toast, etc.)
- [ ] 🔴 React Router setup
- [ ] 🔴 Zustand stores (generation, model, queue, ui, system)
- [ ] 🔴 TanStack Query setup (provider, default config)
- [ ] 🔴 Framer Motion setup
- [ ] 🔴 API service layer (fetch wrapper, error handling)
- [ ] 🟡 WebSocket hooks (useWebSocket, auto-reconnect)

### 1.14 Frontend — Design System

- [ ] 🔴 Dark theme as default
- [ ] 🔴 Color palette (primary, secondary, accent, semantic colors)
- [ ] 🔴 Typography (font family, sizes, weights)
- [ ] 🔴 Spacing scale (consistent padding/margin)
- [ ] 🟡 Icon set (Lucide)
- [ ] 🟡 Animation tokens (duration, easing)

### 1.15 Frontend — Layout & Navigation

- [ ] 🔴 MainLayout component (sidebar + header + content + statusbar)
- [ ] 🔴 Sidebar navigation
- [ ] 🔴 Header with breadcrumb
- [ ] 🔴 Status bar (VRAM, connection, queue count)
- [ ] 🟡 Resizable panels
- [ ] 🟡 Responsive layout

### 1.16 Frontend — Generate Page

- [ ] 🔴 Prompt input (positive prompt, textarea)
- [ ] 🔴 Negative prompt input
- [ ] 🔴 Generate button (with loading state)
- [ ] 🔴 Image preview area (show generated image)
- [ ] 🔴 Progress bar (step progress, percentage)
- [ ] 🟡 Parameter panel:
  - [ ] 🟡 Sampler/Scheduler select
  - [ ] 🟡 Steps slider (1-150)
  - [ ] 🟡 CFG scale slider (1-30)
  - [ ] 🟡 Width/Height inputs
  - [ ] 🟡 Seed input (with random button)
  - [ ] 🟡 Batch count input
- [ ] 🟡 Model selector dropdown
- [ ] 🟢 Size presets (512x512, 768x768, 1024x1024)
- [ ] 🟢 Advanced options toggle

### 1.17 Frontend — Models Page

- [ ] 🟡 Model list (grid/list view)
- [ ] 🟡 Model card (name, type, size, thumbnail)
- [ ] 🟡 Load/Unload model button
- [ ] 🟡 Currently loaded model indicator
- [ ] 🟢 Model details panel

### 1.18 Frontend — Queue & History

- [ ] 🟡 Queue list (items, status, position)
- [ ] 🟡 Cancel queue item button
- [ ] 🟡 Clear queue button
- [ ] 🟢 History list (generated images with metadata)
- [ ] 🟢 History detail view (all parameters)

### 1.19 Frontend — Settings Page

- [ ] 🟢 Output directory setting
- [ ] 🟢 Model directory setting
- [ ] 🟢 Default generation parameters
- [ ] 🟢 Theme toggle
- [ ] 🟢 Save settings button

### 1.20 Frontend — System Monitor

- [ ] 🟡 VRAM usage bar (real-time)
- [ ] 🟡 GPU temperature
- [ ] 🟡 GPU utilization percentage
- [ ] 🟢 CPU/RAM usage
- [ ] 🟢 Disk space

### 1.21 Integration

- [ ] 🔴 Electron starts Python backend automatically
- [ ] 🔴 Frontend connects to backend API
- [ ] 🔴 End-to-end: Type prompt → Generate → Show image
- [ ] 🔴 WebSocket progress during generation
- [ ] 🟡 Error handling across stack (backend error → frontend toast)
- [ ] 🟡 Graceful shutdown (stop backend when closing app)

### 1.22 Testing

- [ ] 🟡 Backend unit tests (services, engine logic)
- [ ] 🟡 Backend integration tests (API endpoints)
- [ ] 🟢 Frontend unit tests (stores, hooks)
- [ ] 🟢 Frontend component tests
- [ ] 🟡 VRAM stress test (50+ sequential generations)
- [ ] 🟢 Performance benchmark (generation time)
- [ ] 🟡 pytest.ini configuration
- [ ] 🟢 vitest configuration

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
| Phase 1 | ~95 | 0 | 0 | ~95 |
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
