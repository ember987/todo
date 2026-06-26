"""
할 일 관리 앱 (Streamlit 버전)

- 할 일 추가 / 수정 / 삭제
- 완료 체크
- 카테고리 분류 (업무 / 개인 / 공부)
- 키워드 기반 자동 카테고리 분류 (🤖 자동 분류)
- 진행률 보기
- JSON 파일에 저장 → 새로고침해도 데이터 유지

실행: streamlit run app.py
"""

import json
import uuid
from datetime import datetime
from pathlib import Path

import streamlit as st

# ---------- 설정 ----------
DATA_FILE = Path(__file__).parent / "todos.json"

AUTO = "auto"  # 자동 분류 선택값

# 카테고리 코드 -> 한글 라벨
CATEGORY_LABELS = {
    "work": "업무",
    "personal": "개인",
    "study": "공부",
}
# 카테고리별 색상 (뱃지용)
CATEGORY_COLORS = {
    "work": "#f97316",      # 주황
    "personal": "#10b981",  # 초록
    "study": "#8b5cf6",     # 보라
}

# ---------- 키워드 기반 자동 분류 ----------
# 텍스트에 아래 키워드가 포함되면 해당 카테고리로 자동 분류한다.
# (한글 키워드는 부분 일치, 영어 키워드는 소문자로 부분 일치)
CATEGORY_KEYWORDS = {
    "work": [
        "회의", "미팅", "보고서", "보고", "발표", "프로젝트", "업무", "메일", "이메일",
        "클라이언트", "고객사", "결재", "출장", "계약", "기획", "제안서", "마감", "납기",
        "협업", "회사", "팀", "리뷰", "킥오프", "스프린트", "배포", "릴리즈",
        "meeting", "report", "project", "deadline", "email", "client", "work",
    ],
    "study": [
        "공부", "강의", "인강", "수업", "시험", "과제", "숙제", "영어", "단어", "암기",
        "독서", "책", "문제", "알고리즘", "자격증", "복습", "예습", "스터디", "논문",
        "코딩", "토익", "수학", "강좌", "리포트",
        "study", "exam", "homework", "lecture", "quiz", "algorithm", "english",
    ],
    "personal": [
        "운동", "헬스", "조깅", "러닝", "요가", "병원", "약속", "장보기", "쇼핑", "청소",
        "빨래", "요리", "은행", "친구", "가족", "약", "미용실", "여행", "식사", "점심",
        "저녁", "취미", "휴식", "산책", "마트", "택배",
        "gym", "workout", "shopping", "hospital", "personal", "family",
    ],
}


def classify_category(text):
    """텍스트의 키워드를 보고 카테고리를 추론한다.
    매칭이 없으면 'personal'(개인)로 폴백한다.
    여러 카테고리에 매칭되면 가장 많이 매칭된 카테고리를 선택한다."""
    lowered = text.lower()
    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        scores[category] = sum(1 for kw in keywords if kw.lower() in lowered)

    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "personal"  # 매칭 키워드 없음 -> 기본값
    return best


# ---------- 데이터 영속성 ----------
def load_todos():
    """JSON 파일에서 할 일 목록을 불러온다. 파일이 없거나 손상되면 빈 목록."""
    if not DATA_FILE.exists():
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        # 손상된 데이터는 빈 목록으로 안전 복구
        return []


def save_todos(todos):
    """할 일 목록을 JSON 파일에 저장한다."""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(todos, f, ensure_ascii=False, indent=2)
    except OSError as e:
        st.error(f"저장에 실패했습니다: {e}")


# ---------- 기능 ----------
def resolve_category(text, category):
    """category가 AUTO면 키워드로 분류, 아니면 그대로 사용한다."""
    if category == AUTO:
        return classify_category(text)
    return category if category in CATEGORY_LABELS else "personal"


def add_todo(text, category):
    text = text.strip()
    if not text:  # 빈 문자열은 추가하지 않음
        return None
    resolved = resolve_category(text, category)
    st.session_state.todos.append(
        {
            "id": uuid.uuid4().hex,
            "text": text,
            "category": resolved,
            "completed": False,
            "created_at": datetime.now().isoformat(),
        }
    )
    save_todos(st.session_state.todos)
    return resolved


def update_todo(todo_id, new_text, new_category):
    new_text = new_text.strip()
    if not new_text:  # 빈 값이면 저장하지 않음
        return None
    resolved = resolve_category(new_text, new_category)
    for todo in st.session_state.todos:
        if todo["id"] == todo_id:
            todo["text"] = new_text
            todo["category"] = resolved
            break
    save_todos(st.session_state.todos)
    return resolved


def delete_todo(todo_id):
    st.session_state.todos = [
        t for t in st.session_state.todos if t["id"] != todo_id
    ]
    save_todos(st.session_state.todos)


def toggle_todo(todo_id, value):
    for todo in st.session_state.todos:
        if todo["id"] == todo_id:
            todo["completed"] = value
            break
    save_todos(st.session_state.todos)


def category_badge(category):
    """카테고리 색상 뱃지 HTML 반환."""
    label = CATEGORY_LABELS.get(category, category)
    color = CATEGORY_COLORS.get(category, "#888")
    return (
        f"<span style='background:{color};color:#fff;padding:2px 10px;"
        f"border-radius:999px;font-size:0.75rem;font-weight:600;'>{label}</span>"
    )


