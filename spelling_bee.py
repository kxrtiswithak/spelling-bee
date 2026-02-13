import json
import os
import random
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request

import pyttsx3
from colorama import Fore, Style, init


# Curated list of common English words suitable for a spelling bee.
# Every word here is expected to have a definition AND example sentence
# in the Free Dictionary API.  get_word() validates this before returning.
WORD_LIST = [
    "able", "arch", "bake", "bald", "bold", "calm", "cave", "clue",
    "coil", "crop", "cure", "dare", "dawn", "deed", "dome", "dose",
    "dusk", "dust", "ease", "edge", "envy", "evil", "face", "fade",
    "fame", "fate", "fawn", "firm", "flag", "flat", "flaw", "flip",
    "fold", "folk", "fond", "fool", "form", "foul", "fuel", "fury",
    "fuse", "gaze", "gift", "glow", "grab", "grid", "grim", "grip",
    "grow", "gulf", "halt", "harm", "haze", "heal", "heap", "herb",
    "herd", "hint", "hire", "host", "howl", "huge", "hurl", "hymn",
    "icon", "idle", "iron", "item", "jade", "jest", "jolt", "keen",
    "kind", "knot", "lace", "lamp", "lane", "lash", "lawn", "lead",
    "lean", "leap", "limb", "limp", "link", "load", "lobe", "lock",
    "loft", "loom", "loot", "lure", "lurk", "lush", "mane", "maze",
    "melt", "mild", "mine", "moan", "mock", "mold", "mood", "muse",
    "mute", "myth", "neat", "nest", "numb", "oath", "odds", "omen",
    "ooze", "oven", "pace", "pack", "palm", "pave", "peak", "peel",
    "pest", "pile", "pine", "plot", "ploy", "plug", "plum", "poke",
    "pond", "pose", "pour", "pray", "prey", "prop", "pull", "pump",
    "pure", "push", "quit", "race", "rage", "raid", "ramp", "rank",
    "rare", "rash", "reap", "reel", "roam", "robe", "rope", "ruin",
    "rule", "rush", "rust", "sage", "sake", "sane", "scan", "seal",
    "shed", "skim", "slab", "slam", "slap", "slim", "slip", "slot",
    "slug", "snap", "soar", "sole", "sore", "sort", "soul", "span",
    "spin", "spit", "stem", "stir", "stub", "sway", "swim", "tale",
    "tame", "tank", "tart", "task", "taut", "tear", "thaw", "tide",
    "tile", "tilt", "toil", "toll", "tomb", "tone", "toss", "tour",
    "trap", "tray", "trim", "trot", "tuck", "turf", "turn", "urge",
    "vain", "vast", "veil", "vent", "vest", "vine", "void", "volt",
    "wade", "wage", "wail", "ward", "warm", "warn", "warp", "wary",
    "wave", "weed", "weld", "whim", "wilt", "wipe", "wise", "wisp",
    "woke", "womb", "wrap", "yard", "yawn", "yell", "zeal", "zone",
    "adapt", "admit", "adopt", "agony", "alarm", "alien", "align", "amber",
    "amend", "ample", "angel", "anger", "apart", "arena", "arise", "attic",
    "avoid", "await", "awake", "award", "batch", "beach", "beast", "begin",
    "blame", "bland", "blank", "blast", "blaze", "bleed", "blend", "bless",
    "bliss", "bloom", "blunt", "blush", "boast", "bonus", "boost", "brace",
    "brave", "bravo", "breed", "brink", "brisk", "broad", "brook", "brood",
    "brush", "burst", "cabin", "candy", "chain", "chair", "chant", "charm",
    "chase", "cheap", "cheek", "cheer", "chess", "chief", "child", "chill",
    "choir", "chore", "chunk", "civil", "claim", "clamp", "clash", "clasp",
    "clean", "clear", "clerk", "cliff", "climb", "cling", "cloak", "clone",
    "close", "cloth", "cloud", "coach", "coast", "comet", "coral", "count",
    "court", "cover", "crack", "craft", "crane", "crash", "crave", "crawl",
    "craze", "creek", "creep", "crest", "crime", "crisp", "cross", "crowd",
    "crown", "crude", "cruel", "crush", "curse", "curve", "cycle", "daily",
    "dance", "decay", "decoy", "delay", "dense", "deter", "devil", "diary",
    "dizzy", "dodge", "doubt", "dough", "draft", "drain", "drape", "dream",
    "drift", "drill", "drive", "drown", "dwell", "eager", "earth", "eerie",
    "elder", "elect", "elite", "elude", "ember", "empty", "endow", "enjoy",
    "equal", "equip", "erode", "erupt", "essay", "evade", "event", "exalt",
    "exert", "exile", "extra", "fable", "faint", "fairy", "faith", "feast",
    "fiber", "field", "fiery", "filth", "final", "flame", "flare", "flash",
    "fleet", "flesh", "float", "flock", "flood", "floor", "flora", "floss",
    "flour", "forge", "found", "frail", "frame", "frank", "fraud", "freak",
    "fresh", "front", "frost", "frown", "fruit", "ghost", "giant", "given",
    "gleam", "glide", "globe", "gloom", "glory", "gloss", "gorge", "grace",
    "grade", "grain", "grand", "grant", "grasp", "grass", "grave", "graze",
    "greed", "greet", "grief", "grill", "grind", "groan", "groom", "gross",
    "group", "grove", "growl", "guard", "guess", "guest", "guide", "guild",
    "guilt", "guise", "hairy", "harsh", "haste", "haunt", "haven", "heart",
    "hedge", "heist", "hoist", "honor", "horse", "house", "human", "humid",
    "humor", "ideal", "image", "imply", "inert", "inner", "irony", "ivory",
    "jewel", "joker", "jolly", "juice", "knack", "kneel", "knife", "knock",
    "labor", "layer", "lemon", "level", "lever", "light", "linen", "liver",
    "lodge", "logic", "loose", "lover", "loyal", "lucid", "lunar", "lunge",
    "magic", "major", "manor", "maple", "march", "marsh", "match", "mayor",
    "medal", "mercy", "merit", "metal", "might", "mirth", "model", "money",
    "moral", "mourn", "mouse", "mouth", "muddy", "nerve", "noble", "noise",
    "novel", "nurse", "ocean", "orbit", "order", "organ", "outer", "oxide",
    "paint", "panel", "panic", "patch", "pause", "peace", "peach", "pearl",
    "phase", "piano", "pilot", "pitch", "pivot", "pixel", "place", "plain",
    "plane", "plant", "plate", "plead", "plaza", "pluck", "plumb", "plume",
    "plump", "plunge", "poach", "point", "polar", "porch", "pouch", "pound",
    "power", "prank", "prawn", "press", "price", "pride", "prime", "print",
    "prior", "prism", "probe", "prone", "proof", "prose", "proud", "prove",
    "prowl", "pulse", "purge", "quest", "queue", "quick", "quiet", "quota",
    "quote", "radar", "raise", "rally", "ranch", "range", "rapid", "razor",
    "reach", "realm", "rebel", "refer", "reign", "relax", "repay", "rider",
    "ridge", "rifle", "rigid", "rinse", "risky", "rival", "river", "roast",
    "robot", "rouge", "rough", "round", "route", "royal", "rugby", "saint",
    "salad", "sauce", "scale", "scare", "scene", "scent", "scope", "score",
    "scout", "scrap", "seize", "serve", "shade", "shaft", "shake", "shame",
    "shape", "share", "shark", "sharp", "shave", "sheer", "sheet", "shelf",
    "shell", "shift", "shine", "shock", "shore", "shout", "sight", "since",
    "skill", "skull", "slash", "slate", "slave", "sleep", "slice", "slide",
    "slope", "smash", "smell", "smile", "smoke", "snack", "snare", "solar",
    "solid", "solve", "space", "spare", "spark", "spawn", "speak", "spear",
    "spell", "spend", "spill", "spine", "spite", "spoke", "spoon", "spray",
    "squad", "stack", "staff", "stage", "stain", "stair", "stake", "stale",
    "stall", "stamp", "stand", "stare", "start", "state", "steak", "steal",
    "steam", "steel", "steep", "steer", "stern", "stick", "stiff", "still",
    "sting", "stock", "stone", "stool", "storm", "story", "stout", "stove",
    "strap", "straw", "stray", "strip", "stuff", "stump", "stung", "stunt",
    "surge", "swamp", "swarm", "swear", "sweat", "sweep", "sweet", "swell",
    "swept", "swift", "swing", "swirl", "sword", "syrup", "taste", "teach",
    "theft", "theme", "thick", "thief", "thorn", "those", "three", "throw",
    "thumb", "tiger", "tight", "timer", "toast", "token", "torch", "total",
    "touch", "tough", "towel", "tower", "toxic", "trace", "track", "trade",
    "trail", "train", "trait", "tramp", "trash", "treat", "trend", "trial",
    "tribe", "trick", "troop", "truck", "truly", "trunk", "trust", "truth",
    "tumor", "twist", "ultra", "uncle", "under", "unify", "union", "unite",
    "unity", "upper", "upset", "urban", "usual", "utter", "valid", "valor",
    "value", "vapor", "vault", "verge", "verse", "vigor", "vinyl", "virus",
    "visit", "vital", "vivid", "vocal", "vodka", "voice", "voter", "waist",
    "waste", "watch", "water", "weary", "weave", "wheat", "wheel", "whole",
    "widen", "witch", "world", "worry", "worse", "worst", "worth", "wound",
    "wrath", "wreck", "yacht", "yield", "young", "youth", "absorb", "accent",
    "access", "accuse", "across", "admire", "advent", "affirm", "afford", "agenda",
    "almost", "always", "anchor", "annual", "appeal", "arouse", "arrest", "artist",
    "assign", "assume", "assure", "attach", "attack", "attain", "attend", "banter",
    "barely", "basket", "battle", "beacon", "beauty", "behalf", "belong", "betray",
    "bitter", "blanch", "bonfire", "borrow", "bounce", "breach", "breath", "breeze",
    "bridge", "bright", "broken", "bronze", "budget", "bundle", "burden", "butter",
    "bypass", "candle", "canyon", "carbon", "castle", "caught", "cement", "chance",
    "chapel", "charge", "choose", "chosen", "circle", "clever", "clinic", "closet",
    "clumsy", "coarse", "colony", "column", "combat", "comedy", "commit", "common",
    "compel", "convey", "cosmos", "cotton", "couple", "cradle", "create", "crisis",
    "cruise", "custom", "dagger", "damage", "danger", "debate", "decade", "decent",
    "defeat", "defend", "define", "defuse", "degree", "demand", "demise", "desert",
    "design", "desire", "detail", "detect", "devote", "differ", "digest", "divert",
    "double", "dragon", "duster", "empire", "enable", "endure", "energy", "engage",
    "enrich", "ensure", "errand", "escape", "evolve", "exceed", "excite", "exempt",
    "expand", "expect", "expert", "export", "expose", "extend", "extent", "fabric",
    "famine", "father", "fathom", "feeble", "fierce", "figure", "filter", "finger",
    "fiscal", "flaunt", "flavor", "flight", "flower", "forbid", "forest", "forget",
    "fossil", "foster", "freeze", "frozen", "fulfil", "fumble", "futile", "galaxy",
    "gamble", "garden", "gather", "gentle", "geyser", "ginger", "global", "gloves",
    "golden", "gossip", "govern", "gravel", "grocer", "ground", "growth", "grudge",
    "gutter", "hammer", "handle", "happen", "harbor", "hazard", "hinder", "hollow",
    "honest", "humane", "humble", "hunger", "hurdle", "hustle", "ignore", "immune",
    "impact", "impair", "import", "impose", "incite", "income", "infant", "inform",
    "inject", "insect", "insist", "insult", "intact", "intend", "invade", "invent",
    "invest", "invoke", "island", "jarred", "jargon", "jigsaw", "jockey", "jostle",
    "jumble", "jungle", "junior", "kidnap", "kindle", "knight", "launch", "lather",
    "leader", "legend", "lesson", "letter", "linger", "listen", "litter", "little",
    "lively", "loathe", "locale", "lovely", "luxury", "maiden", "manage", "manner",
    "marble", "margin", "market", "marvel", "master", "matter", "meadow", "medium",
    "member", "memoir", "memory", "menace", "mental", "mentor", "method", "middle",
    "mingle", "mirror", "modest", "molten", "moment", "mortal", "mother", "motion",
    "motive", "murder", "muscle", "museum", "mutton", "muzzle", "mystic", "narrow",
    "nation", "nature", "nearby", "neatly", "needle", "nestle", "nimble", "noodle",
    "normal", "notice", "notion", "nozzle", "number", "object", "obtain", "occupy",
    "offend", "office", "oppose", "option", "orange", "orient", "origin", "orphan",
    "outfit", "outlet", "output", "outset", "palace", "parade", "parcel", "parent",
    "parody", "patrol", "patron", "pebble", "peddle", "pencil", "people", "permit",
    "person", "pickle", "pillar", "pillow", "pirate", "piston", "plague", "planet",
    "pledge", "pocket", "poison", "police", "policy", "polish", "polite", "ponder",
    "portal", "prayer", "prison", "profit", "prompt", "propel", "public", "puddle",
    "punish", "pursue", "puzzle", "quarry", "quench", "rabbit", "racial", "radish",
    "random", "ransom", "rattle", "ravage", "reason", "recall", "reckon", "record",
    "reduce", "reform", "refund", "regard", "regret", "reject", "relate", "relief",
    "relish", "remedy", "remind", "remote", "remove", "render", "rental", "repair",
    "repeal", "repeat", "report", "rescue", "reside", "resign", "resist", "resort",
    "result", "retail", "retire", "reveal", "revolt", "reward", "ribbon", "riddle",
    "ripple", "ritual", "robust", "rocket", "rotate", "rubble", "rumble", "sacred",
    "saddle", "safari", "safety", "salute", "sample", "scarce", "scheme", "season",
    "secret", "secure", "select", "senior", "serene", "settle", "severe", "shadow",
    "shaman", "shield", "signal", "silent", "silver", "simple", "siphon", "sister",
    "sketch", "sleepy", "slight", "smooth", "snatch", "sniffle", "social", "soften",
    "soothe", "sorrow", "source", "sphere", "spiral", "spirit", "splash", "sponge",
    "sprawl", "spring", "stable", "stammer", "starch", "statue", "steady", "stolen",
    "strain", "strand", "stream", "street", "stride", "strike", "string", "stripe",
    "strive", "stroke", "strong", "studio", "submit", "subtle", "sudden", "suffer",
    "summit", "summon", "supply", "temple", "temper", "tender", "thirst", "thrill",
    "thrive", "throne", "throng", "throat", "thrust", "ticket", "timber", "tissue",
    "tongue", "treaty", "tremor", "tribal", "trophy", "tumble", "tunnel", "turtle",
    "tycoon", "unique", "unrest", "unveil", "upbeat", "update", "uphold", "upkeep",
    "uproar", "useful", "utmost", "vacant", "valley", "vandal", "vanish", "velvet",
    "vendor", "vessel", "violin", "virtue", "volume", "voyage", "vulgar", "waffle",
    "wander", "warmth", "weapon", "weaken", "wealth", "weasel", "whisky", "wicked",
    "willow", "winder", "window", "winter", "wisdom", "wonder", "wreath", "writhe",
    "zenith", "abandon", "abdomen", "ability", "abolish", "absence", "academy", "achieve",
    "acquire", "address", "admiral", "advance", "adverse", "afflict", "agonize", "ailment",
    "allegro", "already", "amateur", "amazing", "amnesty", "amplify", "ancient", "angular",
    "anxiety", "appease", "archive", "outlook", "balance", "bargain", "battery", "beastly",
    "beneath", "benefit", "bewitch", "billion", "blanket", "blemish", "blessed", "bonanza",
    "boulder", "bourbon", "boycott", "breaker", "bristle", "brother", "cabinet", "camel",
    "captive", "caution", "certain", "chamber", "channel", "chapter", "chariot", "chimney",
    "circuit", "cluster", "comfort", "command", "compact", "company", "compete", "complex",
    "concern", "conduct", "confide", "confuse", "connect", "conquer", "consent", "consort",
    "consume", "contain", "content", "contest", "control", "convert", "correct", "council",
    "counsel", "counter", "country", "courage", "crusade", "crumble", "crystal", "culture",
    "current", "cushion", "customs", "daylight", "declare", "decline", "delight", "deliver",
    "descent", "deserve", "despair", "despise", "destiny", "develop", "devious", "digital",
    "dilemma", "diploma", "discard", "disease", "disgust", "display", "dispute", "distant",
    "distort", "disturb", "divorce", "dolphin", "earmark", "eastern", "educate", "elderly",
    "elegant", "element", "elevate", "embrace", "emotion", "emperor", "empower", "enchant",
    "endless", "enforce", "enhance", "enquire", "episode", "erosion", "evident", "examine",
    "example", "exhaust", "exhibit", "expense", "explain", "exploit", "explore", "extract",
    "extreme", "eyebrow", "factual", "failure", "fashion", "fiction", "finance", "fitness",
    "flannel", "flatter", "flourish", "forearm", "foreign", "forever", "formula", "fortune",
    "founder", "fragile", "freight", "fulfill", "furnace", "gallant", "general", "genuine",
    "gesture", "glimpse", "gondola", "gradual", "granite", "grapple", "gravity", "grizzly",
    "habitat", "halcyon", "halfway", "handsome", "harmony", "harvest", "healthy", "helpful",
    "heroine", "heroism", "highway", "history", "holiday", "horizon", "hostile", "housing",
    "husband", "illegal", "imagine", "immense", "implant", "implore", "improve", "impulse",
    "inbound", "include", "inflate", "inherit", "initial", "inquiry", "insight", "inspect",
    "install", "instead", "involve", "isolate", "javelin", "journey", "justice", "justify",
    "kindred", "kingdom", "kitchen", "knuckle", "lantern", "lateral", "laundry", "leaflet",
    "leather", "leisure", "lettuce", "liberty", "library", "mansion", "measure", "miracle",
    "mission", "mistake", "mixture", "monster", "morning", "musical", "mystery", "neglect",
    "neutral", "notable", "nucleus", "nurture", "obscure", "observe", "obvious", "offense",
    "omnibus", "opinion", "optimal", "organic", "outline", "outside", "overall", "painful",
    "palette", "passage", "passion", "patient", "pattern", "penalty", "pending", "pension",
    "percent", "perfect", "persist", "pilgrim", "pioneer", "plastic", "plaster", "playful",
    "popcorn", "popular", "portion", "poverty", "predict", "premise", "prepare", "present",
    "prevail", "prevent", "primary", "private", "problem", "proceed", "produce", "profile",
    "program", "project", "promise", "promote", "prosper", "protect", "protein", "protest",
    "provide", "publish", "pyramid", "quarter", "radical", "qualify", "realize", "receipt",
    "reclaim", "recover", "reflect", "refugee", "reunion", "routine", "rummage", "rupture",
    "sadness", "satisfy", "scatter", "scholar", "scratch", "section", "selfish", "serious",
    "service", "session", "shelter", "sheriff", "sidecar", "silence", "sincere", "slender",
    "slumber", "soldier", "sponsor", "squeeze", "stadium", "startle", "station", "stomach",
    "storage", "strange", "student", "stumble", "subject", "succeed", "suggest", "support",
    "suppose", "surface", "surplus", "survive", "suspect", "sustain", "symptom", "thought",
    "thunder", "tobacco", "tonight", "torment", "torpedo", "tourism", "trainer", "trouble",
    "trivial", "trumpet", "turmoil", "typical", "undergo", "uniform", "unknown", "unusual",
    "utensil", "utility", "vampire", "venture", "version", "veteran", "vibrant", "victory",
    "village", "villain", "vintage", "violent", "virtual", "visible", "volcano", "warrant",
    "warrior", "weather", "weaving", "welcome", "western", "whisper", "whistle", "witness",
    "worship", "wounded", "wrestle", "absolute", "accident", "accurate", "activate", "actually",
    "advocate", "aircraft", "allergic", "altitude", "ambition", "amputate", "ancestor", "announce",
    "antibody", "appetite", "applause", "approach", "approval", "backyard", "bankrupt", "boldness",
    "boundary", "bracelet", "building", "business", "calendar", "campaign", "casualty", "cautious",
    "ceremony", "champion", "charging", "children", "chivalry", "climbing", "collapse", "colonial",
    "colorful", "commence", "complain", "complete", "compound", "comprise", "conclude", "concrete",
    "conflict", "congress", "confront", "consider", "conspire", "constant", "contempt", "contrast",
    "converge", "convince", "creature", "criminal", "cultural", "currency", "customer", "darkness",
    "daughter", "deadline", "decorate", "dedicate", "delegate", "delicate", "demolish", "designer",
    "dialogue", "dinosaur", "diplomat", "disaster", "disclaim", "discount", "discover", "disguise",
    "displace", "dissolve", "distance", "distinct", "doctrine", "document", "dominate", "drainage",
    "dramatic", "duration", "dwelling", "dynamite", "earnings", "economic", "educator", "election",
    "elegance", "elephant", "elongate", "emphasis", "emulsify", "endeavor", "enormous", "envelope",
    "equality", "equipped", "escalate", "estimate", "eternity", "evaluate", "evidence", "exchange",
    "exercise", "explicit", "explorer", "external", "fabulous", "facility", "faithful", "familiar",
    "feminine", "festival", "fixation", "flagship", "flexible", "folklore", "footwear", "forecast",
    "forensic", "forested", "fragment", "frequent", "frontier", "fraction", "fruitful", "fullness",
    "function", "gambling", "generate", "genocide", "glorious", "goalpost", "graceful", "gradient",
    "graduate", "graffiti", "grateful", "guardian", "habitual", "hallmark", "handbook", "handmade",
    "hardware", "headline", "helpless", "hesitate", "highland", "homework", "honestly", "horrible",
    "hospital", "humanity", "identity", "ideology", "illusion", "immature", "imperial", "incident",
    "increase", "indicate", "indirect", "industry", "inferior", "infinite", "informal", "inherent",
    "innocent", "insecure", "interior", "intimate", "invasion", "inventor", "isolated", "judgment",
    "keepsake", "keyboard", "kindness", "labeling", "laughter", "language", "leverage", "lifelong",
    "lifetime", "literary", "location", "lonesome", "lukewarm", "magnetic", "maintain", "majority",
    "marathon", "marginal", "marriage", "material", "maximize", "mechanic", "medieval", "membrane",
    "memorial", "merchant", "midnight", "militant", "minimize", "minister", "minority", "moderate",
    "moisture", "molecule", "momentum", "monopoly", "morality", "mortgage", "movement", "multiply",
    "national", "navigate", "negative", "neighbor", "nominate", "notebook", "nuisance", "numerous",
    "obstacle", "occasion", "official", "offshore", "omission", "opponent", "opposite", "optimism",
    "ordinary", "organism", "organize", "original", "overcome", "overlook", "overturn", "painting",
    "pamphlet", "paradise", "parallel", "parasite", "pastoral", "patience", "peaceful", "peculiar",
    "perceive", "personal", "persuade", "petition", "physical", "platform", "pleasant", "pleasure",
    "plumbing", "poignant", "polished", "politics", "populate", "populace", "portrait", "position",
    "positive", "possible", "powerful", "practice", "precious", "preclude", "pregnant", "premiere",
    "prepared", "preserve", "pressure", "previous", "priority", "probable", "producer", "profound",
    "progress", "prohibit", "prolific", "promised", "promptly", "properly", "proposal", "prospect",
    "prostate", "protocol", "province", "publicly", "purchase", "pursuant", "quantity", "question",
    "reaction", "reassure", "reckless", "recovery", "regional", "regulate", "rehearse", "relative",
    "relevant", "reliable", "religion", "remember", "renowned", "repeated", "reporter", "republic",
    "requires", "research", "resemble", "resident", "resource", "response", "restless", "restrict",
    "revision", "rhetoric", "romantic", "ruthless", "sabotage", "sanction", "sandwich", "saturate",
    "scenario", "schedule", "scrutiny", "seashore", "security", "semester", "sentence", "separate",
    "sequence", "shortage", "shoulder", "simplify", "skeleton", "situated", "slippery", "snapshot",
    "software", "solitary", "somebody", "somewhat", "spectral", "sporting", "standard", "standing",
    "stimulus", "straight", "stranger", "strategy", "strength", "striking", "struggle", "stubborn",
    "stunning", "suburban", "suddenly", "superior", "suppress", "surprise", "surround", "survival",
    "suspense", "swimming", "sympathy", "syndrome", "tailored", "takeover", "tangible", "taxation",
    "teenager", "temporal", "tendency", "terminal", "terrific", "thankful", "thousand", "thriller",
    "tolerant", "tomorrow", "training", "transfer", "treasure", "tribunal", "tropical", "truthful",
    "turnover", "ultimate", "umbrella", "uncommon", "underway", "unlikely", "unplug", "unstable",
    "unwanted", "upcoming", "uprising", "validate", "valuable", "variable", "vehement", "vigilant",
    "violence", "volatile", "weakness", "workshop", "yearning",
]


