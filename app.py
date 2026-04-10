import streamlit as st
from pathlib import Path
from datetime import datetime, timedelta
import uuid

# =========================
# 基本設定
# =========================
st.set_page_config(page_title="文字中轉站", layout="wide")

DATA_DIR = Path("data")
TEXT_DIR = DATA_DIR / "texts"
FILE_DIR = DATA_DIR / "files"

TEXT_DIR.mkdir(parents=True, exist_ok=True)
FILE_DIR.mkdir(parents=True, exist_ok=True)

AUTO_DELETE_DAYS = 14

st.title("📦 文字 / Code 中轉站")
st.caption("可直接打字、貼長文、上傳文字檔，手機與電腦共用")


# =========================
# 工具函式
# =========================
def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def safe_title_name(title: str) -> str:
    return "".join(c for c in title if c not in r'\/:*?"<>|').strip() or "untitled"


def save_text(title: str, content: str, author: str) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    uid = uuid.uuid4().hex[:8]
    safe_title = safe_title_name(title)
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


def list_files(folder: Path) -> list[Path]:
    return sorted(
        [p for p in folder.glob("*") if p.is_file()],
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )


def get_file_age_days(path: Path) -> int:
    modified_time = datetime.fromtimestamp(path.stat().st_mtime)
    age = datetime.now() - modified_time
    return age.days


def delete_file(path: Path) -> tuple[bool, str]:
    try:
        if path.exists() and path.is_file():
            path.unlink()
            return True, f"已刪除：{path.name}"
        return False, f"找不到檔案：{path.name}"
    except Exception as e:
        return False, f"刪除失敗：{path.name}，原因：{e}"


def auto_delete_old_files(folder: Path, max_days: int) -> tuple[int, list[str]]:
    deleted_count = 0
    deleted_names = []
    cutoff_time = datetime.now() - timedelta(days=max_days)

    for path in folder.glob("*"):
        if not path.is_file():
            continue

        try:
            modified_time = datetime.fromtimestamp(path.stat().st_mtime)
            if modified_time < cutoff_time:
                path.unlink()
                deleted_count += 1
                deleted_names.append(path.name)
        except Exception:
            # 自動清理不讓整個頁面報錯，略過有問題的檔案
            continue

    return deleted_count, deleted_names


def run_auto_cleanup() -> tuple[int, list[str]]:
    total_deleted = 0
    all_deleted_names = []

    for folder in [TEXT_DIR, FILE_DIR]:
        deleted_count, deleted_names = auto_delete_old_files(folder, AUTO_DELETE_DAYS)
        total_deleted += deleted_count
        all_deleted_names.extend(deleted_names)

    return total_deleted, all_deleted_names


# =========================
# 自動清除超過 14 天檔案
# =========================
if "cleanup_done" not in st.session_state:
    deleted_count, deleted_names = run_auto_cleanup()
    st.session_state.cleanup_done = True
    st.session_state.cleanup_deleted_count = deleted_count
    st.session_state.cleanup_deleted_names = deleted_names


if st.session_state.get("cleanup_deleted_count", 0) > 0:
    st.info(
        f"系統已自動清除超過 {AUTO_DELETE_DAYS} 天的檔案，共 "
        f"{st.session_state['cleanup_deleted_count']} 個。"
    )


# =========================
# 分頁
# =========================
tab1, tab2, tab3 = st.tabs(["✍️ 直接輸入", "📁 上傳檔案", "📚 查看 / 下載 / 刪除"])


# =========================
# Tab 1：直接輸入
# =========================
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
            path = save_text(
                title=title or "untitled",
                content=content,
                author=author or "unknown"
            )
            st.success(f"已儲存：{path.name}")


# =========================
# Tab 2：上傳檔案
# =========================
with tab2:
    st.subheader("上傳文字檔 / 程式檔")

    uploaded_files = st.file_uploader(
        "可上傳 .txt .py .md .json .csv .log .yaml .yml .ini",
        type=["txt", "py", "md", "json", "csv", "log", "yaml", "yml", "ini"],
        accept_multiple_files=True
    )

    if uploaded_files:
        saved_count = 0
        for f in uploaded_files:
            try:
                save_path = FILE_DIR / f.name
                save_path.write_bytes(f.read())
                saved_count += 1
            except Exception as e:
                st.error(f"上傳失敗：{f.name}，原因：{e}")

        if saved_count > 0:
            st.success(f"已上傳 {saved_count} 個檔案")


# =========================
# Tab 3：查看 / 下載 / 刪除
# =========================
with tab3:
    st.subheader("已儲存內容")

    # ---------- 文字紀錄 ----------
    st.markdown("### 文字紀錄")
    text_files = list_files(TEXT_DIR)

    if not text_files:
        st.info("目前沒有文字紀錄")
    else:
        for p in text_files[:100]:
            age_days = get_file_age_days(p)

            with st.expander(f"📝 {p.name}（{age_days} 天）"):
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

                col1, col2 = st.columns(2)

                with col1:
                    st.download_button(
                        label="下載這份文字",
                        data=content,
                        file_name=p.name,
                        mime="text/plain",
                        key=f"dl_text_{p.name}"
                    )

                with col2:
                    if st.button(
                        "刪除這份文字",
                        key=f"delete_text_{p.name}",
                        type="secondary"
                    ):
                        ok, msg = delete_file(p)
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

    st.divider()

    # ---------- 上傳檔案 ----------
    st.markdown("### 檔案上傳區")
    uploaded_saved_files = list_files(FILE_DIR)

    if not uploaded_saved_files:
        st.info("目前沒有上傳檔案")
    else:
        for p in uploaded_saved_files[:100]:
            age_days = get_file_age_days(p)

            with st.expander(f"📎 {p.name}（{age_days} 天）"):
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

                col1, col2 = st.columns(2)

                with col1:
                    with open(p, "rb") as f:
                        st.download_button(
                            label="下載檔案",
                            data=f,
                            file_name=p.name,
                            key=f"dl_file_{p.name}"
                        )

                with col2:
                    if st.button(
                        "刪除這個檔案",
                        key=f"delete_file_{p.name}",
                        type="secondary"
                    ):
                        ok, msg = delete_file(p)
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

    st.divider()

    # ---------- 手動觸發清理 ----------
    st.markdown("### 清理工具")
    st.caption(f"系統平常會自動清掉超過 {AUTO_DELETE_DAYS} 天的檔案。")

    if st.button("立即執行一次 14 天過期清理"):
        deleted_count, deleted_names = run_auto_cleanup()
        if deleted_count > 0:
            st.success(f"已清除 {deleted_count} 個過期檔案")
        else:
            st.info("沒有需要清除的過期檔案")
        st.rerun()
