"""
VocabPro - WhatsApp Bot Module
Green API Integration for WhatsApp Messaging
"""

import os
from dotenv import load_dotenv

# Load .env file from current directory  
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(env_path)

import random
import time
import json
import threading
import uuid
import requests
from datetime import datetime

# Green API Configuration
GREEN_API_INSTANCE_ID = os.environ.get("GREEN_API_INSTANCE_ID", "7107621945")
GREEN_API_TOKEN = os.environ.get("GREEN_API_TOKEN", "15571d94ece4499f9f117d2edb4282ceb063c9594be849fdb0")
SCHEDULE_TIME = os.environ.get("SCHEDULE_TIME", "09:30")

# Groq API Configuration (Free - for chatbot)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.1-8b-instant"

# OpenRouter API Configuration (Free - for translation/enrichment)
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_FREE_MODEL = "google/gemma-4-31b-it:free"
OPENROUTER_TRANSLATION_MODELS = [
    "meta-llama/llama-3.2-3b-instruct:free",
    "openai/gpt-oss-120b:free",
]

# Fallback vocabulary list (used when database is empty)
fallback_vocab_list = [
    {"word": "Ubiquitous", "phonetic": "yoo-BIK-wi-tuhs", "meaning": "সর্বত্র বিদ্যমান", "example": "Smartphones have become ubiquitous in modern society."},
    {"word": "Pragmatic", "phonetic": "prag-MAT-ik", "meaning": "বাস্তবসম্মত", "example": "She took a pragmatic approach to solving the problem."},
    {"word": "Eloquent", "phonetic": "EL-uh-kwuhnt", "meaning": "বাকপটু", "example": "His eloquent speech moved the audience to tears."},
    {"word": "Benevolent", "phonetic": "buh-NEV-uh-luhnt", "meaning": "দয়ালু", "example": "The benevolent donor gave millions to charity."},
    {"word": "Ambiguous", "phonetic": "am-BIG-yoo-uhs", "meaning": "অস্পষ্ট", "example": "The contract contains several ambiguous clauses."},
    {"word": "Meticulous", "phonetic": "muh-TIK-yoo-luhs", "meaning": "সতর্ক", "example": "She is meticulous about keeping her workspace organized."},
    {"word": "Resilient", "phonetic": "ri-ZIL-yuhnt", "meaning": "সহনশীল", "example": "Children are often more resilient than adults think."},
    {"word": "Innovative", "phonetic": "IN-uh-vay-tiv", "meaning": "উদ্ভাবনী", "example": "The company is known for its innovative products."},
    {"word": "Substantial", "phonetic": "suhb-STAN-shuhl", "meaning": "বিপুল", "example": "There has been a substantial increase in sales."},
    {"word": "Ephemeral", "phonetic": "i-FEM-er-uhl", "meaning": "ক্ষণস্থায়ী", "example": "Fame can be ephemeral in the entertainment industry."},
    {"word": "Ambition", "phonetic": "am-BI-shuhn", "meaning": "উচ্চাকাঙ্ক্ষা", "example": "Her ambition is to become a doctor."},
    {"word": "Apprehensive", "phonetic": "ap-ri-HEN-siv", "meaning": "উদ্বিগ্ন", "example": "I was apprehensive about the job interview."},
    {"word": "Consequence", "phonetic": "KON-suh-kwens", "meaning": "পরিণাম", "example": "You must consider the consequences of your actions."},
    {"word": "Crucial", "phonetic": "KROO-shuhl", "meaning": "গুরুত্বপূর্ণ", "example": "It is crucial to arrive on time for the meeting."},
    {"word": "Diligent", "phonetic": "DIL-i-juhnt", "meaning": "পরিশ্রমী", "example": "She is a diligent student who never misses class."},
    {"word": "Emerge", "phonetic": "i-MURJ", "meaning": "উদ্ভূত হওয়া", "example": "New technologies continue to emerge every year."},
    {"word": "Enormous", "phonetic": "i-NOR-muhs", "meaning": "বিশাল", "example": "The project required an enormous amount of resources."},
    {"word": "Fundamental", "phonetic": "fuhn-duh-MEN-tuhl", "meaning": "মৌলিক", "example": "Reading is a fundamental skill for learning."},
    {"word": "Gratitude", "phonetic": "GRAT-i-tood", "meaning": "কৃতজ্ঞতা", "example": "I expressed my gratitude for their help."},
    {"word": "Hypothesis", "phonetic": "hy-POTH-uh-sis", "meaning": "প্রকল্প", "example": "The scientist tested her hypothesis through experiments."},
    {"word": "Justify", "phonetic": "JUS-tuh-fy", "meaning": "যুক্তি দেখানো", "example": "Can you justify your decision to leave early?"},
    {"word": "Maturity", "phonetic": "muh-CHOR-i-tee", "meaning": "পরিপক্বতা", "example": "He showed maturity beyond his years."},
    {"word": "Perspective", "phonetic": "per-SPEK-tiv", "meaning": "দৃষ্টিভঙ্গি", "example": "Try to see the issue from another perspective."},
    {"word": "Scrutinize", "phonetic": "SKROO-tuh-nyz", "meaning": "গভীরভাবে পরীক্ষা", "example": "The auditor will scrutinize all financial records."},
    {"word": "Transient", "phonetic": "TRAN-zhuhnt", "meaning": "অস্থায়ী", "example": "The transient nature of fame makes it unpredictable."},
    {"word": "Ultimate", "phonetic": "UL-tuh-mit", "meaning": "চূড়ান্ত", "example": "This is the ultimate solution to the problem."},
    {"word": "Validate", "phonetic": "VAL-i-dayt", "meaning": "যাচাই করা", "example": "Please validate your email address to continue."},
    {"word": "Widespread", "phonetic": "WYD-spred", "meaning": "ব্যাপক", "example": "The disease has become widespread across the region."},
{"word": "Adequate", "phonetic": "AD-uh-kwit", "meaning": "পর্যাপ্ত", "example": "Make sure you get adequate rest before the exam."},
    {"word": "Acclaim", "phonetic": "uh-KLAIM", "meaning": "স্বীকৃতি", "example": "The movie received widespread acclaim from critics."},
    {"word": "Brisk", "phonetic": "brisk", "meaning": "তাড়াতাড়ি", "example": "Business is brisk during the holiday season."},
    {"word": "Cacophony", "phonetic": "kuh-KOF-uh-nee", "meaning": "কর্কশ শব্দ", "example": "The cacophony of car horns made it hard to concentrate."},
    {"word": "Decorum", "phonetic": "di-KOR-uhm", "meaning": "শৃঙ্খলা", "example": "The guests maintained decorum throughout the ceremony."},
    {"word": "Ephemeral", "phonetic": "i-FEM-er-uhl", "meaning": "ক্ষণস্থায়ী", "example": "Social media fame is often ephemeral."},
    {"word": "Fervent", "phonetic": "FUR-vuhnt", "meaning": "আবেগপূর্ণ", "example": "She is a fervent supporter of animal rights."},
    {"word": "Gregarious", "phonetic": "gri-GAIR-ee-uhs", "meaning": "মিশুক", "example": "She has a gregarious personality and loves parties."},
    {"word": "Hierarchical", "phonetic": "hy-uh-RAR-kih-kuhl", "meaning": "শ্রেণিবদ্ধ", "example": "The company has a hierarchical structure."},
    {"word": "Immutable", "phonetic": "i-MYOO-tuh-buhl", "meaning": "অপরিবর্তনীয়", "example": "The laws of physics are considered immutable."},
    {"word": "Juxtapose", "phonetic": "juhk-stuh-POHZ", "meaning": "পাশাপাশি রাখা", "example": "The artist juxtaposed light and dark colors."},
    {"word": "Kinetic", "phonetic": "ki-NET-ik", "meaning": "গতিশীল", "example": "The kinetic energy depends on speed."},
    {"word": "Lucid", "phonetic": "LOO-sid", "meaning": "স্পষ্ট", "example": "Her explanation was clear and lucid."},
    {"word": "Magnitude", "phonetic": "MAG-ni-tood", "meaning": "পরিমাণ", "example": "The magnitude of the problem is enormous."},
    {"word": "Nuance", "phonetic": "NOO-ahns", "meaning": "সূক্ষ্মতা", "example": "There are many nuances in the Bengali language."},
    {"word": "Oscillate", "phonetic": "OS-uh-layt", "meaning": "দোলতে থাকা", "example": "The pendulum oscillates back and forth."},
    {"word": "Proliferate", "phonetic": "pruh-LIF-uh-rayt", "meaning": "দ্রুত বিস্তার", "example": "Social media platforms have proliferated."},
    {"word": "Quandary", "phonetic": "KWON-dree", "meaning": "দ্বিধা", "example": "I am in a quandary about which university to choose."},
    {"word": "Radical", "phonetic": "RAD-i-kuhl", "meaning": "মৌলিক", "example": "The new CEO made radical changes."},
    {"word": "Salvage", "phonetic": "SAL-vij", "meaning": "উদ্ধার করা", "example": "They managed to salvage some items from the fire."},
    {"word": "Taciturn", "phonetic": "TAS-i-turn", "meaning": "নীরব", "example": "The taciturn man rarely spoke at meetings."},
    {"word": "Vicarious", "phonetic": "vi-KAIR-ee-uhs", "meaning": "পরোক্ষ", "example": "She felt vicarious joy watching her daughter succeed."},
    {"word": "Zealous", "phonetic": "ZEL-uhs", "meaning": "উৎসাহী", "example": "She is a zealous advocate for environmental causes."},
    {"word": "Analogy", "phonetic": "uh-NAL-uh-jee", "meaning": "উপমা", "example": "The teacher used an analogy to explain the concept."},
    {"word": "Paradox", "phonetic": "PAR-uh-doks", "meaning": "বিপরীত ধারণা", "example": "The paradox of choice is that more options lead to less satisfaction."},
    {"word": "Synthesize", "phonetic": "SIN-thuh-syz", "meaning": "সংশ্লেষণ করা", "example": "The researcher synthesized data from multiple sources."},
    {"word": "Catalyst", "phonetic": "KAT-uh-list", "meaning": "উদ্দীপক", "example": "The meeting was a catalyst for change."},
    {"word": "Emulate", "phonetic": "EM-yoo-layt", "meaning": "অনুকরণ করা", "example": "Young athletes often emulate their sports heroes."},
    {"word": "Formulate", "phonetic": "FOR-myoo-layt", "meaning": "প্রণয়ন করা", "example": "The government formulated a new policy."},
{"word": "Hypothetical", "phonetic": "hy-puh-THET-i-kuhl", "meaning": "অনুমানভিত্তিক", "example": "Let's consider a hypothetical scenario."},
    {"word": "Abundant", "phonetic": "uh-BUHN-duhnt", "meaning": "প্রচুর", "example": "The region has abundant natural resources."},
    {"word": "Bernoulli", "phonetic": "ber-NOO-lee", "meaning": "বার্নুলি (গণিত)", "example": "Bernoulli's principle explains how airplanes fly."},
    {"word": "Conscientious", "phonetic": "kon-shen-SH shuhs", "meaning": "সত্যানিষ্ঠ", "example": "She is a conscientious worker who never cuts corners."},
    {"word": "Debilitate", "phonetic": "di-BIL-i-tayt", "meaning": "দুর্বল করা", "example": "The illness can debilitate patients for months."},
    {"word": "Eclectic", "phonetic": "i-KLEK-tik", "meaning": "নানা ধরনের", "example": "She has eclectic taste in music."},
    {"word": "Fortuitous", "phonetic": "for-TOO-i-tuhs", "meaning": "আকস্মিক", "example": "It was a fortuitous meeting that changed my life."},
    {"word": "Garbled", "phonetic": "GAR-buhld", "meaning": "বিভ্রান্ত", "example": "The message was garbled due to poor connection."},
    {"word": "Hegemony", "phonetic": "hi-JEM-uh-nee", "meaning": "আধিপত্য", "example": "The country established hegemony over the region."},
    {"word": "Implication", "phonetic": "im-pli-KAY-shuhn", "meaning": "প্রভাব", "example": "The implications of this decision are far-reaching."},
    {"word": "Jubilation", "phonetic": "joo-bi-LAY-shuhn", "meaning": "উৎসব", "example": "There was jubilation after the team won."},
    {"word": "Kindle", "phonetic": "KIN-duhl", "meaning": "উদ্দীপ্ত করা", "example": "The speech kindled hope in the audience."},
    {"word": "Lethargic", "phonetic": "luh-THAR-jik", "meaning": "অলস", "example": "The hot weather made everyone feel lethargic."},
    {"word": "Mundane", "phonetic": "muhn-DAYN", "meaning": "সাধারণ", "example": "She finds joy in mundane everyday activities."},
    {"word": "Nefarious", "phonetic": "ni-FAIR-ee-uhs", "meaning": "দুষ্ট", "example": "The villain had nefarious plans for the city."},
    {"word": "Obscure", "phonetic": "uhb-SKYUR", "meaning": "অস্পষ্ট", "example": "The book covers obscure historical facts."},
    {"word": "Prudent", "phonetic": "PROO-dnt", "meaning": "সতর্ক", "example": "It would be prudent to save money for emergencies."},
    {"word": "Quintessential", "phonetic": "kwin-tuh-SEN-shuhl", "meaning": "সেরা", "example": "She is the quintessential professional."},
    {"word": "Robust", "phonetic": "roh-BUHS T", "meaning": "শক্তিশালী", "example": "The company has a robust business model."},
    {"word": "Sublime", "phonetic": "suh-BLYM", "meaning": "উন্নত", "example": "The music was absolutely sublime."},
    {"word": "Tenacious", "phonetic": "tuh-NAY-shuhs", "meaning": "দৃঢ়", "example": "She is tenacious in pursuing her goals."},
    {"word": "Ubiquitous", "phonetic": "yoo-BIK-wi-tuhs", "meaning": "সর্বত্র", "example": "Smartphones have become ubiquitous."},
    {"word": "Verbose", "phonetic": "ver-BOHS", "meaning": "বাগাড়ম্বরপূর্ণ", "example": "His writing style is overly verbose."},
    {"word": "Wary", "phonetic": "WAIR-ee", "meaning": "সতর্ক", "example": "Be wary of strangers offering free gifts."},
    {"word": "Xenophobia", "phonetic": "zen-uh-FOH-bee-uh", "meaning": "বিদেশীদের প্রতি ঘৃণা", "example": "Xenophobia is a serious social problem."},
    {"word": "Yield", "phonetic": "yeeld", "meaning": "ফল দেওয়া", "example": "The investment yielded good returns."},
    {"word": "Zealot", "phonetic": "ZEL-uht", "meaning": "উন্মত্ত অনুসারী", "example": "The zealot refused to listen to reason."},
    {"word": "Adept", "phonetic": "uh-DEPT", "meaning": "দক্ষ", "example": "She is adept at handling difficult situations."},
    {"word": "Brevity", "phonetic": "BREV-i-tee", "meaning": "সংক্ষিপ্ততা", "example": "Brevity is the soul of wit."},
    {"word": "Candid", "phonetic": "KAN-did", "meaning": "সরাসরি", "example": "I appreciate your candid feedback."},
    {"word": "Deteriorate", "phonetic": "di-TEER-ee-uh-rayt", "meaning": "খারাপ হওয়া", "example": "His health began to deteriorate."},
    {"word": "Empirical", "phonetic": "em-PIR-i-kuhl", "meaning": "প্রায়োগিক", "example": "The study is based on empirical evidence."},
    {"word": "Fluctuate", "phonetic": "FLUK-choo-ayt", "meaning": "ওঠানামা করা", "example": "Prices fluctuate based on demand."},
    {"word": "Genuine", "phonetic": "JEN-yoo-in", "meaning": "আসল", "example": "She showed genuine concern for others."},
    {"word": "Haphazard", "phonetic": "HAP-haz-erd", "meaning": "এলোমেলো", "example": "The plans were made in a haphazard manner."},
    {"word": "Intense", "phonetic": "in-TENS", "meaning": "তীব্র", "example": "The heat was intense during summer."},
    {"word": "Jovial", "phonetic": "JOH-vee-uhl", "meaning": "আনন্দময়", "example": "He has a jovial personality that brightens the room."},
    {"word": "Keen", "phonetic": "keen", "meaning": "আগ্রহী", "example": "She is keen to learn new skills."},
    {"word": "Loquacious", "phonetic": "loh-KWAY-shuhs", "meaning": "বাগানী", "example": "The loquacious host kept everyone entertained."},
    {"word": "Mitigate", "phonetic": "MIT-i-gayt", "meaning": "কমানো", "example": "Steps were taken to mitigate the damage."},
    {"word": "Negligible", "phonetic": "NEG-li-ji-buhl", "meaning": "অতি সামান্য", "example": "The risk is negligible."},
    {"word": "Obstinate", "phonetic": "OB-sti-nit", "meaning": "জেদী", "example": "He was obstinate in his views."},
    {"word": "Plausible", "phonetic": "PLAW-zi-buhl", "meaning": "বিশ্বাসযোগ্য", "example": "Her explanation seemed plausible."},
    {"word": "Quirky", "phonetic": "KWUR-kee", "meaning": "অদ্ভুত", "example": "She has a quirky sense of humor."},
    {"word": "Reticent", "phonetic": "RET-i-snt", "meaning": "মুখবন্ধ", "example": "He was reticent about his personal life."},
    {"word": "Surplus", "phonetic": "SUR-pluhs", "meaning": "উদ্বৃত্ত", "example": "We have a surplus of supplies."},
    {"word": "Tangible", "phonetic": "TAN-ji-buhl", "meaning": "বাস্তব", "example": "We need tangible results."},
    {"word": "Undermine", "phonetic": "uhn-der-MYN", "meaning": "দুর্বল করা", "example": "His comments undermine my authority."},
    {"word": "Vague", "phonetic": "vayg", "meaning": "অস্পষ্ট", "example": "The instructions were vague."},
    {"word": "Whimsical", "phonetic": "HWIM-zi-kuhl", "meaning": "কৌতুকপূর্ণ", "example": "The garden has a whimsical design."},
    {"word": "Acclaimed", "phonetic": "uh-KLAIMD", "meaning": "প্রশংসিত", "example": "The film was critically acclaimed."},
    {"word": "Budding", "phonetic": "BUH-ding", "meaning": "উন্নয়নশীল", "example": "She is a budding entrepreneur."},
    {"word": "Cognitive", "phonetic": "KOG-ni-tiv", "meaning": "জ্ঞানীয়", "example": "Cognitive abilities develop over time."},
    {"word": "Diligent", "phonetic": "DIL-i-jnt", "meaning": "পরিশ্রমী", "example": "She is diligent in her studies."},
    {"word": "Exemplify", "phonetic": "eg-ZEM-pli-fy", "meaning": "উদাহরণ হওয়া", "example": "She exemplifies leadership."},
    {"word": "Formidable", "phonetic": "FOR-mi-da-buhl", "meaning": "ভয়ংকর", "example": "They faced formidable challenges."},
    {"word": "Gregarious", "phonetic": "gri-GAIR-ee-uhs", "meaning": "মিশুক", "example": "She is gregarious and makes friends easily."},
    {"word": "Holistic", "phonetic": "hoh-LIS-tik", "meaning": "সম্পূর্ণ", "example": "We need a holistic approach to solving the problem."},
    {"word": "Instinct", "phonetic": "IN-stingkt", "meaning": "স্বতঃস্ফূর্ত", "example": "Trust your instincts when making decisions."},
    {"word": "Judicious", "phonetic": "joo-DISH-uhs", "meaning": "বিচারশীল", "example": "We need a judicious use of resources."},
    {"word": "Kinetic", "phonetic": "ki-NET-ik", "meaning": "গতিসম্পর্কিত", "example": "Kinetic energy depends on mass and velocity."},
    {"word": "Luminous", "phonetic": "LOO-mi-nuhs", "meaning": "উজ্জ্বল", "example": "The luminous moon lit up the night."},
    {"word": "Meticulous", "phonetic": "muh-TIK-yoo-luhs", "meaning": "সতর্ক", "example": "She is meticulous about details."},
    {"word": "Nocturnal", "phonetic": "nok-TUR-nuhl", "meaning": "রাত্রিচর", "example": "Owls are nocturnal birds."},
    {"word": "Omnipotent", "phonetic": "om-NIP-uh-tnt", "meaning": "সর্বশক্তিমান", "example": "No one is truly omnipotent."},
    {"word": "Pervasive", "phonetic": "per-VAY-siv", "meaning": "ব্যাপক", "example": "The influence of social media is pervasive."},
    {"word": "Querulous", "phonetic": "KWER-uh-luhs", "meaning": "অভিযোগকারী", "example": "He is querulous and complains constantly."},
    {"word": "Ravishing", "phonetic": "RAV-i-shing", "meaning": "মনোরম", "example": "She looked ravishing in her dress."},
    {"word": "Scintillating", "phonetic": "SIN-ti-lay-ting", "meaning": "চমকপ্রদ", "example": "The performance was scintillating."},
    {"word": "Thematic", "phonetic": "thi-MAT-ik", "meaning": "বিষয়গত", "example": "The conference has a thematic focus."},
    {"word": "Unequivocal", "phonetic": "un-i-KWIV-uh-kuhl", "meaning": "স্পষ্ট", "example": "Her answer was unequivocal."},
    {"word": "Vigorous", "phonetic": "VIG-er-uhs", "meaning": "শক্তিশালী", "example": "She maintains a vigorous exercise routine."},
    {"word": "Wistful", "phonetic": "WIST-fuhl", "meaning": "বিষণ্ণ", "example": "She had a wistful look as she remembered the past."},
    {"word": "Yearning", "phonetic": "YUR-ning", "meaning": "তীব্র আকাঙ্ক্ষা", "example": "She felt a yearning for home."},
    {"word": "Zephyr", "phonetic": "ZEF-er", "meaning": "মৃদু বাতাস", "example": "A gentle zephyr blew through the trees."},
    {"word": "Ambivalent", "phonetic": "am-BIV-uh-luhnt", "meaning": "দ্বিধাগ্রস্ত", "example": "She felt ambivalent about the decision."},
    {"word": "Benevolent", "phonetic": "buh-NEV-uh-luhnt", "meaning": "দয়ালু", "example": "The benevolent organization helps the poor."},
    {"word": "Capricious", "phonetic": "kuh-PRISH-uhs", "meaning": "অস্থির", "example": "The weather is capricious in spring."},
    {"word": "Deleterious", "phonetic": "del-i-TEER-ee-uhs", "meaning": "ক্ষতিকর", "example": "Smoking has deleterious effects on health."},
    {"word": "Effervescent", "phonetic": "ef-er-VES-nt", "meaning": "উল্লাসপূর্ণ", "example": "She has an effervescent personality."},
    {"word": "Fastidious", "phonetic": "fa-STID-ee-uhs", "meaning": "নিখুঁত", "example": "He is fastidious about cleanliness."},
    {"word": "Garrulous", "phonetic": "GAR-uh-luhs", "meaning": "বাগাড়ম্বরপূর্ণ", "example": "The garrulous talk show host spoke for hours."},
    {"word": "Hubris", "phonetic": "HYOO-bris", "meaning": "অহংকার", "example": "His hubris led to his downfall."},
    {"word": "Iconoclast", "phonetic": "hy-KON-uh-klast", "meaning": "ধর্মনিরপেক্ষ", "example": "She was an iconoclast who challenged traditions."},
    {"word": "Juxtaposition", "phonetic": "juhk-stuh-puh-ZI-shuhn", "meaning": "পাশাপাশি স্থাপন", "example": "The juxtaposition of old and new architecture."},
    {"word": "Kaleidoscope", "phonetic": "kuh-LY-duh-skohp", "meaning": "বর্ণিল", "example": "The market was a kaleidoscope of colors."},
    {"word": "Languid", "phonetic": "LANG-gwid", "meaning": "ক্ষীণ", "example": "The hot weather made everyone feel languid."},
    {"word": "Mellifluous", "phonetic": "muh-LIF-loo-uhs", "meaning": "মধুর", "example": "She has a mellifluous voice."},
    {"word": "Nebulous", "phonetic": "NEB-yoo-luhs", "meaning": "অস্পষ্ট", "example": "The plan remained nebulous."},
    {"word": "Obsequious", "phonetic": "ob-SEE-kwee-uhs", "meaning": "খোশামুদি", "example": "The obsequious waiter pleased the customers."},
    {"word": "Panacea", "phonetic": "pan-uh-SEE-uh", "meaning": "সর্বরোগহার", "example": "There is no panacea for all problems."},
    {"word": "Quixotic", "phonetic": "kwik-SOT-ik", "meaning": "অবাস্তব", "example": "His quixotic ideas rarely succeed."},
    {"word": "Recalcitrant", "phonetic": "ri-KAL-si-trnt", "meaning": "অবাধ্য", "example": "The recalcitrant student refused to follow rules."},
    {"word": "Sagacious", "phonetic": "suh-GAY-shuhs", "meaning": "বিচারশীল", "example": "The sagacious leader made wise decisions."},
    {"word": "Trepidation", "phonetic": "trep-i-DAY-shuhn", "meaning": "ভয়", "example": "She approached the interview with trepidation."},
    {"word": "Unctuous", "phonetic": "UNGK-choo-uhs", "meaning": "চাটুকারিতাপূর্ণ", "example": "His unctuous manner annoyed everyone."},
    {"word": "Vehement", "phonetic": "VEE-uh-mnt", "meaning": "তীব্র", "example": "She was vehement in her opposition."},
    {"word": "Winsome", "phonetic": "WIN-suhm", "meaning": "মনোহর", "example": "She gave a winsome smile."},
    {"word": "Yoke", "phonetic": "yohk", "meaning": "যুক্ত করা", "example": "The treaty yoked the two nations together."},
    {"word": "Zany", "phonetic": "ZAY-nee", "meaning": "পাগলা", "example": "The zany comedy kept everyone laughing."},
  ]

