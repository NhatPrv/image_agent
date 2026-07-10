# 📋 Project Summary — Image Agent

> Tài liệu tổng quan chi tiết về dự án Image Agent

---

## 1. Mô Tả Dự Án

**Image Agent** là một ứng dụng desktop tạo ảnh bằng AI chạy hoàn toàn local trên Windows. Ứng dụng được xây dựng từ đầu với kiến trúc hiện đại, hướng tới việc trở thành nền tảng AI Image Generation toàn diện — không chỉ đơn thuần là giao diện cho Stable Diffusion.

### Tóm Tắt

| Thuộc tính | Chi tiết |
|---|---|
| **Tên dự án** | Image Agent |
| **Loại** | Desktop Application |
| **Nền tảng** | Windows 11 |
| **Backend** | Python (FastAPI + PyTorch + Diffusers) |
| **Frontend** | Electron (React + TypeScript) |
| **Chế độ** | Offline-first, Local-only |
| **License** | MIT |
| **Trạng thái** | Đang phát triển |

### Mô Tả Chi Tiết

Image Agent giải quyết các vấn đề mà các giải pháp hiện tại gặp phải:

1. **Giao diện phức tạp**: ComfyUI mạnh mẽ nhưng giao diện node-based khó tiếp cận cho người mới. SD WebUI sử dụng Gradio với UX hạn chế. Image Agent cung cấp giao diện desktop native đẹp, trực quan, với dark mode và animation mượt mà.

2. **Kiến trúc monolithic**: Hầu hết các giải pháp hiện tại có kiến trúc monolithic, khó mở rộng và bảo trì. Image Agent sử dụng Clean Architecture + Modular Architecture, cho phép mở rộng qua plugin system mà không cần sửa core.

3. **Quản lý tài nguyên kém**: Nhiều ứng dụng không tối ưu VRAM, dẫn đến crash hoặc out-of-memory. Image Agent có VRAM Manager thông minh, tự động quản lý model loading/offloading.

4. **Thiếu tính chuyên nghiệp**: Queue system, batch processing, workflow builder — những tính năng cần thiết cho production workflow — thường thiếu hoặc sơ sài. Image Agent xây dựng chúng như first-class features.

---

## 2. Ý Tưởng

### Triết Lý Thiết Kế

```
"Sức mạnh của ComfyUI, sự đơn giản của Fooocus,
 giao diện của một ứng dụng desktop chuyên nghiệp"
```

Image Agent được sinh ra từ quan sát rằng:

- **Người dùng mới** muốn tạo ảnh AI đẹp mà không cần hiểu kỹ thuật → Cần giao diện đơn giản như Fooocus
- **Người dùng nâng cao** muốn kiểm soát chi tiết mọi parameter → Cần sức mạnh như ComfyUI
- **Professional** muốn batch processing, workflow, queue → Cần tính năng production-grade
- **Developer** muốn mở rộng tính năng → Cần plugin system và API

Image Agent phục vụ TẤT CẢ nhóm người dùng này qua:

- **Simple Mode**: Chỉ cần nhập prompt → Generate. Tất cả parameters được tối ưu tự động.
- **Advanced Mode**: Toàn quyền kiểm soát sampler, scheduler, CFG, steps, seed, etc.
- **Workflow Mode**: Visual workflow builder cho pipeline phức tạp.
- **Developer Mode**: Extension API, Plugin SDK, CLI.

### Nguồn Cảm Hứng

| Ứng dụng | Điều học được |
|---|---|
| **ComfyUI** | Node-based workflow, tính mở rộng, cộng đồng plugins |
| **Fooocus** | Sự đơn giản, auto-optimization, UX tối giản |
| **InvokeAI** | Canvas editing, unified pipeline, queue system |
| **SwarmUI** | Performance monitoring, parameter management |
| **Midjourney** | Chất lượng output, prompt understanding |
| **Adobe Firefly** | Professional UI/UX, workflow integration |

---

## 3. Đối Tượng Sử Dụng

### 3.1 AI Art Enthusiast (Người yêu thích AI Art)

**Profile**: Người muốn tạo ảnh AI đẹp cho mục đích cá nhân, social media, hoặc sáng tạo.

**Nhu cầu**:
- Giao diện dễ dùng, không cần kiến thức kỹ thuật
- Chất lượng ảnh cao ngay từ đầu
- Prompt gợi ý hoặc tự động cải thiện
- Gallery để quản lý ảnh đã tạo

**Image Agent đáp ứng**: Simple Mode + Prompt Enhancer + Gallery

### 3.2 Digital Artist (Họa sĩ số)

**Profile**: Người sử dụng AI như công cụ hỗ trợ sáng tạo chuyên nghiệp.

