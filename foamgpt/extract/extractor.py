"""Claude-based structured extraction: paper text -> PaperExtraction.

Two modes:
  * `extract_one`   - synchronous, for development / spot checks.
  * `submit_batch`  - Message Batches API (50% cheaper, async) for the full corpus.

Output: one JSON line per paper in data/extracted/extractions.jsonl containing the
validated PaperExtraction plus provenance (model, prompt version, usage).
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request
from rich.console import Console

from foamgpt.config import EXTRACTED_DIR, MODEL, TEXT_DIR, anthropic_client
from foamgpt.extract.prompts import PROMPT_VERSION, SYSTEM, USER_TEMPLATE
from foamgpt.harvest.openalex import load_papers
from foamgpt.schema import PaperExtraction

console = Console()
OUT = EXTRACTED_DIR / "extractions.jsonl"
MAX_CHARS = 350_000  # ~90k tokens; enough for any single paper with tables


def _load_text(paper_id: str) -> str | None:
    p = TEXT_DIR / f"{paper_id}.txt"
    if not p.exists():
        return None
    txt = p.read_text(errors="ignore")
    if len(txt) > MAX_CHARS:
        console.print(f"[yellow]{paper_id}: text {len(txt)} chars > cap; truncating to {MAX_CHARS}[/]")
        txt = txt[:MAX_CHARS]
    return txt


def _user_content(paper: dict, text: str) -> str:
    return USER_TEMPLATE.format(
        title=paper.get("title"), year=paper.get("year"), venue=paper.get("venue"),
        paper_id=paper["id"], text=text,
    )


def _schema_text() -> str:
    return json.dumps(PaperExtraction.model_json_schema(), indent=None)


def _system() -> str:
    """System prompt with the JSON schema inlined (schema is too large for constrained decoding)."""
    return (
        SYSTEM
        + "\n\nOutput ONLY a single JSON object (no prose, no code fences) that validates against this "
        + "JSON Schema:\n"
        + _schema_text()
    )


def _parse(raw: str) -> PaperExtraction:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
    return PaperExtraction.model_validate_json(raw)


def _already_done() -> set[str]:
    if not OUT.exists():
        return set()
    return {json.loads(l)["paper_id"] for l in OUT.read_text().splitlines() if l.strip()}


def _append(paper_id: str, extraction: PaperExtraction, meta: dict) -> None:
    for i, rec in enumerate(extraction.records):
        rec.paper_id = paper_id
        rec.record_id = f"{paper_id}-{i:03d}"
    row = {"paper_id": paper_id, "model": MODEL, "prompt_version": PROMPT_VERSION,
           **meta, "extraction": extraction.model_dump(mode="json")}
    with OUT.open("a") as f:
        f.write(json.dumps(row) + "\n")


def extract_sync(limit: int | None = None) -> int:
    """Development helper: extract papers one at a time using messages.parse."""
    client = anthropic_client()
    done = _already_done()
    papers = [p for p in load_papers() if p["id"] not in done and (TEXT_DIR / f"{p['id']}.txt").exists()]
    if limit:
        papers = papers[:limit]
    n = 0
    for p in papers:
        text = _load_text(p["id"])
        messages = [{"role": "user", "content": _user_content(p, text)}]
        extraction = None
        for attempt in range(2):
            with client.messages.stream(
                model=MODEL, max_tokens=32_000, thinking={"type": "adaptive"},
                system=_system(), messages=messages,
            ) as stream:
                msg = stream.get_final_message()
            if msg.stop_reason == "refusal":
                console.print(f"[red]{p['id']}: refusal[/]")
                break
            raw = "".join(b.text for b in msg.content if b.type == "text")
            try:
                extraction = _parse(raw)
                break
            except Exception as e:  # noqa: BLE001
                console.print(f"[yellow]{p['id']}: invalid JSON on attempt {attempt + 1}: {str(e)[:200]}[/]")
                messages = messages + [
                    {"role": "assistant", "content": raw},
                    {"role": "user", "content": f"Your JSON failed validation: {str(e)[:1500]}\n"
                                                "Return the corrected JSON object only."},
                ]
        if extraction is None:
            continue
        _append(p["id"], extraction, {"usage": msg.usage.model_dump(), "mode": "sync"})
        n += 1
        console.print(f"[green]{p['id']}[/]: {len(extraction.records)} records")
    return n


def submit_batch(limit: int | None = None) -> str:
    """Submit the whole corpus as a Message Batch. Returns batch id (saved to disk)."""
    client = anthropic_client()
    done = _already_done()
    papers = [p for p in load_papers() if p["id"] not in done and (TEXT_DIR / f"{p['id']}.txt").exists()]
    if limit:
        papers = papers[:limit]
    requests = []
    for p in papers:
        text = _load_text(p["id"])
        requests.append(
            Request(
                custom_id=p["id"],
                params=MessageCreateParamsNonStreaming(
                    model=MODEL,
                    max_tokens=32_000,
                    thinking={"type": "adaptive"},
                    system=_system(),
                    messages=[{"role": "user", "content": _user_content(p, text)}],
                ),
            )
        )
    batch = client.messages.batches.create(requests=requests)
    (EXTRACTED_DIR / "batches.txt").open("a").write(f"{batch.id}\t{len(requests)}\t{time.time()}\n")
    console.print(f"[green]Submitted batch {batch.id} with {len(requests)} papers[/]")
    return batch.id


def collect_batch(batch_id: str) -> int:
    """Poll a batch until finished and append validated results."""
    client = anthropic_client()
    while True:
        b = client.messages.batches.retrieve(batch_id)
        if b.processing_status == "ended":
            break
        console.print(f"batch {batch_id}: {b.request_counts}")
        time.sleep(30)
    n = 0
    for r in client.messages.batches.results(batch_id):
        if r.result.type != "succeeded":
            console.print(f"[red]{r.custom_id}: {r.result.type}[/]")
            continue
        msg = r.result.message
        if msg.stop_reason == "refusal":
            continue
        raw = "".join(blk.text for blk in msg.content if blk.type == "text")
        try:
            extraction = _parse(raw)
        except Exception as e:  # noqa: BLE001
            console.print(f"[red]{r.custom_id}: schema validation failed: {e}[/]")
            continue
        _append(r.custom_id, extraction, {"usage": msg.usage.model_dump(), "mode": "batch", "batch_id": batch_id})
        n += 1
    console.print(f"[green]Collected {n} extractions from {batch_id}[/]")
    return n


def load_extractions(path: Path | None = None) -> list[dict]:
    path = path or OUT
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
