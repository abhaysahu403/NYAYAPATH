"""Hindi / Hinglish -> English legal search vocabulary, states and districts.

Used to (a) expand search queries (the indexed corpus is mostly English) and
(b) cross-check LLM entity extraction. Deterministic by design.
"""

# term (lower-case, Hindi or romanised) -> English search terms
TERM_MAP = {
    "जमीन": ["land"], "ज़मीन": ["land"], "zameen": ["land"], "jameen": ["land"], "zamin": ["land"], "land": ["land"],
    "कब्जा": ["possession", "encroachment"], "कब्ज़ा": ["possession", "encroachment"], "kabza": ["possession", "encroachment"],
    "kabja": ["possession", "encroachment"], "अतिक्रमण": ["encroachment"], "encroach": ["encroachment"],
    "पड़ोसी": ["neighbour"], "padosi": ["neighbour"], "neighbour": ["neighbour"], "neighbor": ["neighbour"],
    "खसरा": ["khasra", "revenue record"], "khasra": ["khasra", "revenue record"],
    "खतौनी": ["khatauni", "revenue record"], "khatauni": ["khatauni", "revenue record"],
    "खतोनी": ["khatauni", "revenue record"], "जमाबंदी": ["jamabandi", "revenue record"],
    "नामांतरण": ["mutation", "revenue record"], "mutation": ["mutation", "revenue record"],
    "पटवारी": ["patwari", "revenue record"], "तहसीलदार": ["tehsildar"], "tehsildar": ["tehsildar"],
    "रजिस्ट्री": ["sale deed", "registration"], "registry": ["sale deed", "registration"],
    "मकान": ["property", "house"], "makaan": ["property", "house"], "दुकान": ["shop", "property"],
    "संपत्ति": ["property"], "प्रॉपर्टी": ["property"], "property": ["property"],
    "केस": ["case"], "मुकदमा": ["suit", "case"], "मुक़दमा": ["suit", "case"], "case": ["case"],
    "तारीख": ["adjournment", "hearing date"], "तारीख़": ["adjournment", "hearing date"], "tareekh": ["adjournment", "hearing date"],
    "तारीख पर तारीख": ["adjournment", "delay"], "date pe date": ["adjournment", "delay"],
    "आगे नहीं बढ़ रहा": ["delay", "pendency"], "आगे नहीं बढ़": ["delay", "pendency"], "pending": ["pendency", "delay"],
    "लंबित": ["pendency", "delay"], "देरी": ["delay"], "stuck": ["delay"], "adjourn": ["adjournment"],
    "स्थगन": ["injunction", "stay"], "स्टे": ["stay", "injunction"], "stay": ["stay", "injunction"],
    "injunction": ["injunction"], "निषेधाज्ञा": ["injunction"],
    "जमानत": ["bail"], "zamanat": ["bail"], "bail": ["bail"], "गिरफ्तार": ["arrest", "custody"], "jail": ["custody", "undertrial"],
    "जेल": ["custody", "undertrial"], "हिरासत": ["custody"], "एफआईआर": ["FIR"], "fir": ["FIR"],
    "सूचना का अधिकार": ["right to information", "RTI"], "आरटीआई": ["RTI", "right to information"], "rti": ["RTI", "right to information"],
    "तलाक": ["divorce", "matrimonial"], "talaq": ["divorce", "matrimonial"], "divorce": ["divorce"],
    "भरण-पोषण": ["maintenance"], "maintenance": ["maintenance"], "दहेज": ["dowry"],
    "उपभोक्ता": ["consumer"], "consumer": ["consumer"], "मजदूरी": ["wages", "labour"], "नौकरी": ["service", "employment"],
    "दुर्घटना": ["accident", "motor accident"], "accident": ["accident"], "मुआवजा": ["compensation"], "compensation": ["compensation"],
    "वकील": ["lawyer"], "vakil": ["lawyer"], "अदालत": ["court"], "adalat": ["court"], "न्यायालय": ["court"],
    "बेदखली": ["eviction"], "किराएदार": ["tenant", "eviction"], "kirayedar": ["tenant", "eviction"],
    "वसीयत": ["will", "succession"], "बंटवारा": ["partition"], "batwara": ["partition"], "बँटवारा": ["partition"],
}

