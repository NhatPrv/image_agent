# 🎨 Image Agent

> **Nền tảng AI Image Generation chạy hoàn toàn LOCAL trên Windows**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)]()
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)]()
[![Node](https://img.shields.io/badge/node-20+-green.svg)]()
[![Platform](https://img.shields.io/badge/platform-Windows%2011-blue.svg)]()
[![GPU](https://img.shields.io/badge/GPU-NVIDIA%20RTX-green.svg)]()

---

## 📋 Mục Lục

- [Giới Thiệu](#-giới-thiệu)
- [Tại Sao Image Agent?](#-tại-sao-image-agent)
- [Mục Tiêu](#-mục-tiêu)
- [Tính Năng](#-tính-năng)
- [Kiến Trúc](#-kiến-trúc)
- [Yêu Cầu Hệ Thống](#-yêu-cầu-hệ-thống)
- [Cài Đặt](#-cài-đặt)
- [Hướng Dẫn Phát Triển](#-hướng-dẫn-phát-triển)
- [Cấu Trúc Thư Mục](#-cấu-trúc-thư-mục)
- [Roadmap](#-roadmap)
- [Quy Tắc Đóng Góp](#-quy-tắc-đóng-góp)
- [Tài Liệu Liên Quan](#-tài-liệu-liên-quan)

---

## 🌟 Giới Thiệu

**Image Agent** là một ứng dụng desktop AI Image Generation chạy hoàn toàn offline trên Windows. Được thiết kế với kiến trúc hiện đại, modular và plugin-based, Image Agent hướng tới việc trở thành nền tảng toàn diện cho việc tạo ảnh AI — không chỉ đơn thuần là giao diện cho Stable Diffusion.

Image Agent được xây dựng từ đầu với triết lý:

- **Local-first**: Mọi thứ chạy trên máy tính của bạn, không phụ thuộc cloud
- **Privacy-first**: Dữ liệu của bạn không bao giờ rời khỏi máy tính
- **Quality-first**: Không viết code tạm bợ, mọi thiết kế hướng tới dài hạn
- **User-first**: Giao diện đẹp, trực quan, dễ sử dụng cho cả người mới

### So Sánh Với Các Giải Pháp Hiện Tại

| Tính năng | Image Agent | ComfyUI | Fooocus | InvokeAI | SD WebUI |
|---|---|---|---|---|---|
| Giao diện hiện đại | ✅ Native Desktop | ❌ Web Node-based | ✅ Web đơn giản | ⚠️ Web cơ bản | ⚠️ Gradio |
| Plugin System | ✅ Full marketplace | ❌ Custom nodes | ❌ Không | ⚠️ Hạn chế | ⚠️ Extensions |
| VRAM Management | ✅ Smart monitoring | ⚠️ Manual | ✅ Auto | ⚠️ Cơ bản | ⚠️ Cơ bản |
| Workflow System | ✅ Visual + Code | ✅ Node-based | ❌ Không | ⚠️ Hạn chế | ❌ Không |
| Model Manager | ✅ Built-in + Download | ❌ Manual | ⚠️ Cơ bản | ✅ Có | ⚠️ Cơ bản |
| Queue System | ✅ Priority queue | ⚠️ Cơ bản | ❌ Không | ✅ Có | ⚠️ Cơ bản |
| Performance Monitor | ✅ Real-time | ❌ Không | ❌ Không | ❌ Không | ❌ Không |
| Offline-first | ✅ Hoàn toàn | ✅ Có | ✅ Có | ✅ Có | ✅ Có |
| Multi-model Support | ✅ SD/SDXL/Flux/SD3+ | ✅ Rộng | ⚠️ SDXL focus | ✅ Rộng | ✅ Rộng |
| Future: Video/3D/LLM | ✅ Planned | ⚠️ Community | ❌ Không | ❌ Không | ❌ Không |

---

## 🎯 Mục Tiêu

### Ngắn Hạn (6 tháng đầu)

1. **Core Engine**: Xây dựng AI engine ổn định hỗ trợ Text-to-Image, Image-to-Image
2. **Desktop App**: Giao diện Electron đẹp, responsive, dark mode
3. **Model Management**: Tải, quản lý, chuyển đổi model dễ dàng
4. **VRAM Optimization**: Tối ưu cho GPU 8GB VRAM (RTX 4060 Laptop)
5. **Plugin Foundation**: Kiến trúc plugin system sẵn sàng mở rộng

### Trung Hạn (6-12 tháng)

1. **Advanced Features**: Inpainting, Outpainting, ControlNet, LoRA
2. **Workflow System**: Visual workflow builder
3. **Batch Processing**: Tạo ảnh hàng loạt với queue system
4. **Community**: Plugin marketplace, sharing workflows

### Dài Hạn (12+ tháng)

1. **Multi-Model**: Hỗ trợ SDXL, Flux, SD3, Pony, Illustrious
2. **Beyond Image**: Video Generation, 3D Generation
3. **AI Agent**: Tích hợp Local LLM cho prompt enhancement
4. **Platform**: Trở thành nền tảng AI Creation toàn diện

---

## ✨ Tính Năng

### Core Features

| Tính năng | Mô tả | Trạng thái |
|---|---|---|
| Text to Image | Tạo ảnh từ prompt văn bản | 🔜 Phase 1 |
| Image to Image | Biến đổi ảnh dựa trên prompt | 🔜 Phase 1 |
| Negative Prompt | Loại bỏ các yếu tố không mong muốn | 🔜 Phase 1 |
| Inpainting | Chỉnh sửa một phần của ảnh | 🔜 Phase 2 |
| Outpainting | Mở rộng ảnh ra ngoài biên | 🔜 Phase 2 |
| ControlNet | Kiểm soát bố cục, tư thế, đường nét | 🔜 Phase 2 |
| LoRA | Sử dụng LoRA models cho phong cách riêng | 🔜 Phase 2 |
| Upscale | Phóng to ảnh với chất lượng cao | 🔜 Phase 3 |
| Face Restore | Khôi phục khuôn mặt chi tiết | 🔜 Phase 3 |

### Platform Features

| Tính năng | Mô tả | Trạng thái |
|---|---|---|
| Prompt Enhancer | AI cải thiện prompt tự động | 🔜 Phase 3 |
| Batch Generate | Tạo nhiều ảnh cùng lúc | 🔜 Phase 2 |
| Queue System | Hàng đợi xử lý với priority | 🔜 Phase 1 |
| History | Lịch sử tạo ảnh đầy đủ | 🔜 Phase 1 |
| Gallery | Bộ sưu tập ảnh với filter/search | 🔜 Phase 2 |
| Model Manager | Quản lý models đã tải | 🔜 Phase 1 |
| Download Manager | Tải model từ HuggingFace/CivitAI | 🔜 Phase 2 |
| Settings | Cấu hình ứng dụng toàn diện | 🔜 Phase 1 |
| Performance Monitor | Giám sát hiệu suất real-time | 🔜 Phase 1 |
| VRAM Monitor | Giám sát VRAM usage | 🔜 Phase 1 |
| Workflow | Visual workflow builder | 🔜 Phase 3 |
| Plugin System | Extension API cho developers | 🔜 Phase 3 |
| Plugin Marketplace | Cửa hàng plugins | 🔜 Phase 4 |

---

## 🏗 Kiến Trúc

Image Agent sử dụng kiến trúc **Clean Architecture** kết hợp **Modular Architecture** với 4 layer chính:

```
┌─────────────────────────────────────────────────────┐
│                   PRESENTATION LAYER                │
│          Electron + React + TypeScript              │
│    ┌─────────┬─────────┬─────────┬─────────┐       │
│    │  Pages  │Components│ Stores  │ Hooks   │       │
│    └─────────┴─────────┴─────────┴─────────┘       │
└──────────────────────┬──────────────────────────────┘
                       │ IPC / REST API / WebSocket
┌──────────────────────┴──────────────────────────────┐
│                    API LAYER                         │
│              FastAPI + WebSocket                     │
│    ┌─────────┬─────────┬─────────┬─────────┐       │
│    │ Routes  │  DTOs   │  Auth   │  WS     │       │
│    └─────────┴─────────┴─────────┴─────────┘       │
└──────────────────────┬──────────────────────────────┘
                       │ Dependency Injection
┌──────────────────────┴──────────────────────────────┐
│                  SERVICE LAYER                       │
│            Business Logic + Use Cases                │
│    ┌─────────┬─────────┬─────────┬─────────┐       │
│    │Services │  Queue   │ Events  │Plugins  │       │
│    └─────────┴─────────┴─────────┴─────────┘       │
└──────────────────────┬──────────────────────────────┘
                       │ Interfaces / Abstractions
┌──────────────────────┴──────────────────────────────┐
│                   CORE LAYER                         │
│     AI Engine + Data Access + Infrastructure         │
│    ┌─────────┬─────────┬─────────┬─────────┐       │
│    │AI Engine│   DB    │  File   │  Model  │       │
│    │PyTorch  │ SQLite  │ Storage │ Manager │       │
│    │Diffusers│SQLAlchemy│        │         │       │
│    └─────────┴─────────┴─────────┴─────────┘       │
└─────────────────────────────────────────────────────┘
```

### Nguyên Tắc Kiến Trúc

- **Clean Architecture**: Dependency rule — layer ngoài phụ thuộc layer trong, không ngược lại
- **Modular**: Mỗi tính năng là một module độc lập, có thể thêm/bớt
- **Event-Driven**: Giao tiếp giữa các module qua event bus
- **Plugin-Based**: Mở rộng tính năng qua plugin API mà không cần sửa core
- **DI Container**: Dependency Injection cho loose coupling

> 📖 Chi tiết kiến trúc: Xem [ARCHITECTURE.md](./docs/ARCHITECTURE.md)

---

## 💻 Yêu Cầu Hệ Thống

### Tối Thiểu (Minimum)

| Thành phần | Yêu cầu |
|---|---|
| **OS** | Windows 10 64-bit (build 19041+) |
| **CPU** | Intel Core i7 Gen 10+ / AMD Ryzen 7 3700X+ |
| **GPU** | NVIDIA RTX 3060 (6GB VRAM) |
| **RAM** | 16GB DDR4 |
| **Storage** | 50GB SSD trống (cho app + 1 model) |
| **CUDA** | CUDA 11.8+ |

### Khuyến Nghị (Recommended)

| Thành phần | Yêu cầu |
|---|---|
| **OS** | Windows 11 64-bit |
| **CPU** | Intel Core i9-13900HX / AMD Ryzen 9 7945HX |
| **GPU** | NVIDIA RTX 4060+ (8GB VRAM) |
| **RAM** | 32GB DDR5 |
| **Storage** | 200GB NVMe SSD |
| **CUDA** | CUDA 12.1+ |

### Cấu Hình Phát Triển (Development Target)

| Thành phần | Spec |
|---|---|
| **CPU** | Intel Core i9-13900HX |
| **GPU** | NVIDIA RTX 4060 Laptop 8GB VRAM |
| **RAM** | 16GB |
| **OS** | Windows 11 |

### Software Requirements

| Software | Version | Mục đích |
|---|---|---|
| Python | 3.11+ | Backend runtime |
| Node.js | 20 LTS+ | Frontend build |
| CUDA Toolkit | 12.1+ | GPU acceleration |
| cuDNN | 8.9+ | Deep learning primitives |
| Git | 2.40+ | Version control |
| Visual Studio Build Tools | 2022 | Native module compilation |

---

## 🚀 Cài Đặt

### Prerequisites

```bash
# 1. Cài đặt Python 3.11+
# Download từ https://python.org

# 2. Cài đặt Node.js 20 LTS
# Download từ https://nodejs.org

# 3. Cài đặt CUDA Toolkit 12.1
# Download từ https://developer.nvidia.com/cuda-toolkit

# 4. Cài đặt Git
# Download từ https://git-scm.com
```

### Clone & Setup

```bash
# Clone repository
git clone https://github.com/your-org/image-agent.git
cd image-agent

# Setup backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Setup frontend
cd ../frontend
npm install

# Khởi chạy development
# Terminal 1: Backend
cd backend
python -m uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev

# Terminal 3: Electron
cd frontend
npm run electron:dev
```

### Cài Đặt Model Đầu Tiên

```bash
# Sử dụng Model Manager trong ứng dụng
# Hoặc tải manual vào thư mục models/
# Hỗ trợ: .safetensors, .ckpt, .bin
```

---

## 🛠 Hướng Dẫn Phát Triển

### Cấu Trúc Dự Án

Dự án sử dụng **Monorepo** với 2 package chính:

```
image-agent/
├── backend/           # Python Backend (FastAPI)
├── frontend/          # Electron + React Frontend
├── shared/            # Shared types, constants
├── models/            # AI Models storage (gitignored)
├── outputs/           # Generated images (gitignored)
├── plugins/           # Plugin directory
├── docs/              # Documentation
├── scripts/           # Build & utility scripts
├── tests/             # Integration tests
└── tools/             # Development tools
```

### Development Workflow

1. **Feature Branch**: Tạo branch từ `develop`
2. **Implement**: Viết code theo CODING_STANDARD
3. **Test**: Chạy unit tests + integration tests
4. **PR**: Tạo Pull Request với description chi tiết
5. **Review**: Code review bởi ít nhất 1 người
6. **Merge**: Squash merge vào `develop`

### Quy Tắc Quan Trọng

- ❌ **KHÔNG** tạo God Class (class làm quá nhiều việc)
- ❌ **KHÔNG** viết code khó đọc, khó bảo trì
- ❌ **KHÔNG** hardcode giá trị
- ❌ **KHÔNG** bỏ qua error handling
- ❌ **KHÔNG** commit trực tiếp vào `main` hoặc `develop`
- ✅ **LUÔN** viết type hints (Python) / TypeScript types
- ✅ **LUÔN** viết docstring / JSDoc
- ✅ **LUÔN** xử lý edge cases
- ✅ **LUÔN** log có ý nghĩa
- ✅ **LUÔN** tuân thủ SOLID principles

> 📖 Chi tiết: Xem [CODING_STANDARD.md](./docs/CODING_STANDARD.md)

---

## 📁 Cấu Trúc Thư Mục

```
image-agent/
│
├── 📂 backend/                          # ═══ PYTHON BACKEND ═══
│   ├── 📂 app/
│   │   ├── 📂 api/                      # API Layer
│   │   │   ├── 📂 v1/                   # API versioning
│   │   │   │   ├── 📂 routes/           # FastAPI routers
│   │   │   │   │   ├── generation.py    # /generate endpoints
│   │   │   │   │   ├── models.py        # /models endpoints
│   │   │   │   │   ├── gallery.py       # /gallery endpoints
│   │   │   │   │   ├── queue.py         # /queue endpoints
│   │   │   │   │   ├── settings.py      # /settings endpoints
│   │   │   │   │   ├── system.py        # /system endpoints
│   │   │   │   │   └── plugins.py       # /plugins endpoints
│   │   │   │   └── __init__.py
│   │   │   ├── 📂 websocket/            # WebSocket handlers
│   │   │   │   ├── progress.py          # Generation progress
│   │   │   │   ├── monitor.py           # System monitor
│   │   │   │   └── events.py            # Event streaming
│   │   │   ├── 📂 dto/                  # Data Transfer Objects
│   │   │   │   ├── requests.py          # Request schemas
│   │   │   │   ├── responses.py         # Response schemas
│   │   │   │   └── common.py            # Shared schemas
│   │   │   └── 📂 middleware/           # API middleware
│   │   │       ├── error_handler.py     # Global error handler
│   │   │       ├── logging.py           # Request logging
│   │   │       └── cors.py              # CORS configuration
│   │   │
│   │   ├── 📂 core/                     # Core Layer (Domain)
│   │   │   ├── 📂 entities/             # Domain entities
│   │   │   │   ├── generation.py        # Generation entity
│   │   │   │   ├── model.py             # Model entity
│   │   │   │   ├── image.py             # Image entity
│   │   │   │   ├── queue_item.py        # Queue item entity
│   │   │   │   ├── plugin.py            # Plugin entity
│   │   │   │   └── settings.py          # Settings entity
│   │   │   ├── 📂 interfaces/           # Abstract interfaces
│   │   │   │   ├── ai_engine.py         # IAIEngine interface
│   │   │   │   ├── model_loader.py      # IModelLoader interface
│   │   │   │   ├── image_processor.py   # IImageProcessor interface
│   │   │   │   ├── queue_manager.py     # IQueueManager interface
│   │   │   │   ├── storage.py           # IStorage interface
│   │   │   │   ├── plugin_manager.py    # IPluginManager interface
│   │   │   │   └── event_bus.py         # IEventBus interface
│   │   │   ├── 📂 enums/               # Enumerations
│   │   │   │   ├── generation_type.py   # txt2img, img2img, etc.
│   │   │   │   ├── model_type.py        # SD, SDXL, Flux, etc.
│   │   │   │   ├── status.py            # Queue/generation status
│   │   │   │   └── scheduler.py         # Sampler/scheduler types
│   │   │   ├── 📂 exceptions/          # Custom exceptions
│   │   │   │   ├── base.py              # Base exception classes
│   │   │   │   ├── generation.py        # Generation errors
│   │   │   │   ├── model.py             # Model errors
│   │   │   │   └── plugin.py            # Plugin errors
│   │   │   └── 📂 constants/           # Application constants
│   │   │       ├── defaults.py          # Default values
│   │   │       ├── limits.py            # System limits
│   │   │       └── paths.py             # Default paths
│   │   │
│   │   ├── 📂 services/                # Service Layer (Use Cases)
│   │   │   ├── generation_service.py    # Generation orchestration
│   │   │   ├── model_service.py         # Model management
│   │   │   ├── queue_service.py         # Queue management
│   │   │   ├── gallery_service.py       # Gallery management
│   │   │   ├── history_service.py       # History management
│   │   │   ├── settings_service.py      # Settings management
│   │   │   ├── plugin_service.py        # Plugin management
│   │   │   ├── download_service.py      # Download management
│   │   │   └── system_service.py        # System monitoring
│   │   │
│   │   ├── 📂 engine/                  # AI Engine Layer
│   │   │   ├── 📂 pipelines/            # Generation pipelines
│   │   │   │   ├── base_pipeline.py     # Abstract base pipeline
│   │   │   │   ├── txt2img.py           # Text to Image
│   │   │   │   ├── img2img.py           # Image to Image
│   │   │   │   ├── inpaint.py           # Inpainting
│   │   │   │   ├── outpaint.py          # Outpainting
│   │   │   │   └── controlnet.py        # ControlNet
│   │   │   ├── 📂 processors/          # Image processors
│   │   │   │   ├── upscaler.py          # Image upscaling
│   │   │   │   ├── face_restore.py      # Face restoration
│   │   │   │   └── preprocessor.py      # ControlNet preprocessors
│   │   │   ├── 📂 schedulers/          # Noise schedulers
│   │   │   │   └── scheduler_factory.py # Scheduler creation
│   │   │   ├── 📂 optimizers/          # VRAM & performance
│   │   │   │   ├── vram_manager.py      # VRAM management
│   │   │   │   ├── attention.py         # Attention optimization
│   │   │   │   └── model_offload.py     # CPU/GPU offloading
│   │   │   ├── model_loader.py          # Model loading logic
│   │   │   └── engine.py               # Main AI engine
│   │   │
│   │   ├── 📂 infrastructure/          # Infrastructure Layer
│   │   │   ├── 📂 database/             # Database
│   │   │   │   ├── connection.py        # DB connection manager
│   │   │   │   ├── models.py            # SQLAlchemy models
│   │   │   │   ├── migrations/          # Alembic migrations
│   │   │   │   └── repositories/        # Data repositories
│   │   │   │       ├── base.py          # Base repository
│   │   │   │       ├── generation_repo.py
│   │   │   │       ├── model_repo.py
│   │   │   │       ├── image_repo.py
│   │   │   │       └── settings_repo.py
│   │   │   ├── 📂 storage/             # File storage
│   │   │   │   ├── local_storage.py     # Local file storage
│   │   │   │   └── thumbnail.py         # Thumbnail generator
│   │   │   ├── 📂 events/              # Event system
│   │   │   │   ├── event_bus.py         # Event bus implementation
│   │   │   │   ├── event_types.py       # Event type definitions
│   │   │   │   └── handlers/            # Event handlers
│   │   │   ├── 📂 queue/               # Queue system
│   │   │   │   ├── queue_manager.py     # Queue implementation
│   │   │   │   └── worker.py            # Queue worker
│   │   │   └── 📂 plugins/             # Plugin system
│   │   │       ├── plugin_loader.py     # Plugin discovery & loading
│   │   │       ├── plugin_manager.py    # Plugin lifecycle
│   │   │       ├── plugin_api.py        # Plugin API exposure
│   │   │       └── sandbox.py           # Plugin sandboxing
│   │   │
│   │   ├── 📂 di/                      # Dependency Injection
│   │   │   ├── container.py             # DI container setup
│   │   │   └── providers.py             # Service providers
│   │   │
│   │   ├── 📂 config/                  # Configuration
│   │   │   ├── settings.py              # App settings (Pydantic)
│   │   │   ├── logging_config.py        # Logging configuration
│   │   │   └── gpu_config.py            # GPU-specific config
│   │   │
│   │   └── main.py                      # FastAPI app entry point
│   │
│   ├── 📂 tests/                       # Backend tests
│   │   ├── 📂 unit/
│   │   ├── 📂 integration/
│   │   └── 📂 fixtures/
│   │
│   ├── requirements.txt                 # Production dependencies
│   ├── requirements-dev.txt             # Development dependencies
│   ├── pyproject.toml                   # Python project config
│   ├── alembic.ini                      # Database migrations config
│   └── pytest.ini                       # Test configuration
│
├── 📂 frontend/                         # ═══ ELECTRON + REACT ═══
│   ├── 📂 src/
│   │   ├── 📂 main/                    # Electron main process
│   │   │   ├── index.ts                 # Main entry point
│   │   │   ├── window.ts               # Window management
│   │   │   ├── ipc.ts                  # IPC handlers
│   │   │   ├── tray.ts                 # System tray
│   │   │   ├── updater.ts             # Auto-updater
│   │   │   └── backend.ts             # Backend process manager
│   │   │
│   │   ├── 📂 renderer/               # React renderer process
│   │   │   ├── 📂 app/                 # App setup
│   │   │   │   ├── App.tsx             # Root component
│   │   │   │   ├── Router.tsx          # Route definitions
│   │   │   │   └── providers.tsx       # Context providers
│   │   │   │
│   │   │   ├── 📂 pages/              # Page components
│   │   │   │   ├── GeneratePage/       # Main generation page
│   │   │   │   ├── GalleryPage/        # Image gallery
│   │   │   │   ├── ModelsPage/         # Model management
│   │   │   │   ├── QueuePage/          # Queue management
│   │   │   │   ├── HistoryPage/        # Generation history
│   │   │   │   ├── SettingsPage/       # App settings
│   │   │   │   ├── PluginsPage/        # Plugin marketplace
│   │   │   │   └── WorkflowPage/       # Workflow builder
│   │   │   │
│   │   │   ├── 📂 components/         # Shared components
│   │   │   │   ├── 📂 ui/             # shadcn/ui components
│   │   │   │   ├── 📂 layout/         # Layout components
│   │   │   │   │   ├── Sidebar.tsx
│   │   │   │   │   ├── Header.tsx
│   │   │   │   │   ├── StatusBar.tsx
│   │   │   │   │   └── MainLayout.tsx
│   │   │   │   ├── 📂 generation/     # Generation-specific
│   │   │   │   │   ├── PromptInput.tsx
│   │   │   │   │   ├── ParameterPanel.tsx
│   │   │   │   │   ├── ImagePreview.tsx
│   │   │   │   │   ├── SamplerSelect.tsx
│   │   │   │   │   └── SeedControl.tsx
│   │   │   │   ├── 📂 gallery/        # Gallery components
│   │   │   │   ├── 📂 model/          # Model components
│   │   │   │   ├── 📂 monitor/        # Monitor components
│   │   │   │   │   ├── VRAMMonitor.tsx
│   │   │   │   │   ├── GPUMonitor.tsx
│   │   │   │   │   └── PerformancePanel.tsx
│   │   │   │   └── 📂 common/         # Common components
│   │   │   │       ├── ImageViewer.tsx
│   │   │   │       ├── ProgressBar.tsx
│   │   │   │       ├── LoadingSpinner.tsx
│   │   │   │       └── ErrorBoundary.tsx
│   │   │   │
│   │   │   ├── 📂 stores/            # Zustand stores
│   │   │   │   ├── generationStore.ts  # Generation state
│   │   │   │   ├── modelStore.ts       # Model state
│   │   │   │   ├── queueStore.ts       # Queue state
│   │   │   │   ├── galleryStore.ts     # Gallery state
│   │   │   │   ├── settingsStore.ts    # Settings state
│   │   │   │   ├── uiStore.ts          # UI state
│   │   │   │   └── systemStore.ts      # System monitor state
│   │   │   │
│   │   │   ├── 📂 hooks/             # Custom React hooks
│   │   │   │   ├── useGeneration.ts    # Generation logic
│   │   │   │   ├── useModels.ts        # Model operations
│   │   │   │   ├── useWebSocket.ts     # WebSocket connection
│   │   │   │   ├── useQueue.ts         # Queue operations
│   │   │   │   ├── useGallery.ts       # Gallery operations
│   │   │   │   ├── useSystem.ts        # System monitoring
│   │   │   │   └── useKeyboard.ts      # Keyboard shortcuts
│   │   │   │
│   │   │   ├── 📂 services/          # API service layer
│   │   │   │   ├── api.ts              # Axios/fetch setup
│   │   │   │   ├── generationApi.ts    # Generation endpoints
│   │   │   │   ├── modelApi.ts         # Model endpoints
│   │   │   │   ├── galleryApi.ts       # Gallery endpoints
│   │   │   │   ├── queueApi.ts         # Queue endpoints
│   │   │   │   └── systemApi.ts        # System endpoints
│   │   │   │
│   │   │   ├── 📂 types/             # TypeScript types
│   │   │   │   ├── generation.ts       # Generation types
│   │   │   │   ├── model.ts            # Model types
│   │   │   │   ├── image.ts            # Image types
│   │   │   │   ├── queue.ts            # Queue types
│   │   │   │   ├── settings.ts         # Settings types
│   │   │   │   ├── api.ts              # API types
│   │   │   │   └── system.ts           # System types
│   │   │   │
│   │   │   ├── 📂 utils/             # Utility functions
│   │   │   │   ├── format.ts           # Formatting helpers
│   │   │   │   ├── validation.ts       # Input validation
│   │   │   │   ├── image.ts            # Image utilities
│   │   │   │   └── constants.ts        # Frontend constants
│   │   │   │
│   │   │   ├── 📂 styles/            # Global styles
│   │   │   │   ├── globals.css         # Global CSS
│   │   │   │   └── themes/            # Theme definitions
│   │   │   │
│   │   │   └── index.tsx               # Renderer entry point
│   │   │
│   │   └── 📂 preload/               # Electron preload scripts
│   │       └── index.ts                # Preload entry
│   │
│   ├── 📂 public/                     # Static assets
│   │   ├── icons/                      # App icons
│   │   └── images/                     # Static images
│   │
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── vite.config.ts
│   ├── electron-builder.yml
│   └── .eslintrc.cjs
│
├── 📂 shared/                          # ═══ SHARED ═══
│   ├── types/                          # Shared type definitions
│   ├── constants/                      # Shared constants
│   └── utils/                          # Shared utilities
│
├── 📂 models/                          # ═══ AI MODELS (gitignored) ═══
│   ├── checkpoints/                    # Main model files
│   ├── loras/                          # LoRA models
│   ├── controlnet/                     # ControlNet models
│   ├── upscalers/                      # Upscaler models
│   ├── vae/                            # VAE models
│   ├── embeddings/                     # Textual inversions
│   └── other/                          # Other model types
│
├── 📂 outputs/                         # ═══ GENERATED IMAGES (gitignored) ═══
│   ├── txt2img/
│   ├── img2img/
│   ├── inpaint/
│   ├── upscale/
│   └── thumbnails/
│
├── 📂 plugins/                         # ═══ PLUGINS ═══
│   ├── installed/                      # Installed plugins
│   └── dev/                            # Plugins in development
│
├── 📂 docs/                            # ═══ DOCUMENTATION ═══
│   ├── PROJECT_SUMMARY.md
│   ├── DEVELOPMENT_PLAN.md
│   ├── TECH_STACK.md
│   ├── ARCHITECTURE.md
│   ├── CODING_STANDARD.md
│   ├── FUTURE_FEATURES.md
│   ├── TODO.md
│   └── 📂 api/                        # API documentation
│       └── openapi.yaml
│
├── 📂 scripts/                         # ═══ SCRIPTS ═══
│   ├── setup.ps1                       # Windows setup script
│   ├── dev.ps1                         # Development launcher
│   ├── build.ps1                       # Build script
│   └── clean.ps1                       # Cleanup script
│
├── 📂 tests/                           # ═══ INTEGRATION TESTS ═══
│   ├── e2e/                            # End-to-end tests
│   └── performance/                    # Performance benchmarks
│
├── 📂 tools/                           # ═══ DEV TOOLS ═══
│   ├── model_converter/                # Model conversion tools
│   └── benchmark/                      # Benchmark tools
│
├── .gitignore
├── .editorconfig
├── .env.example
├── LICENSE
└── README.md                           # This file
```

---

## 🗺 Roadmap

### Phase 1: Foundation (8-10 tuần)

> Xây dựng nền tảng kiến trúc và tính năng cơ bản nhất

- [x] Project documentation
- [ ] Backend skeleton (FastAPI + Clean Architecture)
- [ ] AI Engine core (PyTorch + Diffusers)
- [ ] Text-to-Image basic
- [ ] Image-to-Image basic
- [ ] Frontend skeleton (Electron + React)
- [ ] Basic UI (Prompt input, Parameter panel, Image preview)
- [ ] Model Manager (load local models)
- [ ] Queue system (basic)
- [ ] History (basic)
- [ ] Settings (basic)
- [ ] VRAM Monitor (basic)
- [ ] WebSocket progress tracking

### Phase 2: Core Features (8-10 tuần)

> Mở rộng tính năng generation và cải thiện UX

- [ ] Inpainting
- [ ] Outpainting
- [ ] ControlNet support
- [ ] LoRA support
- [ ] Batch generation
- [ ] Gallery with search/filter
- [ ] Download Manager (HuggingFace, CivitAI)
- [ ] Advanced queue (priority, pause/resume)
- [ ] Improved UI/UX
- [ ] Keyboard shortcuts

### Phase 3: Advanced (8-10 tuần)

> Tính năng nâng cao và hệ thống plugin

- [ ] Upscale (ESRGAN, SwinIR)
- [ ] Face Restore (GFPGAN, CodeFormer)
- [ ] Prompt Enhancer (Local LLM)
- [ ] Workflow builder
- [ ] Plugin System (Extension API)
- [ ] SDXL full support
- [ ] Advanced VRAM optimization
- [ ] Performance profiling

### Phase 4: Platform (10-12 tuần)

> Trở thành nền tảng toàn diện

- [ ] Plugin Marketplace
- [ ] Flux model support
- [ ] SD3 model support
- [ ] Community workflow sharing
- [ ] ONNX Runtime support
- [ ] Advanced batch workflows
- [ ] Multi-language UI

### Phase 5: Next Generation (12+ tuần)

> Mở rộng sang các lĩnh vực mới

- [ ] Video Generation
- [ ] 3D Generation
- [ ] AI Agent integration
- [ ] Local LLM integration
- [ ] Pony/Illustrious support
- [ ] Multi-GPU support
- [ ] Cloud sync (optional)

---

## 🤝 Quy Tắc Đóng Góp

### Git Workflow

Sử dụng **Git Flow** với các branch:

```
main          ← Production releases
  └── develop     ← Development integration
       ├── feature/xxx   ← New features
       ├── fix/xxx       ← Bug fixes
       ├── refactor/xxx  ← Code refactoring
       └── docs/xxx      ← Documentation
```

### Commit Convention

Sử dụng **Conventional Commits**:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**

| Type | Mô tả |
|---|---|
| `feat` | Tính năng mới |
| `fix` | Sửa lỗi |
| `docs` | Thay đổi documentation |
| `style` | Formatting, không thay đổi logic |
| `refactor` | Refactoring code |
| `perf` | Cải thiện performance |
| `test` | Thêm/sửa tests |
| `chore` | Build, CI, dependencies |

**Ví dụ:**

```
feat(engine): add text-to-image pipeline with diffusers
fix(vram): resolve memory leak when switching models
docs(readme): update installation instructions
refactor(queue): extract queue worker into separate module
perf(engine): optimize attention computation for 8GB VRAM
```

### Pull Request

- Title theo Conventional Commits
- Description phải mô tả rõ: **What**, **Why**, **How**
- Phải có screenshots/recordings nếu thay đổi UI
- Phải pass tất cả tests
- Phải được review bởi ít nhất 1 người

### Code Quality Checklist

Trước khi tạo PR, kiểm tra:

- [ ] Code tuân thủ CODING_STANDARD
- [ ] Có type hints đầy đủ (Python)
- [ ] Có TypeScript types đầy đủ
- [ ] Có docstring/JSDoc cho public API
- [ ] Có unit tests cho logic mới
- [ ] Không có `# TODO` hoặc `// FIXME` bị bỏ quên
- [ ] Không có hardcoded values
- [ ] Error handling đầy đủ
- [ ] Logging có ý nghĩa
- [ ] Không có console.log (frontend) hoặc print (backend)

---

## 📚 Tài Liệu Liên Quan

| Tài liệu | Mô tả |
|---|---|
| [PROJECT_SUMMARY.md](./docs/PROJECT_SUMMARY.md) | Tổng quan dự án chi tiết |
| [DEVELOPMENT_PLAN.md](./docs/DEVELOPMENT_PLAN.md) | Kế hoạch phát triển theo phase |
| [TECH_STACK.md](./docs/TECH_STACK.md) | Phân tích công nghệ sử dụng |
| [ARCHITECTURE.md](./docs/ARCHITECTURE.md) | Thiết kế kiến trúc tổng thể |
| [CODING_STANDARD.md](./docs/CODING_STANDARD.md) | Quy chuẩn viết code |
| [FUTURE_FEATURES.md](./docs/FUTURE_FEATURES.md) | Tính năng tương lai |
| [TODO.md](./docs/TODO.md) | Danh sách việc cần làm |

---

## 📄 License

MIT License — Xem [LICENSE](./LICENSE) để biết chi tiết.

---

<p align="center">
  <strong>Image Agent</strong> — Local AI Image Generation Platform
  <br>
  Built with ❤️ for the AI Art Community
</p>