# ==================== DATABASE FUNCTIONS ====================

def get_vocabulary_from_db(count: int = 10, start_index: int = 0, category: str = None) -> list:
    """Get vocabulary words from PostgreSQL database"""
    try:
        import database
        words = database.get_vocabulary_words(count, start_index, category)
        if words:
            return words
    except Exception as e:
        print(f"Database error: {e}")
    return []

def get_vocabulary_count() -> int:
    """Get total vocabulary count from database"""
    try:
        import database
        return database.get_vocabulary_count()
    except:
        return 0

# ==================== VOCABULARY GENERATION ====================

CATEGORY_PROMPTS = {
    "ielts": "Generate {count} IELTS vocabulary words. Use high-frequency words from Cambridge IELTS and Barron's IELTS word lists. Academic collocations, formal register, Writing Task 2 vocabulary. Difficulty: B2-C1.",

    "gre": "Generate {count} GRE/GMAT vocabulary words. Use challenging words from Barron's 800, Manhattan GRE, and Magoosh word lists. Hard words like 'perfunctory', 'sycophant', 'obsequious', 'recondite'. Difficulty: C1-C2.",

    "common": "Generate {count} common English vocabulary words for everyday use. Useful words for daily conversation, phrasal verbs, idioms, and general communication. Difficulty: A2-B2."
}

