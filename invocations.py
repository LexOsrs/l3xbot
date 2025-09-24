from pydantic import BaseModel
from enum import Enum

# Unused right now
class Type(Enum):
    ATTEMPT = "ATTEMPT"
    TIME_LIMIT = "TIME_LIMIT"
    HELPFUL_SPIRIT = "HELPFUL_SPIRIT"
    PATH_LEVEL = "PATH_LEVEL"

class InvocationInfo(BaseModel):
    x: int
    y: int
    points: int
    type: Type | None = None

# Attempts
TRY_AGAIN = InvocationInfo(x=0, y=0, points=5, type=Type.ATTEMPT)
PERSISTENCE = InvocationInfo(x=1, y=0, points=10, type=Type.ATTEMPT)
SOFTCORE_RUN = InvocationInfo(x=2, y=0, points=15, type=Type.ATTEMPT)
HARDCORE_RUN = InvocationInfo(x=3, y=0, points=25, type=Type.ATTEMPT)

# Time Limit
WALK_FOR_IT = InvocationInfo(x=0, y=1, points=10, type=Type.TIME_LIMIT)
JOG_FOR_IT = InvocationInfo(x=1, y=1, points=15, type=Type.TIME_LIMIT)
RUN_FOR_IT = InvocationInfo(x=2, y=1, points=20, type=Type.TIME_LIMIT)
SPRINT_FOR_IT = InvocationInfo(x=3, y=1, points=25, type=Type.TIME_LIMIT)

# Helpful Spirit
NEED_SOME_HELP = InvocationInfo(x=0, y=2, points=15, type=Type.HELPFUL_SPIRIT)
NEED_LESS_HELP = InvocationInfo(x=1, y=2, points=25, type=Type.HELPFUL_SPIRIT)
NO_HELP_NEEDED = InvocationInfo(x=2, y=2, points=40, type=Type.HELPFUL_SPIRIT)

# Paths
WALK_THE_PATH = InvocationInfo(x=3, y=2, points=50)

# Path Level
PATHSEEKER = InvocationInfo(x=0, y=3, points=15, type=Type.PATH_LEVEL)
PATHFINDER = InvocationInfo(x=1, y=3, points=40, type=Type.PATH_LEVEL)
PATHMASTER = InvocationInfo(x=2, y=3, points=50, type=Type.PATH_LEVEL)

# Prayer
QUIET_PRAYERS = InvocationInfo(x=3, y=3, points=20)
DEADLY_PRAYERS = InvocationInfo(x=0, y=4, points=20)

# Restoration
ON_A_DIET = InvocationInfo(x=1, y=4, points=15)
DEHYDRATION = InvocationInfo(x=2, y=4, points=30)
OVERLY_DRAINING = InvocationInfo(x=3, y=4, points=15)

# Kephri
LIVELY_LARVAE = InvocationInfo(x=0, y=5, points=5)
BLOWING_MUD = InvocationInfo(x=1, y=5, points=10)
MORE_OVERLORDS = InvocationInfo(x=2, y=5, points=15)
MEDIC = InvocationInfo(x=3, y=5, points=15)
AERIAL_ASSAULT = InvocationInfo(x=0, y=6, points=10)

# Zebak
NOT_JUST_A_HEAD = InvocationInfo(x=1, y=6, points=15)
ARTERIAL_SPRAY = InvocationInfo(x=2, y=6, points=10)
BLOOD_THINNERS = InvocationInfo(x=3, y=6, points=5)
UPSET_STOMACH = InvocationInfo(x=0, y=7, points=15)

# Akkha
DOUBLE_TROUBLE = InvocationInfo(x=1, y=7, points=20)
KEEP_BACK = InvocationInfo(x=2, y=7, points=10)
STAY_VIGILANT = InvocationInfo(x=3, y=7, points=15)
FEELING_SPECIAL = InvocationInfo(x=0, y=8, points=20)

# Ba-Ba
MIND_THE_GAP = InvocationInfo(x=1, y=8, points=10)
GOTTA_HAVE_FAITH = InvocationInfo(x=2, y=8, points=10)
JUNGLE_JAPES = InvocationInfo(x=3, y=8, points=5)
SHAKING_THINGS_UP = InvocationInfo(x=0, y=9, points=10)
BOULDERDASH = InvocationInfo(x=1, y=9, points=10)

# The Wardens
ANCIENT_HASTE = InvocationInfo(x=2, y=9, points=10)
ACCELERATION = InvocationInfo(x=3, y=9, points=10)
PENETRATION = InvocationInfo(x=0, y=10, points=10)
OVERCLOCKED = InvocationInfo(x=1, y=10, points=10)
OVERCLOCKED_2 = InvocationInfo(x=2, y=10, points=10)
INSANITY = InvocationInfo(x=3, y=10, points=50)

PROGRESSION = [
    SOFTCORE_RUN,
    ON_A_DIET,
    SHAKING_THINGS_UP,
    MIND_THE_GAP,
    BLOWING_MUD,
    INSANITY,
    OVERCLOCKED,
    OVERCLOCKED_2,
    ACCELERATION,
    PENETRATION,
    JOG_FOR_IT,
    DEADLY_PRAYERS,
    UPSET_STOMACH,
    NOT_JUST_A_HEAD,
    ARTERIAL_SPRAY,
    BLOOD_THINNERS,
    FEELING_SPECIAL,
    STAY_VIGILANT,
    AERIAL_ASSAULT,
    JUNGLE_JAPES,
    GOTTA_HAVE_FAITH,
    BOULDERDASH,
    WALK_THE_PATH,
]


def pick_best_invocations(target_level: int) -> list[InvocationInfo]:
    best_combo = []
    best_total = 0

    def dfs(index: int, current_combo: list[InvocationInfo], current_total: int):
        nonlocal best_combo, best_total

        if current_total == target_level:
            best_combo = current_combo[:]
            best_total = current_total
            return  # early exit — can't do better


        if current_total > target_level:
            return  # over target, discard path

        if current_total > best_total and current_total <= target_level:
            best_combo = current_combo[:]
            best_total = current_total

        if index >= len(PROGRESSION):
            return  # end of list

        inv = PROGRESSION[index]
        if current_total + inv.points <= target_level:
            current_combo.append(inv)
            dfs(index + 1, current_combo, current_total + inv.points)
            current_combo.pop()

    dfs(0, [], 0)

    return best_combo
