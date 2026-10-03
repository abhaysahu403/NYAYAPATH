"""Curated, hedged procedural OPTIONS by topic (bilingual).

Each step may name `keys`: stable identifiers of curated Sources (Source.metadata["key"]). A step is only marked
source-backed if one of those sources was actually retrieved; otherwise it is shown as an unsourced
information-gathering suggestion. Nothing here asserts a fee, deadline or outcome.
"""
from typing import Dict, List

S = lambda en, hi: {"en": en, "hi": hi}  # noqa: E731

STEPS: Dict[str, dict] = {
    "gather_docs": dict(kind="INFORMATION_GATHERING", difficulty="EASY", keys=[],
        title=S("Collect and organise your documents", "अपने दस्तावेज़ इकट्ठा और व्यवस्थित करें"),
        desc=S("Keep copies of everything related to the matter: land/property papers, notices, court orders, receipts and any case paperwork.",
               "मामले से जुड़े सभी कागज़ात की प्रतियां रखें: ज़मीन/संपत्ति के दस्तावेज़, नोटिस, अदालत के आदेश, रसीदें और केस के कागज़।"),
        why=S("A lawyer or officer can only assess the situation from documents.", "वकील या अधिकारी दस्तावेज़ों के आधार पर ही स्थिति समझ सकते हैं।"),
        docs=["Identity proof", "Land / property papers", "Court orders and notices", "Receipts"]),
    "check_status": dict(kind="INFORMATION_GATHERING", difficulty="EASY", keys=[],
        title=S("Check the current case status", "केस की वर्तमान स्थिति जांचें"),
        desc=S("If you have the CNR or case number, the case status can be looked up on the official eCourts services, or by asking the court registry for the latest order sheet.",
               "यदि आपके पास CNR या केस नंबर है तो आधिकारिक eCourts सेवाओं पर केस की स्थिति देखी जा सकती है, या अदालत के रजिस्ट्री कार्यालय से नवीनतम आदेश-पत्र मांगा जा सकता है।"),
        why=S("The record shows the stage of the case and the last/next dates.", "रिकॉर्ड से केस का चरण और पिछली/अगली तारीखें पता चलती हैं।"),
        docs=["CNR or case number"]),
    "legal_aid": dict(kind="INFORMATION_GATHERING", difficulty="EASY", keys=[],
        title=S("Consider speaking to a lawyer or the District Legal Services Authority", "वकील या जिला विधिक सेवा प्राधिकरण से बात करने पर विचार करें"),
        desc=S("A qualified lawyer can review your papers. Free legal aid may be available through the District Legal Services Authority (DLSA) if you are eligible.",
               "योग्य वकील आपके कागज़ात देख सकते हैं। पात्र होने पर जिला विधिक सेवा प्राधिकरण (DLSA) के माध्यम से निःशुल्क विधिक सहायता उपलब्ध हो सकती है।"),
        why=S("Procedure and strategy depend on details only a professional can verify.", "प्रक्रिया और रणनीति ऐसे विवरणों पर निर्भर करती है जिन्हें केवल पेशेवर सत्यापित कर सकते हैं।"),
        docs=["Summary of your case", "All court papers"]),
    "early_hearing": dict(kind="POSSIBLE_OPTION", difficulty="MEDIUM", keys=["SALEM_ORDER17"],
        title=S("Ask your lawyer about seeking an early hearing / limiting adjournments", "अपने वकील से शीघ्र सुनवाई / स्थगन सीमित कराने के बारे में पूछें"),
        desc=S("Where a civil case keeps getting adjourned, a lawyer may consider whether an application for early or day-to-day hearing is appropriate. The retrieved source discusses limits on adjournments under Order XVII CPC.",
               "जहां दीवानी मामला बार-बार स्थगित होता है, वहां वकील शीघ्र या प्रतिदिन सुनवाई के आवेदन की उपयुक्तता पर विचार कर सकते हैं। प्राप्त स्रोत में CPC के आदेश XVII के अंतर्गत स्थगन की सीमाओं पर चर्चा है।"),
        why=S("Your matter has been pending for a long time.", "आपका मामला लंबे समय से लंबित है।"), docs=["Order sheet", "List of past hearing dates"]),
    "interim_relief": dict(kind="POSSIBLE_OPTION", difficulty="HARD", keys=["DORAB_INJUNCTION"],
        title=S("Ask a lawyer whether interim relief (injunction) is relevant", "वकील से पूछें कि क्या अंतरिम राहत (निषेधाज्ञा) प्रासंगिक है"),
        desc=S("For possession/encroachment disputes, a lawyer may assess whether an interim injunction could be sought. The retrieved source discusses the general principles courts consider (prima facie case, balance of convenience, irreparable injury).",
               "कब्जे/अतिक्रमण के विवादों में वकील यह आकलन कर सकते हैं कि अंतरिम निषेधाज्ञा मांगी जा सकती है या नहीं। प्राप्त स्रोत में अदालतों द्वारा देखे जाने वाले सामान्य सिद्धांतों (प्रथम दृष्टया मामला, सुविधा का संतुलन, अपूरणीय क्षति) की चर्चा है।"),
        why=S("The matter involves a possession issue.", "मामले में कब्जे का मुद्दा है।"), docs=["Proof of possession / title", "Photographs, if any"]),
    "revenue_records": dict(kind="POSSIBLE_OPTION", difficulty="MEDIUM", keys=["SURAJ_BHAN_REVENUE"],
        title=S("Obtain certified copies of revenue records and check entries", "राजस्व अभिलेखों की प्रमाणित प्रतियां लें और प्रविष्टियां जांचें"),
        desc=S("Certified copies of khasra/khatauni (or equivalent) and mutation entries can be requested from the revenue office. The retrieved source indicates revenue entries are relevant evidence but do not by themselves decide title.",
               "राजस्व कार्यालय से खसरा/खतौनी (या समकक्ष) और नामांतरण प्रविष्टियों की प्रमाणित प्रतियां मांगी जा सकती हैं। प्राप्त स्रोत के अनुसार राजस्व प्रविष्टियां प्रासंगिक साक्ष्य हैं पर अकेले स्वामित्व तय नहीं करतीं।"),
        why=S("You mentioned having land records.", "आपने भूमि अभिलेख होने का उल्लेख किया है।"), docs=["Khasra", "Khatauni", "Sale deed / title papers"]),
    "rti": dict(kind="POSSIBLE_OPTION", difficulty="EASY", keys=["RTI_ACT_2005"],
        title=S("Consider an information request (RTI) to the relevant office", "संबंधित कार्यालय को सूचना का अधिकार (RTI) आवेदन देने पर विचार करें"),
        desc=S("An RTI application may help obtain official records (for example revenue records or administrative information). The retrieved source summarises the Act's response time and appeal stages; confirm the correct authority, any court-specific rules and fee before filing.",
               "RTI आवेदन से आधिकारिक अभिलेख (जैसे राजस्व अभिलेख या प्रशासनिक जानकारी) प्राप्त करने में मदद मिल सकती है। प्राप्त स्रोत में अधिनियम की समय-सीमा और अपील के चरणों का सार है; दाखिल करने से पहले सही प्राधिकारी, अदालत-विशेष नियम और शुल्क की पुष्टि करें।"),
        why=S("Official records may clarify what is unknown.", "आधिकारिक अभिलेखों से अज्ञात बातें स्पष्ट हो सकती हैं।"), docs=["Applicant details", "Case/property identifiers"]),
    "speedy_trial": dict(kind="POSSIBLE_OPTION", difficulty="HARD", keys=["HUSSAINARA"],
        title=S("Ask a lawyer about delay and the right to speedy trial", "देरी और शीघ्र विचारण के अधिकार के बारे में वकील से पूछें"),
        desc=S("If a criminal matter or custody has been prolonged, a lawyer can advise whether the principles on speedy trial discussed in the retrieved source are relevant.",
               "यदि आपराधिक मामला या हिरासत लंबी खिंच गई है तो वकील बता सकते हैं कि प्राप्त स्रोत में चर्चित शीघ्र विचारण के सिद्धांत प्रासंगिक हैं या नहीं।"),
        why=S("The matter involves a criminal case or bail.", "मामला आपराधिक प्रकरण या जमानत से जुड़ा है।"), docs=["FIR copy", "Charge sheet", "Order sheet"]),
    "revenue_forum": dict(kind="INFORMATION_GATHERING", difficulty="MEDIUM", keys=[],
        title=S("Find out which forum handles your type of dispute", "पता करें कि आपके प्रकार का विवाद किस फोरम में सुना जाता है"),
        desc=S("Depending on whether the dispute is about possession, title or revenue entries, the matter may lie with the civil court or the revenue authorities. Ask a lawyer to confirm the correct forum for your state.",
               "विवाद कब्जे, स्वामित्व या राजस्व प्रविष्टियों का है, इसके आधार पर मामला दीवानी अदालत या राजस्व अधिकारियों के पास जा सकता है। अपने राज्य के लिए सही फोरम की पुष्टि वकील से करें।"),
        why=S("Filing in the wrong forum can waste time.", "गलत फोरम में दाखिल करने से समय व्यर्थ हो सकता है।"), docs=[]),
}