def generate_vocabulary(count: int = 50, category: str = None) -> dict:
    """Generate vocabulary using OpenRouter free API with model fallbacks"""
    if not OPENROUTER_API_KEY:
        return {"success": False, "error": "OPENROUTER_API_KEY not configured"}

    cat = category.lower().strip() if category else None

    if cat and cat in CATEGORY_PROMPTS:
        cat_instruction = CATEGORY_PROMPTS[cat].format(count=count)
    else:
        cat_instruction = f"Generate {count} vocabulary words for English learners in Bangladesh. Mix from all categories."
        cat = None

    prompt = f"""{cat_instruction}

Return a JSON array. Each element:
{{"word":"...","phonetic":"/IPA/","meaning_bn":"বাংলা","example":"English sentence."}}

Rules:
- IPA phonetic with slashes for every word
- meaning_bn: ONE simple Bengali meaning only (no commas, no multiple meanings). Pick the most common/easiest meaning.
- example: Short sentence, MAX 10 words. Simple and easy to understand.
- Return ONLY the JSON array, nothing else

Generate {count} words:"""

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://vocabpro.com",
        "X-Title": "VocabPro"
    }

    all_models = [OPENROUTER_FREE_MODEL] + OPENROUTER_TRANSLATION_MODELS

    for model in all_models:
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=120)

            if response.status_code == 200:
                result = response.json()
                text = result.get("choices", [{}])[0].get("message", {}).get("content", "")

                text = text.strip()
                if text.startswith("```json"):
                    text = text[7:]
                if text.startswith("```"):
                    text = text[3:]
                if text.endswith("```"):
                    text = text[:-3]

                words = json.loads(text.strip())

                import database
                saved = 0
                for w in words:
                    if cat:
                        category_str = cat
                    else:
                        cats = w.get("categories", [])
                        if not cats:
                            cats = [w.get("category", "")]
                        category_str = ",".join(c.strip().lower() for c in cats if c.strip())

                    if database.add_vocabulary_word(
                        w.get("word", ""),
                        w.get("meaning_bn", ""),
                        w.get("example", ""),
                        category_str,
                        w.get("phonetic", "")
                    ):
                        saved += 1

                return {"success": True, "generated": len(words), "saved": saved}
            else:
                print(f"Vocab model {model} failed: {response.status_code}")

        except json.JSONDecodeError as e:
            print(f"Vocab model {model} JSON error: {e}")
        except Exception as e:
            print(f"Vocab model {model} error: {e}")

    return {"success": False, "error": "All translation models failed"}