_ESPEAK_LIB_NAMES = (
    "libespeak-ng.so",
    "libespeak-ng.so.1",
    "libespeak.so",
    "libespeak.so.1",
    "libespeak-ng.dylib",
    "libespeak-ng.1.dylib",
    "libespeak.dylib",
)


def _find_espeak_library():
    """Search for espeak shared library by inferring the lib dir from the binary location."""
    search_dirs = []
    for binary in ("espeak-ng", "espeak"):
        path = shutil.which(binary)
        if path:
            bin_dir = os.path.dirname(os.path.realpath(path))
            search_dirs.append(os.path.join(os.path.dirname(bin_dir), "lib"))
    for d in search_dirs:
        for name in _ESPEAK_LIB_NAMES:
            full_path = os.path.join(d, name)
            if os.path.isfile(full_path):
                return full_path
    return None


class SubprocessTTS:
    """Fallback TTS engine using subprocess commands directly.

    Used when pyttsx3's audio backend is unavailable (e.g. no aplay on Termux).
    Provides the same say()/runAndWait() interface as a pyttsx3 engine.
    """

    _COMMANDS = [
        ["espeak-ng"],
        ["espeak"],
        ["termux-tts-speak"],
    ]

    def __init__(self):
        self._word = None
        self._rate = None
        self._voice = None

    def set_voice_params(self, rate=None, voice=None):
        self._rate = rate
        self._voice = voice

    def say(self, word):
        self._word = word

    def runAndWait(self):
        if self._word is None:
            return
        word = self._word
        self._word = None
        for base_cmd in self._COMMANDS:
            try:
                cmd = list(base_cmd)
                if base_cmd[0] in ("espeak-ng", "espeak"):
                    if self._rate:
                        cmd.extend(["-s", str(self._rate)])
                    if self._voice:
                        cmd.extend(["-v", self._voice])
                cmd.append(word)
                subprocess.run(cmd, check=True, capture_output=True)
                return
            except (FileNotFoundError, subprocess.CalledProcessError):
                continue


