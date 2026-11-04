import os
import sys
import asyncio
import tempfile
import subprocess
from datetime import timedelta
import streamlit as st
import whisper

# ==========================================
# CẤU HÌNH GIAO DIỆN STREAMLIT
# ==========================================
st.set_page_config(
    page_title="Hệ Thống Tự Động Hóa Video Bất Động Sản",
    page_icon="🏡",
    layout="wide"
)

# ==========================================
# HÀM BỔ TRỢ (UTILITIES)
# ==========================================
def format_srt_time(seconds: float) -> str:
    """Chuyển đổi giây thành định dạng thời gian chuẩn SRT: HH:MM:SS,mmm"""
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    millis = int((seconds - int(seconds)) * 1000)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def write_srt(segments: list, srt_filepath: str):
    """Xuất danh sách segment của Whisper ra file định dạng .srt"""
    with open(srt_filepath, "w", encoding="utf-8") as f:
        for idx, seg in enumerate(segments, start=1):
            start_str = format_srt_time(seg["start"])
            end_str = format_srt_time(seg["end"])
            text = seg["text"].strip()
            f.write(f"{idx}\n{start_str} --> {end_str}\n{text}\n\n")

@st.cache_resource
def load_whisper_model():
    """Tải và lưu trữ model Whisper trong cache RAM để tránh tải lại mỗi lần click"""
    return whisper.load_model("base")

async def _edge_tts_runner(text: str, voice: str, output_path: str):
    import edge_tts
    communicate = edge_tts.Communicate(text=text, voice=voice)
    await communicate.save(output_path)

def generate_voiceover(text: str, voice: str, output_path: str):
    """Bọc tác vụ async của edge-tts để chạy an toàn trên luồng của Streamlit"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        # Phòng ngừa trường hợp Streamlit chạy trên event loop lồng nhau
        import nest_asyncio
        nest_asyncio.apply()
        loop.run_until_complete(_edge_tts_runner(text, voice, output_path))
    else:
        loop.run_until_complete(_edge_tts_runner(text, voice, output_path))

def burn_subtitles_and_mux_audio(video_in: str, audio_in: str, srt_in: str, video_out: str):
    """
    Sử dụng FFmpeg để:
    1. Nung cứng (hardsub) phụ đề với style rõ nét cho video BĐS.
    2. Thay thế luồng âm thanh gốc bằng giọng đọc AI mới.
    3. Cắt độ dài video bằng độ dài âm thanh (-shortest).
    """
    # Xử lý escape ký tự đặc biệt cho FFmpeg filter path (đặc biệt là dấu ':' và '\')
    escaped_srt = srt_in.replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
    
    # Định dạng style phụ đề: Chữ trắng, viền đen dày, kích cỡ dễ đọc trên điện thoại
    style = "FontName=Arial,FontSize=18,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=3,Outline=2,MarginV=40,Bold=1"
    subtitles_filter = f"subtitles='{escaped_srt}':force_style='{style}'"

    cmd = [
        "ffmpeg",
        "-y",
        "-i", video_in,
        "-i", audio_in,
        "-filter_complex", f"[0:v]{subtitles_filter}[v]",
        "-map", "[v]",
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
    st.title("🏡 Hệ Thống Tự Động Hóa Video Bất Động Sản")
    st.markdown("Quy trình khép kín: **Tạo Giọng Đọc AI ➔ Bóc Tách Phụ Đề ➔ Ghép Hardsub & Âm Thanh**.")

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.subheader("1. Tải lên tư liệu")
        uploaded_video = st.file_uploader(
            "Chọn video quay nhà đất thô (.mp4, .mov):",
            type=["mp4", "mov"],
            help="Tải lên video thực tế không gian nhà đất của bạn."
        )

        voice_choice = st.selectbox(
            "Chọn giọng đọc AI:",
            options=[
                ("vi-VN-HoaiMyNeural", "Hoài My (Nữ - Truyền cảm, miền Nam)"),
                ("vi-VN-NamMinhNeural", "Nam Minh (Nam - Chuyên nghiệp, miền Bắc)")
            ],
            format_func=lambda x: x[1]
        )

        script_text = st.text_area(
            "2. Nhập kịch bản giới thiệu nhà đất (Script):",
            height=200,
            placeholder="Ví dụ: Chào mừng quý anh chị đã đến với căn biệt thự đơn lập tọa lạc tại khu đô thị sinh thái xanh..."
        )

        submit_btn = st.button("🚀 Sản xuất video tự động", use_container_width=True, type="primary")

    with col2:
        st.subheader("3. Trạng thái & Kết quả")
        result_container = st.container()

    if submit_btn:
        # Kiểm tra điều kiện đầu vào
        if uploaded_video is None:
            st.error("⚠️ Vui lòng tải lên file video gốc!")
            return
        if not script_text.strip():
            st.error("⚠️ Kịch bản đọc (Text Script) không được để trống!")
            return

        temp_files = []
        try:
            with result_container:
                status = st.status("Đang khởi động tiến trình xử lý...", expanded=True)

                # Lưu video gốc tải lên
                status.write("📥 Đang lưu trữ file video tải lên...")
                suffix = os.path.splitext(uploaded_video.name)[1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as raw_video_tmp:
                    raw_video_tmp.write(uploaded_video.read())
                    raw_video_path = raw_video_tmp.name
                temp_files.append(raw_video_path)

                # Bước 1: Tạo Voiceover TTS
                status.write("🎙️ Bước 1: Đang tạo giọng đọc AI từ văn bản...")
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as voice_tmp:
                    voice_path = voice_tmp.name
                temp_files.append(voice_path)

                generate_voiceover(
                    text=script_text.strip(),
                    voice=voice_choice[0],
                    output_path=voice_path
                )

                # Bước 2: Bóc tách phụ đề bằng Whisper
                status.write("🧠 Bước 2: Whisper đang phân tích âm thanh & tạo file phụ đề (.srt)...")
                model = load_whisper_model()
                transcribe_result = model.transcribe(voice_path, language="vi", task="transcribe")

                with tempfile.NamedTemporaryFile(delete=False, suffix=".srt") as srt_tmp:
                    srt_path = srt_tmp.name
                temp_files.append(srt_path)

                write_srt(transcribe_result["segments"], srt_path)

                # Bước 3: Ghép video, nung phụ đề và hợp nhất âm thanh bằng FFmpeg
                status.write("⚡ Bước 3: FFmpeg đang xử lý render video (Hardsub & Ghép âm thanh)...")
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as out_video_tmp:
                    out_video_path = out_video_tmp.name
                temp_files.append(out_video_path)

                burn_subtitles_and_mux_audio(
                    video_in=raw_video_path,
                    audio_in=voice_path,
                    srt_in=srt_path,
                    video_out=out_video_path
                )

                status.update(label="✅ Sản xuất video thành công!", state="complete", expanded=False)

                # Bước 4: Hiển thị video hoàn thiện & Nút tải về
                st.video(out_video_path)

                with open(out_video_path, "rb") as f:
                    final_bytes = f.read()

                st.download_button(
                    label="💾 Tải video hoàn chỉnh xuống (.mp4)",
                    data=final_bytes,
                    file_name="bds_video_hoan_thien.mp4",
                    mime="video/mp4",
                    use_container_width=True
                )

        except Exception as e:
            st.error(f"❌ Đã xảy ra lỗi trong quá trình xử lý: {str(e)}")
        finally:
            # Dọn dẹp toàn bộ file tạm an toàn
            for fpath in temp_files:
                if os.path.exists(fpath):
                    try:
                        os.remove(fpath)
                    except Exception:
                        pass

if __name__ == "__main__":
    main()
