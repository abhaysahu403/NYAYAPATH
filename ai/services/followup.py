"""FollowUpQuestionEngine: ask only for the minimum information that would materially improve the answer."""
from typing import List

from ai.schemas import IntakeResult

Q = {
    "problem": {"en": "Could you briefly describe what the problem is and what has happened so far?",
                "hi": "कृपया संक्षेप में बताइए कि समस्या क्या है और अब तक क्या हुआ है?"},
    "state": {"en": "Which state and district is this matter in?", "hi": "यह मामला किस राज्य और जिले का है?"},
    "district": {"en": "Which district is this matter in?", "hi": "यह मामला किस जिले का है?"},
    "case_number": {"en": "Do you have the case number or the 16-character CNR number? (It is on your court papers.)",
                    "hi": "क्या आपके पास केस नंबर या 16 अक्षर का CNR नंबर है? (यह आपके अदालती कागज़ों पर होता है।)"},
    "existing_case": {"en": "Has a case already been filed in court for this matter?",
                      "hi": "क्या इस मामले में अदालत में पहले से कोई केस दायर है?"},
}
CASE_TOPICS = {"LAND_DISPUTE", "PROPERTY_DISPUTE", "CIVIL_DISPUTE", "CASE_PENDENCY", "CRIMINAL_CASE", "BAIL", "FAMILY_DISPUTE",
               "CONSUMER_DISPUTE", "LABOUR_DISPUTE", "MOTOR_ACCIDENT", "GOVERNMENT_SERVICE"}


class FollowUpService:
    MAX_QUESTIONS = 3

    def questions(self, intake: IntakeResult, lang: str = "en", has_case_record: bool = False) -> List[dict]:
        l = "hi" if lang == "hi" else "en"
        out: List[str] = []
        if intake.legal_topic == "OTHER" and not intake.search_keywords and not intake.key_issues and not intake.problem_summary_en:
            out.append("problem")
        elif intake.legal_topic in CASE_TOPICS or intake.legal_topic == "OTHER":
            if not intake.state:
                out.append("state")
            elif not intake.district and intake.legal_topic != "OTHER":
                out.append("district")
            if intake.existing_case and not (intake.cnr or intake.case_number or has_case_record):
                out.append("case_number")
            elif intake.existing_case is None and intake.legal_topic in CASE_TOPICS and intake.legal_topic != "CASE_PENDENCY":
                out.append("existing_case")
        return [{"field": f, "question": Q[f][l]} for f in out[: self.MAX_QUESTIONS]]
