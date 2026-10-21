"""Generates lang/en_us.json and all recipes. Run: python3 tools/data/gen_data.py"""
import json
import os

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
ASSETS = os.path.join(REPO, 'src/main/resources/assets/tamagotchi')
DATA = os.path.join(REPO, 'src/main/resources/data/tamagotchi')

PETS = {
    'desert_dragon': ('Desert Dragon', 'Ember Roast', 'Hand it raw food or raw ore and it roasts or smelts it with a little puff of flame.'),
    'jungle_dragon': ('Jungle Dragon', 'Green Thumb', 'Makes the crops and saplings around it grow.'),
    'tide_dragon': ('Tide Dragon', 'Tide Blessing', "While you swim near it you get Water Breathing and Dolphin's Grace."),
    'frost_penguin': ('Frost Penguin', 'Frost Steps', 'While it follows you, water freezes under your feet. Belly-slides on snow and ice.'),
    'ember_pup': ('Ember Pup', 'Warm Heart', 'When you catch fire it gives you Fire Resistance. Swims through lava.'),
    'sculk_wisp': ('Sculk Wisp', 'Echo Sense', 'Sends out a sonar ping that makes hostile mobs nearby glow through walls.'),
    'void_kitten': ('Void Kitten', 'Item Magnet', 'Pulls dropped items nearby into its backpack, or teleports them to you.'),
    'pebble_golem': ('Pebble Golem', 'Ore Sniffer', 'Underground it sniffs out the best ore nearby and points a sparkle trail at it.'),
    'hex_toad': ('Hex Toad', 'Brew Buddy', 'When it is happy it brews you a random helpful potion effect now and then.'),
    'mimic': ('Mimic', 'Treasure Belly', 'Has 27 slots of belly storage (54 with a backpack) and coughs up little treasures.'),
}

ITEMS = {
    'tamagotchi_heart': ('Tamagotchi Heart', 'Use it on a wild pet to tame it.'),
    'tama_pager': ('Tama Pager', 'Right-click your pet for its needs, commands and backpack. Beeps when a pet needs care.'),
    'pet_brush': ('Pet Brush', 'Brush your pet to keep it clean and happy.'),
    'laser_pointer': ('Laser Pointer', 'Hold right-click: your pets chase the red dot!'),
    'squeaky_ball': ('Squeaky Ball', 'Throw it and your pet brings it back.'),
    'feather_wand': ('Feather Wand', 'Wave it near your pets to play with them.'),
    'pet_kibble': ('Pet Kibble', 'Every pet likes it. Also fills a food bowl.'),
    'fish_crackers': ('Fish Crackers', None),
    'dragon_fruit': ('Dragon Fruit', None),
    'ember_jerky': ('Ember Jerky', None),
    'rock_candy': ('Rock Candy', None),
    'glow_gummy': ('Glow Gummy', None),
    'golden_biscuit': ('Golden Biscuit', None),
    'tama_egg': ('Tama Egg', 'Fainted. Use it on a block to wake your pet up.'),
}

BLOCKS = {
    'pet_bed': 'Pet Bed', 'pet_basket': 'Pet Basket', 'dragon_nest': 'Dragon Nest', 'food_bowl': 'Food Bowl',
    'pet_bath': 'Pet Bath', 'bouncy_mushroom': 'Bouncy Mushroom', 'running_wheel': 'Running Wheel',
    'scratching_post': 'Scratching Post', 'pet_house': 'Pet House',
}

lang = {'itemGroup.tamagotchi': 'Tamagotchi'}
for pid, (name, talent, desc) in PETS.items():
    lang[f'entity.tamagotchi.{pid}'] = name
    lang[f'item.tamagotchi.{pid}_spawn_egg'] = f'{name} Spawn Egg'
    lang[f'talent.tamagotchi.{pid}'] = talent
    lang[f'talent.tamagotchi.{pid}.desc'] = desc
for iid, (name, tip) in ITEMS.items():
    lang[f'item.tamagotchi.{iid}'] = name
    if tip:
        lang[f'item.tamagotchi.{iid}.tooltip'] = tip
lang['item.tamagotchi.tama_egg.named'] = "%s's Egg"
for bid, name in BLOCKS.items():
    lang[f'block.tamagotchi.{bid}'] = name

