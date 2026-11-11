# Tamacraft

> **Branch `port/1.21.1-neoforge`:** Tamacraft 1.3.0 for **Minecraft 1.21.1 on NeoForge** (version
> `1.3.0+1.21.1-neoforge`, NeoForge 21.1.x, no Fabric API), the same pets, furniture and features as the Fabric
> version `1.3.0+1.21.1` with the same ids and save data. Differences in building and testing are listed under
> [Building](#building).

A Fabric mod for **Minecraft 26.3**: ten rare pets hide in the world's structures. Find one, tame it with a
**Tamacraft Heart**, and look after it – feed it, play with it, keep it clean and let it sleep – and it becomes
your best friend: it follows you, carries a backpack, helps you fight, feeds you golden apples when you are hurt
and has a special talent.

Until version 1.2 the mod was called Tamagotchi; worlds, data packs and modpack files from then keep working, every
old `tamagotchi:` id is read as the `tamacraft:` one (`LegacyIds`, `mixin/LegacyIdMixin`). Tamacraft is inspired by
the classic virtual pets of the 90s and is not affiliated with or endorsed by Bandai.

![The ten pets](docs/screenshots/lineup.jpg)

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
Ember Pup, Sculk Wisp and Mimic bite back. Hold a Tamacraft Heart and they come closer.

## Controls

| On your pet | |
|---|---|
| Right-click, empty hand | Pet it ♥ |
| Sneak + right-click, empty hand | Pet screen: needs, mood, bond, talent, **backpack**, Sit / Follow / Wander |
| Sneak + right-click **with a chest** | Backpack on (27 slots) |
| Sneak + right-click **with shears** | Backpack off – **everything inside spills out** |
| Right-click with the **Tama Pager** | Sit / Stay ↔ Follow |
| Right-click with food / treat | Feed it |
| Right-click with a **golden apple** | Into its backpack – it brings you one when your health is low |
| Right-click with the Pet Brush | Groom it |
| Lead / Name Tag | Work like on any pet |

Use the Tama Pager in the air to open the screen of your nearest pet (within 64 blocks); it **beeps** when a pet is
hungry, bored, sleepy, dirty or hurt. You get a free pager the first time you tame a pet. The craftable **Tamacon**
(book + pink dye + redstone) is the in-game guide to everything.

![The pager screen](docs/screenshots/pet_screen.jpg)

![Idle, petted, sitting with a backpack, asleep](docs/screenshots/pets.jpg)

## Taking care of it

Four needs – **Hunger, Fun, Energy, Hygiene** – make up the **Mood**, shown on the pager screen and as little
bubbles over the pet's head. Happy pets use their talent; sad pets don't; miserable pets refuse to fight.
**Bond** (the hearts on the screen) grows with every bit of care and makes talents recharge faster.

* **Hunger** – Pet Kibble, its favourite treat, its usual food, or a Food Bowl it eats from by itself
* **Fun** – petting, Laser Pointer, Squeaky Ball (fetch!), Feather Wand, Bouncy Mushroom, Running Wheel, Scratching Post,
  Toy Box, plushies, other pets
* **Energy** – sleeping in a Pet Bed / Basket / Dragon Nest at night or when tired (faster next to a plush of its own kind)
* **Hygiene** – Pet Brush or a filled Pet Bath

The three dragons fly when that is faster (or just for fun). In a fight a pet helps like a wolf. Below a third of its health it stops, runs to you and eats food from its
backpack to heal. Tamed pets never die: they **faint into a Tama Egg** that keeps everything – use the egg to wake them up.

Pets also react to the world: they dance to jukeboxes, warm up at campfires, sniff flowers, beg for cake and for
your food, hide from thunderstorms, shake off water, cheer when you level up, play with each other, sleep next
to your bed, and the penguin belly-slides on snow and ice.

## Furniture

![Furniture in use](docs/screenshots/furniture.jpg)

Pet Bed, Pet Basket, Dragon Nest (sleep) · Food Bowl (fill with food) · Pet Bath (fill with a water bucket) ·
Bouncy Mushroom (everyone bounces) · Running Wheel (gives a redstone signal while a pet runs in it) ·
Scratching Post · Pet House (shelter from rain). All craftable; see the recipe book.

Gadgets and decoration (1.1):

![The new furniture](docs/screenshots/furniture_update.jpg)
![Plushies of all ten pets](docs/screenshots/plushies.jpg)

* **Plushies** of all ten pets – squeeze them; lonely pets cuddle them; sleeping next to its own plush rests faster
* **Pet Portrait** – click it and it paints your nearest pet with its name (again for the next pet); dye the backdrop
* **Treat Dispenser** – fill it with treats and give it a redstone pulse: it shoots one to the hungriest pet, which catches it
* **Pet Incubator** – a Tama Egg hatches in 30 s, fully healed and rested
* **Toy Box** – bored pets open it and play with the toys inside
* **Pet Flap** – pets walk through, everyone else is blocked (other mobs path around it)
* **Egg Lamp** – a glowing night light; the Pet Bed, Pet Basket, Egg Lamp and portrait backdrop take any dye

## Compatibility

JEI and REI show every recipe plus info pages on where to find each pet (optional plugins in `compat/`).

For modpacks and data packs:

* **Where pets live:** one structure tag per spawn rule, `tamacraft:pet_home/<rule>` (e.g. `pet_home/hex_toad`,
  `pet_home/mimic_mansion`). They already hold the look-alikes of Repurposed Structures, Dungeons and Taverns,
  Explorations and Moog's structures as optional entries; add your own structures to them.
* **What pets eat:** the item tags `tamacraft:diet/meat`, `fish`, `plant`, `sweet` and `mineral`. They include the
  `c:foods/...` tags, so food from other mods counts too.
* **Ores:** the Pebble Golem sniffs out everything in `c:ores`.
* **Backpack:** any wooden chest (`c:chests/wooden`) puts it on, any shears (`c:tools/shear`) take it off.

## Releasing

Releases are automatic: pushing a tag `v<mod_version>`, or starting `.github/workflows/release.yml` by hand ("Run
workflow" in the Actions tab, on the branch), builds the mod and publishes that version with its section of
`CHANGELOG.md` as the changelog (mod-publish-plugin, `publishMods`):

* **GitHub release**: always (the tag is made if it is missing)
* **CurseForge** (project `1758309`, `curseforge_id` in `gradle.properties`): when the secret `CURSEFORGE_TOKEN` is set
* **Modrinth**: when the secret `MODRINTH_TOKEN` is set and `modrinth_id` is filled in

Every other push runs the same upload as a dry run in `.github/workflows/build.yml`. Locally:
`CURSEFORGE_TOKEN=... ./gradlew publishCurseforge`.

Tokens, as repository secrets (GitHub: Settings → Secrets and variables → Actions):

* `CURSEFORGE_TOKEN` from https://legacy.curseforge.com/account/api-tokens
* `MODRINTH_TOKEN` from https://modrinth.com/settings/pats with the scopes *Create versions*, *Read versions* and
  *Write versions*; then put the project id ("Copy ID" on the Modrinth project page) into `modrinth_id`

Each release: raise `mod_version` in `gradle.properties`, add a `## <version>` section to `CHANGELOG.md`, push, then
push the tag `v<version>` (a tag that does not match `mod_version` is refused) or start the workflow by hand.

## Building

On this branch (Minecraft 1.21.1, NeoForge): Java 21, `./gradlew build` (ModDevGradle, NeoForge 21.1.265, official
Mojang names). The loader layer is NeoForge's: registration on the first `RegisterEvent` (the registry classes are the
same as on Fabric), NeoForge's client registration events, `IClientItemExtensions` for the plush items and the access
transformer `META-INF/accesstransformer.cfg`; the glowing model parts carry NeoForge's per-element light data
(`neoforge_data`) next to `light_emission`. JEI and REI are optional (`-PwithJei` / `-PwithRei` load them into the
client test). `src/gametest` is a second, never shipped mod with the client test harness, the server game tests
(`./gradlew runGameTestServer`) and a registry dump (`./gradlew runRegistryDump -PdumpTo=file`, the same lines as the
Fabric build's for a diff).

On the Fabric branch `port/1.21.1`: Java 21, `./gradlew build`; Loom remaps with the official Mojang mappings.
`tools/data/gen_data.py` ends with the 1.21.1 target `tools/data/mc1211.py`, which turns the generated 26.x data and
item definitions into the 1.21.1 formats. Fabric API has no client game tests for 1.21.1, so `src/gametest` brings a
small harness of its own (`net.kasax.tamacraft.test.harness`, real mouse and key input through the game's GLFW
handlers): `xvfb-run -a ./gradlew runClientGameTest [-Ptests=checks]`. The video harness (`src/film`) is only on 26.3.

On 26.3: Java 25, `./gradlew build`. Art and sound sources live in `tools/` (`tools/petart`, `tools/sprites`,
`tools/sfx`, `tools/gui`, `tools/data`) and regenerate every texture, model and sound. The client game test
`./gradlew runClientGameTest` renders a review gallery into `build/run/clientGameTest/screenshots` and logs
functional checks as `[TamaTest] PASS/FAIL`. Headless: start `Xvfb :98`, then run it with
`DISPLAY=:98 SDL_VIDEO_FORCE_EGL=1` (needs the Mesa EGL libraries).
