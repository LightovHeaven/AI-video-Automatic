import streamlit as st

st.set_page_config(page_title="AI Video Automatic", page_icon="🎬")

st.title("🎬 AI Video Automatic - Hậu Dòng Tiền Real Estate")
st.write("Ứng dụng tự động tạo phụ đề và xử lý video bất động sản chuyên nghiệp.")

uploaded_file = st.file_uploader("Tải video thô của anh lên đây (định dạng .mp4, .mov):", type=["mp4", "mov"])

if uploaded_file is not None:
    st.success("Đã tải video lên thành công!")
    st.video(uploaded_file)
    st.info("Hệ thống AI đang sẵn sàng để xử lý video của anh.")