lang.update({
    'tooltip.tamagotchi.favorite_of': 'Favorite treat of: %s',
    'message.tamagotchi.stay': '%s will stay here.',
    'message.tamagotchi.follow': '%s follows you again.',
    'message.tamagotchi.snack_stored': '%s tucked the golden apple into its snack pouch (%s). It will feed you when you are hurt!',
    'message.tamagotchi.full': '%s is full!',
    'message.tamagotchi.favorite': '%s loves this treat! ♥',
    'message.tamagotchi.tamed': '♥ %s trusts you now!',
    'message.tamagotchi.tamed_help': 'Right-click: pet it • Sneak + right-click with a chest: backpack • Sneak + right-click: stay / follow (takes a backpack off) • Golden apple: a snack for you when you are hurt • Tama Pager: needs, commands and backpack',
    'message.tamagotchi.got_pager': 'You got a Tama Pager! It beeps when your pet needs you.',
    'message.tamagotchi.need.hunger': '%s is hungry!',
    'message.tamagotchi.need.fun': '%s is bored!',
    'message.tamagotchi.need.energy': '%s is sleepy!',
    'message.tamagotchi.need.hygiene': '%s needs a bath!',
    'message.tamagotchi.need.hurt': '%s is hurt!',
    'message.tamagotchi.fainted': '%s fainted and curled up into its egg at %s %s %s. Use the egg to wake it up!',
    'message.tamagotchi.no_pet': 'No pet of yours nearby.',
    'message.tamagotchi.fed_you': '%s gave you a golden apple! (%s left)',
    'message.tamagotchi.too_sad': '%s is too sad to help right now...',
    'message.tamagotchi.talent.warm': '%s keeps you safe from the flames!',
    'message.tamagotchi.talent.ore': '%s sniffed out %s!',
    'message.tamagotchi.talent.brew': '%s brewed you %s!',
    'message.tamagotchi.talent.treasure': '%s coughed up a treasure!',
    'gui.tamagotchi.sit': 'Sit',
    'gui.tamagotchi.follow': 'Follow',
    'gui.tamagotchi.wander': 'Wander',
    'gui.tamagotchi.backpack': 'Backpack',
    'gui.tamagotchi.no_backpack_title': 'Backpack',
    'gui.tamagotchi.no_backpack': 'No backpack yet! Sneak + right-click your pet with a chest to give it one.',
    'gui.tamagotchi.talent': 'Talent',
    'gui.tamagotchi.mood.miserable': 'Miserable',
    'gui.tamagotchi.mood.sad': 'Sad',
    'gui.tamagotchi.mood.okay': 'Okay',
    'gui.tamagotchi.mood.happy': 'Happy',
    'gui.tamagotchi.mood.ecstatic': 'Ecstatic!',
    'gui.tamagotchi.need.hunger': 'Hunger: %s / 100',
    'gui.tamagotchi.need.fun': 'Fun: %s / 100',
    'gui.tamagotchi.need.energy': 'Energy: %s / 100',
    'gui.tamagotchi.need.hygiene': 'Hygiene: %s / 100',
})
lang.update({
    'advancements.tamagotchi.root.title': 'Tamagotchi',
    'advancements.tamagotchi.root.description': 'Get a Tamagotchi Heart. Rare pets hide in pyramids, temples, igloos, monuments and more...',
    'advancements.tamagotchi.first_friend.title': 'A New Best Friend',
    'advancements.tamagotchi.first_friend.description': 'Tame a pet with a Tamagotchi Heart',
    'advancements.tamagotchi.pager.title': 'Beep Beep!',
    'advancements.tamagotchi.pager.description': 'Get a Tama Pager to check on your pets',
    'advancements.tamagotchi.all_pets.title': "Gotta Pet 'Em All",
    'advancements.tamagotchi.all_pets.description': 'Tame all ten pets',
})
subs = os.path.join(REPO, 'tools/sfx/subtitles_en_us.json')
if os.path.exists(subs):
    lang.update(json.load(open(subs)))

os.makedirs(os.path.join(ASSETS, 'lang'), exist_ok=True)
with open(os.path.join(ASSETS, 'lang/en_us.json'), 'w') as f:
    json.dump(lang, f, indent=2, ensure_ascii=False)


# ------------------------------------------------------------------ recipes

def shaped(name, pattern, key, result, count=1):
    return name, {'type': 'minecraft:crafting_shaped', 'key': key, 'pattern': pattern,
                  'result': {'id': result, 'count': count} if count > 1 else {'id': result}}


def shapeless(name, ingredients, result, count=1):
    return name, {'type': 'minecraft:crafting_shapeless', 'ingredients': ingredients,
                  'result': {'id': result, 'count': count} if count > 1 else {'id': result}}