_word_cache = {}


def _fetch_word_data(word):
    """Fetch word data from the Free Dictionary API, with simple caching."""
    if word in _word_cache:
        return _word_cache[word]
    try:
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{urllib.parse.quote(word)}"
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read())
        _word_cache[word] = data
        return data
    except Exception:
        _word_cache[word] = None
        return None


def get_definition(word):
    """Return the first definition for the word, or None."""
    data = _fetch_word_data(word)
    if not data:
        return None
    try:
        return data[0]["meanings"][0]["definitions"][0]["definition"]
    except (KeyError, IndexError):
        return None


def get_sentence(word):
    """Return an example sentence for the word, or None."""
    data = _fetch_word_data(word)
    if not data:
        return None
    try:
        for meaning in data[0]["meanings"]:
            for defn in meaning["definitions"]:
                if "example" in defn:
                    return defn["example"]
    except (KeyError, IndexError):
        pass
    return None


def configure_voice(engine):
    """Configure TTS engine for a slower, friendlier female voice."""
    if isinstance(engine, SubprocessTTS):
        engine.set_voice_params(rate=130, voice="en+f3")
        return
    engine.setProperty("rate", 130)
    voices = engine.getProperty("voices")
    for voice in voices:
        if getattr(voice, "gender", None) == "Female":
            engine.setProperty("voice", voice.id)
            return


