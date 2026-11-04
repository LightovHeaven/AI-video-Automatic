import streamlit as st
import os
import tempfile
import subprocess
import whisper

st.set_page_config(page_title="AI Video Automatic - Hậu Dòng Tiền", page_icon="🎬")

st.title("🎬 Ứng Dụng AI Tự Động Xử Lý Video Bất Động Sản")
st.markdown("### Thương hiệu: **Hậu Dòng Tiền Real Estate**")
st.write("Tải video thô lên đây, hệ thống sẽ tự động tạo phụ đề tiếng Việt chuẩn xác cho anh!")

uploaded_file = st.file_uploader("Chọn file video thô của anh (.mp4, .mov):", type=["mp4", "mov"])

def extract_audio_to_wav(video_path, output_wav_path):
    """
    Trích xuất âm thanh từ video sang file wav bằng subprocess với các tham số chuẩn chống lỗi FFmpeg v7.x
    """
    command = [
        "ffmpeg",
        "-y",                   # Ghi đè file nếu đã tồn tại
        "-i", video_path,       # File video đầu vào
        "-vn",                  # Bỏ qua phần hình ảnh
        "-acodec", "pcm_s16le", # Mã hóa âm thanh chuẩn 16-bit PCM
        "-ar", "16000",         # Tần số lấy mẫu 16kHz (phù hợp cho Whisper)
        "-ac", "1",             # Chuyển thành âm thanh đơn kênh (Mono)
        output_wav_path         # File wav đầu ra
    ]
    
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        error_message = result.stderr.decode('utf-8', errors='ignore')
        raise RuntimeError(f"FFmpeg gặp lỗi khi trích xuất âm thanh: {error_message}")
    
    return output_wav_path

if uploaded_file is not None:
    st.success("Đã tải video lên thành công!")
    st.video(uploaded_file)
    
    if st.button("🚀 Bắt đầu để AI xử lý và tạo Sub"):
        with st.spinner("AI Whisper đang nghe audio và tạo phụ đề (quá trình này mất khoảng 1-2 phút)..."):
            # 1. Lưu tạm video vào thư mục của server
            tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            tfile.write(uploaded_file.read())
            tfile.close()  
            video_path = tfile.name

            wav_path = video_path + ".wav"

            try:
                # 2. Trích xuất sang wav an toàn
                extract_audio_to_wav(video_path, wav_path)
                
                # 3. Tải mô hình AI Whisper và dịch
                model = whisper.load_model("base")
                result = model.transcribe(wav_path, language="vi")
                
                st.success("🎉 Đã tạo phụ đề thành công!")
                
                st.markdown("#### 📜 Nội dung phụ đề AI vừa nhận diện:")
                for segment in result["segments"]:
                    start = segment['start']
                    end = segment['end']
                    text = segment['text'].strip() if hasattr(segment['text'], 'strip') else str(segment['text']).strip()
                    st.text(f"[{start:.1f}s --> {end:.1f}s]: {text}")
                    
                # 4. Tạo file srt để tải về
                srt_filename = "subtitles.srt"
                with open(srt_filename, "w", encoding="utf-8") as f:
                    for i, segment in enumerate(result["segments"], start=1):
                        s = segment["start"]
                        e = segment["end"]
                        t = segment["text"].strip()
                        
                        def format_time(seconds):
                            hrs = int(seconds // 3600)
                            mins = int((seconds % 3600) // 60)
                            secs = int(seconds % 60)
                            ms = int((seconds - int(seconds)) * 1000)
                            return f"{hrs:02d}:{mins:02d}:{secs:02d},{ms:03d}"
                        
                        f.write(f"{i}\n{format_time(s)} --> {format_time(e)}\n{t}\n\n")
                
                with open(srt_filename, "rb") as f:
                    st.download_button(
                        label="📥 Tải xuống file phụ đề (.srt)",
                        data=f,
                        file_name="subtitles.srt",
                        mime="text/plain"
                    )

            except Exception as e:
                st.error(f"Đã xảy ra lỗi trong quá trình xử lý: {e}")

            finally:
                # Dọn dẹp file tạm trên server
                if os.path.exists(video_path):
                    os.remove(video_path)
                if os.path.exists(wav_path):
                    os.remove(wav_path)
