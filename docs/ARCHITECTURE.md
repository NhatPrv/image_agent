# 🏗 Architecture — Image Agent

> Thiết kế kiến trúc tổng thể của Image Agent, bao gồm module diagram, data flow, folder structure, dependency graph, plugin system, event system và tất cả các layer.

---

## Mục Lục

- [Tổng Quan Kiến Trúc](#tổng-quan-kiến-trúc)
- [Nguyên Tắc Thiết Kế](#nguyên-tắc-thiết-kế)
- [Module Diagram](#module-diagram)
- [Layer Architecture](#layer-architecture)
- [Data Flow](#data-flow)
- [Event System](#event-system)
- [Plugin System](#plugin-system)
- [AI Engine Architecture](#ai-engine-architecture)
- [API Layer](#api-layer)
- [Frontend Architecture](#frontend-architecture)
- [Dependency Injection](#dependency-injection)
- [Database Design](#database-design)
- [Communication Patterns](#communication-patterns)
- [Error Handling Architecture](#error-handling-architecture)
- [Security Considerations](#security-considerations)

---

## Tổng Quan Kiến Trúc

Image Agent sử dụng kiến trúc **Clean Architecture** (Uncle Bob) kết hợp **Modular Architecture** và **Event-Driven Architecture**. Hệ thống được chia thành các layer đồng tâm, với dependency rule nghiêm ngặt: **layer ngoài phụ thuộc layer trong, KHÔNG BAO GIỜ ngược lại**.

### Kiến Trúc Tổng Thể (High-Level)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        ELECTRON MAIN PROCESS                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐   │
│  │ Window   │  │ IPC      │  │ Tray     │  │ Backend Process Mgr  │   │
│  │ Manager  │  │ Bridge   │  │ Manager  │  │ (Start/Stop Python)  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────────┘   │
└──────────────────────────────┬─────────────────────────────────────────┘
                               │ IPC Channel
┌──────────────────────────────┴─────────────────────────────────────────┐
│                     ELECTRON RENDERER PROCESS                          │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    REACT APPLICATION                              │  │
│  │  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────────┐  │  │
│  │  │  Pages  │  │Components│  │  Stores  │  │  API Services   │  │  │
│  │  │         │  │ (shadcn) │  │(Zustand) │  │(TanStack Query) │  │  │
│  │  └─────────┘  └──────────┘  └──────────┘  └────────┬────────┘  │  │
│  └──────────────────────────────────────────────────────┼──────────┘  │
└──────────────────────────────────────────────────────────┼────────────┘
                                                           │ HTTP / WebSocket
┌──────────────────────────────────────────────────────────┴────────────┐
│                       PYTHON BACKEND                                  │
│                                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                      API LAYER (FastAPI)                        │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │  │
│  │  │  REST    │  │WebSocket │  │Middleware │  │     DTOs      │  │  │
│  │  │  Routes  │  │ Handlers │  │          │  │  (Pydantic)   │  │  │
│  │  └────┬─────┘  └────┬─────┘  └──────────┘  └───────────────┘  │  │
│  └───────┼──────────────┼─────────────────────────────────────────┘  │
│          │              │                                             │
│  ┌───────┴──────────────┴─────────────────────────────────────────┐  │
│  │                    SERVICE LAYER                                │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │  │
│  │  │  Generation  │  │    Model     │  │      Queue           │  │  │
│  │  │   Service    │  │   Service    │  │     Service          │  │  │
│  │  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │  │
│  │  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────────┴───────────┐  │  │
│  │  │   Gallery    │  │   History    │  │     Plugin           │  │  │
│  │  │   Service    │  │   Service    │  │    Service           │  │  │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘  │  │
│  └───────────────────────────┬────────────────────────────────────┘  │
│                              │                                        │
│  ┌───────────────────────────┴────────────────────────────────────┐  │
│  │                      CORE LAYER                                │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │  │
│  │  │Entities  │  │Interfaces│  │  Enums   │  │ Exceptions   │  │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────────┘  │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                              │                                        │
│  ┌───────────────────────────┴────────────────────────────────────┐  │
│  │                  INFRASTRUCTURE LAYER                           │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │  │
│  │  │AI Engine │  │ Database │  │  Events  │  │   Plugins    │  │  │
│  │  │ PyTorch  │  │ SQLAlch. │  │Event Bus │  │Plugin System │  │  │
│  │  │Diffusers │  │ SQLite   │  │          │  │              │  │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────────┘  │  │
│  │  ┌──────────┐  ┌──────────┐                                   │  │
│  │  │ Storage  │  │  Queue   │                                   │  │
│  │  │File Sys. │  │ Worker   │                                   │  │
│  │  └──────────┘  └──────────┘                                   │  │
│  └───────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Nguyên Tắc Thiết Kế

### 1. Clean Architecture — Dependency Rule

```
         Outer layers depend on inner layers
         Inner layers NEVER depend on outer layers

    ┌──────────────────────────────────────────┐
    │             API LAYER                     │
    │   ┌──────────────────────────────────┐   │
    │   │         SERVICE LAYER            │   │
    │   │   ┌──────────────────────────┐   │   │
    │   │   │       CORE LAYER         │   │   │
    │   │   │   ┌──────────────────┐   │   │   │
    │   │   │   │    ENTITIES      │   │   │   │
    │   │   │   └──────────────────┘   │   │   │
    │   │   └──────────────────────────┘   │   │
    │   └──────────────────────────────────┘   │
    └──────────────────────────────────────────┘
```

- **Entities** (innermost): Pure data classes, không dependency
- **Core Layer**: Interfaces, enums, exceptions — defines contracts
- **Service Layer**: Business logic, sử dụng interfaces (không concrete implementations)
- **Infrastructure**: Concrete implementations (database, AI engine, file storage)
- **API Layer** (outermost): HTTP routes, WebSocket, DTOs

### 2. SOLID Principles

| Principle | Áp dụng trong Image Agent |
|---|---|
| **S** — Single Responsibility | Mỗi class/module một nhiệm vụ. GenerationService chỉ orchestrate generation, không load model |
| **O** — Open/Closed | Thêm model type mới qua pipeline interface, không sửa engine core |
| **L** — Liskov Substitution | Txt2ImgPipeline, Img2ImgPipeline đều substitutable cho BasePipeline |
| **I** — Interface Segregation | IAIEngine, IModelLoader, IQueueManager — interfaces nhỏ, focused |
| **D** — Dependency Inversion | Service Layer phụ thuộc interfaces, không phụ thuộc SQLAlchemy hay PyTorch cụ thể |

### 3. Modular Architecture

Mỗi feature là một module độc lập:

```
Module = {
    Entities      — Domain objects
    Interfaces    — Contracts
    Service       — Business logic
    Repository    — Data access
    API Routes    — HTTP endpoints
    Events        — Module-specific events
}
```

Modules giao tiếp qua:
- **Event Bus** (async, decoupled)
- **Service interfaces** (sync, direct)
- **KHÔNG BAO GIỜ** truy cập trực tiếp vào internal state của module khác

### 4. DRY, KISS

- **DRY**: Base classes cho repositories, pipelines, services. Shared utilities.
- **KISS**: Không over-engineer. Bắt đầu đơn giản, refactor khi cần.

---

## Module Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                        IMAGE AGENT                             │
│                                                                │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐   │
│  │  Generation  │  │    Model     │  │      Queue        │   │
│  │   Module     │  │   Module     │  │     Module        │   │
│  │              │  │              │  │                   │   │
│  │ • txt2img    │  │ • loader     │  │ • priority queue  │   │
│  │ • img2img    │  │ • manager    │  │ • worker          │   │
│  │ • inpaint    │  │ • scanner    │  │ • persistence     │   │
│  │ • outpaint   │  │ • converter  │  │ • scheduling      │   │
│  │ • controlnet │  │ • metadata   │  │                   │   │
│  └──────┬───────┘  └──────┬───────┘  └────────┬──────────┘   │
│         │                 │                    │              │
│  ┌──────┴─────────────────┴────────────────────┴──────────┐   │
│  │                    EVENT BUS                            │   │
│  └──────┬─────────────────┬────────────────────┬──────────┘   │
│         │                 │                    │              │
│  ┌──────┴───────┐  ┌──────┴───────┐  ┌────────┴──────────┐   │
│  │   Gallery    │  │   History    │  │    Settings       │   │
│  │   Module     │  │   Module     │  │    Module         │   │
│  │              │  │              │  │                   │   │
│  │ • browse     │  │ • logging    │  │ • app config     │   │
│  │ • search     │  │ • replay     │  │ • gpu config     │   │
│  │ • tags       │  │ • compare    │  │ • path config    │   │
│  │ • favorites  │  │ • export     │  │ • user prefs     │   │
│  └──────────────┘  └──────────────┘  └───────────────────┘   │
│                                                                │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐   │
│  │   Plugin     │  │   System     │  │    Download       │   │
│  │   Module     │  │   Module     │  │    Module         │   │
│  │              │  │              │  │                   │   │
│  │ • discovery  │  │ • GPU monitor│  │ • HTTP client     │   │
│  │ • lifecycle  │  │ • VRAM       │  │ • resume support  │   │
│  │ • sandbox    │  │ • CPU/RAM    │  │ • HuggingFace     │   │
│  │ • marketplace│  │ • disk       │  │ • CivitAI         │   │
│  │ • API        │  │ • benchmarks │  │ • progress        │   │
│  └──────────────┘  └──────────────┘  └───────────────────┘   │
└────────────────────────────────────────────────────────────────┘
```

### Module Dependencies

```
Generation ──→ Model (cần model để generate)
Generation ──→ Queue (generation được queue)
Generation ──→ Gallery (output lưu vào gallery)
Generation ──→ History (generation được log)
Queue ──→ Generation (queue dispatch generation)
Gallery ──→ History (gallery link tới history)
Download ──→ Model (download tải model)
Plugin ──→ Event Bus (plugin listen events)
System ──→ (independent — monitor hardware)
Settings ──→ (independent — app configuration)
```

**Nguyên tắc**: Không có circular dependencies. Dependencies luôn theo một chiều. Module giao tiếp gián tiếp qua Event Bus.

---

## Layer Architecture

### Core Layer (Domain)

Core Layer chứa business entities, interfaces, enums, exceptions — hoàn toàn **không dependency** vào framework hay library nào.

```python
# Ví dụ: Entity (không dependency nào)
class GenerationEntity:
    id: str
    type: GenerationType
    prompt: str
    negative_prompt: str
    width: int
    height: int
    steps: int
    cfg_scale: float
    seed: int
    sampler: SchedulerType
    model_id: str
    status: GenerationStatus
    created_at: datetime
    completed_at: datetime | None
    duration_ms: int | None

# Ví dụ: Interface (abstract contract)
class IAIEngine(ABC):
    @abstractmethod
    async def generate(self, params: GenerationParams) -> GenerationResult: ...

    @abstractmethod
    async def load_model(self, model_path: str) -> ModelInfo: ...

    @abstractmethod
    async def unload_model(self) -> None: ...

    @abstractmethod
    def get_loaded_model(self) -> ModelInfo | None: ...
```

### Service Layer (Use Cases)

Service Layer chứa business logic. Phụ thuộc vào **interfaces** từ Core Layer, KHÔNG phụ thuộc trực tiếp vào implementations.

```python
# Ví dụ conceptual: GenerationService
class GenerationService:
    def __init__(
        self,
        engine: IAIEngine,              # Interface, không concrete
        queue_manager: IQueueManager,    # Interface
        event_bus: IEventBus,            # Interface
        generation_repo: IGenerationRepository,  # Interface
        image_storage: IStorage,         # Interface
    ):
        self._engine = engine
        self._queue = queue_manager
        self._events = event_bus
        self._repo = generation_repo
        self._storage = image_storage

    async def create_generation(self, params: GenerationParams) -> str:
        # 1. Validate params
        # 2. Create generation entity
        # 3. Add to queue
        # 4. Emit event
        # 5. Return generation ID
        ...

    async def execute_generation(self, generation_id: str) -> GenerationResult:
        # 1. Load generation from DB
        # 2. Call engine.generate()
        # 3. Save output image
        # 4. Update generation status
        # 5. Emit completion event
        ...
```

### Infrastructure Layer

Infrastructure Layer chứa concrete implementations của Core interfaces.

```python
# AI Engine implementation (depends on PyTorch, Diffusers)
class DiffusersAIEngine(IAIEngine):
    """Concrete implementation using HuggingFace Diffusers"""
    async def generate(self, params: GenerationParams) -> GenerationResult:
        # PyTorch + Diffusers specific code
        ...

# Database implementation (depends on SQLAlchemy)
class SQLAlchemyGenerationRepository(IGenerationRepository):
    """Concrete implementation using SQLAlchemy"""
    async def save(self, generation: GenerationEntity) -> None:
        # SQLAlchemy specific code
        ...

# File storage implementation
class LocalFileStorage(IStorage):
    """Concrete implementation using local filesystem"""
    async def save_image(self, image: Image, path: str) -> str:
        # File system specific code
        ...
```

### API Layer

API Layer chứa HTTP routes, WebSocket handlers, middleware, DTOs. Nó gọi Service Layer.

```python
# FastAPI route (thin — chỉ nhận request, gọi service, trả response)
@router.post("/generate")
async def create_generation(
    request: GenerateRequest,                    # DTO (Pydantic)
    service: GenerationService = Depends(),      # DI
) -> GenerateResponse:                           # DTO (Pydantic)
    generation_id = await service.create_generation(
        params=request.to_params()               # DTO → Domain conversion
    )
    return GenerateResponse(id=generation_id, status="queued")
```

---

## Data Flow

### Text-to-Image Generation Flow

```
User clicks "Generate"
        │
        ▼
┌─────────────────┐
│   React App     │ 1. Collect prompt, params
│   (Frontend)    │ 2. Call API via TanStack Query
└────────┬────────┘
         │ POST /api/v1/generate
         ▼
┌─────────────────┐
│   API Route     │ 3. Validate request (Pydantic DTO)
│   (FastAPI)     │ 4. Call GenerationService
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Generation     │ 5. Create GenerationEntity
│   Service       │ 6. Save to DB (via Repository)
│                 │ 7. Add to Queue
│                 │ 8. Emit "generation.queued" event
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Queue Worker   │ 9. Pick next item from queue
│                 │ 10. Call GenerationService.execute()
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   AI Engine     │ 11. Load model (if needed)
│  (Diffusers)    │ 12. Configure pipeline
│                 │ 13. Run inference (PyTorch/CUDA)
│                 │ 14. Step callback → WebSocket progress
│                 │ 15. Return generated image
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Generation     │ 16. Save image to disk (via Storage)
│   Service       │ 17. Generate thumbnail
│                 │ 18. Update DB record (completed)
│                 │ 19. Emit "generation.completed" event
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Event Bus      │ 20. Dispatch to listeners:
│                 │     → History module (log entry)
│                 │     → Gallery module (add image)
│                 │     → WebSocket (notify frontend)
│                 │     → Plugins (custom handlers)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  WebSocket      │ 21. Push "generation.completed" to frontend
│  Handler        │ 22. Include image URL, metadata
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  React App      │ 23. TanStack Query invalidates cache
│  (Frontend)     │ 24. Update UI (show generated image)
│                 │ 25. Show notification
└─────────────────┘
```

### Model Loading Flow

```
User selects model
        │
        ▼
┌─────────────────┐
│   React App     │ 1. Call POST /api/v1/models/load
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Model Service  │ 2. Check if model already loaded
│                 │ 3. Check VRAM availability
│                 │ 4. Emit "model.loading" event
│                 │ 5. Call engine.unload_model() if needed
│                 │ 6. Call engine.load_model(path)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   AI Engine     │ 7. Read safetensors/ckpt file
│                 │ 8. Detect model type (SD/SDXL/etc.)
│                 │ 9. Initialize pipeline
│                 │ 10. Move to GPU
│                 │ 11. Apply optimizations (xformers, etc.)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Model Service  │ 12. Update model status in DB
│                 │ 13. Emit "model.loaded" event
│                 │ 14. Update VRAM usage
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  WebSocket      │ 15. Notify frontend: model loaded
│                 │ 16. VRAM update
└─────────────────┘
```

---

## Event System

### Event Bus Architecture

```
┌─────────────────────────────────────────────────────────┐
│                       EVENT BUS                          │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │              Event Registry                       │   │
│  │  event_type → [handler_1, handler_2, handler_3]   │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Publish    │  │  Subscribe   │  │ Unsubscribe  │  │
│  │  (fire&wait  │  │  (register   │  │  (remove     │  │
│  │   or async)  │  │   handler)   │  │   handler)   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Event Types

```python
# Event hierarchy conceptual design
class EventType(str, Enum):
    # Generation events
    GENERATION_QUEUED = "generation.queued"
    GENERATION_STARTED = "generation.started"
    GENERATION_PROGRESS = "generation.progress"
    GENERATION_COMPLETED = "generation.completed"
    GENERATION_FAILED = "generation.failed"
    GENERATION_CANCELLED = "generation.cancelled"

    # Model events
    MODEL_LOADING = "model.loading"
    MODEL_LOADED = "model.loaded"
    MODEL_UNLOADED = "model.unloaded"
    MODEL_ERROR = "model.error"

    # Queue events
    QUEUE_ITEM_ADDED = "queue.item_added"
    QUEUE_ITEM_STARTED = "queue.item_started"
    QUEUE_ITEM_COMPLETED = "queue.item_completed"
    QUEUE_ITEM_CANCELLED = "queue.item_cancelled"
    QUEUE_CLEARED = "queue.cleared"

    # System events
    SYSTEM_VRAM_WARNING = "system.vram_warning"
    SYSTEM_VRAM_CRITICAL = "system.vram_critical"
    SYSTEM_GPU_TEMPERATURE = "system.gpu_temperature"

    # Plugin events
    PLUGIN_LOADED = "plugin.loaded"
    PLUGIN_UNLOADED = "plugin.unloaded"
    PLUGIN_ERROR = "plugin.error"

    # Settings events
    SETTINGS_CHANGED = "settings.changed"

    # Download events
    DOWNLOAD_STARTED = "download.started"
    DOWNLOAD_PROGRESS = "download.progress"
    DOWNLOAD_COMPLETED = "download.completed"
    DOWNLOAD_FAILED = "download.failed"
```

### Event Flow Example

```
GenerationService
    │
    │ emit(GENERATION_COMPLETED, {id, image_path, ...})
    │
    ▼
Event Bus ──→ HistoryService.on_generation_completed()    → Log to history
         ──→ GalleryService.on_generation_completed()     → Add to gallery
         ──→ WebSocketHandler.on_generation_completed()   → Push to frontend
         ──→ PluginX.on_generation_completed()            → Plugin hook
         ──→ SystemService.on_generation_completed()      → Update stats
```

### Event Bus Implementation Strategy

- **In-Process**: Sử dụng Python asyncio cho event dispatch
- **Typed Events**: Mỗi event type có Pydantic payload schema
- **Async Handlers**: Handlers chạy async, không block publisher
- **Error Isolation**: Handler lỗi không ảnh hưởng handler khác
- **Priority**: Handlers có thể đăng ký priority (system > plugin)
- **Middleware**: Event middleware cho logging, metrics

---

## Plugin System

### Plugin Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                        PLUGIN SYSTEM                               │
│                                                                    │
│  ┌────────────────┐                                               │
│  │ Plugin Manager │ ← Quản lý lifecycle toàn bộ plugins           │
│  └───────┬────────┘                                               │
│          │                                                         │
│  ┌───────┴────────┐                                               │
│  │ Plugin Loader  │ ← Discover, validate, load plugins            │
│  │                │                                               │
│  │ 1. Scan dirs   │                                               │
│  │ 2. Read manifest│                                              │
│  │ 3. Validate    │                                               │
│  │ 4. Load module │                                               │
│  │ 5. Initialize  │                                               │
│  └───────┬────────┘                                               │
│          │                                                         │
│  ┌───────┴────────┐                                               │
│  │ Plugin Sandbox │ ← Isolation, resource limits                  │
│  │                │                                               │
│  │ • Process iso  │                                               │
│  │ • Memory limit │                                               │
│  │ • API whitelist│                                               │
│  │ • File access  │                                               │
│  └───────┬────────┘                                               │
│          │                                                         │
│  ┌───────┴────────────────────────────────────────────────────┐   │
│  │                    PLUGIN API                               │   │
│  │                                                             │   │
│  │  ┌─────────────────┐  ┌─────────────────┐                 │   │
│  │  │  Event Hooks    │  │  Service Access  │                 │   │
│  │  │                 │  │                  │                 │   │
│  │  │ on_before_gen   │  │ get_models()     │                 │   │
│  │  │ on_after_gen    │  │ get_settings()   │                 │   │
│  │  │ on_model_load   │  │ save_image()     │                 │   │
│  │  │ on_prompt_proc  │  │ get_gallery()    │                 │   │
│  │  │ on_startup      │  │ log()            │                 │   │
│  │  │ on_shutdown     │  │                  │                 │   │
│  │  └─────────────────┘  └─────────────────┘                 │   │
│  │                                                             │   │
│  │  ┌─────────────────┐  ┌─────────────────┐                 │   │
│  │  │  UI Extension   │  │  Pipeline Ext   │                 │   │
│  │  │                 │  │                  │                 │   │
│  │  │ register_panel  │  │ register_pipe   │                 │   │
│  │  │ register_tab    │  │ register_proc   │                 │   │
│  │  │ register_menu   │  │ register_sched  │                 │   │
│  │  │ register_widget │  │                  │                 │   │
│  │  └─────────────────┘  └─────────────────┘                 │   │
│  └─────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────┘
```

### Plugin Manifest (plugin.json)

```json
{
  "name": "watermark-plugin",
  "version": "1.0.0",
  "displayName": "Watermark",
  "description": "Add watermark to generated images",
  "author": "Plugin Author",
  "license": "MIT",
  "minAppVersion": "0.3.0",
  "entryPoint": "main.py",
  "permissions": [
    "event:generation.completed",
    "service:storage",
    "service:settings"
  ],
  "ui": {
    "settings": "settings.tsx",
    "panel": null
  },
  "dependencies": {
    "pillow": ">=10.0.0"
  }
}
```

### Plugin Lifecycle

```
   Install        Discover        Load           Enable         Disable        Uninstall
   ───────       ─────────       ──────        ────────       ─────────       ──────────
   Copy to       Read manifest   Import module  Register       Unregister     Remove files
   plugins/      Validate deps   Create inst.   event hooks    event hooks    Clean DB
                                 Call init()    Start UI       Stop UI
                                                Call enable()  Call disable()
```

### Plugin Permission System

| Permission | Mô tả | Risk Level |
|---|---|---|
| `event:*` | Listen to events | 🟢 Low |
| `service:settings` | Read/write settings | 🟡 Medium |
| `service:storage` | Read/write files | 🟡 Medium |
| `service:models` | Access model info | 🟢 Low |
| `service:gallery` | Access gallery | 🟢 Low |
| `pipeline:register` | Register custom pipeline | 🔴 High |
| `ui:panel` | Add UI panel | 🟡 Medium |
| `network:http` | Make HTTP requests | 🔴 High |

---

## AI Engine Architecture

### Pipeline Architecture

```
                    ┌─────────────────────┐
                    │   BasePipeline      │ ← Abstract base
                    │   (ABC)             │
                    │                     │
                    │ + generate()        │
                    │ + configure()       │
                    │ + get_default_params│
                    │ + validate_params() │
                    └──────────┬──────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
    ┌─────┴──────┐    ┌───────┴───────┐    ┌───────┴───────┐
    │ Txt2Img    │    │  Img2Img      │    │  Inpaint      │
    │ Pipeline   │    │  Pipeline     │    │  Pipeline     │
    └────────────┘    └───────────────┘    └───────────────┘
                                                  │
                               ┌──────────────────┤
                               │                  │
                        ┌──────┴──────┐    ┌──────┴──────┐
                        │ Outpaint    │    │ ControlNet  │
                        │ Pipeline    │    │ Pipeline    │
                        └─────────────┘    └─────────────┘
```

### Engine Manager

```
┌─────────────────────────────────────────────────────────────┐
│                      ENGINE MANAGER                          │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Pipeline Registry                        │   │
│  │  "txt2img" → Txt2ImgPipeline                         │   │
│  │  "img2img" → Img2ImgPipeline                         │   │
│  │  "inpaint" → InpaintPipeline                         │   │
│  │  "custom"  → PluginPipeline                          │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │   Model Loader   │  │  VRAM Manager    │                 │
│  │                   │  │                  │                 │
│  │ • load_safetensors│  │ • monitor VRAM   │                 │
│  │ • detect_arch    │  │ • smart offload  │                 │
│  │ • apply_lora     │  │ • attention opt  │                 │
│  │ • merge_weights  │  │ • VAE tiling     │                 │
│  └──────────────────┘  └──────────────────┘                 │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │Scheduler Factory │  │  Post-Processor  │                 │
│  │                   │  │                  │                 │
│  │ • create_euler   │  │ • upscale        │                 │
│  │ • create_dpm++   │  │ • face_restore   │                 │
│  │ • create_ddim    │  │ • watermark      │                 │
│  │ • create_custom  │  │ • color_correct  │                 │
│  └──────────────────┘  └──────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

### VRAM Management Strategy (8GB Target)

```
┌─────────────────────────────────────────────────────────┐
│                 VRAM MANAGEMENT STRATEGY                  │
│                                                          │
│  Available VRAM: 8GB                                     │
│  Target Max Usage: 7.5GB (500MB reserved for system)     │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │              Model Loading Strategy              │    │
│  │                                                   │    │
│  │  SD 1.5 (~2GB)    → Full GPU ✅                  │    │
│  │  SDXL (~6.5GB)    → GPU + attention slicing ⚠️   │    │
│  │  SDXL + LoRA      → GPU + offload text enc. ⚠️  │    │
│  │  Flux (~12GB)     → CPU offload + quantize 🔴    │    │
│  │                                                   │    │
│  │  Strategy:                                        │    │
│  │  1. Check model size vs available VRAM            │    │
│  │  2. If fits → load entirely to GPU                │    │
│  │  3. If tight → enable attention slicing           │    │
│  │  4. If exceeded → sequential CPU offloading       │    │
│  │  5. If still exceeded → model CPU offloading      │    │
│  │  6. Last resort → quantization (future)           │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │              Optimization Layers                  │    │
│  │                                                   │    │
│  │  Layer 1: xformers / SDP Attention (always)      │    │
│  │  Layer 2: VAE Slicing (when image > 512x512)     │    │
│  │  Layer 3: VAE Tiling (when image > 1024x1024)    │    │
│  │  Layer 4: Attention Slicing (when VRAM < 6GB)    │    │
│  │  Layer 5: Sequential CPU Offload (when tight)    │    │
│  │  Layer 6: Model CPU Offload (when very tight)    │    │
│  │  Layer 7: torch.compile (when stable)            │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

---

## API Layer

### REST API Design

```
/api/v1/
├── /generate
│   ├── POST   /              → Create new generation (add to queue)
│   ├── GET    /{id}          → Get generation status & result
│   ├── DELETE /{id}          → Cancel generation
│   └── POST   /batch        → Create batch generation
│
├── /models
│   ├── GET    /              → List all available models
│   ├── GET    /{id}          → Get model details
│   ├── POST   /load         → Load model into GPU
│   ├── POST   /unload       → Unload current model
│   ├── GET    /loaded        → Get currently loaded model
│   ├── POST   /scan         → Scan for new models
│   └── DELETE /{id}          → Delete model file
│
├── /queue
│   ├── GET    /              → Get queue status
│   ├── POST   /{id}/cancel  → Cancel queued item
│   ├── POST   /{id}/priority→ Change priority
│   ├── POST   /pause        → Pause queue processing
│   ├── POST   /resume       → Resume queue processing
│   └── DELETE /              → Clear queue
│
├── /gallery
│   ├── GET    /              → List images (paginated)
│   ├── GET    /{id}          → Get image details
│   ├── DELETE /{id}          → Delete image
│   ├── POST   /{id}/favorite→ Toggle favorite
│   ├── POST   /{id}/tags    → Add tags
│   └── GET    /search       → Search images
│
├── /history
│   ├── GET    /              → Get generation history
│   ├── GET    /{id}          → Get history entry details
│   └── POST   /{id}/replay  → Replay generation with same params
│
├── /settings
│   ├── GET    /              → Get all settings
│   ├── PUT    /              → Update settings
│   ├── GET    /{key}         → Get specific setting
│   └── PUT    /{key}         → Update specific setting
│
├── /system
│   ├── GET    /info          → System info (OS, GPU, RAM)
│   ├── GET    /gpu           → GPU details (VRAM, temp, util)
│   ├── GET    /health        → Health check
│   └── GET    /benchmark     → Performance benchmark
│
├── /plugins
│   ├── GET    /              → List installed plugins
│   ├── POST   /install       → Install plugin
│   ├── DELETE /{id}          → Uninstall plugin
│   ├── POST   /{id}/enable   → Enable plugin
│   ├── POST   /{id}/disable  → Disable plugin
│   └── GET    /marketplace   → Browse marketplace
│
└── /downloads
    ├── GET    /              → List active downloads
    ├── POST   /              → Start download
    ├── DELETE /{id}          → Cancel download
    ├── POST   /{id}/pause   → Pause download
    └── POST   /{id}/resume  → Resume download
```

### WebSocket Endpoints

```
/ws/
├── /progress    → Real-time generation progress
│                  Events: step_update, preview_image, completion
│
├── /monitor     → System monitoring
│                  Events: vram_update, gpu_temp, cpu_usage (1s interval)
│
└── /events      → General event stream
                   Events: all EventBus events forwarded to frontend
```

### API Versioning Strategy

- URL-based versioning: `/api/v1/`, `/api/v2/`
- Breaking changes → new version
- Deprecated endpoints → warning header + 6 month sunset
- Non-breaking additions → same version

---

## Frontend Architecture

### State Management Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   FRONTEND STATE                         │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │            CLIENT STATE (Zustand)                │    │
│  │                                                   │    │
│  │  ┌──────────────┐  ┌──────────────┐             │    │
│  │  │  uiStore     │  │generationForm│             │    │
│  │  │              │  │  Store       │             │    │
│  │  │ • sidebar    │  │              │             │    │
│  │  │ • theme      │  │ • prompt     │             │    │
│  │  │ • panelSizes │  │ • params     │             │    │
│  │  │ • activeTab  │  │ • mode       │             │    │
│  │  └──────────────┘  └──────────────┘             │    │
│  │                                                   │    │
│  │  ┌──────────────┐  ┌──────────────┐             │    │
│  │  │ systemStore  │  │ settingsStore│             │    │
│  │  │              │  │              │             │    │
│  │  │ • vram       │  │ • defaults   │             │    │
│  │  │ • gpuTemp    │  │ • paths      │             │    │
│  │  │ • connected  │  │ • hotkeys    │             │    │
│  │  └──────────────┘  └──────────────┘             │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │          SERVER STATE (TanStack Query)            │    │
│  │                                                   │    │
│  │  useModels()      → GET /api/v1/models           │    │
│  │  useQueue()       → GET /api/v1/queue            │    │
│  │  useGallery()     → GET /api/v1/gallery          │    │
│  │  useHistory()     → GET /api/v1/history          │    │
│  │  useSystemInfo()  → GET /api/v1/system/info      │    │
│  │                                                   │    │
│  │  Cache keys:                                      │    │
│  │  ["models"]        → refetch on model change     │    │
│  │  ["queue"]         → refetch on WS event         │    │
│  │  ["gallery", page] → paginated, infinite         │    │
│  │  ["history", page] → paginated                   │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │         REAL-TIME STATE (WebSocket)               │    │
│  │                                                   │    │
│  │  Progress WS → Update systemStore.progress       │    │
│  │  Monitor WS  → Update systemStore.vram/gpu       │    │
│  │  Events WS   → Invalidate TanStack Query cache   │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### Component Architecture

```
App
├── MainLayout
│   ├── Sidebar
│   │   ├── NavLinks
│   │   ├── ModelSelector
│   │   └── SystemMonitor (compact)
│   │
│   ├── Header
│   │   ├── BreadCrumb
│   │   ├── QueueIndicator
│   │   └── Notifications
│   │
│   ├── MainContent (Router)
│   │   ├── GeneratePage
│   │   │   ├── PromptPanel
│   │   │   │   ├── PromptInput (positive)
│   │   │   │   ├── PromptInput (negative)
│   │   │   │   └── PromptActions (enhance, clear, history)
│   │   │   ├── ParameterPanel
│   │   │   │   ├── SamplerSelect
│   │   │   │   ├── StepsSlider
│   │   │   │   ├── CFGSlider
│   │   │   │   ├── SizeSelect
│   │   │   │   ├── SeedControl
│   │   │   │   ├── BatchControl
│   │   │   │   └── AdvancedOptions
│   │   │   ├── ImagePreview
│   │   │   │   ├── GeneratedImage
│   │   │   │   ├── ProgressOverlay
│   │   │   │   └── ImageActions
│   │   │   └── GenerateButton
│   │   │
│   │   ├── GalleryPage
│   │   ├── ModelsPage
│   │   ├── QueuePage
│   │   ├── HistoryPage
│   │   ├── SettingsPage
│   │   ├── PluginsPage
│   │   └── WorkflowPage
│   │
│   └── StatusBar
│       ├── VRAMBar
│       ├── GPUTemperature
│       ├── QueueCount
│       └── ConnectionStatus
│
└── Modals/Overlays
    ├── ImageDetailModal
    ├── ModelInfoModal
    ├── SettingsModal
    └── ErrorModal
```

---

## Dependency Injection

### Backend DI Container

```python
# Conceptual DI setup
class DIContainer:
    """Central dependency injection container"""

    # Core
    event_bus: IEventBus                → InMemoryEventBus
    config: AppConfig                   → PydanticAppConfig

    # Repositories
    generation_repo: IGenerationRepo    → SQLAlchemyGenerationRepo
    model_repo: IModelRepo              → SQLAlchemyModelRepo
    image_repo: IImageRepo              → SQLAlchemyImageRepo
    settings_repo: ISettingsRepo        → SQLAlchemySettingsRepo

    # Infrastructure
    storage: IStorage                   → LocalFileStorage
    queue_manager: IQueueManager        → InMemoryQueueManager
    plugin_manager: IPluginManager      → PluginManager

    # Engine
    ai_engine: IAIEngine                → DiffusersAIEngine
    vram_manager: IVRAMManager          → NvidiaVRAMManager
    model_loader: IModelLoader          → DiffusersModelLoader

    # Services
    generation_service: GenerationService
    model_service: ModelService
    queue_service: QueueService
    gallery_service: GalleryService
    history_service: HistoryService
    settings_service: SettingsService
    plugin_service: PluginService
    system_service: SystemService
```

### FastAPI Dependency Injection Pattern

```python
# Conceptual — FastAPI Depends() pattern
def get_generation_service(
    engine: IAIEngine = Depends(get_ai_engine),
    queue: IQueueManager = Depends(get_queue_manager),
    events: IEventBus = Depends(get_event_bus),
    repo: IGenerationRepository = Depends(get_generation_repo),
    storage: IStorage = Depends(get_storage),
) -> GenerationService:
    return GenerationService(
        engine=engine,
        queue_manager=queue,
        event_bus=events,
        generation_repo=repo,
        image_storage=storage,
    )
```

**Lợi ích:**
- Test dễ dàng (mock interfaces)
- Swap implementations không sửa business logic
- Clear dependency graph
- Avoid circular dependencies

---

## Database Design

### ER Diagram

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│   generations   │       │     models       │       │     images      │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ PK id (UUID)    │       │ PK id (UUID)    │       │ PK id (UUID)    │
│    type          │  ┌──→│    name          │       │ FK generation_id│──→
│    prompt        │  │   │    filename      │       │    filename      │
│    negative_prompt│  │   │    path          │       │    path          │
│ FK model_id ─────┼──┘   │    type          │       │    thumbnail_path│
│    width         │       │    architecture  │       │    width         │
│    height        │       │    size_bytes    │       │    height        │
│    steps         │       │    hash (SHA256) │       │    seed_used     │
│    cfg_scale     │       │    metadata_json │       │    format        │
│    seed          │       │    is_favorite   │       │    size_bytes    │
│    sampler       │       │    tags          │       │    is_favorite   │
│    clip_skip     │       │    created_at    │       │    rating        │
│    status        │       │    last_used_at  │       │    metadata_json │
│    lora_json     │       └─────────────────┘       │    created_at    │
│    controlnet_json│                                 └────────┬────────┘
│    extra_params_json│                                        │
│    error_message │                                           │
│    created_at    │       ┌─────────────────┐       ┌────────┴────────┐
│    started_at    │       │   queue_items   │       │   image_tags    │
│    completed_at  │       ├─────────────────┤       ├─────────────────┤
│    duration_ms   │       │ PK id (UUID)    │       │ FK image_id     │──→
│    metadata_json │       │ FK generation_id│──→    │ FK tag_id       │──→
└─────────────────┘       │    priority      │       └─────────────────┘
                           │    status        │
┌─────────────────┐       │    position      │       ┌─────────────────┐
│    settings     │       │    created_at    │       │      tags       │
├─────────────────┤       │    started_at    │       ├─────────────────┤
│ PK key          │       │    completed_at  │       │ PK id (UUID)    │
│    value         │       │    error_message │       │    name          │
│    type          │       └─────────────────┘       │    color         │
│    category      │                                  │    created_at    │
│    description   │       ┌─────────────────┐       └─────────────────┘
│    updated_at    │       │    plugins      │
└─────────────────┘       ├─────────────────┤       ┌─────────────────┐
                           │ PK id (UUID)    │       │   downloads     │
                           │    name          │       ├─────────────────┤
                           │    version       │       │ PK id (UUID)    │
                           │    display_name  │       │    url           │
                           │    description   │       │    filename      │
                           │    author        │       │    destination   │
                           │    path          │       │    total_bytes   │
                           │    enabled       │       │    downloaded    │
                           │    config_json   │       │    status        │
                           │    permissions   │       │    speed_bps     │
                           │    installed_at  │       │    error_message │
                           │    updated_at    │       │    created_at    │
                           └─────────────────┘       │    completed_at  │
                                                      └─────────────────┘
```

### Migration Strategy

- Alembic cho schema migrations
- Auto-generate migrations từ SQLAlchemy models
- Migration chạy tự động khi app startup
- Backward-compatible migrations (no data loss)
- Rollback support cho mỗi migration

---

## Communication Patterns

### Frontend ↔ Backend Communication

```
1. REST API (CRUD operations)
   Frontend ──HTTP──→ FastAPI Routes ──→ Services ──→ Response

2. WebSocket (Real-time updates)
   Backend ──WS──→ Frontend (push-based)
   
   Channels:
   • progress: Step-by-step generation progress
   • monitor: GPU/VRAM/CPU stats every 1s
   • events: All system events

3. IPC (Electron ↔ Renderer)
   Renderer ──IPC──→ Main Process ──→ File system, native APIs

4. File-based (Large data)
   • Generated images: Served as static files
   • Model files: Direct file system access
   • Thumbnails: Generated and cached on disk
```

### Backend Internal Communication

```
1. Direct call (synchronous, within same layer)
   Route → Service → Repository

2. Event Bus (asynchronous, cross-module)
   Service A ──emit──→ Event Bus ──dispatch──→ Service B, C, D

3. Queue (async processing)
   Service ──enqueue──→ Queue ──dequeue──→ Worker ──→ Service
```

---

## Error Handling Architecture

### Error Hierarchy

```
ImageAgentError (base)
├── ValidationError
│   ├── InvalidPromptError
│   ├── InvalidParameterError
│   └── InvalidModelError
│
├── EngineError
│   ├── ModelLoadError
│   ├── GenerationError
│   ├── VRAMError (OutOfMemoryError)
│   ├── CUDAError
│   └── PipelineError
│
├── StorageError
│   ├── FileNotFoundError
│   ├── DiskFullError
│   └── PermissionError
│
├── DatabaseError
│   ├── ConnectionError
│   ├── QueryError
│   └── MigrationError
│
├── PluginError
│   ├── PluginLoadError
│   ├── PluginExecutionError
│   └── PluginPermissionError
│
├── QueueError
│   ├── QueueFullError
│   └── QueueItemNotFoundError
│
└── DownloadError
    ├── NetworkError
    ├── InvalidURLError
    └── DownloadInterruptedError
```

### Error Handling Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                    ERROR HANDLING FLOW                        │
│                                                              │
│  Exception occurs                                            │
│       │                                                      │
│       ▼                                                      │
│  Caught at Service Layer?                                    │
│       │                                                      │
│       ├── Yes → Log, emit error event, return error result   │
│       │                                                      │
│       └── No → Propagate to API Layer                        │
│                │                                             │
│                ▼                                             │
│           Global Error Handler (Middleware)                   │
│                │                                             │
│                ├── ImageAgentError → Structured error resp.  │
│                │   (400/404/422/500)                         │
│                │                                             │
│                ├── Unhandled Exception → 500 + log + alert   │
│                │                                             │
│                └── All errors → WebSocket notification        │
│                                  to frontend                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Security Considerations

### Local Application Security

| Threat | Mitigation |
|---|---|
| Plugin malicious code | Sandbox, permission system, code review |
| Model file tampering | SHA256 hash verification |
| API unauthorized access | Localhost-only binding, CORS restricted |
| Path traversal | Input sanitization, path validation |
| Memory corruption | Python memory safety, typed inputs |
| DLL injection | Electron security hardening |

### Electron Security Best Practices

1. **Context Isolation**: `contextIsolation: true` — renderer cannot access Node.js
2. **No Node Integration**: `nodeIntegration: false` — use preload scripts only
3. **Content Security Policy**: Restrict script sources
4. **No Remote Module**: Disabled by default in modern Electron
5. **IPC Validation**: Validate all IPC messages in main process
6. **WebSecurity**: Enable web security (same-origin policy)

### API Security

1. **Localhost-only**: Backend binds to `127.0.0.1` only
2. **CORS**: Allow only Electron renderer origin
3. **Input validation**: Pydantic models validate all inputs
4. **File path validation**: Prevent path traversal in file operations
5. **Rate limiting**: Prevent resource exhaustion
6. **Request size limits**: Prevent large payload attacks
