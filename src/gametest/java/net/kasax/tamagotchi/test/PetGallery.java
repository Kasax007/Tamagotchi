package net.kasax.tamagotchi.test;

import java.util.ArrayList;
import java.util.List;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestServerContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.fabricmc.fabric.api.client.gametest.v1.screenshot.TestScreenshotOptions;
import net.kasax.tamagotchi.block.FoodBowlBlock;
import net.kasax.tamagotchi.block.PetBathBlock;
import net.kasax.tamagotchi.pet.PetAction;
import net.kasax.tamagotchi.pet.PetSpecies;
import net.kasax.tamagotchi.pet.TamaPet;
import net.kasax.tamagotchi.registry.ModBlocks;
import net.kasax.tamagotchi.registry.ModEntities;
import net.kasax.tamagotchi.registry.ModItems;
import net.minecraft.core.BlockPos;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
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
        this.ctx = context;
        ctx.getInput().resizeWindow(1280, 800);
        ctx.runOnClient(mc -> mc.options.fov().set(60));
        hud(false);
        try (TestSingleplayerContext sp = ctx.worldBuilder().create()) {
            this.server = sp.getServer();
            cmd("time set noon");
            cmd("weather clear");
            ctx.waitTicks(40);
            lineup(false);
            lineup(true);
            closeups();
            furniture();
            screen();
            checks();
        }
        LOG.info("[TamaTest] ===== results =====");
        for (String r : this.results) {
            LOG.info("[TamaTest] {}", r);
        }
    }

    private void hud(boolean visible) {
        ctx.runOnClient(mc -> {
            if (mc.gui.hud.isHidden() == visible) {
                mc.gui.hud.toggle();
            }
        });
    }

    private void cmd(String c) {
        this.server.runCommand(c);
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
        TamaPet pet = ModEntities.type(s).create(level, EntitySpawnReason.COMMAND);
        pet.snapTo(x, Y, z, yaw, 0);
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
        cmd(backpacks ? "tp @p 0 -55.5 9 160 32" : "tp @p 0 -57.2 -6.5 0 22");
        ctx.waitTicks(30);
        shot(backpacks ? "02_lineup_backpacks" : "01_lineup");
    }

    private void closeups() {
        clear();
        PetSpecies[] all = PetSpecies.values();
        for (PetSpecies s : all) {
            server.runOnServer(srv -> spawn(srv.overworld(), player(srv), s, 0.5, 0.5, 200F, false));
            cmd("tp @p 1.9 -58.6 -1.6 30 20");
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
        server.runOnServer(s -> {
            ServerLevel level = s.overworld();
            Block[] blocks = {ModBlocks.PET_BED, ModBlocks.PET_BASKET, ModBlocks.DRAGON_NEST, ModBlocks.FOOD_BOWL, ModBlocks.PET_BATH,
                    ModBlocks.BOUNCY_MUSHROOM, ModBlocks.RUNNING_WHEEL, ModBlocks.SCRATCHING_POST, ModBlocks.PET_HOUSE};
            for (int i = 0; i < blocks.length; i++) {
                BlockState st = blocks[i].defaultBlockState();
                if (blocks[i] == ModBlocks.FOOD_BOWL) st = st.setValue(FoodBowlBlock.FILL, 3);
                if (blocks[i] == ModBlocks.PET_BATH) st = st.setValue(PetBathBlock.FILLED, true);
                level.setBlockAndUpdate(new BlockPos(-8 + i * 2, Y, 0), st);
            }
        });
        cmd("tp @p 0 -56 -8 0 25");
        ctx.waitTicks(30);
        shot("20_furniture");
        // a pet running in the wheel, one sleeping in the bed
        server.runOnServer(s -> {
            ServerLevel level = s.overworld();
            TamaPet runner = spawn(level, player(s), PetSpecies.VOID_KITTEN, 4.5, 0.5, 180, false);
            runner.setFlag(TamaPet.F_RUNNING, true);
            net.kasax.tamagotchi.block.RunningWheelBlock.setRunning(level, new BlockPos(4, Y, 0), true);
            TamaPet sleeper = spawn(level, player(s), PetSpecies.FROST_PENGUIN, -7.5, 0.5, 200, false);
            sleeper.setSleeping(true);
            TamaPet bather = spawn(level, player(s), PetSpecies.JUNGLE_DRAGON, 0.5, 0.5, 180, false);
            bather.setFlag(TamaPet.F_BATHING, true);
        });
        cmd("tp @p 0 -57 -5 0 20");
        ctx.waitTicks(20);
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
            pet.setSnacks(3);
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
        hud(false);
        ctx.waitTicks(5);
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
            TamaPet wild = ModEntities.type(PetSpecies.HEX_TOAD).create(level, EntitySpawnReason.COMMAND);
            wild.snapTo(0.5, Y, 2.5, 0, 0);
            level.addFreshEntity(wild);
            p.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND, new ItemStack(ModItems.TAMAGOTCHI_HEART));
            wild.mobInteract(p, net.minecraft.world.InteractionHand.MAIN_HAND);
            tamed[0] = wild.isTame() && wild.isOwnedBy(p) && wild.hasCustomName();
        });
        check("tame with Tamagotchi Heart", tamed[0]);

        // backpack on with sneak + chest, then off spills everything
        int[] spilled = {0};
        boolean[] equipped = {false};
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
            p.setShiftKeyDown(false);
            spilled[0] = level.getEntitiesOfClass(ItemEntity.class, pet.getBoundingBox().inflate(4)).size();
        });
        check("sneak + chest equips a backpack", equipped[0]);
        check("sneak + empty hand spills the backpack (" + spilled[0] + " item entities)", spilled[0] >= 3);

        // golden apple goes into the snack pouch
        int[] snacks = {0};
        server.runOnServer(s -> {
            ServerPlayer p = player(s);
            TamaPet pet = s.overworld().getEntitiesOfClass(TamaPet.class, p.getBoundingBox().inflate(8)).get(0);
            p.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND, new ItemStack(Items.GOLDEN_APPLE, 2));
            pet.mobInteract(p, net.minecraft.world.InteractionHand.MAIN_HAND);
            pet.mobInteract(p, net.minecraft.world.InteractionHand.MAIN_HAND);
            snacks[0] = pet.snacks();
        });
        check("golden apples fill the snack pouch (" + snacks[0] + ")", snacks[0] == 2);

        // fainting leaves a Tama Egg that brings the pet back
        boolean[] egg = {false};
        server.runOnServer(s -> {
            ServerLevel level = s.overworld();
            ServerPlayer p = player(s);
            TamaPet pet = level.getEntitiesOfClass(TamaPet.class, p.getBoundingBox().inflate(8)).get(0);
            pet.hurtServer(level, level.damageSources().generic(), 1000F);
            egg[0] = !pet.isAlive() && level.getEntitiesOfClass(ItemEntity.class, p.getBoundingBox().inflate(8),
                    e -> e.getItem().is(ModItems.TAMA_EGG)).size() == 1;
        });
        check("a tamed pet faints into a Tama Egg", egg[0]);
        ctx.waitTicks(5);
    }
}
