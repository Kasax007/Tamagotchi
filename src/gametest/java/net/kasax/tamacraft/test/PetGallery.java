package net.kasax.tamacraft.test;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import net.kasax.tamacraft.test.harness.FabricClientGameTest;
import net.kasax.tamacraft.test.harness.ClientGameTestContext;
import net.kasax.tamacraft.test.harness.TestServerContext;
import net.kasax.tamacraft.test.harness.TestWorldBuilder.TestSingleplayerContext;
import net.kasax.tamacraft.test.harness.TestScreenshotOptions;
import net.kasax.tamacraft.block.FoodBowlBlock;
import net.kasax.tamacraft.block.PetBathBlock;
import net.kasax.tamacraft.block.RunningWheelBlock;
import net.kasax.tamacraft.pet.PetAction;
import net.kasax.tamacraft.pet.PetSpecies;
import net.kasax.tamacraft.pet.TamaPet;
import net.kasax.tamacraft.registry.ModBlocks;
import net.kasax.tamacraft.registry.ModEntities;
import net.kasax.tamacraft.registry.ModItems;
import net.kasax.tamacraft.registry.ModTab;
import net.kasax.tamacraft.world.PetSpawns;
import net.minecraft.client.gui.screens.inventory.CreativeModeInventoryScreen;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Screenshot gallery for art review plus a few functional checks. Run headless with
 * {@code xvfb-run -a ./gradlew runClientGameTest}; screenshots land in build/run/clientGameTest/screenshots.
 */
public class PetGallery implements FabricClientGameTest {
    private static final Logger LOG = LoggerFactory.getLogger("TamaTest");
    private static final int Y = -60;   // flat world ground is at y=-61

    private ClientGameTestContext ctx;
    private TestServerContext server;
    private final List<String> results = new ArrayList<>();

    @Override
    public void runTest(ClientGameTestContext context) {
        String only = System.getProperty("tama.tests", "all");
        boolean checksOnly = only.contains("checks") && !only.contains("pets");   // -Ptests=checks: functional checks and real clicks only
        if (!only.equals("all") && !only.contains("pets") && !checksOnly) {
            return;
        }
        this.ctx = context;
        ctx.getInput().resizeWindow(1280, 800);
        ctx.runOnClient(mc -> mc.options.fov().set(60));
        hud(false);
        try (TestSingleplayerContext sp = ctx.worldBuilder().create()) {
            this.server = sp.getServer();
            cmd("gamemode creative @p");
            cmd("time set noon");
            cmd("weather clear");
            ctx.waitTicks(40);
            if (!checksOnly) {
                if (recipeViewerCheck()) {
                    return;
                }
                lineup(false);
                lineup(true);
                closeups();
                furniture();
                screen();
                live();
                extras();
            }
            checks();
            fixes();
        }
        if (!checksOnly) {
            naturalSpawns();
        }
        LOG.info("[TamaTest] ===== results =====");
        for (String r : this.results) {
            LOG.info("[TamaTest] {}", r);
        }
    }

    private void hud(boolean visible) {
        ctx.runOnClient(mc -> {
            mc.options.hideGui = !visible;
        });
    }

    private void cmd(String c) {
        this.server.runCommand(c);
    }

    /** Teleports the camera and keeps the player flying there (landing switches creative flight off). */
    private void cam(String where) {
        cmd("tp @p " + where);
        server.runOnServer(s -> {
            ServerPlayer p = player(s);
            p.getAbilities().flying = true;
            p.onUpdateAbilities();
        });
    }

    private void shot(String name) {
        ctx.waitTicks(2);
        ctx.takeScreenshot(TestScreenshotOptions.of(name).disableCounterPrefix());
    }

    private static ServerPlayer player(MinecraftServer s) {
        return s.getPlayerList().getPlayers().get(0);
    }

    private void clear() {
        server.runOnServer(s -> {
            ServerLevel level = s.overworld();
            for (TamaPet p : level.getEntitiesOfClass(TamaPet.class, player(s).getBoundingBox().inflate(64))) {
                p.discard();
            }
            for (ItemEntity i : level.getEntitiesOfClass(ItemEntity.class, player(s).getBoundingBox().inflate(64))) {
                i.discard();
            }
        });
        cmd("fill -20 " + Y + " -20 20 " + (Y + 6) + " 20 air");
    }

    private static TamaPet spawn(ServerLevel level, ServerPlayer owner, PetSpecies s, double x, double z, float yaw, boolean ai) {
        TamaPet pet = ModEntities.type(s).create(level);
        pet.moveTo(x, Y, z, yaw, 0);
        pet.setYHeadRot(yaw);
        pet.setYBodyRot(yaw);
        pet.tame(owner);
        pet.setNoAi(!ai);
        level.addFreshEntity(pet);
        return pet;
    }

    // ------------------------------------------------------------------ scenes

    private void lineup(boolean backpacks) {
        clear();
        server.runOnServer(s -> {
            ServerLevel level = s.overworld();
            ServerPlayer p = player(s);
            PetSpecies[] all = PetSpecies.values();
            for (int i = 0; i < all.length; i++) {
                int row = i / 5, col = i % 5;
                TamaPet pet = spawn(level, p, all[i], -4.8 + col * 2.4, row * 2.6, 180F, false);
                if (backpacks) {
                    pet.equipBackpack();
                }
            }
        });
        cam(backpacks ? "0 -55.5 9 160 32" : "0 -57.2 -6.5 0 22");
        ctx.waitTicks(30);
        shot(backpacks ? "02_lineup_backpacks" : "01_lineup");
    }

    private void closeups() {
        clear();
        PetSpecies[] all = PetSpecies.values();
        for (PetSpecies s : all) {
            // three-quarter view from where a player would stand next to the pet
            server.runOnServer(srv -> spawn(srv.overworld(), player(srv), s, 0.5, 0.5, 165F, false));
            cmd("tp @p 1.65 -60 -1.49 30 29");
            ctx.waitTicks(15);
            shot("10_" + s.id() + "_a_idle");
            server.runOnServer(srv -> srv.overworld().getEntitiesOfClass(TamaPet.class, player(srv).getBoundingBox().inflate(8))
                    .forEach(pet -> pet.playAction(PetAction.PETTED)));
            ctx.waitTicks(8);
            shot("10_" + s.id() + "_b_petted");
            server.runOnServer(srv -> srv.overworld().getEntitiesOfClass(TamaPet.class, player(srv).getBoundingBox().inflate(8))
                    .forEach(pet -> {
                        pet.setInSittingPose(true);
                        pet.equipBackpack();
                    }));
            ctx.waitTicks(30);
            shot("10_" + s.id() + "_c_sit_backpack");
            server.runOnServer(srv -> srv.overworld().getEntitiesOfClass(TamaPet.class, player(srv).getBoundingBox().inflate(8))
                    .forEach(pet -> {
                        pet.setInSittingPose(false);
                        pet.setSleeping(true);
                    }));
            ctx.waitTicks(10);
            shot("10_" + s.id() + "_d_sleep");
            clear();
        }
    }

