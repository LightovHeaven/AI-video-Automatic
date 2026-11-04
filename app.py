import streamlit as st
import os
import tempfile
import subprocess
import whisper

# -----------------------------------------------------------------------------
# CẤU HÌNH GIAO DIỆN
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Video Subtitle - Hậu Dòng Tiền Real Estate",
    page_icon="🎬",
    layout="centered"
)

# -----------------------------------------------------------------------------
# CÁC HÀM XỬ LÝ ÂM THANH & MÔ HÌNH
# -----------------------------------------------------------------------------
@st.cache_resource(show_spinner="Đang nạp mô hình Whisper AI...")
def load_whisper_model(model_name="base"):
    return whisper.load_model(model_name)

def extract_audio_ffmpeg(input_path: str, output_wav_path: str):
    """
    Sử dụng subprocess để gọi FFmpeg trực tiếp, trích xuất âm thanh thành file .wav chuẩn.
    Tránh hoàn toàn lỗi 'Output file does not contain any stream' của FFmpeg 7.x trên Whisper.
    """
    command = [
        "ffmpeg",
        "-y",               # Ghi đè file nếu đã tồn tại
        "-i", input_path,   # File video/audio đầu vào
        "-vn",              # Tắt stream hình ảnh (chỉ lấy âm thanh)
        "-acodec", "pcm_s16le", # Codec 16-bit PCM
        "-ar", "16000",     # Tần số lấy mẫu 16kHz chuẩn của Whisper
        "-ac", "1",         # Kênh âm thanh Mono (1 kênh)
        output_wav_path
    ]
    
    # Thực thi lệnh và bắt lỗi nếu FFmpeg thất bại
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg gặp lỗi khi trích xuất âm thanh:\n{result.stderr}")

def format_time_srt(seconds: float) -> str:
    """Đổi số giây sang định dạng SRT chuẩn (HH:MM:SS,mmm)."""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{ms:03d}"

def generate_srt_content(segments: list) -> str:
    """Tạo chuỗi phụ đề SRT trong bộ nhớ RAM."""
    srt_lines = []
    for i, seg in enumerate(segments, start=1):
        start_str = format_time_srt(seg["start"])
        end_str = format_time_srt(seg["end"])
        text = seg["text"].strip()
        srt_lines.append(f"{i}\n{start_str} --> {end_str}\n{text}\n")
    return "\n".join(srt_lines)

# -----------------------------------------------------------------------------
# GIAO DIỆN CHÍNH (UI)
# -----------------------------------------------------------------------------
st.title("🎬 Ứng Dụng AI Tự Động Tạo Subtitle")
st.markdown("### Thương hiệu: **Hậu Dòng Tiền Real Estate** 🏢")
st.caption("Công cụ trích xuất và bóc tách phụ đề tiếng Việt tự động cho video Bất Động Sản.")

with st.expander("⚙️ Tùy chọn cấu hình AI", expanded=False):
    model_choice = st.selectbox(
        "Kích thước mô hình Whisper:",
        options=["tiny", "base", "small"],
        index=1,
        help="'base' chạy ổn định và vừa vặn nhất với bộ nhớ RAM miễn phí của Streamlit Cloud."
    )

uploaded_file = st.file_uploader(
    "Chọn file video hoặc audio của anh (.mp4, .mov, .mkv, .mp3, .m4a):", 
    type=["mp4", "mov", "mkv", "mp3", "m4a"]
)

if uploaded_file is not None:
    st.success(f"Đã tải lên: **{uploaded_file.name}** ({uploaded_file.size / (1024 * 1024):.2f} MB)")
    
    if uploaded_file.type.startswith("video"):
        st.video(uploaded_file)
    else:
        st.audio(uploaded_file)
    
    if st.button("🚀 Bắt đầu nhận diện & Tạo Sub", type="primary"):
        suffix = os.path.splitext(uploaded_file.name)[-1].lower() or ".mp4"
        
        temp_input_path = None
        temp_wav_path = None
        
        try:
            # 1. Ghi file tải lên vào file tạm
            with st.spinner("Đang lưu trữ dữ liệu..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tfile:
                    tfile.write(uploaded_file.read())
                    temp_input_path = tfile.name

            # 2. Tạo đường dẫn file WAV tạm
            temp_wav_path = temp_input_path + ".converted.wav"

            # 3. Trích xuất âm thanh bằng Subprocess FFmpeg (Fix triệt để lỗi FFmpeg v7.x)
            with st.spinner("Đang trích xuất kênh âm thanh chuẩn (16kHz Mono)..."):
                extract_audio_ffmpeg(temp_input_path, temp_wav_path)

            # 4. Chạy mô hình Whisper nhận diện giọng nói
            with st.spinner(f"AI Whisper ({model_choice}) đang nghe và bóc tách tiếng Việt..."):
                model = load_whisper_model(model_choice)
                
                # Truyền trực tiếp đường dẫn file WAV đã chuẩn hóa
                result = model.transcribe(
                    temp_wav_path,
                    language="vi",
                    fp16=False,
                    verbose=False
                )

            st.success("🎉 Đã tạo phụ đề thành công!")

            # 5. Xuất file SRT & Nút tải về
            srt_content = generate_srt_content(result.get("segments", []))
            base_filename = os.path.splitext(uploaded_file.name)[0]
            
            st.download_button(
                label="📥 Tải xuống file phụ đề (.srt)",
                data=srt_content.encode("utf-8"),
                file_name=f"{base_filename}_subtitles.srt",
                mime="text/plain",
                type="primary"
            )

            # 6. Hiển thị nội dung phụ đề lên giao diện
            st.markdown("#### 📜 Danh sách câu thoại đã nhận diện:")
            segments = result.get("segments", [])
            
            if not segments:
                st.warning("Không nhận diện được giọng nói trong video.")
            else:
                with st.container(height=320):
                    for seg in segments:
                        start_time = format_time_srt(seg['start'])
                        end_time = format_time_srt(seg['end'])
                        text = seg['text'].strip()
                        st.markdown(f"⏱️ **`{start_time} --> {end_time}`** : {text}")

        except Exception as e:
            st.error(f"❌ Xảy ra lỗi: {str(e)}")

        finally:
            # Dọn dẹp cả 2 file tạm để giải phóng bộ nhớ server
            for p in [temp_input_path, temp_wav_path]:
                if p and os.path.exists(p):
                    try:
                        os.remove(p)
                    except Exception:
                        pass
