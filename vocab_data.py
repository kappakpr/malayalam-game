# vocab_data.py

# vocab_data.py

VOCAB_ITEMS = [
    # 1. Family & People (കുടുംബം)
    {"id": "amma", "ml": "അമ്മ", "en": "Mother", "emoji": "👩", "cat": "Family & People"},
    {"id": "achan", "ml": "അച്ഛൻ", "en": "Father", "emoji": "👨", "cat": "Family & People"},
    {"id": "chettan", "ml": "ചേട്ടൻ", "en": "Older Brother", "emoji": "🧑", "cat": "Family & People"},
    {"id": "chechi", "ml": "ചേച്ചി", "en": "Older Sister", "emoji": "👧", "cat": "Family & People"},
    {"id": "muthachan", "ml": "മുത്തച്ഛൻ", "en": "Grandfather", "emoji": "👴", "cat": "Family & People"},
    {"id": "muthassi", "ml": "മുത്തശ്ശി", "en": "Grandmother", "emoji": "👵", "cat": "Family & People"},

    # 2. Animals (മൃഗങ്ങൾ)
    {"id": "aana", "ml": "ആന", "en": "Elephant", "emoji": "🐘", "cat": "Animals"},
    {"id": "poocha", "ml": "പൂച്ച", "en": "Cat", "emoji": "🐱", "cat": "Animals"},
    {"id": "patti", "ml": "പട്ടി", "en": "Dog", "emoji": "🐶", "cat": "Animals"},
    {"id": "simham", "ml": "സിംഹം", "en": "Lion", "emoji": "🦁", "cat": "Animals"},
    {"id": "kടുva", "ml": "കടുവ", "en": "Tiger", "emoji": "🐯", "cat": "Animals"},
    {"id": "muyal", "ml": "മുയൽ", "en": "Rabbit", "emoji": "🐰", "cat": "Animals"},

    # 3. Birds & Water Life (പക്ഷികളും മത്സ്യങ്ങളും)
    {"id": "kili", "ml": "കിളി", "en": "Bird", "emoji": "🐦", "cat": "Birds & Water Life"},
    {"id": "mayil", "ml": "മയിൽ", "en": "Peacock", "emoji": "🦚", "cat": "Birds & Water Life"},
    {"id": "kaakka", "ml": "കാക്ക", "en": "Crow", "emoji": "🐦‍⬛", "cat": "Birds & Water Life"},
    {"id": "thaaraavu", "ml": "താറാവ്", "en": "Duck", "emoji": "🦆", "cat": "Birds & Water Life"},
    {"id": "meen", "ml": "മീൻ", "en": "Fish", "emoji": "🐟", "cat": "Birds & Water Life"},
    {"id": "aama", "ml": "ആമ", "en": "Turtle", "emoji": "🐢", "cat": "Birds & Water Life"},

    # 4. Fruits (പഴങ്ങൾ)
    {"id": "pazham", "ml": "പഴം", "en": "Banana", "emoji": "🍌", "cat": "Fruits"},
    {"id": "maanga", "ml": "മാങ്ങ", "en": "Mango", "emoji": "🥭", "cat": "Fruits"},
    {"id": "chakka", "ml": "ചക്ക", "en": "Jackfruit", "emoji": "🍈", "cat": "Fruits"},
    {"id": "apple", "ml": "ആപ്പിൾ", "en": "Apple", "emoji": "🍎", "cat": "Fruits"},
    {"id": "munthiri", "ml": "മുന്തിരി", "en": "Grapes", "emoji": "🍇", "cat": "Fruits"},
    {"id": "thannimathan", "ml": "തണ്ണിമത്തൻ", "en": "Watermelon", "emoji": "🍉", "cat": "Fruits"},

    # 5. Food & Drinks (ഭക്ഷണം)
    {"id": "paal", "ml": "പാൽ", "en": "Milk", "emoji": "🥛", "cat": "Food & Drinks"},
    {"id": "vellam", "ml": "വെള്ളം", "en": "Water", "emoji": "💧", "cat": "Food & Drinks"},
    {"id": "choru", "ml": "ചോറ്", "en": "Cooked Rice", "emoji": "🍚", "cat": "Food & Drinks"},
    {"id": "dosa", "ml": "ദോശ", "en": "Dosa", "emoji": "🥞", "cat": "Food & Drinks"},
    {"id": "mutta", "ml": "മുട്ട", "en": "Egg", "emoji": "🥚", "cat": "Food & Drinks"},
    {"id": "then", "ml": "തേൻ", "en": "Honey", "emoji": "🍯", "cat": "Food & Drinks"},

    # 6. Nature & Sky (പ്രകൃതി)
    {"id": "maram", "ml": "മരം", "en": "Tree", "emoji": "🌳", "cat": "Nature & Sky"},
    {"id": "poovu", "ml": "പൂവ്", "en": "Flower", "emoji": "🌺", "cat": "Nature & Sky"},
    {"id": "sooryan", "ml": "സൂര്യൻ", "en": "Sun", "emoji": "☀️", "cat": "Nature & Sky"},
    {"id": "chandran", "ml": "ചന്ദ്രൻ", "en": "Moon", "emoji": "🌙", "cat": "Nature & Sky"},
    {"id": "mazha", "ml": "മഴ", "en": "Rain", "emoji": "🌧️", "cat": "Nature & Sky"},
    {"id": "kadal", "ml": "കടൽ", "en": "Sea / Ocean", "emoji": "🌊", "cat": "Nature & Sky"},

    # 7. Colors (നിറങ്ങൾ)
    {"id": "chuvappu", "ml": "ചുവപ്പ്", "en": "Red", "emoji": "🔴", "cat": "Colors"},
    {"id": "neela", "ml": "നീല", "en": "Blue", "emoji": "🔵", "cat": "Colors"},
    {"id": "pacha", "ml": "പച്ച", "en": "Green", "emoji": "🟢", "cat": "Colors"},
    {"id": "manja", "ml": "മഞ്ഞ", "en": "Yellow", "emoji": "🟡", "cat": "Colors"},
    {"id": "vella", "ml": "വെള്ള", "en": "White", "emoji": "⚪", "cat": "Colors"},
    {"id": "karuppu", "ml": "കറുപ്പ്", "en": "Black", "emoji": "⚫", "cat": "Colors"},

    # 8. Numbers (സംഖ്യകൾ)
    {"id": "onnu", "ml": "ഒന്ന്", "en": "One (1)", "emoji": "1️⃣", "cat": "Numbers"},
    {"id": "randu", "ml": "രണ്ട്", "en": "Two (2)", "emoji": "2️⃣", "cat": "Numbers"},
    {"id": "moonnu", "ml": "മൂന്ന്", "en": "Three (3)", "emoji": "3️⃣", "cat": "Numbers"},
    {"id": "naalu", "ml": "നാല്", "en": "Four (4)", "emoji": "4️⃣", "cat": "Numbers"},
    {"id": "anchu", "ml": "അഞ്ച്", "en": "Five (5)", "emoji": "5️⃣", "cat": "Numbers"},
    {"id": "aaru", "ml": "ആറ്", "en": "Six (6)", "emoji": "6️⃣", "cat": "Numbers"},

    # 9. Body Parts (ശരീരഭാഗങ്ങൾ)
    {"id": "kannu", "ml": "കണ്ണ്", "en": "Eye", "emoji": "👁️", "cat": "Body Parts"},
    {"id": "mookku", "ml": "മൂക്ക്", "en": "Nose", "emoji": "👃", "cat": "Body Parts"},
    {"id": "vaaya", "ml": "വായ", "en": "Mouth", "emoji": "👄", "cat": "Body Parts"},
    {"id": "chevi", "ml": "ചെവി", "en": "Ear", "emoji": "👂", "cat": "Body Parts"},
    {"id": "kai", "ml": "കൈ", "en": "Hand", "emoji": "✋", "cat": "Body Parts"},
    {"id": "kaal", "ml": "കാൽ", "en": "Leg / Foot", "emoji": "🦶", "cat": "Body Parts"},

    # 10. Home & Everyday Objects (വീടും സാധനങ്ങളും)
    {"id": "veedu", "ml": "വീട്", "en": "House", "emoji": "🏠", "cat": "Home & Objects"},
    {"id": "pusthakam", "ml": "പുസ്തകം", "en": "Book", "emoji": "📖", "cat": "Home & Objects"},
    {"id": "kuda", "ml": "കുട", "en": "Umbrella", "emoji": "☂️", "cat": "Home & Objects"},
    {"id": "panthu", "ml": "പന്ത്", "en": "Ball", "emoji": "⚽", "cat": "Home & Objects"},
    {"id": "kasera", "ml": "കസേര", "en": "Chair", "emoji": "🪑", "cat": "Home & Objects"},
    {"id": "vilakku", "ml": "വിളക്ക്", "en": "Lamp", "emoji": "🪔", "cat": "Home & Objects"},

    # 11. Vehicles & Travel (വാഹനങ്ങൾ)
    {"id": "vandi", "ml": "വണ്ടി", "en": "Car / Vehicle", "emoji": "🚗", "cat": "Vehicles"},
    {"id": "bus", "ml": "ബസ്", "en": "Bus", "emoji": "🚌", "cat": "Vehicles"},
    {"id": "theevandi", "ml": "തീവണ്ടി", "en": "Train", "emoji": "🚆", "cat": "Vehicles"},
    {"id": "vimanam", "ml": "വിമാനം", "en": "Airplane", "emoji": "✈️", "cat": "Vehicles"},
    {"id": "kappal", "ml": "കപ്പൽ", "en": "Ship", "emoji": "🚢", "cat": "Vehicles"},
    {"id": "vallam", "ml": "വള്ളം", "en": "Boat / Canoe", "emoji": "🛶", "cat": "Vehicles"},

    # 12. Action Words (പ്രവൃത്തികൾ)
    {"id": "oduka", "ml": "ഓടുക", "en": "Run", "emoji": "🏃", "cat": "Actions"},
    {"id": "nadakkuka", "ml": "നടക്കുക", "en": "Walk", "emoji": "🚶", "cat": "Actions"},
    {"id": "urangu", "ml": "ഉറങ്ങുക", "en": "Sleep", "emoji": "😴", "cat": "Actions"},
    {"id": "chirikkuka", "ml": "ചിരിക്കുക", "en": "Laugh / Smile", "emoji": "😄", "cat": "Actions"},
    {"id": "ezhuthuka", "ml": "എഴുതുക", "en": "Write", "emoji": "✍️", "cat": "Actions"},
    {"id": "vaayikkuka", "ml": "വായിക്കുക", "en": "Read", "emoji": "📚", "cat": "Actions"},

    #13.Everyday
    {"id": "rocket", "ml": "റോക്കറ്റ്", "en": "Rocket", "emoji": "🚀", "cat": "Everyday"},
    {"id": "fighter_jet", "ml": "യുദ്ധവിമാനം", "en": "Fighter Jet", "emoji": "🛩️", "cat": "Everyday"},
    {"id": "airplane", "ml": "വിമാനം", "en": "Airplane", "emoji": "✈️", "cat": "Everyday"},
    {"id": "airport", "ml": "വിമാനത്താവളം", "en": "Airport", "emoji": "🛫", "cat": "Everyday"},
    {"id": "car", "ml": "കാർ", "en": "Car", "emoji": "🚗", "cat": "Everyday"},
    {"id": "lorry", "ml": "ലോറി", "en": "Lorry", "emoji": "🚚", "cat": "Everyday"},
    {"id": "bus", "ml": "ബസ്", "en": "Bus", "emoji": "🚌", "cat": "Everyday"},
    {"id": "train", "ml": "തീവണ്ടി", "en": "Train", "emoji": "🚆", "cat": "Everyday"}
]

