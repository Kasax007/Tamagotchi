# Tamagotchi sounds

All custom sounds are synthesized from scratch (numpy only, no samples or downloads) by `make_sfx.py` and encoded as mono 44.1 kHz Ogg Vorbis (`-q:a 4`) into `src/main/resources/assets/tamagotchi/sounds/<group>/<name>.ogg`. Creature vocals mix synthesized calls with pitched-up references to vanilla sound files (no vanilla audio is copied; sounds.json only points at it).

| File | Purpose |
| --- | --- |
| `make_sfx.py` | Synthesizer + encoder + spectrogram sheet. Deterministic and re-runnable: `python3 tools/sfx/make_sfx.py` (`--only "pet/*"`, `--list`, `--no-sheet`, `-j 1`). Needs numpy, Pillow (sheet only) and ffmpeg with libvorbis. |
| `validate_sounds.py` | Checks every sounds.json reference (custom files exist and decode, vanilla keys exist in the asset index), subtitles, variant counts, expected events, size. |
| `subtitles_en_us.json` | `subtitles.tamagotchi.*` keys; merge into `assets/tamagotchi/lang/en_us.json`. |
| `out/spectrograms.png` | Contact sheet of all custom sounds, read back from the encoded files. |

Notes: custom files are peak-normalized to about -3 dBFS; per-variant `volume` in sounds.json balances them against each other and against vanilla (A-weighted loudness matching, so high whistles are set lower than soft rumbles). The engine clamps pitch to 0.5-2.0, so referenced pitches stay at or below 1.75 to leave room for entity pitch variation. Every event has 1-4 variants. Events are listed as `event` - description (custom files; vanilla references).

## Events


### Desert Dragon

- `desert_dragon.ambient` - Warm baby-dragon chirp: a rolled little growl flips into a rising chirp, or a long soft growl with a tiny squeak; plus pitched-up vanilla strider idles. (custom: ambient1, ambient2; vanilla: mob/strider/idle2 x1.35, mob/strider/idle3 x1.3)
- `desert_dragon.happy` - 'Chi-chi-chirrup!': two quick chirps and a trilling one, or a purr that ends in a mew; plus pitched-up strider coos. (custom: happy1, happy2; vanilla: mob/strider/happy1 x1.3, mob/strider/happy5 x1.3)
- `desert_dragon.hurt` - Short 'kyeh!' squeal with a raspy edge; plus pitched-up strider hurt cries. (custom: hurt1; vanilla: mob/strider/hurt2 x1.35, mob/strider/hurt1 x1.3)
- `desert_dragon.death` - Long falling whine that turns into a growl and fades; plus pitched-up strider death cries. (custom: death1; vanilla: mob/strider/death2 x1.3, mob/strider/death4 x1.3)
- `desert_dragon.attack` - Small fire puff: breathy 'fwoof', a warm thump and a few ember sparks (two takes). (custom: attack1, attack2)

### Jungle Dragon

- `jungle_dragon.ambient` - Chirpy bird-like pips and a slurred 'twee-oo' whistle; plus vanilla parrot chirps. (custom: ambient1, ambient2; vanilla: mob/parrot/idle2, mob/parrot/idle4)
- `jungle_dragon.happy` - Long warbling trill that climbs and tips over, or 'ti-ti-tweee!'; plus parrot chirps pitched up. (custom: happy1, happy2; vanilla: mob/parrot/idle6 x1.15, mob/parrot/idle3 x1.2)
- `jungle_dragon.hurt` - Sharp squawk 'kyaa!'; plus vanilla parrot hurt calls. (custom: hurt1; vanilla: mob/parrot/hurt1, mob/parrot/hurt2)
- `jungle_dragon.death` - A trill that slows down and sinks; plus vanilla parrot death cries. (custom: death1; vanilla: mob/parrot/death2, mob/parrot/death4 x0.95)
- `jungle_dragon.attack` - Leafy snap: rustle, crisp snap, a woody tick and settling leaves (single and double snap). (custom: attack1, attack2)

