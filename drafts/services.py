"""DraftGenerationService: produce structured legal documents from user-supplied facts.

Rules:
- Never invent facts. Unknown fields become explicit placeholders like [CASE NUMBER].
- Every field is tagged with its provenance: USER_PROVIDED | CASE_RECORD | UNKNOWN.
- The generated content is marked as informational, not a valid legal filing.
"""
import logging
from typing import Optional

from ai.services.safety import LegalSafetyService
from .models import GeneratedDraft, DraftType

logger = logging.getLogger("nyayapath.drafts")

PLACEHOLDER = lambda label: f"[{label.upper()}]"  # noqa: E731

DISCLAIMER_EN = (
    "IMPORTANT: This draft is generated for informational purposes only. "
    "It is NOT a legally valid filing. All details marked [PLACEHOLDER] must be filled in. "
    "Verify all information and consult a qualified legal professional before submitting."
)
DISCLAIMER_HI = (
    "महत्वपूर्ण: यह मसौदा केवल सूचनात्मक उद्देश्यों के लिए तैयार किया गया है। "
    "यह कानूनी रूप से वैध दस्तावेज़ नहीं है। [PLACEHOLDER] चिह्नित सभी विवरण भरे जाने चाहिए। "
    "जमा करने से पहले किसी योग्य वकील से सत्यापित करें।"
)


def _prov(value, source: str) -> tuple:
    """Return (display_value, provenance_tag)."""
    if value:
        return str(value).strip(), source
    return None, "UNKNOWN"


def _field(val, placeholder_label: str, source: str) -> tuple:
    v, prov = _prov(val, source)
    return (v or PLACEHOLDER(placeholder_label)), prov, (v is None)


def _safe_text(text: str, lang: str) -> str:
    svc = LegalSafetyService()
    result = svc.inspect(text, lang=lang, add_disclaimer=False)
    return result.text


