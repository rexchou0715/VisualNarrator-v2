# 1. Models and how many rounds each should run
MODELS = {
    "GPT-o1": 5,
    "Llama3-8B": 10,
    "Qwen-14B": 10,
}

# 2. Datasets 
DATASETS = [
    "camperplus",
    "fish&chips",
    "grocery",
    "planningpoker",
    "recycling",
    "school",
    "sports",
    "supermarket",
    "ticket"
]


# 3. File-path templates


CLASS_INPUT_TEMPLATE = "data/raw/class/{model}/{dataset}/R{round}.txt"
ASSOC_INPUT_TEMPLATE = "data/raw/association/{model}/{dataset}/R{round}.txt"
CLASS_EXTRACTED_DIR = "output/class/{model}/{dataset}"
ASSOC_EXTRACTED_DIR = "output/association/{model}/{dataset}"
EXPERIMENT_OUTPUT_DIR = "output/experiment"

# 4. Skip keywords for class extraction
SKIP_KEYWORDS = [
    '**Class List:**', 
    '**Final Class List:**', 
    '[Class 1, Class 2, Class 3,...]', 
    'List:**',
    "**Refined List of Class Candidates:**",
    "**Rationale:**",
    "**Final Class List**",
    '**List**',
    'List**',
    '**Class List**'
    '**Rationale**',
    'Rationale: '
    '**Domain Entities:**',
    'Removed',
    'removed',
    'redundant',
    'irrelevant',
    'vague'
    ]



# 5. Gold/Silver/non-punishment/synonym dictionaries
GOLD_STANDARD_CLASS = {
    "recycling": [
        "feedback", "complaints", "user",
        "safe disposal events", "employees", "recycling facility",
        "waste type", "schedule", "reward",
        "activity"
    ],
    "camperplus": [
        "payments", "rules", "camp worker", "attendance", "facilities", "photos",
        "feedback", "camper", "guardians", "schedules", "activities", "camp",
        "forms", "groups", "counselor", "supplies", "positions", "behavior", "repair"
    ],
    "fish&chips": [
        "orders", "coupons", "payment",
        "products", "cash", "requests",
        "customer", "delivery person"
    ],
    "grocery": [
        "employee", "payments", "schedule",
        "message", "contracts", "certificates",
        "complaint", "salary statement", "working hours",
        "manager"
    ],
    "planningpoker": [
        "estimators", "round", "game",
        "item", "card", "estimate"
    ],
    "school": [
        "submission", "assignment", "behavior",
        "disciplinary action", "mentor", "administrator",
        "digital learning module", "guardian", "message",
        "question", "answer", "material",
        "student", "grades", "teacher",
        "class", "timetable", "attendance"
    ],
    "sports": [
        "rooms", "subscription", "schedule",
        "lessons", "trainer", "training sessions",
        "Payment information", "family membership", "customer",
        "spot", "booking", "person",
    ],
    "supermarket": [
        "recipes", "newsletter", "order",
        "products", "customer", "delivery",
        "store", "personal discount", "loyalty card",
        "wishlist", "shopping list", 
    ],
    "ticket": [
        "user", "event types", "events",
        "artists", "ticket", "payment",
        "reseller", "venue", "order",
        "genre"
    ]
}

