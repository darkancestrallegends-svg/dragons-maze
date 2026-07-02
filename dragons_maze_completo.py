"""
🐉 DRAGON'S MAZE - Sucessor Espiritual de Dragon Crystal
Versão Completa - Todos os sistemas integrados
"""

import pygame
import sys
import random
import numpy as np
import json
import os
import base64
import zlib
import math
import heapq
from typing import List, Tuple, Optional, Dict, Set
from enum import Enum, auto
from dataclasses import dataclass, field
from datetime import datetime

# ===========================================
# CONFIGURAÇÕES GLOBAIS
# ===========================================
class GameConfig:
    SCREEN_WIDTH = 960
    SCREEN_HEIGHT = 640
    TILE_SIZE = 32
    MAP_WIDTH = 60
    MAP_HEIGHT = 40
    FPS = 60
    FOV_RADIUS = 6
    
    # Cores
    COLOR_BG = (10, 10, 20)
    COLOR_WALL = (80, 80, 100)
    COLOR_FLOOR = (40, 40, 50)
    COLOR_FLOOR_EXPLORED = (25, 25, 35)
    COLOR_PLAYER = (0, 255, 100)
    COLOR_ENEMY = (255, 60, 60)
    COLOR_ITEM = (255, 215, 0)
    COLOR_STAIRS = (100, 200, 255)
    COLOR_TEXT = (220, 220, 220)
    COLOR_HP = (255, 50, 50)
    COLOR_MP = (50, 100, 255)
    COLOR_EXP = (255, 215, 0)
    COLOR_HUNGER = (255, 140, 0)

class TileType(Enum):
    WALL = 0
    FLOOR = 1
    STAIRS_DOWN = 2
    STAIRS_UP = 3

class GameState(Enum):
    PLAYING = auto()
    PLAYER_TURN = auto()
    ENEMY_TURN = auto()
    INVENTORY = auto()
    SAVE_MENU = auto()
    GAME_OVER = auto()

class ItemType(Enum):
    WEAPON = auto()
    ARMOR = auto()
    SHIELD = auto()
    RING = auto()
    AMULET = auto()
    POTION = auto()
    SCROLL = auto()
    FOOD = auto()
    KEY = auto()

class ItemRarity(Enum):
    COMMON = (200, 200, 200)
    UNCOMMON = (0, 255, 0)
    RARE = (0, 100, 255)
    EPIC = (170, 0, 255)
    LEGENDARY = (255, 150, 0)
    
    @property
    def color(self):
        return self.value

class SpellType(Enum):
    DAMAGE = auto()
    HEAL = auto()
    BUFF = auto()
    DEBUFF = auto()
    UTILITY = auto()

class SpellElement(Enum):
    FIRE = auto()
    ICE = auto()
    LIGHTNING = auto()
    HOLY = auto()
    DARK = auto()
    NATURE = auto()

class MenuState(Enum):
    TITLE = auto()
    MAIN_MENU = auto()
    CLASS_SELECT = auto()
    OPTIONS = auto()
    CREDITS = auto()
    CONTROLS = auto()

# ===========================================
# ENTIDADES
# ===========================================
@dataclass
class Entity:
    x: int = 0
    y: int = 0
    symbol: str = "?"
    color: Tuple[int, int, int] = (255, 255, 255)
    name: str = "Entity"
    hp: int = 50
    max_hp: int = 50
    mp: int = 30
    max_mp: int = 30
    attack: int = 5
    defense: int = 2
    level: int = 1
    exp: int = 0
    exp_to_level: int = 50
    intelligence: int = 5
    luck: int = 5
    is_alive: bool = True

@dataclass
class Player(Entity):
    hunger: float = 100.0
    max_hunger: float = 100.0
    gold: int = 0
    floor: int = 1
    learned_spells: List[int] = field(default_factory=lambda: [1, 2, 4])
    class_name: str = "warrior"
    
    def __post_init__(self):
        self.symbol = "@"
        self.color = GameConfig.COLOR_PLAYER
        self.name = "Hero"

# ===========================================
# ITENS E INVENTÁRIO
# ===========================================
@dataclass
class ItemData:
    name: str
    symbol: str
    item_type: ItemType
    rarity: ItemRarity = ItemRarity.COMMON
    value: int = 0
    description: str = ""
    stackable: bool = False
    max_stack: int = 1
    effects: Dict[str, int] = field(default_factory=dict)
    
    @property
    def color(self) -> Tuple[int, int, int]:
        return self.rarity.color

ITEM_DATABASE = {
    "iron_sword": ItemData("Espada de Ferro", "/", ItemType.WEAPON, ItemRarity.UNCOMMON, 25,
                          "Espada forjada em ferro", effects={"attack": 6}),
    "leather_armor": ItemData("Armadura de Couro", "[", ItemType.ARMOR, ItemRarity.COMMON, 15,
                             "Proteção básica", effects={"defense": 2}),
    "health_potion": ItemData("Poção de Vida", "!", ItemType.POTION, ItemRarity.COMMON, 20,
                             "Restaura 30 HP", stackable=True, max_stack=5, effects={"heal": 30}),
    "mana_potion": ItemData("Poção de Mana", "!", ItemType.POTION, ItemRarity.COMMON, 15,
                           "Restaura 20 MP", stackable=True, max_stack=5, effects={"mana": 20}),
    "bread": ItemData("Pão", "%", ItemType.FOOD, ItemRarity.COMMON, 5,
                     "Restaura 20 de fome", stackable=True, max_stack=10, effects={"hunger": 20}),
    "ring_of_luck": ItemData("Anel da Sorte", "°", ItemType.RING, ItemRarity.UNCOMMON, 35,
                            "Aumenta sua sorte", effects={"luck": 5}),
    "fire_scroll": ItemData("Pergaminho de Fogo", "?", ItemType.SCROLL, ItemRarity.UNCOMMON, 30,
                           "Lança Bola de Fogo", effects={"spell": 1}),
}

class InventorySlot:
    def __init__(self, item_id: str, quantity: int = 1):
        self.item_id = item_id
        self.quantity = quantity
    
    @property
    def item_data(self) -> Optional[ItemData]:
        return ITEM_DATABASE.get(self.item_id)

class Inventory:
    def __init__(self, max_slots: int = 30):
        self.slots: List[Optional[InventorySlot]] = [None] * max_slots
        self.max_slots = max_slots
    
    def add_item(self, item_id: str, quantity: int = 1) -> bool:
        if item_id not in ITEM_DATABASE:
            return False
        item_data = ITEM_DATABASE[item_id]
        
        if item_data.stackable:
            for slot in self.slots:
                if slot and slot.item_id == item_id and slot.quantity < item_data.max_stack:
                    slot.quantity += quantity
                    return True
        
        for i in range(self.max_slots):
            if self.slots[i] is None:
                self.slots[i] = InventorySlot(item_id, quantity)
                return True
        return False
    
    def remove_item(self, slot_index: int, quantity: int = 1) -> bool:
        if 0 <= slot_index < self.max_slots and self.slots[slot_index]:
            self.slots[slot_index].quantity -= quantity
            if self.slots[slot_index].quantity <= 0:
                self.slots[slot_index] = None
            return True
        return False
    
    def get_item(self, slot_index: int) -> Optional[InventorySlot]:
        if 0 <= slot_index < self.max_slots:
            return self.slots[slot_index]
        return None

class EquipmentSlots:
    def __init__(self):
        self.slots: Dict[ItemType, Optional[str]] = {
            ItemType.WEAPON: None,
            ItemType.ARMOR: None,
            ItemType.SHIELD: None,
            ItemType.RING: None,
            ItemType.AMULET: None,
        }
    
    def equip(self, item_id: str) -> Optional[str]:
        if item_id not in ITEM_DATABASE:
            return None
        item_data = ITEM_DATABASE[item_id]
        slot_type = item_data.item_type
        if slot_type not in self.slots:
            return None
        old_item = self.slots[slot_type]
        self.slots[slot_type] = item_id
        return old_item
    
    def get_total_effects(self) -> Dict[str, int]:
        total = {}
        for item_id in self.slots.values():
            if item_id and item_id in ITEM_DATABASE:
                for effect, value in ITEM_DATABASE[item_id].effects.items():
                    total[effect] = total.get(effect, 0) + value
        return total

# ===========================================
# MAGIAS
# ===========================================
class Spell:
    def __init__(self, name: str, mp_cost: int, spell_type: SpellType,
                 element: SpellElement, power: int = 0, description: str = "",
                 duration: int = 0, aoe_radius: int = 0):
        self.name = name
        self.mp_cost = mp_cost
        self.spell_type = spell_type
        self.element = element
        self.power = power
        self.description = description
        self.duration = duration
        self.aoe_radius = aoe_radius

SPELLS = {
    1: Spell("Bola de Fogo", 8, SpellType.DAMAGE, SpellElement.FIRE, 25,
             "Lança uma bola de fogo no inimigo"),
    2: Spell("Raio de Gelo", 6, SpellType.DAMAGE, SpellElement.ICE, 18,
             "Congela o inimigo com gelo"),
    3: Spell("Relâmpago", 10, SpellType.DAMAGE, SpellElement.LIGHTNING, 30,
             "Invoca um poderoso raio", aoe_radius=1),
    4: Spell("Cura Divina", 12, SpellType.HEAL, SpellElement.HOLY, 35,
             "Restaura seus ferimentos"),
    5: Spell("Escudo Arcano", 15, SpellType.BUFF, SpellElement.HOLY, 0,
             "Aumenta sua defesa", duration=5),
    6: Spell("Veneno Sombrio", 8, SpellType.DEBUFF, SpellElement.DARK, 10,
             "Envenena o inimigo", duration=3),
    7: Spell("Teletransporte", 5, SpellType.UTILITY, SpellElement.NATURE, 0,
             "Teleporta para posição aleatória"),
    8: Spell("Explosão Arcana", 20, SpellType.DAMAGE, SpellElement.FIRE, 45,
             "Explosão mágica em área", aoe_radius=2),
}

class Particle:
    def __init__(self, x: float, y: float, color: Tuple[int, int, int],
                 velocity: Tuple[float, float], lifetime: int = 30):
        self.x = x
        self.y = y
        self.color = color
        self.vx, self.vy = velocity
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = random.randint(2, 5)
    
    def update(self) -> bool:
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 1
        self.vx *= 0.95
        self.vy *= 0.95
        return self.lifetime > 0