T = 'tamagotchi:'
RECIPES = [
    shaped('tamagotchi_heart', ['R R', 'RAR', ' R '], {'R': 'minecraft:red_dye', 'A': 'minecraft:amethyst_shard'}, T + 'tamagotchi_heart'),
    shaped('tama_pager', [' N ', 'NGN', 'NRN'], {'N': 'minecraft:iron_nugget', 'G': 'minecraft:glass_pane', 'R': 'minecraft:redstone'}, T + 'tama_pager'),
    shaped('pet_brush', ['WWW', ' S '], {'W': '#minecraft:wool', 'S': 'minecraft:stick'}, T + 'pet_brush'),
    shaped('laser_pointer', ['  R', ' I ', 'I  '], {'R': 'minecraft:redstone_torch', 'I': 'minecraft:iron_ingot'}, T + 'laser_pointer'),
    shaped('squeaky_ball', [' W ', 'WSW', ' W '], {'W': '#minecraft:wool', 'S': 'minecraft:slime_ball'}, T + 'squeaky_ball', 2),
    shaped('feather_wand', ['  F', ' SF', 'S  '], {'F': 'minecraft:feather', 'S': 'minecraft:stick'}, T + 'feather_wand'),
    shapeless('pet_kibble', ['minecraft:wheat', '#minecraft:meat'], T + 'pet_kibble', 4),
    shapeless('pet_kibble_from_fish', ['minecraft:wheat', '#minecraft:fishes'], T + 'pet_kibble', 4),
    shapeless('fish_crackers', ['minecraft:wheat', 'minecraft:cod'], T + 'fish_crackers', 3),
    shapeless('fish_crackers_from_salmon', ['minecraft:wheat', 'minecraft:salmon'], T + 'fish_crackers', 3),
    shapeless('dragon_fruit', ['minecraft:cactus', 'minecraft:sweet_berries', 'minecraft:sugar'], T + 'dragon_fruit', 2),
    shapeless('ember_jerky', ['minecraft:cooked_beef', 'minecraft:blaze_powder'], T + 'ember_jerky', 3),
    shapeless('ember_jerky_from_magma', ['minecraft:cooked_porkchop', 'minecraft:magma_cream'], T + 'ember_jerky', 3),
    shapeless('rock_candy', ['minecraft:sugar', 'minecraft:amethyst_shard', 'minecraft:stick'], T + 'rock_candy', 2),
    shapeless('glow_gummy', ['minecraft:glow_berries', 'minecraft:slime_ball', 'minecraft:sugar'], T + 'glow_gummy', 3),
    shapeless('golden_biscuit', ['minecraft:wheat', 'minecraft:gold_nugget', 'minecraft:gold_nugget', 'minecraft:honey_bottle'], T + 'golden_biscuit', 2),
    shaped('pet_bed', ['   ', 'WCW', 'PPP'], {'W': '#minecraft:wool', 'C': '#minecraft:wool_carpets', 'P': '#minecraft:planks'}, T + 'pet_bed'),
    shaped('pet_basket', ['B B', 'BWB', 'BBB'], {'B': 'minecraft:bamboo', 'W': '#minecraft:wool'}, T + 'pet_basket'),
    shaped('dragon_nest', ['H H', 'FEF', 'HHH'], {'H': 'minecraft:hay_block', 'F': 'minecraft:feather', 'E': 'minecraft:egg'}, T + 'dragon_nest'),
    shaped('food_bowl', ['C C', ' C '], {'C': 'minecraft:clay_ball'}, T + 'food_bowl'),
    shaped('pet_bath', ['P P', 'IWI', 'PPP'], {'P': '#minecraft:planks', 'I': 'minecraft:iron_ingot', 'W': 'minecraft:water_bucket'}, T + 'pet_bath'),
    shaped('bouncy_mushroom', ['RRR', 'SMS', ' M '], {'R': 'minecraft:red_mushroom_block', 'S': 'minecraft:slime_ball', 'M': 'minecraft:mushroom_stem'}, T + 'bouncy_mushroom'),
    shaped('running_wheel', ['SPS', 'PCP', 'SPS'], {'S': 'minecraft:stick', 'P': '#minecraft:planks', 'C': 'minecraft:copper_ingot'}, T + 'running_wheel'),
    shaped('scratching_post', [' C ', ' S ', 'CPC'], {'C': '#minecraft:wool_carpets', 'S': 'minecraft:string', 'P': '#minecraft:planks'}, T + 'scratching_post'),
    shaped('pet_house', [' B ', 'BPB', 'P P'], {'B': 'minecraft:bricks', 'P': '#minecraft:planks'}, T + 'pet_house'),
]
os.makedirs(os.path.join(DATA, 'recipe'), exist_ok=True)
for name, body in RECIPES:
    with open(os.path.join(DATA, 'recipe', name + '.json'), 'w') as f:
        json.dump(body, f, indent=2)
print('lang keys:', len(lang), 'recipes:', len(RECIPES))