**Nhu cầu**:
- Kiểm soát chi tiết parameters
- Inpainting/Outpainting cho chỉnh sửa
- ControlNet cho kiểm soát bố cục
- LoRA cho phong cách riêng
- Batch generate cho nhiều biến thể

**Image Agent đáp ứng**: Advanced Mode + Full feature set

### 3.3 Content Creator

**Profile**: Người tạo nội dung cần sản xuất ảnh số lượng lớn, nhanh chóng.

**Nhu cầu**:
- Batch processing
- Queue system
- Workflow automation
- Consistent output quality

**Image Agent đáp ứng**: Batch Generate + Queue + Workflow

### 3.4 AI/ML Developer

**Profile**: Developer muốn xây dựng ứng dụng AI hoặc nghiên cứu.

**Nhu cầu**:
- API access
- Plugin development
- Custom pipeline
- Model experimentation

**Image Agent đáp ứng**: Extension API + Plugin SDK + Developer Mode

### 3.5 Researcher

**Profile**: Nhà nghiên cứu AI cần công cụ thí nghiệm nhanh.

**Nhu cầu**:
- Thay đổi model, sampler nhanh
- So sánh kết quả
- Performance benchmarking
- Logging chi tiết

**Image Agent đáp ứng**: Advanced Mode + Performance Monitor + History comparison

---

## 4. Mục Tiêu

### 4.1 Mục Tiêu Kỹ Thuật

| # | Mục tiêu | Metrics |
|---|---|---|
| T1 | Tạo ảnh 512x512 (SD 1.5) trong < 10 giây trên RTX 4060 8GB | Benchmark |
| T2 | Tạo ảnh 1024x1024 (SDXL) trong < 30 giây trên RTX 4060 8GB | Benchmark |
| T3 | VRAM usage không vượt quá 7.5GB khi generate | Monitor |
| T4 | Startup time < 5 giây (không tính model loading) | Timer |
| T5 | Model switching < 15 giây | Timer |
| T6 | UI phản hồi dưới 16ms (60fps) khi không generate | Profile |
| T7 | Không memory leak sau 100+ generations liên tục | Monitor |
| T8 | Crash recovery — khôi phục queue sau restart | Test |
| T9 | Plugin isolation — plugin lỗi không crash app | Sandbox |
| T10 | API response time < 100ms cho non-generation endpoints | Benchmark |

### 4.2 Mục Tiêu Sản Phẩm

| # | Mục tiêu | Timeline |
|---|---|---|
| P1 | Release v0.1 (Text2Img + Img2Img + Basic UI) | Phase 1 |
| P2 | Release v0.2 (Inpainting + ControlNet + LoRA) | Phase 2 |
| P3 | Release v0.3 (Plugin System + Workflow) | Phase 3 |
| P4 | Release v0.5 (Multi-model + Marketplace) | Phase 4 |
| P5 | Release v1.0 (Production-ready platform) | Phase 5 |

### 4.3 Mục Tiêu Chất Lượng

- **Code Coverage**: >= 80% cho core modules
- **Documentation**: 100% public API documented
- **Performance**: Đạt benchmark targets trên development hardware
- **Stability**: < 1 crash per 1000 generations
- **Maintainability**: Cyclomatic complexity < 15 cho mọi function

---

## 5. Điểm Nổi Bật

### 5.1 🧠 AI Engine Thông Minh

- **Smart VRAM Management**: Tự động quản lý loading/offloading model dựa trên VRAM availability
- **Adaptive Quality**: Tự động điều chỉnh parameters dựa trên hardware capability
- **Pipeline Optimization**: Xformers, Flash Attention, model CPU offloading khi cần
- **Multi-Model Support**: Kiến trúc abstraction cho phép hỗ trợ nhiều model families (SD, SDXL, Flux, SD3)

### 5.2 🎨 Giao Diện Desktop Native

- **Electron + React**: Giao diện đẹp, mượt mà, responsive
- **Dark Mode First**: Thiết kế tối ưu cho dark mode với accent colors
- **Micro-animations**: Framer Motion cho transitions và feedback mượt mà
- **Keyboard-driven**: Đầy đủ keyboard shortcuts cho power users
- **Multi-panel Layout**: Drag-to-resize panels, customizable layout

### 5.3 ⚡ Production-Grade Features

- **Priority Queue**: Hàng đợi với mức ưu tiên, pause/resume, cancel
- **Batch Processing**: Tạo hàng loạt ảnh với parameter variations
- **History**: Đầy đủ lịch sử với metadata, reproducible (cùng seed + params = cùng kết quả)
- **Crash Recovery**: Queue state persisted, tự khôi phục sau restart

### 5.4 🔌 Plugin Ecosystem

