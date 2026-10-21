# Tamagotchi – Design & Build Plan

Fabric mod for Minecraft **26.3** (same toolchain as Challenge Craft: Loom 1.17.21, Loader 0.19.5,
Fabric API 0.161.0+26.3, Java 25, unobfuscated Mojang names). Mod id `tamagotchi`, package
`net.kasax.tamagotchi`. This file is the single source of truth for the design **and** the progress list,
so an interrupted session can pick up exactly where the last one stopped.

## 1. The ten pets

Each pet is rare: it only appears in its structure, and only by chance (one roll per structure).
All are tamed with the **Tamagotchi Heart**.

| # | Pet | Found in (chance) | Look | Talent (use for the player) | Fights with |
|---|-----|-------------------|------|-----------------------------|-------------|
| 1 | **Desert Dragon** | Desert pyramid (40 %) | sand-gold chubby dragon, terracotta back plates, blue scarab gem, tiny wings | **Ember Roast** – hand it raw food or raw ore, it breathes a little flame and gives back the cooked / smelted item | fire breath (sets target alight) |
| 2 | **Jungle Dragon** | Jungle temple (40 %) | leaf-green dragon, leaf crest + hibiscus flower, leaf wings | **Green Thumb** – makes crops and saplings around it grow | poison bite |
| 3 | **Tide Dragon** | Ocean monument (50 %) | teal sea dragon, fin ears, glowing aqua spots | **Tide Blessing** – owner gets Water Breathing + Dolphin's Grace while swimming near it; swims | bubble blast (knock-back) |
| 4 | **Frost Penguin** | Igloo (45 %) | round navy penguin, red knitted scarf | **Frost Steps** – water freezes under the owner's feet while it follows; belly-slides on snow / ice | snowball volley (slowness) |
| 5 | **Ember Pup** | Nether fortress (30 %) | basalt hound with glowing lava cracks and flame tail (dangerous look) | **Warm Heart** – gives the owner Fire Resistance when they catch fire; swims in lava | burning bite |
| 6 | **Sculk Wisp** | Ancient city (50 %) | floating sculk ghost, glowing cyan spots, antennae (spooky look) | **Echo Sense** – sonar ping makes hostile mobs nearby glow through walls | sonic chirp |
| 7 | **Void Kitten** | End city (30 %) | starry purple-black kitten, glowing magenta eyes, pearl tail tip | **Item Magnet** – pulls dropped items nearby into its backpack (or to you); teleports to you | blink strike |
| 8 | **Pebble Golem** | Trail ruins (35 %), mineshaft (8 %) | mossy boulder with a sprout and ore flecks | **Ore Sniffer** – sniffs out the nearest ore and leaves a sparkle trail to it | tanky ground slam |
| 9 | **Hex Toad** | Swamp hut (45 %) | swamp toad with a tiny witch hat | **Brew Buddy** – gifts the owner a random good potion effect now and then | hex tongue (weakness) |
| 10 | **Mimic** | Trial chambers (30 %), woodland mansion (60 %) | living chest with teeth and tongue (dangerous look) | **Treasure Belly** – double backpack (54 slots) and coughs up small treasures | chomp |

Wild pets stay near their structure, never despawn, shy ones flee when hit, the dangerous-looking
ones (Ember Pup, Sculk Wisp, Mimic) bite back. A player holding a Tamagotchi Heart makes them curious.

## 2. Controls

| Input on your pet | Result |
|---|---|
| Right-click, empty hand | **Pet it** (petting animation, hearts, +Fun, +Bond) |
| Sneak + right-click **with a chest** | Put a **backpack** on (model shows it) |
| Sneak + right-click, empty hand | Backpack on → **take it off, all items spill out**; no backpack → **Sit / Stay** ↔ Follow |
| Right-click with **Tama Pager** | **Pet screen**: needs, mood, bond, talent, Sit / Follow / Wander, backpack, snack pouch |
| Right-click with food / favourite treat | Feed (eat animation) |
| Right-click with **golden apple** | Goes into its **snack pouch** – it feeds you one when your health is low |
| Right-click with toy / brush | Play / groom |
| Lead | Leash (vanilla) |
| Name tag | Rename (vanilla) |

The pager also works in the air (nearest own pet within 64 blocks) and **beeps** when a pet needs care.
The first taming gives a free pager.

## 3. Care (the Tamagotchi part)

Needs 0–100: **Hunger**, **Fun**, **Energy**, **Hygiene** → **Mood** (Ecstatic / Happy / Okay / Sad / Miserable).
Needs only drain while the pet is loaded. **Bond** (0–100, shown as hearts) grows with care and
shortens talent cool-downs. Sad pets don't use their talent; miserable pets refuse to fight.
Needs show as emote bubbles above the head (drumstick, Zzz, stink lines, "?" bored, rain cloud sad, hearts).

* Hunger – food, favourite treat, food bowl
* Fun – petting, toys, playground blocks, playing with other pets
* Energy – sleeping (bed at night, or when tired), sitting
* Hygiene – brush, bath

