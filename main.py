# ==============================================================
#  Streamlit NLP Pipeline Demo — v2 (2 ứng dụng)
#  App 1: Dịch văn bản  ·  App 2: Sửa lỗi chính tả
# ==============================================================
import langcodes
import streamlit as st
from deep_translator import GoogleTranslator
from langdetect import DetectorFactory, LangDetectException, detect
from nltk.tokenize import TreebankWordDetokenizer, wordpunct_tokenize
from spellchecker import SpellChecker

DetectorFactory.seed = 0 #dùng để cố định kết quả nhận diện ngôn ngữ, đảm bảo tính nhất quán sau mỗi lần chạy code
MIN_INPUT_LENGTH = 3 # độ dài của văn bản cần xử lý ít nhất là 3 kí tự

# pyspellchecker chỉ hỗ trợ một số ngôn ngữ
SPELL_LANGS = {"en", "es", "fr", "pt", "de", "ru", "ar", "eu", "lv", "nl"}

# Ngôn ngữ đích cho App 1
TARGET_LANGS = {
    "Tiếng Việt": "vi",
    "Tiếng Anh": "en",
    "Tiếng Pháp": "fr",
    "Tiếng Nhật": "ja",
    "Tiếng Trung (Giản thể)": "zh-cn",
    "Tiếng Trung (Phồn thể)": "zh-tw",
    "Tiếng Hàn": "ko",
    "Tiếng Tây Ban Nha": "es",
    "Tiếng Đức": "de",
}

# Ví dụ mẫu hiện lên trên UI cho người dùng biết cách nhập liệu
EXAMPLES_T = [
    "Every morning, I drink a cup of coffee.",
    "Bonjour, comment allez-vous?",
    "Xin chào, hôm nay trời đẹp quá.",
]

# Ví dụ mẫu hiện lên trên UI cho người dùng biết cách nhập liệu
EXAMPLES_S = [
    "Yesturday, I recieveed a mesage from my freind.",
    "Definately a great oppurtunity.",
    "Je voudraiis allerr au marchee.",
]


# Lưu bộ kiểm tra chính tả vào bộ nhớ đệm để không cần chạy lại mỗi lần gọi hàm
@st.cache_resource(show_spinner=False)
def get_spellchecker(code):
    return SpellChecker(language=code)

# Check ngôn ngữ có được hỗ trợ hay không
def language_name(code):
    try:
        return langcodes.Language.get(code).display_name()
    except Exception:
        return code or "Unknown"

# Trả về ngôn ngữ của văn bản đầu vào
def detect_language(raw):
    try:
        return detect(raw)
    except LangDetectException:
        return None

# Sửa lỗi chính tả
def fix_typos(text, code):
    spell = get_spellchecker(code) # gọi hàm sửa lỗi chính tả
    tokens = wordpunct_tokenize(text) # tách đoạn văn bản gốc thành các token
    fixed = []
    for token in tokens:
        if token.isalpha() and len(token) > 1: # check xem token là những chữ cái thuần túy và độ dài lớn hơn 1
            suggestion = spell.correction(token.lower()) or token # tìm từ đúng, nếu token đã đúng hoặc k tìm từ thích hợp hơn thì trả về token
            suggestion = suggestion.title() if token.istitle() else suggestion # trả về format ban đầu
            suggestion = suggestion.upper() if token.isupper() else suggestion # trả về format ban đầu
            fixed.append(suggestion) # append vào biến kết quả
        else:
            fixed.append(token)
    return TreebankWordDetokenizer().detokenize(fixed), fixed != tokens # ghép các token trong list thành 1 đoạn văn bản, check xem văn bản đã sửa có giống với văn bản ban đầu không


# Dịch văn bản
def run_translation(text, target_code):
    raw = text.strip()
    if len(raw) < MIN_INPUT_LENGTH:
        return {"ok": False, "error": f"Nhập tối thiểu {MIN_INPUT_LENGTH} ký tự."}

    source = detect_language(raw)
    if source is None:
        return {"ok": False, "error": "Không nhận diện được ngôn ngữ."}

    if source == target_code:
        return {
            "ok": True,
            "source": language_name(source),
            "target": language_name(target_code),
            "translated": raw,
            "note": "Câu đã ở ngôn ngữ đích, không cần dịch.",
        }

    try:
        translated = GoogleTranslator(source=source, target=target_code).translate(raw) # gọi hàm dịch của Google
    except Exception as e:
        return {"ok": False, "error": f"Lỗi dịch: {e}"}

    return {
        "ok": True,
        "source": language_name(source),
        "target": language_name(target_code),
        "translated": translated,
    }