GOLD_STANDARD_ASSOCIATION = {
    "recycling": [
        ('user', 'feedback'), ('user', 'complaint'),
        ('recycling facility', 'waste type'), ('recycling facility', 'schedule'),
        ('user', 'schedule'), ('user', 'reward'), ('user', 'activity'),
        ('employee', 'user')
    ],
    "camperplus": [
        ('camper', 'guardian'), ('camper', 'form'), ('camper', 'attendance'),
        ('camp', 'group'), ('camp', 'rule'), ('feedback', 'guardian'),
        ('group', 'schedule'), ('camper', 'photo'), ('camper', 'group'),
        ('facility', 'activity'), ('group', 'activity'), ('camper', 'camp'),
        ('camp', 'facility'), ('supply', 'camp'), ('group', 'counselor'),
        ('activity', 'schedule'), ('position', 'camp worker'), ('camp', 'camp worker'),
        ('camp', 'activity'), ('camper', 'payment'), ('feedback', 'camper'),
        ('position', 'activity'), ('photo', 'camp'), ('group', 'facility'), ('camper', 'behavior'),
        ('guardian', 'form')
    ],
    "fish&chips": [
        ('order', 'product'), ('request', 'product'), ('customer', 'order'),
        ('order', 'coupon'), ('delivery person', 'cash'), ('delivery person', 'order'),
        ('order', 'payment')
    ],
    "grocery": [
        ('employee', 'schedule'), ('employee', 'working hour'), ('employee', 'complaint'),
        ('employee', 'message'), ('employee', 'salary statement'), ('employee', 'contract'),
        ('employee', 'certificate'), ('payment', 'salary statement'), ('manager', 'complaint'), ('manager', 'message')
    ],
    "planningpoker": [
        ('game', 'round'), ('estimate', 'item'), ('item', 'round'),
        ('game', 'estimator'), ('estimator', 'estimate'), ('game', 'card')
    ],
    "school": [
        ('question', 'answer'), ('question', 'digital learning modules'), ('digital learning modules', 'material'),
        ('digital learning modules', 'class'), ('class', 'assignment'), ('class', 'student'),
        ('student', 'timetable'), ('timetable', 'teacher'), ('teacher', 'disciplinary actions'),
        ('teacher', 'behavior'), ('teacher', 'message'), ('behavior', 'student'),
        ('student', 'disciplinary actions'), ('student', 'message'), ('student', 'mentor'),
        ('student', 'guardian'), ('guardian', 'behavior'), ('student', 'submission'),
        ('submission', 'grades'), ('submission', 'assignment'), ('message', 'administrator'),
        ('message', 'guardian'), ('message', 'mentor'), ('class', 'teacher')
    ],
    "sports": [
        # schedul -> schedule, custom -> customer, subscript -> subscription, sess -> session 
        ('room', 'lesson'), ('schedule', 'lesson'), ('customer', 'subscription'),
        ('family membership', 'person'), ('customer', 'family membership'), ('customer', 'payment information'),
        ('schedule', 'trainer'), ('training session', 'schedule'), ('customer', 'booking'),
        ('booking', 'spot'), ('booking', 'lesson'), ('booking', 'training session'),
    ],
    "supermarket": [
        # custom -> customer, newslett -> newsletter, recip -> recipe, servic -> service
        ('customer', 'newsletter'), ('customer', 'wishlist'), ('customer', 'shopping list'),
        ('order', 'product'), ('customer', 'order'), ('store', 'product'),
        ('shopping list', 'product'), ('wishlist', 'product'), ('customer', 'store'),
        ('recipe', 'product'), ('customer', 'delivery'), ('customer', 'personal discount'),
        ('customer', 'loyalty card')
    ],
    "ticket": [
        # genr -> genre; event typ -> event type, venu -> venue
        ('user', 'genre'), ('user', 'event type'), ('order', 'user'),
        ('ticket', 'order'), ('order', 'payment'), ('event', 'event type'),
        ('event', 'venue'), ('event', 'artist'), ('genre', 'event'),
        ('artist', 'user'), ('reseller', 'ticket'), ('event', 'ticket'),
        ('event', 'user')
    ]
}

SILVER_STANDARD_CLASS = {
    "recycling": [
    ],
    "camperplus": [
    ],
    "fish&chips": [
        "cashier"
    ],
    "grocery": [
    ],
    "planningpoker": [
    ],
    "school": [
    ],
    "sports": [
        "timeslot",
        "fine"
    ],
    "supermarket": [
        "payment"
    ],
    "ticket": [
        "seat"
    ]
}

SILVER_STANDARD_ASSOCIATION = {
    "recycling": [
        ('employee', 'safe disposal events'), ('activity', 'waste type')
    ],
    "camperplus": [
    ],
    "fish&chips": [
        ('cashier', 'payment')
    ],
    "grocery": [
        ('employee', 'payment'), ('manager', 'employee')
    ],
    "planningpoker": [
    ],
    "school": [
    ],
    "sports": [
    ],
    "supermarket": [
        ('order', 'delivery'), ('order', 'payment')
    ],
    "ticket": [
    ]
}

