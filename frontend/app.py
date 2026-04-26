from concurrent.futures import ThreadPoolExecutor
from time import perf_counter, sleep
from typing import Any, Callable, Dict, List, Optional, Tuple

import requests
import streamlit as st


DEFAULT_BACKEND_URL = "http://127.0.0.1:8000"
REQUEST_TIMEOUT = 300
PROGRESS_REFRESH_SECONDS = 0.8

TEXT_PROGRESS_STEPS = [
    "发送学习材料",
    "拆分长文本",
    "生成总结和核心要点",
    "解释关键词",
    "生成复习题",
    "整理思维导图",
    "保存结果和 trace",
]

VIDEO_PROGRESS_STEPS = [
    "发送视频链接",
    "提取平台字幕",
    "必要时转写音频",
    "整理 transcript",
    "生成总结和核心要点",
    "生成关键词、复习题和思维导图",
    "保存结果和 trace",
]

TRACE_PROGRESS_STEPS = [
    "发送 trace_id",
    "读取 trace 文件",
    "整理执行明细",
]


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
    started_at = perf_counter()
    try:
        response = requests.request(method, url, json=payload, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict):
            data["_client_elapsed_ms"] = int((perf_counter() - started_at) * 1000)
        return data, None
    except requests.exceptions.RequestException as exc:
        return None, f"请求失败：{exc}"
    except ValueError:
        return None, "后端返回的不是合法 JSON。"


def format_duration_ms(value: Any) -> str:
    try:
        milliseconds = int(float(value or 0))
    except (TypeError, ValueError):
        return "-"

    if milliseconds <= 0:
        return "0 毫秒"
    if milliseconds < 1000:
        return f"{milliseconds} 毫秒"

    seconds = milliseconds / 1000
    if seconds < 60:
        return f"{seconds:.1f} 秒"

    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)
    return f"{minutes} 分 {remaining_seconds} 秒"


def format_number(value: Any) -> str:
    try:
        return f"{int(value or 0):,}"
    except (TypeError, ValueError):
        return "0"


def get_token_totals(data: Dict[str, Any]) -> Tuple[int, int, int]:
    usage = data.get("usage") or []
    prompt_tokens = int(data.get("prompt_tokens") or 0)
    completion_tokens = int(data.get("completion_tokens") or 0)
    total_tokens = int(data.get("total_tokens") or 0)

    if usage and not any([prompt_tokens, completion_tokens, total_tokens]):
        prompt_tokens = sum(int(item.get("prompt_tokens") or 0) for item in usage)
        completion_tokens = sum(int(item.get("completion_tokens") or 0) for item in usage)
        total_tokens = sum(int(item.get("total_tokens") or 0) for item in usage)

    if not total_tokens:
        total_tokens = prompt_tokens + completion_tokens

    return prompt_tokens, completion_tokens, total_tokens


def run_with_progress(
    title: str,
    worker: Callable[[], Tuple[Optional[Dict[str, Any]], Optional[str]]],
    steps: List[str],
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    started_at = perf_counter()
    status = st.status(f"{title}：准备开始", expanded=True)
    progress = st.progress(5, text="准备开始")
    detail = st.empty()

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(worker)
        while not future.done():
            elapsed_ms = int((perf_counter() - started_at) * 1000)
            step_index = min(int(elapsed_ms / 3500), len(steps) - 1)
            step = steps[step_index]
            step_progress = int((step_index + 1) / len(steps) * 78)
            local_progress = int(((elapsed_ms % 3500) / 3500) * 8)
            percent = min(92, 8 + step_progress + local_progress)

            status.update(label=f"{title}：{step}", state="running")
            progress.progress(percent, text=f"{step} · 已等待 {format_duration_ms(elapsed_ms)}")
            detail.caption(f"当前进度：{step}")
            sleep(PROGRESS_REFRESH_SECONDS)

        elapsed_ms = int((perf_counter() - started_at) * 1000)
        try:
            data, error = future.result()
        except Exception as exc:
            data, error = None, f"请求失败：{exc}"

    if data is not None:
        data["_client_elapsed_ms"] = elapsed_ms

    if error:
        status.update(label=f"{title}失败", state="error", expanded=True)
        progress.progress(100, text=f"失败 · 已等待 {format_duration_ms(elapsed_ms)}")
        detail.caption("当前进度：处理失败")
    else:
        status.update(label=f"{title}完成", state="complete", expanded=False)
        progress.progress(100, text=f"完成 · 总等待 {format_duration_ms(elapsed_ms)}")
        detail.caption("当前进度：完成")

    return data, error


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


def show_run_metrics(data: Dict[str, Any]) -> None:
    prompt_tokens, completion_tokens, total_tokens = get_token_totals(data)
    columns = st.columns(5)
    columns[0].metric("后端耗时", format_duration_ms(data.get("latency_ms")))
    columns[1].metric("等待时间", format_duration_ms(data.get("_client_elapsed_ms")))
    columns[2].metric("输入 tokens", format_number(prompt_tokens))
    columns[3].metric("输出 tokens", format_number(completion_tokens))
    columns[4].metric("总 tokens", format_number(total_tokens))

    usage = data.get("usage") or []
    if usage:
        rows = []
        for index, item in enumerate(usage, start=1):
            rows.append(
                {
                    "序号": index,
                    "模型": item.get("model") or "-",
                    "输入 tokens": int(item.get("prompt_tokens") or 0),
                    "输出 tokens": int(item.get("completion_tokens") or 0),
                    "总 tokens": int(item.get("total_tokens") or 0),
                }
            )
        with st.expander("Token 明细", expanded=False):
            st.table(rows)


def show_basic_fields(data: Dict[str, Any]) -> None:
    show_run_metrics(data)

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
            data, error = run_with_progress(
                "生成学习内容",
                lambda: digest_text(backend_url, text),
                TEXT_PROGRESS_STEPS,
            )
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
            data, error = run_with_progress(
                "解析视频并生成学习内容",
                lambda: digest_video_url(backend_url, video_url),
                VIDEO_PROGRESS_STEPS,
            )
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
        data, error = run_with_progress(
            "查询 Trace",
            lambda: get_trace(backend_url, trace_id),
            TRACE_PROGRESS_STEPS,
        )
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
