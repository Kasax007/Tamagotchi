# Tamagotchi

A Fabric mod for **Minecraft 26.3**: ten rare pets hide in the world's structures. Find one, tame it with a
**Tamagotchi Heart**, and look after it – feed it, play with it, keep it clean and let it sleep – and it becomes
your best friend: it follows you, carries a backpack, helps you fight, feeds you golden apples when you are hurt
and has a special talent.

## The pets

| Pet | Lives in (chance per structure) | Talent | Favourite treat |
|---|---|---|---|
| Desert Dragon | Desert pyramid (40 %) | **Ember Roast** – hand it raw food or ore, it roasts / smelts it | Dragon Fruit |
| Jungle Dragon | Jungle temple (40 %) | **Green Thumb** – crops and saplings around it grow | Dragon Fruit |
| Tide Dragon | Ocean monument (50 %) | **Tide Blessing** – Water Breathing + Dolphin's Grace while you swim near it | Fish Crackers |
| Frost Penguin | Igloo (45 %) | **Frost Steps** – water freezes under your feet while it follows you | Fish Crackers |
| Ember Pup | Nether fortress (30 %) | **Warm Heart** – Fire Resistance when you catch fire; swims in lava | Ember Jerky |
| Sculk Wisp | Ancient city (50 %) | **Echo Sense** – sonar ping makes hostile mobs glow through walls | Glow Gummy |
| Void Kitten | End city (30 %) | **Item Magnet** – pulls dropped items into its backpack or to you | Fish Crackers |
| Pebble Golem | Trail ruins (35 %), mineshafts (8 %) | **Ore Sniffer** – sniffs out the best ore nearby and shows the way | Rock Candy |
| Hex Toad | Swamp hut (45 %) | **Brew Buddy** – brews you a random helpful potion effect | Glow Gummy |
| Mimic | Trial chambers (30 %), woodland mansion (60 %) | **Treasure Belly** – 27-slot belly (54 with a backpack), coughs up treasure | Golden Biscuit |

Wild pets stay around their structure and never despawn. The cute ones run away when hit; the
Ember Pup, Sculk Wisp and Mimic bite back. Hold a Tamagotchi Heart and they come closer.

## Controls

| On your pet | |
|---|---|
| Right-click, empty hand | Pet it ♥ |
| Sneak + right-click **with a chest** | Backpack on (27 slots) |
| Sneak + right-click, empty hand | Backpack off – **everything inside spills out**; without a backpack: Sit / Stay ↔ Follow |
| Right-click with the **Tama Pager** | Pet screen: needs, mood, bond, talent, Sit / Follow / Wander, backpack |
| Right-click with food / treat | Feed it |
| Right-click with a **golden apple** | Into its snack pouch – it feeds you one when your health is low |
| Right-click with the Pet Brush | Groom it |
| Lead / Name Tag | Work like on any pet |

The Tama Pager also works in the air (nearest own pet within 64 blocks) and **beeps** when a pet is hungry,
bored, sleepy, dirty or hurt. You get a free pager the first time you tame a pet.

## Taking care of it

Four needs – **Hunger, Fun, Energy, Hygiene** – make up the **Mood**, shown on the pager screen and as little
bubbles over the pet's head. Happy pets use their talent; sad pets don't; miserable pets refuse to fight.
**Bond** (the hearts on the screen) grows with every bit of care and makes talents recharge faster.

* **Hunger** – Pet Kibble, its favourite treat, its usual food, or a Food Bowl it eats from by itself
* **Fun** – petting, Laser Pointer, Squeaky Ball (fetch!), Feather Wand, Bouncy Mushroom, Running Wheel, Scratching Post, other pets
* **Energy** – sleeping in a Pet Bed / Basket / Dragon Nest at night or when tired
* **Hygiene** – Pet Brush or a filled Pet Bath

In a fight a pet helps like a wolf. Below a third of its health it stops, runs to you and eats food from its
backpack to heal. Tamed pets never die: they **faint into a Tama Egg** that keeps everything – use the egg to wake them up.

Pets also react to the world: they dance to jukeboxes, warm up at campfires, sniff flowers, beg for cake and for
your food, hide from thunderstorms, shake off water, cheer when you level up, play with each other, sleep next
to your bed, and the penguin belly-slides on snow and ice.

## Furniture

Pet Bed, Pet Basket, Dragon Nest (sleep) · Food Bowl (fill with food) · Pet Bath (fill with a water bucket) ·
Bouncy Mushroom (everyone bounces) · Running Wheel (gives a redstone signal while a pet runs in it) ·
Scratching Post · Pet House (shelter from rain). All craftable; see the recipe book.

## Building

Java 25, `./gradlew build`. Art and sound sources live in `tools/` (`tools/petart`, `tools/sprites`,
`tools/sfx`, `tools/gui`, `tools/data`) and regenerate every texture, model and sound. The client game test
`./gradlew runClientGameTest` renders a review gallery into `build/run/clientGameTest/screenshots`.
