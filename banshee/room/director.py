"""Horror pacing plus a will of her own. She does not wait to be told."""

from __future__ import annotations

import random
from enum import Enum

from banshee.actors.ghost import Ghost, GhostState
from banshee.actors.shade import Shade, ShadeKind
from banshee.room.props import Props
from banshee.room.voice import Voice
from banshee.room.whispers import Whispers


class Act(str, Enum):
    UNEASE = "UNEASE"
    SHADOWS = "SHADOWS"
    APPEAR = "APPEAR"
    HAUNT = "HAUNT"


class Director:
    def __init__(
        self,
        props: Props,
        ghost: Ghost,
        shade: Shade,
        whispers: Whispers,
        voice: Voice,
    ) -> None:
        self.props = props
        self.ghost = ghost
        self.shade = shade
        self.whispers = whispers
        self.voice = voice
        self.act = Act.UNEASE
        self.t = 0.0
        self.act_t = 0.0
        self.interacts = 0
        self.opened_wardrobe = False
        self._fired: set[str] = set()
        self._shadow_step = 0
        self._haunt_cd = 0.4
        self._mutter_cd = 5.0

    def here(self) -> bool:
        return self.act in (Act.APPEAR, Act.HAUNT) and self.ghost.state is not GhostState.ABSENT

    def note_interact(self, kind: str, detail: str = "") -> None:
        self.interacts += 1
        if kind == "open":
            self.opened_wardrobe = True
        if self.act is Act.UNEASE and self.interacts >= 1:
            self._to(Act.SHADOWS)
        if self.here() and kind in ("open", "close", "poke", "drag", "lamp"):
            snap = detail or kind
            self.voice.ask(
                f"the human just did this in your bedroom: {snap}. "
                "one short comment. do not be helpful.",
                activity=snap,
            )

    def _fire(self, name: str) -> bool:
        if name in self._fired:
            return False
        self._fired.add(name)
        return True

    def _to(self, act: Act) -> None:
        self.act = act
        self.act_t = 0.0

    def update(self, dt: float) -> None:
        self.t += dt
        self.act_t += dt
        if self.act is Act.UNEASE:
            self._unease()
        elif self.act is Act.SHADOWS:
            self._shadows()
        elif self.act is Act.APPEAR:
            self._appear()
        elif self.act is Act.HAUNT:
            self._haunt(dt)

    def _unease(self) -> None:
        if self.act_t >= 2.2 and self._fire("w1"):
            self.whispers.set("dont close the window")
        if self.act_t >= 5.0 and self._fire("tick"):
            self.props.tap_chest()
        if self.act_t >= 6.2 and self._fire("dip"):
            self.props.flicker_lamp(0.35)
        if self.act_t >= 8.0:
            self._to(Act.SHADOWS)

    def _shadows(self) -> None:
        wr = self.props.items["wardrobe"]
        ch = self.props.items["chair"]
        if self.act_t >= 0.6 and self._shadow_step == 0 and not self.shade.alive:
            self.shade.spawn(ShadeKind.WALL_SLIDE)
            self._shadow_step = 1
        if self.act_t >= 4.2 and self._shadow_step == 1 and not self.shade.alive:
            self.shade.spawn(ShadeKind.UNDER_FURNITURE, {"x": ch.x, "y": ch.y + ch.h - 20})
            self._shadow_step = 2
        if self.act_t >= 5.0 and self._fire("w2"):
            self.whispers.set("someone is in the wardrobe")
        if self.act_t >= 7.0 and self._shadow_step == 2 and not self.shade.alive:
            self.shade.spawn(
                ShadeKind.DOOR_CRACK,
                {"x": wr.x + wr.rect.w - 36, "y": wr.y + 70},
            )
            self._shadow_step = 3
        if self.act_t >= 10.0 and self._shadow_step == 3 and not self.shade.alive:
            self.shade.spawn(ShadeKind.FALSE_GHOST, {"x": ch.x - 8, "y": ch.y + 16})
            self._shadow_step = 4
        ready = self._shadow_step >= 4 and not self.shade.alive
        skip = self.opened_wardrobe or self.interacts >= 3
        if ready and (skip or self.act_t >= 12.0):
            self._to(Act.APPEAR)

    def _appear(self) -> None:
        if self._fire("manifest"):
            self.ghost.manifest(self._random_spawn())
            self.whispers.set("")
            self.voice.ask(
                "the human looked too long. you just manifested in the bedroom. "
                "first words. 1 or 2 short sentences. you are pleased they noticed.",
                activity="ghost just appeared",
            )
        if self.ghost.state is GhostState.IDLE and self.act_t > 1.4:
            self.props.unease_rock = False
            self._to(Act.HAUNT)
            self._haunt_cd = 0.3

    def _random_spawn(self) -> tuple[float, float]:
        wr = self.props.items["wardrobe"]
        ch = self.props.items["chair"]
        chest = self.props.items["chest"]
        choices = [
            (ch.x + 20, ch.y - 40),
            (chest.x + 10, chest.y - 70),
        ]
        if wr.opened:
            choices.append((wr.x + 40, wr.y + 40))
        return random.choice(choices)

    def _random_perch(self) -> tuple[float, float]:
        px, py = random.choice(list(self.props.perches.values()))
        return (px, py)

    def _haunt(self, dt: float) -> None:
        self._haunt_cd -= dt
        self._mutter_cd -= dt
        if (
            self._mutter_cd <= 0
            and not self.voice.busy
            and self.ghost.state is not GhostState.ABSENT
        ):
            self._mutter_cd = random.uniform(7.0, 12.0)
            self.voice.ask(
                "you are haunting on your own. mutter one short line about this room "
                "or the human. do not greet. do not ask a question.",
                activity="idle haunt",
            )
        if self.ghost.busy():
            return
        if self.ghost.idle_for() > 1.15:
            self._do("drift")
            return
        if self._haunt_cd > 0:
            return
        self._haunt_cd = random.uniform(1.1, 2.0)
        action = random.choices(
            ("drift", "hide", "vanish", "scare", "knock", "flicker", "nudge", "open"),
            weights=(36, 14, 14, 10, 8, 8, 6, 4),
            k=1,
        )[0]
        self._do(action)

    def _do(self, action: str) -> None:
        if action == "drift":
            self.ghost.drift_to(self._random_perch(), random.uniform(0.55, 1.05))
        elif action == "hide":
            wr = self.props.items["wardrobe"]
            pid = "wardrobe" if wr.opened else "chest"
            self.ghost.hide_behind(pid, self.props.hide_slot(pid), self.props.peek_slot(pid))
        elif action == "vanish":
            self.ghost.vanish_to(self._random_perch())
        elif action == "scare":
            self.ghost.scare()
        elif action == "knock":
            self.props.tap_chest()
            self._haunt_cd = 0.6
        elif action == "flicker":
            self.props.flicker_lamp(0.8)
            self._haunt_cd = 0.5
        elif action == "nudge":
            self.props.nudge("chair", random.choice((-10, 10)))
            self._haunt_cd = 0.5
        elif action == "open":
            wr = self.props.items["wardrobe"]
            wr.opened = not wr.opened
            self._haunt_cd = 0.7