### Tide Dragon

- `tide_dragon.ambient` - Baby-dolphin squeaks: a few clicks and a smooth tremolo whistle ending in a tiny bubble, or 'blup-eee'; plus vanilla dolphin chatter. (custom: ambient1, ambient2; vanilla: mob/dolphin/idle4 x1.1, mob/dolphin/idle5 x1.15)
- `tide_dragon.happy` - Rising squeak runs with bubbles, or a bubbly 'bloop' giggle; plus a vanilla dolphin play call. (custom: happy1, happy2; vanilla: mob/dolphin/play1 x1.1)
- `tide_dragon.hurt` - Falling 'yeek' squeal with clicks; plus vanilla baby-nautilus squeaks. (custom: hurt1; vanilla: mob/baby_nautilus/hurt_land3 x1.1, mob/baby_nautilus/hurt_land1 x1.1)
- `tide_dragon.death` - Sad whistle that sinks, then a few drifting bubbles; plus vanilla dolphin and axolotl cries. (custom: death1; vanilla: mob/dolphin/death2 x1.3, mob/axolotl/death1)
- `tide_dragon.attack` - Bubble burst: a wet blast, a rush of random bubbles and one big bloop, or a fat 'blorp-pop-pop' with a splash. (custom: attack1, attack2)

### Frost Penguin

- `frost_penguin.ambient` - Tiny nasal honks, 'kweh-keh' and 'pip-honk'; plus pitched-up vanilla chicken and donkey calls (penguins really bray). (custom: ambient1, ambient2; vanilla: mob/chicken/say3 x1.25, mob/horse/donkey/idle3 x1.5)
- `frost_penguin.happy` - Excited 'kwe-kwe-kwe-kweee!' honks, or 'pi-pi-pi-hweee' tweets; plus a parrot chirp. (custom: happy1, happy2; vanilla: mob/parrot/idle5 x1.1)
- `frost_penguin.hurt` - 'Kweeek!' squeal; plus vanilla baby-chicken peeps and a donkey squeal. (custom: hurt1; vanilla: mob/chicken/baby_chicken/hurt1 x0.9, mob/horse/donkey/hit2 x1.3)
- `frost_penguin.death` - A sad honk that wobbles down and away; plus a vanilla baby-chicken cry. (custom: death1; vanilla: mob/chicken/baby_chicken/death x0.9)
- `frost_penguin.attack` - Snowball throw: a little 'hup!', a whoosh and a soft 'poff' (single throw, or a two-snowball volley). (custom: attack1, attack2)

### Ember Pup

- `ember_pup.ambient` - Small 'yip!' with a tiny growl behind it and ember crackle, or 'yip-yip' and an ember pop; plus vanilla puppy yips. (custom: ambient1, ambient2; vanilla: mob/wolf/baby/ambient1 x1.1, mob/wolf/puglin/bark2 x1.4)
- `ember_pup.happy` - Excited rising yaps ending in a happy 'wooo' over crackling embers; plus puppy and fox yips. (custom: happy1; vanilla: mob/wolf/baby/ambient4 x1.2, mob/wolf/baby/ambient7 x1.2, mob/fox/idle1 x1.15)
- `ember_pup.hurt` - 'Kyai!' yelp; plus vanilla puppy and fox yelps. (custom: hurt1; vanilla: mob/wolf/baby/hurt2 x1.15, mob/wolf/baby/hurt3 x1.15, mob/fox/hurt2)
- `ember_pup.death` - Long whimper while the embers die out; plus pug and fox cries. (custom: death1; vanilla: mob/wolf/puglin/death x1.25, mob/fox/death1 x1.1)
- `ember_pup.attack` - Fiery snap: growly bark, sharp snap, flame flash and sparks, or 'chk-fwoof'; plus a vanilla fox bite. (custom: attack1, attack2; vanilla: mob/fox/bite2 x0.9)

