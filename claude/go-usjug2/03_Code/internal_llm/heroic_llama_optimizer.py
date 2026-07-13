#!/usr/bin/env python3
"""
Heroic Llama Optimizer — eigener Fusion-Algorithmus
===================================================
1. QUBO-Sample-Selection: maximale Wissensabdeckung pro Epoch
2. Simulated Annealing: Generation-Parameter (temp, top_p, repeat_penalty)
3. Iteratives Scoring gegen Referenz-Antworten (Token-F1 + Längenpenalty)
4. Export: optimized_params.json + Modelfile + metrics
"""

from __future__ import annotations

import json
import math
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


def tokenize(text: str) -> List[str]:
    return re.findall(r"\w+", text.lower())


def token_f1(pred: str, ref: str) -> float:
    p, r = tokenize(pred), tokenize(ref)
    if not p or not r:
        return 0.0
    ps, rs = set(p), set(r)
    tp = len(ps & rs)
    if tp == 0:
        return 0.0
    prec = tp / len(ps)
    rec = tp / len(rs)
    return 2 * prec * rec / (prec + rec)


def make_diversity_qubo(embeddings: np.ndarray, size: int) -> np.ndarray:
    """Max-Cut-ähnliches QUBO: diverse Samples bevorzugen."""
    n = len(embeddings)
    sim = embeddings @ embeddings.T
    np.fill_diagonal(sim, 0)
    Q = -sim / max(sim.max(), 1e-6)
    # Auswahl von `size` Indizes via Greedy auf QUBO-Energie
    return Q


def greedy_qubo_select(Q: np.ndarray, k: int) -> List[int]:
    n = Q.shape[0]
    k = min(k, n)
    selected: List[int] = []
    remaining = set(range(n))
    # Start: höchste Diagonale (eigenständigster Eintrag)
    first = int(np.argmax(np.diag(Q)))
    selected.append(first)
    remaining.discard(first)
    while len(selected) < k and remaining:
        best_i, best_gain = -1, -np.inf
        for i in remaining:
            gain = Q[i, i]
            for j in selected:
                gain += Q[i, j]
            if gain > best_gain:
                best_gain, best_i = gain, i
        selected.append(best_i)
        remaining.discard(best_i)
    return selected


def simulated_annealing_params(
    score_fn,
    steps: int = 40,
    t0: float = 1.0,
) -> Dict[str, float]:
    """SA über Generation-Parameter."""
    rng = np.random.default_rng(42)
    current = {"temperature": 0.7, "top_p": 0.9, "repeat_penalty": 1.1}
    current_score = score_fn(current)
    best = dict(current)
    best_score = current_score
    T = t0

    for step in range(steps):
        cand = {
            "temperature": float(np.clip(current["temperature"] + rng.normal(0, 0.08), 0.1, 1.2)),
            "top_p": float(np.clip(current["top_p"] + rng.normal(0, 0.05), 0.5, 1.0)),
            "repeat_penalty": float(np.clip(current["repeat_penalty"] + rng.normal(0, 0.05), 1.0, 1.5)),
        }
        s = score_fn(cand)
        # Metropolis: Delta immer gegen den Score des AKTUELLEN Zustands,
        # ohne score_fn(current) erneut auszuwerten (teuer bei LLM-Evaluation).
        delta = s - current_score
        accept = delta > 0 or rng.random() < math.exp(delta / max(T, 1e-6))
        if accept:
            current = cand
            current_score = s
            if s > best_score:
                best_score = s
                best = dict(cand)
        T *= 1.0 - 1.0 / steps

    best["score"] = best_score
    return best


@dataclass
class OptimizerConfig:
    model_path: str
    data_path: str = "data.jsonl"
    output_path: str = "./output"
    epochs: int = 2
    batch_size: int = 8
    ctx_len: int = 512
    max_gen_tokens: int = 128
    n_gpu_layers: int = 20
    system_prompt: str = (
        "Du bist ALTE_Frau_95g Heroic Core — Fusion Hero OS v8. "
        "Antworte präzise auf Deutsch mit technischem Heroic-Core-Wissen."
    )

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "OptimizerConfig":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class OptimizerMetrics:
    epoch_scores: List[float] = field(default_factory=list)
    step_scores: List[float] = field(default_factory=list)
    best_params: Dict[str, float] = field(default_factory=dict)
    duration_s: float = 0.0


