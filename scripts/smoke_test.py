# Run: PYTHONPATH=. python scripts/smoke_test.py   (after migrate + seed_demo_data; needs a running Postgres)
import os, io, json, django
os.environ["DJANGO_SETTINGS_MODULE"]="config.settings.development"; django.setup()
from django.conf import settings
settings.ALLOWED_HOSTS=["*"]
from rest_framework.test import APIClient
from django.core.files.uploadedfile import SimpleUploadedFile
c=APIClient()
def show(label,r):
    d=r.json() if r.content and r["Content-Type"].startswith("application/json") else r.content[:100]
    ok = r.status_code<400
    print(("OK  " if ok else "FAIL"),label,r.status_code, "" if ok else json.dumps(d,ensure_ascii=False)[:400]); return d
show("health",c.get("/api/v1/health/"))
show("topics",c.get("/api/v1/legal-topics/"))
d=show("register",c.post("/api/v1/auth/register/",{"email":"t1@x.com","password":"Str0ng#Pass99","name":"T One","preferred_language":"hi"}))
r=c.post("/api/v1/auth/login/",{"email":"demo@nyayapath.local","password":"DemoPass#12345"}); d=show("login",r)
tok=(d.get("data") or {}); print(list(tok.keys()))
access=tok.get("access") or tok.get("tokens",{}).get("access")
c.credentials(HTTP_AUTHORIZATION="Bearer "+access)
show("profile",c.get("/api/v1/auth/profile/"))
msg="मेरे पड़ोसी ने मेरी दो एकड़ जमीन पर कब्जा कर लिया है। मेरा केस चार साल से आगे नहीं बढ़ रहा। मेरे पास खसरा और खतोनी है।"
d=show("chat",c.post("/api/v1/ai/chat/",{"message":msg},format="json"))
dd=d.get("data",{}); print(dd.get("detected_intent"),dd.get("language"),dd.get("verification_status"),len(dd.get("sources",[])),[q["field"] for q in dd.get("follow_up_questions",[])],len(dd.get("next_steps",[])))
print(dd.get("answer","")[:300])
cid=dd.get("conversation_id")
show("chat2",c.post("/api/v1/ai/chat/",{"message":"Bhopal, Madhya Pradesh","conversation_id":cid},format="json"))
show("convs",c.get("/api/v1/ai/conversations/"))
show("guest chat",APIClient().post("/api/v1/ai/chat/",{"message":"my land dispute case is pending 4 years in Madhya Pradesh"},format="json"))
d=show("jsearch",c.post("/api/v1/judgments/search/",{"query":"land possession injunction","state":"Madhya Pradesh"},format="json"))
res=d["data"]; print(len(res))
js=c.get("/api/v1/judgments/").json()["data"]; jid=js[0]["id"]
show("jdetail",c.get(f"/api/v1/judgments/{jid}/"))
show("explain",c.post(f"/api/v1/ai/judgments/{jid}/explain/",{"language":"en"},format="json"))
show("similar",c.post("/api/v1/ai/similar-cases/",{"message":msg},format="json"))
show("courts",c.get("/api/v1/courts/")); show("sources",c.get("/api/v1/sources/"))
cs=show("cases",c.get("/api/v1/cases/")); case_id=cs["data"][0]["id"]
show("case search",c.post("/api/v1/cases/search/",{"district":"Bhopal"},format="json"))
show("case detail",c.get(f"/api/v1/cases/{case_id}/")); show("timeline",c.get(f"/api/v1/cases/{case_id}/timeline/"))
show("case create",c.post("/api/v1/cases/",{"case_title":"New","case_type":"CIVIL","state":"Madhya Pradesh"},format="json"))
# docs
from PIL import Image, ImageDraw
img=Image.new("RGB",(900,300),"white"); ImageDraw.Draw(img).text((20,100),"Khasra number 123 land dispute notice dated 12/03/2022 Bhopal",fill="black")
b=io.BytesIO(); img.save(b,"PNG")
d=show("upload img",c.post("/api/v1/documents/upload/",{"file":SimpleUploadedFile("n.png",b.getvalue(),"image/png")},format="multipart"))
did=d["data"]["id"]; print(d["data"]["status"],d["data"]["ocr_performed"],d["data"]["chunks_count"])
show("doc ask",c.post(f"/api/v1/documents/{did}/ask/",{"question":"What is the khasra number?"},format="json"))
show("doc analyze",c.post(f"/api/v1/documents/{did}/analyze/",{},format="json"))
l=show("dl link",c.post(f"/api/v1/documents/{did}/download-link/")); 
bad=c.post("/api/v1/documents/upload/",{"file":SimpleUploadedFile("x.pdf",b"MZ\x90\x00bad","application/pdf")},format="multipart"); show("bad upload (expect 400)",bad)
other=APIClient(); t=other.post("/api/v1/auth/login/",{"email":"t1@x.com","password":"Str0ng#Pass99"},format="json").json()["data"]
other.credentials(HTTP_AUTHORIZATION="Bearer "+(t.get("access") or t["tokens"]["access"]))
r=other.get(f"/api/v1/documents/{did}/"); print("ownership (expect 403):",r.status_code)
r=other.get(f"/api/v1/cases/{case_id}/"); print("case ownership (expect 403):",r.status_code)
# plans/drafts
d=show("plan",c.post("/api/v1/action-plans/generate/",{"message":msg,"language":"hi","case_id":case_id},format="json"))
pl=d["data"]; sid=pl["steps"][0]["id"]; print(len(pl["steps"]))
show("plan get",c.get(f"/api/v1/action-plans/{pl['id']}/")); show("step",c.post(f"/api/v1/action-plans/{pl['id']}/steps/{sid}/complete/"))
d=show("summary",c.post("/api/v1/drafts/case-summary/",{"message":msg,"language":"en","case_id":case_id},format="json"))
show("brief",c.post("/api/v1/drafts/lawyer-brief/",{"message":msg,"language":"en"},format="json"))
d2=show("rti",c.post("/api/v1/drafts/rti/",{"message":msg,"language":"en"},format="json"))
show("draft get",c.get(f"/api/v1/drafts/{d2['data']['id']}/"))
show("audit non-admin (expect 403)",c)  if False else print("audit non-admin:",c.get("/api/v1/audit-logs/").status_code)
show("schema",c.get("/api/v1/schema/")); print(c.get("/api/v1/nope/").status_code)
