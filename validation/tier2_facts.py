"""Basis-enforcing fact accessor.

Motivation: every number wrong in the Tier-1 briefing was CORRECT under some counting basis
and wrong under the one stated. 'norepinephrine papers' has four defensible values
(176/177/194/195); entity coverage has three (29.8/52.0/53.0). Prose cannot carry a basis,
so quoting from memory silently picks the wrong one.

Rule enforced here: you cannot obtain a number without also obtaining its basis string,
and you cannot obtain a stale number at all -- every read re-evaluates the expression
against the live table.
"""
import json, numpy as np, pandas as pd

class Facts:
    def __init__(self, path, **frames):
        self.G = json.load(open(path)); self.frames = frames
    def __getitem__(self, name):
        f = self.G["facts"][name]
        env = dict(self.frames); env.update(pd=pd, np=np)
        if "M" in env: env["nosplit"] = ~env["M"].split_derived.fillna(False).astype(bool)
        live = eval(f["expr"], env)
        live = int(live) if isinstance(live, np.integer) else (
               round(float(live),1) if isinstance(live,(np.floating,float)) else live)
        return Fact(name, live, f["value"], f["basis"], f["expr"], f.get("note",""))
    def cite(self, name):
        """The ONLY sanctioned way to put a number in prose."""
        return str(self[name])
    def audit(self):
        """Re-evaluate every fact; report drift from the frozen value."""
        out=[]
        for n in self.G["facts"]:
            try: f=self[n]; out.append((n, f.frozen, f.value, True))
            except DriftError as e: out.append((n, F_ := self.G["facts"][n]["value"], str(e).split("live=")[1].split(" ")[0], False))
        return out

class Fact:
    def __init__(s, name, value, frozen, basis, expr, note):
        s.name,s.value,s.frozen,s.basis,s.expr,s.note = name,value,frozen,basis,expr,note
        if value != frozen:
            raise DriftError(f"{name}: live={value} but frozen={frozen} (basis: {basis}). "
                             f"Either the data changed legitimately (re-freeze) or a bug was introduced.")
    def __str__(s):  return f"{s.value:,} [{s.basis}]" if isinstance(s.value,int) else f"{s.value} [{s.basis}]"
    def __repr__(s): return s.__str__()
    def __int__(s):  raise BasisError(
        f"Refusing to yield a bare int for '{s.name}'. Use f'{{facts.cite(\'{s.name}\')}}' so the "
        f"basis travels with the number, or .value if you have already stated the basis: {s.basis}")

class DriftError(RuntimeError): pass
class BasisError(TypeError): pass
