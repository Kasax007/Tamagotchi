# Changelog

Each release uploads the section of its version as the changelog on CurseForge, Modrinth and GitHub.

## 1.3.0+1.21.1

The Minecraft 1.21.1 version of Tamacraft 1.3.0: the same pets, furniture and features as Tamacraft 1.3.0 for 26.3,
now for Minecraft 1.21.1 (Fabric, requires Fabric API). Tamacraft is the new name of the mod (formerly Tamagotchi).

- Ten rare pets to find, tame and look after, with needs, moods, bond, talents, toys, the Tama Pager and the Tamacon
- All 25 pieces of furniture, the plushies and the dyeable colours
- Everything new in 1.2.0 for modpacks (modded food and ores, look-alike structures, pet_home structure tags, any
  wooden chest and shears, diet tags, tooltips, recipe-book unlocks) and all its fixes
- Ids from before the rename (`tamagotchi:...`, for example `tamagotchi:tamagotchi_heart`) are read as the new
  `tamacraft:...` ones, so data packs and modpack files that still name them keep working

## 1.3.0

The mod has a new name: **Tamacraft** (formerly Tamagotchi). Same pets, same furniture, same features.

- Everything that carried the old name now says Tamacraft: the mod id and all ids are `tamacraft:...`, and the
  Tamagotchi Heart is now the **Tamacraft Heart** (`tamacraft:tamacraft_heart`). The Tamacon, the Tama Pager, the
  pets and the furniture keep their names
- Your worlds keep working: pets (tamed, with their needs, mood, bond and backpack), furniture, Tama Eggs and every
  item in inventories and chests load with the new ids, and so do advancements and recipe-book entries. Data packs,
  quests and recipes that still name `tamagotchi:...` ids keep working too
- Tamacraft is inspired by the classic virtual pets of the 90s and is not affiliated with or endorsed by Bandai

## 1.2.0

Modpack-ready: modded food, ores and structures, plus a round of fixes.

- Pets eat food from other mods too (the `c:foods` tags), and the Pebble Golem sniffs out modded ores (`c:ores`)
- Pets also live in look-alike structures from other mods (Repurposed Structures pyramids, witch huts, mineshafts,
  mansions, monuments and more, Moog's igloos and nether fortresses); data packs can add their own through the
  `tamacraft:pet_home/...` structure tags
- Any wooden chest puts a backpack on your pet and any shears take it off, also the ones from other mods
- Furniture shows a tooltip on what your pets do with it
- Recipes appear in the recipe book as soon as you carry one of their ingredients
- Axes, pickaxes and hoes mine the furniture faster
- The Food Bowl recipe now has a bone in the middle (the old one clashed with another mod's clay cup)
- Fix: a tired pet that cannot reach you no longer falls asleep and wakes up again over and over
- Fix: pets stay curled up next to your bed until you get up
- Fix: a golden-apple feeding that gets interrupted no longer makes a free golden apple
- Fix: hurt pets eat their lunch from the backpack, not the golden apples meant for you
- Fix: a pet that faints in the void lands in your inventory as an egg instead of falling forever
- Fix: Tama Eggs on the ground survive fire, lava, cacti and explosions
- Fix: a dragon saved in mid-air no longer hovers forever after loading the world
- Fix: the Void Kitten only pulls items while you are near, and leaves items that players throw alone
- Fix: pets no longer try to follow, beg from or bring a ball to an owner who is in another dimension
- Fix: the pet screen shows "Sit" correctly, also after loading the world; the Tamacon contents react to the left
  mouse button only

## 1.1.0

The furniture update: plushies, gadgets and colours.

- Plushies of all ten pets. Squeeze them; lonely pets cuddle them, and a pet that sleeps next to a plush of its own kind
  rests half again as fast
- Pet Portrait: hang it up and click it, it paints your nearest pet with its name (click again for the next pet)
- Treat Dispenser: fill it with treats, give it a redstone pulse, and it shoots one to the hungriest pet, which jumps
  and catches it
- Pet Incubator: a Tama Egg hatches in thirty seconds, fully healed and rested
- Toy Box: bored pets open it by themselves and play with the toys inside
- Pet Flap: your pets walk through, everyone else bumps into it (other mobs path around it like a wall)
- Egg Lamp: a glowing night light
- Dye the Pet Bed, Pet Basket, Egg Lamp and the portrait backdrop in all sixteen colours; broken furniture keeps its colour
- Tamacon: new chapters "Pet gadgets" and "Decoration"; JEI/REI info pages for the new blocks
- Fix: dragons without AI (NoAI tag, e.g. display pets) no longer take off by themselves

## 1.0.0

The first release.

- Ten rare pets that live in Minecraft's structures: Desert Dragon, Jungle Dragon, Tide Dragon, Frost Penguin,
  Ember Pup, Sculk Wisp, Void Kitten, Pebble Golem, Hex Toad and Mimic, each with its own talent
- Tame them with a Tamacraft Heart; care for hunger, fun, energy and hygiene; bond hearts and moods
- Backpacks (27 slots), golden apples your pet brings you when you are hurt, fights at your side, faints into a Tama Egg
  instead of dying
- The dragons fly when it is faster or just for fun
- Tama Pager, Tamacon (in-game guide), Pet Brush, toys (Laser Pointer, Squeaky Ball, Feather Wand) and seven treats
- Furniture the pets use by themselves: beds, basket, dragon nest, food bowl, bath, bouncy mushroom, running wheel,
  scratching post and pet house
- JEI and REI support with info pages on where to find every pet
