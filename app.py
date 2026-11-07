
import streamlit as st

from rag import ask_rag


# ==========================================
# PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="AAUP Smart Academic Advisor",
    page_icon="🎓",
    layout="centered"
)


# ==========================================
# RTL DESIGN
# ==========================================

st.markdown(
    """
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

    [data-testid="stChatMessageContent"] {
        direction: rtl;
        text-align: right;
        unicode-bidi: plaintext;
    }

    code {
        direction: ltr;
        unicode-bidi: isolate;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ==========================================
# SESSION STATE
# ==========================================

if "messages" not in st.session_state:
    st.session_state.messages = []


def clear_chat():
    st.session_state.messages = []


# ==========================================
# HEADER
# ==========================================

st.title("🎓 المرشد الأكاديمي الذكي")

st.caption(
    "الجامعة العربية الأمريكية | "
    "AAUP Smart Academic Advisor"
)

st.info(
    "اسأل عن التعليمات الأكاديمية، التسجيل، "
    "الغياب، المعدلات، الإنذارات الأكاديمية، "
    "والخطط الدراسية."
)


# ==========================================
# SIDEBAR
# ==========================================

with st.sidebar:

    st.header("🎓 المرشد الأكاديمي")

    st.button(
        "🔄 محادثة جديدة",
        on_click=clear_chat,
        use_container_width=True
    )

    st.divider()

    st.subheader("أسئلة مقترحة")

    suggested_questions = [
        "ما المتطلب السابق لمساق COMP336؟",
        "كم عدد ساعات خطة علم الحاسوب؟",
        "ما هي شروط الإنذار الأكاديمي؟",
        "ما هي شروط التخرج من الجامعة؟"
    ]

    for index, suggested_question in enumerate(
        suggested_questions
    ):
        if st.button(
            suggested_question,
            key=f"suggested_{index}",
            use_container_width=True
        ):
            st.session_state.pending_question = (
                suggested_question
            )


# ==========================================
# DISPLAY CHAT HISTORY
# ==========================================

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ==========================================
# USER INPUT
# ==========================================

typed_question = st.chat_input(
    "اكتب سؤالك الأكاديمي هنا..."
)

pending_question = st.session_state.pop(
    "pending_question",
    None
)

question = typed_question or pending_question


# ==========================================
# PROCESS QUESTION
# ==========================================

if question:

    question = question.strip()

    if question:

        st.session_state.messages.append({
            "role": "user",
            "content": question
        })

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):

            with st.spinner(
                "جاري البحث في تعليمات الجامعة..."
            ):

                try:

                    answer = ask_rag(question)

                except Exception as error:

                    print(
                        "RAG Error:",
                        repr(error),
                        flush=True
                    )

                    st.error(
                        "حدث خطأ أثناء معالجة السؤال. "
                        "يرجى المحاولة مرة أخرى."
                    )

                    st.stop()

            st.markdown(answer)

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })
