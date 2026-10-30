package net.kasax.tamagotchi.film;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.function.Consumer;
import net.kasax.tamagotchi.block.BouncyMushroomBlock;
import net.kasax.tamagotchi.block.FoodBowlBlock;
import net.kasax.tamagotchi.block.PetBathBlock;
import net.kasax.tamagotchi.block.RunningWheelBlock;
import net.kasax.tamagotchi.item.LaserPointerItem;
import net.kasax.tamagotchi.item.TamaEggItem;
import net.kasax.tamagotchi.pet.PetAction;
import net.kasax.tamagotchi.pet.PetSpecies;
import net.kasax.tamagotchi.pet.TamaPet;
import net.kasax.tamagotchi.registry.ModBlocks;
import net.kasax.tamagotchi.registry.ModEntities;
import net.kasax.tamagotchi.registry.ModItems;
import net.kasax.tamagotchi.registry.ModSounds;
import net.kasax.tamagotchi.world.PetSpawns;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.JukeboxBlock;
import net.minecraft.world.level.block.entity.JukeboxBlockEntity;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;

/**
 * The shots of the Tamagotchi videos. All scenes share one world: a little garden stage is built at
 * spawn once (pets, furniture, a pond, a lava pool, an ore wall, a treasure room), and every shot
 * puts its own pets on it, films them with the free camera or the player's eyes, and clears them.
 */
final class PetScenes {
    static final String SEED = "tamagotchi-garden";

    private static BlockPos stage;
    private final FilmDirector d;
    private final Map<String, UUID> pets = new HashMap<>();

    private PetScenes(FilmDirector d) {
        this.d = d;
    }

    static boolean film(FilmDirector d, String scene) {
        PetScenes s = new PetScenes(d);
        Runnable shot = switch (scene) {
            case "hook_petting" -> s::hookPetting;
            case "lineup_dolly" -> s::lineup;
            case "petting_closeups" -> s::pettingCloseups;
            case "tame_heart" -> s::tame;
            case "backpack_on" -> s::backpack;
            case "bowl_eat" -> s::bowl;
            case "bath" -> s::bath;
            case "bounce" -> s::bounce;
            case "wheel" -> s::wheel;
            case "bed_sleep" -> s::bed;
            case "laser_chase" -> s::laser;
            case "feed_owner" -> s::feedOwner;
            case "roast" -> s::roast;
            case "ore_glow" -> s::ore;
            case "frost_steps" -> s::frost;
            case "lava_swim" -> s::lava;
            case "fly_follow" -> s::fly;
            case "fight" -> s::fight;
            case "faint_egg" -> s::faint;
            case "dance" -> s::dance;
            case "campfire_warm" -> s::campfire;
            case "pet_screen" -> s::petScreen;
            case "tamacon_book" -> s::tamacon;
            case "pyramid_wild" -> () -> s.natural("desert_pyramid", PetSpecies.DESERT_DRAGON, "pyramid_wild");
            case "jungle_wild" -> () -> s.natural("jungle_pyramid", PetSpecies.JUNGLE_DRAGON, "jungle_wild");
            case "monument_wild" -> () -> s.natural("monument", PetSpecies.TIDE_DRAGON, "monument_wild");
            case "igloo_penguin" -> s::igloo;
            case "mimic_chamber" -> s::mimic;
            // the furniture update (1.1) and the toys and tools the first videos left out
            case "plush_shelf" -> s::plushShelf;
            case "plush_squeeze" -> s::plushSqueeze;
            case "plush_cuddle" -> s::plushCuddle;
            case "plush_sleep" -> s::plushSleep;
            case "portrait_paint" -> s::portrait;
            case "egg_lamp" -> s::eggLamp;
            case "dye_bed" -> s::dyeBed;
            case "toy_box_open" -> s::toyBoxOpen;
            case "toy_box_play" -> s::toyBoxPlay;
            case "pet_flap" -> s::petFlap;
            case "treat_dispenser" -> s::treatDispenser;
            case "incubator_in" -> s::incubatorIn;
            case "incubator_hatch" -> s::incubatorHatch;
            case "brush" -> s::brush;
            case "fetch_ball" -> s::fetchBall;
            case "feather_wand" -> s::featherWand;
            case "pager_sit" -> s::pagerSit;
            case "scratch_post" -> s::scratchPost;
            default -> null;
        };
        if (shot == null) {
            return false;
        }
        s.ready();
        shot.run();
        s.clear();
        return true;
    }

    // ------------------------------------------------------------------ the stage

    private void ready() {
        if (d.sp == null) {
            // in the film's world every structure gets its pet (the structure shots go looking for them)
            PetSpawns.RULES.replaceAll((k, r) -> new PetSpawns.Rule(r.species(), 1F));
            d.openWorld(SEED, true, false);
            for (String rule : new String[]{"advance_time false", "spawn_mobs false", "spawn_monsters false", "do_fire_tick false",
                    "fire_spread_radius_around_player 0", "mob_griefing false", "do_patrol_spawning false", "spawn_patrols false",
                    "spawn_phantoms false", "spawn_wandering_traders false"}) {
                d.cmd("gamerule " + rule);
            }
            d.cmd("time set 5000");
            d.cmd("effect give @p minecraft:saturation infinite 0 true");
            d.cmd("effect give @p minecraft:resistance infinite 4 true");
            stage = build();
            d.settle(300);
        }
        d.cmd("time set 5000");
        d.cmd("gamemode creative @p");
        // no stray animals or cave mobs near the stage: they only add noise to the sound log (cows stuck in the
        // levelled ground were dying in every shot)
        d.server(server -> {
            for (Entity e : server.overworld().getEntitiesOfClass(net.minecraft.world.entity.Mob.class, new AABB(stage).inflate(120, 80, 120),
                    m -> !(m instanceof TamaPet))) {
                e.discard();
            }
        });
        d.hud(false);
        d.cam.reset();
        // the player waits off stage: a free-camera shot must not find him standing in the picture (shots that need
        // him place him themselves); sounds still reach him from anywhere while filming (SoundRangeMixin)
        d.cam.playerLook(at(0, 0, -40), at(0, 0.5, 0), true);
        Cam.freeWalk = false;
        d.client(mc -> mc.options.guiScale().set(4));
    }