### Sculk Wisp

- `sculk_wisp.ambient` - Whispery 'ooo-ah' coo from a detuned pair of breathy voices with sculk ticks, or ticks over a faint hum; plus pitched-up happy-ghast coos. (custom: ambient1, ambient2; vanilla: mob/happy_ghast/ambient3 x1.6, mob/happy_ghast/ambient6 x1.6)
- `sculk_wisp.happy` - Rising, glittery 'oo-woo!'; plus higher-pitched ghast coos. (custom: happy1; vanilla: mob/happy_ghast/ambient7 x1.75, mob/happy_ghast/ambient9 x1.75)
- `sculk_wisp.hurt` - Breathy, startled 'wuh!' with a click; plus vanilla allay hurt calls. (custom: hurt1; vanilla: mob/allay/hurt1 x1.1, mob/allay/hurt2 x1.1)
- `sculk_wisp.death` - Long fading whisper that sinks away; plus vanilla vex cries. (custom: death1; vanilla: mob/vex/death1 x0.9, mob/vex/death2 x0.9)
- `sculk_wisp.attack` - Sonic chirp: quick charge-up, a falling 'pew' and a soft boom, or 'pi-pwoo'. (custom: attack1, attack2)

### Void Kitten

- `void_kitten.ambient` - Kitten 'mi-aow' with a faint ender shimmer, or a questioning 'mrp?'; plus pitched-up vanilla cat meows. (custom: ambient1, ambient2; vanilla: mob/cat/meow2 x1.4, mob/cat/meow3 x1.45)
- `void_kitten.happy` - Purr with a happy 'mrrp!', or 'mew-mew' with a trail of stardust; plus a high cheerful meow. (custom: happy1, happy2; vanilla: mob/cat/meow1 x1.55)
- `void_kitten.hurt` - Short yowl; plus vanilla cat hurt calls. (custom: hurt1; vanilla: mob/cat/hitt1 x1.3, mob/cat/hitt3 x1.3)
- `void_kitten.death` - Plaintive fading meow with falling stardust; plus ocelot cries. (custom: death1; vanilla: mob/cat/ocelot/death1 x1.3, mob/cat/ocelot/death3 x1.3)
- `void_kitten.attack` - Blink whoosh: a reversed shimmer swells in, then pop and glitter, or a flash and a fast falling sweep; plus a vanilla enderman teleport. (custom: attack1, attack2; vanilla: mob/endermen/portal2 x1.3)

### Pebble Golem

- `pebble_golem.ambient` - Low, nosy 'hmmm?' over a faint rumble and two pebble ticks, or pebbles clicking around a sleepy 'mm'; plus a deep vanilla villager 'hmm' and a sniffer rumble. (custom: ambient1, ambient2; vanilla: mob/villager/idle1 x0.75, mob/sniffer/happy3 x1.3)
- `pebble_golem.happy` - 'Hm-HM!' with a tinkle of pebbles; plus pitched-up sniffer purrs. (custom: happy1; vanilla: mob/sniffer/happy2 x1.4, mob/sniffer/happy4 x1.4)
- `pebble_golem.hurt` - 'Oof!' grunt with a stone clack and a few falling pebbles; plus vanilla armadillo and copper-golem grunts. (custom: hurt1; vanilla: mob/armadillo/hurt4, mob/armadillo/hurt5, mob/coppergolem/regular/hurt3)
- `pebble_golem.death` - Sinking hum, crumbling rubble and one last soft thud; plus vanilla armadillo moans. (custom: death1; vanilla: mob/armadillo/death3 x1.2, mob/armadillo/death4 x1.2)
- `pebble_golem.attack` - Heavy thud: a deep stone slam with a crunch and falling rubble (single and double slam); plus a vanilla mace smash. (custom: attack1, attack2; vanilla: item/mace/smash_ground1 x1.2)

### Hex Toad