class DraftGenerationService:

    def generate_case_summary(self, user, intake, case=None, hits=None, lang="en") -> GeneratedDraft:
        hits = hits or []
        c = case

        title_val, tp, _ = _field(c.case_title if c else None, "CASE TITLE", "CASE_RECORD")
        cnr_val, cnrp, _ = _field(c.cnr_number if c else (intake.cnr), "CNR NUMBER", "CASE_RECORD" if c else "USER_PROVIDED")
        court_val, courtp, _ = _field(
            (c.court.name if c and c.court else None) or (c.state if c else intake.state),
            "COURT NAME", "CASE_RECORD" if c else "USER_PROVIDED"
        )
        state_val, statep, _ = _field(c.state if c else intake.state, "STATE", "CASE_RECORD" if c else "USER_PROVIDED")
        status_val, statusp, _ = _field(c.status if c else None, "CASE STATUS", "CASE_RECORD")
        filing_val, filingp, _ = _field(
            str(c.filing_date) if c and c.filing_date else (str(c.filing_year) if c and c.filing_year else None),
            "FILING DATE", "CASE_RECORD"
        )
        topic_val, topicp, _ = _field(intake.legal_topic, "LEGAL TOPIC", "USER_PROVIDED")
        desc_val, descp, ph = _field(intake.problem_summary_en or (c.description if c else None),
                                      "PROBLEM DESCRIPTION", "USER_PROVIDED")

        source_refs = _hits_to_refs(hits)
        placeholders = [label for label, _, is_ph in [
            (cnr_val, cnrp, cnr_val.startswith("[")),
            (court_val, courtp, court_val.startswith("[")),
        ] if is_ph]

        if lang == "hi":
            content = f"""केस सारांश
{'='*50}

शीर्षक       : {title_val}
CNR संख्या   : {cnr_val}
न्यायालय     : {court_val}
राज्य        : {state_val}
स्थिति       : {status_val}
दाखिल दिनांक : {filing_val}
कानूनी विषय  : {topic_val}

समस्या विवरण:
{desc_val}

प्रासंगिक दस्तावेज़: {', '.join(intake.documents) if intake.documents else '[दस्तावेज़ सूची]'}

स्रोत संदर्भ:
{_format_refs(source_refs, lang)}

{DISCLAIMER_HI}"""
        else:
            content = f"""CASE SUMMARY
{'='*50}

Title        : {title_val}
CNR Number   : {cnr_val}
Court        : {court_val}
State        : {state_val}
Status       : {status_val}
Filing Date  : {filing_val}
Legal Topic  : {topic_val}

Problem Description:
{desc_val}

Documents Available: {', '.join(intake.documents) if intake.documents else '[DOCUMENT LIST]'}

Source References:
{_format_refs(source_refs, lang)}

{DISCLAIMER_EN}"""

        content = _safe_text(content, lang)

        return GeneratedDraft.objects.create(
            user=user, case=case,
            draft_type=DraftType.CASE_SUMMARY,
            title=f"Case Summary – {title_val}"[:500],
            content_english=content if lang == "en" else "",
            content_hindi=content if lang == "hi" else "",
            language=lang,
            placeholders_used=placeholders,
            field_provenance={"title": tp, "cnr": cnrp, "court": courtp, "status": statusp,
                               "filing": filingp, "topic": topicp, "description": descp},
            source_references=source_refs,
            disclaimer=DISCLAIMER_EN,
            important_notes=[
                "Fields shown as [PLACEHOLDER] were not available and must be filled in.",
                "Verify all details with official court records before use.",
            ],
        )

    def generate_lawyer_brief(self, user, intake, case=None, hits=None, lang="en",
                               lawyer_name="", court_name="") -> GeneratedDraft:
        hits = hits or []
        c = case
        lawyer_val = lawyer_name or PLACEHOLDER("LAWYER NAME")
        court_display = court_name or (c.court.name if c and c.court else PLACEHOLDER("COURT NAME"))
        client_name = PLACEHOLDER("CLIENT NAME")
        cnr_val, _, _ = _field(c.cnr_number if c else intake.cnr, "CNR NUMBER", "CASE_RECORD" if c else "USER_PROVIDED")
        state_val, _, _ = _field(c.state if c else intake.state, "STATE", "CASE_RECORD" if c else "USER_PROVIDED")
        topic_val = intake.legal_topic.replace("_", " ").title()
        problem = intake.problem_summary_en or (c.description if c else PLACEHOLDER("PROBLEM DESCRIPTION"))
        docs_list = ", ".join(intake.documents) if intake.documents else PLACEHOLDER("DOCUMENT LIST")
        issues_list = "; ".join(intake.key_issues) if intake.key_issues else PLACEHOLDER("KEY ISSUES")
        source_refs = _hits_to_refs(hits)

        if lang == "hi":
            content = f"""विधिक परामर्श संक्षेप
{'='*50}

प्रति,
{lawyer_val}
{court_display}

विषय: {topic_val} विषयक कानूनी सलाह हेतु

मान्यवर,

मेरा नाम {client_name} है। मैं आपसे निम्नलिखित विषय में मार्गदर्शन प्राप्त करना चाहता/चाहती हूँ।

समस्या विवरण:
{problem}

राज्य / जिला: {state_val} / {intake.district or PLACEHOLDER("DISTRICT")}
CNR / केस संख्या: {cnr_val}
लंबित वर्ष: {str(int(intake.case_age_years)) + ' वर्ष' if intake.case_age_years else PLACEHOLDER("YEARS PENDING")}

उपलब्ध दस्तावेज़:
{docs_list}

प्रमुख मुद्दे:
{issues_list}

प्रासंगिक स्रोत:
{_format_refs(source_refs, lang)}

मैं आपसे अनुरोध करता/करती हूँ कि उपरोक्त मामले में कानूनी विकल्पों के बारे में सलाह दें।

भवदीय,
{client_name}
दिनांक: [DATE]

{DISCLAIMER_HI}"""
        else:
            content = f"""LAWYER CONSULTATION BRIEF
{'='*50}

To,
{lawyer_val}
{court_display}

Subject: Request for Legal Advice – {topic_val}

Dear Sir/Madam,

My name is {client_name}. I am seeking your guidance regarding the following matter.

Problem Description:
{problem}

State / District: {state_val} / {intake.district or PLACEHOLDER("DISTRICT")}
CNR / Case Number: {cnr_val}
Years Pending: {str(int(intake.case_age_years)) + ' years' if intake.case_age_years else PLACEHOLDER("YEARS PENDING")}

Documents Available:
{docs_list}

Key Issues:
{issues_list}

Relevant Sources:
{_format_refs(source_refs, lang)}

I request your advice on the legal options available in this matter.

Yours sincerely,
{client_name}
Date: [DATE]

{DISCLAIMER_EN}"""

        content = _safe_text(content, lang)
        return GeneratedDraft.objects.create(
            user=user, case=case,
            draft_type=DraftType.LAWYER_BRIEF,
            title=f"Lawyer Brief – {topic_val}"[:500],
            content_english=content if lang == "en" else "",
            content_hindi=content if lang == "hi" else "",
            language=lang,
            placeholders_used=[x for x in [lawyer_name, court_name] if not x],
            field_provenance={"lawyer": "USER_PROVIDED" if lawyer_name else "UNKNOWN",
                               "court": "USER_PROVIDED" if court_name else "UNKNOWN"},
            source_references=source_refs,
            disclaimer=DISCLAIMER_EN,
            important_notes=[
                "Fill in all [PLACEHOLDER] fields before presenting to a lawyer.",
                "This brief is a starting point only — your lawyer will need to verify all details.",
            ],
        )

    def generate_rti(self, user, intake, case=None, hits=None, lang="en",
                     applicant_name="", public_authority="", information_sought="") -> GeneratedDraft:
        hits = hits or []
        c = case
        app_val = applicant_name or PLACEHOLDER("APPLICANT NAME")
        auth_val = public_authority or PLACEHOLDER("PUBLIC AUTHORITY / DEPARTMENT")
        info_val = information_sought or _default_rti_info(intake, c)
        state_val, _, _ = _field(c.state if c else intake.state, "STATE", "CASE_RECORD" if c else "USER_PROVIDED")
        cnr_val, _, _ = _field(c.cnr_number if c else intake.cnr, "CNR NUMBER", "CASE_RECORD" if c else "USER_PROVIDED")
        source_refs = _hits_to_refs(hits)

        if lang == "hi":
            content = f"""सूचना का अधिकार (RTI) आवेदन
{'='*50}

सेवा में,
लोक सूचना अधिकारी
{auth_val}

विषय: सूचना के अधिकार अधिनियम, 2005 की धारा 6(1) के अंतर्गत सूचना प्राप्त करने हेतु आवेदन

महोदय/महोदया,

मैं, {app_val}, राज्य {state_val} का निवासी, निम्नलिखित जानकारी प्राप्त करना चाहता/चाहती हूँ:

मांगी गई जानकारी:
{info_val}

संदर्भ केस संख्या / CNR: {cnr_val}

मैं RTI अधिनियम 2005 के अंतर्गत उपरोक्त जानकारी 30 दिनों के भीतर प्रदान करने का अनुरोध करता/करती हूँ।

आवेदक का नाम : {app_val}
पता            : [APPLICANT ADDRESS]
दिनांक         : [DATE]
शुल्क          : ₹10/- (नकद/डिमांड ड्राफ्ट/आईपीओ)

नोट: यह मसौदा है। दाखिल करने से पहले सभी विवरण जाँचें।

{DISCLAIMER_HI}"""
        else:
            content = f"""APPLICATION UNDER RIGHT TO INFORMATION ACT, 2005
{'='*50}

To,
The Public Information Officer
{auth_val}

Subject: Application for Information under Section 6(1) of the RTI Act, 2005

Sir/Madam,

I, {app_val}, resident of {state_val}, wish to obtain the following information:

Information Sought:
{info_val}

Reference Case Number / CNR: {cnr_val}

I request the above information within 30 days as provided under the RTI Act, 2005.

Applicant Name : {app_val}
Address        : [APPLICANT ADDRESS]
Date           : [DATE]
Fee            : ₹10/- (Cash / Demand Draft / IPO)

Note: This is a draft. Verify all details before filing.

{DISCLAIMER_EN}"""

        content = _safe_text(content, lang)
        return GeneratedDraft.objects.create(
            user=user, case=case,
            draft_type=DraftType.RTI_APPLICATION,
            title=f"RTI Application – {auth_val[:60]}"[:500],
            content_english=content if lang == "en" else "",
            content_hindi=content if lang == "hi" else "",
            language=lang,
            placeholders_used=[x for x in [applicant_name, public_authority] if not x],
            field_provenance={"applicant": "USER_PROVIDED" if applicant_name else "UNKNOWN",
                               "authority": "USER_PROVIDED" if public_authority else "UNKNOWN",
                               "information": "USER_PROVIDED" if information_sought else "GENERATED"},
            source_references=source_refs,
            filing_instructions=(
                "1. Fill in all [PLACEHOLDER] fields.\n"
                "2. Pay ₹10 fee (cash/DD/IPO) at the public authority's office or online.\n"
                "3. Submit in person or by registered post to the PIO of the concerned department.\n"
                "4. Keep a copy and the receipt.\n"
                "5. If no response in 30 days, file a First Appeal with the First Appellate Authority."
            ),
            disclaimer=DISCLAIMER_EN,
            important_notes=[
                "RTI Act, 2005 applies to Central and State government bodies.",
                "Certain information is exempt under Sections 8 and 9 of the RTI Act.",
                "This draft has not been verified by a legal professional.",
            ],
        )