TRACE_LETTERS = [
    # Vowels (സ്വരങ്ങൾ)
    {"id": "letter_a", "char": "അ", "translit": "a", "hint": "അമ്മ (Amma - Mother)"},
    {"id": "letter_aa", "char": "ആ", "translit": "aa", "hint": "ആന (Aana - Elephant)"},
    {"id": "letter_i", "char": "ഇ", "translit": "i", "hint": "ഇല (Ila - Leaf)"},
    {"id": "letter_ee", "char": "ഈ", "translit": "ee", "hint": "ഈച്ച (Eecha - Housefly)"},
    {"id": "letter_u", "char": "ഉ", "translit": "u", "hint": "ഉറുമ്പ് (Urumbu - Ant)"},
    {"id": "letter_oo", "char": "ഊ", "translit": "oo", "hint": "ഊഞ്ഞാൽ (Oonjaal - Swing)"},
    {"id": "letter_e", "char": "എ", "translit": "e", "hint": "എലി (Eli - Mouse)"},
    {"id": "letter_ae", "char": "ഏ", "translit": "ae", "hint": "ഏണി (Aeni - Ladder)"},
    {"id": "letter_ai", "char": "ഐ", "translit": "ai", "hint": "ഐസ് (Ice)"},
    {"id": "letter_o", "char": "ഒ", "translit": "o", "hint": "ഒട്ടകം (Ottakam - Camel)"},
    {"id": "letter_oa", "char": "ഓ", "translit": "oa", "hint": "ഓടം (Odam - Boat)"},
    # Common Consonants (വ്യഞ്ജനങ്ങൾ)
    {"id": "letter_ka", "char": "ക", "translit": "ka", "hint": "കണ്ണ് (Kannu - Eye)"},
    {"id": "letter_cha", "char": "ച", "translit": "cha", "hint": "ചക്ക (Chakka - Jackfruit)"},
    {"id": "letter_tha", "char": "ത", "translit": "tha", "hint": "തവള (Thavala - Frog)"},
    {"id": "letter_na", "char": "ന", "translit": "na", "hint": "നക്ഷത്രം (Nakshathram - Star)"},
    {"id": "letter_pa", "char": "പ", "translit": "pa", "hint": "പൂച്ച (Poocha - Cat)"},
    {"id": "letter_ma", "char": "മ", "translit": "ma", "hint": "മരം (Maram - Tree)"},
    {"id": "letter_ya", "char": "യ", "translit": "ya", "hint": "യന്ത്രം (Yanthram - Machine)"},
    {"id": "letter_ra", "char": "ര", "translit": "ra", "hint": "രണ്ട് (Randu - Two)"},
    {"id": "letter_la", "char": "ല", "translit": "la", "hint": "ലഡു (Laddu)"},
    {"id": "letter_va", "char": "വ", "translit": "va", "hint": "വള്ളം (Vallam - Boat)"},
]