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
    page_title="Hậu Dòng Tiền Real Estate | Auto Video Studio & Vision AI",
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
    
    /* Header thương hiệu */
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
    
    /* Badge DNA Style */
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
# 3. TRẠM AI & VISION MULTIMODAL (GEMINI 3.8 FLASH)
# ==============================================================================
def generate_standard_script(api_key: str, content_type: str, details: dict) -> str:
    """Sinh kịch bản video ngắn (35-45s) chuẩn Hook-Body-CTA từ thông số văn bản."""
    try:
        client = genai.Client(api_key=api_key)
        
        system_instruction = (
            "Bạn là Giám đốc Marketing và Chuyên gia truyền thông kỳ cựu của thương hiệu "
            "'Hậu Dòng Tiền Real Estate' tại Đà Nẵng. Bạn chuyên phân khúc BĐS dòng tiền, "
            "tòa căn hộ dịch vụ và khách sạn ven biển từ 10 - 50 tỷ đồng.\n"
            "Hãy viết kịch bản video giọng đọc (voiceover) chuẩn 35 - 45 giây "
            "(tầm 110 - 140 từ tiếng Việt), nhịp điệu dứt khoát, uy quyền, số liệu sắc nét.\n"
            "Cấu trúc kịch bản bắt buộc:\n"
            "1. HOOK (0-5s): Đánh thẳng vào nỗi đau hoặc con số dòng tiền/vị trí đắt giá.\n"
            "2. BODY (5-35s): Thông số cụ thể, bài toán khai thác, tỷ suất chống lạm phát.\n"
            "3. CTA (35-42s): Kêu gọi kết nối trực tiếp với Hậu Dòng Tiền để nhận hồ sơ pháp lý.\n"
            "LƯU Ý: Chỉ xuất duy nhất phần lời thoại để đọc, không thêm ký hiệu cảnh quay hay ngoặc đơn chú thích."
        )

        if content_type == "Giới thiệu Tài sản Dòng Tiền Thực Tế":
            prompt = (
                f"Tạo kịch bản giới thiệu tài sản thực tế với các thông số sau:\n"
                f"- Tên / Loại tài sản: {details.get('title', 'Tòa Căn Hộ Dịch Vụ')}\n"
                f"- Vị trí: {details.get('location', 'Gần biển Mỹ Khê, Ngũ Hành Sơn, Đà Nẵng')}\n"
                f"- Diện tích & Kết cấu: {details.get('spec', '120m2, 7 tầng thang máy, 16 phòng studio')}\n"
                f"- Giá bán: {details.get('price', '25 tỷ')}\n"
                f"- Doanh thu khai thác dòng tiền: {details.get('cashflow', '120 triệu/tháng')}\n"
                f"- Điểm mạnh: {details.get('highlights', 'Full phòng quanh năm, PCCC chuẩn nghiệm thu')}"
            )
        else:
            prompt = (
                f"Tạo kịch bản video chia sẻ tư duy/kinh nghiệm đầu tư BĐS dòng tiền:\n"
                f"- Chủ đề cốt lõi: {details.get('topic', 'Đất nền phân lô vs Tòa căn hộ dòng tiền ven biển')}\n"
                f"- Góc nhìn thực chiến: {details.get('insight', 'Bất động sản sinh ra dòng tiền hàng tháng là bức tường lửa bảo vệ vốn trước lạm phát')}\n"
                f"- Bài học/Khuyên nhủ: {details.get('advice', 'Đừng mua kỳ vọng tương lai mà hãy mua giá trị khai thác hiện hữu')}"
            )

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7,
                max_output_tokens=350
            )
        )
        return response.text.strip()
    except Exception as e:
        raise RuntimeError(f"Lỗi khi gọi Gemini Text API: {str(e)}")


