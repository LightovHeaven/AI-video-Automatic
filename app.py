import os
import sys
import asyncio
import tempfile
import subprocess
from datetime import timedelta
import streamlit as st
import whisper
import edge_tts
import nest_asyncio

# Cho phép lồng event loop an toàn trong môi trường chạy của Streamlit
nest_asyncio.apply()

# ==========================================
# CẤU HÌNH GIAO DIỆN STREAMLIT
# ==========================================
st.set_page_config(
    page_title="Hậu Dòng Tiền - Sản Xuất Video BĐS Tự Động",
    page_icon="🏢",
    layout="wide"
)

# ==========================================
# CÁC HÀM XỬ LÝ KỸ THUẬT (BACKEND ENGINE)
# ==========================================
def format_srt_time(seconds: float) -> str:
    """Chuyển đổi giây thành timestamp chuẩn định dạng SRT: HH:MM:SS,mmm"""
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    millis = int((seconds - int(seconds)) * 1000)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def write_srt_file(segments: list, srt_filepath: str):
    """Xuất danh sách phân đoạn của Whisper ra file .srt chuẩn"""
    with open(srt_filepath, "w", encoding="utf-8") as f:
        for idx, seg in enumerate(segments, start=1):
            start = format_srt_time(seg["start"])
            end = format_srt_time(seg["end"])
            text = seg["text"].strip()
            f.write(f"{idx}\n{start} --> {end}\n{text}\n\n")

@st.cache_resource
def load_whisper_model():
    """Tải và lưu trữ model Whisper Base trên RAM để tái sử dụng nhanh"""
    return whisper.load_model("base")

async def _generate_voiceover_async(text: str, voice: str, output_path: str):
    """Gọi Edge-TTS sinh file âm thanh từ văn bản kịch bản"""
    communicate = edge_tts.Communicate(text=text, voice=voice)
    await communicate.save(output_path)