SYNONYM_DICT_CLASS = {
    "camperplus": {'camp worker': ['worker', 'staff', 'staff member', 'worker-camper', 'campworker', 'staffmember', 'camp staff member', 'camp staff'], 
                   'group': ['camp group', 'campergroup', 'campgroup', 'camper group'], 
                   'activity': ['camp activity', 'task', 'event', 'campactivity'], 
                   'guardian': ['parentguardian', 'parent', 'parent/guardian', 'camperparent'], 
                   'form': ['registrationform', 'consentform', 'medical form', 'medicalform', 'registration form', 'consent form'], 
                   'facility': ['camp facility', 'internal camp facility', 'campfacility'], 
                   'feedback': ['message'],
                   'camper': ['enrolled camper'],
                   'counselor': ['camp counselor'],
                   'behavior': ['behaviorrecord'],
                   'attendance': ['attendancelog', 'AttendanceRecord']
                   },
    "fish&chips": { 'delivery person': ['deliveryperson', 'home delivery person', 'delivery-person', 'deliveryemployee', 'delivery driver', 'delivery employee'],
                   'request': ['special request', 'specialrequest']
    },
    "grocery": {'salary statement': ['employeepay', 'financial statement', 'salary', 'salarystatement', 
                                    'Financial Annual Statement', 'financialstatement', 'financial annual statement',
                                    'statement'],
                'working hour': ["scheduled Wwrk hours", "workhour", "work hour", "workinghour"],
                'schedule': ['work schedule'],
                'contract': ["employeecontract", "employee contract"],
                "certificate": ["employeecertificate", "employee certificate", "certification"],
                "manager": ["employer"],
    },
    "planningpoker": {'estimators': ["participant", "GameEstimator", "gameparticipant"],
                      'estimate': ["estimation"],
                      'round': ['gameround', 'current round']
    },
    "recycling": {'recycling facility': ['recycling center', 'special waste drop off site', 
                                         'facility','wastedropoffsite', 'waste drop off site', "recyclingfacility",
                                         "special waste drop off sites", "center", "facility", "Recyclingfacility"],
                  'waste type': ['recyclable waste type', 'recyclable material', 'non-recycllable material', 
                                 'material', 'type of waste', 'type of recyclable waste', "recyclable waste",
                                 "recyclable waste"],
                  'feedback': ['question', "userquestion"],
                  "safe disposal event": ["disposal event", "safedisposalevent"]
    },
    "school": {"class": ["subject", "course"],
               "attendance": ["absence", "student absence", "student attendance", 
                              "academic attendance", "attendance record"],
               "student": ["child"],
               "assignment": ["homework", "submission element"],
               "submission": ["answer submission", "homework submission"],
               "administrator": ["administrative staff"],
               "timetable": ["schedule"],
               "digital learning module": ["DLM", "digital learning modules (dlm)", "dlm (digital learning module)"],
               "question": ["open question", "multiple-choice question"],
               "disciplinary action": ["disciplinary record", "academic disciplinary action", 
                                       "disciplinaryaction",],
               "grade": ["academic grade",],
               "behavior": ["academic behavior"],
               "material": ["text", "video", "picture"],
    },
    "sports":{"family membership": ["membership", "familymembership"],
              "booking": ['book'],
              "training sessions": ["trainingsession", "session", "PersonalTrainingSession", 
                                    "personal training session", "personaltrainingsession", "training"],
              "Payment Information": ["paymentinformation"],
              "timeslot": ["time slot", "lessontimeslot"], 
              "room": ["practicearea", "practice area", "free practice area"]
    },
    "supermarket": {"delivery": ["grocery delivery", "delivery service", "expressdelivery", "deliveryservice", "grocerydelivery"],
                    "recipe": ["product reciprocal recipe", "meal idea", "recipe idea"],
                    "personal discount": ["discount", "special personal discount", "personaldiscount",],
                    "loyalty card": ["loyaltycard", "loyalty_card", "card"],
                    "newsletter": ["news letter"],
                    "shopping list": ["shoppinglist", "shopping_list", "grocerylist"],
                    "recipe": ["recipe idea"],
                    "order": ["grocery order", "grocery"]
    },
    "ticket": {"order": ["ticket order", "ticketorder"],
               "event type": ["eventtype", "type"],
               "user": ["attendance"],
               "event": ["show"],
               "seat": ["seating place"],
               "genre": ["genre preference"],
               "artist": ["artist preference"],
    }
}

NON_PUNISH_CLASS = {
    "camperplus": {
        "form": ["medicalForm", "consentform", "registrationForm", 
                 "consent form", "medical form", "registration form",
                 "medical form"],
    },
    "sports": {
        "room": ["practicearea", "practice area", "free practice area"]
    },
    "school": {
        "material": ["text", "video", "picture"],
        "question": ["open question", "multiple-choice question"],
    }
}

