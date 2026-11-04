import os
import sys
import tempfile
import subprocess
from datetime import timedelta
import streamlit as st
import whisper

# ==========================================
# CẤU HÌNH GIAO DIỆN STREAMLIT
# ==========================================
st.set_page_config(
    page_title="Hậu Dòng Tiền - Video Studio",
    page_icon="🏢",
    layout="wide"
)

# ==========================================
# CÁC HÀM XỬ LÝ PHỤ TRỢ (HELPER FUNCTIONS)
# ==========================================
def format_srt_time(seconds: float) -> str:
    """Định dạng giây thành timestamp chuẩn SRT: HH:MM:SS,mmm"""
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    millis = int((seconds - int(seconds)) * 1000)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def write_srt_file(segments: list, srt_filepath: str):
    """Xuất danh sách phân đoạn Whisper ra file .srt"""
    with open(srt_filepath, "w", encoding="utf-8") as f:
        for idx, seg in enumerate(segments, start=1):
            start = format_srt_time(seg["start"])
            end = format_srt_time(seg["end"])
            text = seg["text"].strip()
            f.write(f"{idx}\n{start} --> {end}\n{text}\n\n")

@st.cache_resource
def load_whisper_model():
    """Tải và lưu trữ model Whisper Base trên RAM"""
    return whisper.load_model("base")

def extract_audio_to_wav(video_path: str, wav_path: str) -> bool:
    """
    Trích xuất âm thanh từ video sang định dạng chuẩn 16kHz Mono WAV cho Whisper.
    Trả về True nếu thành công, False nếu video không có audio stream hoặc trích xuất thất bại.
    """
    cmd = [
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        wav_path
    ]
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        # Kiểm tra return code và kích thước file sau khi xuất
        if result.returncode != 0 or not os.path.exists(wav_path) or os.path.getsize(wav_path) == 0:
            return False
        return True
    except Exception:
        return False

def generate_cashflow_script(property_data: dict, openai_key: str = "") -> str:
    """Tạo kịch bản bán BĐS dòng tiền (Sử dụng OpenAI API nếu có, fallback về template nội bộ)"""
    title = property_data.get("title", "")
    location = property_data.get("location", "")
    area = property_data.get("area", "")
    price = property_data.get("price", "")
    cashflow = property_data.get("cashflow", "")
    highlight = property_data.get("highlight", "")

    if openai_key.strip():
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key.strip())
            prompt = f"""
            Bạn là chuyên gia marketing kênh 'Hậu Dòng Tiền Real Estate'.
            Hãy viết kịch bản video ngắn (60-90 từ) dứt khoát, thuyết phục, tập trung vào DÒNG TIỀN và LÃI KÉP:
            - Loại hình/Tên: {title}
            - Vị trí: {location}
            - Diện tích/Quy mô: {area}
            - Giá bán: {price}
            - Dòng tiền khai thác: {cashflow}
            - Lợi thế/Điểm nổi bật: {highlight}
            """
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=250
            )
            return response.choices[0].message.content.strip()
        except Exception:
            pass

    return (
        f"Cơ hội sở hữu cỗ máy in tiền thụ động ngay tại {location}! "
        f"Chào mừng quý nhà đầu tư đến với {title}, quy mô {area}. "
        f"Tài sản đang tạo ra dòng tiền cho thuê đều đặn {cashflow}, đạt tỷ suất sinh lời vượt trội so với gửi ngân hàng. "
        f"Đặc biệt: {highlight}. Giá sang nhượng trọn gói chỉ {price}. "
        f"Liên hệ ngay Hậu Dòng Tiền để nhận bảng phân tích tài chính chi tiết từng tháng!"
    )