def load_dataset(path: str, ctx_len: int) -> List[Dict[str, str]]:
    samples: List[Dict[str, str]] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if "prompt" in obj and "response" in obj:
                samples.append({
                    "prompt": str(obj["prompt"])[:ctx_len],
                    "response": str(obj["response"])[:ctx_len],
                })
    if not samples:
        raise ValueError(f"Keine Daten in {path}")
    return samples


def embed_texts(texts: List[str], dim: int = 64) -> np.ndarray:
    """Leichtgewichtiges Bag-of-words Embedding für QUBO-Selektion."""
    vocab: Dict[str, int] = {}
    for t in texts:
        for w in tokenize(t):
            vocab.setdefault(w, len(vocab) % dim)
    mat = np.zeros((len(texts), dim), dtype=np.float64)
    for i, t in enumerate(texts):
        for w in tokenize(t):
            mat[i, vocab[w]] += 1.0
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return mat / norms


class HeroicLlamaOptimizer:
    def __init__(self, cfg: OptimizerConfig) -> None:
        self.cfg = cfg
        self.llm = None
        self._backend = "llama_cpp"
        self.metrics = OptimizerMetrics()

    def _format_prompt(self, prompt: str) -> str:
        return (
            f"<|system|>\n{self.cfg.system_prompt}\n"
            f"<|user|>\n{prompt}\n"
            f"<|assistant|>\n"
        )

    def _init_backend(self) -> None:
        try:
            from llama_server_backend import healthy, generate as server_generate
            if healthy():
                self._server_generate = server_generate
                self._backend = "server"
                print("    Backend: llama-server (:8081)")
                return
        except Exception:
            pass
        try:
            from llama_cpp import Llama
            self.llm = Llama(
                model_path=self.cfg.model_path,
                n_ctx=self.cfg.ctx_len,
                n_gpu_layers=self.cfg.n_gpu_layers,
                n_threads=max(4, (os.cpu_count() or 4) - 2),
                verbose=False,
            )
            self._backend = "llama_cpp"
            print("    Backend: llama-cpp-python")
        except Exception as exc:
            from llama_cli_backend import generate as cli_generate
            self._cli_generate = cli_generate
            self._backend = "cli"
            print(f"    Backend: llama-cli (Fallback: {type(exc).__name__})")

    def _generate(self, prompt: str, params: Dict[str, float]) -> str:
        full = self._format_prompt(prompt)
        if self._backend == "server":
            text = self._server_generate(full, params, max_tokens=self.cfg.max_gen_tokens)
            for stop in ("<|user|>", "<|system|>", "\n\nUser:"):
                if stop in text:
                    text = text.split(stop, 1)[0]
            return text.strip()
        if self._backend == "cli":
            text = self._cli_generate(
                self.cfg.model_path,
                full,
                params,
                max_tokens=self.cfg.max_gen_tokens,
                n_gpu_layers=self.cfg.n_gpu_layers,
            )
            for stop in ("<|user|>", "<|system|>", "\n\nUser:"):
                if stop in text:
                    text = text.split(stop, 1)[0]
            return text.strip()
        assert self.llm is not None
        out = self.llm(
            full,
            max_tokens=self.cfg.max_gen_tokens,
            temperature=params.get("temperature", 0.7),
            top_p=params.get("top_p", 0.9),
            repeat_penalty=params.get("repeat_penalty", 1.1),
            stop=["<|user|>", "<|system|>", "\n\nUser:"],
        )
        return out["choices"][0]["text"].strip()

    def optimize(self) -> Dict[str, Any]:
        import os
        t0 = time.time()
        out_dir = Path(self.cfg.output_path)
        out_dir.mkdir(parents=True, exist_ok=True)

        if not Path(self.cfg.model_path).exists():
            raise FileNotFoundError(f"Modell fehlt: {self.cfg.model_path}")

        print(f"[*] Heroic Llama Optimizer")
        print(f"    Modell: {self.cfg.model_path}")
        print(f"    Daten:  {self.cfg.data_path}")

        self._init_backend()

        dataset = load_dataset(self.cfg.data_path, self.cfg.ctx_len)
        texts = [d["prompt"] + " " + d["response"] for d in dataset]
        embeddings = embed_texts(texts)
        Q = make_diversity_qubo(embeddings, self.cfg.batch_size)

        # Phase 1: SA auf Validierungs-Subset (erste 20 Samples)
        val_n = min(20, len(dataset))
        val_set = dataset[:val_n]
        base_params = {"temperature": 0.7, "top_p": 0.9, "repeat_penalty": 1.1}

        val_samples = int(os.getenv("FUSION_TRAIN_VAL_SAMPLES", "4"))
        sa_steps = int(os.getenv("FUSION_TRAIN_SA_STEPS", "8"))

        def score_params(p: Dict[str, float]) -> float:
            scores = []
            for sample in val_set[:val_samples]:
                pred = self._generate(sample["prompt"], p)
                scores.append(token_f1(pred, sample["response"]))
            return float(np.mean(scores)) if scores else 0.0

        print("[*] Phase 1: Simulated Annealing (Generation-Parameter)...")
        best_params = simulated_annealing_params(score_params, steps=sa_steps)
        print(f"    Beste Params: {best_params}")

        # Phase 2: Epochs mit QUBO-Sample-Selection
        for epoch in range(self.cfg.epochs):
            selected_idx = greedy_qubo_select(Q, min(self.cfg.batch_size * 2, len(dataset)))
            epoch_scores: List[float] = []
            print(f"[*] Epoch {epoch + 1}/{self.cfg.epochs} — {len(selected_idx)} QUBO-Samples")

            for i, idx in enumerate(selected_idx):
                sample = dataset[idx]
                pred = self._generate(sample["prompt"], best_params)
                score = token_f1(pred, sample["response"])
                epoch_scores.append(score)
                self.metrics.step_scores.append(score)
                if (i + 1) % 10 == 0 or i == 0:
                    print(f"    [{i+1}/{len(selected_idx)}] F1={score:.3f}")

            epoch_avg = float(np.mean(epoch_scores)) if epoch_scores else 0.0
            self.metrics.epoch_scores.append(epoch_avg)
            print(f"    Epoch avg F1: {epoch_avg:.4f}")

        self.metrics.best_params = {k: v for k, v in best_params.items() if k != "score"}
        self.metrics.duration_s = time.time() - t0

        # Export
        try:
            from system_prompt_normalize import normalize_system_prompt

            sys_prompt = normalize_system_prompt(self.cfg.system_prompt)
        except Exception:
            sys_prompt = self.cfg.system_prompt

        config_out = {
            "algorithm": "heroic_qubo_annealing_v1",
            "model_path": self.cfg.model_path,
            "system_prompt": sys_prompt,
            "generation": self.metrics.best_params,
            "metrics": {
                "epoch_scores": self.metrics.epoch_scores,
                "final_f1": self.metrics.epoch_scores[-1] if self.metrics.epoch_scores else 0,
                "duration_s": round(self.metrics.duration_s, 1),
                "samples_total": len(dataset),
            },
        }
        (out_dir / "heroic_llama_config.json").write_text(
            json.dumps(config_out, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        modelfile = f"""# Heroic Llama — optimiert via QUBO + Simulated Annealing
FROM {Path(self.cfg.model_path).resolve()}
PARAMETER temperature {best_params.get('temperature', 0.7)}
PARAMETER top_p {best_params.get('top_p', 0.9)}
PARAMETER repeat_penalty {best_params.get('repeat_penalty', 1.1)}
SYSTEM \"\"\"{sys_prompt}\"\"\"
"""
        (out_dir / "Modelfile").write_text(modelfile, encoding="utf-8")
        print(f"[*] Gespeichert: {out_dir / 'heroic_llama_config.json'}")
        print(f"[*] Gespeichert: {out_dir / 'Modelfile'}")
        return config_out