    private void furniture() {
        clear();
        // front row: beds, bowl, bath; back row: the tall play blocks
        BlockPos bed = new BlockPos(-4, Y, 0), bowl = new BlockPos(2, Y, 0), bath = new BlockPos(4, Y, 0);
        BlockPos mushroom = new BlockPos(-3, Y, 3), wheel = new BlockPos(-1, Y, 3), post = new BlockPos(1, Y, 3);
        server.runOnServer(s -> {
            ServerLevel level = s.overworld();
            level.setBlockAndUpdate(bed, ModBlocks.PET_BED.defaultBlockState());
            level.setBlockAndUpdate(new BlockPos(-2, Y, 0), ModBlocks.PET_BASKET.defaultBlockState());
            level.setBlockAndUpdate(new BlockPos(0, Y, 0), ModBlocks.DRAGON_NEST.defaultBlockState());
            level.setBlockAndUpdate(bowl, ModBlocks.FOOD_BOWL.defaultBlockState().setValue(FoodBowlBlock.FILL, 3));
            level.setBlockAndUpdate(bath, ModBlocks.PET_BATH.defaultBlockState().setValue(PetBathBlock.FILLED, true));
            level.setBlockAndUpdate(mushroom, ModBlocks.BOUNCY_MUSHROOM.defaultBlockState());
            level.setBlockAndUpdate(wheel, ModBlocks.RUNNING_WHEEL.defaultBlockState().setValue(RunningWheelBlock.FACING, Direction.NORTH));
            level.setBlockAndUpdate(post, ModBlocks.SCRATCHING_POST.defaultBlockState());
            level.setBlockAndUpdate(new BlockPos(3, Y, 3), ModBlocks.PET_HOUSE.defaultBlockState());
        });
        cam("0.5 -57.6 -4.5 0 30");
        ctx.waitTicks(30);
        shot("20_furniture");
        // every block in use: asleep in the bed, eating, bathing, running, scratching, bouncing
        server.runOnServer(s -> {
            ServerLevel level = s.overworld();
            ServerPlayer p = player(s);
            spawn(level, p, PetSpecies.FROST_PENGUIN, bed.getX() + 0.5, bed.getZ() + 0.5, 200, false).setSleeping(true);
            spawn(level, p, PetSpecies.EMBER_PUP, bowl.getX() + 0.5, bowl.getZ() + 1.4, 180, false).playAction(PetAction.EAT);
            spawn(level, p, PetSpecies.JUNGLE_DRAGON, bath.getX() + 0.5, bath.getZ() + 0.5, 200, false).setFlag(TamaPet.F_BATHING, true);
            spawn(level, p, PetSpecies.VOID_KITTEN, wheel.getX() + 0.5, wheel.getZ() + 0.5, Direction.EAST.toYRot(), false).setFlag(TamaPet.F_RUNNING, true);
            level.getEntitiesOfClass(TamaPet.class, new net.minecraft.world.phys.AABB(wheel)).forEach(r -> r.setPos(r.getX(), Y + 0.13, r.getZ()));
            RunningWheelBlock.setRunning(level, wheel, true);
            spawn(level, p, PetSpecies.PEBBLE_GOLEM, post.getX() + 1.45, post.getZ() + 0.5, 90, false).playAction(PetAction.SCRATCH);
            TamaPet bouncer = spawn(level, p, PetSpecies.HEX_TOAD, mushroom.getX() + 0.5, mushroom.getZ() + 0.5, 200, false);
            bouncer.moveTo(bouncer.getX(), Y + 0.75, bouncer.getZ(), 200, 0);
            bouncer.playAction(PetAction.BOUNCE);
        });
        ctx.waitTicks(6);
        shot("21_furniture_in_use");
    }

    private void screen() {
        clear();
        server.runOnServer(s -> {
            ServerLevel level = s.overworld();
            TamaPet pet = spawn(level, player(s), PetSpecies.DESERT_DRAGON, 0.5, 2.5, 180, false);
            pet.equipBackpack();
            pet.store(new ItemStack(Items.BREAD, 12));
            pet.store(new ItemStack(Items.TORCH, 32));
            pet.store(new ItemStack(ModItems.PET_KIBBLE, 8));
            pet.store(new ItemStack(Items.GOLDEN_APPLE, 3));
            pet.needs().hunger = 40;
            pet.needs().fun = 85;
            pet.needs().energy = 60;
            pet.needs().hygiene = 18;
            pet.needs().bond = 64;
        });
        cmd("tp @p 0.5 -60 -1 0 10");
        ctx.waitTicks(20);
        hud(true);
        server.runOnServer(s -> s.overworld().getEntitiesOfClass(TamaPet.class, player(s).getBoundingBox().inflate(8))
                .forEach(pet -> pet.openPetScreen(player(s))));
        ctx.waitTicks(20);
        shot("30_pet_screen");
        ctx.runOnClient(mc -> {
            if (mc.player != null) {
                mc.player.closeContainer();
            }
        });
        // the creative tab with every item and block
        ctx.runOnClient(mc -> {
            CreativeModeInventoryScreen inv = new CreativeModeInventoryScreen(mc.player, mc.player.connection.enabledFeatures(), false);
            mc.setScreen(inv);
            ((net.kasax.tamacraft.test.mixin.CreativeScreenAccessor) inv).tamatest$selectTab(BuiltInRegistries.CREATIVE_MODE_TAB.getOrThrow(ModTab.KEY));
        });
        ctx.waitTicks(10);
        shot("31_creative_tab");
        ctx.runOnClient(mc -> mc.setScreen(null));
        hud(false);
        ctx.waitTicks(5);
    }