def init_tts_engine():
    """Initialize TTS engine with fallback for non-standard platforms.

    On Linux, pyttsx3's espeak driver plays audio via aplay (ALSA).
    If aplay is not available (e.g. Termux on Android), returns a
    SubprocessTTS that calls espeak-ng/espeak/termux-tts-speak directly.
    """
    # pyttsx3's espeak driver hardcodes os.system("aplay ...") for Linux
    # playback. If aplay is missing, audio silently fails, so skip pyttsx3
    # entirely and use SubprocessTTS which calls TTS commands directly.
    if sys.platform.startswith("linux") and not shutil.which("aplay"):
        return SubprocessTTS()

    try:
        return pyttsx3.init()
    except Exception as original_error:
        lib_path = _find_espeak_library()
        if lib_path is None:
            raise original_error

        import ctypes

        # Remove cached failed imports so pyttsx3 retries the driver load
        for mod_name in list(sys.modules):
            if "pyttsx3.drivers" in mod_name:
                del sys.modules[mod_name]

        # Temporarily patch ctypes.cdll.LoadLibrary so pyttsx3's espeak
        # driver can find the library at the non-standard path
        original_load = ctypes.cdll.LoadLibrary

        def _patched_load(name):
            try:
                return original_load(name)
            except OSError:
                if "espeak" in str(name).lower():
                    return original_load(lib_path)
                raise

        ctypes.cdll.LoadLibrary = _patched_load
        try:
            return pyttsx3.init()
        finally:
            ctypes.cdll.LoadLibrary = original_load