- `hex_toad.ambient` - Pulse-train 'ri-bbit' ribbit and a rolled 'brrrup', each ending in a small bubble; plus vanilla frog croaks. (custom: ambient1, ambient2; vanilla: mob/frog/idle1 x1.2, mob/frog/idle4 x1.25)
- `hex_toad.happy` - Bouncy double ribbit ending in a 'bwip'; plus higher-pitched frog croaks. (custom: happy1; vanilla: mob/frog/idle1 x1.45, mob/frog/idle4 x1.5)
- `hex_toad.hurt` - Wet little 'gwak!'; plus vanilla frog hurt calls. (custom: hurt1; vanilla: mob/frog/hurt1 x1.15, mob/frog/hurt3 x1.15, mob/frog/hurt2 x1.2)
- `hex_toad.death` - A croak that slowly deflates, with a few popping bubbles; plus vanilla frog death cries. (custom: death1; vanilla: mob/frog/death1 x1.2, mob/frog/death2 x1.2)
- `hex_toad.attack` - Tongue slurp: a flick, wet rising bubbles, a smack and a gulp, or a quicker one with a wet pop. (custom: attack1, attack2)

### Mimic

- `mimic.ambient` - Long wooden creak ending in a lid tick, or a playful low growl with two lid clacks; plus a vanilla chest-lid creak and creaking-tree sway. (custom: ambient1, ambient2; vanilla: mob/creaking/creaking_sway3 x0.9, block/chest/open x0.9)
- `mimic.happy` - Giggle: rapid lid chatter with a squeaky creak; plus pitched-up creaking-tree sways. (custom: happy1; vanilla: mob/creaking/creaking_sway2 x1.3, mob/creaking/creaking_sway4 x1.2)
- `mimic.hurt` - A clack and a short creaky yelp; plus a vanilla locked-chest rattle. (custom: hurt1; vanilla: block/chest/close_locked x1.1, mob/creaking/creaking_sway3 x1.5)
- `mimic.death` - Long sinking creak, then the lid drops shut; plus a vanilla creaking-tree deactivate groan. (custom: death1; vanilla: mob/creaking/creaking_deactivate)
- `mimic.attack` - Chomp: a growl and a wooden lid slam (single and double); plus a vanilla chest slam. (custom: attack1, attack2; vanilla: block/chest/close1 x1.3)

### Talents

- `talent.roast` - Ember Roast: flame whoosh with a low rumble, then sizzling and crackle, finished by a tiny 'done!' ding (long and short). (custom: roast1, roast2)
- `talent.grow` - Green Thumb: rising music-box bells over a climbing glow, rustling leaves and glitter. (custom: grow1)
- `talent.blessing` - Tide Blessing: a swirling band of water, wobbly harp plucks and a few bubbles. (custom: blessing1)
- `talent.freeze` - Frost Steps: an ice crack, a shower of glassy ticks and a frosty shimmer. (custom: freeze1)
- `talent.warm` - Warm Heart: soft low fire 'whoomph' with a warm glowing pad and gentle crackle. (custom: warm1)
- `talent.ping` - Echo Sense: a round sonar ping with three fading echoes. (custom: ping1)
- `talent.magnet` - Item Magnet: a magic sweep falling into the centre, a rising tone and a soft pluck. (custom: magnet1)
- `talent.sniff` - Ore Sniffer: quick nasal 'sniff-sniff-snf' (three sniffs, or two). (custom: sniff1, sniff2)
- `talent.brew` - Brew Buddy: a cauldron bubbling faster and faster, then 'pop!' and a sparkle; plus the vanilla brewing-stand bubbling. (custom: brew1; vanilla: block/brewing_stand/brew1 x1.15, block/brewing_stand/brew2 x1.15)
- `talent.treasure` - Treasure Belly: a little 'ehm-hm' cough, then three coins clinking. (custom: treasure1)

### Shared pet sounds