def learn_style_and_generate_script(
    api_key: str,
    video_sample_path: str,
    content_type: str,
    details: dict
) -> tuple[str, str]:
    """
    Sử dụng Gemini Vision Multimodal để phân tích video mẫu,
    trích xuất DNA (Hook, Body, CTA) và áp dụng vào thông số BĐS mới.
    Trả về: (dna_summary, generated_script)
    """
    client = genai.Client(api_key=api_key)
    uploaded_file = None
    try:
        # 1. Tải video mẫu lên Gemini Files API
        uploaded_file = client.files.upload(file=video_sample_path)
        
        # 2. Chờ xử lý video trên hạ tầng Gemini
        while uploaded_file.state.name == "PROCESSING":
            time.sleep(2)
            uploaded_file = client.files.get(name=uploaded_file.name)
            
        if uploaded_file.state.name == "FAILED":
            raise RuntimeError("Gemini không thể xử lý video mẫu này. Hãy thử video có dung lượng nhỏ hơn.")

        # 3. Yêu cầu phân tích DNA và viết kịch bản mới
        prompt = (
            "Bạn là Giám đốc Sáng tạo cấp cao của thương hiệu 'Hậu Dòng Tiền Real Estate' tại Đà Nẵng "
            "(chuyên BĐS dòng tiền, tòa căn hộ, khách sạn biển 10 - 50 tỷ).\n\n"
            "HÃY THỰC HIỆN 2 BƯỚC SAU:\n"
            "BƯỚC 1 - TRÍCH XUẤT DNA TỪ VIDEO MẪU:\n"
            "- Phân tích kỹ thuật giật Hook 3-5 giây đầu (câu hỏi, con số sốc, nỗi đau hay hình ảnh tương phản).\n"
            "- Phân tích nhịp điệu Body (cách dẫn dắt thông tin, tốc độ nhả chữ, tính liên kết logic).\n"
            "- Phân tích đòn chốt CTA (cách thúc giục nhà đầu tư để lại tin nhắn hoặc gọi điện).\n\n"
            "BƯỚC 2 - TẠO KỊCH BẢN THOẠI MỚI DỰA TRÊN DNA VỪA HỌC:\n"
            f"- Định dạng nội dung: {content_type}\n"
            f"- Dữ liệu thông số BĐS mới: {details}\n"
            "- Yêu cầu: Thời lượng thoại chuẩn 35 - 45 giây (110 - 140 từ tiếng Việt), "
            "giữ nguyên cấu trúc tâm lý và nhịp độ từ video mẫu nhưng thay bằng thông số tài sản của Hậu Dòng Tiền.\n\n"
            "ĐỊNH DẠNG ĐẦU RA BẮT BUỘC:\n"
            "Hãy phân tách 2 phần bằng dòng chữ '===SCRIPT_SPLIT===':\n"
            "[Tóm tắt ngắn gọn DNA học được: Hook là gì, Body triển khai thế nào, CTA ra sao]\n"
            "===SCRIPT_SPLIT===\n"
            "[DUY NHẤT lời thoại kịch bản để thu âm/lồng tiếng, không kèm ghi chú đạo diễn hay nhãn phân đoạn]"
        )

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=[uploaded_file, prompt],
            config=types.GenerateContentConfig(
                temperature=0.75,
                max_output_tokens=600
            )
        )

        result_text = response.text.strip()
        if "===SCRIPT_SPLIT===" in result_text:
            dna_part, script_part = result_text.split("===SCRIPT_SPLIT===", 1)
            return dna_part.strip(), script_part.strip()
        else:
            return "Đã áp dụng trực tiếp DNA nhịp điệu từ video mẫu vào kịch bản.", result_text

    except Exception as e:
        raise RuntimeError(f"Lỗi Gemini Vision Multimodal: {str(e)}")
    finally:
        # Xóa file video khỏi Cloud để tối ưu bảo mật và bộ nhớ
        if uploaded_file is not None:
            try:
                client.files.delete(name=uploaded_file.name)
            except Exception:
                pass


# ==============================================================================
# 4. TRẠM TỔNG HỢP GIỌNG ĐỌC (EDGE-TTS)
# ==============================================================================
async def _async_generate_voice(text: str, voice: str, rate: str, output_path: str):
    """Xử lý bất đồng bộ cho Edge-TTS."""
    import edge_tts
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate)
    await communicate.save(output_path)

def generate_voiceover(text: str, voice: str, rate: str, output_path: str):
    """Hàm wrapper đồng bộ để gọi Edge-TTS."""
    try:
        asyncio.run(_async_generate_voice(text, voice, rate, output_path))
    except Exception as e:
        raise RuntimeError(f"Lỗi chuyển văn bản thành giọng đọc (Edge-TTS): {str(e)}")