def get_daily_words(count: int = 10, start_index: int = 0, category: str = None) -> list:
    """Get vocabulary words - first from database, then fallback to list"""
    db_words = get_vocabulary_from_db(count, start_index, category)
    if db_words:
        return db_words
    
    words = []
    vocab_len = len(fallback_vocab_list)
    
    for i in range(count):
        index = (start_index + i) % vocab_len
        item = fallback_vocab_list[index]
        words.append({
            "word": item["word"],
            "phonetic": item["phonetic"],
            "meaning": item["meaning"],
            "example": item["example"]
        })
    
    return words

def enrich_words_with_ai(word_list: list, category: str = "", batch_size: int = 20) -> dict:
    """Take a list of plain words and use AI to generate meanings, phonetics, examples.
    Processes in batches to avoid timeout. Returns {"processed": N, "saved": N, "skipped": N}."""
    import database

    total_processed = 0
    total_saved = 0
    total_skipped = 0

    for i in range(0, len(word_list), batch_size):
        batch = word_list[i:i + batch_size]
        words_str = ", ".join(batch)

        prompt = f"""For these English words, provide their details as a JSON array:
Words: {words_str}

For each word return:
{{"word":"the_word","phonetic":"/IPA pronunciation/","meaning_bn":"bengali meaning in bengali script","example":"example sentence"}}

Rules:
- IPA phonetic with slashes for every word
- Bengali script for meaning_bn
- Natural English example sentence
- Return ONLY the JSON array, nothing else
- Include ALL {len(batch)} words, do not skip any"""

        enriched = _call_ai_for_enrichment(prompt)
        if not enriched:
            total_skipped += len(batch)
            continue

        for w in enriched:
            word = w.get("word", "").strip()
            if not word:
                total_skipped += 1
                continue
            success = database.add_vocabulary_word(
                word,
                w.get("meaning_bn", ""),
                w.get("example", ""),
                category,
                w.get("phonetic", "")
            )
            if success:
                total_saved += 1
            else:
                total_skipped += 1
            total_processed += 1

    return {"processed": total_processed, "saved": total_saved, "skipped": total_skipped}