    /** Levels a 56 x 48 garden at spawn and builds the sets on it; returns the centre at ground level. */
    private BlockPos build() {
        BlockPos c = d.fromServer(server -> {
            ServerLevel l = server.overworld();
            BlockPos s = l.getRespawnData().pos();
            int y = l.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, s.getX(), s.getZ());
            return new BlockPos(s.getX(), Math.max(y, l.getSeaLevel() + 2), s.getZ());
        });
        int x = c.getX(), y = c.getY(), z = c.getZ();
        for (int dx = -28; dx < 28; dx += 14) {
            for (int dz = -24; dz < 24; dz += 12) {
                box(x + dx, y, z + dz, x + dx + 13, y + 24, z + dz + 11, "air");
                box(x + dx, y - 1, z + dz, x + dx + 13, y - 1, z + dz + 11, "grass_block");
                box(x + dx, y - 6, z + dz, x + dx + 13, y - 2, z + dz + 11, "dirt");
            }
        }
        for (int bx = x - 48; bx < x + 48; bx += 16) {
            for (int bz = z - 48; bz < z + 48; bz += 16) {
                d.cmd(String.format("fillbiome %d %d %d %d %d %d minecraft:flower_forest", bx, y - 8, bz, bx + 15, y + 40, bz + 15));
            }
        }
        d.run(5);
        d.server(server -> {
            ServerLevel l = server.overworld();
            var rnd = l.getRandom();
            String[] flowers = {"poppy", "dandelion", "cornflower", "oxeye_daisy", "azure_bluet", "allium", "short_grass", "short_grass", "short_grass"};
            for (int i = 0; i < 260; i++) {
                int fx = x - 27 + rnd.nextInt(55), fz = z - 23 + rnd.nextInt(47);
                if (Math.abs(fx - x) < 9 && Math.abs(fz - z) < 9) {
                    continue;   // the middle stays clear for the pets
                }
                var block = net.minecraft.core.registries.BuiltInRegistries.BLOCK.getValue(
                        net.minecraft.resources.Identifier.withDefaultNamespace(flowers[rnd.nextInt(flowers.length)]));
                BlockPos p = new BlockPos(fx, y, fz);
                if (l.getBlockState(p).isAir() && l.getBlockState(p.below()).is(Blocks.GRASS_BLOCK)) {
                    l.setBlockAndUpdate(p, block.defaultBlockState());
                }
            }
        });
        for (int[] t : new int[][]{{-24, -20}, {24, -20}, {-24, 20}, {22, 18}, {-6, 22}, {8, -22}}) {
            d.cmd(String.format("place feature minecraft:oak %d %d %d", x + t[0], y, z + t[1]));
        }
        // the furniture row (x +10 .. +20, z -6)
        d.server(server -> {
            ServerLevel l = server.overworld();
            l.setBlockAndUpdate(new BlockPos(x + 10, y, z - 6), ModBlocks.FOOD_BOWL.defaultBlockState().setValue(FoodBowlBlock.FILL, 3));
            l.setBlockAndUpdate(new BlockPos(x + 13, y, z - 6), ModBlocks.PET_BATH.defaultBlockState().setValue(PetBathBlock.FILLED, true));
            l.setBlockAndUpdate(new BlockPos(x + 16, y, z - 6), ModBlocks.BOUNCY_MUSHROOM.defaultBlockState());
            l.setBlockAndUpdate(new BlockPos(x + 19, y, z - 6), ModBlocks.RUNNING_WHEEL.defaultBlockState().setValue(RunningWheelBlock.FACING, Direction.NORTH));
            l.setBlockAndUpdate(new BlockPos(x + 22, y, z - 6), ModBlocks.PET_BED.defaultBlockState());
            l.setBlockAndUpdate(new BlockPos(x + 22, y, z - 3), ModBlocks.PET_HOUSE.defaultBlockState());
            l.setBlockAndUpdate(new BlockPos(x + 10, y, z - 3), ModBlocks.SCRATCHING_POST.defaultBlockState());
            l.setBlockAndUpdate(new BlockPos(x - 4, y, z - 6), Blocks.CAMPFIRE.defaultBlockState());
            l.setBlockAndUpdate(new BlockPos(x + 4, y, z + 10), Blocks.JUKEBOX.defaultBlockState());
        });
        // a pond (frost steps) and a lava pool with a stone rim (the ember pup)
        box(x - 22, y - 3, z - 14, x - 12, y - 1, z - 6, "water");
        box(x - 23, y - 4, z + 5, x - 13, y - 1, z + 13, "stone");
        box(x - 22, y - 3, z + 6, x - 14, y - 1, z + 12, "lava");
        // a stone wall with a diamond ore inside (the pebble golem)
        box(x - 3, y - 1, z - 18, x + 3, y + 3, z - 16, "stone");
        d.cmd(String.format("setblock %d %d %d minecraft:diamond_ore", x, y + 1, z - 17));
        // a little treasure room (the mimic): tuff bricks, chests, a vault and a trial spawner
        box(x + 14, y - 1, z + 8, x + 22, y - 1, z + 14, "tuff_bricks");
        box(x + 14, y, z + 14, x + 22, y + 4, z + 14, "tuff_bricks");
        box(x + 14, y, z + 8, x + 14, y + 4, z + 14, "tuff_bricks");
        box(x + 22, y, z + 8, x + 22, y + 4, z + 14, "tuff_bricks");
        box(x + 14, y + 4, z + 8, x + 22, y + 4, z + 14, "waxed_copper_bulb");
        d.cmd(String.format("setblock %d %d %d minecraft:chest[facing=north]", x + 16, y, z + 13));
        d.cmd(String.format("setblock %d %d %d minecraft:vault[facing=north]", x + 18, y, z + 13));
        d.cmd(String.format("setblock %d %d %d minecraft:chest[facing=north]", x + 20, y, z + 13));
        d.cmd(String.format("setblock %d %d %d minecraft:trial_spawner", x + 21, y, z + 10));
        d.cmd(String.format("setblock %d %d %d minecraft:barrel[facing=up]", x + 15, y, z + 10));
        d.run(10);
        d.cmd("kill @e[type=minecraft:item]");
        return c;
    }

    private void box(int x0, int y0, int z0, int x1, int y1, int z1, String block) {
        d.cmd(String.format("fill %d %d %d %d %d %d minecraft:%s", x0, y0, z0, x1, y1, z1, block));
    }

    private Vec3 at(double dx, double dy, double dz) {
        return new Vec3(stage.getX() + 0.5 + dx, stage.getY() + dy, stage.getZ() + 0.5 + dz);
    }

    private void clear() {
        d.server(server -> {
            ServerLevel l = server.overworld();
            for (TamaPet p : l.getEntitiesOfClass(TamaPet.class, new AABB(stage).inflate(400, 60, 400))) {
                p.discard();
            }
            for (Entity e : l.getEntitiesOfClass(ItemEntity.class, new AABB(stage).inflate(400, 60, 400))) {
                e.discard();
            }
            for (Entity e : l.getEntitiesOfClass(Husk.class, new AABB(stage).inflate(100))) {
                e.discard();
            }
            ServerPlayer p = d.player(server);
            p.getInventory().clearContent();
            p.setShiftKeyDown(false);
            p.setHealth(p.getMaxHealth());
            p.removeAllEffects();
        });
        d.cmd("effect give @p minecraft:saturation infinite 0 true");
        d.cmd("effect give @p minecraft:resistance infinite 4 true");
        d.client(mc -> {
            if (mc.gui.screen() != null) {
                mc.gui.setScreen(null);
            }
        });
        this.pets.clear();
        d.run(2);
    }

    /** Spawns a pet on the stage; {@code tame}: owned by the film player; {@code ai}: moves by itself. */
    private void pet(String name, PetSpecies s, Vec3 pos, float yaw, boolean tame, boolean ai) {
        UUID id = d.fromServer(server -> {
            ServerLevel l = server.overworld();
            TamaPet p = ModEntities.type(s).create(l, EntitySpawnReason.COMMAND);
            p.snapTo(pos.x, pos.y, pos.z, yaw, 0);
            p.setYHeadRot(yaw);
            p.setYBodyRot(yaw);
            if (tame) {
                p.tame(d.player(server));
            }
            p.setNoAi(!ai);
            p.setPersistenceRequired();
            l.addFreshEntity(p);
            return p.getUUID();
        });
        this.pets.put(name, id);
    }

    private void with(String name, Consumer<TamaPet> action) {
        UUID id = this.pets.get(name);
        d.server(server -> {
            if (server.overworld().getEntity(id) instanceof TamaPet p) {
                action.accept(p);
            }
        });
    }

    private Vec3 posOf(String name) {
        UUID id = this.pets.get(name);
        return d.fromServer(server -> server.overworld().getEntity(id) instanceof TamaPet p ? p.position() : Vec3.ZERO);
    }

    /** Where the client draws the pet (it trails the server by a few ticks of smoothing). */
    private Vec3 clientPos(String name) {
        int id = d.fromServer(server -> server.overworld().getEntity(this.pets.get(name)) instanceof TamaPet p ? p.getId() : -1);
        return d.ctx.computeOnClient(mc -> {
            Entity e = mc.level == null ? null : mc.level.getEntity(id);
            return e == null ? Vec3.ZERO : e.position();
        });
    }

    private void hold(ItemStack stack) {
        d.server(server -> d.player(server).setItemInHand(InteractionHand.MAIN_HAND, stack.copy()));
    }

    /** The player right-clicks the pet with what is in his hand (swinging it on screen). */
    private void use(String name, boolean sneaking) {
        d.client(mc -> mc.player.swing(InteractionHand.MAIN_HAND, net.minecraft.world.item.component.SwingAnimation.DEFAULT, false));
        with(name, p -> {
            ServerPlayer pl = d.player((MinecraftServer) p.level().getServer());
            pl.setShiftKeyDown(sneaking);
            p.mobInteract(pl, InteractionHand.MAIN_HAND);
            pl.setShiftKeyDown(false);
        });
    }

    private void track(int t, Vec3 eye, Vec3 look) {
        if (t <= 0) {
            d.cam.cutTo(eye, look);
        } else {
            d.cam.moveTo(eye, look);
        }
    }

    private static Vec3 lerp(Vec3 a, Vec3 b, double f) {
        return new Vec3(FilmDirector.lerp(a.x, b.x, f), FilmDirector.lerp(a.y, b.y, f), FilmDirector.lerp(a.z, b.z, f));
    }

    // ------------------------------------------------------------------ the shots

    private void hookPetting() {
        pet("d", PetSpecies.DESERT_DRAGON, at(0, 0, 0), 180, true, false);
        Vec3 look = at(0, 0.5, 0);
        d.cam.cutTo(at(0.9, 1.0, -1.7), look);
        d.run(5);
        d.shoot("hook_petting", 4.5, t -> {
            double f = FilmDirector.ease(t, 0, 90);
            track(t, lerp(at(0.9, 1.0, -1.7), at(0.35, 0.85, -1.25), f), look);
            if (t == 6 || t == 50) {
                with("d", p -> p.pet(null));
            }
        });
    }

    private void lineup() {
        // a little crowd that fits a phone screen: four at the back, three, three in front
        PetSpecies[] all = PetSpecies.values();
        double[][] spots = {{-1.7, 1.3}, {-0.57, 1.45}, {0.57, 1.45}, {1.7, 1.3}, {-1.15, 0.2}, {0, 0.3}, {1.15, 0.2}, {-1.2, -0.95}, {0, -0.9}, {1.2, -0.95}};
        int[] order = {2, 5, 9, 0, 6, 1, 7, 4, 3, 8};
        for (int i = 0; i < all.length; i++) {
            double[] sp = spots[order[i]];
            pet("p" + i, all[i], at(sp[0], 0, sp[1]), 180 + (float) sp[0] * 9, true, false);
        }
        d.run(5);
        Vec3 look = at(0, 0.45, 0.2);
        d.shoot("lineup_dolly", 8.5, t -> {
            double f = FilmDirector.ease(t, 0, 170);
            track(t, lerp(at(-0.8, 1.9, -6.0), at(0.5, 1.4, -4.0), f), look);
            if (t % 12 == 6) {
                with("p" + (t / 12 % 10), p -> p.pet(null));
            }
        });
    }

    private void pettingCloseups() {
        PetSpecies[] who = {PetSpecies.FROST_PENGUIN, PetSpecies.VOID_KITTEN, PetSpecies.TIDE_DRAGON};
        for (int i = 0; i < who.length; i++) {
            pet("p" + i, who[i], at(-2 + i * 2, 0, 0), 180, true, false);
        }
        d.run(5);
        d.shoot("petting_closeups", 5, t -> {
            double f = FilmDirector.ease(t, 0, 100);
            Vec3 eye = lerp(at(-2.6, 0.95, -1.5), at(2.6, 0.95, -1.5), f);
            track(t, eye, new Vec3(eye.x * 0.7 + at(0, 0, 0).x * 0.3, at(0, 0.45, 0).y, at(0, 0, 0).z));
            if (t == 4) with("p0", p -> p.pet(null));
            if (t == 36) with("p1", p -> p.pet(null));
            if (t == 68) with("p2", p -> p.pet(null));
        });
    }

    private void tame() {
        pet("d", PetSpecies.DESERT_DRAGON, at(0, 0, 2.2), 180, false, false);
        hold(new ItemStack(ModItems.TAMAGOTCHI_HEART));
        d.hud(true);
        d.cam.player();
        d.cam.playerLook(at(0, 0, -0.6), at(0, 0.4, 2.2), true);
        d.run(8);
        d.shoot("tame_heart", 5, t -> {
            d.cam.playerLook(lerp(at(0, 0, -0.6), at(0, 0, 0.4), FilmDirector.ease(t, 0, 30)), at(0, 0.4, 2.2), false);
            if (t == 36) {
                use("d", false);
            }
        });
        d.hud(false);
    }

    private void backpack() {
        pet("d", PetSpecies.JUNGLE_DRAGON, at(0, 0, 1.6), 0, true, false);
        hold(new ItemStack(Items.CHEST));
        d.cam.playerLook(at(0, 0, 0), at(0, 0.5, 1.6), true);
        d.client(mc -> mc.player.setShiftKeyDown(true));
        Vec3 look = at(0, 0.6, 1.4);
        d.cam.cutTo(at(2.2, 1.4, 0.4), look);
        d.run(5);
        d.shoot("backpack_on", 4.5, t -> {
            track(t, lerp(at(2.2, 1.4, 0.4), at(1.9, 1.5, 2.6), FilmDirector.ease(t, 0, 90)), look);
            if (t == 28) {
                use("d", true);
            }
        });
        d.client(mc -> mc.player.setShiftKeyDown(false));
    }

    private void bowl() {
        pet("p", PetSpecies.EMBER_PUP, at(10, 0, -4.9), 180, true, false);
        Vec3 look = at(10, 0.35, -5.6);
        d.cam.cutTo(at(11.3, 1.0, -3.6), look);
        d.run(5);
        d.shoot("bowl_eat", 3.5, t -> {
            track(t, lerp(at(11.3, 1.0, -3.6), at(10.9, 0.9, -3.4), FilmDirector.ease(t, 0, 70)), look);
            if (t % 40 == 1) {
                with("p", p -> p.eat(new ItemStack(ModItems.PET_KIBBLE)));   // as at the bowl: animation, munch and crumbs
            }
        });
    }

    private void bath() {
        pet("p", PetSpecies.JUNGLE_DRAGON, at(13, 0, -6), 180, true, false);
        with("p", p -> p.setFlag(TamaPet.F_BATHING, true));
        Vec3 look = at(13, 0.6, -6);
        d.cam.cutTo(at(13.8, 1.4, -4.2), look);
        d.run(5);
        d.shoot("bath", 3.5, t -> {
            track(t, lerp(at(13.8, 1.4, -4.2), at(13.4, 1.3, -4.0), FilmDirector.ease(t, 0, 70)), look);
            if (t % 6 == 0) {
                d.server(server -> server.overworld().sendParticles(ParticleTypes.SPLASH, look.x, look.y + 0.1, look.z, 6, 0.3, 0.1, 0.3, 0.1));
            }
            if (t % 10 == 0 && t < 52) {
                with("p", p -> p.playSound(ModSounds.PET_SPLASH, 0.6F, 1.0F + p.getRandom().nextFloat() * 0.3F));   // as in the bath goal
            }
            if (t == 52) {
                with("p", p -> {
                    p.setFlag(TamaPet.F_BATHING, false);
                    p.playAction(PetAction.SHAKE);
                    p.playSound(ModSounds.PET_SHAKE, 0.7F, 1.0F);
                });
            }
        });
    }

    private void bounce() {
        pet("p", PetSpecies.HEX_TOAD, at(16, 0.65, -6), 200, true, false);
        Vec3 look = at(16, 1.0, -6);
        d.cam.cutTo(at(17.3, 1.3, -3.9), look);
        d.run(5);
        d.shoot("bounce", 3.5, t -> {
            track(t, at(17.3, 1.3, -3.9), look);
            int ph = t % 16;
            double h = Math.sin(ph / 16.0 * Math.PI) * 1.1;
            with("p", p -> p.setPos(stage.getX() + 16.5, stage.getY() + 0.65 + h, stage.getZ() - 5.5));
            if (ph == 0) {
                with("p", p -> p.playAction(PetAction.BOUNCE));
                d.server(server -> BouncyMushroomBlock.squish(server.overworld(), stage.offset(16, 0, -6)));
            }
        });
    }

    private void wheel() {
        pet("p", PetSpecies.VOID_KITTEN, at(19, 0.13, -6), Direction.EAST.toYRot(), true, false);
        with("p", p -> p.setFlag(TamaPet.F_RUNNING, true));
        d.server(server -> RunningWheelBlock.setRunning(server.overworld(), stage.offset(19, 0, -6), true));
        Vec3 look = at(19, 0.65, -6);
        d.cam.cutTo(at(19.6, 1.1, -8.3), look);
        d.run(10);
        d.shoot("wheel", 3.5, t -> {
            track(t, lerp(at(19.6, 1.1, -8.3), at(18.9, 1.0, -8.0), FilmDirector.ease(t, 0, 70)), look);
            // the running pet keeps the wheel turning (and rattling) every tick, as in the goal
            d.server(server -> RunningWheelBlock.setRunning(server.overworld(), stage.offset(19, 0, -6), true));
        });
        d.server(server -> RunningWheelBlock.setRunning(server.overworld(), stage.offset(19, 0, -6), false));
    }

    private void bed() {
        pet("p", PetSpecies.FROST_PENGUIN, at(22, 0, -6), 200, true, false);
        with("p", p -> p.setSleeping(true));
        Vec3 look = at(22, 0.4, -6);
        d.cam.cutTo(at(23.2, 1.2, -4.4), look);
        d.run(10);
        d.shoot("bed_sleep", 3.5, t -> {
            track(t, lerp(at(23.2, 1.2, -4.4), at(22.9, 1.0, -4.7), FilmDirector.ease(t, 0, 70)), look);
            if (t % 24 == 0) {
                d.server(server -> server.overworld().sendParticles(net.kasax.tamagotchi.registry.ModParticles.ZZZ, look.x, look.y + 0.5, look.z, 1, 0.1, 0.05, 0.1, 0));
            }
            if (t == 12 || t == 52) {
                with("p", p -> p.playSound(ModSounds.PET_SNORE, 0.4F, 1.1F));   // a sleeping pet snores now and then
            }
        });
    }

    private void laser() {
        PetSpecies[] who = {PetSpecies.VOID_KITTEN, PetSpecies.EMBER_PUP, PetSpecies.FROST_PENGUIN};
        for (int i = 0; i < who.length; i++) {
            pet("p" + i, who[i], at(-1.5 + i * 1.5, 0, 3), 180, true, true);
            with("p" + i, p -> p.setMode(TamaPet.Mode.FOLLOW));
        }
        d.cam.playerLook(at(0, 0, -3), at(0, 0, 3), true);
        hold(new ItemStack(ModItems.LASER_POINTER));
        Vec3 look = at(0, 0.2, 3);
        d.cam.cutTo(at(-0.6, 2.4, -0.6), look);
        d.run(5);
        d.shoot("laser_chase", 5, t -> {
            double a = t * 0.06;
            Vec3 dot = at(Math.sin(a) * 1.8, 0.03, 3.2 + Math.sin(a * 2) * 0.9);
            d.server(server -> LaserPointerItem.pointAt(server.overworld(), d.player(server), dot));
            track(t, at(-0.6, 2.4, -0.6), lerp(look, dot, 0.3));
        });
    }

    private void feedOwner() {
        d.cmd("gamemode survival @p");
        d.cmd("effect clear @p minecraft:resistance");
        pet("d", PetSpecies.TIDE_DRAGON, at(0.8, 0, 3.6), 180, true, true);
        with("d", p -> {
            p.setMode(TamaPet.Mode.FOLLOW);
            p.equipBackpack();
            p.store(new ItemStack(Items.GOLDEN_APPLE, 3));
        });
        d.hud(true);
        d.cam.player();
        d.cam.playerLook(at(0, 0, -1), at(0, 0.3, 4), true);
        d.run(30);
        d.server(server -> d.player(server).setHealth(4F));
        d.shoot("feed_owner", 6, t -> d.cam.playerLook(at(0, 0, -1), posOf("d").add(0, 0.9, 0), false));
        d.hud(false);
        d.cmd("gamemode creative @p");
    }

    private void roast() {
        pet("d", PetSpecies.DESERT_DRAGON, at(0, 0, 1.3), 180, true, false);
        hold(new ItemStack(Items.BEEF));
        d.cam.playerLook(at(0.4, 0, -1.4), at(0, 0.5, 1.3), true);
        Vec3 look = at(0, 0.6, 1.0);
        d.cam.cutTo(at(-1.9, 1.1, 0.4), look);
        d.run(5);
        d.shoot("roast", 4, t -> {
            track(t, lerp(at(-1.9, 1.1, 0.4), at(-1.6, 1.0, 1.0), FilmDirector.ease(t, 0, 80)), look);
            if (t == 20) {
                use("d", false);
            }
        });
    }

    private void ore() {
        pet("g", PetSpecies.PEBBLE_GOLEM, at(0, 0, -14.6), 180, true, true);
        with("g", p -> p.setMode(TamaPet.Mode.SIT));
        d.cam.playerLook(at(3.5, 0, -9.0), at(0, 1, -17), true);
        d.cam.cutTo(at(1.4, 1.5, -12.2), at(0, 1.0, -16.5));
        d.run(150);   // talents warm up after taming
        d.shoot("ore_glow", 5, t -> track(t, lerp(at(1.4, 1.5, -12.2), at(0.8, 1.4, -12.6), FilmDirector.ease(t, 0, 100)), at(0, 1.0, -16.5)));
    }

    private void frost() {
        pet("p", PetSpecies.FROST_PENGUIN, at(-10.2, 0, -10.6), 90, true, true);
        with("p", p -> p.setMode(TamaPet.Mode.FOLLOW));
        d.cmd("gamemode survival @p");
        d.cam.playerLook(at(-11.5, 0, -10), at(-20, 0, -10), true);
        Cam.freeWalk = true;
        d.run(10);
        d.cam.cutTo(at(-9.5, 2.6, -6.5), at(-12, 0, -10));
        d.ctx.getInput().holdKey(o -> o.keyUp);
        d.shoot("frost_steps", 5, t -> {
            d.cam.playerAim(at(-30, 1.6, -10));
            Vec3 me = d.ctx.computeOnClient(mc -> mc.player.position());
            track(t, me.add(2.6, 2.3, 3.6), me.add(0.8, 0.2, 0));
        });
        d.ctx.getInput().releaseKey(o -> o.keyUp);
        Cam.freeWalk = false;
        d.cmd("gamemode creative @p");
        box(stage.getX() - 22, stage.getY() - 3, stage.getZ() - 14, stage.getX() - 12, stage.getY() - 1, stage.getZ() - 6, "water");
    }

    private void lava() {
        pet("p", PetSpecies.EMBER_PUP, at(-21.5, -0.6, 9), 90, true, true);
        with("p", p -> p.setMode(TamaPet.Mode.FOLLOW));
        d.cam.playerLook(at(-11.5, 0, 9), at(-18, 0, 9), true);
        d.cam.cutTo(at(-17.5, 2.6, 4.2), at(-18, -0.5, 9));
        d.run(3);
        d.shoot("lava_swim", 4, t -> track(t, lerp(at(-19.5, 2.6, 4.2), at(-15.5, 2.4, 4.4), FilmDirector.ease(t, 0, 80)), posOf("p").add(0, 0.3, 0)));
    }

    private void fly() {
        pet("d", PetSpecies.DESERT_DRAGON, at(6, 0, -12), 0, true, true);
        with("d", p -> p.setMode(TamaPet.Mode.FOLLOW));
        Vec3[] feet = {at(6, 0, -10)};
        d.cam.playerLook(feet[0], feet[0].add(0, 1.4, 5), true);
        Cam.freeWalk = true;   // under the free camera the player only tells the server where it went while this is on
        d.run(10);
        d.shoot("fly_follow", 6, t -> {
            if (t > 0 && t < 60) {
                feet[0] = feet[0].add(0, 0, 0.6);   // faster than the dragon walks: it takes off
                d.cam.playerLook(feet[0], feet[0].add(0, 1.4, 5), false);
            }
            Vec3 dragon = clientPos("d");
            track(t, new Vec3(dragon.x + 3.0, dragon.y + 0.9, dragon.z - 1.2), dragon.add(0, 0.4, 0));
        });
        Cam.freeWalk = false;
    }

    private void fight() {
        pet("a", PetSpecies.EMBER_PUP, at(-1, 0, 0), 0, true, true);
        pet("b", PetSpecies.MIMIC, at(1, 0, 0), 0, true, true);
        d.cam.playerLook(at(0, 0, -2), at(0, 1, 4), true);
        UUID[] husks = new UUID[2];
        d.server(server -> {
            ServerLevel l = server.overworld();
            for (int i = 0; i < 2; i++) {
                Husk h = EntityTypes.HUSK.create(l, EntitySpawnReason.COMMAND);
                Vec3 p = at(-1.5 + i * 3, 0, 4.5);
                h.snapTo(p.x, p.y, p.z, 180, 0);
                l.addFreshEntity(h);
                husks[i] = h.getUUID();
            }
        });
        with("a", p -> p.setTarget((net.minecraft.world.entity.LivingEntity) p.level().getServer().overworld().getEntity(husks[0])));
        with("b", p -> p.setTarget((net.minecraft.world.entity.LivingEntity) p.level().getServer().overworld().getEntity(husks[1])));
        d.cam.cutTo(at(3.8, 1.8, 0.2), at(0, 0.6, 3));
        d.shoot("fight", 4.5, t -> track(t, lerp(at(3.8, 1.8, 0.2), at(3.2, 1.6, 1.4), FilmDirector.ease(t, 0, 90)), at(0, 0.6, 3)));
    }

    private void faint() {
        pet("d", PetSpecies.FROST_PENGUIN, at(0, 0, 1.6), 180, true, false);
        hold(new ItemStack(Items.AIR));
        d.cam.player();
        d.cam.playerLook(at(0, 0, -0.4), at(0, 0.2, 1.6), true);
        d.hud(true);
        d.run(5);
        d.shoot("faint_egg", 6, t -> {
            if (t == 12) {
                with("d", p -> p.hurtServer((ServerLevel) p.level(), p.damageSources().generic(), 1000F));
            }
            if (t == 60) {
                d.server(server -> {
                    ServerLevel l = server.overworld();
                    ServerPlayer pl = d.player(server);
                    for (ItemEntity e : l.getEntitiesOfClass(ItemEntity.class, new AABB(stage).inflate(6))) {
                        if (e.getItem().is(ModItems.TAMA_EGG)) {
                            pl.setItemInHand(InteractionHand.MAIN_HAND, e.getItem().copy());
                            e.discard();
                        }
                    }
                });
            }
            if (t == 92) {
                d.client(mc -> mc.player.swing(InteractionHand.MAIN_HAND, net.minecraft.world.item.component.SwingAnimation.DEFAULT, false));
                d.server(server -> {
                    ServerPlayer pl = d.player(server);
                    BlockPos ground = stage.offset(0, -1, 1);
                    ItemStack egg = pl.getMainHandItem();
                    if (egg.getItem() instanceof TamaEggItem item) {
                        item.useOn(new UseOnContext(pl, InteractionHand.MAIN_HAND,
                                new BlockHitResult(Vec3.atCenterOf(ground).add(0, 0.5, 0), Direction.UP, ground, false)));
                    }
                });
            }
        });
        d.hud(false);
    }

    private void dance() {
        PetSpecies[] who = {PetSpecies.HEX_TOAD, PetSpecies.JUNGLE_DRAGON, PetSpecies.FROST_PENGUIN};
        for (int i = 0; i < who.length; i++) {
            pet("p" + i, who[i], at(2.6 + i * 1.3, 0, 9.6 - (i == 1 ? 0.8 : 0)), 200, true, false);
            with("p" + i, p -> p.setFlag(TamaPet.F_DANCING, true));
        }
        Vec3 look = at(4, 0.5, 9.8);
        d.cam.cutTo(at(5.2, 1.4, 6.8), look);
        d.run(5);
        d.shoot("dance", 3.5, t -> {
            if (t == 0) {   // the record starts with the shot, so the sound log has it
                d.server(server -> {
                    if (server.overworld().getBlockEntity(stage.offset(4, 0, 10)) instanceof JukeboxBlockEntity box) {
                        box.setTheItem(new ItemStack(Items.MUSIC_DISC_CAT));
                    }
                });
            }
            track(t, lerp(at(5.2, 1.4, 6.8), at(3.6, 1.4, 6.9), FilmDirector.ease(t, 0, 70)), look);
            if (t % 10 == 0) {
                d.server(server -> server.overworld().sendParticles(ParticleTypes.NOTE, stage.getX() + 4.5, stage.getY() + 1.2, stage.getZ() + 10.5,
                        1, 0.2, 0.1, 0.2, 1));
            }
        });
        d.server(server -> {
            if (server.overworld().getBlockEntity(stage.offset(4, 0, 10)) instanceof JukeboxBlockEntity box) {
                box.popOutTheItem();
            }
        });
        d.cmd("kill @e[type=minecraft:item]");
    }

    private void campfire() {
        d.cmd("time set 14500");
        PetSpecies[] who = {PetSpecies.FROST_PENGUIN, PetSpecies.EMBER_PUP};
        for (int i = 0; i < who.length; i++) {
            pet("p" + i, who[i], at(-5.15 + i * 2.3, 0, -5.5), i == 0 ? -90 : 90, true, false);
            with("p" + i, p -> {
                p.setFlag(TamaPet.F_WARMING, true);
                p.setInSittingPose(true);
            });
        }
        Vec3 look = at(-4, 0.35, -5.6);
        d.cam.cutTo(at(-4.0, 1.5, -1.9), look);
        d.run(10);
        d.shoot("campfire_warm", 3.5, t -> track(t, lerp(at(-4.0, 1.5, -1.9), at(-4.2, 1.3, -2.5), FilmDirector.ease(t, 0, 70)), look));
        d.cmd("time set 5000");
    }

    private void petScreen() {
        pet("d", PetSpecies.DESERT_DRAGON, at(0, 0, 1.6), 180, true, false);
        with("d", p -> {
            p.equipBackpack();
            p.store(new ItemStack(Items.GOLDEN_APPLE, 3));
            p.store(new ItemStack(ModItems.PET_KIBBLE, 16));
            p.store(new ItemStack(Items.BREAD, 9));
            p.needs().hunger = 55;
            p.needs().fun = 90;
            p.needs().energy = 70;
            p.needs().hygiene = 35;
            p.needs().bond = 70;
        });
        d.client(mc -> mc.options.guiScale().set(3));
        d.cam.player();
        d.cam.playerLook(at(0, 0, -0.6), at(0, 0.4, 1.6), true);
        d.hud(true);
        d.run(5);
        d.server(server -> {
            ServerLevel l = server.overworld();
            for (TamaPet p : l.getEntitiesOfClass(TamaPet.class, new AABB(stage).inflate(4))) {
                p.openPetScreen(d.player(server));
            }
        });
        d.run(5);
        d.shoot("pet_screen", 4, t -> {
        });
        d.hud(false);
    }

    private void tamacon() {
        d.client(mc -> mc.options.guiScale().set(3));
        d.cam.player();
        d.cam.playerLook(at(0, 0, -0.6), at(0, 1, 6), true);
        d.client(mc -> mc.gui.setScreen(new net.kasax.tamagotchi.client.screen.TamaconScreen()));
        d.run(3);
        d.shoot("tamacon_book", 5, t -> {
            if (t == 30 || t == 60) {
                d.ctx.getInput().pressKey(com.mojang.blaze3d.platform.InputConstants.KEY_RIGHT);
            }
        });
    }

    /** Places a structure far from the garden with its pet forced in, and films the wild pet in it. */
    private void structure(String id, PetSpecies species, BlockPos at, String shot, Vec3 offset) {
        var saved = new HashMap<>(PetSpawns.RULES);
        PetSpawns.RULES.replaceAll((k, r) -> new PetSpawns.Rule(r.species(), 1F));
        d.cam.player();
        d.cam.playerLook(new Vec3(at.getX(), 140, at.getZ()), new Vec3(at.getX(), 60, at.getZ() + 5), true);
        d.settle(300);
        BlockPos base = d.fromServer(server -> {
            ServerLevel l = server.overworld();
            return new BlockPos(at.getX(), l.getHeight(Heightmap.Types.WORLD_SURFACE, at.getX(), at.getZ()), at.getZ());
        });
        d.cam.playerLook(new Vec3(base.getX(), base.getY() + 30, base.getZ()), Vec3.atCenterOf(base), true);
        d.settle(100);
        d.cmd(String.format("place structure minecraft:%s %d %d %d", id, base.getX(), base.getY(), base.getZ()));
        PetSpawns.RULES.clear();
        PetSpawns.RULES.putAll(saved);
        d.run(20);
        UUID found = d.fromServer(server -> {
            for (TamaPet p : server.overworld().getEntitiesOfClass(TamaPet.class, new AABB(base).inflate(64, 80, 64))) {
                if (p.species() == species) {
                    p.setNoAi(true);
                    return p.getUUID();
                }
            }
            return null;
        });
        if (found == null) {
            FilmDirector.LOG.warn("[Film] no {} in the placed {}", species.id(), id);
            return;
        }
        this.pets.put("w", found);
        Vec3 p = posOf("w");
        Vec3 look = p.add(0, 0.5, 0);
        Vec3 off = clearView(look, offset);
        d.cam.cutTo(p.add(off), look);
        d.run(10);
        d.shoot(shot, 4.5, t -> track(t, lerp(p.add(off), p.add(off.scale(0.75)).add(0, 0.1, 0), FilmDirector.ease(t, 0, 90)), look));
        d.still(shot);
    }

    /** The first of sixteen directions round {@code look} from which the camera sees it unblocked. */
    private Vec3 clearView(Vec3 look, Vec3 preferred) {
        double r = Math.hypot(preferred.x, preferred.z), h = preferred.y;
        double a0 = Math.atan2(preferred.z, preferred.x);
        return d.fromServer(server -> {
            ServerLevel l = server.overworld();
            for (double scale : new double[]{1.0, 0.7, 0.5}) {
                for (int i = 0; i < 16; i++) {
                    double a = a0 + (i % 2 == 0 ? 1 : -1) * ((i + 1) / 2) * Math.PI / 8;
                    Vec3 off = new Vec3(Math.cos(a) * r * scale, h * scale, Math.sin(a) * r * scale);
                    Vec3 eye = look.add(off).subtract(0, 0.5, 0);
                    var hit = l.clip(new net.minecraft.world.level.ClipContext(look, eye.add(off.normalize().scale(0.4)),
                            net.minecraft.world.level.ClipContext.Block.VISUAL, net.minecraft.world.level.ClipContext.Fluid.NONE,
                            net.minecraft.world.phys.shapes.CollisionContext.empty()));
                    if (hit.getType() == net.minecraft.world.phys.HitResult.Type.MISS) {
                        return off;
                    }
                }
            }
            return preferred;
        });
    }

    /** The nearest naturally generated structure of a kind, visited: its wild pet (every structure has one here). */
    private void natural(String structure, PetSpecies species, String shot) {
        BlockPos found = d.fromServer(server -> {
            ServerLevel l = server.overworld();
            var key = net.minecraft.resources.ResourceKey.create(net.minecraft.core.registries.Registries.STRUCTURE,
                    net.minecraft.resources.Identifier.withDefaultNamespace(structure));
            var holder = l.registryAccess().lookupOrThrow(net.minecraft.core.registries.Registries.STRUCTURE).getOrThrow(key);
            var r = l.getChunkSource().getGenerator().findNearestMapStructure(l, net.minecraft.core.HolderSet.direct(holder), stage, 100, false);
            return r == null ? null : r.getFirst();
        });
        if (found == null) {
            FilmDirector.LOG.warn("[Film] no {} found", structure);
            return;
        }
        d.cam.player();
        d.cam.playerLook(new Vec3(found.getX(), 150, found.getZ()), new Vec3(found.getX(), 60, found.getZ() + 5), true);
        d.settle(400);
        UUID id = null;
        for (int i = 0; i < 20 && id == null; i++) {
            d.run(10);
            id = d.fromServer(server -> {
                for (TamaPet p : server.overworld().getEntitiesOfClass(TamaPet.class, new AABB(found).inflate(96, 120, 96))) {
                    if (p.species() == species && !p.isTame()) {
                        p.setNoAi(true);
                        return p.getUUID();
                    }
                }
                return null;
            });
        }
        if (id == null) {
            FilmDirector.LOG.warn("[Film] the {} at {} has no {}", structure, found, species.id());
            return;
        }
        this.pets.put("w", id);
        Vec3 p = posOf("w");
        d.cam.playerLook(p.add(0, 12, 0), p, true);
        d.run(20);
        Vec3 look = p.add(0, 0.5, 0);
        Vec3 off = clearView(look, new Vec3(2.6, 1.4, 2.6));
        d.cam.cutTo(p.add(off), look);
        d.cam.nightVision();   // the halls inside are dim
        d.run(10);
        d.shoot(shot, 4.5, t -> track(t, lerp(p.add(off), p.add(off.scale(0.72)).add(0, 0.1, 0), FilmDirector.ease(t, 0, 90)), look));
    }

    private void igloo() {
        BlockPos base = stage.offset(-60, 0, 0);
        d.cam.playerLook(new Vec3(base.getX(), base.getY() + 20, base.getZ() - 10), Vec3.atCenterOf(base), true);
        d.settle(150);
        box(base.getX() - 12, base.getY(), base.getZ() - 12, base.getX() + 12, base.getY() + 12, base.getZ() + 12, "air");
        box(base.getX() - 12, base.getY() - 3, base.getZ() - 12, base.getX() + 12, base.getY() - 1, base.getZ() + 12, "snow_block");
        d.cmd(String.format("fillbiome %d %d %d %d %d %d minecraft:snowy_plains", base.getX() - 16, base.getY() - 4, base.getZ() - 16,
                base.getX() + 15, base.getY() + 20, base.getZ() + 15));
        d.cmd(String.format("place template minecraft:igloo/top %d %d %d", base.getX() - 3, base.getY(), base.getZ() - 3));
        d.run(10);
        // where is the door? the open block at ground level on the template's edge
        BlockPos door = d.fromServer(server -> {
            ServerLevel l = server.overworld();
            for (int dx = -4; dx <= 6; dx++) {
                for (int dz = -4; dz <= 6; dz++) {
                    BlockPos q = base.offset(dx, 0, dz);
                    boolean edge = l.getBlockState(q).isAir() && l.getBlockState(q.above()).isAir()
                            && (l.getBlockState(q.north()).is(Blocks.SNOW_BLOCK) || l.getBlockState(q.south()).is(Blocks.SNOW_BLOCK))
                            && l.getBlockState(q.east()).is(Blocks.SNOW_BLOCK) && l.getBlockState(q.west()).is(Blocks.SNOW_BLOCK);
                    if (edge) {
                        return q;
                    }
                }
            }
            return base.offset(0, 0, 5);
        });
        boolean southDoor = d.fromServer(server -> server.overworld().getBlockState(door.north()).is(Blocks.SNOW_BLOCK));
        Vec3 out = Vec3.atBottomCenterOf(door).add(0, 0, southDoor ? 1.6 : -1.6);
        pet("w", PetSpecies.FROST_PENGUIN, out, southDoor ? 0 : 180, false, false);
        Vec3 look = out.add(0, 0.9, 0);
        Vec3 from = out.add(southDoor ? 3.4 : -3.4, 1.6, southDoor ? 4.4 : -4.4);
        Vec3 to = out.add(southDoor ? 2.0 : -2.0, 1.2, southDoor ? 2.8 : -2.8);
        d.cam.cutTo(from, look);
        d.run(10);
        d.shoot("igloo_penguin", 4.5, t -> {
            track(t, lerp(from, to, FilmDirector.ease(t, 0, 90)), look);
            if (t == 40) {
                with("w", p -> p.playAction(PetAction.LOOK_UP));
            }
        });
    }

    private void mimic() {
        pet("m", PetSpecies.MIMIC, at(18, 0, 11.5), 200, false, false);
        Vec3 look = at(18, 0.5, 11.5);
        d.cam.cutTo(at(19.2, 1.5, 8.6), look);
        d.run(5);
        d.shoot("mimic_chamber", 4, t -> {
            track(t, lerp(at(19.6, 1.5, 8.4), at(18.6, 1.3, 9.2), FilmDirector.ease(t, 0, 80)), look);
            if (t == 30) {
                with("m", p -> p.playAction(PetAction.ATTACK));
            }
        });
    }

    // ------------------------------------------------------------------ the furniture update (1.1)

    /** A block position on the stage. */
    private BlockPos sp(int dx, int dy, int dz) {
        return stage.offset(dx, dy, dz);
    }

    private String xyz(BlockPos p) {
        return p.getX() + " " + p.getY() + " " + p.getZ();
    }

    private void set(BlockPos p, String block) {
        d.cmd("setblock " + xyz(p) + " " + block);
    }

    /** Clears the stage's middle (where these shots build their sets) back to grass. */
    private void wipeMiddle() {
        box(stage.getX() - 6, stage.getY(), stage.getZ() - 4, stage.getX() + 6, stage.getY() + 4, stage.getZ() + 6, "air");
        box(stage.getX() - 6, stage.getY() - 1, stage.getZ() - 4, stage.getX() + 6, stage.getY() - 1, stage.getZ() + 6, "grass_block");
        d.cmd("kill @e[type=minecraft:item]");
    }

    /** The player right-clicks a block with what is in his hand, the way the game does it (the hand swings on screen). */
    private void useBlock(BlockPos pos, Direction face) {
        d.client(mc -> mc.player.swing(InteractionHand.MAIN_HAND, net.minecraft.world.item.component.SwingAnimation.DEFAULT, false));
        d.server(server -> {
            ServerPlayer pl = d.player(server);
            pl.gameMode.useItemOn(pl, server.overworld(), pl.getMainHandItem(), InteractionHand.MAIN_HAND,
                    new BlockHitResult(Vec3.atCenterOf(pos), face, pos, false));
        });
    }

    /** The player uses the item in his hand in the air (throws the ball, waves the wand). */
    private void useItem() {
        d.client(mc -> mc.player.swing(InteractionHand.MAIN_HAND, net.minecraft.world.item.component.SwingAnimation.DEFAULT, false));
        d.server(server -> {
            ServerPlayer pl = d.player(server);
            pl.gameMode.useItem(pl, server.overworld(), pl.getMainHandItem(), InteractionHand.MAIN_HAND);
        });
    }

    private void named(String name, String label) {
        with(name, p -> p.setCustomName(net.minecraft.network.chat.Component.literal(label)));
    }

    private void plushShelf() {
        // two rows of plushies, the back row up on a shelf of slabs
        PetSpecies[] all = PetSpecies.values();
        for (int i = 0; i < all.length; i++) {
            int x = i % 5 - 2, row = i / 5;
            if (row == 1) {
                set(sp(x, 0, 1), "minecraft:spruce_slab[type=top]");
            }
            set(sp(x, row, row), "tamagotchi:" + all[i].id() + "_plush[rotation=8]");
        }
        Vec3 look = at(0, 0.7, 0.6);
        d.cam.cutTo(at(-2.6, 1.25, -2.2), look);
        d.run(10);
        d.shoot("plush_shelf", 5, t -> {
            track(t, lerp(at(-2.6, 1.25, -2.2), at(2.4, 1.2, -2.0), FilmDirector.ease(t, 0, 100)), look);
            if (t == 22 || t == 50 || t == 78) {
                BlockPos plush = t == 22 ? sp(-1, 0, 0) : t == 50 ? sp(0, 1, 1) : sp(1, 0, 0);
                d.server(server -> net.kasax.tamagotchi.block.PlushBlock.squeeze(server.overworld(), plush));
            }
        });
        wipeMiddle();
    }

    private void plushSqueeze() {
        set(sp(0, 0, 1), "tamagotchi:frost_penguin_plush[rotation=8]");
        d.hud(true);
        d.cam.player();
        d.cam.playerLook(at(0, 0, -0.15), at(0, 0.35, 1), true);
        d.run(8);
        d.shoot("plush_squeeze", 4, t -> {
            if (t == 16 || t == 44 || t == 64) {
                useBlock(sp(0, 0, 1), Direction.NORTH);
            }
        });
        d.hud(false);
        wipeMiddle();
    }

    private void plushCuddle() {
        // a lonely toad cuddles its plush: what the toy goal does every 27 ticks (a squeeze, hearts, fun)
        set(sp(0, 0, 1), "tamagotchi:hex_toad_plush[rotation=5]");
        pet("t", PetSpecies.HEX_TOAD, at(-0.62, 0, 0.9), 290, true, false);
        with("t", p -> p.setInSittingPose(true));
        Vec3 look = at(-0.25, 0.35, 0.9);
        d.cam.cutTo(at(-0.9, 1.05, -1.2), look);
        d.run(8);
        d.shoot("plush_cuddle", 5, t -> {
            track(t, lerp(at(-0.9, 1.05, -1.2), at(0.3, 0.95, -1.15), FilmDirector.ease(t, 0, 100)), look);
            if (t % 27 == 4) {
                d.server(server -> net.kasax.tamagotchi.block.PlushBlock.squeeze(server.overworld(), sp(0, 0, 1)));
                with("t", p -> p.playAction(PetAction.PETTED));
            }
        });
        wipeMiddle();
    }

    private void plushSleep() {
        // a penguin asleep in its bed with its own plush next to it (it rests half again as fast)
        set(sp(0, 0, 1), "tamagotchi:pet_bed[color=light_blue]");
        set(sp(1, 0, 1), "tamagotchi:frost_penguin_plush[rotation=12]");
        pet("p", PetSpecies.FROST_PENGUIN, at(0, 0, 1), 200, true, false);
        with("p", p -> p.setSleeping(true));
        Vec3 look = at(0.5, 0.3, 1);
        d.cam.cutTo(at(-0.4, 1.3, -1.3), look);
        d.run(8);
        d.shoot("plush_sleep", 4.5, t -> {
            track(t, lerp(at(-0.4, 1.3, -1.3), at(0.4, 1.2, -1.2), FilmDirector.ease(t, 0, 90)), look);
            if (t % 24 == 0) {
                Vec3 z = at(0, 0.9, 1);
                d.server(server -> server.overworld().sendParticles(net.kasax.tamagotchi.registry.ModParticles.ZZZ, z.x, z.y, z.z, 1, 0.1, 0.05, 0.1, 0));
            }
            if (t == 20 || t == 66) {
                with("p", p -> p.playSound(ModSounds.PET_SNORE, 0.4F, 1.1F));
            }
        });
        wipeMiddle();
    }

    private void portrait() {
        // a wall with an empty portrait; a click paints the nearest pet, the next click the next one, a dye recolours it
        box(stage.getX() - 3, stage.getY(), stage.getZ() + 3, stage.getX() + 3, stage.getY() + 2, stage.getZ() + 3, "spruce_planks");
        set(sp(0, 1, 2), "tamagotchi:pet_portrait[facing=north]");
        pet("d", PetSpecies.DESERT_DRAGON, at(1.5, 0, 1.4), 200, true, false);
        named("d", "Sandy");
        with("d", p -> p.setInSittingPose(true));
        pet("p", PetSpecies.FROST_PENGUIN, at(-1.6, 0, 1.0), 160, true, false);
        named("p", "Waddles");
        with("p", p -> p.equipBackpack());
        d.hud(true);
        d.cam.player();
        d.cam.playerLook(at(0, 0, 0.35), at(0, 1.45, 2.4), true);
        d.run(8);
        d.shoot("portrait_paint", 6, t -> {
            if (t == 14 || t == 50) {
                useBlock(sp(0, 1, 2), Direction.NORTH);
            }
            if (t == 78) {
                hold(new ItemStack(Items.DYE.pick(net.minecraft.world.item.DyeColor.LIGHT_BLUE)));
            }
            if (t == 90) {
                useBlock(sp(0, 1, 2), Direction.NORTH);
            }
        });
        d.hud(false);
        wipeMiddle();
    }

    private void eggLamp() {
        // dusk: three lamps; one switched off and on again, one dyed
        d.cmd("time set 13200");
        set(sp(-1, 0, 1), "tamagotchi:egg_lamp[facing=north,color=pink,lit=true]");
        set(sp(0, 0, 1), "tamagotchi:egg_lamp[facing=north,color=light_blue,lit=true]");
        set(sp(1, 0, 1), "tamagotchi:egg_lamp[facing=north,color=yellow,lit=true]");
        d.hud(true);
        d.cam.player();
        d.cam.playerLook(at(0, 0, -1.2), at(0, 0.45, 1), true);
        d.run(10);
        d.shoot("egg_lamp", 5.5, t -> {
            if (t == 14 || t == 40) {
                useBlock(sp(0, 0, 1), Direction.NORTH);
            }
            if (t == 62) {
                hold(new ItemStack(Items.DYE.pick(net.minecraft.world.item.DyeColor.LIME)));
            }
            if (t == 74) {
                useBlock(sp(1, 0, 1), Direction.NORTH);
            }
            if (t == 90) {
                hold(new ItemStack(Items.DYE.pick(net.minecraft.world.item.DyeColor.PURPLE)));
            }
            if (t == 100) {
                useBlock(sp(-1, 0, 1), Direction.NORTH);
            }
        });
        d.hud(false);
        d.cmd("time set 5000");
        wipeMiddle();
    }

    private void dyeBed() {
        // a row of dyed beds and baskets; the red bed in front is dyed blue, then pink
        String[] beds = {"orange", "yellow", "lime", "purple"};
        for (int i = 0; i < beds.length; i++) {
            set(sp(i - 2 + (i >= 2 ? 1 : 0), 0, 3), "tamagotchi:pet_bed[color=" + beds[i] + "]");
        }
        set(sp(-2, 0, 2), "tamagotchi:pet_basket[facing=north,color=white]");
        set(sp(2, 0, 2), "tamagotchi:pet_basket[facing=north,color=magenta]");
        set(sp(0, 0, 1), "tamagotchi:pet_bed[color=red]");
        hold(new ItemStack(Items.DYE.pick(net.minecraft.world.item.DyeColor.BLUE)));
        d.hud(true);
        d.cam.player();
        d.cam.playerLook(at(0, 0, -1.4), at(0, 0.2, 1.4), true);
        d.run(8);
        d.shoot("dye_bed", 4.5, t -> {
            if (t == 20) {
                useBlock(sp(0, 0, 1), Direction.UP);
            }
            if (t == 46) {
                hold(new ItemStack(Items.DYE.pick(net.minecraft.world.item.DyeColor.PINK)));
            }
            if (t == 58) {
                useBlock(sp(0, 0, 1), Direction.UP);
            }
        });
        d.hud(false);
        wipeMiddle();
    }

    private void fillToyBox(BlockPos pos) {
        d.server(server -> {
            if (server.overworld().getBlockEntity(pos) instanceof net.kasax.tamagotchi.block.ToyBoxBlockEntity box) {
                box.setItem(0, new ItemStack(ModItems.SQUEAKY_BALL, 2));
                box.setItem(2, new ItemStack(ModItems.FEATHER_WAND));
                box.setItem(4, new ItemStack(ModBlocks.PLUSHES.get(PetSpecies.VOID_KITTEN)));
                box.setItem(6, new ItemStack(ModItems.LASER_POINTER));
                box.setItem(8, new ItemStack(Items.BONE));
            }
        });
    }

    private void toyBoxOpen() {
        set(sp(0, 0, 1), "tamagotchi:toy_box[facing=north]");
        fillToyBox(sp(0, 0, 1));
        d.hud(true);
        d.cam.player();
        d.cam.playerLook(at(0, 0, -1.0), at(0, 0.4, 1), true);
        d.run(8);
        d.shoot("toy_box_open", 4.5, t -> {
            if (t == 12) {
                useBlock(sp(0, 0, 1), Direction.NORTH);   // opens the 3 x 3 box screen
            }
            if (t == 62) {
                d.client(mc -> mc.player.closeContainer());
            }
        });
        d.hud(false);
        wipeMiddle();
    }

    private void toyBoxPlay() {
        // what the toy goal does: the lid opens, the pet takes a toy out and plays (a hop and a squeak every 30 ticks)
        BlockPos box = sp(0, 0, 1);
        set(box, "tamagotchi:toy_box[facing=north]");
        fillToyBox(box);
        pet("k", PetSpecies.VOID_KITTEN, at(0.2, 0, -0.1), 200, true, false);
        Vec3 look = at(0, 0.45, 0.6);
        d.cam.cutTo(at(1.9, 1.2, -1.6), look);
        d.run(8);
        d.shoot("toy_box_play", 5, t -> {
            track(t, lerp(at(1.9, 1.2, -1.6), at(1.2, 1.05, -1.9), FilmDirector.ease(t, 0, 100)), look);
            if (t == 6) {
                d.server(server -> {
                    if (server.overworld().getBlockEntity(box) instanceof net.kasax.tamagotchi.block.ToyBoxBlockEntity b) {
                        b.petPlay(110);
                    }
                });
            }
            if (t == 14) {
                with("k", p -> p.setCarried(new ItemStack(ModItems.SQUEAKY_BALL)));
            }
            int ph = (t - 20) % 30;
            if (t >= 20 && ph == 0) {
                with("k", p -> {
                    p.playAction(PetAction.PLAY);
                    p.playSound(ModSounds.TOY_SQUEAK, 0.6F, 1.0F + p.getRandom().nextFloat() * 0.4F);
                });
            }
            if (t >= 20) {
                double h = ph < 10 ? Math.sin(ph / 10.0 * Math.PI) * 0.45 : 0;
                with("k", p -> p.setPos(stage.getX() + 0.7, stage.getY() + h, stage.getZ() + 0.4));
            }
        });
        wipeMiddle();
    }

    private void petFlap() {
        // a wall with a pet flap: the pup runs through it to its owner, the flap swings and closes again
        box(stage.getX() - 4, stage.getY(), stage.getZ() + 2, stage.getX() + 4, stage.getY() + 2, stage.getZ() + 2, "oak_planks");
        set(sp(0, 0, 2), "tamagotchi:pet_flap[facing=north]");
        pet("p", PetSpecies.EMBER_PUP, at(0.3, 0, 5.5), 0, true, true);
        with("p", p -> p.setMode(TamaPet.Mode.WANDER));
        Vec3 look = at(0, 0.45, 1.6);
        d.cam.cutTo(at(-1.9, 1.25, -0.9), look);
        d.run(8);
        d.shoot("pet_flap", 6, t -> {
            track(t, lerp(at(-1.9, 1.25, -0.9), at(-1.3, 1.15, -0.8), FilmDirector.ease(t, 0, 120)), look);
            // out through the flap to the front, then back in again
            if (t == 4 || t == 24) {
                with("p", p -> p.getNavigation().moveTo(stage.getX() + 1.0, stage.getY(), stage.getZ() + 0.2, 1.0));
            }
            if (t == 62 || t == 80) {
                with("p", p -> p.getNavigation().moveTo(stage.getX() + 0.5, stage.getY(), stage.getZ() + 5.0, 1.0));
            }
        });
        wipeMiddle();
    }

    private void treatDispenser() {
        // a button press: one treat flies in an arc to the hungry pup, which jumps and catches it (side view: the
        // machine on the left, the pup two blocks to its right)
        BlockPos disp = sp(0, 0, 1);
        set(disp, "tamagotchi:treat_dispenser[facing=north]");
        set(sp(1, 0, 1), "minecraft:stone_button[face=floor,facing=north]");
        d.server(server -> {
            if (server.overworld().getBlockEntity(disp) instanceof net.kasax.tamagotchi.block.TreatDispenserBlockEntity b) {
                b.setItem(4, new ItemStack(ModItems.EMBER_JERKY, 3));
            }
        });
        pet("p", PetSpecies.EMBER_PUP, at(-1.6, 0, 1.2), 90, true, true);
        with("p", p -> {
            p.setOrderedToSit(true);
            p.needs().add(net.kasax.tamagotchi.pet.PetNeeds.Need.HUNGER, -60);
            p.syncNeeds();
        });
        Vec3 look = at(-0.55, 0.75, 1.1);
        d.cam.cutTo(at(-0.55, 1.45, -2.4), look);
        d.run(10);
        d.shoot("treat_dispenser", 6, t -> {
            track(t, lerp(at(-0.55, 1.45, -2.4), at(-0.45, 1.4, -2.15), FilmDirector.ease(t, 0, 120)), look);
            if (t == 10 || t == 70) {
                d.server(server -> {
                    ServerPlayer pl = d.player(server);
                    BlockPos b = sp(1, 0, 1);
                    pl.gameMode.useItemOn(pl, server.overworld(), ItemStack.EMPTY, InteractionHand.MAIN_HAND,
                            new BlockHitResult(Vec3.atCenterOf(b), Direction.UP, b, false));
                });
            }
        });
        wipeMiddle();
    }

    private ItemStack eggOf(PetSpecies s, String label) {
        pet("egg", s, at(0, 0, -8), 0, true, false);
        named("egg", label);
        ItemStack[] egg = {ItemStack.EMPTY};
        with("egg", p -> {
            egg[0] = TamaEggItem.fromPet(p);
            p.discard();
        });
        return egg[0];
    }

    private void incubatorIn() {
        set(sp(0, 0, 1), "tamagotchi:pet_incubator[facing=north]");
        hold(eggOf(PetSpecies.EMBER_PUP, "Cinder"));
        d.hud(true);
        d.cam.player();
        d.cam.playerLook(at(0, 0, -0.8), at(0, 0.4, 1), true);
        d.run(8);
        d.shoot("incubator_in", 4.5, t -> {
            if (t == 16) {
                useBlock(sp(0, 0, 1), Direction.NORTH);
            }
        });
        d.hud(false);
        // the egg stays in for the next shot
    }

    private void incubatorHatch() {
        BlockPos inc = sp(0, 0, 1);
        if (!d.fromServer(server -> server.overworld().getBlockEntity(inc) instanceof net.kasax.tamagotchi.block.PetIncubatorBlockEntity b
                && !b.getEgg().isEmpty())) {
            set(inc, "tamagotchi:pet_incubator[facing=north]");
            ItemStack egg = eggOf(PetSpecies.EMBER_PUP, "Cinder");
            d.server(server -> {
                if (server.overworld().getBlockEntity(inc) instanceof net.kasax.tamagotchi.block.PetIncubatorBlockEntity b) {
                    b.insert(egg, null);
                }
            });
        }
        // the last five seconds before it hatches: wobbling harder, three cracks, out comes the pup
        int left = d.fromServer(server -> server.overworld().getBlockEntity(inc) instanceof net.kasax.tamagotchi.block.PetIncubatorBlockEntity b
                ? Math.round((1 - b.progress(0)) * net.kasax.tamagotchi.block.PetIncubatorBlockEntity.HATCH_TICKS) : 0);
        d.run(Math.max(0, left - 110));
        Vec3 look = at(0, 0.45, 0.6);
        d.cam.cutTo(at(1.3, 1.0, -1.3), look);
        d.shoot("incubator_hatch", 6, t -> track(t, lerp(at(1.3, 1.0, -1.3), at(0.9, 0.9, -1.5), FilmDirector.ease(t, 0, 120)), look));
        wipeMiddle();
    }

    // ------------------------------------------------------------------ toys and tools the first videos left out

    private void brush() {
        pet("k", PetSpecies.VOID_KITTEN, at(0, 0, 1.4), 180, true, false);
        hold(new ItemStack(ModItems.PET_BRUSH));
        d.hud(true);
        d.cam.player();
        d.cam.playerLook(at(0, 0, -1.3), at(0, 0.4, 1.4), true);
        d.run(8);
        d.shoot("brush", 4, t -> {
            if (t == 12 || t == 44) {
                use("k", false);
            }
        });
        d.hud(false);
    }

    private void fetchBall() {
        pet("d", PetSpecies.JUNGLE_DRAGON, at(0.6, 0, 0.4), 180, true, true);
        with("d", p -> p.setMode(TamaPet.Mode.FOLLOW));
        hold(new ItemStack(ModItems.SQUEAKY_BALL, 4));
        d.hud(true);
        d.cam.player();
        d.cam.playerLook(at(0, 0, -1.5), at(0, 0.6, 6), true);
        d.run(10);
        d.shoot("fetch_ball", 7, t -> {
            if (t == 8) {
                useItem();
            }
            if (t > 30) {
                d.cam.playerLook(at(0, 0, -1.5), posOf("d").add(0, 0.6, 0), false);
            }
        });
        d.hud(false);
    }

    private void featherWand() {
        pet("p0", PetSpecies.VOID_KITTEN, at(-0.7, 0, 1.6), 180, true, true);
        pet("p1", PetSpecies.FROST_PENGUIN, at(0.8, 0, 1.8), 200, true, true);
        for (String n : new String[]{"p0", "p1"}) {
            with(n, p -> p.setOrderedToSit(false));
        }
        hold(new ItemStack(ModItems.FEATHER_WAND));
        d.hud(true);
        d.cam.player();
        d.cam.playerLook(at(0, 0, -0.8), at(0, 0.5, 1.7), true);
        d.run(8);
        d.shoot("feather_wand", 4.5, t -> {
            if (t == 10 || t == 40 || t == 70) {
                useItem();
            }
        });
        d.hud(false);
    }

    private void pagerSit() {
        pet("d", PetSpecies.TIDE_DRAGON, at(0, 0, 1.6), 180, true, true);
        with("d", p -> p.setMode(TamaPet.Mode.FOLLOW));
        hold(new ItemStack(ModItems.TAMA_PAGER));
        d.hud(true);
        d.cam.player();
        d.cam.playerLook(at(0, 0, -0.6), at(0, 0.5, 1.6), true);
        d.run(8);
        d.shoot("pager_sit", 4, t -> {
            if (t == 14 || t == 56) {
                use("d", false);
            }
        });
        d.hud(false);
    }

    private void scratchPost() {
        // what the scratch goal does: a swipe and a scratch every 40 ticks
        pet("p", PetSpecies.PEBBLE_GOLEM, at(11.45, 0, -3), 90, true, false);
        d.cam.playerLook(at(16, 0, 12), at(11, 0.5, -3), true);
        Vec3 look = at(10.6, 0.6, -3);
        d.cam.cutTo(at(11.6, 1.3, -0.9), look);
        d.run(5);
        d.shoot("scratch_post", 4, t -> {
            track(t, lerp(at(11.6, 1.3, -0.9), at(11.0, 1.2, -1.0), FilmDirector.ease(t, 0, 80)), look);
            if (t % 40 == 4) {
                with("p", p -> {
                    p.playAction(PetAction.SCRATCH);
                    p.playSound(net.minecraft.sounds.SoundEvents.WOOL_HIT, 0.6F, 1.2F);
                });
            }
        });
    }
}