class ParticleSystem:
    def __init__(self):
        self.particles: List[Particle] = []
    
    def emit(self, x: float, y: float, color: Tuple[int, int, int],
             count: int = 20, spread: float = 3.0):
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(0.5, spread)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            self.particles.append(Particle(x, y, color, (vx, vy), random.randint(15, 40)))
    
    def update(self):
        self.particles = [p for p in self.particles if p.update()]

class MagicSystem:
    def __init__(self):
        self.particles = ParticleSystem()
        self.active_effects: Dict[str, Dict] = {}
        self.log: List[str] = []
    
    def cast_spell(self, caster, spell_num: int, targets: List, game_map=None) -> Tuple[bool, str]:
        if spell_num not in SPELLS:
            return False, "Magia desconhecida!"
        
        spell = SPELLS[spell_num]
        
        if hasattr(caster, 'mp') and caster.mp < spell.mp_cost:
            return False, f"MP insuficiente! Precisa de {spell.mp_cost} MP"
        
        if hasattr(caster, 'mp'):
            caster.mp -= spell.mp_cost
        
        result = ""
        
        if spell.spell_type == SpellType.DAMAGE:
            result = self._cast_damage(caster, spell, targets)
        elif spell.spell_type == SpellType.HEAL:
            result = self._cast_heal(caster, spell)
        elif spell.spell_type == SpellType.BUFF:
            result = self._cast_buff(caster, spell)
        elif spell.spell_type == SpellType.DEBUFF:
            result = self._cast_debuff(caster, spell, targets)
        elif spell.spell_type == SpellType.UTILITY:
            result = self._cast_utility(caster, spell, game_map)
        
        element_colors = {
            SpellElement.FIRE: (255, 100, 0),
            SpellElement.ICE: (100, 200, 255),
            SpellElement.LIGHTNING: (255, 255, 0),
            SpellElement.HOLY: (255, 255, 200),
            SpellElement.DARK: (100, 0, 100),
            SpellElement.NATURE: (0, 255, 100),
        }
        color = element_colors.get(spell.element, (255, 255, 255))
        self.particles.emit(caster.x * 32 + 16, caster.y * 32 + 16, color, 10, 2.0)
        
        return True, result
    
    def _cast_damage(self, caster, spell: Spell, targets: List) -> str:
        if not targets:
            return "Nenhum alvo!"
        
        results = []
        for target in targets:
            if not target.is_alive:
                continue
            
            damage = spell.power + random.randint(-5, 8)
            is_crit = random.random() < 0.1
            
            if is_crit:
                damage = int(damage * 1.5)
                results.append(f"💥 CRÍTICO! {spell.name} causa {damage} de dano em {target.name}!")
            else:
                results.append(f"✨ {spell.name} causa {damage} de dano em {target.name}!")
            
            target.hp = max(0, target.hp - damage)
            
            if target.hp <= 0:
                target.is_alive = False
                results.append(f"💀 {target.name} foi destruído!")
        
        return "\n".join(results) if results else "Nenhum alvo atingido!"
    
    def _cast_heal(self, caster, spell: Spell) -> str:
        heal_amount = spell.power + random.randint(-5, 10)
        old_hp = caster.hp
        caster.hp = min(caster.max_hp, caster.hp + heal_amount)
        actual_heal = caster.hp - old_hp
        return f"💚 Cura restaura {actual_heal} HP!"
    
    def _cast_buff(self, caster, spell: Spell) -> str:
        if spell.name == "Escudo Arcano":
            defense_bonus = 5
            caster.defense += defense_bonus
            effect_key = f"shield_{id(caster)}"
            self.active_effects[effect_key] = {
                'type': 'buff', 'stat': 'defense', 'value': defense_bonus,
                'duration': spell.duration, 'target': caster
            }
            return f"🛡️ Escudo Arcano! +{defense_bonus} DEF por {spell.duration} turnos!"
        return f"{spell.name} ativado!"
    
    def _cast_debuff(self, caster, spell: Spell, targets: List) -> str:
        if not targets:
            return "Nenhum alvo!"
        
        results = []
        for target in targets:
            if not target.is_alive:
                continue
            effect_key = f"poison_{id(target)}"
            self.active_effects[effect_key] = {
                'type': 'dot', 'damage': spell.power,
                'duration': spell.duration, 'target': target
            }
            results.append(f"☠️ {target.name} envenenado! {spell.power} de dano/turno por {spell.duration} turnos!")
        
        return "\n".join(results)
    
    def _cast_utility(self, caster, spell: Spell, game_map) -> str:
        if spell.name == "Teletransporte" and game_map is not None:
            for _ in range(50):
                new_x = random.randint(1, game_map.shape[1] - 2)
                new_y = random.randint(1, game_map.shape[0] - 2)
                if game_map[new_y][new_x] == TileType.FLOOR.value:
                    caster.x, caster.y = new_x, new_y
                    return f"🌀 Teleportado para ({new_x}, {new_y})!"
            return "🌀 Falha no teleporte!"
        return f"{spell.name} usado!"
    
    def update_effects(self):
        effects_to_remove = []
        for key, effect in self.active_effects.items():
            effect['duration'] -= 1
            if effect['type'] == 'dot':
                target = effect['target']
                if target.is_alive:
                    target.hp = max(0, target.hp - effect['damage'])
                    self.log.append(f"☠️ {target.name} sofre {effect['damage']} de dano do veneno!")
            if effect['duration'] <= 0:
                effects_to_remove.append(key)
        
        for key in effects_to_remove:
            effect = self.active_effects[key]
            if effect['type'] == 'buff':
                target = effect['target']
                if effect['stat'] == 'defense':
                    target.defense -= effect['value']
            del self.active_effects[key]