def _call_ai_for_enrichment(prompt: str) -> list:
    """Call OpenRouter to enrich words. Returns parsed JSON list or None."""

    if OPENROUTER_API_KEY:
        all_models = [OPENROUTER_FREE_MODEL] + OPENROUTER_TRANSLATION_MODELS
        for model in all_models:
            try:
                url = "https://openrouter.ai/api/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://vocabpro.com",
                    "X-Title": "VocabPro"
                }
                data = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3
                }
                response = requests.post(url, headers=headers, json=data, timeout=90)
                if response.status_code == 200:
                    text = response.json().get("choices", [{}])[0].get("message", {}).get("content") or ""
                    text = text.strip()
                    if text.startswith("```json"):
                        text = text[7:]
                    if text.startswith("```"):
                        text = text[3:]
                    if text.endswith("```"):
                        text = text[:-3]
                    if text:
                        return json.loads(text.strip())
                else:
                    print(f"Enrichment model {model} failed: {response.status_code}")
            except Exception as e:
                print(f"Enrichment model {model} error: {e}")

    return None


def create_vocabulary_message(words: list) -> str:
    """Create formatted vocabulary message with new format"""
    message = "📚 *Daily Vocabulary - VocabPro*\n"
    message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for i, item in enumerate(words, 1):
        word = item.get('word', '')
        phonetic = item.get('phonetic', '')
        meaning = item.get('meaning', item.get('meaning_bn', ''))
        example = item.get('example', '')
        
        # New format: Word (phonetic) - meaning
        if phonetic:
            message += f"{i}. {word} ({phonetic}) - {meaning}\n"
        else:
            message += f"{i}. {word} - {meaning}\n"
        
        # Example sentence
        if example:
            message += f"   📝 {example}\n"
        
        message += "\n"
    
    message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    message += f"⏰ Daily at {SCHEDULE_TIME}\n"
    message += "💡 Practice makes perfect!"
    
    return message

