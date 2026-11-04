import streamlit as st
import os
import tempfile
import whisper

# -----------------------------------------------------------------------------
# CẤU HÌNH GIAO DIỆN STREAMLIT
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Video Subtitle - Hậu Dòng Tiền Real Estate",
    page_icon="🎬",
    layout="centered"
)

# -----------------------------------------------------------------------------
# HÀM BỔ TRỢ & CACHE MODEL
# -----------------------------------------------------------------------------
@st.cache_resource(show_spinner="Đang khởi tạo mô hình Whisper AI...")
def load_whisper_model(model_name="base"):
    """
    Tải và cache mô hình Whisper vào bộ nhớ RAM.
    Giúp tránh việc phải tải lại model mỗi lần người dùng bấm nút.
    """
    return whisper.load_model(model_name)

def format_time_srt(seconds: float) -> str:
    """Chuyển đổi số giây sang định dạng chuẩn SRT (HH:MM:SS,mmm)."""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{ms:03d}"

def generate_srt_content(segments: list) -> str:
    """Tạo chuỗi nội dung file .srt trực tiếp trên RAM, không cần ghi đè file rác."""
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
st.title("🎬 Ứng Dụng AI Tự Động Bóc Tách Phụ Đề Video")
st.markdown("### Thương hiệu: **Hậu Dòng Tiền Real Estate** 🏢")
st.caption("Công cụ hỗ trợ bóc tách âm thanh, nhận diện tiếng Việt và xuất file phụ đề chuẩn xác.")

# Tùy chọn mô hình
with st.expander("⚙️ Tùy chọn cấu hình AI", expanded=False):
    model_choice = st.selectbox(
        "Chọn kích thước mô hình (Mặc định 'base' là tối ưu nhất cho Streamlit Cloud):",
        options=["tiny", "base", "small"],
        index=1,
        help="'tiny' nhanh nhất nhưng kém chính xác; 'base' cân bằng tốt; 'small' chính xác hơn nhưng tốn RAM hơn."
    )

uploaded_file = st.file_uploader(
    "Chọn file video của anh (.mp4, .mov, .mkv, .mp3):", 
    type=["mp4", "mov", "mkv", "mp3", "m4a"]
)

if uploaded_file is not None:
    st.success(f"Đã nhận file: **{uploaded_file.name}** ({uploaded_file.size / (1024 * 1024):.2f} MB)")
    
    # Hiển thị video preview
    if uploaded_file.type.startswith("video"):
        st.video(uploaded_file)
    elif uploaded_file.type.startswith("audio"):
        st.audio(uploaded_file)
    
    if st.button("🚀 Bắt đầu nhận diện & Tạo Sub", type="primary"):
        # Lấy đuôi file mở rộng thực tế
        suffix = os.path.splitext(uploaded_file.name)[-1].lower() or ".mp4"
        
        temp_video_path = None
        try:
            # 1. Lưu file tạm và đóng stream (BẮT BUỘC ĐỂ KHẮC PHỤC LỖI FFMPEG)
            with st.spinner("Đang lưu trữ dữ liệu tạm thời..."):
                tfile = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
                tfile.write(uploaded_file.read())
                temp_video_path = tfile.name
                tfile.flush()
                tfile.close()  # <-- Đóng file để nhường quyền truy cập cho FFmpeg

            # 2. Chạy mô hình Whisper
            with st.spinner(f"AI Whisper ({model_choice}) đang nghe và bóc tách tiếng Việt... Vui lòng đợi trong giây lát."):
                model = load_whisper_model(model_choice)
                
                # Chạy bóc tách âm thanh
                result = model.transcribe(
                    temp_video_path,
                    language="vi",
                    fp16=False,            # Tắt fp16 vì Streamlit Cloud chạy CPU
                    verbose=False
                )

            st.success("🎉 Đã tạo phụ đề thành công!")

            # 3. Tạo nội dung file SRT & nút tải về
            srt_content = generate_srt_content(result.get("segments", []))
            base_filename = os.path.splitext(uploaded_file.name)[0]
            
            st.download_button(
                label="📥 Tải xuống file phụ đề (.srt)",
                data=srt_content.encode("utf-8"),
                file_name=f"{base_filename}_subtitles.srt",
                mime="text/plain",
                type="primary"
            )

            # 4. Hiển thị nội dung phụ đề trực quan
            st.markdown("#### 📜 Danh sách đoạn hội thoại đã nhận diện:")
            segments = result.get("segments", [])
            
            if not segments:
                st.warning("Không tìm thấy đoạn hội thoại nào trong video/audio.")
            else:
                sub_container = st.container(height=320)
                with sub_container:
                    for seg in segments:
                        start_time = format_time_srt(seg['start'])
                        end_time = format_time_srt(seg['end'])
                        text = seg['text'].strip()
                        st.markdown(f"⏱️ **`{start_time} --> {end_time}`** : {text}")

        except Exception as e:
            st.error(f"❌ Đã xảy ra lỗi trong quá trình xử lý: {str(e)}")
            st.info("💡 Mẹo: Nếu video quá dài hoặc dung lượng lớn, hãy nén nhẹ video trước khi tải lên.")

        finally:
            # Dọn dẹp file tạm trên server để tránh đầy bộ nhớ
            if temp_video_path and os.path.exists(temp_video_path):
                try:
                    os.remove(temp_video_path)
                except Exception:
                    pass
