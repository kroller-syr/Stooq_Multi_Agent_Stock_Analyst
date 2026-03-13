import json
from typing import Any

from openai import OpenAI


def _safe_json_load(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except Exception:
        # fallback: wrap raw text
        return {"report_markdown": text, "recommendation": None, "confidence": None, "qa": {"pass": False, "issues": ["Non-JSON output from model"]}}


def build_llm_payload(state) -> dict[str, Any]:
    # Keep payload compact to avoid token blowups
    top_articles = (state.sentiment.get("per_article") or [])[:10]
    top_articles_min = [
        {
            "title": a.get("title"),
            "domain": a.get("domain"),
            "seendate": a.get("seendate"),
            "url": a.get("url"),
            "sentiment_score": a.get("score"),
        }
        for a in top_articles
    ]

    return {
        "ticker": state.ticker,
        "timeframe": {"start": str(state.start_date.date()), "end": str(state.end_date.date())},
        "stats": state.stats,
        "sentiment_summary": (state.sentiment.get("summary") or {}),
        "top_articles": top_articles_min,
        "figure_paths": state.figure_paths,
    }


def generate_report_and_recommendation(
    client: OpenAI,
    state,
    model: str = "gpt-4.1-mini",
) -> dict[str, Any]:
    """
    Produces:
      - report_markdown: long-form report text with numbered sections and figure callouts
      - recommendation: BUY/HOLD/SELL (non-personal, informational)
      - confidence: Low/Medium/High
      - qa: {pass: bool, issues: [..], suggested_fixes: [..]}
    """
    payload = build_llm_payload(state)

    developer = (
        "You are part of a multi-agent financial analysis system.\n"
        "Write a clear, data-driven report. You MUST:\n"
        "1) Use the provided stats + sentiment summary.\n"
        "2) Reference top articles by [n] and include a Sources list at the end with those URLs.\n"
        "3) Call out figures as Figure 1/2/3 (these will be embedded later).\n"
        "4) Provide a non-personal recommendation (BUY/HOLD/SELL) and confidence (Low/Medium/High).\n"
        "5) Include a short disclaimer: 'Not financial advice.'\n\n"
        "Return ONLY valid JSON with keys:\n"
        "report_markdown (string), recommendation (string), confidence (string), qa (object).\n"
        "qa must include: pass (bool), issues (list of strings), suggested_fixes (list of strings).\n"
        "If everything is good, qa.pass=true and lists may be empty."
    )

    user = (
        "Create the report and recommendation for the following analysis package:\n"
        f"{json.dumps(payload, indent=2)}"
    )

    resp = client.responses.create(
        model=model,
        input=[
            {"role": "developer", "content": [{"type": "input_text", "text": developer}]},
            {"role": "user", "content": [{"type": "input_text", "text": user}]},
        ],
        # keep deterministic-ish
        temperature=0.2,
    )

    text = getattr(resp, "output_text", "") or ""
    data = _safe_json_load(text)

    # Basic post-checks
    if not isinstance(data.get("qa"), dict):
        data["qa"] = {"pass": False, "issues": ["Missing qa object"], "suggested_fixes": ["Return qa with pass/issues/suggested_fixes"]}

    return data


def supervisor_qa_retry_if_needed(
    client: OpenAI,
    state,
    first_pass: dict[str, Any],
    model: str = "gpt-4.1-mini",
) -> dict[str, Any]:
    """
    If qa.pass is False, run one corrective pass with the issues injected.
    """
    qa = first_pass.get("qa") or {}
    if qa.get("pass") is True:
        return first_pass

    issues = qa.get("issues") or ["Unspecified issues"]
    fixes = qa.get("suggested_fixes") or []

    developer = (
        "You are the supervisor agent. You will repair the draft report.\n"
        "You MUST address the listed issues. Return ONLY valid JSON with the same keys:\n"
        "report_markdown, recommendation, confidence, qa(pass/issues/suggested_fixes).\n"
        "If fixed, set qa.pass=true."
    )

    user = (
        "Here is the current state payload:\n"
        f"{json.dumps(build_llm_payload(state), indent=2)}\n\n"
        "Here is the previous output JSON:\n"
        f"{json.dumps(first_pass, indent=2)}\n\n"
        "Issues to fix:\n"
        f"{json.dumps(issues, indent=2)}\n\n"
        "Suggested fixes:\n"
        f"{json.dumps(fixes, indent=2)}"
    )

    resp = client.responses.create(
        model=model,
        input=[
            {"role": "developer", "content": [{"type": "input_text", "text": developer}]},
            {"role": "user", "content": [{"type": "input_text", "text": user}]},
        ],
        temperature=0.2,
    )

    text = getattr(resp, "output_text", "") or ""
    return _safe_json_load(text)