def create_welcome_words_message(words: list) -> str:
    """Create formatted message for 3 welcome words"""
    message = ""
    
    for i, item in enumerate(words, 1):
        word = item.get('word', '')
        phonetic = item.get('phonetic', '')
        meaning = item.get('meaning', item.get('meaning_bn', ''))
        example = item.get('example', '')
        
        if phonetic:
            message += f"{i}. {word} ({phonetic}) - {meaning}\n"
        else:
            message += f"{i}. {word} - {meaning}\n"
        
        if example:
            message += f"   📝 {example}\n"
        
        message += "\n"
    
    return message


def create_welcome_message(name: str) -> str:
    """Create enhanced welcome message for new subscriber"""
    words = get_daily_words(count=3, start_index=0, category=None)
    words_message = create_welcome_words_message(words)
    
    return f"""🌟 Welcome to VocabPro, {name}! 🌟

🎯 Your English journey starts NOW!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💪 Here's what VocabPro offers you:
• 📖 10 new vocabulary words daily
• 🤖 AI-powered chatbot for practice
• 🏆 Weekly quiz contests with prizes
• 📊 Track progress & earn achievements

⭐ You're on a FREE 7-DAY TRIAL
   Master 70+ words in just one week!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📚 Your first 3 words - start learning now!

{words_message}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 "Consistency is the key to fluency!"

Stay motivated, keep learning! 🇧🇩🚀

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📞 Questions? Reply to this message!"""

def create_help_message() -> str:
    """Create help message"""
    return """📖 *VocabPro Commands*

• JOIN - Subscribe to daily vocabulary
• STOP - Unsubscribe
• VOCAB - Get 10 words now
• STATUS - Check your subscription
• TIME - Show schedule time
• HELP - Show this message

Daily words at {} - Practice every day!""".format(SCHEDULE_TIME)

def create_subscription_message(is_paid: bool, days_left: int = 0) -> str:
    """Create subscription status message"""
    if is_paid:
        return "✅ Your VocabPro subscription is active! You'll receive daily vocabulary."
    else:
        return f"⚠️ Your trial ends in {days_left} days. Pay 15 Taka to continue:\n\nSend 15 Taka to 01608872016 via bKash"

def send_whatsapp_message(phone: str, message: str) -> bool:
    """Send WhatsApp message via Green API"""
    url = f"https://api.green-api.com/waInstance{GREEN_API_INSTANCE_ID}/sendMessage/{GREEN_API_TOKEN}"
    data = {
        "chatId": f"{phone}@c.us",
        "message": message
    }
    
    try:
        response = requests.post(url, json=data, timeout=30)
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending to {phone}: {e}")
        return False