# ===========================================
# DUNGEON GENERATOR
# ===========================================
class DungeonGenerator:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.map = np.zeros((height, width), dtype=int)
        self.rooms = []
        
    def generate(self, floor_number: int = 1) -> np.ndarray:
        self.map.fill(TileType.WALL.value)
        self.rooms = []
        
        num_rooms = random.randint(6, 10)
        for _ in range(100):
            if len(self.rooms) >= num_rooms:
                break
            w = random.randint(4, 9)
            h = random.randint(4, 9)
            x = random.randint(1, self.width - w - 1)
            y = random.randint(1, self.height - h - 1)
            new_room = {'x': x, 'y': y, 'w': w, 'h': h}
            if not self._overlaps(new_room):
                self._create_room(new_room)
                self.rooms.append(new_room)
        
        for i in range(len(self.rooms) - 1):
            r1 = self.rooms[i]
            r2 = self.rooms[i + 1]
            x1 = r1['x'] + r1['w'] // 2
            y1 = r1['y'] + r1['h'] // 2
            x2 = r2['x'] + r2['w'] // 2
            y2 = r2['y'] + r2['h'] // 2
            
            if random.random() < 0.5:
                self._h_corridor(x1, x2, y1)
                self._v_corridor(y1, y2, x2)
            else:
                self._v_corridor(y1, y2, x1)
                self._h_corridor(x1, x2, y2)
        
        if self.rooms:
            first = self.rooms[0]
            self.map[first['y'] + first['h']//2][first['x'] + first['w']//2] = TileType.STAIRS_DOWN.value
            last = self.rooms[-1]
            self.map[last['y'] + last['h']//2][last['x'] + last['w']//2] = TileType.STAIRS_UP.value
        
        return self.map
    
    def _overlaps(self, room: dict) -> bool:
        for other in self.rooms:
            if (room['x'] < other['x'] + other['w'] + 1 and
                room['x'] + room['w'] + 1 > other['x'] and
                room['y'] < other['y'] + other['h'] + 1 and
                room['y'] + room['h'] + 1 > other['y']):
                return True
        return False
    
    def _create_room(self, room: dict):
        self.map[room['y']:room['y']+room['h'], room['x']:room['x']+room['w']] = TileType.FLOOR.value
    
    def _h_corridor(self, x1: int, x2: int, y: int):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if 0 <= x < self.width and 0 <= y < self.height:
                self.map[y][x] = TileType.FLOOR.value
    
    def _v_corridor(self, y1: int, y2: int, x: int):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            if 0 <= x < self.width and 0 <= y < self.height:
                self.map[y][x] = TileType.FLOOR.value

# ===========================================
# FOG OF WAR
# ===========================================
class FogOfWar:
    def __init__(self, width: int, height: int, radius: int = 6):
        self.width = width
        self.height = height
        self.radius = radius
        self.visible = np.zeros((height, width), dtype=bool)
        self.explored = np.zeros((height, width), dtype=bool)
    
    def update(self, px: int, py: int, game_map: np.ndarray):
        self.visible.fill(False)
        for y in range(max(0, py - self.radius), min(self.height, py + self.radius + 1)):
            for x in range(max(0, px - self.radius), min(self.width, px + self.radius + 1)):
                if self._has_los(px, py, x, y, game_map):
                    self.visible[y][x] = True
                    self.explored[y][x] = True
    
    def _has_los(self, x0: int, y0: int, x1: int, y1: int, game_map: np.ndarray) -> bool:
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        x, y = x0, y0
        n = 1 + dx + dy
        x_inc = 1 if x1 > x0 else -1
        y_inc = 1 if y1 > y0 else -1
        error = dx - dy
        dx *= 2
        dy *= 2
        
        for _ in range(n):
            if 0 <= x < self.width and 0 <= y < self.height:
                if game_map[y][x] == TileType.WALL.value:
                    return (x == x1 and y == y1)
            if error > 0:
                x += x_inc
                error -= dy
            else:
                y += y_inc
                error += dx
        return True

# ===========================================
# PATHFINDING
# ===========================================
class Pathfinding:
    def __init__(self, game_map: np.ndarray):
        self.map = game_map
        self.width = game_map.shape[1]
        self.height = game_map.shape[0]
    
    def find_path(self, start: Tuple[int, int], goal: Tuple[int, int], max_steps: int = 30) -> List[Tuple[int, int]]:
        if start == goal:
            return []
        
        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}
        
        while open_set:
            _, current = heapq.heappop(open_set)
            
            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                return path[::-1]
            
            for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                neighbor = (current[0] + dx, current[1] + dy)
                if 0 <= neighbor[0] < self.width and 0 <= neighbor[1] < self.height:
                    if self.map[neighbor[1]][neighbor[0]] == TileType.WALL.value:
                        continue
                    tentative_g = g_score[current] + 1
                    if neighbor not in g_score or tentative_g < g_score[neighbor]:
                        g_score[neighbor] = tentative_g
                        f_score = tentative_g + abs(neighbor[0] - goal[0]) + abs(neighbor[1] - goal[1])
                        heapq.heappush(open_set, (f_score, neighbor))
                        came_from[neighbor] = current
        return []

# ===========================================
# ... [CONTINUA NA PRÓXIMA MENSAGEM DEVIDO AO TAMANHO] ...
# ===========================================
# COMBAT SYSTEM
# ===========================================
class CombatSystem:
    def __init__(self):
        self.log: List[str] = []
    
    def attack(self, attacker: Entity, defender: Entity) -> str:
        if not defender.is_alive:
            return ""
        
        hit_chance = 0.8 + (attacker.level - defender.level) * 0.05
        hit_chance = max(0.1, min(0.95, hit_chance))
        
        if random.random() > hit_chance:
            msg = f"{attacker.name} errou {defender.name}!"
            self.log.append(msg)
            return msg
        
        damage = max(1, attacker.attack - defender.defense + random.randint(-2, 4))
        
        is_crit = random.random() < 0.1
        if is_crit:
            damage = int(damage * 2)
            msg = f"⚡ CRÍTICO! {attacker.name} causou {damage} de dano em {defender.name}!"
        else:
            msg = f"{attacker.name} causou {damage} de dano em {defender.name}!"
        
        defender.hp -= damage
        self.log.append(msg)
        
        if defender.hp <= 0:
            defender.hp = 0
            defender.is_alive = False
            death_msg = f"💀 {defender.name} foi derrotado!"
            self.log.append(death_msg)
            
            if isinstance(attacker, Player):
                exp_gain = defender.level * 15 + random.randint(5, 15)
                attacker.exp += exp_gain
                self.log.append(f"✨ +{exp_gain} EXP")
                
                if attacker.exp >= attacker.exp_to_level:
                    self._level_up(attacker)
        
        return msg
    
    def _level_up(self, player: Player):
        player.level += 1
        player.exp -= player.exp_to_level
        player.exp_to_level = int(player.exp_to_level * 1.5)
        player.max_hp += 15
        player.hp = player.max_hp
        player.max_mp += 5
        player.mp = player.max_mp
        player.attack += 3
        player.defense += 2
        self.log.append(f"⭐ LEVEL UP! {player.name} agora é nível {player.level}!")
    
    def get_log(self, clear: bool = False) -> List[str]:
        log = self.log[-5:] if len(self.log) > 5 else self.log.copy()
        if clear:
            self.log = self.log[-3:]
        return log

# ===========================================
# ... CONTINUA NA PRÓXIMA MENSAGEM ...
# ===========================================
# RENDERER
# ===========================================
class Renderer:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.font = pygame.font.Font(None, 22)
        self.big_font = pygame.font.Font(None, 36)
        self.tile_size = GameConfig.TILE_SIZE
    
    def render(self, game_map: np.ndarray, player: Player, enemies: List[Entity],
               items: List, fow: FogOfWar, combat_log: List[str],
               camera_x: int, camera_y: int, particles: ParticleSystem = None):
        
        self.screen.fill(GameConfig.COLOR_BG)
        
        view_w = GameConfig.SCREEN_WIDTH * 2 // 3 // self.tile_size
        view_h = GameConfig.SCREEN_HEIGHT // self.tile_size
        
        self._render_map(game_map, player, enemies, items, fow, camera_x, camera_y, view_w, view_h)
        
        if particles:
            self._render_particles(particles, camera_x, camera_y, view_w)
        
        self._render_hud(player, combat_log, view_w)
        
        pygame.display.flip()
    
    def _render_map(self, game_map, player, enemies, items, fow, cx, cy, vw, vh):
        for y in range(vh):
            for x in range(vw):
                map_x = cx + x
                map_y = cy + y
                screen_x = x * self.tile_size
                screen_y = y * self.tile_size
                
                if 0 <= map_x < GameConfig.MAP_WIDTH and 0 <= map_y < GameConfig.MAP_HEIGHT:
                    if fow.visible[map_y][map_x]:
                        tile = game_map[map_y][map_x]
                        if tile == TileType.WALL.value:
                            color = GameConfig.COLOR_WALL
                        elif tile in [TileType.STAIRS_DOWN.value, TileType.STAIRS_UP.value]:
                            color = GameConfig.COLOR_STAIRS
                        else:
                            color = GameConfig.COLOR_FLOOR
                        
                        pygame.draw.rect(self.screen, color,
                                       (screen_x, screen_y, self.tile_size, self.tile_size))
                        
                        # Desenhar bordas das paredes
                        if tile == TileType.WALL.value:
                            pygame.draw.rect(self.screen, (60, 60, 70),
                                           (screen_x, screen_y, self.tile_size, self.tile_size), 1)
                        
                        # Desenhar escadas
                        if tile == TileType.STAIRS_DOWN.value:
                            text = self.big_font.render("▼", True, (255, 255, 255))
                            text_rect = text.get_rect(center=(screen_x + self.tile_size//2, screen_y + self.tile_size//2))
                            self.screen.blit(text, text_rect)
                        elif tile == TileType.STAIRS_UP.value:
                            text = self.big_font.render("▲", True, (255, 255, 255))
                            text_rect = text.get_rect(center=(screen_x + self.tile_size//2, screen_y + self.tile_size//2))
                            self.screen.blit(text, text_rect)
                    
                    elif fow.explored[map_y][map_x]:
                        pygame.draw.rect(self.screen, GameConfig.COLOR_FLOOR_EXPLORED,
                                       (screen_x, screen_y, self.tile_size, self.tile_size))
        
        # Renderizar itens
        for item in items:
            if fow.visible[item.y][item.x]:
                sx = (item.x - cx) * self.tile_size
                sy = (item.y - cy) * self.tile_size
                if 0 <= sx < vw * self.tile_size and 0 <= sy < vh * self.tile_size:
                    # Brilho pulsante para itens
                    pulse = int(127 + 127 * math.sin(pygame.time.get_ticks() * 0.005))
                    item_color = (min(255, item.color[0] + pulse//2),
                                min(255, item.color[1] + pulse//2),
                                min(255, item.color[2] + pulse//2))
                    
                    text = self.big_font.render(item.symbol, True, item_color)
                    text_rect = text.get_rect(center=(sx + self.tile_size//2, sy + self.tile_size//2))
                    self.screen.blit(text, text_rect)
        
        # Renderizar inimigos
        for enemy in enemies:
            if enemy.is_alive and fow.visible[enemy.y][enemy.x]:
                sx = (enemy.x - cx) * self.tile_size
                sy = (enemy.y - cy) * self.tile_size
                if 0 <= sx < vw * self.tile_size and 0 <= sy < vh * self.tile_size:
                    # Barra de HP do inimigo
                    if enemy.hp < enemy.max_hp:
                        bar_width = self.tile_size - 4
                        bar_height = 3
                        bar_x = sx + 2
                        bar_y = sy - 6
                        
                        hp_ratio = enemy.hp / enemy.max_hp
                        pygame.draw.rect(self.screen, (60, 0, 0), (bar_x, bar_y, bar_width, bar_height))
                        pygame.draw.rect(self.screen, (255, 50, 50), 
                                       (bar_x, bar_y, int(bar_width * hp_ratio), bar_height))
                    
                    text = self.big_font.render(enemy.symbol, True, enemy.color)
                    text_rect = text.get_rect(center=(sx + self.tile_size//2, sy + self.tile_size//2))
                    self.screen.blit(text, text_rect)
        
        # Renderizar player
        px = (player.x - cx) * self.tile_size
        py = (player.y - cy) * self.tile_size
        text = self.big_font.render(player.symbol, True, player.color)
        text_rect = text.get_rect(center=(px + self.tile_size//2, py + self.tile_size//2))
        self.screen.blit(text, text_rect)
    
    def _render_particles(self, particles: ParticleSystem, cx: int, cy: int, vw: int):
        for particle in particles.particles:
            screen_x = (particle.x / self.tile_size - cx) * self.tile_size
            screen_y = (particle.y / self.tile_size - cy) * self.tile_size
            
            if 0 <= screen_x < vw * self.tile_size and 0 <= screen_y < GameConfig.SCREEN_HEIGHT:
                alpha = int(255 * (particle.lifetime / particle.max_lifetime))
                size = int(particle.size * (particle.lifetime / particle.max_lifetime))
                
                if size > 0:
                    color_with_alpha = (*particle.color, alpha)
                    surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                    pygame.draw.circle(surf, color_with_alpha, (size, size), size)
                    self.screen.blit(surf, (int(screen_x), int(screen_y)))
    
    def _render_hud(self, player: Player, combat_log: List[str], view_w: int):
        hud_x = view_w * self.tile_size + 10
        hud_width = GameConfig.SCREEN_WIDTH - hud_x - 10
        
        # Fundo do HUD
        hud_surf = pygame.Surface((hud_width + 10, GameConfig.SCREEN_HEIGHT), pygame.SRCALPHA)
        hud_surf.fill((20, 20, 30, 230))
        self.screen.blit(hud_surf, (hud_x - 5, 0))
        
        pygame.draw.rect(self.screen, (60, 60, 80), (hud_x - 5, 0, hud_width + 10, GameConfig.SCREEN_HEIGHT), 2)
        
        y = 15
        
        # Título
        title = self.big_font.render("🐉 Dragon's Maze", True, (255, 200, 50))
        self.screen.blit(title, (hud_x, y))
        y += 40
        
        # Status do player
        texts = [
            f"Andar: {player.floor}  Nível: {player.level}",
            f"Classe: {player.class_name.capitalize()}",
            "",
            f"HP: {player.hp}/{player.max_hp}",
            f"MP: {player.mp}/{player.max_mp}",
            f"EXP: {player.exp}/{player.exp_to_level}",
            f"Fome: {int(player.hunger)}%",
            f"ATK: {player.attack}  DEF: {player.defense}",
            f"INT: {player.intelligence}  SORT: {player.luck}",
            f"Ouro: {player.gold}",
            "",
            "═══ CONTROLES ═══",
            "WASD/Setas: Mover",
            "1-4: Magias",
            "E: Escada  I: Inventário",
            "F1: Salvar  F2: Carregar",
            "F5: Quick Save",
            "ESC: Menu",
            "",
            "═══ COMBATE ═══",
        ]
        
        for text in texts:
            if text.startswith("═══"):
                rendered = self.font.render(text, True, (255, 200, 50))
            else:
                rendered = self.font.render(text, True, GameConfig.COLOR_TEXT)
            self.screen.blit(rendered, (hud_x, y))
            y += 20
        
        # Log de combate
        y += 5
        for log in combat_log[-6:]:
            color = (255, 255, 200) if "CRÍTICO" in log or "LEVEL UP" in log else (200, 200, 200)
            rendered = self.font.render(log, True, color)
            self.screen.blit(rendered, (hud_x, y))
            y += 18
        
        # Barras de HP e Fome
        bar_width = hud_width - 10
        bar_x = hud_x
        
        # HP Bar
        hp_ratio = player.hp / player.max_hp
        pygame.draw.rect(self.screen, (40, 0, 0), (bar_x, GameConfig.SCREEN_HEIGHT - 45, bar_width, 15))
        hp_color = (255, 50, 50) if hp_ratio > 0.3 else (255, 100, 0)
        pygame.draw.rect(self.screen, hp_color, (bar_x, GameConfig.SCREEN_HEIGHT - 45, int(bar_width * hp_ratio), 15))
        hp_label = self.font.render(f"HP", True, (255, 255, 255))
        self.screen.blit(hp_label, (bar_x + 5, GameConfig.SCREEN_HEIGHT - 45))
        
        # Fome Bar
        hunger_ratio = player.hunger / player.max_hunger
        pygame.draw.rect(self.screen, (40, 30, 0), (bar_x, GameConfig.SCREEN_HEIGHT - 25, bar_width, 10))
        pygame.draw.rect(self.screen, GameConfig.COLOR_HUNGER, 
                        (bar_x, GameConfig.SCREEN_HEIGHT - 25, int(bar_width * hunger_ratio), 10))
        hunger_label = self.font.render("FOME", True, (255, 255, 255))
        self.screen.blit(hunger_label, (bar_x + 5, GameConfig.SCREEN_HEIGHT - 25))
    
    def render_map_only(self, game_map, player, enemies, items, fow, cx, cy):
        """Renderiza apenas o mapa (para telas de menu)"""
        view_w = GameConfig.SCREEN_WIDTH * 2 // 3 // self.tile_size
        view_h = GameConfig.SCREEN_HEIGHT // self.tile_size
        self._render_map(game_map, player, enemies, items, fow, cx, cy, view_w, view_h)

# ===========================================
# ... CONTINUA NA PRÓXIMA MENSAGEM ...
# ===========================================
# MENU PRINCIPAL
# ===========================================
class MenuParticle:
    """Partícula decorativa para o menu"""
    def __init__(self, x: float, y: float, speed: float, color: Tuple[int, int, int]):
        self.x = x
        self.y = y
        self.base_x = x
        self.base_y = y
        self.speed = speed
        self.color = color
        self.angle = random.uniform(0, math.pi * 2)
        self.amplitude = random.uniform(20, 60)
        self.size = random.randint(1, 3)
        self.alpha = random.randint(50, 150)
    
    def update(self, time: float):
        self.x = self.base_x + math.cos(self.angle + time * self.speed) * self.amplitude
        self.y = self.base_y + math.sin(self.angle + time * self.speed * 0.7) * self.amplitude * 0.5
        self.alpha = int(100 + 55 * math.sin(time * self.speed + self.angle))

class MenuButton:
    def __init__(self, text: str, x: int, y: int, width: int, height: int,
                 color: Tuple[int, int, int] = (60, 60, 100),
                 hover_color: Tuple[int, int, int] = (100, 100, 180),
                 text_color: Tuple[int, int, int] = (220, 220, 220)):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_hovered = False
        self.scale = 1.0
        self.target_scale = 1.0
    
    def update(self, mouse_pos: Tuple[int, int]):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        self.target_scale = 1.05 if self.is_hovered else 1.0
        self.scale += (self.target_scale - self.scale) * 0.2
    
    def render(self, screen: pygame.Surface, font: pygame.font.Font):
        color = self.hover_color if self.is_hovered else self.color
        
        scaled_width = int(self.rect.width * self.scale)
        scaled_height = int(self.rect.height * self.scale)
        scaled_x = self.rect.x - (scaled_width - self.rect.width) // 2
        scaled_y = self.rect.y - (scaled_height - self.rect.height) // 2
        
        shadow_rect = pygame.Rect(scaled_x + 3, scaled_y + 3, scaled_width, scaled_height)
        pygame.draw.rect(screen, (20, 20, 30), shadow_rect, border_radius=8)
        
        main_rect = pygame.Rect(scaled_x, scaled_y, scaled_width, scaled_height)
        pygame.draw.rect(screen, color, main_rect, border_radius=8)
        pygame.draw.rect(screen, (255, 255, 255, 50), main_rect, 2, border_radius=8)
        
        text_surface = font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=main_rect.center)
        screen.blit(text_surface, text_rect)
    
    def is_clicked(self, pos: Tuple[int, int]) -> bool:
        return self.rect.collidepoint(pos)

class ClassOption:
    def __init__(self, name: str, description: str, stats: dict, 
                 symbol: str, color: Tuple[int, int, int]):
        self.name = name
        self.description = description
        self.stats = stats
        self.symbol = symbol
        self.color = color

CLASSES = {
    "warrior": ClassOption(
        "Guerreiro", "Mestre das armas e combate corpo a corpo. Alta resistência e força bruta.",
        {"hp": 120, "mp": 20, "attack": 12, "defense": 8, "intelligence": 3, "luck": 4},
        "⚔️", (255, 100, 50)
    ),
    "mage": ClassOption(
        "Mago", "Estudioso das artes arcanas. Poderoso em magias, mas frágil fisicamente.",
        {"hp": 70, "mp": 80, "attack": 5, "defense": 3, "intelligence": 15, "luck": 6},
        "🧙", (100, 150, 255)
    ),
    "rogue": ClassOption(
        "Ladrão", "Ágil e sorrateiro. Especialista em furtividade e ataques precisos.",
        {"hp": 90, "mp": 40, "attack": 9, "defense": 5, "intelligence": 6, "luck": 10},
        "🗡️", (100, 255, 100)
    ),
}

class MainMenu:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.state = MenuState.TITLE
        self.transition_alpha = 0
        self.is_transitioning = False
        
        self.title_font = pygame.font.Font(None, 72)
        self.subtitle_font = pygame.font.Font(None, 36)
        self.button_font = pygame.font.Font(None, 32)
        self.small_font = pygame.font.Font(None, 24)
        self.description_font = pygame.font.Font(None, 20)
        
        self.particles = self._create_particles()
        self.time = 0
        
        self.buttons: List[MenuButton] = []
        self._create_main_buttons()
        
        self.class_buttons: List[MenuButton] = []
        self.selected_class: Optional[str] = None
        self._create_class_buttons()
        
        self.option_buttons: List[MenuButton] = []
        self._create_option_buttons()
        
        self.difficulty = "normal"
        self.sound_enabled = True
        self.fullscreen = False
        
        self.title_y_offset = 0
        self.title_alpha = 255
        
        self.dragon_art = [
            "                    ___________                    ",
            "                   /           \\                  ",
            "                  /   O     O   \\                 ",
            "                 |       ^       |                ",
            "                 |    \\_____/    |                ",
            "                  \\             /                 ",
            "                   \\___________/                  ",
            "                         |                        ",
            "                   /-----|-----\\                 ",
            "                  /      |      \\                ",
            "                 /       |       \\               ",
            "                /        |        \\              ",
            "         ______/_________|_________\\______       ",
            "        /                                \\      ",
        ]
    
    def _create_particles(self) -> List[MenuParticle]:
        particles = []
        colors = [(255, 100, 50), (255, 200, 50), (255, 50, 50), (200, 100, 255), (50, 150, 255)]
        for _ in range(50):
            x = random.randint(0, self.screen.get_width())
            y = random.randint(0, self.screen.get_height())
            speed = random.uniform(0.3, 1.5)
            color = random.choice(colors)
            particles.append(MenuParticle(x, y, speed, color))
        return particles
    
    def _create_main_buttons(self):
        button_width = 250
        button_height = 50
        center_x = self.screen.get_width() // 2 - button_width // 2
        start_y = 350
        
        self.buttons = [
            MenuButton("Novo Jogo", center_x, start_y, button_width, button_height),
            MenuButton("Continuar", center_x, start_y + 65, button_width, button_height,
                      color=(40, 40, 60), hover_color=(80, 80, 120)),
            MenuButton("Opções", center_x, start_y + 130, button_width, button_height),
            MenuButton("Controles", center_x, start_y + 195, button_width, button_height),
            MenuButton("Créditos", center_x, start_y + 260, button_width, button_height),
            MenuButton("Sair", center_x, start_y + 325, button_width, button_height,
                      color=(80, 30, 30), hover_color=(150, 50, 50)),
        ]
    
    def _create_class_buttons(self):
        button_width = 200
        button_height = 200
        spacing = 30
        total_width = 3 * button_width + 2 * spacing
        start_x = (self.screen.get_width() - total_width) // 2
        start_y = 200
        
        self.class_buttons = [
            MenuButton("", start_x, start_y, button_width, button_height),
            MenuButton("", start_x + button_width + spacing, start_y, button_width, button_height),
            MenuButton("", start_x + 2 * (button_width + spacing), start_y, button_width, button_height),
        ]
    
    def _create_option_buttons(self):
        button_width = 250
        button_height = 40
        center_x = self.screen.get_width() // 2 - button_width // 2
        start_y = 300
        
        self.option_buttons = [
            MenuButton("Dificuldade: Normal", center_x, start_y, button_width, button_height),
            MenuButton("Som: Ligado", center_x, start_y + 55, button_width, button_height),
            MenuButton("Tela Cheia: Não", center_x, start_y + 110, button_width, button_height),
            MenuButton("Voltar", center_x, start_y + 180, button_width, button_height,
                      color=(80, 30, 30), hover_color=(150, 50, 50)),
        ]
    
    def update(self, dt: float):
        self.time += dt * 0.001
        for particle in self.particles:
            particle.update(self.time)
        
        self.title_y_offset = math.sin(self.time * 0.5) * 5
        self.title_alpha = int(200 + 55 * math.sin(self.time * 0.8))
        
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            button.update(mouse_pos)
        for button in self.class_buttons:
            button.update(mouse_pos)
        for button in self.option_buttons:
            button.update(mouse_pos)
        
        if self.is_transitioning:
            self.transition_alpha = min(255, self.transition_alpha + 8)
    
    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self._handle_click(event.pos)
        
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.state == MenuState.MAIN_MENU:
                return "quit"
            else:
                self.state = MenuState.MAIN_MENU
                self.transition_alpha = 0
                self.is_transitioning = True
        
        return None
    
    def _handle_click(self, pos: Tuple[int, int]) -> Optional[str]:
        if self.state == MenuState.MAIN_MENU:
            for i, button in enumerate(self.buttons):
                if button.is_clicked(pos):
                    actions = ["new_game", "continue", "options", "controls", "credits", "quit"]
                    if actions[i] == "new_game":
                        self.state = MenuState.CLASS_SELECT
                        self.transition_alpha = 0
                        self.is_transitioning = True
                    elif actions[i] == "options":
                        self.state = MenuState.OPTIONS
                        self.transition_alpha = 0
                        self.is_transitioning = True
                    elif actions[i] == "controls":
                        self.state = MenuState.CONTROLS
                        self.transition_alpha = 0
                        self.is_transitioning = True
                    elif actions[i] == "credits":
                        self.state = MenuState.CREDITS
                        self.transition_alpha = 0
                        self.is_transitioning = True
                    else:
                        return actions[i]
        
        elif self.state == MenuState.CLASS_SELECT:
            class_names = list(CLASSES.keys())
            for i, button in enumerate(self.class_buttons):
                if button.is_clicked(pos) and i < len(class_names):
                    self.selected_class = class_names[i]
            
            confirm_rect = pygame.Rect(self.screen.get_width() // 2 - 100, 460, 200, 50)
            if confirm_rect.collidepoint(pos) and self.selected_class:
                self.transition_alpha = 0
                self.is_transitioning = True
                return f"start_{self.selected_class}"
        
        elif self.state == MenuState.OPTIONS:
            for i, button in enumerate(self.option_buttons):
                if button.is_clicked(pos):
                    if i == 0:
                        difficulties = ["fácil", "normal", "difícil"]
                        current = difficulties.index(self.difficulty)
                        self.difficulty = difficulties[(current + 1) % len(difficulties)]
                        self.option_buttons[0].text = f"Dificuldade: {self.difficulty.capitalize()}"
                    elif i == 1:
                        self.sound_enabled = not self.sound_enabled
                        status = "Ligado" if self.sound_enabled else "Desligado"
                        self.option_buttons[1].text = f"Som: {status}"
                    elif i == 2:
                        self.fullscreen = not self.fullscreen
                        status = "Sim" if self.fullscreen else "Não"
                        self.option_buttons[2].text = f"Tela Cheia: {status}"
                        if self.fullscreen:
                            pygame.display.set_mode((GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT), pygame.FULLSCREEN)
                        else:
                            pygame.display.set_mode((GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT))
                    elif i == 3:
                        self.state = MenuState.MAIN_MENU
                        self.transition_alpha = 0
                        self.is_transitioning = True
        
        elif self.state in [MenuState.CONTROLS, MenuState.CREDITS]:
            self.state = MenuState.MAIN_MENU
            self.transition_alpha = 0
            self.is_transitioning = True
        
        return None
    
    def render(self):
        self.screen.fill((10, 10, 20))
        
        for particle in self.particles:
            color = (*particle.color, particle.alpha)
            size = particle.size
            surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, color, (size, size), size)
            self.screen.blit(surf, (int(particle.x), int(particle.y)))
        
        if self.state == MenuState.MAIN_MENU:
            self._render_main_menu()
        elif self.state == MenuState.CLASS_SELECT:
            self._render_class_select()
        elif self.state == MenuState.OPTIONS:
            self._render_options()
        elif self.state == MenuState.CONTROLS:
            self._render_controls()
        elif self.state == MenuState.CREDITS:
            self._render_credits()
        
        if self.is_transitioning:
            overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
            overlay.set_alpha(min(self.transition_alpha, 255))
            overlay.fill((0, 0, 0))
            self.screen.blit(overlay, (0, 0))
            if self.transition_alpha >= 255:
                self.is_transitioning = False
                self.transition_alpha = 0
        
        pygame.display.flip()
    
    def _render_main_menu(self):
        title_y = 100 + self.title_y_offset
        title_text = self.title_font.render("DRAGON'S MAZE", True, (255, 200, 50))
        title_rect = title_text.get_rect(center=(self.screen.get_width() // 2, title_y))
        
        shadow_text = self.title_font.render("DRAGON'S MAZE", True, (100, 70, 20))
        shadow_rect = shadow_text.get_rect(center=(self.screen.get_width() // 2 + 3, title_y + 3))
        self.screen.blit(shadow_text, shadow_rect)
        self.screen.blit(title_text, title_rect)
        
        subtitle = self.subtitle_font.render("Sucessor Espiritual de Dragon Crystal", True, (200, 200, 200))
        subtitle_rect = subtitle.get_rect(center=(self.screen.get_width() // 2, title_y + 40))
        self.screen.blit(subtitle, subtitle_rect)
        
        dragon_y = 160
        for i, line in enumerate(self.dragon_art):
            dragon_text = self.small_font.render(line, True, (150, 150, 150))
            dragon_rect = dragon_text.get_rect(center=(self.screen.get_width() // 2, dragon_y + i * 15))
            self.screen.blit(dragon_text, dragon_rect)
        
        for button in self.buttons:
            button.render(self.screen, self.button_font)
        
        version_text = self.small_font.render("v1.0 - DeepSeek Studios", True, (100, 100, 100))
        self.screen.blit(version_text, (10, self.screen.get_height() - 25))
    
    def _render_class_select(self):
        title = self.title_font.render("ESCOLHA SUA CLASSE", True, (255, 200, 50))
        title_rect = title.get_rect(center=(self.screen.get_width() // 2, 60))
        self.screen.blit(title, title_rect)
        
        for i, (class_id, class_data) in enumerate(CLASSES.items()):
            if i >= len(self.class_buttons):
                break
            
            button = self.class_buttons[i]
            x, y, w, h = button.rect.x, button.rect.y, button.rect.width, button.rect.height
            
            is_selected = self.selected_class == class_id
            border_color = (255, 200, 50) if is_selected else (60, 60, 80)
            bg_color = (50, 50, 70) if is_selected else (30, 30, 40)
            
            pygame.draw.rect(self.screen, bg_color, button.rect, border_radius=10)
            pygame.draw.rect(self.screen, border_color, button.rect, 3, border_radius=10)
            
            symbol_text = self.title_font.render(class_data.symbol, True, class_data.color)
            symbol_rect = symbol_text.get_rect(center=(x + w // 2, y + 50))
            self.screen.blit(symbol_text, symbol_rect)
            
            name_text = self.button_font.render(class_data.name, True, (255, 255, 255))
            name_rect = name_text.get_rect(center=(x + w // 2, y + 100))
            self.screen.blit(name_text, name_rect)
            
            stats = class_data.stats
            stat_texts = [
                f"HP: {stats['hp']}  MP: {stats['mp']}",
                f"ATK: {stats['attack']}  DEF: {stats['defense']}",
                f"INT: {stats['intelligence']}  SORT: {stats['luck']}",
            ]
            for j, stat_text in enumerate(stat_texts):
                stat_render = self.small_font.render(stat_text, True, (200, 200, 200))
                stat_rect = stat_render.get_rect(center=(x + w // 2, y + 130 + j * 20))
                self.screen.blit(stat_render, stat_rect)
        
        if self.selected_class:
            class_data = CLASSES[self.selected_class]
            desc_text = self.description_font.render(class_data.description, True, (200, 200, 200))
            desc_rect = desc_text.get_rect(center=(self.screen.get_width() // 2, 430))
            self.screen.blit(desc_text, desc_rect)
            
            confirm_rect = pygame.Rect(self.screen.get_width() // 2 - 100, 460, 200, 50)
            pygame.draw.rect(self.screen, (50, 150, 50), confirm_rect, border_radius=8)
            pygame.draw.rect(self.screen, (100, 255, 100), confirm_rect, 2, border_radius=8)
            
            confirm_text = self.button_font.render("COMEÇAR", True, (255, 255, 255))
            confirm_rect2 = confirm_text.get_rect(center=confirm_rect.center)
            self.screen.blit(confirm_text, confirm_rect2)
        
        inst_text = self.small_font.render("ESC: Voltar | Clique na classe e depois em COMEÇAR", True, (150, 150, 150))
        self.screen.blit(inst_text, (self.screen.get_width() // 2 - inst_text.get_width() // 2, 530))
    
    def _render_options(self):
        title = self.title_font.render("OPÇÕES", True, (255, 200, 50))
        title_rect = title.get_rect(center=(self.screen.get_width() // 2, 100))
        self.screen.blit(title, title_rect)
        
        for button in self.option_buttons:
            button.render(self.screen, self.button_font)
        
        inst_text = self.small_font.render("ESC: Voltar", True, (150, 150, 150))
        self.screen.blit(inst_text, (self.screen.get_width() // 2 - inst_text.get_width() // 2, 500))
    
    def _render_controls(self):
        title = self.title_font.render("CONTROLES", True, (255, 200, 50))
        title_rect = title.get_rect(center=(self.screen.get_width() // 2, 80))
        self.screen.blit(title, title_rect)
        
        controls = [
            ("WASD / Setas", "Mover personagem"),
            ("1-8", "Lançar magias"),
            ("E", "Usar escadas"),
            ("I", "Abrir inventário"),
            ("Mouse", "Selecionar itens"),
            ("F1", "Salvar jogo"),
            ("F2", "Carregar jogo"),
            ("F5", "Quick Save"),
            ("ESC", "Menu / Sair"),
            ("", ""),
            ("No Inventário:", ""),
            ("E", "Equipar item"),
            ("U", "Usar item"),
            ("D", "Dropar item"),
        ]
        
        y = 180
        for key, action in controls:
            if not key and not action:
                y += 10
                continue
            color = (255, 200, 50) if "No" in key else (255, 255, 100)
            key_text = self.button_font.render(f"{key}:", True, color)
            action_text = self.button_font.render(action, True, (200, 200, 200))
            
            key_x = self.screen.get_width() // 2 - 200
            action_x = self.screen.get_width() // 2 + 20
            
            self.screen.blit(key_text, (key_x, y))
            self.screen.blit(action_text, (action_x, y))
            y += 35
        
        inst_text = self.small_font.render("Clique para voltar", True, (150, 150, 150))
        self.screen.blit(inst_text, (self.screen.get_width() // 2 - inst_text.get_width() // 2, 550))
    
    def _render_credits(self):
        title = self.title_font.render("CRÉDITOS", True, (255, 200, 50))
        title_rect = title.get_rect(center=(self.screen.get_width() // 2, 80))
        self.screen.blit(title, title_rect)
        
        credits = [
            "DRAGON'S MAZE",
            "Sucessor Espiritual de Dragon Crystal",
            "",
            "Desenvolvido com DeepSeek AI",
            "Engine: Python + Pygame",
            "",
            "Inspirado no clássico:",
            "Dragon Crystal (Sega Master System, 1990)",
            "",
            "Agradecimentos especiais:",
            "Comunidade Roguelike",
            "Fãs de Dragon Crystal",
            "",
            "Obrigado por jogar! 🐉",
        ]
        
        y = 180
        for line in credits:
            if not line:
                y += 10
                continue
            if line.startswith("DRAGON"):
                color = (255, 200, 50)
                font = self.subtitle_font
            elif line.startswith("Desenvolvido"):
                color = (100, 200, 255)
                font = self.button_font
            else:
                color = (200, 200, 200)
                font = self.small_font
            
            text = font.render(line, True, color)
            text_rect = text.get_rect(center=(self.screen.get_width() // 2, y))
            self.screen.blit(text, text_rect)
            y += 30
        
        inst_text = self.small_font.render("Clique para voltar", True, (150, 150, 150))
        self.screen.blit(inst_text, (self.screen.get_width() // 2 - inst_text.get_width() // 2, 550))
    
    def get_class_stats(self) -> Optional[dict]:
        if self.selected_class and self.selected_class in CLASSES:
            return CLASSES[self.selected_class].stats
        return None

# ===========================================
# ... CONTINUA NA PRÓXIMA MENSAGEM ...
# ===========================================
# SAVE SYSTEM
# ===========================================
@dataclass
class SaveData:
    version: str = "1.0"
    timestamp: str = ""
    play_time: float = 0.0
    player_name: str = "Hero"
    player_class: str = "warrior"
    player_level: int = 1
    player_exp: int = 0
    player_exp_to_level: int = 50
    player_hp: int = 100
    player_max_hp: int = 100
    player_mp: int = 30
    player_max_mp: int = 30
    player_attack: int = 10
    player_defense: int = 5
    player_intelligence: int = 5
    player_luck: int = 5
    player_hunger: float = 100.0
    player_gold: int = 0
    player_x: int = 0
    player_y: int = 0
    player_floor: int = 1
    inventory_slots: List = field(default_factory=list)
    equipment_slots: Dict[str, str] = field(default_factory=dict)
    learned_spells: List[int] = field(default_factory=lambda: [1, 2, 4])
    difficulty: str = "normal"
    enemies_defeated: int = 0
    explored_map: List = field(default_factory=list)

class SaveSystem:
    def __init__(self):
        self.encryption_key = "Dr4g0nM4z3_2024"
    
    def save_game(self, game_instance, slot_number: int = 0) -> bool:
        try:
            player = game_instance.player
            save_data = SaveData()
            
            save_data.timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
            save_data.play_time = game_instance.play_time
            save_data.player_name = player.name
            save_data.player_class = player.class_name
            save_data.player_level = player.level
            save_data.player_exp = player.exp
            save_data.player_exp_to_level = player.exp_to_level
            save_data.player_hp = player.hp
            save_data.player_max_hp = player.max_hp
            save_data.player_mp = player.mp
            save_data.player_max_mp = player.max_mp
            save_data.player_attack = player.attack
            save_data.player_defense = player.defense
            save_data.player_intelligence = player.intelligence
            save_data.player_luck = player.luck
            save_data.player_hunger = player.hunger
            save_data.player_gold = player.gold
            save_data.player_x = player.x
            save_data.player_y = player.y
            save_data.player_floor = player.floor
            save_data.learned_spells = player.learned_spells.copy()
            save_data.difficulty = getattr(game_instance, 'difficulty', 'normal')
            save_data.enemies_defeated = getattr(game_instance, 'enemies_defeated', 0)
            
            if hasattr(player, 'inventory'):
                save_data.inventory_slots = []
                for slot in player.inventory.slots:
                    if slot:
                        save_data.inventory_slots.append({'item_id': slot.item_id, 'quantity': slot.quantity})
                    else:
                        save_data.inventory_slots.append(None)
            
            if hasattr(player, 'equipment'):
                save_data.equipment_slots = {}
                for slot_type, item_id in player.equipment.slots.items():
                    if item_id:
                        save_data.equipment_slots[slot_type.name] = item_id
            
            if hasattr(game_instance, 'fow') and game_instance.fow:
                save_data.explored_map = game_instance.fow.explored.tolist()
            
            json_data = json.dumps(asdict(save_data), indent=2)
            encoded = base64.b64encode(zlib.compress(json_data.encode('utf-8'))).decode('ascii')
            
            filepath = f"save_slot_{slot_number}.sav" if slot_number > 0 else "auto_save.sav"
            with open(filepath, 'w') as f:
                f.write(encoded)
            
            return True
        except Exception as e:
            print(f"Erro ao salvar: {e}")
            return False
    
    def load_game(self, slot_number: int = 0) -> Optional[SaveData]:
        try:
            filepath = f"save_slot_{slot_number}.sav" if slot_number > 0 else "auto_save.sav"
            if not os.path.exists(filepath):
                return None
            
            with open(filepath, 'r') as f:
                encoded = f.read()
            
            json_data = zlib.decompress(base64.b64decode(encoded.encode('ascii'))).decode('utf-8')
            data = json.loads(json_data)
            
            save_data = SaveData()
            for key, value in data.items():
                if hasattr(save_data, key):
                    setattr(save_data, key, value)
            
            return save_data
        except Exception as e:
            print(f"Erro ao carregar: {e}")
            return None
    
    def delete_save(self, slot_number: int) -> bool:
        try:
            filepath = f"save_slot_{slot_number}.sav"
            if os.path.exists(filepath):
                os.remove(filepath)
            return True
        except:
            return False
    
    def get_save_info(self, slot_number: int = 0) -> Optional[Dict]:
        try:
            filepath = f"save_slot_{slot_number}.sav" if slot_number > 0 else "auto_save.sav"
            if not os.path.exists(filepath):
                return None
            
            with open(filepath, 'r') as f:
                encoded = f.read()
            
            json_data = zlib.decompress(base64.b64decode(encoded.encode('ascii'))).decode('utf-8')
            data = json.loads(json_data)
            
            return {
                'player_name': data.get('player_name', 'Hero'),
                'player_class': data.get('player_class', 'warrior'),
                'player_level': data.get('player_level', 1),
                'player_floor': data.get('player_floor', 1),
                'play_time': data.get('play_time', 0),
                'timestamp': data.get('timestamp', 'Desconhecido'),
            }
        except:
            return None

# ===========================================
# ... CONTINUA NA PRÓXIMA MENSAGEM ...
# ===========================================
# GAME PRINCIPAL - DRAGON'S MAZE
# ===========================================
class DragonsMaze:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT))
        pygame.display.set_caption("Dragon's Maze - Sucessor Espiritual de Dragon Crystal")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Menu
        self.menu = MainMenu(self.screen)
        self.game_started = False
        self.state = GameState.PLAYER_TURN
        
        # Save system
        self.save_system = SaveSystem()
        self.save_menu_open = False
        self.is_saving = True
        self.selected_save_slot = -1
        self.play_time = 0.0
        self.start_time = 0.0
        
        # Stats
        self.enemies_defeated = 0
        self.total_gold_earned = 0
        self.difficulty = "normal"
        
        # Sistemas (inicializados depois)
        self.dungeon_gen = None
        self.game_map = None
        self.player = None
        self.enemies = []
        self.items = []
        self.fow = None
        self.combat = CombatSystem()
        self.renderer = None
        self.magic_system = MagicSystem()
        self.inventory_open = False
        self.camera_x = 0
        self.camera_y = 0
    
    def _init_game(self, class_stats: dict, class_name: str = "warrior"):
        """Inicializa o jogo com a classe escolhida"""
        self.dungeon_gen = DungeonGenerator(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT)
        self.game_map = self.dungeon_gen.generate(1)
        
        self.player = Player(
            x=0, y=0,
            hp=class_stats.get("hp", 100),
            max_hp=class_stats.get("hp", 100),
            mp=class_stats.get("mp", 30),
            max_mp=class_stats.get("mp", 30),
            attack=class_stats.get("attack", 10),
            defense=class_stats.get("defense", 5)
        )
        self.player.intelligence = class_stats.get("intelligence", 5)
        self.player.luck = class_stats.get("luck", 5)
        self.player.class_name = class_name
        self.player.learned_spells = [1, 2, 3, 4] if class_name == "mage" else [1, 2, 4]
        
        self.enemies = []
        self.items = []
        
        self.fow = FogOfWar(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT, GameConfig.FOV_RADIUS)
        self.combat = CombatSystem()
        self.renderer = Renderer(self.screen)
        self.magic_system = MagicSystem()
        
        self.player.inventory = Inventory(30)
        self.player.equipment = EquipmentSlots()
        
        self.start_time = pygame.time.get_ticks()
        self.play_time = 0.0
        
        self._init_floor()
        self.game_started = True
        self.combat.log.append(f"🐉 Bem-vindo à Dragon's Maze, {class_name.capitalize()}!")
    
    def _load_game_from_save(self, save_data: SaveData):
        """Carrega um jogo salvo"""
        self.dungeon_gen = DungeonGenerator(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT)
        self.game_map = self.dungeon_gen.generate(save_data.player_floor)
        
        self.player = Player(
            x=save_data.player_x, y=save_data.player_y,
            hp=save_data.player_hp, max_hp=save_data.player_max_hp,
            mp=save_data.player_mp, max_mp=save_data.player_max_mp,
            attack=save_data.player_attack, defense=save_data.player_defense
        )
        self.player.name = save_data.player_name
        self.player.level = save_data.player_level
        self.player.exp = save_data.player_exp
        self.player.exp_to_level = save_data.player_exp_to_level
        self.player.intelligence = save_data.player_intelligence
        self.player.luck = save_data.player_luck
        self.player.hunger = save_data.player_hunger
        self.player.gold = save_data.player_gold
        self.player.floor = save_data.player_floor
        self.player.class_name = save_data.player_class
        self.player.learned_spells = save_data.learned_spells
        
        self.enemies = []
        self.items = []
        
        self.fow = FogOfWar(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT, GameConfig.FOV_RADIUS)
        if save_data.explored_map:
            self.fow.explored = np.array(save_data.explored_map, dtype=bool)
        
        self.combat = CombatSystem()
        self.renderer = Renderer(self.screen)
        self.magic_system = MagicSystem()
        
        self.player.inventory = Inventory(30)
        self.player.equipment = EquipmentSlots()
        
        for i, slot_data in enumerate(save_data.inventory_slots):
            if slot_data and i < 30:
                self.player.inventory.slots[i] = InventorySlot(slot_data['item_id'], slot_data['quantity'])
        
        for slot_name, item_id in save_data.equipment_slots.items():
            try:
                slot_type = ItemType[slot_name]
                self.player.equipment.slots[slot_type] = item_id
            except:
                pass
        
        self._apply_equipment_effects()
        
        self.enemies_defeated = save_data.enemies_defeated
        self.difficulty = save_data.difficulty
        self.play_time = save_data.play_time
        self.start_time = pygame.time.get_ticks()
        
        self._init_floor()
        self.fow.update(self.player.x, self.player.y, self.game_map)
        self._update_camera()
        
        self.game_started = True
        self.state = GameState.PLAYER_TURN
        self.combat.log.append("📂 Jogo carregado com sucesso!")
    
    def _init_floor(self):
        """Inicializa um andar"""
        self.game_map = self.dungeon_gen.generate(self.player.floor)
        
        if self.dungeon_gen.rooms:
            start_room = self.dungeon_gen.rooms[0]
            if self.player.x == 0 and self.player.y == 0:
                self.player.x = start_room['x'] + start_room['w'] // 2
                self.player.y = start_room['y'] + start_room['h'] // 2
        
        self.enemies.clear()
        self.items.clear()
        
        num_enemies = 5 + self.player.floor * 3
        for _ in range(num_enemies):
            for _ in range(50):
                x = random.randint(1, GameConfig.MAP_WIDTH - 2)
                y = random.randint(1, GameConfig.MAP_HEIGHT - 2)
                
                if (self.game_map[y][x] == TileType.FLOOR.value and
                    abs(x - self.player.x) > 5 and abs(y - self.player.y) > 5):
                    
                    enemy_types = [
                        {"name": "Slime", "symbol": "s", "color": (100, 255, 100), "hp": 15, "atk": 3, "def": 1},
                        {"name": "Morcego", "symbol": "b", "color": (150, 100, 150), "hp": 12, "atk": 5, "def": 0},
                        {"name": "Goblin", "symbol": "g", "color": (0, 200, 0), "hp": 25, "atk": 6, "def": 2},
                        {"name": "Esqueleto", "symbol": "S", "color": (200, 200, 200), "hp": 35, "atk": 8, "def": 3},
                    ]
                    
                    available = enemy_types[:min(self.player.floor + 2, len(enemy_types))]
                    template = random.choice(available)
                    
                    level = self.player.floor + random.randint(0, 2)
                    hp_mult = 1 + (level - 1) * 0.3
                    
                    enemy = Entity(
                        x=x, y=y,
                        symbol=template["symbol"],
                        color=template["color"],
                        name=template["name"],
                        hp=int(template["hp"] * hp_mult),
                        max_hp=int(template["hp"] * hp_mult),
                        attack=template["atk"] + level,
                        defense=template["def"] + level // 2,
                        level=level
                    )
                    self.enemies.append(enemy)
                    break
        
        num_items = 5 + random.randint(0, 5)
        item_ids = list(ITEM_DATABASE.keys())
        for _ in range(num_items):
            for _ in range(50):
                x = random.randint(1, GameConfig.MAP_WIDTH - 2)
                y = random.randint(1, GameConfig.MAP_HEIGHT - 2)
                
                if self.game_map[y][x] == TileType.FLOOR.value:
                    item_id = random.choice(item_ids)
                    item_data = ITEM_DATABASE[item_id]
                    
                    # Criar um objeto Item simplificado para o chão
                    ground_item = type('GroundItem', (), {
                        'x': x, 'y': y,
                        'symbol': item_data.symbol,
                        'color': item_data.color,
                        'name': item_data.name,
                        'item_id': item_id,
                        'item_type': item_data.item_type.value
                    })()
                    self.items.append(ground_item)
                    break
        
        self.fow = FogOfWar(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT, GameConfig.FOV_RADIUS)
        self.fow.update(self.player.x, self.player.y, self.game_map)
        self._update_camera()
    
    def _update_camera(self):
        view_w = GameConfig.SCREEN_WIDTH * 2 // 3 // GameConfig.TILE_SIZE
        view_h = GameConfig.SCREEN_HEIGHT // GameConfig.TILE_SIZE
        
        self.camera_x = self.player.x - view_w // 2
        self.camera_y = self.player.y - view_h // 2
        
        self.camera_x = max(0, min(self.camera_x, GameConfig.MAP_WIDTH - view_w))
        self.camera_y = max(0, min(self.camera_y, GameConfig.MAP_HEIGHT - view_h))
    
    def _apply_equipment_effects(self):
        """Aplica efeitos dos equipamentos"""
        self.player.attack = 10 + (self.player.level - 1) * 3
        self.player.defense = 5 + (self.player.level - 1) * 2
        
        effects = self.player.equipment.get_total_effects()
        if "attack" in effects:
            self.player.attack += effects["attack"]
        if "defense" in effects:
            self.player.defense += effects["defense"]
        if "intelligence" in effects:
            self.player.intelligence += effects["intelligence"]
        if "luck" in effects:
            self.player.luck += effects["luck"]
    
    def handle_magic_input(self, spell_num: int):
        """Processa input de magia"""
        if spell_num not in self.player.learned_spells:
            self.combat.log.append("❌ Você não aprendeu esta magia!")
            return
        
        spell = SPELLS[spell_num]
        
        targets = []
        if spell.spell_type in [SpellType.DAMAGE, SpellType.DEBUFF]:
            for enemy in self.enemies:
                if enemy.is_alive and self.fow.visible[enemy.y][enemy.x]:
                    distance = abs(enemy.x - self.player.x) + abs(enemy.y - self.player.y)
                    max_range = 5 + spell.aoe_radius
                    if distance <= max_range:
                        targets.append(enemy)
            
            if not targets:
                self.combat.log.append("❌ Nenhum inimigo ao alcance!")
                return
        
        success, message = self.magic_system.cast_spell(self.player, spell_num, targets, self.game_map)
        self.combat.log.append(message)
        
        if success:
            self.state = GameState.ENEMY_TURN
    
    def _move_player(self, dx: int, dy: int):
        """Move o jogador"""
        new_x = self.player.x + dx
        new_y = self.player.y + dy
        
        if not (0 <= new_x < GameConfig.MAP_WIDTH and 0 <= new_y < GameConfig.MAP_HEIGHT):
            return
        
        if self.game_map[new_y][new_x] == TileType.WALL.value:
            return
        
        for enemy in self.enemies:
            if enemy.is_alive and enemy.x == new_x and enemy.y == new_y:
                self.combat.attack(self.player, enemy)
                self.state = GameState.ENEMY_TURN
                return
        
        self.player.x = new_x
        self.player.y = new_y
        
        self.player.hunger = max(0, self.player.hunger - 0.3)
        if self.player.hunger <= 0:
            self.player.hp = max(0, self.player.hp - 1)
            if self.player.hp <= 0:
                self.player.is_alive = False
                self.state = GameState.GAME_OVER
        
        for item in self.items[:]:
            if item.x == self.player.x and item.y == self.player.y:
                self._pickup_item(item)
        
        self.fow.update(self.player.x, self.player.y, self.game_map)
        self._update_camera()
        self.state = GameState.ENEMY_TURN
    
    def _pickup_item(self, item):
        """Pega item do chão"""
        if hasattr(item, 'item_id'):
            if self.player.inventory.add_item(item.item_id, 1):
                self.items.remove(item)
                item_data = ITEM_DATABASE[item.item_id]
                self.combat.log.append(f"📦 {item_data.name} coletado!")
            else:
                self.combat.log.append("❌ Inventário cheio!")
    
    def _use_stairs(self):
        """Usa escadas"""
        tile = self.game_map[self.player.y][self.player.x]
        
        if tile == TileType.STAIRS_DOWN.value:
            self.player.floor += 1
            self._init_floor()
            self.combat.log.append(f"⬇️ Descendo para o andar {self.player.floor}...")
            self.save_system.save_game(self, 0)
        elif tile == TileType.STAIRS_UP.value and self.player.floor > 1:
            self.player.floor -= 1
            self._init_floor()
            self.combat.log.append(f"⬆️ Subindo para o andar {self.player.floor}...")
    
    def update_enemies(self):
        """Atualiza IA dos inimigos"""
        if self.state != GameState.ENEMY_TURN:
            return
        
        self.magic_system.update_effects()
        self.magic_system.particles.update()
        
        pathfinder = Pathfinding(self.game_map)
        
        for enemy in self.enemies:
            if not enemy.is_alive:
                continue
            
            dist = abs(enemy.x - self.player.x) + abs(enemy.y - self.player.y)
            
            if dist <= 8 and self.fow.visible[enemy.y][enemy.x]:
                if dist <= 1:
                    self.combat.attack(enemy, self.player)
                    if not self.player.is_alive:
                        self.state = GameState.GAME_OVER
                        return
                else:
                    path = pathfinder.find_path((enemy.x, enemy.y), (self.player.x, self.player.y), 10)
                    if path and len(path) > 0:
                        next_pos = path[0]
                        
                        blocked = False
                        for other in self.enemies:
                            if other.is_alive and other != enemy and other.x == next_pos[0] and other.y == next_pos[1]:
                                blocked = True
                                break
                        
                        if not blocked and not (next_pos[0] == self.player.x and next_pos[1] == self.player.y):
                            enemy.x, enemy.y = next_pos
            else:
                if random.random() < 0.3:
                    dx = random.choice([-1, 0, 1])
                    dy = random.choice([-1, 0, 1])
                    nx, ny = enemy.x + dx, enemy.y + dy
                    
                    if (0 <= nx < GameConfig.MAP_WIDTH and 0 <= ny < GameConfig.MAP_HEIGHT and
                        self.game_map[ny][nx] != TileType.WALL.value and
                        not (nx == self.player.x and ny == self.player.y)):
                        
                        blocked = any(e.is_alive and e != enemy and e.x == nx and e.y == ny for e in self.enemies)
                        if not blocked:
                            enemy.x, enemy.y = nx, ny
        
        self.player.mp = min(self.player.max_mp, self.player.mp + 1)
        self.state = GameState.PLAYER_TURN
    
    def run(self):
        """Loop principal do jogo"""
        while self.running:
            dt = self.clock.tick(GameConfig.FPS)
            
            if self.game_started and self.start_time > 0:
                self.play_time = (pygame.time.get_ticks() - self.start_time) / (1000 * 60 * 60)
            
            if not self.game_started:
                self.menu.update(dt)
                
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                        break
                    
                    action = self.menu.handle_event(event)
                    
                    if action == "quit":
                        self.running = False
                        break
                    elif action == "continue":
                        self._show_load_menu()
                    elif action and action.startswith("start_"):
                        class_name = action.replace("start_", "")
                        class_stats = CLASSES[class_name].stats
                        self._init_game(class_stats, class_name)
                        self.save_system.save_game(self, 0)
                
                self.menu.render()
                continue
            
            if self.save_menu_open:
                self._handle_save_menu()
                continue
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    if self.player and self.player.is_alive:
                        self.save_system.save_game(self, 0)
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.save_system.save_game(self, 0)
                        self.game_started = False
                        self.state = GameState.PLAYER_TURN
                    elif event.key == pygame.K_F1:
                        self._open_save_menu(is_saving=True)
                    elif event.key == pygame.K_F2:
                        self._show_load_menu()
                    elif event.key == pygame.K_F5:
                        if self.save_system.save_game(self, 0):
                            self.combat.log.append("💾 Quick Save realizado!")
                    elif event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]:
                        self.handle_magic_input(int(event.unicode) if event.unicode.isdigit() else 
                                                {pygame.K_1:1, pygame.K_2:2, pygame.K_3:3, pygame.K_4:4}[event.key])
                    elif event.key == pygame.K_e:
                        self._use_stairs()
                    elif event.key == pygame.K_i:
                        self.inventory_open = not self.inventory_open
                        self.state = GameState.INVENTORY if self.inventory_open else GameState.PLAYER_TURN
            
            if self.state == GameState.GAME_OVER:
                self._render_game_over()
                continue
            
            if self.inventory_open:
                self._render_inventory_screen()
                continue
            
            if self.state == GameState.PLAYER_TURN:
                keys = pygame.key.get_pressed()
                dx, dy = 0, 0
                
                if keys[pygame.K_w] or keys[pygame.K_UP]: dy = -1
                elif keys[pygame.K_s] or keys[pygame.K_DOWN]: dy = 1
                elif keys[pygame.K_a] or keys[pygame.K_LEFT]: dx = -1
                elif keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx = 1
                
                if dx != 0 or dy != 0:
                    self._move_player(dx, dy)
            
            self.update_enemies()
            
            combat_log = self.combat.get_log()
            
            self.renderer.render(
                self.game_map, self.player, self.enemies, self.items,
                self.fow, combat_log, self.camera_x, self.camera_y,
                self.magic_system.particles
            )
        
        pygame.quit()
        sys.exit()
    
    def _show_load_menu(self):
        """Mostra menu de carregar jogo"""
        saves = []
        for i in range(4):
            info = self.save_system.get_save_info(i)
            saves.append({
                'slot': i,
                'name': 'Auto-Save' if i == 0 else f'Slot {i}',
                'exists': info is not None,
                'info': info
            })
        
        # Aqui você pode implementar uma interface simples de load
        # Por simplicidade, vamos carregar o slot 0 (auto-save)
        save_data = self.save_system.load_game(0)
        if save_data:
            self._load_game_from_save(save_data)
        else:
            print("Nenhum save encontrado!")
    
    def _open_save_menu(self, is_saving: bool = True):
        """Abre menu de save"""
        self.save_menu_open = True
        self.is_saving = is_saving
        self.selected_save_slot = -1
    
    def _handle_save_menu(self):
        """Processa menu de save"""
        self.screen.fill((20, 20, 30))
        
        font = pygame.font.Font(None, 36)
        small_font = pygame.font.Font(None, 24)
        
        title_text = "💾 SALVAR JOGO" if self.is_saving else "📂 CARREGAR JOGO"
        title = font.render(title_text, True, (255, 200, 50))
        self.screen.blit(title, (self.screen.get_width()//2 - title.get_width()//2, 50))
        
        saves_info = []
        for i in range(4):
            info = self.save_system.get_save_info(i)
            saves_info.append({
                'slot': i,
                'name': 'Auto-Save' if i == 0 else f'Slot {i}',
                'info': info
            })
        
        y = 150
        for save in saves_info:
            color = (255, 255, 255) if save['info'] else (100, 100, 100)
            
            slot_text = font.render(save['name'], True, color)
            self.screen.blit(slot_text, (100, y))
            
            if save['info']:
                info_text = f"Nv.{save['info']['player_level']} {save['info']['player_class']} - Andar {save['info']['player_floor']}"
                info_render = small_font.render(info_text, True, color)
                self.screen.blit(info_render, (100, y + 30))
                
                time_text = f"Tempo: {save['info']['play_time']:.1f}h - {save['info']['timestamp']}"
                time_render = small_font.render(time_text, True, color)
                self.screen.blit(time_render, (100, y + 50))
            else:
                empty_text = small_font.render("(Vazio)", True, (80, 80, 80))
                self.screen.blit(empty_text, (100, y + 30))
            
            # Botão do slot
            slot_rect = pygame.Rect(50, y - 10, self.screen.get_width() - 100, 80)
            pygame.draw.rect(self.screen, (40, 40, 50), slot_rect, 2)
            
            y += 100
        
        inst_text = small_font.render("Clique no slot | ESC: Cancelar", True, (150, 150, 150))
        self.screen.blit(inst_text, (self.screen.get_width()//2 - inst_text.get_width()//2, self.screen.get_height() - 50))
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                self.save_menu_open = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.save_menu_open = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_y = event.pos[1]
                slot_index = (mouse_y - 140) // 100
                
                if 0 <= slot_index < 4:
                    if self.is_saving:
                        if self.save_system.save_game(self, slot_index):
                            self.combat.log.append(f"💾 Jogo salvo no slot {slot_index}!")
                            self.save_menu_open = False
                    else:
                        save_data = self.save_system.load_game(slot_index)
                        if save_data:
                            self._load_game_from_save(save_data)
                            self.save_menu_open = False
    
    def _render_game_over(self):
        """Renderiza tela de game over"""
        self.screen.fill((0, 0, 0))
        
        font = pygame.font.Font(None, 72)
        small_font = pygame.font.Font(None, 36)
        
        game_over_text = font.render("GAME OVER", True, (255, 50, 50))
        self.screen.blit(game_over_text, 
                        (self.screen.get_width()//2 - game_over_text.get_width()//2, 200))
        
        stats_text = [
            f"Andar alcançado: {self.player.floor}",
            f"Nível: {self.player.level}",
            f"Inimigos derrotados: {self.enemies_defeated}",
            f"Tempo de jogo: {self.play_time:.1f} horas",
        ]
        
        y = 300
        for text in stats_text:
            render = small_font.render(text, True, (200, 200, 200))
            self.screen.blit(render, (self.screen.get_width()//2 - render.get_width()//2, y))
            y += 40
        
        inst_text = small_font.render("ESC: Menu Principal", True, (150, 150, 150))
        self.screen.blit(inst_text, 
                        (self.screen.get_width()//2 - inst_text.get_width()//2, 450))
        
        pygame.display.flip()
        
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            self.game_started = False
            self.state = GameState.PLAYER_TURN
            self.player.is_alive = True
            self.player.hp = self.player.max_hp
    
    def _render_inventory_screen(self):
        """Renderiza tela de inventário simples"""
        self.renderer.render_map_only(
            self.game_map, self.player, self.enemies, self.items,
            self.fow, self.camera_x, self.camera_y
        )
        
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        font = pygame.font.Font(None, 28)
        small_font = pygame.font.Font(None, 22)
        
        title = font.render("🎒 INVENTÁRIO", True, (255, 200, 50))
        self.screen.blit(title, (50, 30))
        
        y = 80
        for i, slot in enumerate(self.player.inventory.slots):
            if slot and slot.item_data:
                item_data = slot.item_data
                text = f"{item_data.symbol} {item_data.name}"
                if slot.quantity > 1:
                    text += f" x{slot.quantity}"
                
                color = item_data.color
                render = small_font.render(text, True, color)
                self.screen.blit(render, (50, y))
                y += 25
        
        if y == 80:
            empty_text = small_font.render("Inventário vazio", True, (150, 150, 150))
            self.screen.blit(empty_text, (50, y))
        
        inst_text = small_font.render("I: Fechar | E: Equipar | U: Usar | D: Dropar", True, (150, 150, 150))
        self.screen.blit(inst_text, (50, self.screen.get_height() - 40))
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_i:
                    self.inventory_open = False
                    self.state = GameState.PLAYER_TURN

# ===========================================
# EXECUTAR O JOGO
# ===========================================
if __name__ == "__main__":
    game = DragonsMaze()
    game.run()