# English-ish topic hints -> LegalTopic code (used by heuristics)
TOPIC_HINTS = [
    ("RTI", ["rti", "right to information", "सूचना का अधिकार", "आरटीआई", "information request"]),
    ("BAIL", ["bail", "जमानत", "zamanat", "anticipatory"]),
    ("MOTOR_ACCIDENT", ["motor accident", "road accident", "दुर्घटना", "accident claim", "mact"]),
    ("CONSUMER_DISPUTE", ["consumer", "उपभोक्ता", "defective product", "refund"]),
    ("LABOUR_DISPUTE", ["labour", "wages", "मजदूरी", "termination", "retrench", "salary not paid"]),
    ("GOVERNMENT_SERVICE", ["government service", "pension", "सरकारी नौकरी", "promotion", "suspension"]),
    ("FAMILY_DISPUTE", ["divorce", "तलाक", "talaq", "maintenance", "भरण", "custody of child", "dowry", "दहेज", "matrimonial"]),
    ("CRIMINAL_CASE", ["fir", "एफआईआर", "arrest", "गिरफ्तार", "police", "पुलिस", "criminal", "ipc", "bns", "thana", "थाना", "chargesheet"]),
    ("LAND_DISPUTE", ["land", "जमीन", "ज़मीन", "zameen", "jameen", "khasra", "खसरा", "khatauni", "खतौनी", "खतोनी", "kabza", "कब्जा", "कब्ज़ा",
                      "encroach", "अतिक्रमण", "mutation", "नामांतरण", "खेत", "khet", "acre", "एकड़", "bigha", "बीघा", "patwari", "पटवारी"]),
    ("PROPERTY_DISPUTE", ["property", "संपत्ति", "मकान", "makaan", "flat", "plot", "partition", "बंटवारा", "batwara", "tenant", "eviction", "वसीयत"]),
    ("CASE_PENDENCY", ["pending", "लंबित", "adjourn", "तारीख पर तारीख", "date pe date", "delay", "देरी", "not moving", "आगे नहीं बढ़"]),
    ("COURT_PROCEDURE", ["procedure", "how to file", "filing", "court fee", "प्रक्रिया"]),
    ("CIVIL_DISPUTE", ["civil suit", "recovery of money", "contract", "agreement", "सिविल"]),
]

STATES = {
    "Andhra Pradesh": ["andhra pradesh", "आंध्र प्रदेश"], "Arunachal Pradesh": ["arunachal", "अरुणाचल"],
    "Assam": ["assam", "असम"], "Bihar": ["bihar", "बिहार"], "Chhattisgarh": ["chhattisgarh", "छत्तीसगढ़", "chattisgarh"],
    "Goa": ["goa", "गोवा"], "Gujarat": ["gujarat", "गुजरात"], "Haryana": ["haryana", "हरियाणा"],
    "Himachal Pradesh": ["himachal", "हिमाचल"], "Jharkhand": ["jharkhand", "झारखंड"], "Karnataka": ["karnataka", "कर्नाटक"],
    "Kerala": ["kerala", "केरल"], "Madhya Pradesh": ["madhya pradesh", "मध्य प्रदेश", "मध्यप्रदेश", "mp "],
    "Maharashtra": ["maharashtra", "महाराष्ट्र"], "Manipur": ["manipur", "मणिपुर"], "Meghalaya": ["meghalaya", "मेघालय"],
    "Mizoram": ["mizoram", "मिजोरम"], "Nagaland": ["nagaland", "नागालैंड"], "Odisha": ["odisha", "orissa", "ओडिशा", "उड़ीसा"],
    "Punjab": ["punjab", "पंजाब"], "Rajasthan": ["rajasthan", "राजस्थान"], "Sikkim": ["sikkim", "सिक्किम"],
    "Tamil Nadu": ["tamil nadu", "तमिलनाडु", "tamilnadu"], "Telangana": ["telangana", "तेलंगाना"], "Tripura": ["tripura", "त्रिपुरा"],
    "Uttar Pradesh": ["uttar pradesh", "उत्तर प्रदेश", "उत्तरप्रदेश", "up "], "Uttarakhand": ["uttarakhand", "उत्तराखंड"],
    "West Bengal": ["west bengal", "पश्चिम बंगाल"], "Delhi": ["delhi", "दिल्ली"], "Jammu and Kashmir": ["jammu", "kashmir", "जम्मू"],
    "Ladakh": ["ladakh", "लद्दाख"], "Chandigarh": ["chandigarh", "चंडीगढ़"], "Puducherry": ["puducherry", "pondicherry", "पुडुचेरी"],
}