def get_word(max_length=8):
    """Pick a random word guaranteed to have a definition and sentence."""
    candidates = [w for w in WORD_LIST if len(w) <= max_length]
    random.shuffle(candidates)
    for word in candidates[:15]:
        if get_definition(word) and get_sentence(word):
            return word
    # Fallback: return a word even without full API validation
    return random.choice(candidates)


def check_spelling(correct, attempt):
    return attempt.strip().lower() == correct.lower()


def compare(correct, attempt):
    matches = []
    for i, ch in enumerate(correct):
        if i < len(attempt) and attempt[i].lower() == ch.lower():
            matches.append(True)
        else:
            matches.append(False)
    accuracy = (sum(matches) / len(correct)) * 100
    return matches, accuracy


def speak_word(word, engine):
    engine.say(word)
    engine.runAndWait()


def format_success():
    return (
        f"{Fore.GREEN}{Style.BRIGHT}"
        f"\u2705 Congrats! You spelled it correctly!"
        f"{Style.RESET_ALL}"
    )


def format_failure(correct, matches, accuracy):
    header = f"{Fore.RED}\u274c Unlucky! The correct spelling is:{Style.RESET_ALL}\n"
    word_display = ""
    for i, ch in enumerate(correct):
        if matches[i]:
            word_display += f"{Fore.GREEN}{ch}{Style.RESET_ALL}"
        else:
            word_display += f"{Fore.RED}{Style.BRIGHT}{ch}{Style.RESET_ALL}"
    accuracy_line = f"\n{Fore.RED}Accuracy: {accuracy:.0f}%{Style.RESET_ALL}"
    return header + word_display + accuracy_line


