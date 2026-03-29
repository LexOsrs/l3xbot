from discord.ext import commands
from discord import ui
import discord
import aiohttp
import logging
import os
import io

logger = logging.getLogger(__name__)

API_BASE = os.getenv("BINGO_API_URL", "http://localhost:5209/api/bingo")
DEFAULT_PLAYER = "Lex 26"  # Hardcoded for now — will use Discord auth later


class Bingo(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session: aiohttp.ClientSession | None = None
        # Track which messages are submissions: discord_message_id -> submission data
        self._submission_map: dict[int, dict] = {}

    async def get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def cog_unload(self):
        if self.session and not self.session.closed:
            await self.session.close()

    async def api_get(self, path: str):
        session = await self.get_session()
        async with session.get(f"{API_BASE}{path}") as resp:
            if resp.status == 200:
                return await resp.json()
            logger.error(f"API GET {path} -> {resp.status}: {await resp.text()}")
            return None

    async def api_post(self, path: str, data: dict):
        session = await self.get_session()
        async with session.post(f"{API_BASE}{path}", json=data) as resp:
            if resp.status == 200:
                return await resp.json()
            logger.error(f"API POST {path} -> {resp.status}: {await resp.text()}")
            return None

    async def api_put(self, path: str, data: dict):
        session = await self.get_session()
        async with session.put(f"{API_BASE}{path}", json=data) as resp:
            if resp.status == 200:
                return await resp.json()
            logger.error(f"API PUT {path} -> {resp.status}: {await resp.text()}")
            return None

    # --- Slash commands ---

    @discord.app_commands.command(
        name="bingo-setup",
        description="Create tile threads in each team's channel for a bingo event",
    )
    @discord.app_commands.describe(event_id="The bingo event ID")
    async def bingo_setup(self, interaction: discord.Interaction, event_id: int):
        await interaction.response.defer()

        teams = await self.api_get(f"/discord/event/{event_id}/teams")
        tiles = await self.api_get(f"/discord/event/{event_id}/tiles")
        if not teams or not tiles:
            await interaction.followup.send("Could not fetch event data. Is the event ID correct?")
            return

        teams_with_channels = [t for t in teams if t.get("discordChannelId")]
        if not teams_with_channels:
            await interaction.followup.send(
                "No teams have Discord channels configured. "
                "Use `/bingo-channel` to assign channels first."
            )
            return

        existing = await self.api_get(f"/discord/event/{event_id}/teamtiles") or []
        existing_threads = {(tt["teamId"], tt["tileId"]): tt for tt in existing if tt.get("discordThreadId")}

        created = 0
        skipped = 0
        for team in teams_with_channels:
            channel = self.bot.get_channel(team["discordChannelId"])
            if not channel:
                continue

            for tile in tiles:
                if (team["id"], tile["id"]) in existing_threads:
                    skipped += 1
                    continue

                team_tile = next(
                    (tt for tt in existing if tt["teamId"] == team["id"] and tt["tileId"] == tile["id"]),
                    None,
                )

                if not team_tile:
                    result = await self.api_post(
                        f"/events/{event_id}/teams/{team['id']}/tiles/{tile['id']}",
                        {"status": "InProgress"},
                    )
                    if not result:
                        continue
                    existing = await self.api_get(f"/discord/event/{event_id}/teamtiles") or []
                    team_tile = next(
                        (tt for tt in existing if tt["teamId"] == team["id"] and tt["tileId"] == tile["id"]),
                        None,
                    )
                    if not team_tile:
                        continue

                thread = await channel.create_thread(
                    name=tile["title"],
                    type=discord.ChannelType.public_thread,
                )

                await self.api_put(
                    f"/discord/teamtiles/{team_tile['id']}/thread",
                    {"threadId": thread.id},
                )

                await thread.send(
                    f"**{tile['title']}** — {tile.get('points', 0)} pts\n"
                    f"Post your screenshots here. A moderator will react to approve them."
                )
                created += 1

        await interaction.followup.send(
            f"Created **{created}** threads across {len(teams_with_channels)} team channels. "
            f"{skipped} already existed."
        )

    @discord.app_commands.command(
        name="bingo-channel",
        description="Assign a Discord channel to a bingo team",
    )
    @discord.app_commands.describe(team_id="The team ID", channel="The team's channel")
    async def bingo_channel(self, interaction: discord.Interaction, team_id: int, channel: discord.TextChannel):
        result = await self.api_put(
            f"/discord/teams/{team_id}/channel",
            {"channelId": channel.id},
        )
        if result:
            await interaction.response.send_message(f"Linked **{result.get('name', 'team')}** to {channel.mention}")
        else:
            await interaction.response.send_message("Failed to link team to channel.")

    @discord.app_commands.command(
        name="bingo-teams",
        description="List teams for a bingo event",
    )
    @discord.app_commands.describe(event_id="The bingo event ID")
    async def bingo_teams(self, interaction: discord.Interaction, event_id: int):
        teams = await self.api_get(f"/discord/event/{event_id}/teams")
        if not teams:
            await interaction.response.send_message("Could not fetch teams.")
            return

        lines = []
        for t in teams:
            ch = f"<#{t['discordChannelId']}>" if t.get("discordChannelId") else "No channel"
            lines.append(f"**{t['name']}** (ID: {t['id']}) — {ch}")

        await interaction.response.send_message("\n".join(lines) or "No teams found.")

    @discord.app_commands.command(
        name="bingo-board",
        description="Show your team's bingo board (run in your team channel)",
    )
    async def bingo_board(self, interaction: discord.Interaction):
        await interaction.response.defer()

        # Figure out the channel — could be in a thread or the team channel itself
        channel_id = interaction.channel.parent_id if isinstance(interaction.channel, discord.Thread) else interaction.channel_id

        # Look up which team owns this channel
        team_data = await self.api_get(f"/discord/team-by-channel/{channel_id}")
        if not team_data:
            await interaction.followup.send("This doesn't seem to be a bingo team channel.")
            return

        event_id = team_data['eventId']
        team_id = team_data['id']

        # Fetch board data for the summary text
        data = await self.api_get(f"/discord/board/{event_id}/{team_id}")

        # Fetch the board image from the site
        session = await self.get_session()
        async with session.get(f"{API_BASE}/board-image/{event_id}/{team_id}") as resp:
            if resp.status != 200:
                await interaction.followup.send("Could not generate board image.")
                return
            image_data = await resp.read()

        buf = io.BytesIO(image_data)
        buf.seek(0)

        summary = ""
        if data:
            summary = f"**{data['title']}** — {data['teamName']}\n"
            summary += f"{data['completedTiles']}/{data['totalTiles']} tiles"
            if data.get("lines", 0) > 0:
                summary += f" · {data['lines']} lines"
            summary += f" · **{data['totalPoints']} pts**"

        await interaction.followup.send(
            summary,
            file=discord.File(buf, filename="bingo-board.png"),
        )

    # --- Auto-detect screenshots in tile threads ---

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.attachments:
            return
        if not isinstance(message.channel, discord.Thread):
            return

        images = [a for a in message.attachments if a.content_type and a.content_type.startswith("image/")]
        if not images:
            return

        image_url = images[0].url
        caption = message.content if message.content else None
        is_start = caption and any(w in caption.lower() for w in ["start", "starting", "before"])

        result = await self.api_post("/discord/submit", {
            "threadId": message.channel.id,
            "messageId": message.id,
            "playerName": DEFAULT_PLAYER,
            "imageUrl": image_url,
            "caption": caption,
            "isStart": is_start or False,
        })

        if not result:
            return  # Not a bingo thread

        submission_id = result.get("id")
        tile_title = result.get("tileTitle", "Unknown")

        # Store submission info for reaction handling
        self._submission_map[message.id] = {
            "submission_id": submission_id,
            "tile_title": tile_title,
            "is_start": is_start or False,
        }

        await message.add_reaction("📸")

    # --- Moderator reactions on screenshots ---

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        # Ignore bot reactions
        if payload.user_id == self.bot.user.id:
            return

        # TODO: Check if the reacting user has a moderator role (e.g. BINGO_MOD_ROLE_ID env var)
        # For now, anyone can approve/deny. Should restrict to mods only.

        emoji = str(payload.emoji)
        if emoji not in ("✅", "❌"):
            return

        # Look up submission by Discord message ID — survives bot restarts
        sub_data = await self.api_get(f"/discord/submission/by-message/{payload.message_id}")
        if not sub_data:
            return  # Not a tracked submission

        submission_id = sub_data["id"]
        is_start = sub_data.get("type") == "Start"
        status = sub_data.get("status")

        # Don't re-process already reviewed submissions
        if status != "Pending":
            return

        user = self.bot.get_user(payload.user_id)
        reviewer = user.display_name if user else "Moderator"
        channel = self.bot.get_channel(payload.channel_id)

        if emoji == "❌":
            result = await self.api_put(f"/discord/submission/{submission_id}/review", {
                "status": "Denied",
                "reviewedBy": reviewer,
            })
            if result and channel:
                try:
                    msg = await channel.fetch_message(payload.message_id)
                    await msg.reply(f"❌ Denied by {reviewer}.", mention_author=False)
                except Exception:
                    pass

        elif emoji == "✅":
            if is_start:
                result = await self.api_put(f"/discord/submission/{submission_id}/review", {
                    "status": "Approved",
                    "reviewedBy": reviewer,
                })
                if result and channel:
                    try:
                        msg = await channel.fetch_message(payload.message_id)
                        await msg.reply(f"✅ Starting screenshot approved by {reviewer}.", mention_author=False)
                    except Exception:
                        pass
            else:
                labels = sub_data.get("requirementLabels", [])
                if not labels:
                    await self.api_put(f"/discord/submission/{submission_id}/review", {
                        "status": "Approved",
                        "reviewedBy": reviewer,
                    })
                    return

                if channel:
                    view = ItemAssignView(
                        cog=self,
                        submission_id=submission_id,
                        labels=labels,
                        reviewer=reviewer,
                        reviewer_id=payload.user_id,
                    )
                    try:
                        msg = await channel.fetch_message(payload.message_id)
                        await msg.reply(
                            f"✅ **{reviewer}** is approving this. What does it count for?",
                            view=view,
                            mention_author=False,
                        )
                    except Exception as e:
                        logger.error(f"Failed to send item assign view: {e}")


class ItemAssignView(ui.View):
    """Discord view with dropdowns to assign items to a submission."""

    def __init__(self, cog: Bingo, submission_id: int, labels: list[str], reviewer: str, reviewer_id: int):
        super().__init__(timeout=300)
        self.cog = cog
        self.submission_id = submission_id
        self.labels = labels
        self.reviewer = reviewer
        self.reviewer_id = reviewer_id
        self.entries: list[dict] = []

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.reviewer_id:
            await interaction.response.send_message("Only the approving moderator can use this.", ephemeral=True)
            return False
        return True

        # Add the requirement select
        options = [discord.SelectOption(label=l, value=l) for l in labels[:25]]
        self.req_select = ui.Select(
            placeholder="Select requirement...",
            options=options,
            row=0,
        )
        self.req_select.callback = self.on_select
        self.add_item(self.req_select)

    async def on_select(self, interaction: discord.Interaction):
        selected = self.req_select.values[0] if self.req_select.values else None
        if not selected:
            return

        # Show a modal asking for the amount
        modal = AmountModal(self, selected)
        await interaction.response.send_modal(modal)

    @ui.button(label="Done — Approve", style=discord.ButtonStyle.green, row=2)
    async def done_button(self, interaction: discord.Interaction, button: ui.Button):
        if not self.entries:
            await interaction.response.send_message("Add at least one item first.", ephemeral=True)
            return

        result = await self.cog.api_put(f"/discord/submission/{self.submission_id}/review", {
            "status": "Approved",
            "reviewedBy": self.reviewer,
            "entries": [{"label": e["label"], "amount": e["amount"]} for e in self.entries],
        })

        if result:
            summary = ", ".join(f"+{e['amount']} {e['label']}" for e in self.entries)
            await interaction.response.edit_message(
                content=f"✅ Approved by {self.reviewer}: {summary}",
                view=None,
            )
        else:
            await interaction.response.send_message("Failed to approve. Check the site.", ephemeral=True)

        self.stop()

    @ui.button(label="Cancel", style=discord.ButtonStyle.grey, row=2)
    async def cancel_button(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(content="Approval cancelled.", view=None)
        self.stop()

    def add_entry(self, label: str, amount: int):
        self.entries.append({"label": label, "amount": amount})


class AmountModal(ui.Modal):
    """Modal to input the amount for a requirement."""

    amount_input = ui.TextInput(
        label="Amount",
        placeholder="e.g. 1",
        default="1",
        max_length=10,
        style=discord.TextStyle.short,
    )

    def __init__(self, view: ItemAssignView, label: str):
        super().__init__(title=f"How many: {label[:40]}")
        self.parent_view = view
        self.label = label

    async def on_submit(self, interaction: discord.Interaction):
        try:
            amount = int(self.amount_input.value)
        except ValueError:
            await interaction.response.send_message("Invalid number.", ephemeral=True)
            return

        if amount < 1:
            await interaction.response.send_message("Amount must be at least 1.", ephemeral=True)
            return

        self.parent_view.add_entry(self.label, amount)

        summary = ", ".join(f"+{e['amount']} {e['label']}" for e in self.parent_view.entries)
        await interaction.response.edit_message(
            content=f"✅ **{self.parent_view.reviewer}** is approving this: **{summary}**\n"
                    f"Select another item or click **Done — Approve**.",
        )


async def setup(bot):
    await bot.add_cog(Bingo(bot))
