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
    page_title="Hậu Dòng Tiền Real Estate | Auto Video Studio & Storytelling AI",
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
    
    /* Header thương hiệu cao cấp */
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
    
    /* Badge DNA Style & Framework */
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
# 3. ĐỊNH NGHĨA 10 STORYTELLING FRAMEWORKS & BRAND DNA
# ==============================================================================
FRAMEWORK_GUIDES = {
    "1. Cấu trúc ba hồi (Mở, Xung đột, Giải quyết)": (
        "Mở đầu thiết lập bối cảnh thị trường/tài sản -> Đẩy mâu thuẫn/áp lực lên đỉnh điểm "
        "(chôn vốn vào đất nền đóng băng, lạm phát bào mòn tài sản) -> Đưa ra giải pháp là tòa BĐS "
        "dòng tiền này giải tỏa toàn bộ áp lực."
    ),
    "2. PAS (Vấn đề, Khuấy sâu, Giải pháp)": (
        "Nêu vấn đề nhức nhối của nhà đầu tư (cầm 20-30 tỷ gửi ngân hàng mất giá, mua đất vùng ven "
        "thanh khoản kém) -> Khuấy sâu nỗi đau (tiền bốc hơi từng ngày, lãi vay đè nặng) -> Giải pháp: "
        "BĐS dòng tiền ven biển Đà Nẵng, gà đẻ trứng vàng hằng tháng."
    ),
    "3. BAB (Trước, Sau, Cầu nối)": (
        "Bức tranh trước khi đầu tư (bất an, loay hoay tìm kênh trú ẩn an toàn) -> Bức tranh tương lai "
        "thịnh vượng (nhận đều đặn 100-150 triệu mỗi tháng, thong dong an nhàn) -> Cầu nối chính là "
        "tài sản dòng tiền đang được giới thiệu."
    ),
    "4. ABT (Và, Nhưng, Vì vậy)": (
        "Bạn sở hữu khối tài sản lớn VÀ luôn muốn dòng vốn sinh sôi an toàn -> NHƯNG thị trường nhiều biến "
        "động, đất nền chôn vốn khiến bạn mất thanh khoản -> VÌ VẬY, tòa căn hộ khai thác dòng tiền ngay "
        "biển Mỹ Khê này là chìa khóa tài chính tối ưu nhất."
    ),
    "5. Hành trình thu nhỏ của nhân vật": (
        "Kể câu chuyện về một nhà đầu tư từng đối mặt ngã rẽ khó khăn -> Vượt qua bẫy 'bánh vẽ tương lai' "
        "nhờ chuyển hướng sang mua giá trị khai thác thật -> Đạt tự do dòng tiền với tài sản triệu đô tại Đà Nẵng."
    ),
    "6. Vòng lặp mở (Open loop)": (
        "Mở đầu bằng nghịch lý gây tò mò tột độ (Ví dụ: 'Tại sao có người sẵn sàng chi 30 tỷ mua tòa nhà này "
        "trong khi lãi suất ngân hàng đang cao?') -> Dẫn dắt lôi cuốn qua số liệu thực chiến -> Khép lại vòng "
        "lặp ở cuối video để kích thích nhà đầu tư hành động ngay."
    ),
    "7. Chi tiết cụ thể, đánh vào giác quan": (
        "Đánh mạnh vào giác quan: ngửi thấy mùi gió biển Mỹ Khê cách vài bước chân, nghe tiếng ting ting "
        "120 triệu tiền thuê phòng đổ về tài khoản mùng 1 hàng tháng, ngắm nhìn tòa nhà 7 tầng full kính rực sáng."
    ),
    "8. Câu chuyện khách hàng (Người thật, số thật)": (
        "Dẫn dắt bằng câu chuyện thực tế của một khách hàng quen từ Hà Nội hoặc Sài Gòn, sở hữu tài sản này, "
        "vận hành tỷ lệ lấp đầy 95%, dòng tiền thật chứng minh qua sao kê ngân hàng."
    ),
    "9. Một ngày trong đời (Cảm giác sở hữu/an tâm)": (
        "Khắc họa một ngày thảnh thơi của chủ nhân: Thức dậy thong dong uống cà phê ngắm biển Đà Nẵng, "
        "không phải bận tâm quản lý vì đơn vị chuyên nghiệp vận hành, dòng tiền tự động chảy về tài khoản."
    ),
    "10. Câu chuyện khởi nguồn (Xây dựng niềm tin cá nhân)": (
        "Chia sẻ chân thành từ chính góc nhìn của Anh Hậu Dòng Tiền: Lý do anh kiên định chỉ chọn và phân tích "
        "BĐS dòng tiền thật tại Đà Nẵng để giúp các nhà đầu tư lớn bảo vệ vốn tuyệt đối trước chu kỳ thị trường."
    )
}