def process_video_ffmpeg(video_in: str, srt_in: str, logo_in: str, video_out: str):
    """
    Sử dụng FFmpeg để:
    1. Scale logo bản quyền và đóng dấu watermark góc trên bên phải.
    2. Nung cứng (hardsub) phụ đề với viền đen tương phản cao.
    3. Giữ nguyên luồng âm thanh gốc của video.
    """
    escaped_srt = srt_in.replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
    subtitle_style = (
        "FontName=Arial,FontSize=18,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,BorderStyle=3,Outline=2.5,MarginV=35,Bold=1"
    )

    cmd = ["ffmpeg", "-y", "-i", video_in]
    filter_steps = []

    if logo_in and os.path.exists(logo_in):
        cmd.extend(["-i", logo_in])
        filter_steps.append("[1:v]scale=170:-1[logo]")
        filter_steps.append("[0:v][logo]overlay=W-w-25:25[vlogo]")
        filter_steps.append(f"[vlogo]subtitles='{escaped_srt}':force_style='{subtitle_style}'[vout]")
    else:
        filter_steps.append(f"[0:v]subtitles='{escaped_srt}':force_style='{subtitle_style}'[vout]")

    cmd.extend([
        "-filter_complex", ";".join(filter_steps),
        "-map", "[vout]",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        video_out
    ])

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Lỗi FFmpeg: {result.stderr}")

