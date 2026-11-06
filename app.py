import os
import sys
import time
import asyncio
import tempfile
import subprocess
from pathlib import Path
from datetime import timedelta
import streamlit as st
import whisper
from google import genai
from google.genai import types

# ==============================================================================
# 1. CẤU HÌNH TRANG & GIAO DIỆN LUXURY BRANDING (HẬU DÒNG TIỀN REAL ESTATE)
# ==============================================================================
st.set_page_config(
    page_title="Hậu Dòng Tiền Real Estate | Auto Video Studio & Storytelling AI",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    .stApp {
        background-color: #0B0F19;
        color: #F3F4F6;
    }
    
    /* Header thương hiệu cao cấp */
    .brand-header {
        background: linear-gradient(135deg, #111827 0%, #1F2937 100%);
        padding: 24px 30px;
        border-radius: 16px;
        border: 1px solid #D4AF37;
        box-shadow: 0 10px 25px -5px rgba(212, 175, 55, 0.15);
        margin-bottom: 25px;
    }
    .brand-title {
        color: #D4AF37;
        font-size: 26px;
        font-weight: 800;
        letter-spacing: 0.5px;
        margin: 0;
        text-transform: uppercase;
    }
    .brand-subtitle {
        color: #9CA3AF;
        font-size: 14px;
        margin-top: 5px;
    }
    
    /* Khối thẻ giao diện */
    .section-card {
        background: #111827;
        padding: 20px;
        border-radius: 14px;
        border: 1px solid #1F2937;
        margin-bottom: 20px;
    }
    .section-title {
        color: #F59E0B;
        font-size: 16px;
        font-weight: 700;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    /* Badge DNA Style & Framework */
    .dna-box {
        background: rgba(212, 175, 55, 0.08);
        border: 1px dashed #D4AF37;
        border-radius: 10px;
        padding: 12px 16px;
        font-size: 13px;
        color: #FDE68A;
        margin-top: 10px;
        line-height: 1.5;
    }

    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #D4AF37 0%, #B45309 100%);
        color: #000000;
        font-weight: 700;
        border: none;
        border-radius: 10px;
        padding: 12px 24px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 14px 0 rgba(212, 175, 55, 0.3);
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #F59E0B 0%, #D4AF37 100%);
        transform: translateY(-2px);
        box-shadow: 0 6px 20px 0 rgba(212, 175, 55, 0.45);
        color: #000000;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ==============================================================================
# 2. CACHE CÁC HÀM TẢI MÔ HÌNH NẶNG (WHISPER)
# ==============================================================================
@st.cache_resource(show_spinner=False)
def load_whisper_model(model_name: str = "base"):
    """Tải và lưu trữ model Whisper trong RAM để tránh reload."""
    return whisper.load_model(model_name)


# ==============================================================================
# 3. ĐỊNH NGHĨA 10 STORYTELLING FRAMEWORKS & BRAND DNA
# ==============================================================================
FRAMEWORK_GUIDES = {
    "1. Cấu trúc ba hồi (Mở, Xung đột, Giải quyết)": (
        "Mở đầu thiết lập bối cảnh thị trường/tài sản -> Đẩy mâu thuẫn/áp lực lên đỉnh điểm "
        "(chôn vốn vào đất nền đóng băng, lạm phát bào mòn tài sản) -> Đưa ra giải pháp là tòa BĐS "
        "dòng tiền này giải tỏa toàn bộ áp lực."
    ),
    "2. PAS (Vấn đề, Khuấy sâu, Giải pháp)": (
        "Nêu vấn đề nhức nhối của nhà đầu tư (cầm 20-30 tỷ gửi ngân hàng mất giá, mua đất vùng ven "
        "thanh khoản kém) -> Khuấy sâu nỗi đau (tiền bốc hơi từng ngày, lãi vay đè nặng) -> Giải pháp: "
        "BĐS dòng tiền ven biển Đà Nẵng, gà đẻ trứng vàng hằng tháng."
    ),
    "3. BAB (Trước, Sau, Cầu nối)": (
        "Bức tranh trước khi đầu tư (bất an, loay hoay tìm kênh trú ẩn an toàn) -> Bức tranh tương lai "
        "thịnh vượng (nhận đều đặn 100-150 triệu mỗi tháng, thong dong an nhàn) -> Cầu nối chính là "
        "tài sản dòng tiền đang được giới thiệu."
    ),
    "4. ABT (Và, Nhưng, Vì vậy)": (
        "Bạn sở hữu khối tài sản lớn VÀ luôn muốn dòng vốn sinh sôi an toàn -> NHƯNG thị trường nhiều biến "
        "động, đất nền chôn vốn khiến bạn mất thanh khoản -> VÌ VẬY, tòa căn hộ khai thác dòng tiền ngay "
        "biển Mỹ Khê này là chìa khóa tài chính tối ưu nhất."
    ),
    "5. Hành trình thu nhỏ của nhân vật": (
        "Kể câu chuyện về một nhà đầu tư từng đối mặt ngã rẽ khó khăn -> Vượt qua bẫy 'bánh vẽ tương lai' "
        "nhờ chuyển hướng sang mua giá trị khai thác thật -> Đạt tự do dòng tiền với tài sản triệu đô tại Đà Nẵng."
    ),
    "6. Vòng lặp mở (Open loop)": (
        "Mở đầu bằng nghịch lý gây tò mò tột độ (Ví dụ: 'Tại sao có người sẵn sàng chi 30 tỷ mua tòa nhà này "
        "trong khi lãi suất ngân hàng đang cao?') -> Dẫn dắt lôi cuốn qua số liệu thực chiến -> Khép lại vòng "
        "lặp ở cuối video để kích thích nhà đầu tư hành động ngay."
    ),
    "7. Chi tiết cụ thể, đánh vào giác quan": (
        "Đánh mạnh vào giác quan: ngửi thấy mùi gió biển Mỹ Khê cách vài bước chân, nghe tiếng ting ting "
        "120 triệu tiền thuê phòng đổ về tài khoản mùng 1 hàng tháng, ngắm nhìn tòa nhà 7 tầng full kính rực sáng."
    ),
    "8. Câu chuyện khách hàng (Người thật, số thật)": (
        "Dẫn dắt bằng câu chuyện thực tế của một khách hàng quen từ Hà Nội hoặc Sài Gòn, sở hữu tài sản này, "
        "vận hành tỷ lệ lấp đầy 95%, dòng tiền thật chứng minh qua sao kê ngân hàng."
    ),
    "9. Một ngày trong đời (Cảm giác sở hữu/an tâm)": (
        "Khắc họa một ngày thảnh thơi của chủ nhân: Thức dậy thong dong uống cà phê ngắm biển Đà Nẵng, "
        "không phải bận tâm quản lý vì đơn vị chuyên nghiệp vận hành, dòng tiền tự động chảy về tài khoản."
    ),
    "10. Câu chuyện khởi nguồn (Xây dựng niềm tin cá nhân)": (
        "Chia sẻ chân thành từ chính góc nhìn của Anh Hậu Dòng Tiền: Lý do anh kiên định chỉ chọn và phân tích "
        "BĐS dòng tiền thật tại Đà Nẵng để giúp các nhà đầu tư lớn bảo vệ vốn tuyệt đối trước chu kỳ thị trường."
    )
}

BRAND_SYSTEM_INSTRUCTION = (
    "Bạn là Giám đốc Sáng tạo và Trợ lý Truyền thông độc quyền cho thương hiệu 'Hậu Dòng Tiền Real Estate' "
    "tại Đà Nẵng. Anh Hậu là chuyên gia thực chiến phân khúc BĐS dòng tiền, đất ven biển, tòa căn hộ dịch vụ "
    "và khách sạn từ 10 - 50 tỷ đồng.\n\n"
    "NGUYÊN TẮC BRAND DNA BẮT BUỘC:\n"
    "1. Định vị: Uy quyền, bản lĩnh, sâu sắc, thực chiến, am hiểu tường tận thị trường Đà Nẵng.\n"
    "2. Triết lý đầu tư: 'Mua giá trị khai thác hiện hữu, không mua bánh vẽ tương lai'. BĐS dòng tiền ven biển "
    "chính là bức tường lửa vững chắc nhất bảo vệ vốn trước lạm phát.\n"
    "3. Cấu trúc kịch bản: Thời lượng chuẩn 35 - 45 giây (khoảng 110 - 140 từ tiếng Việt), nhịp điệu dứt khoát.\n"
    "   - 3 giây đầu (Hook): Giật tít cực mạnh, đánh thẳng nỗi đau hoặc con số doanh thu/vị trí đắt giá.\n"
    "   - Thân bài (Body): Cảm xúc trước - lý trí sau, minh chứng bằng số liệu cụ thể (diện tích, dòng tiền/tháng, tỷ suất).\n"
    "   - Kết bài (CTA): Kêu gọi dứt khoát kết nối với Anh Hậu để nhận hồ sơ pháp lý và thẩm định quy hoạch.\n"
    "4. BẮT BUỘC: Chỉ xuất duy nhất phần lời thoại để thu âm/lồng tiếng, tuyệt đối không chèn ký hiệu cảnh quay, "
    "không ngoặc đơn chú thích [Hook], [Body], [CTA] vào văn bản."
)


# ==============================================================================
# 4. TRẠM AI KỊCH BẢN & GEMINI VISION (GEMINI 3.8 FLASH)
# ==============================================================================
def generate_standard_script(api_key: str, content_type: str, framework_name: str, details: dict) -> str:
    """Sinh kịch bản video ngắn (35-45s) chuẩn cấu trúc kết hợp Storytelling Framework được chọn."""
    try:
        client = genai.Client(api_key=api_key)
        framework_guide = FRAMEWORK_GUIDES.get(framework_name, "")

        if content_type == "Giới thiệu Tài sản Dòng Tiền Thực Tế":
            prompt = (
                f"Hãy viết kịch bản video giới thiệu tài sản dòng tiền thực tế áp dụng phương pháp kể chuyện: "
                f"'{framework_name}'.\n"
                f"Hướng dẫn phương pháp: {framework_guide}\n\n"
                f"THÔNG SỐ BẤT ĐỘNG SẢN:\n"
                f"- Tên / Loại hình: {details.get('title', 'Tòa Căn Hộ Dịch Vụ')}\n"
                f"- Vị trí: {details.get('location', 'Gần biển Mỹ Khê, Ngũ Hành Sơn, Đà Nẵng')}\n"
                f"- Diện tích & Kết cấu: {details.get('spec', '120m2, 7 tầng thang máy, 16 phòng studio')}\n"
                f"- Mức giá chào bán: {details.get('price', '25 tỷ')}\n"
                f"- Doanh thu khai thác dòng tiền: {details.get('cashflow', '120 triệu/tháng')}\n"
                f"- Điểm mạnh pháp lý/vận hành: {details.get('highlights', 'Full phòng quanh năm, PCCC chuẩn nghiệm thu')}"
            )
        else:
            prompt = (
                f"Hãy viết kịch bản video chia sẻ tư duy/kinh nghiệm đầu tư BĐS dòng tiền áp dụng phương pháp kể chuyện: "
                f"'{framework_name}'.\n"
                f"Hướng dẫn phương pháp: {framework_guide}\n\n"
                f"THÔNG TIN CHỦ ĐỀ ĐẦU TƯ:\n"
                f"- Chủ đề cốt lõi: {details.get('topic', 'Đất nền phân lô vs Tòa căn hộ dòng tiền ven biển')}\n"
                f"- Góc nhìn thực chiến: {details.get('insight', 'Bất động sản sinh ra dòng tiền hàng tháng là bức tường lửa bảo vệ vốn trước lạm phát')}\n"
                f"- Bài học đúc kết: {details.get('advice', 'Đừng mua kỳ vọng tương lai mà hãy mua giá trị khai thác hiện hữu')}"
            )

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=BRAND_SYSTEM_INSTRUCTION,
                temperature=0.75,
                max_output_tokens=400
            )
        )
        return response.text.strip()
    except Exception as e:
        raise RuntimeError(f"Lỗi Gemini 3.8 Flash API: {str(e)}")


def learn_style_and_generate_script(
    api_key: str,
    video_sample_path: str,
    content_type: str,
    framework_name: str,
    details: dict
) -> tuple[str, str]:
    """Sử dụng Gemini Vision phân tích video mẫu kết hợp Storytelling Framework được chọn."""
    client = genai.Client(api_key=api_key)
    uploaded_file = None
    try:
        uploaded_file = client.files.upload(file=video_sample_path)
        while uploaded_file.state.name == "PROCESSING":
            time.sleep(2)
            uploaded_file = client.files.get(name=uploaded_file.name)
            
        if uploaded_file.state.name == "FAILED":
            raise RuntimeError("Gemini không thể giải mã video mẫu này. Hãy thử video dung lượng nhẹ hơn.")

        framework_guide = FRAMEWORK_GUIDES.get(framework_name, "")
        prompt = (
            f"BƯỚC 1: Hãy xem kỹ video mẫu được đính kèm và trích xuất DNA phong cách:\n"
            f"- Kỹ thuật giật Hook 3s đầu của người nói.\n"
            f"- Tốc độ nhả chữ, nhịp điệu ngắt nghỉ và cách dẫn dắt logic.\n"
            f"- Đòn chốt CTA kêu gọi hành động.\n\n"
            f"BƯỚC 2: Kết hợp DNA nhịp điệu từ video mẫu VÀ Phương pháp kể chuyện '{framework_name}' "
            f"({framework_guide}) để viết một kịch bản thoại mới chuẩn 35-45 giây (110-140 từ tiếng Việt) "
            f"cho dữ liệu tài sản sau:\n"
            f"- Loại nội dung: {content_type}\n"
            f"- Thông tin: {details}\n\n"
            f"ĐỊNH DẠNG ĐẦU RA BẮT BUỘC (phân tách bởi ===SCRIPT_SPLIT===):\n"
            f"[Tóm tắt ngắn gọn DNA học được từ video mẫu và cách vận dụng Framework {framework_name}]\n"
            f"===SCRIPT_SPLIT===\n"
            f"[DUY NHẤT lời thoại kịch bản hoàn chỉnh để lồng tiếng]"
        )

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=[uploaded_file, prompt],
            config=types.GenerateContentConfig(
                system_instruction=BRAND_SYSTEM_INSTRUCTION,
                temperature=0.75,
                max_output_tokens=650
            )
        )

        result_text = response.text.strip()
        if "===SCRIPT_SPLIT===" in result_text:
            dna_part, script_part = result_text.split("===SCRIPT_SPLIT===", 1)
            return dna_part.strip(), script_part.strip()
        else:
            return f"Đã kết hợp DNA từ video mẫu và Framework '{framework_name}'.", result_text

    except Exception as e:
        raise RuntimeError(f"Lỗi Gemini Vision Multimodal: {str(e)}")
    finally:
        if uploaded_file is not None:
            try:
                client.files.delete(name=uploaded_file.name)
            except Exception:
                pass