- **Extension API**: Documented API cho plugin developers
- **Plugin SDK**: Bộ công cụ phát triển plugin
- **Sandboxed Execution**: Plugin chạy trong sandbox, không ảnh hưởng core
- **Marketplace**: Cửa hàng plugin trong ứng dụng
- **Hot Reload**: Tải/gỡ plugin không cần restart app

### 5.5 📊 Real-time Monitoring

- **VRAM Monitor**: Hiển thị VRAM usage real-time
- **GPU Monitor**: Temperature, utilization, clock speed
- **Performance Panel**: Generation time, throughput, queue stats
- **System Health**: CPU, RAM, disk usage

---

## 6. Công Nghệ Sử Dụng

### Backend Stack

| Công nghệ | Version | Vai trò |
|---|---|---|
| **Python** | 3.11+ | Runtime chính |
| **FastAPI** | 0.110+ | Web framework, API server |
| **Pydantic** | 2.x | Data validation, settings |
| **SQLAlchemy** | 2.x | ORM, database abstraction |
| **SQLite** | 3.x | Embedded database |
| **Alembic** | 1.x | Database migrations |
| **PyTorch** | 2.x | Deep learning framework |
| **Diffusers** | 0.30+ | Diffusion model library |
| **Transformers** | 4.x | Tokenizer, text encoder |
| **Safetensors** | 0.4+ | Model file format |
| **Pillow** | 10+ | Image processing |
| **aiofiles** | 23+ | Async file I/O |
| **uvicorn** | 0.27+ | ASGI server |
| **python-multipart** | 0.0.6+ | File upload handling |
| **pynvml** | 11+ | NVIDIA GPU monitoring |

### Frontend Stack

| Công nghệ | Version | Vai trò |
|---|---|---|
| **Electron** | 30+ | Desktop app shell |
| **React** | 18+ | UI library |
| **TypeScript** | 5.x | Type-safe JavaScript |
| **Vite** | 5.x | Build tool, dev server |
| **TailwindCSS** | 3.x | Utility-first CSS |
| **shadcn/ui** | Latest | UI component library |
| **Zustand** | 4.x | State management |
| **TanStack Query** | 5.x | Server state, caching |
| **Framer Motion** | 11+ | Animation library |
| **React Router** | 6.x | Client-side routing |
| **Lucide React** | Latest | Icon library |
| **React Resizable Panels** | Latest | Resizable layout |

### DevOps & Tools

| Công nghệ | Vai trò |
|---|---|
| **Git** | Version control |
| **ESLint** | JavaScript/TypeScript linting |
| **Prettier** | Code formatting |
| **Ruff** | Python linting + formatting |
| **Pytest** | Python testing |
| **Vitest** | Frontend testing |
| **Playwright** | E2E testing |
| **electron-builder** | App packaging |
| **GitHub Actions** | CI/CD |

> 📖 Phân tích chi tiết: Xem [TECH_STACK.md](./TECH_STACK.md)

---

## 7. Định Hướng Tương Lai

### 7.1 Mở Rộng Model Support

```
Hiện tại              Ngắn hạn              Trung hạn              Dài hạn
─────────            ──────────            ──────────            ──────────
SD 1.5               SDXL                  Flux                  Custom models
                     SD 2.x                SD3                   ONNX Runtime
                                           Pony                  GGUF
                                           Illustrious           TensorRT
```

### 7.2 Mở Rộng Chức Năng

```
Phase 1-2             Phase 3-4             Phase 5+
──────────           ──────────            ──────────
Image Gen             Workflow              Video Gen
Basic Edit            Plugin System         3D Gen
Model Mgmt            Marketplace           AI Agent
                      Prompt Enhance        Local LLM
                      Upscale/Restore       Multi-GPU
```

### 7.3 Mở Rộng Nền Tảng (Tương Lai Xa)

- **macOS**: Apple Silicon (M1/M2/M3) với MPS backend
- **Linux**: Ubuntu/Fedora với CUDA
- **Web**: Cloud-based version (optional, premium)
- **Mobile**: Companion app xem gallery, remote control

### 7.4 Tích Hợp AI Agent

Tầm nhìn dài hạn là biến Image Agent thành AI Creation Assistant:

1. **Local LLM Integration**: Chạy LLM nhỏ (7B params) locally để:
   - Prompt enhancement: Cải thiện prompt tự động
   - Prompt translation: Viết prompt bằng tiếng Việt → tự động dịch
   - Style suggestion: Gợi ý phong cách dựa trên mô tả

2. **AI Workflow Agent**: Agent tự động:
   - Phân tích ảnh output và đề xuất cải thiện
   - Tự động chọn model/LoRA phù hợp
   - Tạo variations dựa trên feedback