# ==============================================================================
# 5. TRẠM TRÍCH XUẤT PHỤ ĐỀ (WHISPER -> SRT)
# ==============================================================================
def format_timestamp_to_srt(seconds: float) -> str:
    """Chuyển đổi giây thành định dạng thời gian chuẩn SRT: HH:MM:SS,mmm"""
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    millis = int(td.microseconds / 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def transcribe_audio_to_srt(audio_path: str, output_srt_path: str, model_name: str = "base"):
    """Dùng Whisper bóc tách giọng nói từ audio sang file SRT."""
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
# 6. TRẠM BIÊN TẬP & NUNG SUB THÔNG MINH (FFMPEG PIPELINE 9:16 & 16:9)
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
    """
    Pipeline FFmpeg xử lý video hoàn chỉnh:
    - Hỗ trợ định dạng 9:16 (1080x1920) hoặc 16:9 (1920x1080)
    - Auto-trim đoạn thừa đầu video (mặc định 2s)
    - Tăng tương phản, độ sáng và làm nét (Color grade & unsharp)
    - Tự động co giãn và gắn Logo thương hiệu ở góc phải trên
    - Nung cứng Hardsub viền đen dày nổi bật
    - Hòa âm giọng đọc với nhạc nền Lofi/Cinematic (nếu có)
    """
    safe_srt_path = Path(srt_path).resolve().as_posix()
    safe_srt_path = safe_srt_path.replace(":", r"\:")

    if aspect_ratio == "16:9":
        target_w, target_h = 1920, 1080
        logo_scale = "scale=220:-1"
        logo_overlay = "overlay=W-w-45:45"
    else:  # Mặc định 9:16
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

    # Input 1: Giọng đọc chính (Voiceover)
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

    # Xử lý video filter
    scale_crop_str = f"[{video_input_idx}:v]scale={target_w}:{target_h}:force_original_aspect_ratio=increase,crop={target_w}:{target_h},{color_filter}[v_base]"
    filter_complex_parts.append(scale_crop_str)

    if logo_input_idx is not None:
        filter_complex_parts.append(f"[{logo_input_idx}:v]{logo_scale}[logo_scaled]")
        filter_complex_parts.append(f"[v_base][logo_scaled]{logo_overlay}[v_with_logo]")
        filter_complex_parts.append(f"[v_with_logo]{sub_filter}[vout]")
    else:
        filter_complex_parts.append(f"[v_base]{sub_filter}[vout]")

    # Xử lý audio mixing
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
        raise RuntimeError(f"FFmpeg gặp lỗi trong quá trình render:\n{process.stderr}")


# ==============================================================================
# 7. GIAO DIỆN CHÍNH ỨNG DỤNG STREAMLIT
# ==============================================================================
def main():
    st.markdown("""
    <div class="brand-header">
        <div class="brand-title">🏛️ HẬU DÒNG TIỀN REAL ESTATE • AUTO VIDEO STUDIO</div>
        <div class="brand-subtitle">Trợ Lý Dựng Phim Tự Động • Tích Hợp Gemini 3.8 Flash Vision Học Phong Cách Video Mẫu</div>
    </div>
    """, unsafe_allow_html=True)

    if "generated_script" not in st.session_state:
        st.session_state.generated_script = ""
    if "extracted_dna" not in st.session_state:
        st.session_state.extracted_dna = ""

    col_left, col_right = st.columns([1.05, 1.15], gap="large")

    # --------------------------------------------------------------------------
    # CỘT TRÁI: NGUỒN ÂM THANH & TRẠM AI KỊCH BẢN / VISION
    # --------------------------------------------------------------------------
    with col_left:
        # Card 1: Khởi tạo & Cấu hình Âm thanh
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">⚙️ 1. Cấu Hình Khởi Tạo & Âm Thanh</div>', unsafe_allow_html=True)
        
        api_key = st.text_input(
            "Gemini API Key:",
            type="password",
            value=st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", "")),
            placeholder="Dán Gemini API Key để kích hoạt Vision & Viết kịch bản...",
            help="Sử dụng model Gemini 3.8 Flash tốc độ cao."
        )

        audio_source_type = st.radio(
            "Nguồn giọng thuyết minh:",
            options=["Giọng AI Tự Động (Edge-TTS)", "Tải file ghi âm giọng thật (.mp3/.wav)"],
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
            min_value=5, max_value=40, value=15, step=1, format="%d%%"
        )
        bgm_volume_float = bgm_volume_pct / 100.0

        st.markdown('</div>', unsafe_allow_html=True)

        # Card 2: Trạm AI Kịch Bản & Học Phong Cách Vision
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">✍️ 2. Trạm AI Kịch Bản & Gemini Vision (Gemini 3.8 Flash)</div>', unsafe_allow_html=True)
        
        content_type = st.radio(
            "Định hướng kịch bản BĐS dòng tiền:",
            options=["Giới thiệu Tài sản Dòng Tiền Thực Tế", "Chia sẻ Tư Duy & Kinh Nghiệm Đầu Tư"],
            horizontal=True
        )

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

        # TÍNH NĂNG MỚI: HỌC PHONG CÁCH TỪ VIDEO MẪU BẰNG GEMINI VISION
        with st.expander("🧠 Học Phong Cách Từ Video Mẫu (Gemini Vision - Tùy Chọn)", expanded=False):
            st.caption("Tải lên 1 video ngắn (TikTok/Reels/Shorts) có lượt xem cao để Gemini phân tích công thức Hook - Body - CTA.")
            ref_video_file = st.file_uploader(
                "Tải lên video mẫu phong cách (.mp4, .mov):",
                type=["mp4", "mov"],
                key="ref_video_uploader"
            )

        btn_c1, btn_c2 = st.columns(2)
        with btn_c1:
            gen_standard_btn = st.button("✨ TẠO KỊCH BẢN TIÊU CHUẨN", use_container_width=True)
        with btn_c2:
            gen_vision_btn = st.button("🔬 HỌC DNA & TẠO KỊCH BẢN", use_container_width=True)

        # Xử lý sinh kịch bản tiêu chuẩn
        if gen_standard_btn:
            if not api_key:
                st.error("⚠️ Vui lòng điền Gemini API Key để khởi chạy Trạm AI.")
            else:
                with st.spinner("Gemini 3.8 Flash đang tổng hợp kịch bản 35-45s..."):
                    try:
                        generated_txt = generate_standard_script(api_key, content_type, payload_details)
                        st.session_state.generated_script = generated_txt
                        st.session_state.extracted_dna = ""
                        st.success("✅ Đã tạo kịch bản sắc bén thành công!")
                    except Exception as err:
                        st.error(str(err))

        # Xử lý sinh kịch bản học phong cách từ video mẫu qua Gemini Vision
        if gen_vision_btn:
            if not api_key:
                st.error("⚠️ Vui lòng điền Gemini API Key để chạy tính năng Vision.")
            elif not ref_video_file:
                st.warning("⚠️ Bạn chưa tải lên Video Mẫu trong mục mở rộng bên trên!")
            else:
                with st.spinner("🧠 Gemini Vision đang xem video mẫu, giải mã DNA nhịp điệu và viết kịch bản..."):
                    try:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_ref:
                            tmp_ref.write(ref_video_file.read())
                            tmp_ref_path = tmp_ref.name

                        dna_res, script_res = learn_style_and_generate_script(
                            api_key=api_key,
                            video_sample_path=tmp_ref_path,
                            content_type=content_type,
                            details=payload_details
                        )

                        if os.path.exists(tmp_ref_path):
                            os.remove(tmp_ref_path)

                        st.session_state.extracted_dna = dna_res
                        st.session_state.generated_script = script_res
                        st.success("🎉 Đã học DNA từ video mẫu và chuyển hóa kịch bản thành công!")
                    except Exception as vision_err:
                        st.error(str(vision_err))

        if st.session_state.extracted_dna:
            st.markdown(f'<div class="dna-box">🧬 <b>DNA Phong Cách Đã Trích Xuất:</b><br>{st.session_state.extracted_dna}</div>', unsafe_allow_html=True)

        st.session_state.generated_script = st.text_area(
            "Lời thoại kịch bản (Bạn có thể tinh chỉnh trực tiếp bên dưới):",
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