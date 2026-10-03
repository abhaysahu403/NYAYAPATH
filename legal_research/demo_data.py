"""DEMO seed data. Everything here is is_demo_data=True and verification DEMO/UNVERIFIED — NEVER 'VERIFIED'.

Real, well-known case names are included only as pointers with a short ILLUSTRATIVE summary written for this demo;
citations must be checked against official sources before any production use. The 'MP High Court' and 'District
Court' records are SYNTHETIC (fictional) and are labelled [DEMO].
"""
COURTS = [
    dict(name="Supreme Court of India", court_type="SUPREME_COURT", state=None, website="https://www.sci.gov.in"),
    dict(name="High Court of Madhya Pradesh", court_type="HIGH_COURT", state="Madhya Pradesh", district="Jabalpur"),
    dict(name="District and Sessions Court, Bhopal", court_type="DISTRICT_COURT", state="Madhya Pradesh", district="Bhopal"),
]

# key = stable id used by playbooks to mark steps as source-backed
LEGAL_INFO = [
    dict(key="RTI_ACT_2005", identifier="DEMO-RTI-ACT-2005", title="Right to Information Act, 2005 — overview (DEMO summary)",
         url="https://rtionline.gov.in", topics=["RTI", "CASE_PENDENCY", "LAND_DISPUTE"], state=None,
         text=("The Right to Information Act, 2005 lets a citizen request information held by public authorities. "
               "An application is made to the Public Information Officer of the concerned authority, with the prescribed fee. "
               "Requests can concern records such as the status of files and revenue records held by government offices. "
               "Fees, formats and timelines should be confirmed on the official RTI portal or with the authority.")),
    dict(key="ECOURTS_STATUS", identifier="DEMO-ECOURTS-STATUS", title="eCourts services — checking case status (DEMO summary)",
         url="https://ecourts.gov.in/ecourts_home/", topics=["CASE_PENDENCY", "COURT_PROCEDURE", "LAND_DISPUTE"], state=None,
         text=("The eCourts services portal lets a litigant look up the status of a case using details such as the CNR number, "
               "case number or party name. The CNR is a 16-character identifier printed on court papers. "
               "Information shown online may lag behind the court file; the court registry holds the authoritative record.")),
    dict(key="LEGAL_AID", identifier="DEMO-LEGAL-AID", title="Free legal aid under the Legal Services Authorities Act, 1987 (DEMO summary)",
         url="https://nalsa.gov.in", topics=["COURT_PROCEDURE", "CIVIL_DISPUTE", "LAND_DISPUTE", "CRIMINAL_CASE", "BAIL"], state=None,
         text=("Legal Services Authorities at the district, state and national level provide free legal services to eligible persons. "
               "Eligibility categories are set by law and rules. A person may approach the District Legal Services Authority "
               "to ask whether they qualify.")),
]

JUDGMENTS = [
    dict(key="SALEM_ORDER17", identifier="DEMO-SALEM-2005", title="Salem Advocate Bar Association v. Union of India", citation="(2005) 6 SCC 344",
         court="Supreme Court of India", year=2005, state=None, topics=["CASE_PENDENCY", "CIVIL_DISPUTE", "COURT_PROCEDURE"],
         summary="ILLUSTRATIVE (demo): concerned the working of civil procedure provisions aimed at reducing delay in civil trials, including limits on adjournments.",
         text=("This demo record points to a Supreme Court decision on civil procedure reforms aimed at reducing delay in civil suits. "
               "As summarised for this demo, the Court discussed how adjournments should be limited and how courts should manage civil trials "
               "to avoid unnecessary delay in pending civil cases. Read the official judgment before relying on any statement here.")),
    dict(key="DORAB_INJUNCTION", identifier="DEMO-DORAB-1990", title="Dorab Cawasji Warden v. Coomi Sorab Warden", citation="(1990) 2 SCC 117",
         court="Supreme Court of India", year=1990, state=None, topics=["PROPERTY_DISPUTE", "LAND_DISPUTE", "CIVIL_DISPUTE"],
         summary="ILLUSTRATIVE (demo): discusses principles courts consider when deciding temporary injunction applications in civil disputes.",
         text=("This demo record points to a Supreme Court decision discussing the considerations a court weighs when asked for a temporary "
               "injunction in a civil dispute, such as whether there is a prima facie case, the balance of convenience and the risk of "
               "irreparable harm. Whether any of this applies to a particular possession dispute depends on its facts; verify with a lawyer.")),
    dict(key="SURAJ_BHAN_REVENUE", identifier="DEMO-SURAJ-2007", title="Suraj Bhan v. Financial Commissioner", citation="(2007) 6 SCC 186",
         court="Supreme Court of India", year=2007, state=None, topics=["LAND_DISPUTE", "PROPERTY_DISPUTE"],
         summary="ILLUSTRATIVE (demo): about the legal weight of revenue-record entries and mutation in land matters.",
         text=("This demo record points to a Supreme Court decision about revenue records such as mutation entries in land matters. "
               "As summarised for this demo, such entries are generally maintained for fiscal purposes and are not by themselves a final "
               "determination of title, which is decided by a competent civil court. Read the original judgment to confirm.")),
    dict(key="HUSSAINARA", identifier="DEMO-HUSSAINARA-1980", title="Hussainara Khatoon v. Home Secretary, State of Bihar", citation="(1980) 1 SCC 81",
         court="Supreme Court of India", year=1980, state=None, topics=["CRIMINAL_CASE", "BAIL", "CASE_PENDENCY"],
         summary="ILLUSTRATIVE (demo): associated with the recognition of speedy trial as part of the right to life and personal liberty.",
         text=("This demo record points to a Supreme Court decision concerning undertrial prisoners and the right to a speedy trial "
               "as part of personal liberty under Article 21 of the Constitution. Verify details against the official report.")),
    dict(key="DEMO_MP_LAND", identifier="DEMO-MP-HC-LAND-1", title="[DEMO] Ramesh v. State of Madhya Pradesh (synthetic land possession example)",
         citation=None, court="High Court of Madhya Pradesh", year=2019, state="Madhya Pradesh",
         topics=["LAND_DISPUTE", "PROPERTY_DISPUTE", "CASE_PENDENCY"],
         summary="SYNTHETIC DEMO: fictional example of a land possession matter pending for years in Madhya Pradesh.",
         text=("[DEMO — fictional record, not a real judgment.] A farmer in Madhya Pradesh alleged that a neighbour occupied two acres of "
               "agricultural land and that the civil suit had not progressed for several years. The fictional order records that the "
               "trial court was requested to list the matter for early hearing and that parties were to produce khasra and khatauni "
               "revenue records. This example exists only to demonstrate how NyayaPath displays sources.")),
    dict(key="DEMO_DISTRICT", identifier="DEMO-BHOPAL-DC-1", title="[DEMO] Sharma v. Verma (synthetic district court property example)",
         citation=None, court="District and Sessions Court, Bhopal", year=2021, state="Madhya Pradesh", district="Bhopal",
         topics=["PROPERTY_DISPUTE", "CIVIL_DISPUTE", "LAND_DISPUTE"],
         summary="SYNTHETIC DEMO: fictional district-court property dispute used to test search.",
         text=("[DEMO — fictional record, not a real judgment.] The fictional civil suit concerned a boundary and possession dispute over a "
               "plot in Bhopal. The record notes that the parties filed revenue records and that the court listed the case for evidence. "
               "This example exists only for testing.")),
]