# ==========================================
# GIAO DIỆN NGƯỜI DÙNG (STREAMLIT UI)
# ==========================================
def main():
    st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>🏢 HẬU DÒNG TIỀN REAL ESTATE</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Hệ thống sản xuất video BĐS tự động: Kịch Bản AI - Trích Xuất Phụ Đề Chuẩn Xác - Đóng Dấu Bản Quyền</p>", unsafe_allow_html=True)
    st.divider()

    with st.sidebar:
        st.header("⚙️ Cấu hình")
        openai_key = st.text_input(
            "OpenAI API Key (Tùy chọn):",
            type="password",
            help="Để trống sẽ dùng kịch bản mẫu tối ưu sẵn cho BĐS dòng tiền."
        )

    col1, col2 = st.columns([1.1, 0.9], gap="large")

    with col1:
        st.subheader("1. Thông tin BĐS")
        c1, c2 = st.columns(2)
        with c1:
            prop_title = st.text_input("Loại hình / Tiêu đề:", value="Tòa Căn Hộ Dịch Vụ 7 Tầng Thang Máy")
            prop_location = st.text_input("Vị trí tài sản:", value="Mỹ Đình, Nam Từ Liêm, Hà Nội")
            prop_area = st.text_input("Diện tích / Quy mô:", value="85m² x 7 tầng, 18 phòng khép kín")
        with c2:
            prop_price = st.text_input("Giá bán / Sang nhượng:", value="15.8 Tỷ")
            prop_cashflow = st.text_input("Dòng tiền khai thác / tháng:", value="85 Triệu/tháng (Dòng tiền ròng ~6.5%/năm)")
            prop_highlight = st.text_input("Lợi thế cạnh tranh:", value="PCCC chuẩn chỉ, full nội thất, luôn kín phòng")

        st.subheader("2. Dữ liệu Video & Logo")
        uploaded_video = st.file_uploader(
            "Tải lên video thực tế BĐS có tiếng nói (.mp4, .mov):",
            type=["mp4", "mov"],
            help="Video quay kèm giọng đọc thuyết minh thực tế của bạn."
        )
        uploaded_logo = st.file_uploader(
            "Tải lên Logo bản quyền (.png trong suốt):",
            type=["png"],
            help="Logo thương hiệu để đóng dấu watermark."
        )

        submit_btn = st.button("🚀 Sản xuất Video Bất Động Sản Hoàn Chỉnh", type="primary", use_container_width=True)

    with col2:
        st.subheader("3. Màn hình sản xuất & Thành phẩm")
        output_area = st.container()

    if submit_btn:
        if uploaded_video is None:
            st.error("⚠️ Vui lòng tải lên file video gốc (.mp4 hoặc .mov)!")
            return

        temp_files = []
        has_error = False

        try:
            with output_area:
                status_box = st.status("Đang chuẩn bị tiến trình...", expanded=True)

                # Bước 1: Tạo kịch bản BĐS
                status_box.write("📝 **Bước 1/4**: Khởi tạo kịch bản BĐS dòng tiền...")
                prop_data = {
                    "title": prop_title,
                    "location": prop_location,
                    "area": prop_area,
                    "price": prop_price,
                    "cashflow": prop_cashflow,
                    "highlight": prop_highlight
                }
                ai_script = generate_cashflow_script(prop_data, openai_key)
                st.markdown("**📋 Kịch bản phân tích tài chính:**")
                st.info(ai_script)

                # Lưu video gốc
                status_box.write("📥 Đang lưu trữ file video tải lên...")
                vid_suffix = os.path.splitext(uploaded_video.name)[1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=vid_suffix) as tmp_vid:
                    tmp_vid.write(uploaded_video.read())
                    raw_video_path = tmp_vid.name
                temp_files.append(raw_video_path)

                # Lưu logo (nếu có)
                logo_path = ""
                if uploaded_logo is not None:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_logo:
                        tmp_logo.write(uploaded_logo.read())
                        logo_path = tmp_logo.name
                    temp_files.append(logo_path)

                # Bước 2: Tách Audio sang file WAV riêng biệt
                status_box.write("🎵 **Bước 2/4**: Đang trích xuất luồng âm thanh sang định dạng chuẩn WAV...")
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_wav:
                    wav_path = tmp_wav.name
                temp_files.append(wav_path)

                audio_extracted = extract_audio_to_wav(raw_video_path, wav_path)

                # Xử lý trường hợp video không có tiếng hoặc lỗi luồng âm thanh
                if not audio_extracted:
                    status_box.update(label="⚠️ Không thể đọc âm thanh!", state="error", expanded=False)
                    st.warning("Video này không có âm thanh hoặc luồng tiếng bị lỗi, vui lòng kiểm tra lại file video!")
                    has_error = True
                    return

                # Bước 3: Whisper nhận trực tiếp file WAV
                status_box.write("🎙️ **Bước 3/4**: Whisper đang bóc tách phụ đề từ file âm thanh WAV...")
                whisper_model = load_whisper_model()
                # TUYỆT ĐỐI KHÔNG truyền file video vào đây, truyền trực tiếp wav_path đã chuẩn hóa
                transcribe_res = whisper_model.transcribe(wav_path, language="vi", task="transcribe")

                with tempfile.NamedTemporaryFile(delete=False, suffix=".srt") as tmp_srt:
                    srt_path = tmp_srt.name
                temp_files.append(srt_path)

                write_srt_file(transcribe_res.get("segments", []), srt_path)

                # Bước 4: FFmpeg đóng dấu Watermark & Nung phụ đề
                status_box.write("⚡ **Bước 4/4**: FFmpeg đang đóng dấu watermark & nung phụ đề lên video...")
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_out:
                    final_video_path = tmp_out.name
                temp_files.append(final_video_path)

                process_video_ffmpeg(
                    video_in=raw_video_path,
                    srt_in=srt_path,
                    logo_in=logo_path,
                    video_out=final_video_path
                )

                status_box.update(label="🎉 Sản xuất video hoàn tất!", state="complete", expanded=False)

                # Hiển thị và tải video
                st.video(final_video_path)

                with open(final_video_path, "rb") as f:
                    final_video_bytes = f.read()

                st.download_button(
                    label="💾 Tải Video Hoàn Thiện Về Máy (.mp4)",
                    data=final_video_bytes,
                    file_name="HauDongTien_Video_Export.mp4",
                    mime="video/mp4",
                    use_container_width=True
                )

        except Exception as e:
            if not has_error:
                st.error(f"❌ Xảy ra lỗi trong quá trình xử lý: {str(e)}")
        finally:
            # Dọn dẹp tài nguyên file tạm
            for path in temp_files:
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except Exception:
                        pass

if __name__ == "__main__":
    main()