# ==============================================================================
# 5. TRẠM TỔNG HỢP GIỌNG ĐỌC (EDGE-TTS)
# ==============================================================================
async def _async_generate_voice(text: str, voice: str, rate: str, output_path: str):
    import edge_tts
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate)
    await communicate.save(output_path)

def generate_voiceover(text: str, voice: str, rate: str, output_path: str):
    try:
        asyncio.run(_async_generate_voice(text, voice, rate, output_path))
    except Exception as e:
        raise RuntimeError(f"Lỗi tổng hợp giọng đọc Edge-TTS: {str(e)}")


# ==============================================================================
# 6. TRẠM TRÍCH XUẤT PHỤ ĐỀ (WHISPER -> SRT)
# ==============================================================================
def format_timestamp_to_srt(seconds: float) -> str:
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    millis = int(td.microseconds / 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def transcribe_audio_to_srt(audio_path: str, output_srt_path: str, model_name: str = "base"):
    try:
        model = load_whisper_model(model_name)
        result = model.transcribe(audio_path, language="vi", task="transcribe")
        
        segments = result.get("segments", [])
        with open(output_srt_path, "w", encoding="utf-8") as srt_file:
            for idx, seg in enumerate(segments, start=1):
                start_time = format_timestamp_to_srt(seg["start"])
                end_time = format_timestamp_to_srt(seg["end"])
                text = seg["text"].strip()
                srt_file.write(f"{idx}\n{start_time} --> {end_time}\n{text}\n\n")
    except Exception as e:
        raise RuntimeError(f"Lỗi trích xuất phụ đề Whisper: {str(e)}")


# ==============================================================================
# 7. TRẠM BIÊN TẬP & NUNG SUB THÔNG MINH (FFMPEG PIPELINE 9:16 & 16:9)
# ==============================================================================
def render_final_video(
    raw_video_path: str,
    voice_audio_path: str,
    srt_path: str,
    logo_path: str,
    bgm_path: str,
    bgm_volume: float,
    output_path: str,
    aspect_ratio: str = "9:16",
    trim_start: float = 2.0,
    font_size: int = 18,
    margin_v: int = 130,
    enhance_color: bool = True
):
    safe_srt_path = Path(srt_path).resolve().as_posix()
    safe_srt_path = safe_srt_path.replace(":", r"\:")

    if aspect_ratio == "16:9":
        target_w, target_h = 1920, 1080
        logo_scale = "scale=220:-1"
        logo_overlay = "overlay=W-w-45:45"
    else:  # Mặc định 9:16 Shorts/Reels
        target_w, target_h = 1080, 1920
        logo_scale = "scale=180:-1"
        logo_overlay = "overlay=W-w-35:45"

    sub_filter = (
        f"subtitles='{safe_srt_path}':force_style="
        f"'Fontname=Arial,FontSize={font_size},Bold=1,"
        f"PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
        f"BorderStyle=1,Outline=2.6,Shadow=1,Alignment=2,MarginV={margin_v}'"
    )

    color_filter = "eq=contrast=1.12:brightness=0.03:saturation=1.22,unsharp=5:5:0.8:5:5:0.0" if enhance_color else "null"

    inputs = []
    filter_complex_parts = []
    current_input_index = 0

    # Input 0: Video gốc (loop tự động)
    inputs.extend(["-stream_loop", "-1", "-ss", str(trim_start), "-i", raw_video_path])
    video_input_idx = current_input_index
    current_input_index += 1

    # Input 1: Voiceover chính
    inputs.extend(["-i", voice_audio_path])
    voice_input_idx = current_input_index
    current_input_index += 1

    # Input Logo (Tùy chọn)
    logo_input_idx = None
    if logo_path and os.path.exists(logo_path):
        inputs.extend(["-i", logo_path])
        logo_input_idx = current_input_index
        current_input_index += 1

    # Input Nhạc nền BGM (Tùy chọn)
    bgm_input_idx = None
    if bgm_path and os.path.exists(bgm_path):
        inputs.extend(["-stream_loop", "-1", "-i", bgm_path])
        bgm_input_idx = current_input_index
        current_input_index += 1

    # Xử lý video filtergraph
    scale_crop_str = f"[{video_input_idx}:v]scale={target_w}:{target_h}:force_original_aspect_ratio=increase,crop={target_w}:{target_h},{color_filter}[v_base]"
    filter_complex_parts.append(scale_crop_str)

    if logo_input_idx is not None:
        filter_complex_parts.append(f"[{logo_input_idx}:v]{logo_scale}[logo_scaled]")
        filter_complex_parts.append(f"[v_base][logo_scaled]{logo_overlay}[v_with_logo]")
        filter_complex_parts.append(f"[v_with_logo]{sub_filter}[vout]")
    else:
        filter_complex_parts.append(f"[v_base]{sub_filter}[vout]")

    # Xử lý audio mix
    if bgm_input_idx is not None:
        filter_complex_parts.append(
            f"[{voice_input_idx}:a]volume=1.0[a_voice];"
            f"[{bgm_input_idx}:a]volume={bgm_volume:.2f}[a_bgm];"
            f"[a_voice][a_bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        )
        audio_map = "[aout]"
    else:
        audio_map = f"{voice_input_idx}:a"

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", ";".join(filter_complex_parts),
        "-map", "[vout]",
        "-map", audio_map,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "20",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_path
    ]

    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if process.returncode != 0:
        raise RuntimeError(f"FFmpeg gặp sự cố trong quá trình render:\n{process.stderr}")


# ==============================================================================
# 8. GIAO DIỆN CHÍNH ỨNG DỤNG STREAMLIT
# ==============================================================================
def main():
    st.markdown("""
    <div class="brand-header">
        <div class="brand-title">🏛️ HẬU DÒNG TIỀN REAL ESTATE • AUTO VIDEO STUDIO</div>
        <div class="brand-subtitle">Trợ Lý Dựng Phim Tự Động • Tích Hợp 10 Storytelling Frameworks & Gemini 3.8 Flash Vision</div>
    </div>
    """, unsafe_allow_html=True)

    if "generated_script" not in st.session_state:
        st.session_state.generated_script = ""
    if "extracted_dna" not in st.session_state:
        st.session_state.extracted_dna = ""

    col_left, col_right = st.columns([1.05, 1.15], gap="large")

    # --------------------------------------------------------------------------
    # CỘT TRÁI: CẤU HÌNH ÂM THANH & TRẠM AI STORYTELLING
    # --------------------------------------------------------------------------
    with col_left:
        # Card 1: Khởi tạo & Cấu hình Âm thanh
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">⚙️ 1. Cấu Hình Khởi Tạo & Nguồn Âm Thanh</div>', unsafe_allow_html=True)
        
        api_key = st.text_input(
            "Gemini API Key:",
            type="password",
            value=st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", "")),
            placeholder="Dán Gemini API Key để kích hoạt Vision & AI Storytelling...",
            help="Sử dụng model Gemini 3.8 Flash tốc độ cao."
        )

        audio_source_type = st.radio(
            "Nguồn giọng thuyết minh:",
            options=["Giọng AI Tự Động (Edge-TTS)", "Tải file ghi âm giọng thật (.mp3/.wav/.m4a)"],
            horizontal=True
        )

        uploaded_custom_audio = None
        voice_choice = "vi-VN-NamMinhNeural"
        voice_speed = "+10%"

        if audio_source_type == "Giọng AI Tự Động (Edge-TTS)":
            sub_col1, sub_col2 = st.columns(2)
            with sub_col1:
                voice_choice = st.selectbox(
                    "MC Thuyết Minh:",
                    options=["vi-VN-NamMinhNeural", "vi-VN-HoaiMyNeural"],
                    index=0,
                    format_func=lambda x: "Nam Minh (Trầm ấm, Uy lực)" if "NamMinh" in x else "Hoài My (Truyền cảm, Sang trọng)"
                )
            with sub_col2:
                voice_speed = st.select_slider(
                    "Tốc độ đọc giọng AI:",
                    options=["-10%", "+0%", "+10%", "+15%", "+20%"],
                    value="+10%"
                )
        else:
            uploaded_custom_audio = st.file_uploader(
                "Tải lên file ghi âm giọng đọc (.mp3, .wav, .m4a):",
                type=["mp3", "wav", "m4a"]
            )

        st.write("---")
        uploaded_bgm = st.file_uploader(
            "🎵 Nhạc nền Lofi / Cinematic (Tùy chọn .mp3, .wav):",
            type=["mp3", "wav", "m4a"]
        )
        bgm_volume_pct = st.slider(
            "Âm lượng nhạc nền (% so với giọng đọc):",
            min_value=5, max_value=20, value=12, step=1, format="%d%%"
        )
        bgm_volume_float = bgm_volume_pct / 100.0

        st.markdown('</div>', unsafe_allow_html=True)

        # Card 2: Trạm AI Storytelling & Vision
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">✍️ 2. Trạm AI Kịch Bản & 10 Storytelling Frameworks</div>', unsafe_allow_html=True)
        
        content_type = st.radio(
            "Định hướng kịch bản BĐS dòng tiền:",
            options=["Giới thiệu Tài sản Dòng Tiền Thực Tế", "Chia sẻ Tư Duy & Kinh Nghiệm Đầu Tư"],
            horizontal=True
        )

        # LỰA CHỌN 10 PHƯƠNG PHÁP KỂ CHUYỆN (STORYTELLING FRAMEWORKS)
        selected_framework = st.selectbox(
            "🎯 Chọn Phương pháp kể chuyện (Storytelling Framework):",
            options=list(FRAMEWORK_GUIDES.keys()),
            index=0
        )
        st.caption(f"💡 *Nguyên lý áp dụng:* {FRAMEWORK_GUIDES[selected_framework]}")

        payload_details = {}
        if content_type == "Giới thiệu Tài sản Dòng Tiền Thực Tế":
            c1, c2 = st.columns(2)
            with c1:
                payload_details['title'] = st.text_input("Tên/Loại hình BĐS:", "Tòa Căn Hộ Dịch Vụ Ven Biển")
                payload_details['location'] = st.text_input("Vị trí đắc địa:", "Khu An Thượng, Ngũ Hành Sơn, Đà Nẵng")
                payload_details['price'] = st.text_input("Mức giá chuyển nhượng:", "28.5 Tỷ (TLCC)")
            with c2:
                payload_details['spec'] = st.text_input("Quy mô kết cấu:", "110m2, 6 tầng, 14 căn hộ full nội thất")
                payload_details['cashflow'] = st.text_input("Dòng tiền khai thác:", "115 Triệu/tháng (Lợi suất ~5%)")
                payload_details['highlights'] = st.text_input("Điểm nhấn pháp lý/vận hành:", "Sổ hồng hoàn công, full PCCC, tỷ lệ lấp đầy 95%")
        else:
            payload_details['topic'] = st.text_input("Chủ đề tư duy cốt lõi:", "Tại sao giới nhà giàu Đà Nẵng săn lùng BĐS dòng tiền thay vì lướt sóng đất nền?")
            payload_details['insight'] = st.text_area("Luận điểm & Thực chiến:", "Đất nền có thể đóng băng 3-5 năm chôn vốn. BĐS dòng tiền vừa giữ giá đất ven biển, vừa tự trả lãi ngân hàng và cung cấp thu nhập thụ động đều đặn.")
            payload_details['advice'] = st.text_input("Lời đúc kết cho nhà đầu tư:", "Đừng mua hy vọng tăng giá bằng niềm tin, hãy mua dòng tiền thực tế.")

        # TÍNH NĂNG HỌC PHONG CÁCH TỪ VIDEO MẪU BẰNG GEMINI VISION
        with st.expander("🧠 Học Phong Cách Từ Video Mẫu (Gemini Vision - Tùy Chọn)", expanded=False):
            st.caption("Tải lên 1 video triệu view để Gemini bóc tách nhịp điệu mở đầu, kết hợp cùng Framework đã chọn.")
            ref_video_file = st.file_uploader(
                "Tải lên video mẫu phong cách (.mp4, .mov):",
                type=["mp4", "mov"],
                key="ref_video_uploader"
            )

        btn_c1, btn_c2 = st.columns(2)
        with btn_c1:
            gen_standard_btn = st.button("✨ TẠO KỊCH BẢN THEO FRAMEWORK", use_container_width=True)
        with btn_c2:
            gen_vision_btn = st.button("🔬 HỌC DNA & TẠO KỊCH BẢN", use_container_width=True)

        # Xử lý tạo kịch bản theo Storytelling Framework
        if gen_standard_btn:
            if not api_key:
                st.error("⚠️ Vui lòng điền Gemini API Key để khởi chạy Trạm AI.")
            else:
                with st.spinner(f"Gemini 3.8 Flash đang ứng dụng '{selected_framework}' biên soạn kịch bản..."):
                    try:
                        generated_txt = generate_standard_script(api_key, content_type, selected_framework, payload_details)
                        st.session_state.generated_script = generated_txt
                        st.session_state.extracted_dna = ""
                        st.success("✅ Đã tạo kịch bản sắc bén chuẩn Brand DNA thành công!")
                    except Exception as err:
                        st.error(str(err))

        # Xử lý tạo kịch bản học phong cách video mẫu kết hợp Framework
        if gen_vision_btn:
            if not api_key:
                st.error("⚠️ Vui lòng điền Gemini API Key để chạy tính năng Vision.")
            elif not ref_video_file:
                st.warning("⚠️ Bạn chưa tải lên Video Mẫu trong mục mở rộng bên trên!")
            else:
                with st.spinner("🧠 Gemini Vision đang phân tích nhịp điệu video mẫu và hòa quyện cùng Storytelling Framework..."):
                    try:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_ref:
                            tmp_ref.write(ref_video_file.read())
                            tmp_ref_path = tmp_ref.name

                        dna_res, script_res = learn_style_and_generate_script(
                            api_key=api_key,
                            video_sample_path=tmp_ref_path,
                            content_type=content_type,
                            framework_name=selected_framework,
                            details=payload_details
                        )

                        if os.path.exists(tmp_ref_path):
                            os.remove(tmp_ref_path)

                        st.session_state.extracted_dna = dna_res
                        st.session_state.generated_script = script_res
                        st.success("🎉 Đã học DNA từ video mẫu và áp dụng Framework thành công!")
                    except Exception as vision_err:
                        st.error(str(vision_err))

        if st.session_state.extracted_dna:
            st.markdown(f'<div class="dna-box">🧬 <b>DNA & Framework Đã Áp Dụng:</b><br>{st.session_state.extracted_dna}</div>', unsafe_allow_html=True)

        st.session_state.generated_script = st.text_area(
            "Lời thoại kịch bản (Bạn có thể tinh chỉnh trực tiếp bên dưới trước khi nung video):",
            value=st.session_state.generated_script,
            height=130
        )
        st.markdown('</div>', unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # CỘT PHẢI: TIMELINE STUDIO & DỰNG PHIM ĐA ĐỊNH DẠNG
    # --------------------------------------------------------------------------
    with col_right:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🎬 3. Timeline Studio: Nạp Tài Nguyên & Dựng Phim</div>', unsafe_allow_html=True)

        aspect_ratio_selection = st.radio(
            "📐 Chọn định dạng khung hình xuất bản:",
            options=[
                "Shorts / TikTok / Reels (9:16 - 1080x1920)",
                "YouTube Video Ngang (16:9 - 1920x1080)"
            ],
            index=0,
            horizontal=True
        )
        is_16_9 = "16:9" in aspect_ratio_selection
        ratio_tag = "16:9" if is_16_9 else "9:16"

        uploaded_video = st.file_uploader("Tải lên Video thực tế thô (MP4/MOV):", type=["mp4", "mov", "m4v"])
        uploaded_logo = st.file_uploader("Logo thương hiệu 'Hậu Dòng Tiền' (File PNG trong suốt - Tùy chọn):", type=["png"])

        with st.expander("🛠️ Tùy Chỉnh Biên Tập & Phụ Đề Tự Động", expanded=True):
            edit_c1, edit_c2 = st.columns(2)
            with edit_c1:
                trim_start_sec = st.slider("Cắt bỏ phần thừa đầu video (Auto-trim giây):", 0.0, 5.0, 2.0, 0.1)
                default_font_size = 22 if is_16_9 else 18
                font_size = st.slider("Cỡ chữ phụ đề (Subtitle Size):", 12, 32, default_font_size)
            with edit_c2:
                default_margin_v = 65 if is_16_9 else 130
                margin_vertical = st.slider("Khoảng cách phụ đề từ đáy (Margin Bottom):", 40, 250, default_margin_v)
                enhance_color = st.checkbox("Bộ lọc tăng sáng, tương phản & làm nét video", value=True)

        button_label = f"🚀 XUẤT BẢN VIDEO CHUẨN {'YOUTUBE 16:9' if is_16_9 else 'SHORTS / REELS 9:16'}"
        render_btn = st.button(button_label, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # ----------------------------------------------------------------------
        # QUY TRÌNH RENDER HỆ THỐNG
        # ----------------------------------------------------------------------
        if render_btn:
            has_voice = False
            if audio_source_type == "Giọng AI Tự Động (Edge-TTS)":
                if st.session_state.generated_script.strip():
                    has_voice = True
                else:
                    st.error("⚠️ Bạn đang chọn Giọng AI nhưng kịch bản thoại đang trống! Vui lòng tạo kịch bản ở Cột trái.")
            else:
                if uploaded_custom_audio is not None:
                    has_voice = True
                else:
                    st.error("⚠️ Bạn đang chọn Tải file ghi âm nhưng chưa nạp file âm thanh (.mp3/.wav).")

            if not uploaded_video:
                st.error("⚠️ Vui lòng tải lên ít nhất 1 video quay thực tế tài sản.")
            elif has_voice:
                progress_bar = st.progress(0)
                status_box = st.empty()

                with tempfile.TemporaryDirectory() as temp_dir:
                    try:
                        # 1. Lưu file video thô và logo
                        status_box.info("📥 [1/4] Đang tiếp nhận tài nguyên đầu vào...")
                        temp_video_path = os.path.join(temp_dir, "raw_input.mp4")
                        with open(temp_video_path, "wb") as f:
                            f.write(uploaded_video.read())

                        temp_logo_path = ""
                        if uploaded_logo:
                            temp_logo_path = os.path.join(temp_dir, "logo.png")
                            with open(temp_logo_path, "wb") as f:
                                f.write(uploaded_logo.read())

                        temp_bgm_path = ""
                        if uploaded_bgm:
                            temp_bgm_path = os.path.join(temp_dir, "bgm.mp3")
                            with open(temp_bgm_path, "wb") as f:
                                f.write(uploaded_bgm.read())
                        progress_bar.progress(25)

                        # 2. Xử lý âm thanh giọng đọc (Voiceover)
                        temp_voice_path = os.path.join(temp_dir, "voice.mp3")
                        if audio_source_type == "Giọng AI Tự Động (Edge-TTS)":
                            status_box.info("🎙️ [2/4] Trạm Edge-TTS đang tổng hợp giọng đọc AI truyền cảm...")
                            generate_voiceover(
                                text=st.session_state.generated_script,
                                voice=voice_choice,
                                rate=voice_speed,
                                output_path=temp_voice_path
                            )
                        else:
                            status_box.info("🎙️ [2/4] Đang xử lý file thu âm giọng thật của bạn...")
                            with open(temp_voice_path, "wb") as f:
                                f.write(uploaded_custom_audio.read())
                        progress_bar.progress(50)

                        # 3. Trích xuất phụ đề tự động từ Whisper
                        status_box.info("🧠 [3/4] Whisper AI đang trích xuất phụ đề từng khung hình chính xác...")
                        temp_srt_path = os.path.join(temp_dir, "subtitles.srt")
                        transcribe_audio_to_srt(
                            audio_path=temp_voice_path,
                            output_srt_path=temp_srt_path,
                            model_name="base"
                        )
                        progress_bar.progress(75)

                        # 4. Pipeline FFmpeg render video hoàn thiện
                        status_box.info(f"⚡ [4/4] FFmpeg đang cắt thừa {trim_start_sec}s, Color Grade, dập Logo và nung Hardsub...")
                        final_output_path = os.path.join(temp_dir, "hau_dong_tien_final.mp4")
                        render_final_video(
                            raw_video_path=temp_video_path,
                            voice_audio_path=temp_voice_path,
                            srt_path=temp_srt_path,
                            logo_path=temp_logo_path,
                            bgm_path=temp_bgm_path,
                            bgm_volume=bgm_volume_float,
                            output_path=final_output_path,
                            aspect_ratio=ratio_tag,
                            trim_start=trim_start_sec,
                            font_size=font_size,
                            margin_v=margin_vertical,
                            enhance_color=enhance_color
                        )
                        progress_bar.progress(100)
                        status_box.success(f"🎉 TUYỆT VỜI! Video BĐS Dòng Tiền định dạng {ratio_tag} đã xuất bản hoàn tất!")

                        # Đọc video thành phẩm ra bộ nhớ
                        with open(final_output_path, "rb") as f:
                            video_bytes = f.read()

                        st.markdown('<div class="section-card">', unsafe_allow_html=True)
                        st.markdown(f'<div class="section-title">📺 Video Thành Phẩm Hoàn Thiện ({ratio_tag})</div>', unsafe_allow_html=True)
                        st.video(video_bytes)

                        download_filename = f"HauDongTien_{'YouTube_16x9' if is_16_9 else 'Shorts_9x16'}.mp4"
                        st.download_button(
                            label=f"⬇️ TẢI XUỐNG VIDEO ({download_filename})",
                            data=video_bytes,
                            file_name=download_filename,
                            mime="video/mp4",
                            use_container_width=True
                        )
                        st.markdown('</div>', unsafe_allow_html=True)

                    except Exception as process_error:
                        status_box.empty()
                        st.error(f"❌ Xảy ra sự cố trong quá trình xử lý: {str(process_error)}")


if __name__ == "__main__":
    main()