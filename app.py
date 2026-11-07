
import streamlit as st
from rag import ask_rag

st.set_page_config(
    page_title="AAUP Smart Academic Advisor",
    page_icon="🎓",
    layout="centered"
)

st.markdown("""
<style>
.stApp {
    direction: rtl;
}
h1, h2, h3, p {
    text-align: right;
}
[data-testid="stChatMessage"] {
    direction: rtl;
    text-align: right;
}
[data-testid="stChatInput"] {
    direction: rtl;
}
</style>
""", unsafe_allow_html=True)

st.title("🎓 المرشد الأكاديمي الذكي")
st.caption("الجامعة العربية الأمريكية | AAUP Smart Academic Advisor")

st.info(
    "اسأل عن التعليمات الأكاديمية، التسجيل، "
    "الغياب، المعدلات، والإنذارات الأكاديمية."
)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input("اكتب سؤالك الأكاديمي هنا...")

if question:
    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("جاري البحث في تعليمات الجامعة..."):
            try:
                answer = ask_rag(question)
            except Exception as error:
                print("RAG Error:", error)
                answer = (
                    "حدث خطأ أثناء معالجة السؤال. "
                    "يرجى المحاولة مرة أخرى."
                )

        st.markdown(answer)

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })
