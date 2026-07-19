# 🗺️ LỘ TRÌNH HỌC TẬP & KIẾN THỨC NỀN TẢNG (TỪ CON SỐ 0)
## DỰ ÁN IMAGE AGENT (DESKTOP ARTIFICIAL INTELLIGENCE APP)

Tài liệu này được thiết kế để cung cấp toàn bộ các kiến thức từ cơ bản (con số 0) đến chuyên sâu giúp bạn đọc, hiểu, bảo trì và phát triển toàn diện dự án **Image Agent**. Lộ trình được chia theo các cấp độ kiến thức nền tảng và tương ứng cụ thể theo từng Phase phát triển của dự án.

---

## 📌 PHẦN 1: KIẾN THỨC NỀN TẢNG CƠ BẢN (LEVEL 0)

Trước khi đi vào cấu trúc cụ thể của dự án, đây là các khối kiến thức cốt lõi bạn cần nắm được:

### 1. Frontend & Desktop Wrapper (React + TypeScript + Electron)
*   **TypeScript (Cơ bản & Nâng cao)**:
    *   Hiểu về kiểu dữ liệu tĩnh (`type`, `interface`, `generic`), ép kiểu (`type assertion`), và an toàn kiểu dữ liệu.
    *   *Tại sao cần?* Frontend và Backend giao tiếp qua dữ liệu dạng JSON phức tạp, việc gán kiểu chặt chẽ giúp tránh lỗi Runtime.
*   **React (Hooks & State)**:
    *   Nắm vững cơ chế hoạt động của `useState`, `useEffect` (vòng đời component), `useMemo`, `useCallback`, và `useRef`.
    *   *Tại sao cần?* Quản lý các giao diện tương tác cao như Canvas vẽ mặt nạ (Inpainting), trạng thái tải mô hình, và tiến trình vẽ ảnh theo thời gian thực.
*   **Zustand (State Management)**:
    *   Cách tạo và sử dụng store chung để quản lý trạng thái ứng dụng mà không cần truyền prop thủ công qua nhiều cấp component (Prop Drilling).
    *   *Tại sao cần?* Lưu trữ cấu hình sinh ảnh toàn cục (prompt, width, height, steps, active model) để các View khác nhau (GenerateView, HistoryView) đồng bộ tức thì.
*   **Kiến trúc Electron**:
    *   **Main Process**: Chạy trên Node.js, quản lý cửa sổ ứng dụng (BrowserWindow), tương tác với HĐH (mở hộp thoại, lưu file).
    *   **Renderer Process**: Giao diện người dùng chạy trên môi trường Chromium (React App).
    *   **IPC (Inter-Process Communication)**: Giao tiếp bất đồng bộ giữa Main và Renderer thông qua kênh `ipcMain` và `ipcRenderer`.
    *   **Preload Scripts**: Cầu nối an toàn cho phép Renderer truy cập một số API bảo mật của Node.js qua đối tượng `window.api`.

### 2. Backend & Database (Fastapi + Async Python + SQLite)
*   **Python Bất đồng bộ (Asyncio)**:
    *   Hiểu các từ khóa `async`, `await`, cơ chế hoạt động của Event Loop và cách chạy các tác vụ chặn (blocking I/O) trong luồng phụ (`run_in_executor`).
    *   *Tại sao cần?* Tiến trình nạp mô hình AI (~6GB) và sinh ảnh vô cùng tốn thời gian, nếu không dùng lập trình bất đồng bộ, giao diện người dùng sẽ bị đóng băng hoàn toàn.
*   **FastAPI**:
    *   Cách xây dựng RESTful API, thiết kế Route, Dependency Injection (`Depends`), và xác thực dữ liệu đầu vào bằng **Pydantic**.
*   **SQLAlchemy 2.0 (Async ORM) & SQLite**:
    *   Thiết kế cơ sở dữ liệu quan hệ, quan hệ 1-N (ví dụ: Một tiến trình sinh ảnh có thể sinh ra nhiều bức ảnh con), viết câu lệnh truy vấn bất đồng bộ (`select`, `insert`, `delete`).

### 3. Khái Niệm AI & Bộ Nhớ GPU (VRAM)
*   **Mô Hình Khuếch Tán (Diffusion Models)**:
    *   Hiểu nguyên lý cơ bản: Từ một ảnh nhiễu ngẫu nhiên (noise), mô hình sẽ khử nhiễu từng bước (steps) dựa trên câu lệnh (prompt) để tạo thành bức ảnh rõ nét.