def generate_voiceover(text: str, voice: str, output_path: str):
    """Bọc tác vụ async để chạy đồng bộ và an toàn trong Streamlit"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    loop.run_until_complete(_generate_voiceover_async(text, voice, output_path))

def burn_subtitles_and_replace_audio(video_in: str, audio_in: str, srt_in: str, video_out: str):
    """
    Sử dụng FFmpeg để:
    1. Lấy luồng hình ảnh từ video gốc (0:v:0).
    2. Đè luồng âm thanh giọng đọc AI mới vào (1:a:0).
    3. Ép cứng phụ đề (Hardsub) với viền đen chữ đậm dễ đọc cho video BĐS.
    4. Cắt khớp thời lượng video theo âm thanh (-shortest).
    """
    # Xử lý escape ký tự đặc biệt cho FFmpeg path (trên cả Windows và Linux)
    escaped_srt = srt_in.replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
    subtitle_style = (
        "FontName=Arial,FontSize=18,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,BorderStyle=3,Outline=2.5,MarginV=35,Bold=1"
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-i", video_in,
        "-i", audio_in,
        "-vf", f"subtitles='{escaped_srt}':force_style='{subtitle_style}'",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        video_out
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Lỗi FFmpeg: {result.stderr}")

# ==========================================
# GIAO DIỆN NGƯỜI DÙNG (STREAMLIT UI)
# ==========================================
def main():
    st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>🏢 HẬU DÒNG TIỀN REAL ESTATE</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Tự động hóa sản xuất video: Kịch Bản ➔ Giọng Đọc AI ➔ Đồng Bộ Phụ Đề ➔ Hardsub Video</p>", unsafe_allow_html=True)
    st.divider()

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.subheader("1. Dữ liệu đầu vào")
        uploaded_video = st.file_uploader(
            "Tải lên video thực tế BĐS thô (.mp4, .mov):",
            type=["mp4", "mov"],
            help="Video quay không gian nhà, tòa nhà hoặc căn hộ."
        )

        voice_choice = st.selectbox(
            "Chọn giọng đọc AI thuyết minh:",
            options=[
                ("vi-VN-HoaiMyNeural", "Hoài My (Nữ - Miền Nam truyền cảm)"),
                ("vi-VN-NamMinhNeural", "Nam Minh (Nam - Miền Bắc chuyên nghiệp)")
            ],
            format_func=lambda x: x[1]
        )

        script_text = st.text_area(
            "Kịch bản (Script) thuyết minh BĐS:",
            height=220,
            value=(
                "Chào mừng quý nhà đầu tư đến với tòa căn hộ dịch vụ cao cấp tại Mỹ Đình. "
                "Tòa nhà quy mô 7 tầng thang máy, 18 phòng full nội thất đang khai thác kín phòng, "
                "dòng tiền cho thuê đều đặn đạt 85 triệu mỗi tháng, tương đương tỷ suất sinh lời vượt trội 6.5% một năm. "
                "Sổ đỏ chính chủ, pháp lý chuẩn chỉ. Liên hệ ngay Hậu Dòng Tiền để sở hữu tài sản sinh lời này!"
            ),
            help="Nhập toàn bộ nội dung kịch bản để AI đọc và tạo phụ đề tương ứng."
        )

        submit_btn = st.button("🚀 Sản xuất Video Bất Động Sản", type="primary", use_container_width=True)

    with col2:
        st.subheader("2. Màn hình sản xuất & Thành phẩm")
        output_container = st.container()

    if submit_btn:
        # Kiểm tra dữ liệu đầu vào
        if uploaded_video is None:
            st.warning("⚠️ Vui lòng tải lên file video thô (.mp4 hoặc .mov)!")
            return
        if not script_text.strip():
            st.warning("⚠️ Kịch bản (Script) không được để trống!")
            return

        temp_files = []

        try:
            with output_container:
                status_box = st.status("Đang khởi động quy trình sản xuất...", expanded=True)

                # Lưu video gốc tải lên vào file tạm
                status_box.write("📥 Đang lưu file video tải lên...")
                vid_suffix = os.path.splitext(uploaded_video.name)[1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=vid_suffix) as tmp_vid:
                    tmp_vid.write(uploaded_video.read())
                    raw_video_path = tmp_vid.name
                temp_files.append(raw_video_path)

                # Bước 1: Tạo giọng đọc AI từ Kịch bản văn bản bằng Edge-TTS
                status_box.write("🎙️ **Bước 1/3**: Đang tạo file giọng đọc AI tiếng Việt từ kịch bản...")
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_audio:
                    voice_path = tmp_audio.name
                temp_files.append(voice_path)

                generate_voiceover(
                    text=script_text.strip(),
                    voice=voice_choice[0],
                    output_path=voice_path
                )

                # Bước 2: Whisper nhận TRỰC TIẾP file âm thanh AI vừa tạo (Không chạm vào video gốc)
                status_box.write("🧠 **Bước 2/3**: Whisper đang bóc tách mốc thời gian phụ đề từ giọng đọc AI...")
                whisper_model = load_whisper_model()
                transcribe_result = whisper_model.transcribe(voice_path, language="vi", task="transcribe")

                with tempfile.NamedTemporaryFile(delete=False, suffix=".srt") as tmp_srt:
                    srt_path = tmp_srt.name
                temp_files.append(srt_path)

                write_srt_file(transcribe_result.get("segments", []), srt_path)

                # Bước 3: FFmpeg ghép giọng đọc mới & Ép cứng phụ đề (Hardsub)
                status_box.write("⚡ **Bước 3/3**: FFmpeg đang ghép âm thanh AI và nung phụ đề lên video...")
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_out:
                    final_video_path = tmp_out.name
                temp_files.append(final_video_path)

                burn_subtitles_and_replace_audio(
                    video_in=raw_video_path,
                    audio_in=voice_path,
                    srt_in=srt_path,
                    video_out=final_video_path
                )

                status_box.update(label="🎉 Sản xuất video thành công!", state="complete", expanded=False)

                # Bước 4: Hiển thị Video và Cung cấp nút Tải về
                st.video(final_video_path)

                with open(final_video_path, "rb") as f:
                    final_bytes = f.read()

                st.download_button(
                    label="💾 Tải Video Hoàn Thiện Về Máy (.mp4)",
                    data=final_bytes,
                    file_name="HauDongTien_Video_Complete.mp4",
                    mime="video/mp4",
                    use_container_width=True
                )

        except Exception as e:
            st.error(f"❌ Xảy ra lỗi trong quá trình xử lý: {str(e)}")
        finally:
            # Dọn dẹp triệt để toàn bộ file tạm để tránh tràn ổ cứng
            for path in temp_files:
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except Exception:
                        pass

if __name__ == "__main__":
    main()
