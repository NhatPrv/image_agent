# 📏 Coding Standard — Image Agent

> Quy chuẩn viết code, naming convention, git workflow, error handling, logging, testing và best practices cho toàn bộ dự án Image Agent.

---

## Mục Lục

- [Python Coding Convention](#python-coding-convention)
- [TypeScript Coding Convention](#typescript-coding-convention)
- [Naming Convention](#naming-convention)
- [Folder Convention](#folder-convention)
- [Comment Convention](#comment-convention)
- [Git Convention](#git-convention)
- [Error Handling](#error-handling)
- [Logging](#logging)
- [Testing](#testing)
- [Best Practices](#best-practices)

---

## Python Coding Convention

### Style Guide

- **Base**: PEP 8 + PEP 257 (docstrings)
- **Formatter**: Ruff (thay thế Black)
- **Linter**: Ruff (thay thế flake8 + isort)
- **Line length**: 99 characters (thoải mái hơn 79, nhưng không quá dài)
- **Quotes**: Double quotes `"` cho strings, single quotes `'` chỉ khi string chứa `"`
- **Trailing commas**: Luôn sử dụng trong multiline

### Type Hints

**BẮT BUỘC** cho tất cả:
- Function parameters
- Function return types
- Class attributes
- Variables khi type không rõ ràng

```python
# ✅ Tốt
def create_generation(
    self,
    prompt: str,
    negative_prompt: str = "",
    width: int = 512,
    height: int = 512,
    steps: int = 20,
    cfg_scale: float = 7.0,
    seed: int = -1,
) -> GenerationResult:
    ...

# ❌ Xấu — thiếu type hints
def create_generation(self, prompt, negative_prompt="", width=512):
    ...
```

### Modern Python Features

```python
# Union types (3.10+)
# ✅ Tốt
def get_model(self, model_id: str) -> ModelInfo | None:
    ...

# ❌ Cũ
from typing import Optional, Union
def get_model(self, model_id: str) -> Optional[ModelInfo]:
    ...

# Built-in generics (3.9+)
# ✅ Tốt
models: list[ModelInfo] = []
params: dict[str, Any] = {}

# ❌ Cũ
from typing import List, Dict
models: List[ModelInfo] = []
```

### Imports

```python
# Thứ tự imports (Ruff sẽ auto-sort):
# 1. Standard library
# 2. Third-party
# 3. Local application

# ✅ Tốt
import asyncio
from pathlib import Path

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.entities.generation import GenerationEntity
from app.core.interfaces.ai_engine import IAIEngine
from app.services.generation_service import GenerationService
```

### Async/Await

```python
# Sử dụng async cho:
# - API endpoints
# - Database operations
# - File I/O
# - Event handling
# - Queue operations

# ✅ Tốt
async def generate_image(self, params: GenerationParams) -> GenerationResult:
    model = await self._model_loader.get_model()
    result = await self._engine.generate(model, params)
    await self._storage.save_image(result.image)
    await self._event_bus.emit(GenerationCompleted(result=result))
    return result

# ❌ Xấu — blocking I/O trong async context
async def generate_image(self, params: GenerationParams):
    image.save("output.png")  # Blocking! Sử dụng aiofiles thay thế
```

### Class Design

```python
# ✅ Tốt — Single Responsibility, small class
class GenerationService:
    """Orchestrates image generation workflow."""

    def __init__(
        self,
        engine: IAIEngine,
        queue: IQueueManager,
        event_bus: IEventBus,
        repo: IGenerationRepository,
    ) -> None:
        self._engine = engine
        self._queue = queue
        self._event_bus = event_bus
        self._repo = repo

    async def create(self, params: GenerationParams) -> str:
        """Create a new generation and add to queue."""
        ...

    async def execute(self, generation_id: str) -> GenerationResult:
        """Execute a queued generation."""
        ...

# ❌ Xấu — God Class
class ImageManager:
    """Does everything: load models, generate, save, queue, monitor..."""
    # 500+ lines, 30+ methods
```

### Dataclasses và Pydantic

```python
# Domain entities — dùng dataclass hoặc Pydantic BaseModel
from pydantic import BaseModel, Field

class GenerationParams(BaseModel):
    """Parameters for image generation."""

    prompt: str = Field(..., min_length=1, max_length=2000)
    negative_prompt: str = Field(default="", max_length=2000)
    width: int = Field(default=512, ge=64, le=2048, multiple_of=8)
    height: int = Field(default=512, ge=64, le=2048, multiple_of=8)
    steps: int = Field(default=20, ge=1, le=150)
    cfg_scale: float = Field(default=7.0, ge=1.0, le=30.0)
    seed: int = Field(default=-1, ge=-1)
    sampler: SchedulerType = Field(default=SchedulerType.EULER_A)

    model_config = ConfigDict(frozen=True)  # Immutable
```

---

## TypeScript Coding Convention

### Style Guide

- **Formatter**: Prettier
- **Linter**: ESLint
- **Line length**: 100 characters
- **Quotes**: Double quotes (consistent với Python)
- **Semicolons**: Required
- **Trailing commas**: Always in multiline

### TypeScript Strictness

tsconfig.json phải có:
```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "forceConsistentCasingInFileNames": true
  }
}
```

### Types & Interfaces

```typescript
// ✅ Tốt — Explicit types everywhere
interface GenerationParams {
  prompt: string;
  negativePrompt: string;
  width: number;
  height: number;
  steps: number;
  cfgScale: number;
  seed: number;
  sampler: SchedulerType;
}

// Use 'interface' for object shapes, 'type' for unions/intersections
type GenerationStatus = "queued" | "running" | "completed" | "failed" | "cancelled";

type GenerationMode = "txt2img" | "img2img" | "inpaint" | "outpaint";

// ❌ Xấu — any, implicit types
const generateImage = (params: any) => { ... };
```

### React Components

```typescript
// ✅ Tốt — Typed props, clear structure
interface PromptInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  maxLength?: number;
  disabled?: boolean;
}

export function PromptInput({
  value,
  onChange,
  placeholder = "Enter your prompt...",
  maxLength = 2000,
  disabled = false,
}: PromptInputProps) {
  return (
    <textarea
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      maxLength={maxLength}
      disabled={disabled}
      className="w-full min-h-[100px] resize-none"
    />
  );
}

// ❌ Xấu — Untyped, default export, class component
export default class PromptInput extends React.Component {
  render() {
    return <textarea onChange={this.props.onChange} />;
  }
}
```

### Hooks Pattern

```typescript
// ✅ Tốt — Custom hook encapsulating logic
export function useGeneration() {
  const queryClient = useQueryClient();

  const createMutation = useMutation({
    mutationFn: (params: GenerationParams) =>
      generationApi.create(params),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["queue"] });
    },
  });

  return {
    generate: createMutation.mutate,
    isGenerating: createMutation.isPending,
    error: createMutation.error,
  };
}
```

### Zustand Store Pattern

```typescript
// ✅ Tốt — Typed store with clear actions
interface UIState {
  // State
  sidebarOpen: boolean;
  activeTab: string;
  theme: "light" | "dark";

  // Actions
  toggleSidebar: () => void;
  setActiveTab: (tab: string) => void;
  setTheme: (theme: "light" | "dark") => void;
}

export const useUIStore = create<UIState>()((set) => ({
  sidebarOpen: true,
  activeTab: "generate",
  theme: "dark",

  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setActiveTab: (tab) => set({ activeTab: tab }),
  setTheme: (theme) => set({ theme }),
}));
```

---

## Naming Convention

### Python

| Loại | Convention | Ví dụ |
|---|---|---|
| **Module** | snake_case | `generation_service.py` |
| **Package** | snake_case | `ai_engine/` |
| **Class** | PascalCase | `GenerationService` |
| **Function** | snake_case | `create_generation()` |
| **Method** | snake_case | `def load_model(self)` |
| **Variable** | snake_case | `model_path` |
| **Constant** | UPPER_SNAKE | `MAX_VRAM_USAGE` |
| **Private** | _prefix | `_engine`, `_process_queue()` |
| **Protected** | _prefix | `_validate_params()` |
| **Interface** | I prefix + PascalCase | `IAIEngine`, `IStorage` |
| **Abstract** | Base/Abstract prefix | `BasePipeline` |
| **Enum** | PascalCase | `GenerationType` |
| **Enum Value** | UPPER_SNAKE | `GenerationType.TEXT_TO_IMAGE` |
| **Type Alias** | PascalCase | `ModelConfig = dict[str, Any]` |
| **Exception** | PascalCase + Error | `ModelLoadError` |

### TypeScript

| Loại | Convention | Ví dụ |
|---|---|---|
| **File (component)** | PascalCase | `PromptInput.tsx` |
| **File (util/hook)** | camelCase | `useGeneration.ts` |
| **File (store)** | camelCase + Store | `generationStore.ts` |
| **File (type)** | camelCase | `generation.ts` |
| **Component** | PascalCase | `PromptInput` |
| **Function** | camelCase | `createGeneration()` |
| **Variable** | camelCase | `modelPath` |
| **Constant** | UPPER_SNAKE | `MAX_PROMPT_LENGTH` |
| **Interface** | PascalCase | `GenerationParams` |
| **Type** | PascalCase | `GenerationStatus` |
| **Enum** | PascalCase | `GenerationType` |
| **Enum Value** | PascalCase | `GenerationType.TextToImage` |
| **Hook** | use + PascalCase | `useGeneration` |
| **Store** | use + PascalCase + Store | `useGenerationStore` |
| **CSS class** | kebab-case (TailwindCSS) | `text-primary` |

### Database

| Loại | Convention | Ví dụ |
|---|---|---|
| **Table** | snake_case, plural | `generations`, `queue_items` |
| **Column** | snake_case | `created_at`, `model_id` |
| **Primary Key** | `id` | `id UUID` |
| **Foreign Key** | ref_table_id | `model_id`, `generation_id` |
| **Index** | ix_table_column | `ix_generations_created_at` |
| **JSON column** | _json suffix | `metadata_json`, `lora_json` |
| **Boolean** | is_/has_ prefix | `is_favorite`, `has_lora` |
| **Timestamp** | _at suffix | `created_at`, `completed_at` |

### API

| Loại | Convention | Ví dụ |
|---|---|---|
| **URL** | kebab-case, plural | `/api/v1/queue-items` |
| **Query param** | camelCase | `?pageSize=20&sortBy=date` |
| **JSON field** | camelCase | `{ "cfgScale": 7.0 }` |
| **HTTP method** | Semantic | GET=read, POST=create, PUT=update, DELETE=remove |

---

## Folder Convention

### Backend

```
app/
├── api/           → HTTP layer (routes, DTOs, middleware, WebSocket)
├── core/          → Domain layer (entities, interfaces, enums, exceptions, constants)
├── services/      → Business logic layer (use cases, orchestration)
├── engine/        → AI engine (pipelines, processors, optimizers, model loader)
├── infrastructure/→ Implementation layer (database, storage, events, queue, plugins)
├── di/            → Dependency injection (container, providers)
├── config/        → Configuration (settings, logging, GPU)
└── main.py        → Application entry point
```

**Nguyên tắc:**
- Mỗi thư mục = 1 layer hoặc 1 concern
- Không có file loose ở root ngoài `main.py`
- Mỗi thư mục có `__init__.py` (có thể trống)
- Không quá 10 files trong 1 thư mục (refactor nếu cần)
- Test files mirror source structure

### Frontend

```
src/
├── main/          → Electron main process
├── preload/       → Electron preload scripts
└── renderer/      → React application
    ├── app/       → App setup (root, router, providers)
    ├── pages/     → Page components (1 folder per page)
    ├── components/→ Shared components (by domain: generation/, gallery/, common/)
    ├── stores/    → Zustand stores (1 file per store)
    ├── hooks/     → Custom hooks (1 file per hook)
    ├── services/  → API service layer
    ├── types/     → TypeScript type definitions
    ├── utils/     → Utility functions
    └── styles/    → Global styles, themes
```

**Nguyên tắc:**
- Components co-locate: `ComponentName/index.tsx`, `ComponentName.test.tsx`
- 1 component per file
- Pages import from components, không ngược lại
- Hooks encapsulate complex logic
- Services isolate API calls

---

## Comment Convention

### Python Docstrings

```python
# ✅ Tốt — Google-style docstrings
class GenerationService:
    """Service for orchestrating image generation workflow.

    This service manages the lifecycle of image generation requests,
    from creation through queue management to execution.

    Attributes:
        _engine: AI engine for running generation.
        _queue: Queue manager for ordering requests.
        _event_bus: Event bus for publishing lifecycle events.
    """

    async def create_generation(
        self,
        params: GenerationParams,
    ) -> str:
        """Create a new generation request and add to queue.

        Args:
            params: Generation parameters including prompt, size, etc.

        Returns:
            The unique ID of the created generation.

        Raises:
            ValidationError: If parameters are invalid.
            ModelNotLoadedError: If no model is loaded.
            QueueFullError: If the queue is at capacity.
        """
        ...
```

### TypeScript JSDoc

```typescript
/**
 * Custom hook for managing image generation state and actions.
 *
 * @example
 * ```tsx
 * const { generate, isGenerating } = useGeneration();
 * ```
 */
export function useGeneration() {
  ...
}

/**
 * Prompt input component with auto-resize and token counting.
 *
 * @param props - Component props
 * @param props.value - Current prompt text
 * @param props.onChange - Callback when text changes
 * @param props.maxLength - Maximum character length (default: 2000)
 */
export function PromptInput({ value, onChange, maxLength = 2000 }: PromptInputProps) {
  ...
}
```

### Inline Comments

```python
# ✅ Tốt — Giải thích WHY, không phải WHAT
# xformers provides 30-40% VRAM reduction on 8GB GPU
pipe.enable_xformers_memory_efficient_attention()

# Seed -1 means random seed, generate one for reproducibility
actual_seed = seed if seed >= 0 else random.randint(0, 2**32 - 1)

# ❌ Xấu — Mô tả lại code
# Set width to 512
width = 512

# Loop through models
for model in models:
    ...
```

### TODO/FIXME Convention

```python
# TODO(username): Description of what needs to be done
#   Issue: #123 (if applicable)

# FIXME(username): Description of bug/issue
#   This causes memory leak when switching models rapidly

# HACK(username): Temporary workaround, explain why
#   Diffusers v0.28 has bug with SDXL LoRA, remove after upgrade

# NOTE: Important context for future developers
#   VRAM usage peaks at step 15-20, not at the end
```

**Nguyên tắc:** Tất cả TODO/FIXME phải có username và mô tả rõ ràng. Không để TODO orphan (không có issue link hoặc plan).

---

## Git Convention

### Branch Strategy (Git Flow)

```
main              ← Production-ready releases
├── develop       ← Integration branch
│   ├── feature/  ← New features
│   ├── fix/      ← Bug fixes
│   ├── refactor/ ← Code refactoring
│   ├── docs/     ← Documentation
│   ├── test/     ← Test additions
│   └── chore/    ← Build, CI, deps
└── release/      ← Release preparation
    └── hotfix/   ← Production bug fixes
```

### Branch Naming

```
feature/short-description
fix/issue-number-description
refactor/module-name-description
docs/document-name
chore/dependency-update

# Ví dụ
feature/txt2img-pipeline
feature/vram-monitor-widget
fix/42-model-load-memory-leak
refactor/generation-service-split
docs/api-documentation
chore/update-pytorch-2.3
```

### Commit Convention (Conventional Commits)

```
<type>(<scope>): <description>

[optional body — WHY this change is made]

[optional footer — Breaking changes, issue refs]
```

**Types:**

| Type | Khi nào dùng | Ví dụ |
|---|---|---|
| `feat` | Tính năng mới | `feat(engine): add txt2img pipeline` |
| `fix` | Sửa lỗi | `fix(vram): resolve OOM on SDXL generation` |
| `docs` | Documentation | `docs(api): add generation endpoint docs` |
| `style` | Formatting only | `style(backend): apply ruff formatting` |
| `refactor` | Restructure code | `refactor(service): extract queue logic` |
| `perf` | Performance | `perf(engine): enable xformers attention` |
| `test` | Tests | `test(service): add generation service tests` |
| `chore` | Tooling, deps | `chore(deps): update diffusers to 0.30` |
| `ci` | CI/CD | `ci: add pytest workflow` |
| `build` | Build system | `build(electron): configure electron-builder` |

**Scope** (optional):

| Scope | Nghĩa |
|---|---|
| `engine` | AI Engine module |
| `api` | API routes, DTOs |
| `service` | Service layer |
| `db` | Database, migrations |
| `ui` | Frontend UI |
| `store` | Zustand/state |
| `plugin` | Plugin system |
| `queue` | Queue system |
| `vram` | VRAM management |
| `config` | Configuration |
| `deps` | Dependencies |
| `electron` | Electron main process |

**Rules:**
- Description viết bằng tiếng Anh, lowercase, no period
- Description tối đa 72 characters
- Body giải thích WHY, không phải WHAT (code đã nói WHAT)
- Footer chứa `BREAKING CHANGE:` nếu có
- Footer ref issues: `Closes #42`, `Fixes #123`

### Pull Request

**Template:**

```markdown
## What
Brief description of changes.

## Why
Why these changes are needed.

## How
How the changes work (high-level).

## Testing
- [ ] Unit tests added/updated
- [ ] Manual testing done
- [ ] Edge cases considered

## Screenshots (if UI changes)
Before | After

## Checklist
- [ ] Code follows CODING_STANDARD
- [ ] Types/hints complete
- [ ] Docstrings added
- [ ] No console.log/print left
- [ ] No TODO without issue ref
```

---

## Error Handling

### Python Error Handling

```python
# ✅ Tốt — Specific exceptions, clear messages, context
async def load_model(self, model_path: str) -> ModelInfo:
    if not Path(model_path).exists():
        raise ModelNotFoundError(
            f"Model file not found: {model_path}",
            model_path=model_path,
        )

    try:
        model_info = await self._loader.load(model_path)
    except torch.cuda.OutOfMemoryError as e:
        await self._cleanup_vram()
        raise VRAMInsufficientError(
            f"Not enough VRAM to load model. Required: {estimated_vram}MB, "
            f"Available: {available_vram}MB",
            required_vram=estimated_vram,
            available_vram=available_vram,
        ) from e
    except Exception as e:
        logger.exception("Unexpected error loading model: %s", model_path)
        raise ModelLoadError(
            f"Failed to load model: {model_path}",
            model_path=model_path,
            original_error=str(e),
        ) from e

    return model_info

# ❌ Xấu
async def load_model(self, model_path):
    try:
        return self._loader.load(model_path)
    except:  # Bare except!
        print("Error!")  # print instead of log!
        return None  # Swallowing error!
```

### TypeScript Error Handling

```typescript
// ✅ Tốt — Typed errors, user-friendly messages
try {
  const result = await generationApi.create(params);
  return result;
} catch (error) {
  if (error instanceof ApiError) {
    if (error.status === 422) {
      toast.error("Invalid generation parameters. Please check your settings.");
    } else if (error.status === 503) {
      toast.error("AI engine is busy. Your request has been queued.");
    } else {
      toast.error(`Generation failed: ${error.message}`);
    }
  } else {
    toast.error("An unexpected error occurred. Please try again.");
    console.error("Generation error:", error);
  }
  throw error; // Re-throw for TanStack Query error handling
}
```

### Error Response Format

```json
{
  "error": {
    "code": "VRAM_INSUFFICIENT",
    "message": "Not enough VRAM to load model",
    "details": {
      "required_vram_mb": 6500,
      "available_vram_mb": 4200,
      "model_name": "sdxl-base-1.0"
    },
    "suggestion": "Try closing other GPU applications or use a smaller model"
  }
}
```

---

## Logging

### Python Logging

```python
import logging

logger = logging.getLogger(__name__)

# Log levels:
# DEBUG    → Detailed diagnostic info (not in production)
# INFO     → Confirmation of expected behavior
# WARNING  → Unexpected but recoverable situation
# ERROR    → Error that prevented operation
# CRITICAL → System-level failure

# ✅ Tốt — Structured, contextual logging
logger.info(
    "Generation started",
    extra={
        "generation_id": generation_id,
        "model": model_name,
        "width": width,
        "height": height,
        "steps": steps,
    },
)

logger.warning(
    "VRAM usage high: %.1f%%",
    vram_percent,
    extra={"vram_used_mb": vram_used, "vram_total_mb": vram_total},
)

logger.error(
    "Generation failed: %s",
    str(error),
    extra={"generation_id": generation_id},
    exc_info=True,  # Include traceback
)

# ❌ Xấu
print(f"Starting generation...")  # NEVER use print
logger.info(f"Generation {id} started")  # f-string in logger (use % formatting)
```

### Logging Configuration

```python
# Structured logging config
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "json": {
            # JSON formatter for production/parsing
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "level": "DEBUG",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/image_agent.log",
            "maxBytes": 10_000_000,  # 10MB
            "backupCount": 5,
            "formatter": "standard",
            "level": "INFO",
        },
    },
    "loggers": {
        "app": {"level": "DEBUG", "handlers": ["console", "file"]},
        "uvicorn": {"level": "INFO"},
        "sqlalchemy": {"level": "WARNING"},
        "diffusers": {"level": "WARNING"},
    },
}
```

### Log Rotation

- Max file size: 10MB
- Max backup files: 5
- Oldest logs auto-deleted
- Log directory: `logs/`
- Log file naming: `image_agent.log`, `image_agent.log.1`, etc.

---

## Testing

### Python Testing (Pytest)

#### Test Structure

```
tests/
├── unit/
│   ├── services/
│   │   ├── test_generation_service.py
│   │   ├── test_model_service.py
│   │   └── test_queue_service.py
│   ├── engine/
│   │   ├── test_txt2img_pipeline.py
│   │   └── test_vram_manager.py
│   └── infrastructure/
│       ├── test_event_bus.py
│       └── test_local_storage.py
├── integration/
│   ├── test_api_generation.py
│   ├── test_api_models.py
│   └── test_engine_integration.py
└── fixtures/
    ├── conftest.py
    ├── model_fixtures.py
    └── generation_fixtures.py
```

#### Test Naming

```python
# Pattern: test_<method>_<scenario>_<expected>
class TestGenerationService:
    async def test_create_generation_valid_params_returns_id(self):
        ...

    async def test_create_generation_empty_prompt_raises_validation_error(self):
        ...

    async def test_create_generation_no_model_loaded_raises_error(self):
        ...

    async def test_execute_generation_success_emits_completed_event(self):
        ...
```

#### Test Patterns

```python
# ✅ Tốt — AAA pattern (Arrange, Act, Assert)
async def test_create_generation_valid_params_returns_id(
    self,
    generation_service: GenerationService,
    sample_params: GenerationParams,
):
    # Arrange
    mock_engine = generation_service._engine
    mock_engine.is_model_loaded.return_value = True

    # Act
    generation_id = await generation_service.create(sample_params)

    # Assert
    assert generation_id is not None
    assert isinstance(generation_id, str)
    assert len(generation_id) == 36  # UUID format
```

#### Fixtures

```python
# conftest.py
@pytest.fixture
def mock_engine() -> Mock:
    engine = AsyncMock(spec=IAIEngine)
    engine.is_model_loaded.return_value = True
    return engine

@pytest.fixture
def generation_service(
    mock_engine: Mock,
    mock_queue: Mock,
    mock_event_bus: Mock,
    mock_repo: Mock,
) -> GenerationService:
    return GenerationService(
        engine=mock_engine,
        queue_manager=mock_queue,
        event_bus=mock_event_bus,
        generation_repo=mock_repo,
    )

@pytest.fixture
def sample_params() -> GenerationParams:
    return GenerationParams(
        prompt="a beautiful sunset",
        width=512,
        height=512,
        steps=20,
    )
```

### TypeScript Testing (Vitest)

```typescript
// ✅ Tốt — Component test with React Testing Library
import { render, screen, fireEvent } from "@testing-library/react";
import { PromptInput } from "./PromptInput";

describe("PromptInput", () => {
  it("renders with placeholder text", () => {
    render(<PromptInput value="" onChange={() => {}} />);
    expect(screen.getByPlaceholderText("Enter your prompt...")).toBeInTheDocument();
  });

  it("calls onChange when text is entered", () => {
    const onChange = vi.fn();
    render(<PromptInput value="" onChange={onChange} />);

    fireEvent.change(screen.getByRole("textbox"), {
      target: { value: "test prompt" },
    });

    expect(onChange).toHaveBeenCalledWith("test prompt");
  });

  it("disables input when disabled prop is true", () => {
    render(<PromptInput value="" onChange={() => {}} disabled />);
    expect(screen.getByRole("textbox")).toBeDisabled();
  });
});
```

### Coverage Requirements

| Module | Min Coverage |
|---|---|
| Core (entities, interfaces) | 90% |
| Services | 85% |
| Engine (non-GPU code) | 80% |
| Infrastructure | 75% |
| API routes | 70% |
| Frontend components | 60% |
| Frontend hooks/stores | 80% |

---

## Best Practices

### General

| ✅ DO | ❌ DON'T |
|---|---|
| Write self-documenting code | Write clever/tricky code |
| Use meaningful variable names | Use single-letter variables (except `i`, `j` in loops) |
| Keep functions < 30 lines | Create 100+ line functions |
| Keep classes < 200 lines | Create God Classes |
| Return early (guard clauses) | Deep nesting (> 3 levels) |
| Use constants for magic numbers | Hardcode values |
| Handle all error cases | Swallow exceptions silently |
| Log meaningful context | Use print statements |
| Write tests for new features | Skip tests "for now" |
| Review your own code before PR | Submit code without self-review |

### Performance

| ✅ DO | ❌ DON'T |
|---|---|
| Use async I/O for file/network | Block event loop with sync I/O |
| Cache expensive computations | Recompute on every call |
| Use lazy loading for heavy modules | Import everything at startup |
| Profile before optimizing | Optimize prematurely |
| Use generators for large datasets | Load everything into memory |
| Release GPU memory after use | Leave tensors on GPU |
| Use batch operations for DB | Run N individual queries |

### Security

| ✅ DO | ❌ DON'T |
|---|---|
| Validate all inputs (Pydantic) | Trust user input |
| Sanitize file paths | Allow path traversal |
| Use parameterized SQL queries | Build SQL strings |
| Bind to localhost only | Expose API to network |
| Hash model files for integrity | Load unverified files |
| Sandbox plugins | Give plugins full access |

### Python-Specific

| ✅ DO | ❌ DON'T |
|---|---|
| Use `pathlib.Path` | Use string concatenation for paths |
| Use context managers (`with`) | Manual open/close |
| Use `__slots__` for data classes | Waste memory on instances |
| Use `functools.lru_cache` | Recompute pure functions |
| Use `asyncio.gather` for concurrent | Sequential await for independent tasks |
| Use `from __future__ import annotations` | Forget forward references |

### React-Specific

| ✅ DO | ❌ DON'T |
|---|---|
| Use functional components | Use class components |
| Memoize expensive renders | Re-render entire tree |
| Use `useCallback`/`useMemo` wisely | Premature memoization everywhere |
| Keep components pure | Side effects in render |
| Lift state up when shared | Prop drill through 5+ levels |
| Use error boundaries | Let errors crash the app |
| Lazy load pages/routes | Bundle everything together |