*   **VRAM (Video RAM)**:
    *   Khác với RAM hệ thống, VRAM nằm trên Card đồ họa (GPU). Mô hình AI phải được nạp toàn bộ trọng số (weights) vào VRAM mới có thể tính toán sinh ảnh được.
    *   *Quy luật VRAM*: GPU 8GB VRAM (như RTX 4060) chỉ chứa được tối đa mô hình SDXL (~6GB) kèm cấu hình tối ưu nhẹ. Nếu nạp các mô hình lớn hơn (như FLUX 12GB+), VRAM sẽ bị tràn, hệ thống buộc phải dùng RAM ảo (Shared VRAM) dẫn đến tốc độ sinh ảnh chậm đi hàng chục lần hoặc sập phần mềm.

---

## 🗺️ PHẦN 2: KIẾN THỨC CẦN BIẾT THEO TỪNG PHASE CỦA DỰ ÁN

### 📋 Phase 1: MVP & Core Setup (Dựng Khung & Sinh Ảnh Cơ Bản)
> **Mục tiêu**: Dựng được khung ứng dụng Desktop, tự động kích hoạt máy chủ Python từ Electron và thực hiện lệnh vẽ Text-to-Image cục bộ cơ bản.

*   **Kiến thức cần học**:
    1.  **Child Process (Node.js)**: Cách dùng `spawn` để khởi chạy máy chủ Python FastAPI ngầm (`uvicorn`) khi ứng dụng Electron được mở và dọn dẹp tiến trình (`kill`) khi đóng ứng dụng.
    2.  **WebSocket (aiosqlite / websockets)**: Giao tiếp hai chiều thời gian thực. Giúp Backend liên tục gửi dữ liệu bước nhảy (ví dụ: "Đang vẽ 10%... 20%...") và ảnh xem trước tạm thời (preview image) lên giao diện React.
    3.  **Thư viện Diffusers (Hugging Face)**:
        *   Cách sử dụng `StableDiffusionPipeline` để nạp tệp checkpoint `.safetensors` hoặc `.ckpt`.
        *   Cách sử dụng đối số `from_single_file` để nạp mô hình cục bộ đã tải về máy thay vì tải từ internet.
