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
    'pebble_golem': ('Pebble Golem', 'Ore Sniffer', 'Sniffs out the best ore nearby, points a sparkle trail at it and makes it glow through the walls.'),
    'hex_toad': ('Hex Toad', 'Brew Buddy', 'When it is happy it brews you a random helpful potion effect now and then.'),
    'mimic': ('Mimic', 'Treasure Belly', 'Has 27 slots of belly storage (54 with a backpack) and coughs up little treasures.'),
}

ITEMS = {
    'tamagotchi_heart': ('Tamagotchi Heart', 'Use it on a wild pet to tame it.'),
    'tama_pager': ('Tama Pager', 'Right-click your pet: stay / follow. Use it in the air: screen of your nearest pet. Beeps when a pet needs care.'),
    'tamacon': ('Tamacon', 'Your guide to pets, care, toys and furniture. Right-click to read.'),
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
    'message.tamagotchi.snack_stored': '%s packed the golden apple into its backpack (%s). It brings you one when you are hurt!',
    'message.tamagotchi.snack_no_backpack': '%s needs a backpack to carry golden apples for you. Sneak + right-click it with a chest!',
    'message.tamagotchi.snack_full': "%s's backpack is full!",
    'message.tamagotchi.full': '%s is full!',
    'message.tamagotchi.favorite': '%s loves this treat! ♥',
    'message.tamagotchi.tamed': '♥ %s trusts you now!',
    'message.tamagotchi.tamed_help': 'Right-click: pet it • Sneak + right-click: pet screen and backpack • Sneak + right-click with a chest: backpack on, with shears: off • Tama Pager on it: stay / follow • Golden apples in its backpack: it feeds you when you are hurt • Craft a Tamacon to learn everything!',
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
    'gui.tamagotchi.tamacon.contents': 'Contents',
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
# ------------------------------------------------------------------ Tamacon (in-game guide)
FOUND = {
    'desert_dragon': 'desert pyramids (40%)', 'jungle_dragon': 'jungle temples (40%)', 'tide_dragon': 'ocean monuments (50%)',
    'frost_penguin': 'igloos (45%)', 'ember_pup': 'nether fortresses (30%)', 'sculk_wisp': 'ancient cities (50%)',
    'void_kitten': 'end cities (30%)', 'pebble_golem': 'trail ruins (35%) and mineshafts (8%)', 'hex_toad': 'swamp huts (45%)',
    'mimic': 'trial chambers (30%) and woodland mansions (60%)',
}
TREAT = {
    'desert_dragon': 'Dragon Fruit', 'jungle_dragon': 'Dragon Fruit', 'tide_dragon': 'Fish Crackers', 'frost_penguin': 'Fish Crackers',
    'ember_pup': 'Ember Jerky', 'sculk_wisp': 'Glow Gummy', 'void_kitten': 'Fish Crackers', 'pebble_golem': 'Rock Candy',
    'hex_toad': 'Glow Gummy', 'mimic': 'Golden Biscuit',
}
FIGHT = {
    'desert_dragon': 'a puff of fire that sets enemies alight', 'jungle_dragon': 'a poison bite', 'tide_dragon': 'a bubble blast that knocks enemies back',
    'frost_penguin': 'a volley of snowballs that slows enemies', 'ember_pup': 'a burning bite', 'sculk_wisp': 'a sonic chirp',
    'void_kitten': 'a blink strike: it teleports next to the enemy', 'pebble_golem': 'a heavy ground slam', 'hex_toad': 'a hex tongue that weakens',
    'mimic': 'a big chomp',
}
EXTRA = {
    'desert_dragon': 'It is a dragon, so it flies after you when that is faster, and sometimes just for fun. Sand and sun make it happy.',
    'jungle_dragon': 'It flies after you when that is faster, and sometimes just for fun. Leaf wings, a hibiscus flower and a very green thumb.',
    'tide_dragon': 'It swims as well as it flies and never needs air under water. Bring it along when you dive!',
    'frost_penguin': 'On snow and ice it belly-slides. It never gets cold, but it loves a warm campfire anyway.',
    'ember_pup': 'Fire and lava cannot hurt it, and it swims through lava like other pets swim through water.',
    'sculk_wisp': 'It floats instead of walking and is so quiet that sculk sensors never notice it.',
    'void_kitten': 'If it gets lost it simply teleports back to you.',
    'pebble_golem': 'Slow but very tough. The ore it sniffs out glows through the walls for twenty seconds.',
    'hex_toad': 'It hops everywhere and loves rain and swamps.',
    'mimic': 'A living chest! Its belly already holds 27 items without a backpack, 54 with one.',
}
TAMACON = {
    'welcome': ('Welcome!', 'The Tamacon knows everything about the ten rare pets of this world and how to make them happy.\n\n'
                'Use the arrows, your mouse wheel or the arrow keys to turn the pages, and click a chapter on the contents page to jump there.\n\n'
                'Tip: craft a Tamagotchi Heart first (red dye and an amethyst shard). You need it to tame a pet.'),
    'finding': ('Finding pets', 'Pets live in structures, but not in every one: each structure rolls once whether a pet lives there.\n\n'
                'Desert pyramid: Desert Dragon. Jungle temple: Jungle Dragon. Ocean monument: Tide Dragon. Igloo: Frost Penguin. '
                'Nether fortress: Ember Pup. Ancient city: Sculk Wisp. End city: Void Kitten. Trail ruins and mineshafts: Pebble Golem. '
                'Swamp hut: Hex Toad. Trial chambers and woodland mansions: Mimic.\n\n'
                'Wild pets stay near their home and never despawn. Look inside and around the building. The cute ones run away when hit, '
                'the Ember Pup, Sculk Wisp and Mimic bite back.\n\n'
                'Hold a Tamagotchi Heart and wild pets come closer. Right-click one with the heart to tame it.'),
    'controls': ('Controls', 'Right-click with an empty hand: pet it.\n\n'
                 'Sneak + right-click with an empty hand: open the pet screen with its needs, mood, backpack and the Sit / Follow / Wander buttons.\n\n'
                 'Sneak + right-click with a chest: put a backpack on.\n\n'
                 'Sneak + right-click with shears: take the backpack off. Careful: everything inside spills out!\n\n'
                 'Right-click with the Tama Pager: Sit / Stay or Follow.\n\n'
                 'Right-click with food or its favorite treat: feed it. With a golden apple: it goes into its backpack. '
                 'With the Pet Brush: groom it. Leads and name tags work like on any pet.'),
    'care': ('Taking care', 'Every pet has four needs from 0 to 100: Hunger, Fun, Energy and Hygiene. Together they make its mood: '
             'Ecstatic, Happy, Okay, Sad or Miserable.\n\n'
             'Hunger: food, its favorite treat or a Food Bowl.\n'
             'Fun: petting, toys, other pets, the Bouncy Mushroom, the Running Wheel and the Scratching Post.\n'
             'Energy: sleeping in a Pet Bed, Basket or Dragon Nest, or sitting.\n'
             'Hygiene: the Pet Brush or a filled Pet Bath.\n\n'
             'Happy pets use their talent, sad ones do not, and miserable pets refuse to fight. '
             'Bond (the hearts on the screen) grows with every bit of care and makes talents recharge faster.\n\n'
             'Needs only change while the pet is loaded, so a pet left at home waits for you.'),
    'pager': ('Tama Pager', 'You get a free Tama Pager when you tame your first pet, and you can craft more.\n\n'
              'Right-click your pet with it to tell it to stay or to follow you. Use it in the air to open the screen of your nearest pet '
              '(up to 64 blocks away).\n\n'
              'While it is in your inventory it beeps when a pet is hungry, bored, sleepy, dirty or hurt.'),
    'backpack': ('Backpack', 'Sneak + right-click your pet with a chest and it wears a backpack with 27 slots. '
                 'Open it with sneak + right-click (empty hand) and put anything in.\n\n'
                 'Golden apples in the backpack are special: when your health gets low, your pet runs to you and feeds you one. '
                 'Right-click your pet with a golden apple to pack it straight into the backpack.\n\n'
                 'Food in the backpack is the pet\'s own lunch box: when it gets hurt in a fight, it eats from it.\n\n'
                 'Sneak + right-click with shears takes the backpack off and everything spills out.'),
    'combat': ('Fighting', 'Your pet fights with you like a wolf: it attacks whatever attacks you and whatever you attack, each pet in its own style.\n\n'
               'Below a third of its health it stops fighting, runs to you and eats food from its backpack to heal.\n\n'
               'A tamed pet never dies. It faints and curls up into a Tama Egg that keeps its name, needs, bond and backpack. '
               'Use the egg on a block to wake it up again.'),
    'flying': ('Flying dragons', 'The Desert, Jungle and Tide Dragon have wings and use them. When you are far away or up on a ledge, '
               'a dragon simply flies after you, and now and then it takes off just for the joy of it.\n\n'
               'Dragons never take fall damage. Tell one to stay with the Tama Pager and it stays on the ground.'),
    'food': ('Food', 'Pet Kibble: every pet likes it. It also fills a Food Bowl.\n\n'
             'Favorite treats feed more, heal more and give bond: Dragon Fruit (dragons), Fish Crackers (Tide Dragon, Frost Penguin, Void Kitten), '
             'Ember Jerky (Ember Pup), Rock Candy (Pebble Golem), Glow Gummy (Sculk Wisp, Hex Toad) and the Golden Biscuit (Mimic).\n\n'
             'Pets also eat their usual food: meat, fish, fruit or vegetables depending on the pet. Everything is craftable.'),
    'toys': ('Toys', 'Laser Pointer: hold right-click and your pets chase the red dot and pounce on it.\n\n'
             'Squeaky Ball: throw it and your pet fetches it back to you.\n\n'
             'Feather Wand: wave it near your pets and they jump and swipe at it.\n\n'
             'Pet Brush: grooming fills Hygiene. Pets also play with each other when they meet.'),
    'furniture': ('Furniture', 'Pets use furniture by themselves when they need it.\n\n'
                  'Pet Bed, Pet Basket, Dragon Nest: they sleep in them at night or when tired.\n'
                  'Food Bowl: right-click it with food, hungry pets eat from it.\n'
                  'Pet Bath: fill it with a water bucket, dirty pets splash around in it.\n'
                  'Bouncy Mushroom: pets (and players) bounce on it.\n'
                  'Running Wheel: a pet runs inside it, and it gives a redstone signal while it spins.\n'
                  'Scratching Post: fun for claws.\n'
                  'Pet House: a shelter from rain and thunder.'),
    'reactions': ('Little moments', 'Pets react to the world around them: they dance to a playing jukebox, hop to note blocks, look up at bells, '
                  'warm up at a campfire at night, sniff flowers, beg for cake and for the food you eat, hide from thunder and explosions, '
                  'shake off water, cheer when you level up, curl up next to your bed when you sleep and play chase with other pets. '
                  'The Frost Penguin belly-slides on snow and ice.'),
}
for pid, (name, talent, desc) in PETS.items():
    TAMACON[pid] = (name, f'Lives in {FOUND[pid]}.\n\nTalent - {talent}: {desc}\n\nFavorite treat: {TREAT[pid]}.\n\n'
                          f'Fights with {FIGHT[pid]}.\n\n{EXTRA[pid]}')
lang['info.tamagotchi.tamagotchi_heart'] = 'Tames a wild pet. Pets live in structures: desert pyramids, jungle temples, ocean monuments, igloos, nether fortresses, ancient cities, end cities, trail ruins, mineshafts, swamp huts, trial chambers and woodland mansions. Not every structure has one!'
lang['info.tamagotchi.tamacon'] = 'The in-game guide: everything about the pets, their care, controls, toys, food and furniture. Right-click to read.'
lang['info.tamagotchi.tama_pager'] = 'You get one for free when you tame your first pet. Right-click your pet: stay / follow. Use it in the air: screen of your nearest pet. It beeps when a pet needs you.'
lang['info.tamagotchi.tama_egg'] = 'A tamed pet that fainted curls up into this egg. Use it on a block to wake the pet up again, with everything it had.'
for pid, (name, talent, desc) in PETS.items():
    lang[f'info.tamagotchi.pet.{pid}'] = f'The {name} lives in {FOUND[pid]}. Tame it with a Tamagotchi Heart. Talent - {talent}: {desc} Favorite treat: {TREAT[pid]}.'
for cid, (title, text) in TAMACON.items():
    lang[f'tamacon.tamagotchi.{cid}.title'] = title
    lang[f'tamacon.tamagotchi.{cid}'] = text

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
    shapeless('tamacon', ['minecraft:book', 'minecraft:pink_dye', 'minecraft:redstone'], T + 'tamacon'),
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
