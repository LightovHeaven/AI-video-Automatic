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

def generate_cashflow_script(property_data: dict, openai_key: str = "") -> str:
    """Tạo kịch bản bán BĐS dòng tiền (Sử dụng OpenAI API nếu có key, hoặc Template Engine nâng cao)"""
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
            Bạn là chuyên gia marketing bất động sản dòng tiền của kênh 'Hậu Dòng Tiền Real Estate'.
            Hãy viết một kịch bản video ngắn (khoảng 60-90 từ) với phong cách cuốn hút, thực chiến, tập trung vào yếu tố DÒNG TIỀN và GIÁ TRỊ LÃI KÉP:
            - Loại hình/Tên: {title}
            - Vị trí: {location}
            - Diện tích/Quy mô: {area}
            - Giá bán: {price}
            - Dòng tiền khai thác: {cashflow}
            - Lợi thế/Điểm nổi bật: {highlight}
            Yêu cầu: Mở đầu bằng một câu Hook giật tít về dòng tiền, thân bài dứt khoát số liệu, kết bài kêu gọi liên hệ Hậu Dòng Tiền.
            """
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=250
            )
            return response.choices[0].message.content.strip()
        except Exception:
            pass # Tự động fallback về template engine nếu lỗi API

    # Template Engine chuyên sâu cho Bất Động Sản Dòng Tiền
    script = (
        f"Cơ hội sở hữu cỗ máy in tiền thụ động ngay tại {location}! "
        f"Chào mừng quý nhà đầu tư đến với {title}, quy mô {area}. "
        f"Tài sản đang tạo ra dòng tiền cho thuê đều đặn {cashflow}, đạt tỷ suất sinh lời vượt trội so với gửi ngân hàng. "
        f"Đặc biệt: {highlight}. Giá sang nhượng trọn gói chỉ {price}. "
        f"Liên hệ ngay Hậu Dòng Tiền để nhận bảng phân tích tài chính chi tiết từng tháng!"
    )
    return script

def process_video_ffmpeg(video_in: str, srt_in: str, logo_in: str, video_out: str):
    """
    Xử lý FFmpeg nâng cao:
    - Scale Logo phù hợp (chiều ngang 170px) và overlay góc trên bên phải.
    - Nung cứng (hardsub) phụ đề với font chữ viền đen rõ nét.
    - Giữ nguyên luồng âm thanh gốc (-map 0:a?).
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
        # Scale logo chiều rộng về 170px để tránh che khuất màn hình
        filter_steps.append("[1:v]scale=170:-1[logo]")
        # Đóng dấu watermark góc trên bên phải: cách lề phải 25px, lề trên 25px
        filter_steps.append("[0:v][logo]overlay=W-w-25:25[vlogo]")
        # Ép phụ đề lên luồng video đã có watermark
        filter_steps.append(f"[vlogo]subtitles='{escaped_srt}':force_style='{subtitle_style}'[vout]")
    else:
        # Nếu không có logo, chỉ hardsub trực tiếp
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
# GIAO DIỆN NGƯỜI DÙNG (STREAMLIT)
# ==========================================
def main():
    st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>🏢 HẬU DÒNG TIỀN REAL ESTATE</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Hệ thống sản xuất video BĐS tự động hóa: Tạo Kịch Bản AI - Bóc Tách Phụ Đề - Đóng Dấu Bản Quyền</p>", unsafe_allow_html=True)
    st.divider()

    with st.sidebar:
        st.header("⚙️ Cấu hình nâng cao")
        openai_key = st.text_input(
            "OpenAI API Key (Không bắt buộc):",
            type="password",
            help="Nhập key nếu muốn kịch bản biến hóa đa dạng hơn bằng GPT-4o-mini. Để trống sẽ dùng Template Engine mặc định."
        )
        st.info("💡 **Gợi ý**: Video xuất bản sẽ tự động đồng bộ phụ đề gốc và chèn watermark bản quyền nhận diện thương hiệu.")

    col1, col2 = st.columns([1.1, 0.9], gap="large")

    with col1:
        st.subheader("1. Thông tin BĐS khai thác dòng tiền")
        c1, c2 = st.columns(2)
        with c1:
            prop_title = st.text_input("Loại hình / Tiêu đề:", value="Tòa Căn Hộ Dịch Vụ 7 Tầng Thang Máy")
            prop_location = st.text_input("Vị trí tài sản:", value="Mỹ Đình, Nam Từ Liêm, Hà Nội")
            prop_area = st.text_input("Diện tích / Quy mô:", value="85m² x 7 tầng, 18 phòng khép kín")
        with c2:
            prop_price = st.text_input("Giá bán / Sang nhượng:", value="15.8 Tỷ")
            prop_cashflow = st.text_input("Dòng tiền khai thác / tháng:", value="85 Triệu/tháng (Dòng tiền ròng ~6.5%/năm)")
            prop_highlight = st.text_input("Lợi thế cạnh tranh:", value="PCCC chuẩn chỉ, full nội thất, luôn kín phòng")

        st.subheader("2. Tư liệu Media")
        uploaded_video = st.file_uploader(
            "Tải lên video thực tế BĐS (.mp4, .mov):",
            type=["mp4", "mov"],
            help="Video quay thực tế không gian nhà, phòng cho thuê hoặc mặt tiền."
        )
        uploaded_logo = st.file_uploader(
            "Tải lên Logo bản quyền (.png trong suốt):",
            type=["png"],
            help="Logo thương hiệu 'Hậu Dòng Tiền' nền trong suốt để đóng dấu watermark."
        )

        generate_btn = st.button("🚀 Sản xuất Video Bất Động Sản Hoàn Chỉnh", type="primary", use_container_width=True)

    with col2:
        st.subheader("3. Màn hình sản xuất & Thành phẩm")
        output_area = st.container()

    if generate_btn:
        if uploaded_video is None:
            st.error("⚠️ Vui lòng tải lên file video gốc (.mp4 hoặc .mov)!")
            return

        temp_files = []
        try:
            with output_area:
                status_box = st.status("Đang chuẩn bị dữ liệu...", expanded=True)

                # Bước 1: Sinh kịch bản BĐS dòng tiền
                status_box.write("📝 **Bước 1/3**: Khởi tạo kịch bản bán BĐS dòng tiền...")
                prop_data = {
                    "title": prop_title,
                    "location": prop_location,
                    "area": prop_area,
                    "price": prop_price,
                    "cashflow": prop_cashflow,
                    "highlight": prop_highlight
                }
                ai_script = generate_cashflow_script(prop_data, openai_key)
                st.markdown("**📋 Kịch bản gợi ý cho BĐS:**")
                st.info(ai_script)

                # Lưu video gốc vào file tạm
                status_box.write("📥 Đang nạp video đầu vào...")
                vid_suffix = os.path.splitext(uploaded_video.name)[1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=vid_suffix) as tmp_vid:
                    tmp_vid.write(uploaded_video.read())
                    raw_video_path = tmp_vid.name
                temp_files.append(raw_video_path)

                # Lưu logo vào file tạm (nếu có)
                logo_path = ""
                if uploaded_logo is not None:
                    status_box.write("🖼️ Đang nạp logo watermark...")
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_logo:
                        tmp_logo.write(uploaded_logo.read())
                        logo_path = tmp_logo.name
                    temp_files.append(logo_path)

                # Bước 2: Bóc tách phụ đề bằng Whisper
                status_box.write("🎙️ **Bước 2/3**: Whisper đang bóc tách âm thanh sang phụ đề tiếng Việt...")
                whisper_model = load_whisper_model()
                transcribe_res = whisper_model.transcribe(raw_video_path, language="vi", task="transcribe")

                with tempfile.NamedTemporaryFile(delete=False, suffix=".srt") as tmp_srt:
                    srt_path = tmp_srt.name
                temp_files.append(srt_path)

                write_srt_file(transcribe_res.get("segments", []), srt_path)

                # Bước 3: FFmpeg Overlay Logo & Hardsub
                status_box.write("⚡ **Bước 3/3**: FFmpeg đang đóng dấu watermark & nung phụ đề...")
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

                # Hiển thị video thành phẩm
                st.video(final_video_path)

                # Đọc byte và tạo nút tải về
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
            st.error(f"❌ Xảy ra lỗi trong quá trình xử lý: {str(e)}")
        finally:
            # Thu hồi toàn bộ tài nguyên file tạm
            for path in temp_files:
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except Exception:
                        pass

if __name__ == "__main__":
    main()
