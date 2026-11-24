"""Stage 2: LLM extraction of PATM entries, up to 3 regenerations, differences logged.
Edit call_llm() for the chosen provider. Everything else is provider-independent."""
import json, sys, csv
from validate_patm import validate
MAX_RETRY=3
def call_llm(prompt):
    raise NotImplementedError("connect the chosen LLM here; return the text of the reply")
def extract(context, statements, resources, log):
    tpl=open("prompt_stage2.txt").read(); out=[]
    for step,text in statements:
        errors=""; entry=None
        for attempt in range(MAX_RETRY+1):
            p=tpl.format(context=context,statement=f"{step}. {text}",errors=errors)
            raw=call_llm(p).strip()
            err,entry=validate(raw,step,resources)
            log.append({"step":step,"attempt":attempt,"errors":err})
            if not err: break
            errors="ERRORS OF THE PREVIOUS OUTPUT (correct them):\n"+"\n".join(err)+"\n"
        out.append({"step":step,"entry":entry,"valid":entry is not None})
    return out
if __name__=="__main__":
    print("Use extract() from the run script.")
