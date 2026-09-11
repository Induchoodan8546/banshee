"""Horror pacing: unease → shadows → she appears → she acts alone."""

from __future__ import annotations

import random
from enum import Enum

from banshee.actors.ghost import Ghost, GhostState
from banshee.actors.shade import Shade, ShadeKind
from banshee.room.props import Props
from banshee.room.whispers import Whispers


class Act(str, Enum):
    UNEASE = "UNEASE"
    SHADOWS = "SHADOWS"
    APPEAR = "APPEAR"
    HAUNT = "HAUNT"


class Director:
    def __init__(self, props: Props, ghost: Ghost, shade: Shade, whispers: Whispers) -> None:
        self.props = props
        self.ghost = ghost
        self.shade = shade
        self.whispers = whispers
        self.act = Act.UNEASE
        self.t = 0.0
        self.act_t = 0.0
        self.interacts = 0
        self.opened_wardrobe = False
        self._fired: set[str] = set()
        self._shadow_step = 0
        self._next_haunt = 2.8
        self._haunt_cd = 0.0

    def note_interact(self, kind: str) -> None:
        self.interacts += 1
        if kind == "open":
            self.opened_wardrobe = True
        if self.act is Act.UNEASE and self.interacts >= 1:
            self._to(Act.SHADOWS)

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
            spot = self._random_spawn()
            self.ghost.manifest(spot)
            self.whispers.set("you looked too long")
        if self.ghost.state is GhostState.IDLE and self.act_t > 1.4:
            self.ghost.talk_now()
            self.props.unease_rock = False
            self._to(Act.HAUNT)

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
        x, y = random.choice(choices)
        return (x, y)

    def _haunt(self, dt: float) -> None:
        self._haunt_cd -= dt
        if self.ghost.busy() or self._haunt_cd > 0:
            return
        action = random.choice(
            ("drift", "drift", "hide", "scare", "knock", "flicker", "nudge", "vanish")
        )
        self._haunt_cd = random.uniform(2.6, 4.8)
        if action == "drift":
            name = random.choice(list(self.props.perches))
            px, py = self.props.perches[name]
            self.ghost.drift_to((px, py), random.uniform(0.8, 1.2))
        elif action == "hide":
            wr = self.props.items["wardrobe"]
            if wr.opened:
                self.ghost.hide_behind(
                    "wardrobe",
                    self.props.hide_slot("wardrobe"),
                    self.props.peek_slot("wardrobe"),
                )
            else:
                self.ghost.hide_behind(
                    "chest",
                    self.props.hide_slot("chest"),
                    self.props.peek_slot("chest"),
                )
        elif action == "scare":
            self.ghost.scare()
        elif action == "knock":
            self.props.tap_chest()
        elif action == "flicker":
            self.props.flicker_lamp(0.9)
        elif action == "nudge":
            self.props.nudge("chair", random.choice((-8, 8)))
        elif action == "vanish":
            name = random.choice(list(self.props.perches))
            self.ghost.vanish_to(self.props.perches[name])