BRAND_SYSTEM_INSTRUCTION = (
    "Bạn là Giám đốc Sáng tạo và Trợ lý Truyền thông độc quyền cho thương hiệu 'Hậu Dòng Tiền Real Estate' "
    "tại Đà Nẵng. Anh Hậu là chuyên gia thực chiến phân khúc BĐS dòng tiền, đất ven biển, tòa căn hộ dịch vụ "
    "và khách sạn từ 10 - 50 tỷ đồng.\n\n"
    "NGUYÊN TẮC BRAND DNA BẮT BUỘC:\n"
    "1. Định vị: Uy quyền, bản lĩnh, sâu sắc, thực chiến, am hiểu tường tận thị trường Đà Nẵng.\n"
    "2. Triết lý đầu tư: 'Mua giá trị khai thác hiện hữu, không mua bánh vẽ tương lai'. BĐS dòng tiền ven biển "
    "chính là bức tường lửa vững chắc nhất bảo vệ vốn trước lạm phát.\n"
    "3. Cấu trúc kịch bản: Thời lượng chuẩn 35 - 45 giây (khoảng 110 - 140 từ tiếng Việt), nhịp điệu dứt khoát.\n"
    "   - 3 giây đầu (Hook): Giật tít cực mạnh, đánh thẳng nỗi đau hoặc con số doanh thu/vị trí đắt giá.\n"
    "   - Thân bài (Body): Cảm xúc trước - lý trí sau, minh chứng bằng số liệu cụ thể (diện tích, dòng tiền/tháng, tỷ suất).\n"
    "   - Kết bài (CTA): Kêu gọi dứt khoát kết nối với Anh Hậu để nhận hồ sơ pháp lý và thẩm định quy hoạch.\n"
    "4. BẮT BUỘC: Chỉ xuất duy nhất phần lời thoại để thu âm/lồng tiếng, tuyệt đối không chèn ký hiệu cảnh quay, "
    "không ngoặc đơn chú thích [Hook], [Body], [CTA] vào văn bản."
)