    /** Pets with their AI on, low needs, in a little playground: they should use the furniture by themselves. */
    private void live() {
        clear();
        server.runOnServer(s -> {
            ServerLevel level = s.overworld();
            level.setBlockAndUpdate(new BlockPos(-3, Y, 3), ModBlocks.FOOD_BOWL.defaultBlockState().setValue(FoodBowlBlock.FILL, 3));
            level.setBlockAndUpdate(new BlockPos(3, Y, 3), ModBlocks.PET_BATH.defaultBlockState().setValue(PetBathBlock.FILLED, true));
            level.setBlockAndUpdate(new BlockPos(0, Y, 6), ModBlocks.BOUNCY_MUSHROOM.defaultBlockState());
            level.setBlockAndUpdate(new BlockPos(-4, Y, 7), ModBlocks.RUNNING_WHEEL.defaultBlockState());
            level.setBlockAndUpdate(new BlockPos(4, Y, 7), ModBlocks.SCRATCHING_POST.defaultBlockState());
            PetSpecies[] who = {PetSpecies.EMBER_PUP, PetSpecies.FROST_PENGUIN, PetSpecies.VOID_KITTEN, PetSpecies.JUNGLE_DRAGON};
            for (int i = 0; i < who.length; i++) {
                TamaPet pet = spawn(level, player(s), who[i], -1.5 + i, 4.5, 180, true);
                pet.setMode(TamaPet.Mode.WANDER);
                pet.needs().hunger = i == 0 ? 30 : 80;
                pet.needs().hygiene = i == 3 ? 30 : 80;
                pet.needs().fun = i == 1 || i == 2 ? 25 : 80;
                pet.needs().energy = 80;
            }
        });
        cam("0 -55 -4 0 32");
        for (int i = 1; i <= 6; i++) {
            ctx.waitTicks(60);
            shot("40_live_" + i);
        }
    }

    /** With JEI or REI loaded (-PwithJei / -PwithRei): list the mod's items and open a recipe, nothing else. */
    private boolean recipeViewerCheck() {
        String viewer = net.fabricmc.loader.api.FabricLoader.getInstance().isModLoaded("jei") ? "jei"
                : net.fabricmc.loader.api.FabricLoader.getInstance().isModLoaded("roughlyenoughitems") ? "rei" : null;
        if (viewer == null) {
            return false;
        }
        cmd("gamemode survival @p");
        hud(true);
        ctx.waitTicks(10);
        ctx.runOnClient(mc -> mc.setScreen(new net.minecraft.client.gui.screens.inventory.InventoryScreen(mc.player)));
        ctx.waitTicks(20);
        double[] win = new double[2];
        ctx.runOnClient(mc -> {
            win[0] = mc.getWindow().getScreenWidth();
            win[1] = mc.getWindow().getScreenHeight();
        });
        ctx.getInput().setCursorPos(win[0] * Double.parseDouble(System.getProperty("tama.sx", "0.84")),
                win[1] * Double.parseDouble(System.getProperty("tama.sy", "0.94")));
        ctx.getInput().pressMouse(com.mojang.blaze3d.platform.InputConstants.MOUSE_BUTTON_LEFT);   // 1.21.1: GLFW numbering, left = 0
        ctx.waitTicks(2);
        ctx.getInput().typeChars("@tamacraft");
        ctx.waitTicks(20);
        shot("60_" + viewer + "_items");
        // the recipe of the Tamacon and the info page of a spawn egg, opened through our own plugin
        String plugin = viewer.equals("jei") ? "net.kasax.tamacraft.compat.JeiCompat" : "net.kasax.tamacraft.compat.ReiCompat";
        ItemStack[] show = {new ItemStack(ModItems.TAMACON), new ItemStack(ModItems.SPAWN_EGGS.get(PetSpecies.JUNGLE_DRAGON))};
        for (int i = 0; i < show.length; i++) {
            ItemStack stack = show[i];
            ctx.runOnClient(mc -> {
                try {
                    Class.forName(plugin).getMethod("showRecipes", ItemStack.class).invoke(null, stack);
                } catch (ReflectiveOperationException e) {
                    throw new RuntimeException(e);
                }
            });
            ctx.waitTicks(20);
            shot("6" + (i + 1) + "_" + viewer + "_" + (i == 0 ? "tamacon_recipe" : "egg_info"));
        }
        ctx.runOnClient(mc -> mc.setScreen(null));
        return true;
    }