3. **Multi-Modal Pipeline**: Kết hợp:
   - Text → Image → Video pipeline
   - Image → 3D model pipeline
   - Sketch → Refined Image pipeline

---

## 8. Khả Năng Mở Rộng

### 8.1 Kiến Trúc Mở Rộng

Image Agent được thiết kế với khả năng mở rộng ở nhiều cấp độ:

```
Level 1: Configuration
  └── Settings, themes, keybindings
  └── Không cần viết code

Level 2: Plugin
  └── Extension API, custom nodes
  └── JavaScript/Python plugins

Level 3: Pipeline
  └── Custom AI pipelines
  └── New model architectures

Level 4: Platform
  └── New generation modalities (video, 3D)
  └── Yêu cầu core changes
```

### 8.2 Plugin Architecture

```
┌─────────────────────────────────────┐
│           Plugin Manager            │
│  ┌──────────┬──────────┬─────────┐  │
│  │ Discover │  Load    │ Sandbox │  │
│  └──────────┴──────────┴─────────┘  │
└──────────────┬──────────────────────┘
               │
    ┌──────────┴──────────┐
    │    Plugin API        │
    │  ┌────────────────┐  │
    │  │ Hooks           │  │  → Lifecycle events
    │  │ Services        │  │  → Access app services
    │  │ UI Components   │  │  → Custom UI elements
    │  │ Pipelines       │  │  → Custom AI pipelines
    │  │ Processors      │  │  → Custom processors
    │  └────────────────┘  │
    └──────────────────────┘
```

### 8.3 Event-Driven Scaling

Mọi giao tiếp giữa modules qua Event Bus:

```
Module A ──event──→ Event Bus ──dispatch──→ Module B
                                       ──→ Module C
                                       ──→ Plugin X
```

Điều này cho phép:
- Thêm module mới mà không sửa module cũ
- Plugin listen to events mà không cần core modification
- Async processing tự nhiên
- Easy testing qua mock events

### 8.4 Database Scaling Strategy

```
Phase 1-3: SQLite (đơn giản, embedded, zero-config)
     │
     │  Nếu cần (1M+ records, concurrent writes):
     ▼
Phase 4+: PostgreSQL (optional migration path)
```

SQLAlchemy abstraction layer đảm bảo việc chuyển đổi database engine minh bạch với application code.

### 8.5 Performance Scaling

| Optimization | Khi nào | Cách thức |
|---|---|---|
| Model CPU Offload | VRAM < model size | Offload layers sang RAM |
| Attention Slicing | VRAM thấp | Giảm VRAM peak bằng sequential attention |
| VAE Tiling | Ảnh lớn | Xử lý VAE theo tiles |
| xformers | Luôn luôn | Memory-efficient attention |
| Flash Attention | Ampere+ GPU | Fast attention kernel |
| TensorRT | Tương lai | Compiled model optimization |
| ONNX Runtime | Tương lai | Cross-platform optimization |
| Torch Compile | PyTorch 2.x | JIT compilation |

---

## Phụ Lục

### A. Thuật Ngữ

| Thuật ngữ | Giải thích |
|---|---|
| **Diffusion Model** | Mô hình AI tạo ảnh bằng cách loại bỏ noise dần dần |
| **Checkpoint** | File model chính (.safetensors, .ckpt) |
| **LoRA** | Low-Rank Adaptation — fine-tuning nhẹ cho style/concept |
| **ControlNet** | Model phụ kiểm soát bố cục, tư thế |
| **VAE** | Variational Auto-Encoder — encode/decode giữa pixel và latent |
| **Sampler/Scheduler** | Thuật toán denoising (Euler, DPM++, DDIM, etc.) |
| **CFG Scale** | Classifier-Free Guidance — mức độ tuân theo prompt |
| **VRAM** | Video RAM — bộ nhớ GPU |
| **Latent Space** | Không gian biểu diễn nén của ảnh |
| **Inpainting** | Tạo lại một phần ảnh được mask |
| **Outpainting** | Mở rộng ảnh ra ngoài biên ban đầu |
| **Upscale** | Phóng to ảnh với chất lượng cao |
| **Face Restore** | Khôi phục chi tiết khuôn mặt |
| **Embedding** | Textual Inversion — concept embedding |

### B. Tham Khảo

- [Stable Diffusion Paper](https://arxiv.org/abs/2112.10752)
- [HuggingFace Diffusers](https://huggingface.co/docs/diffusers)
- [ComfyUI](https://github.com/comfyanonymous/ComfyUI)
- [InvokeAI](https://github.com/invoke-ai/InvokeAI)
- [Fooocus](https://github.com/lllyasviel/Fooocus)
- [Stable Diffusion WebUI](https://github.com/AUTOMATIC1111/stable-diffusion-webui)