# ==============================================================================
# 4. TRẠM AI KỊCH BẢN: CƠ CHẾ RETRY & FALLBACK KHI GẶP LỖI 503
# ==============================================================================
def generate_real_estate_script(api_key: str, content_type: str, framework_name: str, details: dict) -> str:
    """
    Sinh kịch bản video BĐS dòng tiền với cơ chế tự động Retry (Exponential Backoff)
    và Fallback Model (gemini-3.8-flash -> gemini-2.5-flash) khi gặp lỗi 503 hoặc quá tải.
    """
    models_priority = ["gemini-3.8-flash", "gemini-2.5-flash"]
    client = genai.Client(api_key=api_key)
    framework_guide = FRAMEWORK_GUIDES.get(framework_name, "")

    if content_type == "Giới thiệu Tài sản Dòng Tiền Thực Tế":
        prompt = (
            f"Hãy viết kịch bản video giới thiệu tài sản dòng tiền thực tế áp dụng phương pháp kể chuyện: "
            f"'{framework_name}'.\n"
            f"Hướng dẫn phương pháp: {framework_guide}\n\n"
            f"THÔNG SỐ BẤT ĐỘNG SẢN:\n"
            f"- Tên / Loại hình: {details.get('title', 'Tòa Căn Hộ Dịch Vụ')}\n"
            f"- Vị trí: {details.get('location', 'Gần biển Mỹ Khê, Ngũ Hành Sơn, Đà Nẵng')}\n"
            f"- Diện tích & Kết cấu: {details.get('spec', '120m2, 7 tầng thang máy, 16 phòng studio')}\n"
            f"- Mức giá chào bán: {details.get('price', '25 tỷ')}\n"
            f"- Doanh thu khai thác dòng tiền: {details.get('cashflow', '120 triệu/tháng')}\n"
            f"- Điểm mạnh pháp lý/vận hành: {details.get('highlights', 'Full phòng quanh năm, PCCC chuẩn nghiệm thu')}"
        )
    else:
        prompt = (
            f"Hãy viết kịch bản video chia sẻ tư duy/kinh nghiệm đầu tư BĐS dòng tiền áp dụng phương pháp kể chuyện: "
            f"'{framework_name}'.\n"
            f"Hướng dẫn phương pháp: {framework_guide}\n\n"
            f"THÔNG TIN CHỦ ĐỀ ĐẦU TƯ:\n"
            f"- Chủ đề cốt lõi: {details.get('topic', 'Đất nền phân lô vs Tòa căn hộ dòng tiền ven biển')}\n"
            f"- Góc nhìn thực chiến: {details.get('insight', 'Bất động sản sinh ra dòng tiền hàng tháng là bức tường lửa bảo vệ vốn trước lạm phát')}\n"
            f"- Bài học đúc kết: {details.get('advice', 'Đừng mua kỳ vọng tương lai mà hãy mua giá trị khai thác hiện hữu')}"
        )

    last_error = None

    for model_idx, model_name in enumerate(models_priority):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=BRAND_SYSTEM_INSTRUCTION,
                        temperature=0.75,
                        max_output_tokens=400
                    )
                )
                if response.text:
                    if model_idx > 0:
                        st.toast(f"✅ Đã tạo kịch bản thành công bằng Model dự phòng: {model_name}!", icon="🛡️")
                    return response.text.strip()
            except Exception as e:
                last_error = e
                err_msg = str(e)
                
                # Nếu chưa hết số lần thử của model hiện tại: Áp dụng Exponential Backoff (2s, 4s)
                if attempt < max_retries - 1:
                    wait_seconds = 2 * (attempt + 1)
                    st.toast(
                        f"⏳ Máy chủ {model_name} phản hồi bận (503). Đang tự động thử lại ({attempt + 1}/{max_retries}) sau {wait_seconds}s...",
                        icon="🔄"
                    )
                    time.sleep(wait_seconds)
                else:
                    # Nếu hết lượt thử của model hiện tại và còn model dự phòng: Chuyển Model
                    if model_idx < len(models_priority) - 1:
                        fallback_model = models_priority[model_idx + 1]
                        st.toast(
                            f"⚠️ {model_name} quá tải sau 3 lần thử. Đang tự động kích hoạt Model dự phòng: {fallback_model}...",
                            icon="🔀"
                        )
                    break

    raise RuntimeError(f"Tất cả các Model AI ({', '.join(models_priority)}) đều gặp lỗi máy chủ: {str(last_error)}")


def learn_style_and_generate_script(
    api_key: str,
    video_sample_path: str,
    content_type: str,
    framework_name: str,
    details: dict
) -> tuple[str, str]:
    """Sử dụng Gemini Vision phân tích video mẫu kết hợp Storytelling Framework cùng cơ chế Retry/Fallback."""
    models_priority = ["gemini-3.8-flash", "gemini-2.5-flash"]
    client = genai.Client(api_key=api_key)
    uploaded_file = None
    framework_guide = FRAMEWORK_GUIDES.get(framework_name, "")

    try:
        uploaded_file = client.files.upload(file=video_sample_path)
        while uploaded_file.state.name == "PROCESSING":
            time.sleep(2)
            uploaded_file = client.files.get(name=uploaded_file.name)
            
        if uploaded_file.state.name == "FAILED":
            raise RuntimeError("Gemini không thể xử lý video mẫu này. Vui lòng thử video dung lượng nhẹ hơn.")

        prompt = (
            f"BƯỚC 1: Hãy xem kỹ video mẫu được đính kèm và trích xuất DNA phong cách:\n"
            f"- Kỹ thuật giật Hook 3s đầu của người nói.\n"
            f"- Tốc độ nhả chữ, nhịp điệu ngắt nghỉ và cách dẫn dắt logic.\n"
            f"- Đòn chốt CTA kêu gọi hành động.\n\n"
            f"BƯỚC 2: Kết hợp DNA nhịp điệu từ video mẫu VÀ Phương pháp kể chuyện '{framework_name}' "
            f"({framework_guide}) để viết một kịch bản thoại mới chuẩn 35-45 giây (110-140 từ tiếng Việt) "
            f"cho dữ liệu tài sản sau:\n"
            f"- Loại nội dung: {content_type}\n"
            f"- Thông tin: {details}\n\n"
            f"ĐỊNH DẠNG ĐẦU RA BẮT BUỘC (phân tách bởi ===SCRIPT_SPLIT===):\n"
            f"[Tóm tắt ngắn gọn DNA học được từ video mẫu và cách vận dụng Framework {framew