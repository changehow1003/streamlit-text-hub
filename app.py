import streamlit as st
from pathlib import Path
from datetime import datetime
import uuid

st.set_page_config(page_title="文字中轉站", layout="wide")

DATA_DIR = Path("data")
TEXT_DIR = DATA_DIR / "texts"
FILE_DIR = DATA_DIR / "files"

TEXT_DIR.mkdir(parents=True, exist_ok=True)
FILE_DIR.mkdir(parents=True, exist_ok=True)

st.title("📦 文字 / Code 中轉站")
st.caption("可直接打字、貼長文、上傳文字檔，手機與電腦共用")

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def save_text(title: str, content: str, author: str):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    uid = uuid.uuid4().hex[:8]
    safe_title = "".join(c for c in title if c not in r'\/:*?"<>|').strip() or "untitled"
    filename = f"{ts}_{uid}_{safe_title}.txt"
    path = TEXT_DIR / filename

    full_text = (
        f"標題: {title}\n"
        f"作者: {author}\n"
        f"時間: {now_str()}\n"
        f"{'-'*60}\n"
        f"{content}"
    )
    path.write_text(full_text, encoding="utf-8")
    return path

def list_files(folder: Path):
    return sorted(folder.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)

tab1, tab2, tab3 = st.tabs(["✍️ 直接輸入", "📁 上傳檔案", "📚 查看與下載"])

with tab1:
    st.subheader("直接輸入文字 / Code")

    with st.form("text_form", clear_on_submit=False):
        author = st.text_input("作者 / 裝置名稱", value="手機")
        title = st.text_input("標題", value="")
        content = st.text_area(
            "內容",
            value="",
            height=400,
            max_chars=None,
            placeholder="可直接貼上 code、筆記、訊息..."
        )
        submitted = st.form_submit_button("儲存文字")

    if submitted:
        if not content.strip():
            st.warning("內容不能空白")
        else:
            path = save_text(title=title or "untitled", content=content, author=author or "unknown")
            st.success(f"已儲存：{path.name}")

with tab2:
    st.subheader("上傳文字檔 / 程式檔")

    uploaded_files = st.file_uploader(
        "可上傳 .txt .py .md .json .csv .log .yaml .yml .ini",
        type=["txt", "py", "md", "json", "csv", "log", "yaml", "yml", "ini"],
        accept_multiple_files=True
    )

    if uploaded_files:
        for f in uploaded_files:
            save_path = FILE_DIR / f.name
            save_path.write_bytes(f.read())
        st.success(f"已上傳 {len(uploaded_files)} 個檔案")

with tab3:
    st.subheader("已儲存內容")

    st.markdown("### 文字紀錄")
    text_files = list_files(TEXT_DIR)

    if not text_files:
        st.info("目前沒有文字紀錄")
    else:
        for p in text_files[:100]:
            with st.expander(f"📝 {p.name}"):
                try:
                    content = p.read_text(encoding="utf-8")
                except Exception as e:
                    content = f"讀取失敗：{e}"

                st.text_area(
                    f"preview_{p.name}",
                    value=content,
                    height=250,
                    disabled=True,
                    label_visibility="collapsed"
                )

                st.download_button(
                    label="下載這份文字",
                    data=content,
                    file_name=p.name,
                    mime="text/plain",
                    key=f"dl_text_{p.name}"
                )

    st.markdown("### 檔案上傳區")
    uploaded_saved_files = list_files(FILE_DIR)

    if not uploaded_saved_files:
        st.info("目前沒有上傳檔案")
    else:
        for p in uploaded_saved_files[:100]:
            with st.expander(f"📎 {p.name}"):
                suffix = p.suffix.lower()

                if suffix in [".txt", ".py", ".md", ".json", ".csv", ".log", ".yaml", ".yml", ".ini"]:
                    try:
                        content = p.read_text(encoding="utf-8")
                        st.text_area(
                            f"file_preview_{p.name}",
                            value=content,
                            height=250,
                            disabled=True,
                            label_visibility="collapsed"
                        )
                    except Exception as e:
                        st.warning(f"無法以文字預覽：{e}")

                with open(p, "rb") as f:
                    st.download_button(
                        label="下載檔案",
                        data=f,
                        file_name=p.name,
                        key=f"dl_file_{p.name}"
                    )