    /** Wheel close-up, a flying dragon, the ore glow and the Tamacon. */
    private void extras() {
        clear();
        BlockPos wheel = new BlockPos(0, Y, 2);
        server.runOnServer(s -> {
            ServerLevel level = s.overworld();
            level.setBlockAndUpdate(wheel, ModBlocks.RUNNING_WHEEL.defaultBlockState().setValue(RunningWheelBlock.FACING, Direction.NORTH));
            TamaPet runner = spawn(level, player(s), PetSpecies.DESERT_DRAGON, 0.5, 2.5, Direction.EAST.toYRot(), false);
            runner.setPos(0.5, Y + 0.13, 2.5);
            runner.setFlag(TamaPet.F_RUNNING, true);
            RunningWheelBlock.setRunning(level, wheel, true);
        });
        cam("1.6 -59.2 0.4 35 18");
        ctx.waitTicks(20);
        shot("50_wheel");
        clear();
        // a dragon flies after its owner when that is faster
        boolean[] flew = {false};
        server.runOnServer(s -> {
            ServerLevel level = s.overworld();
            level.setBlockAndUpdate(wheel, Blocks.AIR.defaultBlockState());
            TamaPet d = spawn(level, player(s), PetSpecies.JUNGLE_DRAGON, 0.5, -14.5, 0, true);
            d.setMode(TamaPet.Mode.FOLLOW);
        });
        cam("0.5 -59 6 180 5");
        boolean[] close = {false};
        for (int i = 0; i < 60 && !close[0]; i++) {
            ctx.waitTicks(2);
            server.runOnServer(s -> s.overworld().getEntitiesOfClass(TamaPet.class, player(s).getBoundingBox().inflate(40))
                    .forEach(p -> {
                        flew[0] |= p.isFlying();
                        close[0] |= p.isFlying() && p.distanceTo(player(s)) < 8;
                    }));
        }
        shot("51_flying_dragon");
        check("a dragon far from its owner flies after it", flew[0]);
        clear();
        // the pebble golem's ore glows through the wall
        int[] markers = {0};
        cmd("fill -3 -61 4 3 -58 6 stone");
        server.runOnServer(s -> {
            ServerLevel level = s.overworld();
            level.setBlockAndUpdate(new BlockPos(0, -60, 5), Blocks.DIAMOND_ORE.defaultBlockState());
            spawn(level, player(s), PetSpecies.PEBBLE_GOLEM, 0.5, 2.5, 0, true).setMode(TamaPet.Mode.SIT);
        });
        cam("0.5 -59 -1.5 0 10");
        ctx.waitTicks(240);   // talents warm up for ten seconds after taming
        server.runOnServer(s -> markers[0] = s.overworld().getEntitiesOfClass(net.minecraft.world.entity.Display.BlockDisplay.class,
                player(s).getBoundingBox().inflate(12), net.minecraft.world.entity.Entity::isCurrentlyGlowing).size());
        shot("52_ore_glow");
        check("the pebble golem makes a nearby ore glow (" + markers[0] + ")", markers[0] == 1);
        cmd("fill -3 -61 4 3 -58 6 air");
        cmd("fill -3 -61 4 3 -61 6 grass_block");
        clear();
        // the Tamacon guide
        ctx.runOnClient(mc -> mc.setScreen(new net.kasax.tamacraft.client.screen.TamaconScreen()));
        ctx.waitTicks(5);
        shot("53_tamacon_contents");
        ctx.getInput().pressKey(com.mojang.blaze3d.platform.InputConstants.KEY_RIGHT);
        ctx.waitTicks(3);
        shot("54_tamacon_page");
        for (int i = 0; i < 9; i++) {
            ctx.getInput().pressKey(com.mojang.blaze3d.platform.InputConstants.KEY_RIGHT);
        }
        ctx.waitTicks(3);
        shot("55_tamacon_page");
        for (int i = 0; i < 6; i++) {
            ctx.getInput().pressKey(com.mojang.blaze3d.platform.InputConstants.KEY_RIGHT);
        }
        ctx.waitTicks(3);
        shot("56_tamacon_page");
        // every pet page (they show the pet itself)
        for (int i = 0; i < 24; i++) {
            ctx.getInput().pressKey(com.mojang.blaze3d.platform.InputConstants.KEY_RIGHT);
            ctx.waitTicks(1);
            if (i % 3 == 2) {
                shot("59_tamacon_pet_" + i);
            }
        }
        ctx.runOnClient(mc -> mc.setScreen(null));
        // the 3D pager and laser pointer, in first and third person
        cam("0.5 -60 0.5 0 15");
        hud(true);
        Item[] held = {ModItems.TAMA_PAGER, ModItems.LASER_POINTER};
        for (Item item : held) {
            server.runOnServer(s -> player(s).setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND, new ItemStack(item)));
            ctx.waitTicks(10);
            shot("57_held_" + BuiltInRegistries.ITEM.getKey(item).getPath());
            ctx.runOnClient(mc -> mc.options.setCameraType(net.minecraft.client.CameraType.THIRD_PERSON_FRONT));
            ctx.waitTicks(10);
            shot("58_held_3rd_" + BuiltInRegistries.ITEM.getKey(item).getPath());
            ctx.runOnClient(mc -> mc.options.setCameraType(net.minecraft.client.CameraType.FIRST_PERSON));
        }
        server.runOnServer(s -> player(s).setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND, ItemStack.EMPTY));
        hud(false);
    }

    /** A real (not flat) world: pets must turn up in naturally generated jungle temples and ocean monuments. */
    private void naturalSpawns() {
        Map<ResourceLocation, PetSpawns.Rule> saved = new LinkedHashMap<>(PetSpawns.RULES);
        PetSpawns.RULES.replaceAll((id, rule) -> new PetSpawns.Rule(rule.species(), 1F));
        String[][] targets = {{"jungle_pyramid", "jungle_dragon"}, {"monument", "tide_dragon"}, {"desert_pyramid", "desert_dragon"}};
        try (TestSingleplayerContext sp = ctx.worldBuilder().setUseConsistentSettings(false)
                .setSeed("tamacraft").create()) {
            this.server = sp.getServer();
            cmd("gamemode spectator @p");
            for (String[] t : targets) {
                BlockPos[] at = {null};
                server.runOnServer(s -> {
                    ServerLevel level = s.overworld();
                    var key = net.minecraft.resources.ResourceKey.create(net.minecraft.core.registries.Registries.STRUCTURE, ResourceLocation.withDefaultNamespace(t[0]));
                    var holder = level.registryAccess().lookupOrThrow(net.minecraft.core.registries.Registries.STRUCTURE).getOrThrow(key);
                    var found = level.getChunkSource().getGenerator().findNearestMapStructure(level,
                            net.minecraft.core.HolderSet.direct(holder), BlockPos.ZERO, 100, false);
                    at[0] = found == null ? null : found.getFirst();
                });
                if (at[0] == null) {
                    check("found a " + t[0] + " to search", false);
                    continue;
                }
                cmd("tp @p " + at[0].getX() + " 120 " + at[0].getZ());
                int[] n = {0};
                for (int i = 0; i < 40 && n[0] == 0; i++) {
                    ctx.waitTicks(20);
                    server.runOnServer(s -> n[0] = s.overworld().getEntitiesOfClass(TamaPet.class,
                            new AABB(at[0]).inflate(72, 200, 72), p -> p.species().id().equals(t[1])).size());
                }
                check("natural " + t[0] + " at " + at[0].getX() + " " + at[0].getZ() + " has a wild " + t[1] + " (" + n[0] + ")", n[0] >= 1);
            }
        } finally {
            PetSpawns.RULES.clear();
            PetSpawns.RULES.putAll(saved);
        }
    }

    // ------------------------------------------------------------------ regression checks (1.2.0)

    /** Counts how often the pet falls asleep or wakes up during {@code ticks}. */
    private int sleepFlips(int ticks) {
        int[] flips = {0};
        boolean[] last = {false};
        server.runOnServer(s -> last[0] = s.overworld().getEntitiesOfClass(TamaPet.class, player(s).getBoundingBox().inflate(20)).get(0).isSleeping());
        for (int i = 0; i < ticks; i++) {
            ctx.waitTicks(1);
            server.runOnServer(s -> {
                boolean now = s.overworld().getEntitiesOfClass(TamaPet.class, player(s).getBoundingBox().inflate(20)).get(0).isSleeping();
                if (now != last[0]) {
                    flips[0]++;
                }
                last[0] = now;
            });
        }
        return flips[0];
    }

    private static TamaPet onlyPet(MinecraftServer s) {
        return s.overworld().getEntitiesOfClass(TamaPet.class, player(s).getBoundingBox().inflate(40)).get(0);
    }

    private void fixes() {
        clear();
        cmd("tp @p 0.5 " + Y + " 0.5 0 0");
        server.runOnServer(s -> {
            player(s).getAbilities().flying = false;
            player(s).onUpdateAbilities();
        });

        // a tired, following pet that cannot reach its owner must not fall asleep and wake up again every tick
        cmd("fill 9 " + Y + " -1 13 " + (Y + 2) + " 1 glass hollow");
        server.runOnServer(s -> {
            TamaPet pet = spawn(s.overworld(), player(s), PetSpecies.PEBBLE_GOLEM, 11.0, 0.5, 0, true);
            pet.setMode(TamaPet.Mode.FOLLOW);
            pet.needs().energy = 10;
        });
        ctx.waitTicks(10);
        int far = sleepFlips(80);
        check("a tired pet far from its owner does not keep waking up (" + far + " flips)", far <= 1);
        clear();

        // ... and a rested one curled up next to its sleeping owner stays asleep
        cmd("time set midnight");
        cmd("setblock 0 " + Y + " -2 minecraft:red_bed[facing=north,part=foot]");
        cmd("setblock 0 " + Y + " -3 minecraft:red_bed[facing=north,part=head]");
        server.runOnServer(s -> {
            TamaPet pet = spawn(s.overworld(), player(s), PetSpecies.HEX_TOAD, 2.5, -2.5, 0, true);
            pet.setMode(TamaPet.Mode.FOLLOW);
            pet.needs().energy = 100;
            player(s).startSleeping(new BlockPos(0, Y, -3));
        });
        ctx.waitTicks(10);
        int bed = sleepFlips(80);
        boolean[] ownerSlept = {false};
        server.runOnServer(s -> {
            ownerSlept[0] = player(s).isSleeping();
            player(s).stopSleeping();
        });
        check("a rested pet next to its sleeping owner stays asleep (" + bed + " flips, owner asleep " + ownerSlept[0] + ")",
                bed <= 1 && ownerSlept[0]);
        cmd("time set noon");
        clear();
        cmd("tp @p 0.5 " + Y + " 0.5 0 0");

        // the golden apple a pet holds up is only for show: interrupted, it must not turn into a free apple
        server.runOnServer(s -> {
            ServerPlayer p = player(s);
            p.getInventory().clearContent();
            TamaPet pet = spawn(s.overworld(), p, PetSpecies.HEX_TOAD, 1.5, 1.5, 0, true);
            pet.equipBackpack();
            pet.store(new ItemStack(Items.GOLDEN_APPLE));
            p.setHealth(4F);
        });
        boolean[] showing = {false};
        for (int i = 0; i < 80 && !showing[0]; i++) {
            ctx.waitTicks(1);
            server.runOnServer(s -> showing[0] = onlyPet(s).getCarried().is(Items.GOLDEN_APPLE));
        }
        server.runOnServer(s -> player(s).setHealth(player(s).getMaxHealth()));   // healed before the pet hands it over
        ctx.waitTicks(80);
        int[] apples = {0};
        server.runOnServer(s -> {
            TamaPet pet = onlyPet(s);
            apples[0] = pet.snacks() + player(s).getInventory().countItem(Items.GOLDEN_APPLE) + (pet.getCarried().isEmpty() ? 0 : 10);
        });
        check("an interrupted golden-apple feeding makes no extra apple (saw it held: " + showing[0] + ", apples " + apples[0] + ")",
                showing[0] && apples[0] == 1);
        clear();

        // a hurt pet eats its own lunch from the backpack, never the golden apples meant for its owner
        server.runOnServer(s -> {
            TamaPet pet = spawn(s.overworld(), player(s), PetSpecies.PEBBLE_GOLEM, 1.5, 1.5, 0, true);
            pet.equipBackpack();
            pet.inventory().setItem(0, new ItemStack(Items.GOLDEN_APPLE));
            pet.inventory().setItem(1, new ItemStack(Items.BREAD, 3));
            pet.setHealth(pet.getMaxHealth() * 0.2F);
        });
        ctx.waitTicks(80);
        int[] lunch = {0, 0};
        server.runOnServer(s -> {
            TamaPet pet = onlyPet(s);
            lunch[0] = pet.snacks();
            lunch[1] = pet.inventory().getItem(1).getCount();
        });
        check("a hurt pet eats bread, not the golden apple (apples " + lunch[0] + ", bread " + lunch[1] + ")", lunch[0] == 1 && lunch[1] < 3);
        clear();

        // fainting in the void: the egg goes to the owner instead of falling forever
        boolean[] voidEgg = {false};
        server.runOnServer(s -> {
            ServerLevel level = s.overworld();
            ServerPlayer p = player(s);
            p.getInventory().clearContent();
            TamaPet pet = spawn(level, p, PetSpecies.FROST_PENGUIN, 0.5, 0.5, 0, true);
            pet.setPos(0.5, level.getMinBuildHeight() - 70, 0.5);
            pet.hurt(level.damageSources().fellOutOfWorld(), 1000F);
            voidEgg[0] = !pet.isAlive() && p.getInventory().countItem(ModItems.TAMA_EGG) == 1;
        });
        check("a pet that faints in the void lands in its owner's inventory as an egg", voidEgg[0]);

        // the egg on the ground survives explosions (and fire, lava, cactus)
        boolean[] eggSurvives = {false};
        server.runOnServer(s -> {
            ServerLevel level = s.overworld();
            TamaPet pet = spawn(level, player(s), PetSpecies.EMBER_PUP, 3.5, 3.5, 0, true);
            pet.hurt(level.damageSources().generic(), 1000F);
            level.explode(null, 3.5, Y + 0.5, 3.5, 3F, net.minecraft.world.level.Level.ExplosionInteraction.NONE);
        });
        ctx.waitTicks(3);
        server.runOnServer(s -> eggSurvives[0] = s.overworld().getEntitiesOfClass(ItemEntity.class, new AABB(3.5, Y, 3.5, 3.5, Y, 3.5).inflate(4),
                e -> e.getItem().is(ModItems.TAMA_EGG)).size() == 1);
        check("a Tama Egg on the ground survives an explosion", eggSurvives[0]);
        clear();

        // a dragon saved in mid-air comes back with gravity (it used to hover forever)
        boolean[] lands = {false};
        server.runOnServer(s -> {
            ServerLevel level = s.overworld();
            TamaPet dragon = spawn(level, player(s), PetSpecies.DESERT_DRAGON, 2.5, 2.5, 0, true);
            dragon.startFlying(dragon.position().add(0, 4, 0), 100);
            boolean flying = dragon.isFlying() && dragon.isNoGravity();
            ItemStack egg = net.kasax.tamacraft.item.TamaEggItem.fromPet(dragon);
            dragon.discard();
            TamaPet back = net.kasax.tamacraft.item.TamaEggItem.wake(level, egg, new net.minecraft.world.phys.Vec3(2.5, Y, 2.5), 0, false);
            lands[0] = flying && back != null && !back.isNoGravity();
        });
        check("a dragon saved while flying lands again after loading", lands[0]);
        clear();

        // a pet told to stay still still shows "Sit" on its screen after loading (vanilla loads "Sitting" behind our back)
        boolean[] stays = {false};
        server.runOnServer(s -> {
            ServerLevel level = s.overworld();
            TamaPet pet = spawn(level, player(s), PetSpecies.HEX_TOAD, 2.5, 2.5, 0, true);
            pet.setMode(TamaPet.Mode.SIT);
            ItemStack egg = net.kasax.tamacraft.item.TamaEggItem.fromPet(pet);
            pet.discard();
            TamaPet back = net.kasax.tamacraft.item.TamaEggItem.wake(level, egg, new net.minecraft.world.phys.Vec3(2.5, Y, 2.5), 0, false);
            stays[0] = back != null && back.mode() == TamaPet.Mode.SIT && back.hasFlag(TamaPet.F_STAY);
        });
        check("a sitting pet shows Sit on its screen after loading", stays[0]);
        clear();

        // any wooden chest (c:chests/wooden, here a trapped chest) puts a backpack on, any shears (c:tools/shear) take it off
        boolean[] pack = {false, false};
        server.runOnServer(s -> {
            ServerPlayer p = player(s);
            TamaPet pet = spawn(s.overworld(), p, PetSpecies.PEBBLE_GOLEM, 1.5, 1.5, 0, true);
            p.setShiftKeyDown(true);
            p.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND, new ItemStack(Items.TRAPPED_CHEST));
            pet.mobInteract(p, net.minecraft.world.InteractionHand.MAIN_HAND);
            pack[0] = pet.hasBackpack();
            p.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND, new ItemStack(Items.SHEARS));
            pet.mobInteract(p, net.minecraft.world.InteractionHand.MAIN_HAND);
            pack[1] = !pet.hasBackpack();
            p.setShiftKeyDown(false);
            p.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND, ItemStack.EMPTY);
        });
        check("any wooden chest puts a backpack on, shears take it off (on " + pack[0] + ", off " + pack[1] + ")", pack[0] && pack[1]);
        clear();

        // the Void Kitten only pulls items while its owner is near (a kitten left at home must not send them away)
        server.runOnServer(s -> {
            ServerLevel level = s.overworld();
            TamaPet kitten = spawn(level, player(s), PetSpecies.VOID_KITTEN, 30.5, 0.5, 0, true);
            kitten.setMode(TamaPet.Mode.SIT);
            ItemEntity stone = new ItemEntity(level, 31.5, Y, 0.5, new ItemStack(Items.COBBLESTONE));
            stone.setNoPickUpDelay();
            level.addFreshEntity(stone);
        });
        ctx.waitTicks(60);
        int[] stayed = {0};
        server.runOnServer(s -> stayed[0] = s.overworld().getEntitiesOfClass(ItemEntity.class, new AABB(31.5, Y, 0.5, 31.5, Y, 0.5).inflate(3),
                e -> e.getItem().is(Items.COBBLESTONE)).size());
        check("a Void Kitten far from its owner leaves dropped items alone (" + stayed[0] + ")", stayed[0] == 1);
        clear();

        // modpack compatibility: modded food (c:foods tags), modded ores (c:ores), look-alike structures (tags)
        boolean[] food = {false};
        boolean[] ores = {false};
        boolean[] homes = {false};
        server.runOnServer(s -> {
            ServerLevel level = s.overworld();
            TamaPet jungle = ModEntities.type(PetSpecies.JUNGLE_DRAGON).create(level);
            TamaPet penguin = ModEntities.type(PetSpecies.FROST_PENGUIN).create(level);
            TamaPet mimic = ModEntities.type(PetSpecies.MIMIC).create(level);
            food[0] = jungle.isPetFood(new ItemStack(Items.POTATO)) && penguin.isPetFood(new ItemStack(Items.COOKED_COD))
                    && !jungle.isPetFood(new ItemStack(Items.GOLDEN_APPLE)) && !mimic.isPetFood(new ItemStack(Items.ENCHANTED_GOLDEN_APPLE))
                    && mimic.isPetFood(new ItemStack(Items.BREAD));
            jungle.discard();
            penguin.discard();
            mimic.discard();
            int quartz = net.kasax.tamacraft.pet.Talents.oreRank(Blocks.NETHER_QUARTZ_ORE.defaultBlockState());
            ores[0] = quartz >= 0 && net.kasax.tamacraft.pet.Talents.oreRank(Blocks.DIAMOND_ORE.defaultBlockState()) < quartz
                    && net.kasax.tamacraft.pet.Talents.oreRank(Blocks.ANCIENT_DEBRIS.defaultBlockState())
                    < net.kasax.tamacraft.pet.Talents.oreRank(Blocks.GOLD_ORE.defaultBlockState())
                    && net.kasax.tamacraft.pet.Talents.oreRank(Blocks.STONE.defaultBlockState()) == -1;
            var structures = level.registryAccess().lookupOrThrow(net.minecraft.core.registries.Registries.STRUCTURE);
            PetSpawns.Rule mineshaft = PetSpawns.ruleFor(structures.getOrThrow(net.minecraft.world.level.levelgen.structure.BuiltinStructures.MINESHAFT));
            PetSpawns.Rule mansion = PetSpawns.ruleFor(structures.getOrThrow(net.minecraft.world.level.levelgen.structure.BuiltinStructures.WOODLAND_MANSION));
            PetSpawns.Rule village = PetSpawns.ruleFor(structures.getOrThrow(net.minecraft.world.level.levelgen.structure.BuiltinStructures.VILLAGE_PLAINS));
            homes[0] = mineshaft != null && mineshaft.species() == PetSpecies.PEBBLE_GOLEM && mineshaft.chance() < 0.1F
                    && mansion != null && mansion.species() == PetSpecies.MIMIC && mansion.chance() > 0.5F && village == null;
        });
        check("diets use food tags (modded food counts, golden apples never)", food[0]);
        check("the Ore Sniffer knows c:ores and ranks them", ores[0]);
        check("pet homes come from the pet_home structure tags", homes[0]);

        // furniture tooltips and recipe-book unlocks
        boolean[] tips = {true};
        ctx.runOnClient(mc -> {
            for (Item item : ModBlocks.BLOCK_ITEMS) {
                tips[0] &= net.minecraft.locale.Language.getInstance().has(item.getDescriptionId() + ".tooltip");
            }
        });
        check("every furniture item has a tooltip", tips[0]);
        // worlds from before the rename (1.2.0 and older) name everything tamagotchi:...
        boolean[] legacy = {false};
        server.runOnServer(s -> legacy[0] = BuiltInRegistries.ITEM.get(ResourceLocation.parse("tamagotchi:tamagotchi_heart")) == ModItems.TAMACRAFT_HEART
                && BuiltInRegistries.BLOCK.get(ResourceLocation.parse("tamagotchi:pet_bed")) == ModBlocks.PET_BED
                && BuiltInRegistries.ENTITY_TYPE.get(ResourceLocation.parse("tamagotchi:hex_toad")) == ModEntities.type(PetSpecies.HEX_TOAD)
                && ResourceLocation.tryParse("tamagotchi:recipes/misc/tamagotchi_heart").equals(net.kasax.tamacraft.Tamacraft.id("recipes/misc/tamacraft_heart"))
                && s.getAdvancements().get(ResourceLocation.parse("tamagotchi:first_friend")) != null);
        check("ids from before the rename (tamagotchi:...) read as tamacraft:...", legacy[0]);
        cmd("advancement revoke @p only tamacraft:recipes/misc/food_bowl");
        cmd("recipe take @p tamacraft:food_bowl");
        cmd("give @p minecraft:bone");
        ctx.waitTicks(10);
        boolean[] unlocked = {false};
        server.runOnServer(s -> unlocked[0] = player(s).getRecipeBook().contains(net.kasax.tamacraft.Tamacraft.id("food_bowl")));
        check("picking up an ingredient unlocks the recipe in the recipe book", unlocked[0]);
        server.runOnServer(s -> player(s).getInventory().clearContent());
        clicks();
    }

    /** Moves the real cursor onto a GUI point and presses a mouse button (1.21.1: GLFW numbering, left = 0, right = 1). */
    private void clickGui(double gx, double gy, int button) {
        int[] scale = {1};
        ctx.runOnClient(mc -> scale[0] = (int) mc.getWindow().getGuiScale());
        ctx.getInput().setCursorPos(gx * scale[0], gy * scale[0]);
        ctx.getInput().pressMouse(button);
        ctx.waitTicks(5);
    }

    /** Centre of the n-th button on the open screen, in GUI coordinates. */
    private double[] buttonCentre(int n) {
        double[] at = new double[2];
        ctx.runOnClient(mc -> {
            var b = mc.screen.children().stream().filter(net.minecraft.client.gui.components.Button.class::isInstance)
                    .map(net.minecraft.client.gui.components.Button.class::cast).toList().get(n);
            at[0] = b.getX() + b.getWidth() / 2.0;
            at[1] = b.getY() + b.getHeight() / 2.0;
        });
        return at;
    }

    /** Every click path of the mod's screens, with real mouse clicks. */
    private void clicks() {
        int left = com.mojang.blaze3d.platform.InputConstants.MOUSE_BUTTON_LEFT;
        clear();
        cmd("tp @p 0.5 " + Y + " 0.5 0 0");
        server.runOnServer(s -> {
            TamaPet pet = spawn(s.overworld(), player(s), PetSpecies.HEX_TOAD, 1.5, 1.5, 0, true);
            pet.setMode(TamaPet.Mode.FOLLOW);
        });
        ctx.waitTicks(5);
        server.runOnServer(s -> onlyPet(s).openPetScreen(player(s)));
        ctx.waitTicks(10);
        // the pet screen: Wander, Sit, Follow (buttons 2, 0, 1); the pressed one greys out on the client
        TamaPet.Mode[] want = {TamaPet.Mode.WANDER, TamaPet.Mode.SIT, TamaPet.Mode.FOLLOW};
        int[] button = {2, 0, 1};
        boolean modes = true;
        for (int i = 0; i < want.length; i++) {
            double[] at = buttonCentre(button[i]);
            clickGui(at[0], at[1], left);
            TamaPet.Mode[] got = {null};
            server.runOnServer(s -> got[0] = onlyPet(s).mode());
            boolean[] greyed = {false};
            int n = button[i];
            ctx.runOnClient(mc -> greyed[0] = mc.screen instanceof net.kasax.tamacraft.client.screen.PetScreen && !mc.screen.children().stream()
                    .filter(net.minecraft.client.gui.components.Button.class::isInstance).map(net.minecraft.client.gui.components.Button.class::cast)
                    .toList().get(n).active);
            modes &= got[0] == want[i] && greyed[0];
            LOG.info("[TamaTest] pet screen click {}: mode {}, button greyed {}", want[i], got[0], greyed[0]);
        }
        check("the pet screen's Sit / Follow / Wander buttons work with real left clicks", modes);
        ctx.runOnClient(mc -> mc.screen.onClose());   // like Esc: the server closes the menu too
        ctx.waitTicks(5);
        clear();

        // the Tamacon: the Contents button, then a chapter on the contents page (a right click does nothing)
        ctx.runOnClient(mc -> mc.setScreen(new net.kasax.tamacraft.client.screen.TamaconScreen()));
        ctx.waitTicks(5);
        double[] contents = buttonCentre(1);
        clickGui(contents[0], contents[1], left);
        int[] page = {-1};
        int[] chapter = {-1};
        double[] entry = new double[2];
        Runnable read = () -> ctx.runOnClient(mc -> {
            try {
                Class<?> c = net.kasax.tamacraft.client.screen.TamaconScreen.class;
                var pageField = c.getDeclaredField("page");
                pageField.setAccessible(true);
                page[0] = pageField.getInt(mc.screen);
                var starts = c.getDeclaredField("chapterStart");
                starts.setAccessible(true);
                chapter[0] = ((List<?>) starts.get(mc.screen)).get(3) instanceof Integer at ? at : -1;
                var rect = c.getDeclaredMethod("contentsRect", int.class);
                rect.setAccessible(true);
                int[] r = (int[]) rect.invoke(mc.screen, 3);
                entry[0] = r[0] + r[2] / 2.0;
                entry[1] = r[1] + r[3] / 2.0 - 1;
            } catch (ReflectiveOperationException e) {
                throw new RuntimeException(e);
            }
        });
        read.run();
        boolean onContents = page[0] == 0;
        clickGui(entry[0], entry[1], com.mojang.blaze3d.platform.InputConstants.MOUSE_BUTTON_RIGHT);
        read.run();
        boolean rightIgnored = page[0] == 0;
        clickGui(entry[0], entry[1], left);
        read.run();
        check("Tamacon: Contents button and chapter links work with real left clicks (contents " + onContents + ", right click ignored "
                + rightIgnored + ", page " + page[0] + " = chapter " + chapter[0] + ")", onContents && rightIgnored && page[0] == chapter[0] && page[0] > 0);
        int before = page[0];
        double[] next = buttonCentre(2);
        clickGui(next[0], next[1], left);
        read.run();
        check("Tamacon: the > button turns the page (" + before + " -> " + page[0] + ")", page[0] == before + 1);
        ctx.runOnClient(mc -> mc.setScreen(null));
    }

    // ------------------------------------------------------------------ functional checks

    private void check(String name, boolean ok) {
        this.results.add((ok ? "PASS " : "FAIL ") + name);
    }

    private void checks() {
        clear();
        // taming with the heart
        boolean[] tamed = {false};
        server.runOnServer(s -> {
            ServerLevel level = s.overworld();
            ServerPlayer p = player(s);
            TamaPet wild = ModEntities.type(PetSpecies.HEX_TOAD).create(level);
            wild.moveTo(0.5, Y, 2.5, 0, 0);
            level.addFreshEntity(wild);
            p.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND, new ItemStack(ModItems.TAMACRAFT_HEART));
            wild.mobInteract(p, net.minecraft.world.InteractionHand.MAIN_HAND);
            tamed[0] = wild.isTame() && wild.isOwnedBy(p) && wild.hasCustomName();
        });
        check("tame with Tamacraft Heart", tamed[0]);

        // backpack on with sneak + chest, then off spills everything
        int[] spilled = {0};
        boolean[] equipped = {false};
        boolean[] screenOpened = {false};
        boolean[] pagerSits = {false};
        server.runOnServer(s -> {
            ServerLevel level = s.overworld();
            ServerPlayer p = player(s);
            TamaPet pet = level.getEntitiesOfClass(TamaPet.class, p.getBoundingBox().inflate(8)).get(0);
            p.setShiftKeyDown(true);
            p.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND, new ItemStack(Items.CHEST));
            pet.mobInteract(p, net.minecraft.world.InteractionHand.MAIN_HAND);
            equipped[0] = pet.hasBackpack() && pet.storageSlots() == 27;
            pet.store(new ItemStack(Items.DIAMOND, 5));
            pet.store(new ItemStack(Items.APPLE, 3));
            p.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND, ItemStack.EMPTY);
            pet.mobInteract(p, net.minecraft.world.InteractionHand.MAIN_HAND);
            screenOpened[0] = p.containerMenu instanceof net.kasax.tamacraft.menu.PetMenu;
            p.closeContainer();
            p.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND, new ItemStack(Items.SHEARS));
            pet.mobInteract(p, net.minecraft.world.InteractionHand.MAIN_HAND);
            p.setShiftKeyDown(false);
            p.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND, new ItemStack(ModItems.TAMA_PAGER));
            pet.mobInteract(p, net.minecraft.world.InteractionHand.MAIN_HAND);
            pagerSits[0] = pet.isOrderedToSit();
            pet.mobInteract(p, net.minecraft.world.InteractionHand.MAIN_HAND);
            pagerSits[0] &= !pet.isOrderedToSit();
            spilled[0] = level.getEntitiesOfClass(ItemEntity.class, pet.getBoundingBox().inflate(4)).size();
        });
        check("sneak + chest equips a backpack", equipped[0]);
        check("sneak + empty hand opens the pet screen", screenOpened[0]);
        check("sneak + shears takes the backpack off and spills it (" + spilled[0] + " item entities)", spilled[0] >= 3);
        check("the Tama Pager toggles stay / follow", pagerSits[0]);

        // golden apple goes into the snack pouch
        int[] snacks = {0};
        server.runOnServer(s -> {
            ServerPlayer p = player(s);
            TamaPet pet = s.overworld().getEntitiesOfClass(TamaPet.class, p.getBoundingBox().inflate(8)).get(0);
            p.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND, new ItemStack(Items.GOLDEN_APPLE, 2));
            pet.mobInteract(p, net.minecraft.world.InteractionHand.MAIN_HAND);   // no backpack: refused
            snacks[0] = pet.snacks() == 0 && p.getMainHandItem().getCount() == 2 ? 0 : -100;
            pet.equipBackpack();
            pet.mobInteract(p, net.minecraft.world.InteractionHand.MAIN_HAND);
            pet.mobInteract(p, net.minecraft.world.InteractionHand.MAIN_HAND);
            snacks[0] += pet.snacks();
            // the pet feeds a hurt owner from its backpack
            p.setHealth(4F);
        });
        check("golden apples go into the backpack (" + snacks[0] + ")", snacks[0] == 2);
        ctx.waitTicks(60);
        int[] fed = {0};
        server.runOnServer(s -> {
            ServerPlayer p = player(s);
            TamaPet pet = s.overworld().getEntitiesOfClass(TamaPet.class, p.getBoundingBox().inflate(8)).get(0);
            fed[0] = pet.snacks();
            p.setHealth(p.getMaxHealth());
        });
        check("a hurt owner gets a golden apple from the backpack (" + fed[0] + " left)", fed[0] == 1);

        // fainting leaves a Tama Egg that brings the pet back
        boolean[] egg = {false};
        server.runOnServer(s -> {
            ServerLevel level = s.overworld();
            ServerPlayer p = player(s);
            TamaPet pet = level.getEntitiesOfClass(TamaPet.class, p.getBoundingBox().inflate(8)).get(0);
            pet.hurt(level.damageSources().generic(), 1000F);
            egg[0] = !pet.isAlive() && level.getEntitiesOfClass(ItemEntity.class, p.getBoundingBox().inflate(8),
                    e -> e.getItem().is(ModItems.TAMA_EGG)).size() == 1;
        });
        check("a tamed pet faints into a Tama Egg", egg[0]);
        ctx.waitTicks(5);

        // structure spawns: force the chance roll, place real structures, look for the wild pet
        String[][] structures = {{"igloo", "frost_penguin", "40", "40"}, {"swamp_hut", "hex_toad", "-40", "40"},
                {"desert_pyramid", "desert_dragon", "40", "-40"}, {"jungle_pyramid", "jungle_dragon", "-40", "-40"}};
        Map<ResourceLocation, PetSpawns.Rule> saved = new LinkedHashMap<>(PetSpawns.RULES);
        server.runOnServer(s -> PetSpawns.RULES.replaceAll((id, rule) -> new PetSpawns.Rule(rule.species(), 1F)));
        for (String[] st : structures) {
            cmd("place structure minecraft:" + st[0] + " " + st[2] + " " + Y + " " + st[3]);
        }
        ctx.waitTicks(5);
        for (String[] st : structures) {
            int[] found = {0};
            server.runOnServer(s -> found[0] = s.overworld().getEntitiesOfClass(TamaPet.class,
                    new AABB(Integer.parseInt(st[2]), Y - 20, Integer.parseInt(st[3]), Integer.parseInt(st[2]), Y + 30, Integer.parseInt(st[3])).inflate(40),
                    pet -> pet.species().id().equals(st[1]) && !pet.isTame()).size());
            check("a wild " + st[1] + " lives in the placed " + st[0] + " (" + found[0] + ")", found[0] == 1);
        }
        server.runOnServer(s -> {
            PetSpawns.RULES.clear();
            PetSpawns.RULES.putAll(saved);
        });
    }
}
