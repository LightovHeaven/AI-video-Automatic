import os
import sys
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
    page_title="Hậu Dòng Tiền Real Estate | Auto Video Studio",
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
    
    /* Thanh tiêu đề chính */
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
    
    /* Card style */
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
# 3. TRẠM AI VIẾT KỊCH BẢN (GEMINI 2.5 FLASH)
# ==============================================================================
def generate_real_estate_script(api_key: str, content_type: str, details: dict) -> str:
    """Sinh kịch bản video ngắn (35-45s) chuẩn cấu trúc Hook-Body-CTA qua Gemini 2.5 Flash."""
    try:
        client = genai.Client(api_key=api_key)
        
        system_instruction = (
            "Bạn là Giám đốc Marketing và Chuyên gia truyền thông kỳ cựu của thương hiệu "
            "'Hậu Dòng Tiền Real Estate' tại Đà Nẵng. Bạn chuyên phân khúc BĐS dòng tiền, "
            "tòa căn hộ dịch vụ và khách sạn ven biển từ 10 - 50 tỷ đồng.\n"
            "Hãy viết kịch bản video ngắn dạng giọng đọc (voiceover) chuẩn 35 - 45 giây "
            "(tầm 110 - 140 từ tiếng Việt), nhịp điệu dứt khoát, quyền lực, đáng tin cậy.\n"
            "Cấu trúc kịch bản bắt buộc:\n"
            "1. HOOK (0-5s): Đánh thẳng vào nỗi đau hoặc con số dòng tiền/vị trí đắt giá.\n"
            "2. BODY (5-35s): Thông số sắc bén, bài toán khai thác, tiềm năng chống lạm phát.\n"
            "3. CTA (35-42s): Kêu gọi kết nối trực tiếp với Hậu Dòng Tiền để thẩm định hồ sơ pháp lý.\n"
            "LƯU Ý QUAN TRỌNG: Chỉ xuất duy nhất phần lời thoại để đọc, không thêm bất kỳ ký hiệu cảnh quay, "
            "lời mở đầu, ngoặc đơn chú thích hay [Hook]/[Body] vào trong văn bản."
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
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7,
                max_output_tokens=300
            )
        )
        return response.text.strip()
    except Exception as e:
        raise RuntimeError(f"Lỗi khi gọi Gemini API: {str(e)}")


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
# 6. TRẠM BIÊN TẬP & NUNG SUB THÔNG MINH (FFMPEG PIPELINE)
# ==============================================================================
def render_final_video(
    raw_video_path: str,
    audio_path: str,
    srt_path: str,
    logo_path: str,
    output_path: str,
    trim_start: float = 0.0,
    font_size: int = 18,
    margin_v: int = 130,
    enhance_color: bool = True
):
    """
    Xử lý toàn bộ pipeline video bằng FFmpeg:
    - Auto-trim đầu video
    - Scale & Crop thành 9:16 chuẩn TikTok/Shorts (1080x1920)
    - Tăng sáng, tăng tương phản và làm nét (Color enhance & unsharp)
    - Đóng dấu Logo thương hiệu ở góc phải trên
    - Nung cứng Hardsub viền đen dày nổi bật
    - Thay thế audio gốc bằng giọng đọc AI (-shortest)
    """
    # Chuẩn hóa đường dẫn SRT để tránh lỗi escape dấu gạch chéo ngược trên Windows
    safe_srt_path = Path(srt_path).resolve().as_posix()
    safe_srt_path = safe_srt_path.replace(":", r"\:")

    # Bộ lọc phụ đề ASS style
    sub_filter = (
        f"subtitles='{safe_srt_path}':force_style="
        f"'Fontname=Arial,FontSize={font_size},Bold=1,"
        f"PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
        f"BorderStyle=1,Outline=2.6,Shadow=1,Alignment=2,MarginV={margin_v}'"
    )

    # Bộ lọc màu & sắc nét
    color_filter = "eq=contrast=1.12:brightness=0.03:saturation=1.22,unsharp=5:5:0.8:5:5:0.0" if enhance_color else "null"

    # Xây dựng filter_complex tùy thuộc vào việc có kèm Logo hay không
    inputs = []
    
    # Input 0: Video gốc (dùng stream_loop để nếu video ngắn hơn audio thì tự lặp lại mượt mà)
    inputs.extend(["-stream_loop", "-1", "-ss", str(trim_start), "-i", raw_video_path])
    
    # Input 1: Audio thuyết minh
    inputs.extend(["-i", audio_path])
    
    if logo_path and os.path.exists(logo_path):
        # Input 2: Logo PNG
        inputs.extend(["-i", logo_path])
        filter_complex = (
            f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,{color_filter}[base];"
            f"[2:v]scale=180:-1[logo];"
            f"[base][logo]overlay=W-w-35:45[vwithlogo];"
            f"[vwithlogo]{sub_filter}[vout]"
        )
    else:
        filter_complex = (
            f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,{color_filter},{sub_filter}[vout]"
        )

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-map", "1:a",
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
    # Header nhận diện thương hiệu
    st.markdown("""
    <div class="brand-header">
        <div class="brand-title">🏛️ HẬU DÒNG TIỀN REAL ESTATE • AUTO VIDEO STUDIO</div>
        <div class="brand-subtitle">Hệ thống sản xuất Short-form Video tự động hóa dành riêng cho BĐS Khai Thác & Dòng Tiền Đà Nẵng (10 - 50 Tỷ)</div>
    </div>
    """, unsafe_allow_html=True)

    # Khởi tạo session state
    if "generated_script" not in st.session_state:
        st.session_state.generated_script = ""

    # Bố cục 2 cột chính
    col_left, col_right = st.columns([1.05, 1.15], gap="large")

    # --------------------------------------------------------------------------
    # CỘT TRÁI: THIẾT LẬP THÔNG SỐ & TRẠM AI KỊCH BẢN
    # --------------------------------------------------------------------------
    with col_left:
        # Card 1: Cấu hình API & Giọng đọc
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">⚙️ 1. Cấu Hình Khởi Tạo Hệ Thống</div>', unsafe_allow_html=True)
        
        api_key = st.text_input(
            "Gemini API Key:",
            type="password",
            value=os.environ.get("GEMINI_API_KEY", ""),
            placeholder="Nhập Google Gemini API Key để sinh kịch bản...",
            help="Lấy API Key miễn phí tại Google AI Studio."
        )

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
        st.markdown('</div>', unsafe_allow_html=True)

        # Card 2: Trạm AI Viết kịch bản
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">✍️ 2. Trạm AI Viết Kịch Bản BĐS Triệu Đô</div>', unsafe_allow_html=True)
        
        content_type = st.radio(
            "Chọn định hướng nội dung video:",
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

        if st.button("✨ TỰ ĐỘNG SINH KỊCH BẢN CHUẨN HOOK - BODY - CTA", use_container_width=True):
            if not api_key:
                st.error("⚠️ Vui lòng điền Gemini API Key để khởi chạy Trạm AI.")
            else:
                with st.spinner("Hệ thống AI đang phân tích dữ liệu và biên soạn kịch bản 35-45s..."):
                    try:
                        generated_txt = generate_real_estate_script(api_key, content_type, payload_details)
                        st.session_state.generated_script = generated_txt
                        st.success("✅ Đã tạo kịch bản sắc bén thành công!")
                    except Exception as err:
                        st.error(str(err))

        st.session_state.generated_script = st.text_area(
            "Lời thoại kịch bản (Bạn có thể tinh chỉnh trực tiếp bên dưới):",
            value=st.session_state.generated_script,
            height=140
        )
        st.markdown('</div>', unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # CỘT PHẢI: TIMELINE STUDIO & DỰNG PHIM TỰ ĐỘNG
    # --------------------------------------------------------------------------
    with col_right:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🎬 3. Timeline Studio: Nạp Tài Nguyên & Dựng Phim</div>', unsafe_allow_html=True)

        uploaded_video = st.file_uploader("Tải lên Video thực tế thô (MP4/MOV):", type=["mp4", "mov", "m4v"])
        uploaded_logo = st.file_uploader("Logo thương hiệu 'Hậu Dòng Tiền' (File PNG nền trong suốt - Tùy chọn):", type=["png"])

        with st.expander("🛠️ Tùy Chỉnh Biên Tập & Hiệu Ứng Nâng Cao", expanded=True):
            edit_c1, edit_c2 = st.columns(2)
            with edit_c1:
                trim_start_sec = st.slider("Cắt bỏ phần thừa đầu video (Auto-trim giây):", 0.0, 5.0, 0.5, 0.1)
                font_size = st.slider("Cỡ chữ phụ đề (Subtitle Size):", 14, 26, 18)
            with edit_c2:
                margin_vertical = st.slider("Khoảng cách phụ đề từ đáy (Margin Bottom):", 80, 250, 130)
                enhance_color = st.checkbox("Bộ lọc tăng sáng, tương phản & làm nét video", value=True)

        render_btn = st.button("🚀 XUẤT BẢN VIDEO FULL HD 9:16", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # ----------------------------------------------------------------------
        # QUY TRÌNH RENDER HỆ THỐNG
        # ----------------------------------------------------------------------
        if render_btn:
            if not st.session_state.generated_script.strip():
                st.error("⚠️ Bạn chưa có kịch bản thuyết minh. Vui lòng tạo kịch bản ở Cột trái trước!")
            elif not uploaded_video:
                st.error("⚠️ Vui lòng tải lên ít nhất 1 video quay thực tế tài sản.")
            else:
                progress_bar = st.progress(0)
                status_box = st.empty()

                # Tạo thư mục làm việc tạm thời an toàn
                with tempfile.TemporaryDirectory() as temp_dir:
                    try:
                        # 1. Lưu file video thô
                        status_box.info("📥 [1/4] Đang tiếp nhận tài nguyên đầu vào...")
                        temp_video_path = os.path.join(temp_dir, "raw_input.mp4")
                        with open(temp_video_path, "wb") as f:
                            f.write(uploaded_video.read())

                        temp_logo_path = ""
                        if uploaded_logo:
                            temp_logo_path = os.path.join(temp_dir, "logo.png")
                            with open(temp_logo_path, "wb") as f:
                                f.write(uploaded_logo.read())
                        progress_bar.progress(25)

                        # 2. Sinh Voiceover từ Edge-TTS
                        status_box.info("🎙️ [2/4] Trạm Edge-TTS đang tổng hợp giọng đọc AI truyền cảm...")
                        temp_audio_path = os.path.join(temp_dir, "voice.mp3")
                        generate_voiceover(
                            text=st.session_state.generated_script,
                            voice=voice_choice,
                            rate=voice_speed,
                            output_path=temp_audio_path
                        )
                        progress_bar.progress(50)

                        # 3. Trích xuất phụ đề tự động từ Whisper
                        status_box.info("🧠 [3/4] Whisper AI đang trích xuất phụ đề từng khung hình chính xác...")
                        temp_srt_path = os.path.join(temp_dir, "subtitles.srt")
                        transcribe_audio_to_srt(
                            audio_path=temp_audio_path,
                            output_srt_path=temp_srt_path,
                            model_name="base"
                        )
                        progress_bar.progress(75)

                        # 4. Pipeline FFmpeg render video hoàn thiện
                        status_box.info("⚡ [4/4] FFmpeg Pipeline đang Color Grade, dập Logo, nung Hardsub và xuất chuẩn 9:16...")
                        final_output_path = os.path.join(temp_dir, "hau_dong_tien_final.mp4")
                        render_final_video(
                            raw_video_path=temp_video_path,
                            audio_path=temp_audio_path,
                            srt_path=temp_srt_path,
                            logo_path=temp_logo_path,
                            output_path=final_output_path,
                            trim_start=trim_start_sec,
                            font_size=font_size,
                            margin_v=margin_vertical,
                            enhance_color=enhance_color
                        )
                        progress_bar.progress(100)
                        status_box.success("🎉 TUYỆT VỜI! Video BĐS Dòng Tiền đã xuất bản hoàn tất!")

                        # Đọc file ra memory để hiển thị và tải xuống
                        with open(final_output_path, "rb") as f:
                            video_bytes = f.read()

                        st.markdown('<div class="section-card">', unsafe_allow_html=True)
                        st.markdown('<div class="section-title">📺 Video Thành Phẩm Hoàn Thiện</div>', unsafe_allow_html=True)
                        st.video(video_bytes)

                        st.download_button(
                            label="⬇️ TẢI XUỐNG VIDEO ĐỂ ĐĂNG TIKTOK / REELS / SHORTS",
                            data=video_bytes,
                            file_name="HauDongTien_RealEstate_9x16.mp4",
                            mime="video/mp4",
                            use_container_width=True
                        )
                        st.markdown('</div>', unsafe_allow_html=True)

                    except Exception as process_error:
                        status_box.empty()
                        st.error(f"❌ Xảy ra sự cố trong quá trình xử lý: {str(process_error)}")


if __name__ == "__main__":
    main()