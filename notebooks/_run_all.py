
import json, sys, os, io, traceback, contextlib, glob
os.environ["MPLBACKEND"]="Agg"
results={}
for nbp in sorted(glob.glob("*.ipynb")):
    name=os.path.basename(nbp)
    doc=json.load(open(nbp))
    ns={"__name__":"__main__"}
    ok=True; err=None; nexec=0; outs=[]
    for j,cell in enumerate(doc["cells"]):
        if cell["cell_type"]!="code": continue
        src="".join(cell["source"])
        buf=io.StringIO()
        try:
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                exec(compile(src,f"{name}#cell{j}","exec"), ns)
            nexec+=1
            o=buf.getvalue()
            outs.append({"cell":j,"stdout":o[-4000:]})
            cell["outputs"]=[{"output_type":"stream","name":"stdout","text":o.splitlines(keepends=True)}] if o else []
            cell["execution_count"]=nexec
        except Exception:
            ok=False
            err={"cell":j,"src":src[:600],"trace":traceback.format_exc()[-2500:],"stdout_tail":buf.getvalue()[-1200:]}
            break
    results[name]={"ok":ok,"cells_executed":nexec,"error":err}
    if ok:
        json.dump(doc, open(f"_exec/{name}", "w"), indent=1)
        json.dump(outs, open(f"_exec/{name}.outputs.json","w"), indent=1)
json.dump(results, open("_exec/_results.json","w"), indent=1, default=str)
for k,v in results.items():
    print(k, "OK" if v["ok"] else "FAIL", v["cells_executed"], "code cells")
    if v["error"]:
        print("   cell", v["error"]["cell"]); print("   ", v["error"]["trace"].strip().split("\n")[-1])
        print("   src:", v["error"]["src"][:300].replace("\n"," | "))