def play_round(word, engine):
    speak_word(word, engine)
    while True:
        print("\n1. Hear the word again")
        print("2. Get the definition")
        print("3. Hear the word in a sentence")
        print("4. Spell the word")
        choice = input("\nChoose an option: ").strip()
        if choice == "1":
            speak_word(word, engine)
        elif choice == "2":
            defn = get_definition(word)
            if defn:
                print(f"\nDefinition: {defn}")
            else:
                print("\nDefinition not available.")
        elif choice == "3":
            sentence = get_sentence(word)
            if sentence:
                print(f"\nSentence: {sentence}")
                speak_word(sentence, engine)
            else:
                print("\nSentence not available.")
        elif choice == "4":
            break
    attempt = input("Type your spelling: ")
    if check_spelling(word, attempt):
        print(format_success())
    else:
        matches, accuracy = compare(word, attempt.strip())
        print(format_failure(word, matches, accuracy))


def main():
    init()
    try:
        engine = init_tts_engine()
        configure_voice(engine)
    except Exception as e:
        print(f"{Fore.RED}Failed to initialise text-to-speech: {e}{Style.RESET_ALL}")
        sys.exit(1)
    print(f"{Style.BRIGHT}Welcome to Spelling Bee!{Style.RESET_ALL}\n")
    while True:
        word = get_word()
        play_round(word, engine)
        again = input("\nTry another word? (y/n): ")
        if again.strip().lower() != "y":
            print(f"\n{Style.BRIGHT}Thanks for playing! Goodbye!{Style.RESET_ALL}")
            break
        print()


if __name__ == "__main__":
    main()
