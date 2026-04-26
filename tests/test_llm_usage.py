from types import SimpleNamespace

from backend.core import llm


def test_generate_json_records_token_usage(monkeypatch) -> None:
    class FakeCompletions:
        def create(self, **kwargs):
            return SimpleNamespace(
                model=kwargs["model"],
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(content='{"ok": true}'),
                    )
                ],
                usage=SimpleNamespace(
                    prompt_tokens=12,
                    completion_tokens=5,
                    total_tokens=17,
                ),
            )

    fake_client = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions()))
    monkeypatch.setattr(
        llm,
        "get_settings",
        lambda: SimpleNamespace(llm_model="test-model", llm_api_key="key", llm_base_url=None),
    )
    monkeypatch.setattr(llm, "get_llm_client", lambda: fake_client)

    token = llm.begin_token_usage_tracking()
    try:
        result = llm.generate_json("返回 JSON")
        usage = llm.finish_token_usage_tracking(token)
    except Exception:
        llm.finish_token_usage_tracking(token)
        raise

    assert result == {"ok": True}
    assert usage == [
        {
            "model": "test-model",
            "prompt_tokens": 12,
            "completion_tokens": 5,
            "total_tokens": 17,
        }
    ]
    assert llm.summarize_token_usage(usage) == {
        "prompt_tokens": 12,
        "completion_tokens": 5,
        "total_tokens": 17,
    }
