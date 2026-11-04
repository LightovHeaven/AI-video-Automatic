import streamlit as st
import os
import tempfile

st.set_page_config(page_title="AI Video Automatic - Hậu Dòng Tiền", page_icon="🎬")

st.title("🎬 Ứng Dụng AI Tự Động Xử Lý Video Bất Động Sản")
st.markdown("### Thương hiệu: **Hậu Dòng Tiền Real Estate**")
st.write("Tải video thô lên đây, hệ thống sẽ tự động tạo phụ đề tiếng Việt chuẩn xác cho anh!")

uploaded_file = st.file_uploader("Chọn file video thô của anh (.mp4, .mov):", type=["mp4", "mov"])

if uploaded_file is not None:
    st.success("Đã tải video lên thành công!")
    st.video(uploaded_file)
    
    if st.button("🚀 Bắt đầu để AI xử lý và tạo Sub"):
        with st.spinner("AI Whisper đang nghe audio và tạo phụ đề (quá trình này mất khoảng 1-2 phút)..."):
            # Lưu tạm video vào thư mục của server
            tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            tfile.write(uploaded_file.read())
            video_path = tfile.name

            import whisper
            # Tải mô hình AI Whisper bản base
            model = whisper.load_model("base")
            result = model.transcribe(video_path, language="vi")
            
            st.success("🎉 Đã tạo phụ đề thành công!")
            
            st.markdown("#### 📜 Nội dung phụ đề AI vừa nhận diện:")
            for segment in result["segments"]:
                start = segment['start']
                end = segment['end']
                text = segment['text'].strip()
                st.text(f"[{start:.1f}s --> {end:.1f}s]: {text}")
                
            # Lưu file srt
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