*   **Tệp tin mã nguồn tương ứng trong dự án**:
    *   [index.ts](file:///C:/mydata/selfproject/image_agent/frontend/src/main/index.ts): Quản lý spawn tiến trình Python ở Main process.
    *   [websocket.py](file:///C:/mydata/selfproject/image_agent/backend/app/api/v1/endpoints/websocket.py): Máy chủ WebSocket đẩy trạng thái tiến trình vẽ.
    *   [txt2img.py](file:///C:/mydata/selfproject/image_agent/backend/app/engine/pipelines/txt2img.py): Thực thi nạp mô hình SD1.5/SDXL và chạy khử nhiễu.

---

### 🎨 Phase 2: Advanced Generation (Các Tính Năng Vẽ Nâng Cao)
> **Mục tiêu**: Tích hợp các kỹ thuật vẽ chuyên sâu như Inpainting (sửa ảnh), Outpainting (vẽ tràn viền), LoRA (vẽ nhân vật/phong cách cụ thể), và ControlNet (điều khiển tư thế, đường nét).

*   **Kiến thức cần học**:
    1.  **Canvas Drawing API (HTML5)**: Cách xây dựng một trình chỉnh sửa cọ vẽ (brush), tẩy (eraser) để người dùng tô lên các vùng ảnh muốn sửa (tạo mask nhị phân: vùng tô có màu trắng, vùng giữ nguyên có màu đen).
    2.  **Inpainting Pipeline**: Hiểu cách hoạt động của `StableDiffusionInpaintPipeline`. Nó nhận vào 3 tham số: Ảnh gốc, Ảnh mặt nạ (Mask), và Prompt mới để chỉ tái tạo vùng ảnh bị tô.
    3.  **PEFT (Parameter-Efficient Fine-Tuning)**:
        *   Hiểu cơ chế hoạt động của **LoRA (Low-Rank Adaptation)**: Chỉ tinh chỉnh một lượng nhỏ tham số ma trận thay vì huấn luyện lại toàn bộ mô hình lớn.
        *   Cách gọi `load_lora_weights(lora_dir, weight_name=...)` để nạp tệp LoRA và `set_adapters(names, weights)` để kích hoạt, thay đổi trọng số hoặc phối hợp nhiều LoRA cùng lúc (Multi-LoRA).
        *   *Chú ý*: Phải nắm rõ cấu trúc thư mục chứa LoRA để tránh lỗi key-mapping của Diffusers khi nạp file cục bộ.
    4.  **ControlNet**:
        *   Cách hoạt động của mạng lưới điều khiển phụ (ControlNet).
        *   Cách sử dụng các bộ tiền xử lý hình ảnh (preprocessors) như: Thuật toán Canny (dò cạnh), mô hình MiDaS (tính chiều sâu), hoặc OpenPose (dò xương người) để tạo ra ảnh điều khiển trước khi đưa vào pipeline.
    5.  **Hàng đợi Công việc (Priority Queue)**: Thiết kế hàng đợi trong Python để khi người dùng nhấn vẽ liên tục, các yêu cầu sẽ được xếp hàng và xử lý tuần tự nhằm tránh tràn VRAM.
*   **Tệp tin mã nguồn tương ứng trong dự án**:
    *   [inpaint.py](file:///C:/mydata/selfproject/image_agent/backend/app/engine/pipelines/inpaint.py): Triển khai pipeline sửa ảnh.
    *   [base.py (apply_loras)](file:///C:/mydata/selfproject/image_agent/backend/app/engine/pipelines/base.py#L168-L218): Nạp và quản lý trọng số LoRA.
    *   [queue_manager.py](file:///C:/mydata/selfproject/image_agent/backend/app/infrastructure/queue/queue_manager.py): Bộ quản lý hàng đợi tác vụ vẽ.

---

### 📂 Phase 3: Album, Tags & History Management (Lưu Trữ & Quản Lý Dữ Liệu)
> **Mục tiêu**: Xây dựng kho lưu trữ cục bộ, phân loại album ảnh thông minh, gắn thẻ tag và hiển thị thư viện ảnh mượt mà.

*   **Kiến thức cần học**:
    1.  **Xử lý ảnh hiệu năng cao (Pillow / Sharp)**: Cách nén ảnh, tạo ảnh thu nhỏ (thumbnail) định dạng `.webp` dung lượng thấp để tối ưu hóa hiển thị danh sách hàng ngàn ảnh trên giao diện mà không bị lag.
    2.  **Đồng bộ hóa Database & Đĩa cứng**: Cách viết cơ chế quét thư mục (folder scanning), tự động xóa bản ghi database nếu người dùng xóa file trên ổ cứng, tính toán mã băm SHA-256 để định danh duy nhất cho từng mô hình AI.
    3.  **Thiết kế Schema Database**: Mối quan hệ bảng: `generations` (lịch sử cấu hình lệnh vẽ) -> `images` (các tệp ảnh đầu ra).
*   **Tệp tin mã nguồn tương ứng trong dự án**:
    *   [image_repo.py](file:///C:/mydata/selfproject/image_agent/backend/app/infrastructure/database/repositories/image_repo.py): Lưu và quản lý ảnh trong SQLite.
    *   [model_service.py](file:///C:/mydata/selfproject/image_agent/backend/app/services/model_service.py): Quét mô hình và đồng bộ database.

---

### ⚡ Phase 4: Advanced Engine Optimizations (Tối Ưu Hóa Bộ Nhớ & Hiệu Năng)
> **Mục tiêu**: Giúp các máy cấu hình yếu (8GB VRAM hoặc ít hơn) chạy được các mô hình nặng (SDXL) thông qua các kỹ thuật tối ưu hóa bộ nhớ chuyên sâu của PyTorch và Diffusers.

*   **Kiến thức cần học**:
    1.  **Attention Slicing & VAE Slicing/Tiling**: 
        *   Thay vì tính toán ma trận Attention của toàn bộ bức ảnh cùng lúc (yêu cầu lượng VRAM khổng lồ), thuật toán chia nhỏ ảnh thành các lát cắt (slices) hoặc các ô (tiles) để tính toán tuần tự.
        *   *Hiệu quả*: Giúp vẽ ảnh độ phân giải cao (ví dụ 1024x1024 trở lên) trên card 8GB VRAM mà không bị báo lỗi `Out of Memory`.
    2.  **Model CPU Offloading**:
        *   Tự động đẩy các thành phần mô hình chưa dùng tới (như bộ mã hóa văn bản Text Encoder, bộ giải mã VAE) từ bộ nhớ GPU (VRAM) sang bộ nhớ RAM hệ thống (CPU), chỉ giữ lại UNet đang tính toán trên GPU.
    3.  **Lượng tử hóa (Quantization - fp16, fp8, int8)**:
        *   Hiểu sự khêu biệt về độ chính xác số học: Số thực 32-bit (fp32) tốn gấp đôi dung lượng so với 16-bit (fp16).
        *   Cách tải và cấu hình mô hình ở định dạng `torch.float16` hoặc nén lượng tử `fp8` để giảm dung lượng VRAM tiêu thụ đi một nửa mà không làm suy giảm đáng kể chất lượng ảnh.
    4.  **Xformers & FlashAttention**:
        *   Cài đặt và cấu hình thư viện tăng tốc phần cứng, thay thế thuật toán tính toán Self-Attention mặc định của PyTorch bằng thuật toán tối ưu hóa của Meta (xFormers) giúp tăng tốc độ sinh ảnh lên tới 30%.
*   **Tệp tin mã nguồn tương ứng trong dự án**:
    *   [base.py (apply_optimizations)](file:///C:/mydata/selfproject/image_agent/backend/app/engine/pipelines/base.py#L34-L113): Tích hợp CPU offload, VAE tiling/slicing, xFormers cho pipeline.

---

### 🌐 Phase 5: Cloud Bridge & Plugins (Kết Nối Đám Mây & Hệ Thống Tiện Ích)
> **Mục tiêu**: Vượt qua giới hạn phần cứng cục bộ. Cho phép người dùng chuyển đổi chế độ chạy đám mây (Cloud Mode) để vẽ các mô hình cực nặng (như FLUX.1) hoặc tích hợp các tính năng mở rộng từ bên thứ ba.

*   **Kiến thức cần học**:
    1.  **Kiến trúc Plugin động (Dynamic Imports)**:
        *   Cách sử dụng mô-đun `importlib` của Python để quét thư mục và nạp động các file code tiện ích mà không cần khai báo cứng trong hệ thống.
    2.  **API Integration (REST / SDKs)**:
        *   Tương tác với các dịch vụ GPU đám mây thông qua API của **Fal.ai**, **Replicate**, hoặc triển khai mô hình riêng lên **AWS Sagemaker / EC2**.
        *   Cách thiết kế giao diện thích ứng: Người dùng chỉ cần bật công tắc "Cloud Mode", toàn bộ tham số vẽ sẽ được chuyển hướng gửi lên API đám mây thay vì chạy trên GPU local.
    3.  **Quản lý Khóa bảo mật (API Key Storage)**:
        *   Cách lưu trữ mã hóa các khóa API Key của người dùng một cách an toàn dưới ổ đĩa cục bộ.

---

## 🛠️ PHẦN 3: DANH SÁCH CÁC CÔNG CỤ VÀ THƯ VIỆN THEN CHỐT CẦN TÌM HIỂU

Để làm chủ dự án này, bạn hãy tìm kiếm tài liệu và thực hành trên các công cụ sau:

1.  **Về Phía AI/Python**:
    *   **Hugging Face Diffusers**: Đọc hướng dẫn sử dụng thư viện (mục *Pipelines*, *Optimization*, *LoRA*).
    *   **PyTorch**: Các câu lệnh kiểm tra GPU (`torch.cuda.is_available()`, `torch.cuda.empty_cache()`).
    *   **PEFT (by Hugging Face)**: Đọc cơ chế quản lý adapter của LoRA.
2.  **Về Phía Phát Triển Desktop App**:
    *   **Electron-Vite**: Bộ công cụ build ứng dụng Electron sử dụng Vite cực kỳ nhanh chóng.
    *   **Zustand**: Đọc tài liệu trang chủ để biết cách tạo store và xử lý async actions trong store.
    *   **TailwindCSS**: Thư viện CSS dạng tiện ích giúp thiết kế giao diện cao cấp nhanh chóng.
