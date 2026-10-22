"""embed_v12.py — MiniLM embeddings for the site's finding texts, quantised to uint8 shards (site contract: emb/manifest.json,
emb/quant_params.json, per-dimension min/scale; browser dequantises q*scale+qmin then L2-normalises)."""
import json, glob, os, sys, time, numpy as np
from sentence_transformers import SentenceTransformer
data = sys.argv[1]; out = os.path.join(data, "emb"); os.makedirs(out, exist_ok=True)
texts = []
for f in sorted(glob.glob(os.path.join(data, "text_*.json"))): texts += json.load(open(f))["t"]
n = len(texts); print("texts", n, flush=True)
m = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
t0 = time.time(); X = np.zeros((n, 384), dtype=np.float32)
for i in range(0, n, 2048):
    X[i:i+2048] = m.encode(texts[i:i+2048], batch_size=256, normalize_embeddings=True, show_progress_bar=False)
    if (i // 2048) % 10 == 0: print(i, round(time.time() - t0), "s", flush=True)
qmin = X.min(axis=0); qmax = X.max(axis=0); scale = (qmax - qmin) / 255.0; scale[scale == 0] = 1e-9
Q = np.clip(np.round((X - qmin) / scale), 0, 255).astype(np.uint8)
deq = Q.astype(np.float32) * scale + qmin; deq /= np.linalg.norm(deq, axis=1, keepdims=True)
fid = float(np.mean(np.sum(deq * X, axis=1)))
for f in glob.glob(os.path.join(out, "*")): os.remove(f)
SH = 6000; shards = []
for s in range(0, n, SH):
    fn = f"emb_v12_{s // SH:02d}.bin"; Q[s:s+SH].tofile(os.path.join(out, fn)); shards.append({"file": fn, "start": s, "end": min(s + SH, n), "rows": min(SH, n - s), "bytes": int(Q[s:s+SH].nbytes)})
json.dump({"qmin": qmin.tolist(), "scale": scale.tolist()}, open(os.path.join(out, "quant_params.json"), "w"))
json.dump({"version": "v1.2", "model": "all-MiniLM-L6-v2", "dims": 384, "dtype": "uint8", "quantization": "per-dimension min/scale, dequant = q*scale+qmin then L2-normalize",
           "fidelity_mean_cosine": round(fid, 5), "total_rows": n, "shard_rows": SH, "shards": shards,
           "note": "Row i embeds the display text of finding row i (text_NN.json), full v1.2 corpus in package order."}, open(os.path.join(out, "manifest.json"), "w"))
print("done", n, "fidelity", round(fid, 5), "MB", round(Q.nbytes / 1e6, 1), round(time.time() - t0), "s", flush=True)
