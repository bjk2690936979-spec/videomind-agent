from typing import Any, Dict, Optional, Tuple

import requests
import streamlit as st


DEFAULT_BACKEND_URL = "http://127.0.0.1:8000"
REQUEST_TIMEOUT = 300


def normalize_backend_url(backend_url: str) -> str:
    return backend_url.strip().rstrip("/")


def request_json(
    method: str,
    backend_url: str,
    path: str,
    payload: Optional[Dict[str, Any]] = None,
    timeout: int = REQUEST_TIMEOUT,
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    # 前端统一用 (data, error) 返回，避免每个按钮重复处理 requests 异常。
    url = f"{normalize_backend_url(backend_url)}{path}"
    try:
        response = requests.request(method, url, json=payload, timeout=timeout)
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.RequestException as exc:
        return None, f"请求失败：{exc}"
    except ValueError:
        return None, "后端返回的不是合法 JSON。"


def check_health(backend_url: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    return request_json("GET", backend_url, "/health", timeout=10)


def digest_text(backend_url: str, text: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    return request_json("POST", backend_url, "/digest/text", {"text": text})


def digest_video_url(backend_url: str, url: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    return request_json("POST", backend_url, "/digest/video-url", {"url": url})


def get_trace(backend_url: str, trace_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    return request_json("GET", backend_url, f"/trace/{trace_id}", timeout=30)


def show_sidebar() -> str:
    st.sidebar.header("配置")
    backend_url = st.sidebar.text_input("后端地址", DEFAULT_BACKEND_URL)

    if st.sidebar.button("检查后端状态"):
        health, error = check_health(backend_url)
        if error:
            st.sidebar.error("后端未启动或连接失败")
            st.sidebar.caption(error)
        else:
            st.sidebar.success("后端连接正常")
            st.sidebar.json(health)

    st.sidebar.markdown(
        """
文本 / 视频  
↓  
转写 / 提取字幕  
↓  
长文本压缩  
↓  
LangGraph 工作流  
↓  
总结 / 关键词 / 复习题 / 思维导图  
↓  
trace 日志
"""
    )
    return backend_url


def show_basic_fields(data: Dict[str, Any]) -> None:
    trace_id = data.get("trace_id")
    if trace_id:
        st.info("trace_id")
        st.code(str(trace_id), language="text")

    # 视频和文本返回字段不同，先压成紧凑元信息再展示。
    meta_fields = {
        "input_type": data.get("input_type", "text"),
        "transcript_source": data.get("transcript_source"),
        "fallback_needed": data.get("fallback_needed"),
        "fallback_used": data.get("fallback_used"),
    }
    compact_meta = {key: value for key, value in meta_fields.items() if value is not None}
    if compact_meta:
        st.json(compact_meta)

    if data.get("error"):
        st.error(str(data["error"]))


def show_learning_content(data: Dict[str, Any]) -> None:
    one_sentence = data.get("one_sentence")
    if one_sentence:
        st.subheader("一句话总结")
        st.success(str(one_sentence))

    key_points = data.get("key_points") or []
    st.subheader("核心要点")
    if key_points:
        for point in key_points:
            st.markdown(f"- {point}")
    else:
        st.caption("暂无核心要点。")

    st.subheader("关键词解释")
    terms = data.get("terms") or []
    if terms:
        st.table(terms)
    else:
        st.caption("暂无关键词解释。")

    st.subheader("复习题")
    quiz = data.get("quiz") or []
    if quiz:
        for index, item in enumerate(quiz, start=1):
            question = item.get("question", "")
            answer = item.get("answer", "")
            st.markdown(f"**Q{index}：{question}**")
            st.markdown(f"A：{answer}")
    else:
        st.caption("暂无复习题。")

    st.subheader("思维导图 Mermaid 文本")
    mindmap = data.get("mindmap") or ""
    if mindmap:
        st.code(mindmap, language="mermaid")
    else:
        st.caption("暂无思维导图。")


def show_result(data: Optional[Dict[str, Any]]) -> None:
    if not data:
        return

    st.header("结果展示")
    show_basic_fields(data)
    show_learning_content(data)


def show_input_area(backend_url: str) -> None:
    st.header("输入")
    input_type = st.radio("输入类型", ["文本", "视频链接"], horizontal=True)

    if input_type == "文本":
        text = st.text_area("请输入学习材料文本", height=220)
        if st.button("生成学习内容", type="primary"):
            if not text.strip():
                st.warning("请输入文本。")
                return
            with st.spinner("正在生成学习内容..."):
                data, error = digest_text(backend_url, text)
            if error:
                st.error(error)
            else:
                # 保留最近一次结果，便于页面 rerun 后继续展示。
                st.session_state["last_result"] = data
    else:
        video_url = st.text_input("请输入视频链接")
        if st.button("解析视频并生成学习内容", type="primary"):
            if not video_url.strip():
                st.warning("请输入视频链接。")
                return
            with st.spinner("正在解析视频并生成学习内容..."):
                data, error = digest_video_url(backend_url, video_url)
            if error:
                st.error(error)
            else:
                # 视频链路也复用同一个结果展示区。
                st.session_state["last_result"] = data


def show_trace_query(backend_url: str) -> None:
    st.header("Trace 查询")
    trace_id = st.text_input("trace_id")
    if st.button("查询 Trace"):
        if not trace_id.strip():
            st.warning("请输入 trace_id。")
            return
        with st.spinner("正在查询 trace..."):
            data, error = get_trace(backend_url, trace_id)
        if error:
            st.error(error)
        else:
            st.json(data)


def main() -> None:
    st.set_page_config(page_title="VideoMind Agent", page_icon="VM", layout="wide")
    st.title("VideoMind Agent：视频学习内容消化助手")
    st.caption("支持输入文本或视频链接，自动生成总结、关键词解释、复习题和思维导图。")

    backend_url = show_sidebar()
    show_input_area(backend_url)
    show_result(st.session_state.get("last_result"))
    st.divider()
    show_trace_query(backend_url)


if __name__ == "__main__":
    main()