# Small district -> (canonical district, state) map: enough for demo inference; NOT exhaustive.
DISTRICTS = {
    "bhopal": ("Bhopal", "Madhya Pradesh"), "भोपाल": ("Bhopal", "Madhya Pradesh"),
    "indore": ("Indore", "Madhya Pradesh"), "इंदौर": ("Indore", "Madhya Pradesh"),
    "jabalpur": ("Jabalpur", "Madhya Pradesh"), "जबलपुर": ("Jabalpur", "Madhya Pradesh"),
    "gwalior": ("Gwalior", "Madhya Pradesh"), "ग्वालियर": ("Gwalior", "Madhya Pradesh"),
    "ujjain": ("Ujjain", "Madhya Pradesh"), "उज्जैन": ("Ujjain", "Madhya Pradesh"),
    "sagar": ("Sagar", "Madhya Pradesh"), "सागर": ("Sagar", "Madhya Pradesh"),
    "rewa": ("Rewa", "Madhya Pradesh"), "रीवा": ("Rewa", "Madhya Pradesh"),
    "satna": ("Satna", "Madhya Pradesh"), "सतना": ("Satna", "Madhya Pradesh"),
    "dewas": ("Dewas", "Madhya Pradesh"), "देवास": ("Dewas", "Madhya Pradesh"),
    "sehore": ("Sehore", "Madhya Pradesh"), "सीहोर": ("Sehore", "Madhya Pradesh"),
    "lucknow": ("Lucknow", "Uttar Pradesh"), "लखनऊ": ("Lucknow", "Uttar Pradesh"),
    "patna": ("Patna", "Bihar"), "पटना": ("Patna", "Bihar"),
    "jaipur": ("Jaipur", "Rajasthan"), "जयपुर": ("Jaipur", "Rajasthan"),
    "pune": ("Pune", "Maharashtra"), "पुणे": ("Pune", "Maharashtra"), "mumbai": ("Mumbai", "Maharashtra"), "मुंबई": ("Mumbai", "Maharashtra"),
    "raipur": ("Raipur", "Chhattisgarh"), "रायपुर": ("Raipur", "Chhattisgarh"),
}

DOCUMENT_HINTS = {
    "khasra": ["khasra", "खसरा"], "khatauni": ["khatauni", "खतौनी", "खतोनी"], "sale deed": ["sale deed", "registry", "रजिस्ट्री", "बैनामा"],
    "mutation record": ["mutation", "नामांतरण"], "court order": ["court order", "order sheet", "आदेश"], "notice": ["notice", "नोटिस"],
    "FIR copy": ["fir", "एफआईआर"], "plaint": ["plaint", "वाद पत्र"], "property tax receipt": ["tax receipt", "property tax"],
    "jamabandi": ["jamabandi", "जमाबंदी"], "map / naksha": ["naksha", "नक्शा", "site map"],
}