PLAYBOOKS: Dict[str, List[str]] = {
    "LAND_DISPUTE": ["gather_docs", "check_status", "legal_aid", "early_hearing", "interim_relief", "revenue_records", "rti"],
    "PROPERTY_DISPUTE": ["gather_docs", "check_status", "legal_aid", "early_hearing", "interim_relief", "revenue_records", "rti"],
    "CASE_PENDENCY": ["check_status", "gather_docs", "legal_aid", "early_hearing", "rti"],
    "COURT_PROCEDURE": ["check_status", "gather_docs", "legal_aid"],
    "RTI": ["gather_docs", "rti", "legal_aid"],
    "BAIL": ["legal_aid", "gather_docs", "check_status", "speedy_trial"],
    "CRIMINAL_CASE": ["legal_aid", "gather_docs", "check_status", "speedy_trial"],
    "CIVIL_DISPUTE": ["gather_docs", "check_status", "legal_aid", "early_hearing", "revenue_forum"],
}
DEFAULT = ["gather_docs", "legal_aid", "check_status"]


def select_steps(topic: str, flags: List[str], has_case: bool) -> List[str]:
    keys = list(PLAYBOOKS.get(topic, DEFAULT))
    flags = flags or []
    if topic in {"LAND_DISPUTE", "PROPERTY_DISPUTE"}:
        if "POSSESSION_ISSUE" not in flags:
            keys.remove("interim_relief")
        if "REVENUE_RECORD_ISSUE" not in flags:
            keys.remove("revenue_records")
        if "PENDENCY_ISSUE" not in flags and not has_case:
            keys.remove("early_hearing")
        if not has_case:
            keys.append("revenue_forum")
    return keys[:6]


def build(key: str, lang: str) -> dict:
    s = STEPS[key]
    l = "hi" if lang == "hi" else "en"
    return {"key": key, "title": s["title"][l], "description": s["desc"][l], "why_relevant": s["why"][l],
            "required_documents": s["docs"], "kind": s["kind"], "difficulty": s["difficulty"], "keys": s["keys"]}
