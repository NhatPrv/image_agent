# 🔧 Tech Stack — Image Agent

> Phân tích chi tiết toàn bộ công nghệ sử dụng, lý do lựa chọn và so sánh với các giải pháp thay thế

---

## Mục Lục

- [Tổng Quan](#tổng-quan)
- [Backend](#backend)
- [Frontend](#frontend)
- [AI Engine](#ai-engine)
- [Database](#database)
- [DevOps & Tools](#devops--tools)
- [Tổng Kết Quyết Định](#tổng-kết-quyết-định)

---

## Tổng Quan

### Stack Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     DESKTOP APPLICATION                      │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              FRONTEND (Renderer Process)             │    │
│  │  React 18 + TypeScript 5 + TailwindCSS + shadcn/ui  │    │
│  │  Zustand + TanStack Query + Framer Motion            │    │
│  └────────────────────────┬────────────────────────────┘    │
│                           │ IPC                              │
│  ┌────────────────────────┴────────────────────────────┐    │
│  │              ELECTRON (Main Process)                 │    │
│  │  Window Mgmt + Tray + Auto-Update + Backend Mgmt    │    │
│  └────────────────────────┬────────────────────────────┘    │
│                           │ HTTP / WebSocket                 │
│  ┌────────────────────────┴────────────────────────────┐    │
│  │              BACKEND (Python Process)                │    │
│  │  FastAPI + Pydantic + SQLAlchemy + PyTorch           │    │
│  │  Diffusers + CUDA + Event Bus + Plugin System        │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              DATA LAYER                              │    │
│  │  SQLite + File System (models, outputs, configs)     │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## Backend

### Python 3.11+

**Lý do chọn:**
- Hệ sinh thái AI/ML tốt nhất (PyTorch, HuggingFace, etc.)
- Type hints mature (PEP 484, 604, 612)
- Performance cải thiện đáng kể ở 3.11+ (10-60% faster)
- asyncio mature cho async operations
- Cộng đồng lớn nhất cho AI development

**So sánh:**

| Tiêu chí | Python | Rust | Go | Node.js |
|---|---|---|---|---|
| AI/ML ecosystem | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐ |
| Performance | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| Development speed | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| PyTorch integration | ⭐⭐⭐⭐⭐ | ⭐⭐ (tch) | ❌ | ❌ |
| HuggingFace support | ⭐⭐⭐⭐⭐ | ⭐⭐ | ❌ | ⭐⭐ |
| Type safety | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |

**Kết luận:** Python là lựa chọn duy nhất hợp lý cho AI backend. Không có ngôn ngữ nào khác có ecosystem AI/ML sánh được. Rust có thể dùng cho performance-critical modules trong tương lai (qua PyO3).

**Version 3.11+ vì:**
- Exception groups (PEP 654) — tốt cho concurrent error handling
- TaskGroup trong asyncio — quản lý concurrent tasks tốt hơn
- Significant performance improvements
- tomllib built-in
- 3.12+ có thể cân nhắc khi stable hơn

---

### FastAPI

**Lý do chọn:**
- Async-native — phù hợp cho concurrent generation requests
- Auto-generate OpenAPI docs — API documentation tự động
- Pydantic integration — data validation tự động
- WebSocket support — real-time progress updates
- Dependency injection built-in — clean architecture
- Performance tốt nhất trong Python web frameworks
- Modern, actively maintained

**So sánh:**

| Tiêu chí | FastAPI | Flask | Django | Litestar |
|---|---|---|---|---|
| Async native | ✅ | ❌ (ext) | ⚠️ (ASGI) | ✅ |
| Auto API docs | ✅ OpenAPI | ❌ | ❌ | ✅ |
| Pydantic | ✅ Built-in | ❌ | ❌ | ✅ |
| WebSocket | ✅ | ❌ | ⚠️ Channels | ✅ |
| DI built-in | ✅ Depends() | ❌ | ❌ | ✅ |
| Performance | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Community | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Learning curve | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |

**Litestar là alternative tốt** (performance tương đương, kiến trúc sạch hơn), nhưng FastAPI thắng về:
- Community size lớn hơn nhiều
- Nhiều tutorials, StackOverflow answers hơn
- Ecosystem plugins phong phú hơn
- Adoption rộng rãi hơn trong AI projects

**Flask/Django bị loại vì:**
- Flask: Synchronous, thiếu type safety, thiếu WebSocket native
- Django: Quá nặng cho use case này (ORM riêng, admin panel không cần)

---

### Pydantic v2

**Lý do chọn:**
- Data validation mạnh mẽ với type hints
- Settings management (BaseSettings)
- JSON serialization/deserialization nhanh (Rust core ở v2)
- Tích hợp hoàn hảo với FastAPI
- Schema generation cho API documentation

**Vai trò cụ thể:**
1. **Request/Response DTOs**: Validate API input/output
2. **Configuration**: App settings, GPU config, model config
3. **Domain Entities**: Validate business objects
4. **Event Payloads**: Typed event data

**Tại sao v2:**
- 5-50x nhanh hơn v1 (Rust core)
- Strict mode mặc định (an toàn hơn)
- Model validators cải thiện
- Better error messages

---

### SQLAlchemy 2.x + SQLite

**Lý do chọn SQLAlchemy:**
- ORM mature nhất của Python
- Hỗ trợ cả ORM và Core (raw SQL)
- Database-agnostic — dễ migrate sang PostgreSQL sau này
- Relationship management
- Migration support qua Alembic
- Async support (2.x)

**Lý do chọn SQLite:**
- Zero-config, embedded — phù hợp desktop app
- Không cần cài đặt thêm
- Single file database — dễ backup
- Đủ nhanh cho use case (single user)
- WAL mode cho concurrent reads

**So sánh Database:**

| Tiêu chí | SQLite | PostgreSQL | MongoDB | LevelDB |
|---|---|---|---|---|
| Setup complexity | ⭐⭐⭐⭐⭐ Zero | ⭐⭐ Install | ⭐⭐ Install | ⭐⭐⭐⭐ |
| Desktop app fit | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| Concurrent writes | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| Query flexibility | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| Backup/portability | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| Offline support | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

**Migration path**: SQLAlchemy abstraction cho phép migrate sang PostgreSQL nếu cần (khi có multi-user hoặc data lớn) mà không cần viết lại application code.

**Alembic** cho database migrations — đảm bảo schema evolution khi update ứng dụng.

---

## Frontend

### Electron

**Lý do chọn:**
- Cross-platform desktop app từ web technologies
- Access native APIs (file system, GPU info, process management)
- Quản lý Python backend process
- System tray, notifications, auto-update
- Mature ecosystem, battle-tested (VS Code, Discord, Slack)

**So sánh:**

| Tiêu chí | Electron | Tauri | Flutter Desktop | Qt (PySide) |
|---|---|---|---|---|
| Bundle size | ⭐⭐ (~150MB) | ⭐⭐⭐⭐⭐ (~5MB) | ⭐⭐⭐ (~30MB) | ⭐⭐⭐ (~50MB) |
| Performance | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Web tech | ✅ Full | ✅ Full | ❌ Dart | ❌ Python/C++ |
| React ecosystem | ✅ Full | ✅ Full | ❌ | ❌ |
| Native access | ✅ Node.js | ✅ Rust | ⚠️ FFI | ✅ C++ |
| Community | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Maturity | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| Auto-update | ✅ Built-in | ✅ Built-in | ⚠️ Manual | ⚠️ Manual |
| DevTools | ✅ Chrome | ⚠️ Limited | ⚠️ | ⚠️ |

**Tại sao không chọn Tauri:**
- Tauri v2 mới ra, ecosystem chưa mature bằng
- Debugging khó hơn (không có Chrome DevTools đầy đủ)
- Viết backend logic bằng Rust thay vì Node.js — learning curve
- IPC patterns khác biệt, ít resources
- **Nhưng**: Tauri là candidate tốt cho tương lai nếu cần giảm bundle size

**Tại sao không chọn Web-only (như ComfyUI):**
- Không quản lý được Python backend process
- Không có native file system access
- Không có system tray, notifications
- User phải mở terminal + browser riêng

---

### React 18

**Lý do chọn:**
- UI library phổ biến nhất — dễ recruit/tìm tài liệu
- Concurrent features (React 18) — smooth UI khi heavy operations
- Hooks pattern — composable, testable logic
- Virtual DOM — efficient updates
- Huge ecosystem (shadcn/ui, Framer Motion, etc.)

**So sánh:**

| Tiêu chí | React | Vue 3 | Svelte 5 | Solid |
|---|---|---|---|---|
| Ecosystem | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| Component library | ⭐⭐⭐⭐⭐ (shadcn) | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| Performance | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Learning curve | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| TypeScript | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Electron compat | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| Animation libs | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |

**Svelte/Solid có performance tốt hơn**, nhưng React thắng ở ecosystem và component libraries — quan trọng cho productivity.

---

### TypeScript 5

**Lý do chọn:**
- Type safety — bắt lỗi tại compile time
- Better IDE support (IntelliSense, refactoring)
- Self-documenting code
- Easier maintenance và collaboration
- Industry standard cho React projects

**Không có alternative hợp lý** — JavaScript thuần thiếu type safety, không phù hợp cho dự án lớn.

---

### TailwindCSS 3

**Lý do chọn:**
- Utility-first — nhanh, consistent
- Purge unused CSS — bundle size nhỏ
- Responsive design dễ dàng
- Dark mode built-in
- Tương thích hoàn hảo với shadcn/ui
- Customizable design system

**So sánh:**

| Tiêu chí | TailwindCSS | CSS Modules | Styled Components | Vanilla CSS |
|---|---|---|---|---|
| Development speed | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| Consistency | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| Bundle size | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| shadcn/ui compat | ✅ Required | ❌ | ❌ | ❌ |
| Learning curve | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

### shadcn/ui

**Lý do chọn:**
- Copy-paste components — full ownership, customizable
- Radix UI primitives — accessible, composable
- TailwindCSS styling — consistent với design system
- Không phải npm dependency — không phiên bản lock
- High quality, professional look
- Active community

**So sánh:**

| Tiêu chí | shadcn/ui | Ant Design | MUI | Chakra UI |
|---|---|---|---|---|
| Customizability | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Bundle size | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| Accessibility | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Design quality | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| TailwindCSS | ✅ Native | ❌ CSS-in-JS | ❌ Emotion | ❌ Emotion |
| Ownership | ✅ Your code | ❌ npm dep | ❌ npm dep | ❌ npm dep |

**Ant Design/MUI bị loại vì**: Quá nặng (bundle size), opinionated styling khó customize, CSS-in-JS conflict với TailwindCSS.

---

### Zustand

**Lý do chọn:**
- Minimal API — ít boilerplate
- TypeScript-first
- No providers needed (unlike Redux, Jotai)
- Middleware support (persist, devtools, immer)
- Performance tốt — selective subscriptions
- Nhỏ gọn (~1KB)

**So sánh:**

| Tiêu chí | Zustand | Redux Toolkit | Jotai | Recoil | MobX |
|---|---|---|---|---|---|
| Boilerplate | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Learning curve | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| Performance | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| DevTools | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| Bundle size | ⭐⭐⭐⭐⭐ (1KB) | ⭐⭐⭐ (12KB) | ⭐⭐⭐⭐⭐ (3KB) | ⭐⭐⭐ (20KB) | ⭐⭐⭐ (15KB) |
| Middleware | ✅ | ✅ | ⚠️ | ⚠️ | ✅ |

**Zustand cho client state, TanStack Query cho server state** — sự phân tách này tránh duplicating server data trong client store.

---

### TanStack Query (React Query) v5

**Lý do chọn:**
- Server state management — caching, refetching, invalidation
- Tránh duplicating API data trong Zustand
- Automatic background refetching
- Optimistic updates
- Request deduplication
- Retry logic built-in
- DevTools

**Vai trò:**
- Fetch model list → cache → auto refetch khi invalidate
- Fetch generation history → paginated, cached
- Fetch gallery images → infinite query
- Fetch system info → polling interval

**Tại sao cần cả Zustand + TanStack Query:**
- **Zustand**: Client-only state (UI preferences, form state, sidebar state)
- **TanStack Query**: Server state (models, gallery, history, system info)
- Separation of concerns — mỗi tool làm đúng việc của nó

---

### Framer Motion

**Lý do chọn:**
- API đơn giản — `<motion.div animate={{ opacity: 1 }}>`
- Layout animations — smooth khi elements resize/reorder
- Gesture support — drag, swipe
- AnimatePresence — exit animations
- Performance tốt — hardware-accelerated
- React-specific — tích hợp tự nhiên

**So sánh:**

| Tiêu chí | Framer Motion | React Spring | GSAP | CSS Animations |
|---|---|---|---|---|
| Ease of use | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Layout animation | ✅ | ❌ | ⚠️ | ❌ |
| Exit animation | ✅ | ⚠️ | ✅ | ❌ |
| Gesture support | ✅ | ❌ | ✅ | ❌ |
| Bundle size | ⭐⭐⭐ (32KB) | ⭐⭐⭐⭐ (15KB) | ⭐⭐⭐ (30KB) | ⭐⭐⭐⭐⭐ (0) |
| React integration | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |

---

## AI Engine

### PyTorch 2.x

**Lý do chọn:**
- Framework deep learning được sử dụng nhiều nhất cho research & production
- CUDA support tốt nhất
- Dynamic graph — debug dễ
- torch.compile (2.x) — JIT compilation cho performance
- Ecosystem: Diffusers, Transformers, xformers, etc.
- Cộng đồng lớn nhất

**So sánh:**

| Tiêu chí | PyTorch 2.x | TensorFlow | JAX | ONNX Runtime |
|---|---|---|---|---|
| Ecosystem AI Gen | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| Ease of use | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| Dynamic graph | ✅ | ⚠️ Eager mode | ⚠️ | N/A |
| Diffusers support | ✅ Native | ⚠️ | ⚠️ (Flax) | ✅ (convert) |
| Windows support | ✅ | ✅ | ⚠️ | ✅ |
| Model availability | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |

**ONNX Runtime** sẽ được thêm trong Phase 4 như alternative inference backend — có thể nhanh hơn PyTorch cho inference trên một số models.

---

### HuggingFace Diffusers

**Lý do chọn:**
- Thư viện chính thức cho diffusion models
- Hỗ trợ tất cả model architectures (SD, SDXL, Flux, SD3)
- Pipeline abstraction — dễ sử dụng
- Scheduler library — Euler, DPM++, DDIM, etc.
- Model loading — safetensors, ckpt
- LoRA support built-in
- ControlNet support built-in
- Optimization: attention slicing, VAE tiling, model offloading
- Actively maintained bởi HuggingFace team

**So sánh:**

| Tiêu chí | Diffusers | ComfyUI nodes | Custom PyTorch | k-diffusion |
|---|---|---|---|---|
| API cleanliness | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| Model support | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| Documentation | ⭐⭐⭐⭐⭐ | ⭐⭐ | N/A | ⭐⭐⭐ |
| Maintenance | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Manual | ⭐⭐⭐ |
| Optimization | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Manual | ⭐⭐⭐ |
| Flexibility | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

**Diffusers có flexibility ít hơn ComfyUI's custom approach**, nhưng:
- API sạch hơn nhiều
- Documentation tốt hơn
- Maintenance bởi professional team
- Khi cần flexibility hơn, có thể extend pipeline hoặc sử dụng low-level API

---

### CUDA + cuDNN

**Lý do chọn:**
- NVIDIA GPU acceleration — bắt buộc cho AI generation
- PyTorch tối ưu cho CUDA
- cuDNN cho deep learning primitives (convolution, attention)
- Hỗ trợ tốt nhất trên Windows

**Version target:**
- CUDA 12.1+ (PyTorch 2.x official support)
- cuDNN 8.9+ (performance improvements)

**Tương lai:**
- ROCm (AMD GPU) — khi có nhu cầu
- MPS (Apple Silicon) — khi port sang macOS
- DirectML — alternative cho Windows
- Vulkan — cross-platform compute

---

### Additional AI Libraries

| Library | Vai trò | Phase |
|---|---|---|
| **xformers** | Memory-efficient attention | Phase 1 |
| **transformers** | Text encoder, tokenizer | Phase 1 |
| **safetensors** | Safe model file loading | Phase 1 |
| **accelerate** | Mixed precision, model offloading | Phase 1 |
| **compel** | Prompt weighting, blending | Phase 2 |
| **controlnet-aux** | ControlNet preprocessors | Phase 2 |
| **GFPGAN** | Face restoration | Phase 3 |
| **CodeFormer** | Face restoration (alternative) | Phase 3 |
| **Real-ESRGAN** | Image upscaling | Phase 3 |
| **onnxruntime-gpu** | ONNX inference | Phase 4 |
| **pynvml** | NVIDIA GPU monitoring | Phase 1 |

---

## Database

### SQLite + SQLAlchemy + Alembic

**Database Schema (High-level):**

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  generations │    │    models     │    │    images     │
├──────────────┤    ├──────────────┤    ├──────────────┤
│ id           │    │ id           │    │ id           │
│ type         │    │ name         │    │ generation_id│──→ generations
│ prompt       │    │ path         │    │ path         │
│ neg_prompt   │    │ type         │    │ thumbnail    │
│ model_id     │──→ │ architecture │    │ width        │
│ width        │    │ size_bytes   │    │ height       │
│ height       │    │ hash         │    │ seed         │
│ steps        │    │ metadata     │    │ created_at   │
│ cfg_scale    │    │ created_at   │    └──────────────┘
│ seed         │    └──────────────┘
│ sampler      │    ┌──────────────┐    ┌──────────────┐
│ status       │    │  queue_items │    │   settings   │
│ created_at   │    ├──────────────┤    ├──────────────┤
│ completed_at │    │ id           │    │ key          │
│ duration_ms  │    │ generation_id│──→ │ value        │
│ metadata     │    │ priority     │    │ type         │
└──────────────┘    │ status       │    │ updated_at   │
                    │ created_at   │    └──────────────┘
┌──────────────┐    │ started_at   │
│   plugins    │    │ completed_at │    ┌──────────────┐
├──────────────┤    └──────────────┘    │    tags       │
│ id           │                        ├──────────────┤
│ name         │    ┌──────────────┐    │ id           │
│ version      │    │ image_tags   │    │ name         │
│ path         │    ├──────────────┤    │ color        │
│ enabled      │    │ image_id     │──→ │ created_at   │
│ config       │    │ tag_id       │──→ └──────────────┘
│ installed_at │    └──────────────┘
└──────────────┘
```

---

## DevOps & Tools

### Linting & Formatting

| Tool | Ngôn ngữ | Vai trò |
|---|---|---|
| **Ruff** | Python | Linter + Formatter (thay thế flake8, isort, black) |
| **ESLint** | TypeScript | Linter |
| **Prettier** | TypeScript/CSS | Formatter |

**Tại sao Ruff thay vì Black + flake8 + isort:**
- Ruff = All-in-one (linting + formatting)
- 10-100x nhanh hơn (viết bằng Rust)
- Cấu hình đơn giản hơn
- Active development

### Testing

| Tool | Vai trò | Ngôn ngữ |
|---|---|---|
| **Pytest** | Unit & integration tests | Python |
| **pytest-asyncio** | Async test support | Python |
| **pytest-cov** | Coverage reporting | Python |
| **httpx** | Async HTTP test client | Python |
| **Vitest** | Unit tests | TypeScript |
| **React Testing Library** | Component tests | TypeScript |
| **Playwright** | E2E tests | TypeScript |

### Build & Package

| Tool | Vai trò |
|---|---|
| **Vite** | Frontend build tool |
| **electron-builder** | Electron packaging |
| **PyInstaller** | Python bundling (optional) |
| **electron-vite** | Unified Electron + Vite setup |

**electron-vite** là cầu nối giữa Electron và Vite, cung cấp:
- Hot Module Replacement cho renderer process
- Main process rebuild on change
- Preload script support
- Unified configuration

---

## Tổng Kết Quyết Định

### Bảng Tổng Hợp

| Category | Chosen | Runner-up | Reason for choice |
|---|---|---|---|
| **Language (BE)** | Python 3.11+ | — | AI/ML ecosystem, PyTorch |
| **Web Framework** | FastAPI | Litestar | Community, ecosystem |
| **Validation** | Pydantic v2 | — | FastAPI integration, performance |
| **ORM** | SQLAlchemy 2.x | — | Maturity, migration path |
| **Database** | SQLite | PostgreSQL | Desktop app, zero-config |
| **AI Framework** | PyTorch 2.x | — | Industry standard for AI |
| **Diffusion Library** | Diffusers | Custom | API quality, maintenance |
| **Desktop Shell** | Electron | Tauri | Maturity, ecosystem |
| **UI Library** | React 18 | Vue 3 | Ecosystem, shadcn/ui |
| **Language (FE)** | TypeScript 5 | — | Type safety, standard |
| **CSS Framework** | TailwindCSS 3 | CSS Modules | Speed, shadcn/ui compat |
| **UI Components** | shadcn/ui | Radix UI | Customizable, TailwindCSS |
| **State (Client)** | Zustand | Jotai | Simplicity, middleware |
| **State (Server)** | TanStack Query | SWR | Features, devtools |
| **Animation** | Framer Motion | React Spring | API, layout animations |
| **Python Linting** | Ruff | Black+flake8 | All-in-one, speed |
| **Testing (BE)** | Pytest | — | Standard |
| **Testing (FE)** | Vitest | Jest | Vite compat, speed |
| **E2E Testing** | Playwright | Cypress | Modern, fast |
| **Build (FE)** | Vite | Webpack | Speed, DX |

### Chưa Quyết Định (Tương Lai)

| Decision | Options | When |
|---|---|---|
| ONNX vs TensorRT | ONNX Runtime, TensorRT, cả hai | Phase 4 |
| GGUF support | llama.cpp, ctransformers | Phase 5 |
| Tauri migration | Stay Electron vs Migrate to Tauri | Phase 5+ |
| Cloud sync | Firebase, Supabase, Custom | Phase 5+ |
| macOS backend | MPS, CoreML | Phase 5+ |