def category_options():
    """카테고리 선택 옵션 (자동 분류 포함)."""
    return [AUTO] + list(CATEGORY_LABELS.keys())


def category_format(key):
    return "🤖 자동 분류" if key == AUTO else CATEGORY_LABELS[key]


# ---------- 초기화 ----------
st.set_page_config(page_title="할 일 관리", page_icon="📝", layout="centered")

if "todos" not in st.session_state:
    st.session_state.todos = load_todos()
if "editing_id" not in st.session_state:
    st.session_state.editing_id = None

# rerun 이후에도 토스트를 표시하기 위한 큐
if "_toast" in st.session_state:
    st.toast(st.session_state.pop("_toast"))

st.title("📝 할 일 관리")
st.caption("카테고리를 '🤖 자동 분류'로 두면 입력한 내용의 키워드로 알아서 분류합니다.")

# ---------- 진행률 ----------
todos = st.session_state.todos
total = len(todos)
done = sum(1 for t in todos if t["completed"])
percent = round(done / total * 100) if total else 0

if total == 0:
    st.caption("할 일 없음")
    st.progress(0)
else:
    st.caption(f"진행률: {percent}% ({done}/{total})")
    st.progress(percent / 100)

st.divider()

# ---------- 할 일 추가 ----------
with st.form("add_form", clear_on_submit=True):
    col_text, col_cat, col_btn = st.columns([3, 1.2, 1])
    with col_text:
        new_text = st.text_input(
            "할 일", placeholder="할 일을 입력하세요", label_visibility="collapsed"
        )
    with col_cat:
        new_cat = st.selectbox(
            "카테고리",
            options=category_options(),
            format_func=category_format,
            index=0,  # 기본값: 자동 분류
            label_visibility="collapsed",
        )
    with col_btn:
        submitted = st.form_submit_button("추가", use_container_width=True)

    if submitted:
        resolved = add_todo(new_text, new_cat)
        if resolved is None:
            st.warning("내용을 입력해 주세요.")
        else:
            if new_cat == AUTO:
                st.session_state._toast = (
                    f"🤖 '{CATEGORY_LABELS[resolved]}' 카테고리로 자동 분류했습니다."
                )
            st.rerun()

# ---------- 카테고리 필터 ----------
filter_options = ["all"] + list(CATEGORY_LABELS.keys())
selected_filter = st.radio(
    "필터",
    options=filter_options,
    format_func=lambda k: "전체" if k == "all" else CATEGORY_LABELS[k],
    horizontal=True,
    label_visibility="collapsed",
)

st.divider()

# ---------- 할 일 목록 ----------
visible = (
    todos
    if selected_filter == "all"
    else [t for t in todos if t["category"] == selected_filter]
)

if not visible:
    st.info("표시할 할 일이 없습니다.")

for todo in visible:
    todo_id = todo["id"]

    # ----- 수정 모드 -----
    if st.session_state.editing_id == todo_id:
        c_text, c_cat, c_save, c_cancel = st.columns([3, 1.2, 0.7, 0.7])
        with c_text:
            edit_text = st.text_input(
                "수정",
                value=todo["text"],
                key=f"edit_text_{todo_id}",
                label_visibility="collapsed",
            )
        with c_cat:
            opts = category_options()
            edit_cat = st.selectbox(
                "카테고리",
                options=opts,
                format_func=category_format,
                index=opts.index(todo["category"]),  # 현재 카테고리 선택
                key=f"edit_cat_{todo_id}",
                label_visibility="collapsed",
            )
        with c_save:
            if st.button("저장", key=f"save_{todo_id}", use_container_width=True):
                resolved = update_todo(todo_id, edit_text, edit_cat)
                if resolved is None:
                    st.warning("내용을 입력해 주세요.")
                else:
                    st.session_state.editing_id = None
                    if edit_cat == AUTO:
                        st.session_state._toast = (
                            f"🤖 '{CATEGORY_LABELS[resolved]}' 카테고리로 자동 분류했습니다."
                        )
                    st.rerun()
        with c_cancel:
            if st.button("취소", key=f"cancel_{todo_id}", use_container_width=True):
                st.session_state.editing_id = None
                st.rerun()

    # ----- 일반 표시 모드 -----
    else:
        c_check, c_text, c_badge, c_edit, c_del = st.columns([0.5, 3, 1, 0.5, 0.5])
        with c_check:
            checked = st.checkbox(
                "완료",
                value=todo["completed"],
                key=f"check_{todo_id}",
                label_visibility="collapsed",
            )
            if checked != todo["completed"]:
                toggle_todo(todo_id, checked)
                st.rerun()
        with c_text:
            if todo["completed"]:
                st.markdown(f"~~{todo['text']}~~", help="완료됨")
            else:
                st.write(todo["text"])
        with c_badge:
            st.markdown(category_badge(todo["category"]), unsafe_allow_html=True)
        with c_edit:
            if st.button("✏️", key=f"edit_{todo_id}", help="수정"):
                st.session_state.editing_id = todo_id
                st.rerun()
        with c_del:
            if st.button("🗑️", key=f"del_{todo_id}", help="삭제"):
                delete_todo(todo_id)
                st.rerun()