# Chỉnh sửa lỗi văn bản
def run_spellcheck(text):
    raw = text.strip()
    if len(raw) < MIN_INPUT_LENGTH:
        return {"ok": False, "error": f"Nhập tối thiểu {MIN_INPUT_LENGTH} ký tự."}

    code = detect_language(raw)
    if code is None:
        return {"ok": False, "error": "Không nhận diện được ngôn ngữ."}

    if code not in SPELL_LANGS:
        return {
            "ok": False,
            "error": f"pyspellchecker chưa hỗ trợ {language_name(code)} ({code}).",
        }

    fixed, changed = fix_typos(raw, code)
    return {
        "ok": True,
        "language": language_name(code),
        "fixed": fixed,
        "changed": changed,
    }


# ---------------- UI ----------------
st.set_page_config(page_title="NLP Pipeline", layout="centered")
st.title("Streamlit NLP Pipeline")
st.caption("Hai ứng dụng: Dịch văn bản · Sửa lỗi chính tả")

tab_t, tab_s = st.tabs(["Dịch văn bản", "Sửa lỗi chính tả"])


# ===== Tab 1: Translation =====
with tab_t:
    st.session_state.setdefault("res_t", None) #khởi tạo biến toàn cục res_t, nhằm giữ lại kết quả trên màn hình khi ứng dụng rerun

    with st.expander("Ví dụ"): # hiển thị một số câu ví dụ đã định nghĩa ở trên
        for ex in EXAMPLES_T:
            st.markdown(f"- {ex}")

    with st.form("form_translate"):
        text_t = st.text_area("Câu cần dịch", height=90,
                              placeholder="Nhập câu ở bất kỳ ngôn ngữ nào...")
        target = st.selectbox("Dịch sang", list(TARGET_LANGS.keys()))
        submitted_t = st.form_submit_button("Dịch", type="primary")

    if submitted_t:
        st.session_state.res_t = run_translation(text_t, TARGET_LANGS[target]) # dịch

    res = st.session_state.res_t
    if res:
        if res["ok"]: # check đã dịch thành công
            st.caption(f"Nguồn: {res['source']}  →  Đích: {res['target']}") # hiển thị ngôn ngữ nguồn đến đích
            st.success(res["translated"]) # hiển thị văn bản được dịch
            if res.get("note"):
                st.info(res["note"]) # nếu kêt quả dịch có kèm ghi chú, sẽ hiện phần ghi chú này trong phần khác
        else:
            st.warning(res["error"]) # hiện error khi dịch không thành công


# ===== Tab 2: Spell check =====
with tab_s:
    st.session_state.setdefault("res_s", None) # biến khởi tạo như trên

    with st.expander("Ví dụ"):
        for ex in EXAMPLES_S:
            st.markdown(f"- {ex}")
    st.caption(f"Hỗ trợ: {', '.join(sorted(SPELL_LANGS))}")

    with st.form("form_spell"):
        text_s = st.text_area("Câu cần kiểm tra", height=90,
                              placeholder="Nhập câu để kiểm tra chính tả...")
        submitted_s = st.form_submit_button("Kiểm tra", type="primary")

    if submitted_s:
        st.session_state.res_s = run_spellcheck(text_s)

    res = st.session_state.res_s
    if res:
        if res["ok"]: # check có sửa lỗi thành công không
            st.caption(f"Ngôn ngữ: {res['language']}") # hiện ngôn ngữ gốc
            st.success(res["fixed"])  # hiện kết quả sửa loại
            st.caption("Có sửa lỗi chính tả" if res["changed"] else "Không phát hiện lỗi") # nếu có lỗi sẽ hiện có sửa lỗi chính tả
        else:
            st.warning(res["error"]) # hiển thị khi có error