def send_to_all_subscribers(subscribers: list) -> dict:
    """Send daily vocabulary to all subscribers with spam prevention"""
    import database
    
    sent = 0
    failed = 0
    total = len(subscribers)
    
    print(f"Starting broadcast to {total} subscribers...")
    
    for i, subscriber in enumerate(subscribers):
        phone = subscriber.get("whatsapp_number", "")
        user_id = subscriber.get("id")
        last_index = subscriber.get("last_word_index", 0)
        
        if phone:
            try:
                # Random delay 2-5 seconds between each message
                # This prevents WhatsApp from flagging as spam
                if i > 0:
                    delay = random.randint(2, 5)
                    print(f"Waiting {delay}s before sending to {phone}...")
                    time.sleep(delay)
                
                # Get user's preferred category
                user_category = subscriber.get("preferred_category", "ielts")

                # Get words starting from user's last index, filtered by category
                words = get_daily_words(10, last_index, category=user_category)
                message = create_vocabulary_message(words)

                if send_whatsapp_message(phone, message):
                    sent += 1
                    # Update last_word_index for next time
                    total_words = get_vocabulary_count()
                    new_index = (last_index + 10) % total_words if total_words > 0 else last_index + 10
                    database.update_last_word_index(user_id, new_index)
                    # Update leaderboard counters
                    database.increment_leaderboard_words(user_id, 10)
                    database.update_user_progress(user_id)
                    print(f"✓ Sent to {phone} (word index: {new_index})")
                else:
                    failed += 1
                    print(f"✗ Failed to send to {phone}")
                    
            except Exception as e:
                print(f"Error sending to {phone}: {e}")
                failed += 1
    
    print(f"Broadcast complete: {sent} sent, {failed} failed")
    return {"sent": sent, "failed": failed, "total": total}

def send_welcome_to_user(phone: str, name: str) -> bool:
    """Send welcome message to new user"""
    message = create_welcome_message(name)
    return send_whatsapp_message(phone, message)


def create_contest_winner_message(winner: dict, contest_name: str) -> str:
    """Create WhatsApp message for contest winner"""
    rank = winner.get("rank", 0)
    name = winner.get("name", "User")
    score = winner.get("score", 0)
    time_seconds = winner.get("time_seconds", 0)
    
    minutes = time_seconds // 60
    seconds = time_seconds % 60
    
    rank_emoji = {
        1: "🥇",
        2: "🥈",
        3: "🥉",
        4: "4️⃣",
        5: "5️⃣"
    }.get(rank, f"#{rank}")
    
    message = f"""🏆 VocabPro Weekly Challenge Results!

{rank_emoji} {name}!

📊 Your Score: {score}/25
⏱️ Time: {minutes}m {seconds}s
🎯 Rank: #{rank}

Congratulations on your achievement!

Next challenge starts this Friday!
💪 Keep practicing!"""

    return message


def handle_incoming_message(phone: str, message: str) -> str:
    """Process incoming message and return response"""
    msg = message.strip().upper()
    
    if msg in ["JOIN", "SUBSCRIBE", "START", "YES"]:
        return "You're already subscribed! Send VOCAB to get words now."
    
    elif msg in ["STOP", "UNSUBSCRIBE", "CANCEL"]:
        return "Unsubscribed successfully! Send JOIN to subscribe again."
    
    elif msg in ["VOCAB", "WORDS", "GET"]:
        words = get_daily_words()
        return create_vocabulary_message(words)
    
    elif msg in ["STATUS", "SUBSCRIPTION"]:
        return "Your subscription is active! Daily words at " + SCHEDULE_TIME
    
    elif msg in ["TIME", "SCHEDULE"]:
        return f"Daily vocabulary is sent at {SCHEDULE_TIME} Bangladesh time."
    
    elif msg in ["HELP", "INFO", "?"]:
        return create_help_message()
    
    else:
        return f"Unknown command. Send HELP for available commands."

# ==================== CHATBOT ====================

CHATBOT_PERSONAS = {
    "chat": {
        "name": "C_ium",
        "icon": "🤖",
        "description": "Friendly AI companion for casual English conversation",
        "system_prompt": """You are C_ium, a friendly AI English companion by VocabPro for Bengali students in Bangladesh.

Rules:
- Act like a warm, casual friend — not a teacher
- Keep replies to 1-2 short sentences max, like texting
- Understand Bengali and respond in English
- Correct grammar naturally by modeling, not lecturing
- On greeting: just say hi and ask one short question. NEVER write more than 2 sentences on first greeting."""
    },
    "mentor": {
        "name": "C_ium",
        "icon": "🎓",
        "description": "Personal English mentor and exam coach",
        "system_prompt": """You are C_ium, a personal English mentor by VocabPro for Bengali students in Bangladesh preparing for IELTS/GRE.

Rules:
- Be encouraging and supportive
- On greeting: say hi and ask ONE question only (e.g. "preparing for IELTS or GRE?"). NEVER write more than 2 sentences on first greeting.
- Keep replies focused (2-3 paragraphs max)
- Use bullet points for explanations
- End with a question to keep them engaged"""
    },
    "tutor": {
        "name": "C_ium",
        "icon": "👨‍🏫",
        "description": "Patient, encouraging personal language coach",
        "system_prompt": """You are C_ium, a patient English tutor by VocabPro for Bengali students in Bangladesh.

Rules:
- Help with vocabulary, grammar, pronunciation, and translations
- Keep replies short (1-2 paragraphs)
- On greeting: just say hi and ask how you can help. Max 2 sentences."""
    },
    "ielts_examiner": {
        "name": "C_ium",
        "icon": "📝",
        "description": "Practice IELTS speaking and writing with a mock examiner",
        "system_prompt": """You are C_ium, a mock IELTS examiner by VocabPro for Bengali students in Bangladesh.

Rules:
- Help with IELTS Speaking and Writing practice
- On greeting: say hi, ask if they want speaking or writing practice. Max 2 sentences.
- Keep replies focused (2-3 paragraphs)"""
    },
    "conversation_partner": {
        "name": "C_ium",
        "icon": "💬",
        "description": "Casual English conversation practice",
        "system_prompt": """You are C_ium, a casual conversation partner by VocabPro for Bengali students in Bangladesh.

Rules:
- Have natural, relaxed conversations
- Gently correct mistakes by modeling correct English
- Keep replies short (1-2 sentences)
- On greeting: say hi casually and ask what's up. Max 2 sentences."""
    },
    "grammar_teacher": {
        "name": "C_ium",
        "icon": "📖",
        "description": "Deep grammar explanations and exercises",
        "system_prompt": """You are C_ium, a grammar teacher by VocabPro for Bengali students in Bangladesh.

Rules:
- Explain grammar rules clearly with examples
- Use bullet points for complex rules
- Keep explanations concise (2-3 paragraphs)
- On greeting: say hi and ask what grammar topic they need. Max 2 sentences."""
    }
}