- `pet.petting` - Contented purr with a soft coo on top, or a two-note dove-like coo and a purr tail. (custom: petting1, petting2)
- `pet.eat` - Nom-nom-nom: three soft chews, or four quick chews and a gulp; plus pitched-up vanilla eating bites. (custom: eat1, eat2; vanilla: random/eat3 x1.3, random/eat1 x1.3)
- `pet.yawn` - Big breathy 'aaah-hm' with a little squeak, or a shorter yawn ending in a rising squeak. (custom: yawn1, yawn2)
- `pet.snore` - Tiny snore: a rattly 'hnnk' in, a soft 'fwooo' out (second take adds a little whistle). (custom: snore1, snore2)
- `pet.splash` - Small splash: a wet whoosh, a 'plop' and a spray of droplet bubbles; plus a pitched-up vanilla splash. (custom: splash1, splash2; vanilla: liquid/splash x1.5)
- `pet.shake` - 'Brrrrr': fast fluttering shake with a fur flap and flying droplets; plus a pitched-up vanilla wolf shake. (custom: shake1, shake2; vanilla: mob/wolf/shake x1.3)
- `pet.tame` - Magical rising chime arpeggio (C-E-G-C-E-G) that blooms into a chord with glitter, or a harp-like pentatonic run. (custom: tame1, tame2)
- `pet.faint` - Gentle sad descending tones (G-E-D-A) with a soft tremolo, or a slow music-box version. (custom: faint1, faint2)
- `pet.wake` - Egg crack-crack-pop, then a sparkle chime with glitter (two takes with different chimes). (custom: wake1, wake2)
- `pet.celebrate` - Happy little fanfare: 'ta-ta-ta-TAAA!' toy horn with bells and glitter, or a bouncy arpeggio and trill. (custom: celebrate1, celebrate2)
- `pet.scared` - Two trembling whimpers and a sniffle, or three quick shivery whimpers; plus a vanilla puppy whine. (custom: scared1, scared2; vanilla: mob/wolf/baby/whine1 x1.1)
- `pet.feed_owner` - 'Pop!' and a bright two-note chime (G-C or E-A) with sparkle. (custom: feed_owner1, feed_owner2)

### Pager and toys

- `pager.beep` - Authentic virtual-pet piezo square-wave beeps: double beep twice, a rising 'bee-bee-beep', or a low 'bip-bip'. (custom: beep1, beep2, beep3)
- `pager.open` - Short square-wave UI 'bleep-bloop' (or 'bloop-bleep'). (custom: open1, open2)
- `toy.squeak` - Rubbery squeaky-toy squeak, or a lower double 'ee-eek'. (custom: squeak1, squeak2)
- `toy.laser` - Soft electronic 'zip' into a gentle humming tone (long and short). (custom: laser1, laser2)
- `toy.feather` - Soft airy swish with a faint flutter (up-and-over, and back). (custom: feather1, feather2)

### Blocks and items

- `block.bounce` - Cartoony 'boing-oing-oing' spring wobble (big and small). (custom: bounce1, bounce2)
- `block.wheel` - Wooden wheel spinning: soft whirr, slow creaks and spoke ticks; exactly 1.5 s and seamlessly loopable. (custom: wheel1)
- `block.bowl_fill` - Kibble pouring into a bowl: a rattling shower of ticks and a few settling clinks (long and short pour). (custom: bowl_fill1, bowl_fill2)
- `item.brush` - Soft brushing 'scritch-scritch' (two long strokes, or three short ones). (custom: brush1, brush2)
- `backpack.equip` - Leather rustle, strap creak, buckle click-click and a soft settle; plus pitched-up vanilla leather-armor equips. (custom: equip1, equip2; vanilla: item/armor/equip_leather1 x1.1, item/armor/equip_leather5 x1.1)
- `backpack.spill` - The bag opens and items tumble out with wood, stone and metal bounces; plus the vanilla bundle drop. (custom: spill1, spill2; vanilla: item/bundle/drop_contents3)
