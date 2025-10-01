import discord
from discord.ext import commands
import os
import logging
from pydantic import BaseModel
from enum import Enum
from PIL import Image

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# Invocation definitions
class Type(Enum):
    ATTEMPT = "ATTEMPT"
    TIME_LIMIT = "TIME_LIMIT"
    HELPFUL_SPIRIT = "HELPFUL_SPIRIT"
    PATH_LEVEL = "PATH_LEVEL"

class InvocationInfo(BaseModel):
    x: int
    y: int
    points: int
    name: str
    type: Type | None = None

# All invocation instances
TRY_AGAIN = InvocationInfo(x=0, y=0, points=5, name="Try again", type=Type.ATTEMPT)
PERSISTENCE = InvocationInfo(x=1, y=0, points=10, name="Persistence", type=Type.ATTEMPT)
SOFTCORE_RUN = InvocationInfo(x=2, y=0, points=15, name="Softcore run", type=Type.ATTEMPT)
HARDCORE_RUN = InvocationInfo(x=3, y=0, points=25, name="Hardcore run", type=Type.ATTEMPT)
WALK_FOR_IT = InvocationInfo(x=0, y=1, points=10, name="Walk for it", type=Type.TIME_LIMIT)
JOG_FOR_IT = InvocationInfo(x=1, y=1, points=15, name="Jog for it", type=Type.TIME_LIMIT)
RUN_FOR_IT = InvocationInfo(x=2, y=1, points=20, name="Run for it", type=Type.TIME_LIMIT)
SPRINT_FOR_IT = InvocationInfo(x=3, y=1, points=25, name="Sprint for it", type=Type.TIME_LIMIT)
NEED_SOME_HELP = InvocationInfo(x=0, y=2, points=15, name="Need some help", type=Type.HELPFUL_SPIRIT)
NEED_LESS_HELP = InvocationInfo(x=1, y=2, points=25, name="Need less help", type=Type.HELPFUL_SPIRIT)
NO_HELP_NEEDED = InvocationInfo(x=2, y=2, points=40, name="No help needed", type=Type.HELPFUL_SPIRIT)
WALK_THE_PATH = InvocationInfo(x=3, y=2, points=50, name="Walk the path")
PATHSEEKER = InvocationInfo(x=0, y=3, points=15, name="Pathseeker", type=Type.PATH_LEVEL)
PATHFINDER = InvocationInfo(x=1, y=3, points=40, name="Pathfinder", type=Type.PATH_LEVEL)
PATHMASTER = InvocationInfo(x=2, y=3, points=50, name="Pathmaster", type=Type.PATH_LEVEL)
QUIET_PRAYERS = InvocationInfo(x=3, y=3, points=20, name="Quiet prayers")
DEADLY_PRAYERS = InvocationInfo(x=0, y=4, points=20, name="Deadly prayers")
ON_A_DIET = InvocationInfo(x=1, y=4, points=15, name="On a diet")
DEHYDRATION = InvocationInfo(x=2, y=4, points=30, name="Dehydration")
OVERLY_DRAINING = InvocationInfo(x=3, y=4, points=15, name="Overly draining")
LIVELY_LARVAE = InvocationInfo(x=0, y=5, points=5, name="Lively larvae")
BLOWING_MUD = InvocationInfo(x=1, y=5, points=10, name="Blowing mud")
MORE_OVERLORDS = InvocationInfo(x=2, y=5, points=15, name="More overlords")
MEDIC = InvocationInfo(x=3, y=5, points=15, name="Medic")
AERIAL_ASSAULT = InvocationInfo(x=0, y=6, points=10, name="Aerial assault")
NOT_JUST_A_HEAD = InvocationInfo(x=1, y=6, points=15, name="Not just a head")
ARTERIAL_SPRAY = InvocationInfo(x=2, y=6, points=10, name="Arterial spray")
BLOOD_THINNERS = InvocationInfo(x=3, y=6, points=5, name="Blood thinners")
UPSET_STOMACH = InvocationInfo(x=0, y=7, points=15, name="Upset stomach")
DOUBLE_TROUBLE = InvocationInfo(x=1, y=7, points=20, name="Double trouble")
KEEP_BACK = InvocationInfo(x=2, y=7, points=10, name="Keep back")
STAY_VIGILANT = InvocationInfo(x=3, y=7, points=15, name="Stay vigilant")
FEELING_SPECIAL = InvocationInfo(x=0, y=8, points=20, name="Feeling special")
MIND_THE_GAP = InvocationInfo(x=1, y=8, points=10, name="Mind the gap")
GOTTA_HAVE_FAITH = InvocationInfo(x=2, y=8, points=10, name="Gotta have faith")
JUNGLE_JAPES = InvocationInfo(x=3, y=8, points=5, name="Jungle japes")
SHAKING_THINGS_UP = InvocationInfo(x=0, y=9, points=10, name="Shaking things up")
BOULDERDASH = InvocationInfo(x=1, y=9, points=10, name="Boulderdash")
ANCIENT_HASTE = InvocationInfo(x=2, y=9, points=10, name="Ancient haste")
ACCELERATION = InvocationInfo(x=3, y=9, points=10, name="Acceleration")
PENETRATION = InvocationInfo(x=0, y=10, points=10, name="Penetration")
OVERCLOCKED = InvocationInfo(x=1, y=10, points=10, name="Overclocked")
OVERCLOCKED_2 = InvocationInfo(x=2, y=10, points=10, name="Overclocked 2")
INSANITY = InvocationInfo(x=3, y=10, points=50, name="Insanity")

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
    result = []

    def dfs(index: int, current_combo: list[InvocationInfo], current_total: int):
        if current_total == target_level:
            nonlocal result
            result = current_combo[:]
            return True  # Found a valid combo, stop searching
        if current_total > target_level or index >= len(PROGRESSION):
            return False

        # Try including current invocation
        if dfs(index + 1, current_combo + [PROGRESSION[index]], current_total + PROGRESSION[index].points):
            return True
        # Try skipping current invocation
        if dfs(index + 1, current_combo, current_total):
            return True
        return False

    dfs(0, [], 0)
    return result

def generate_image(filename: str, invos: list[InvocationInfo]) -> None:
    base = Image.open('images/invo_off.png').convert("RGBA")
    highlighted = Image.open('images/invo_on.png').convert("RGBA")
    box_width = base.width / 4
    box_height = base.height / 11
    frame = base.copy()
    for invo in invos:
        box = (
            int(invo.x * box_width),
            int(invo.y * box_height),
            int((invo.x + 1) * box_width),
            int((invo.y + 1) * box_height),
        )
        icon = highlighted.crop(box)
        position = (int(invo.x * box_width), int(invo.y * box_height))
        frame.paste(icon, position)
    frame.save(filename)


class Invo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="invo", description="Show ToA Invocation")
    async def invo(self, interaction: discord.Interaction, level: int):
        desired_level = int(5 * (level / 5))
        file = f"images/invo_{desired_level}.png"
        if not os.path.exists(file):
            invocations = pick_best_invocations(desired_level)
            for invo in invocations:
                print(f" - {invo.name} ({invo.points})")
            generate_image(file, invocations)
        await interaction.response.send_message(f"Raid level {desired_level}", file=discord.File(file))

async def setup(bot):
    await bot.add_cog(Invo(bot))