def _call_openrouter_model(model: str, messages: list) -> dict:
    """Try a single OpenRouter model. Returns {'success': True, 'response': ...} or {'success': False}."""
    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://vocabpro.com",
            "X-Title": "VocabPro"
        }
        data = {"model": model, "messages": messages, "temperature": 0.7, "max_tokens": 1024}
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            text = result.get("choices", [{}])[0].get("message", {}).get("content") or ""
            if text.strip():
                return {"success": True, "response": text.strip()}
        print(f"OpenRouter model {model} failed: {response.status_code}")
    except Exception as e:
        print(f"OpenRouter model {model} error: {e}")
    return {"success": False}


# ============================================================================
# IMPORT JOB MANAGEMENT
# ============================================================================

IMPORT_JOBS = {}

def create_import_job(words: list, category: str = "general") -> str:
    """Start a background import job. Returns job_id for progress tracking."""
    job_id = str(uuid.uuid4())[:8]

    IMPORT_JOBS[job_id] = {
        "status": "running",
        "total": len(words),
        "processed": 0,
        "saved": 0,
        "failed": 0,
        "errors": [],
        "words": words,
        "category": category
    }

    thread = threading.Thread(target=_process_import_job, args=(job_id,), daemon=True)
    thread.start()

    return job_id

def _process_import_job(job_id: str):
    """Background worker that processes word import batches."""
    import database

    job = IMPORT_JOBS.get(job_id)
    if not job:
        return

    words = job["words"]
    category = job["category"]
    batch_size = 20  # Smaller batches for faster AI response

    for i in range(0, len(words), batch_size):
        batch = words[i:i + batch_size]

        current_job = IMPORT_JOBS.get(job_id, {})
        if current_job.get("status") == "cancelled":
            job["status"] = "cancelled"
            break

        words_str = ", ".join(batch)
        prompt = f"""For these English words, provide their details as a JSON array:
Words: {words_str}

For each word return:
{{"word":"the_word","phonetic":"/IPA/","meaning_bn":"bengali meaning","example":"example sentence"}}

Rules:
- IPA phonetic with slashes
- Bengali script for meaning_bn
- Natural English example sentence
- Return ONLY the JSON array
- Include ALL {len(batch)} words"""

        try:
            enriched = _call_ai_for_enrichment(prompt)
        except Exception as e:
            print(f"Import batch {i//batch_size + 1} error: {e}")
            enriched = None

        if enriched and len(enriched) > 0:
            # Add category to each word for bulk insert
            for w in enriched:
                if "category" not in w or not w["category"]:
                    w["category"] = category
            result = database.bulk_insert_vocabulary(enriched)
            job["saved"] += result["success"]
            job["failed"] += result["failed"]
            print(f"Import batch {i//batch_size + 1}: saved {result['success']}, failed {result['failed']}")
        else:
            job["failed"] += len(batch)
            job["errors"].append(f"AI failed for batch {i//batch_size + 1}")
            print(f"Import batch {i//batch_size + 1}: AI enrichment returned None")

        job["processed"] += len(batch)

    current_job = IMPORT_JOBS.get(job_id, {})
    if current_job.get("status") != "cancelled":
        if job["processed"] >= job["total"]:
            job["status"] = "completed"
        else:
            job["status"] = "partial"

def get_job_status(job_id: str) -> dict:
    """Get the current status of an import job."""
    job = IMPORT_JOBS.get(job_id)
    if not job:
        return {"status": "not_found"}

    if job["total"] > 0:
        percentage = int((job["processed"] / job["total"]) * 100)
    else:
        percentage = 0

    return {
        "status": job["status"],
        "percentage": percentage,
        "processed": job["processed"],
        "total": job["total"],
        "saved": job["saved"],
        "failed": job["failed"],
        "errors": job.get("errors", [])[:5]
    }

def cancel_import_job(job_id: str) -> bool:
    """Cancel a running import job."""
    if job_id in IMPORT_JOBS:
        IMPORT_JOBS[job_id]["status"] = "cancelled"
        return True
    return False


def _call_groq_model(messages: list) -> dict:
    """Try Groq API for chatbot. Returns {'success': True, 'response': ...} or {'success': False}."""
    if not GROQ_API_KEY:
        return {"success": False}
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {"model": GROQ_MODEL, "messages": messages, "temperature": 0.7, "max_tokens": 1024}
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            text = result.get("choices", [{}])[0].get("message", {}).get("content") or ""
            if text.strip():
                return {"success": True, "response": text.strip()}
        print(f"Groq model {GROQ_MODEL} failed: {response.status_code}")
    except Exception as e:
        print(f"Groq model {GROQ_MODEL} error: {e}")
    return {"success": False}


def generate_chatbot_response(user_message: str, context: list, persona: str = "chat") -> dict:
    """Generate a chatbot response using Groq (primary) and DeepSeek via OpenRouter (secondary)"""
    persona_config = CHATBOT_PERSONAS.get(persona, CHATBOT_PERSONAS["chat"])
    system_prompt = persona_config["system_prompt"]

    # Build messages array: system + context + new user message
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(context)
    messages.append({"role": "user", "content": user_message})

    # Try Groq first (primary)
    result = _call_groq_model(messages)
    if result["success"]:
        return result

    # Fallback to DeepSeek via OpenRouter (secondary)
    if OPENROUTER_API_KEY:
        result = _call_openrouter_model("deepseek/deepseek-v4-flash:free", messages)
        if result["success"]:
            return result

    return {"success": False, "error": "Sorry, I couldn't process your message right now. Please try again."}


# Test function
def test_send():
    """Test sending message"""
    test_phone = "8801608872016"
    message = "Test message from VocabPro!"
    result = send_whatsapp_message(test_phone, message)
    print(f"Test send result: {result}")
    return result

if __name__ == "__main__":
    test_send()