**Combat:** helps like a wolf (owner's attacker / owner's target). Under 35 % health it stops
fighting, runs to the owner and eats food from its backpack to heal (animation). A tamed pet never
dies: it **faints into a Tama Egg** that keeps everything (name, stats, backpack). Use the egg to wake it up.

## 4. Items, blocks, toys, food

* **Tamagotchi Heart** (tames), **Tama Pager** (screen + beeps), **Pet Brush**, **Tama Egg** (fainted pet)
* Toys: **Laser Pointer** (hold use – pets chase the red dot and pounce), **Squeaky Ball** (throw – fetch),
  **Feather Wand** (pets jump and swipe at it)
* Food: **Pet Kibble** (all) + favourite treats: **Fish Crackers**, **Dragon Fruit**, **Ember Jerky**,
  **Rock Candy**, **Glow Gummy**, **Golden Biscuit**
* Blocks (pets use them on their own, with animations):
  **Pet Bed / Pet Basket / Dragon Nest** (sleep → energy), **Food Bowl** (stores food, pets eat from it),
  **Pet Bath** (splash → hygiene), **Bouncy Mushroom** (bounce → fun, players bounce too),
  **Running Wheel** (run → fun, gives a redstone signal while spinning), **Scratching Post** (fun),
  **Pet House** (shelter from rain and thunder)
* Own creative tab, spawn egg per pet, recipes for everything craftable.

## 5. Reactions to the world (cute moments)

Jukebox → dance · note block → hop + notes · bell → look and perk up · thunder/explosion → scared,
hides behind owner · leaving rain/water → shakes off · lit campfire at night → warms up next to it ·
flowers → sniffs · cake → begs · owner eats → begs · owner sleeps → curls up next to the bed ·
owner levels up → celebrates · fireworks → looks up, jumps · two pets meet → play-chase ·
snow/ice → penguin belly-slides · lava → ember pup swims · sculk sensor → wisp chirps along.

## 6. Architecture

* `PetSpecies` (enum): stats, size, gait (walk / hop / float / swim), diet, favourite treat, talent,
  structure spawns, names, sounds. One `EntityType` per species, one shared entity class `TamaPet`.
* `TamaPet extends TamableAnimal`: needs, bond, backpack (`SimpleContainer` 27/54), snack pouch,
  command mode, action/animation sync (entity events + synced data), faint → egg.
* Goals: follow / sit / wander, defend + species attack, retreat-and-eat, feed owner, use blocks,
  reactions, toys, talents.
* Client: one generic `PetModel` built from generated `LayerDefinition`s, procedural + keyframe
  animation layer (`PetAnimator`), expression planes for eyes (open / blink / happy / sleep / sad),
  emissive layer, held-item layer, `PetRenderer`.
* Structure spawning: mixin at the end of `StructureStart.placeInChunk`, one roll per structure in the
  chunk that holds the first piece's centre; spot search inside the pieces.
* Art pipeline (`tools/`): Python model + texture generator (pets as data → Java model code + painted
  64×64 textures + preview contact sheets); pixel-map sprites for items; synthesized + pitched vanilla sounds.
* Tests: server game tests (tame, backpack spill, feed, faint → egg) and a client game test that
  screenshots every pet, block and the pet screen for art review.

## 7. Progress

- [x] 0 Project skeleton, toolchain (Loom 1.17.21, Java 25; container needs `~/.gradle/init.d` mirror for Maven Central 429s)
- [x] 1 Core entity + species + registration + spawn eggs + creative tab
- [x] 2 Art pipeline (`tools/petart`) + 10 pet models/textures with 7 expressions
- [x] 3 Renderer, procedural animator, expressions, glow + held-item layers, particles
- [x] 4 Interactions: tame, pet, feed, backpack add/remove/spill, sit/follow/wander, leash, snack pouch
- [x] 5 Needs, mood, bond, emotes, pager beeps
- [x] 6 Combat (10 attack styles), retreat-and-eat, feed owner, faint → Tama Egg
- [x] 7 Pet screen (menu, LCD-style screen, buttons via clickMenuButton)
- [x] 8 Items, food, recipes, item art (subagent, `tools/sprites`)
- [x] 9 Blocks + wheel renderer + pet AI for furniture (art by subagent)
- [x] 10 Talents (10)
- [x] 11 Reactions (jukebox, campfire, cake, flowers, owner eating, thunder, rain shake, fireworks, play dates, level-up)
- [x] 12 Structure spawning (mixin on StructureStart.placeInChunk)
- [x] 13 Sounds (subagent, `tools/sfx`) + particles
- [x] 14 In-game screenshot review (`runClientGameTest` under xvfb) + polish: small custom hearts, clearer sit/sleep
      poses, wheel runner faces across the axle, bigger portrait on the pet screen; functional checks (tame, backpack
      on/spill, snack pouch, faint → egg, wild pets in placed structures) log `[TamaTest] PASS/FAIL`
- [x] 15 README