# ---------------------------------------------------------------------------
def _hits_to_refs(hits) -> list:
    refs = []
    for i, h in enumerate(hits[:5]):
        j = h.judgment
        src = h.source
        refs.append({
            "label": f"S{i+1}",
            "title": j.title if j else src.title,
            "citation": j.citation if j else None,
            "url": (j.source_url if j and j.source_url else src.url) if src else None,
            "verification_status": src.verification_status if src else "UNVERIFIED",
        })
    return refs


def _format_refs(refs: list, lang: str) -> str:
    if not refs:
        return "[No verified sources retrieved for this query]"
    lines = []
    for r in refs:
        citation = f" ({r['citation']})" if r.get("citation") else ""
        lines.append(f"[{r['label']}] {r['title']}{citation} — {r.get('verification_status', 'UNVERIFIED')}")
    return "\n".join(lines)


def _default_rti_info(intake, case) -> str:
    parts = []
    if case and case.cnr_number:
        parts.append(f"1. Current status and stage of case bearing CNR number {case.cnr_number}.")
        parts.append("2. Copies of all orders passed in the above case.")
        parts.append("3. Reason for pendency and expected next hearing date.")
    else:
        parts.append("1. [DESCRIBE THE SPECIFIC INFORMATION YOU NEED]")
        parts.append("2. [ADD MORE POINTS IF NEEDED]")
    if intake.legal_topic in ("LAND_DISPUTE", "PROPERTY_DISPUTE"):
        parts.append("4. Certified copy of revenue / land records pertaining to [SURVEY NUMBER / PLOT NUMBER].")
    return "\n".join(parts)
