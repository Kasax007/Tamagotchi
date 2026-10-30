package net.kasax.tamagotchi.test;

import java.util.ArrayList;
import java.util.List;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestServerContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.fabricmc.fabric.api.client.gametest.v1.screenshot.TestScreenshotOptions;
import net.kasax.tamagotchi.block.Dyeing;
import net.kasax.tamagotchi.block.EggLampBlock;
import net.kasax.tamagotchi.block.PetFlapBlock;
import net.kasax.tamagotchi.block.PetIncubatorBlock;
import net.kasax.tamagotchi.block.PetIncubatorBlockEntity;
import net.kasax.tamagotchi.block.PetPortraitBlock;
import net.kasax.tamagotchi.block.PetPortraitBlockEntity;
import net.kasax.tamagotchi.block.PlushBlock;
import net.kasax.tamagotchi.block.ToyBoxBlock;
import net.kasax.tamagotchi.block.ToyBoxBlockEntity;
import net.kasax.tamagotchi.block.TreatDispenserBlockEntity;
import net.kasax.tamagotchi.item.TamaEggItem;
import net.kasax.tamagotchi.pet.PetNeeds;
import net.kasax.tamagotchi.pet.PetSpecies;
import net.kasax.tamagotchi.pet.TamaPet;
import net.kasax.tamagotchi.registry.ModBlocks;
import net.kasax.tamagotchi.registry.ModEntities;
import net.kasax.tamagotchi.registry.ModItems;
import net.kasax.tamagotchi.registry.ModTab;
import net.minecraft.client.gui.screens.inventory.CreativeModeInventoryScreen;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.animal.cow.Cow;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.DyeColor;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.BlockItemStateProperties;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.pathfinder.Path;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * The furniture added after the first release: screenshots for review and one functional check per block.
 * Run only this with {@code ./gradlew runClientGameTest -Ptests=blocks}.
 */
public class BlockGallery implements FabricClientGameTest {
    private static final Logger LOG = LoggerFactory.getLogger("TamaTest");
    private static final int Y = -60;   // flat world ground is at y=-61

    private ClientGameTestContext ctx;
    private TestServerContext server;
    private final List<String> results = new ArrayList<>();

    @Override
    public void runTest(ClientGameTestContext context) {
        String only = System.getProperty("tama.tests", "all");
        if (!only.equals("all") && !only.contains("blocks")) {
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
            cmd("gamerule advance_time false");
            ctx.waitTicks(40);
            overview();
            plushies();
            dyes();
            inUse();
            items();
            checks();
        }
        LOG.info("[TamaTest] ===== block results =====");
        for (String r : this.results) {
            LOG.info("[TamaTest] {}", r);
        }
    }

    // ------------------------------------------------------------------ helpers

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
            AABB box = player(s).getBoundingBox().inflate(64);
            level.getEntitiesOfClass(TamaPet.class, box).forEach(e -> e.discard());
            level.getEntitiesOfClass(ItemEntity.class, box).forEach(e -> e.discard());
            level.getEntitiesOfClass(Cow.class, box).forEach(e -> e.discard());
        });
        cmd("fill -20 " + Y + " -20 20 " + (Y + 6) + " 20 air");
        cmd("fill -20 " + (Y - 1) + " -20 20 " + (Y - 1) + " 20 grass_block");   // grass under the walls turns to dirt
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

    private static BlockHitResult hit(BlockPos pos, Direction face) {
        return new BlockHitResult(Vec3.atCenterOf(pos), face, pos, false);
    }

    /** A right-click on a block by the player, the way the game does it (item first, then the empty-hand use). */
    private static void click(ServerPlayer p, ServerLevel level, BlockPos pos, ItemStack held) {
        p.setItemInHand(InteractionHand.MAIN_HAND, held);
        p.gameMode.useItemOn(p, level, p.getMainHandItem(), InteractionHand.MAIN_HAND, hit(pos, Direction.NORTH));
    }

    private static ItemStack eggOf(ServerLevel level, ServerPlayer owner, PetSpecies s) {
        TamaPet pet = spawn(level, owner, s, 0.5, -10.5, 0, false);
        ItemStack egg = TamaEggItem.fromPet(pet);
        pet.discard();
        return egg;
    }

    private void check(String name, boolean ok) {
        this.results.add((ok ? "PASS " : "FAIL ") + name);
    }

    // ------------------------------------------------------------------ scenes

    /** Every new block in a little room: lamps, toy box, dispenser, incubator, flap and portraits on the wall. */
    private void overview() {
        clear();
        server.runOnServer(s -> {
            ServerLevel level = s.overworld();
            ServerPlayer p = player(s);
            for (int x = -6; x <= 6; x++) {
                for (int y = Y; y <= Y + 2; y++) {
                    level.setBlockAndUpdate(new BlockPos(x, y, 4), Blocks.SPRUCE_PLANKS.defaultBlockState());
                }
            }
            level.setBlockAndUpdate(new BlockPos(2, Y, 4), ModBlocks.PET_FLAP.defaultBlockState().setValue(PetFlapBlock.FACING, Direction.NORTH));
            level.setBlockAndUpdate(new BlockPos(-3, Y + 1, 3), ModBlocks.PET_PORTRAIT.defaultBlockState().setValue(PetPortraitBlock.FACING, Direction.NORTH));
            level.setBlockAndUpdate(new BlockPos(-1, Y + 1, 3), ModBlocks.PET_PORTRAIT.defaultBlockState().setValue(PetPortraitBlock.FACING, Direction.NORTH)
                    .setValue(Dyeing.BACKDROP, DyeColor.LIGHT_BLUE));
            TamaPet dragon = spawn(level, p, PetSpecies.DESERT_DRAGON, -10, -10, 0, false);
            dragon.setCustomName(net.minecraft.network.chat.Component.literal("Sandy"));
            TamaPet penguin = spawn(level, p, PetSpecies.FROST_PENGUIN, -10, -12, 0, false);
            penguin.setCustomName(net.minecraft.network.chat.Component.literal("Waddles"));
            penguin.equipBackpack();
            ((PetPortraitBlockEntity) level.getBlockEntity(new BlockPos(-3, Y + 1, 3))).paint(dragon);
            ((PetPortraitBlockEntity) level.getBlockEntity(new BlockPos(-1, Y + 1, 3))).paint(penguin);
            dragon.discard();
            penguin.discard();
            level.setBlockAndUpdate(new BlockPos(-5, Y, 1), ModBlocks.EGG_LAMP.defaultBlockState());
            level.setBlockAndUpdate(new BlockPos(-4, Y, 1), ModBlocks.EGG_LAMP.defaultBlockState().setValue(Dyeing.COLOR, DyeColor.LIGHT_BLUE));
            level.setBlockAndUpdate(new BlockPos(5, Y, 1), ModBlocks.EGG_LAMP.defaultBlockState().setValue(EggLampBlock.LIT, false));
            level.setBlockAndUpdate(new BlockPos(-2, Y, 1), ModBlocks.TOY_BOX.defaultBlockState());
            level.setBlockAndUpdate(new BlockPos(0, Y, 1), ModBlocks.TOY_BOX.defaultBlockState().setValue(ToyBoxBlock.OPEN, true));
            level.setBlockAndUpdate(new BlockPos(1, Y, 2), ModBlocks.TREAT_DISPENSER.defaultBlockState());
            BlockPos inc = new BlockPos(3, Y, 1);
            level.setBlockAndUpdate(inc, ModBlocks.PET_INCUBATOR.defaultBlockState());
            ((PetIncubatorBlockEntity) level.getBlockEntity(inc)).insert(eggOf(level, p, PetSpecies.FROST_PENGUIN), null);
            level.setBlockAndUpdate(new BlockPos(4, Y, 2), ModBlocks.PET_INCUBATOR.defaultBlockState());
        });
        cam("0.5 -58.2 -3.5 0 22");
        ctx.waitTicks(30);
        shot("40_new_furniture");
        cam("-2 -58.6 0.2 0 8");
        ctx.waitTicks(10);
        shot("41_portraits");
        cam("3.5 -59.2 -0.6 0 35");
        ctx.waitTicks(10);
        shot("42_incubator_lamp");
        // zoomed in from four blocks away (the camera is at eye height, 1.62 above the feet)
        ctx.runOnClient(mc -> mc.options.fov().set(30));
        cam("3.5 -60 -2.5 0 17");
        ctx.waitTicks(4);
        shot("42b_incubator_close");
        ctx.runOnClient(mc -> mc.options.fov().set(60));
        // dusk: the lamps and the incubator glow
        cmd("time set 13800");
        cam("0.5 -58.2 -3.5 0 22");
        ctx.waitTicks(20);
        shot("43_new_furniture_night");
        cmd("time set noon");
    }

    private void plushies() {
        clear();
        server.runOnServer(s -> {
            ServerLevel level = s.overworld();
            PetSpecies[] all = PetSpecies.values();
            for (int i = 0; i < all.length; i++) {
                BlockPos pos = new BlockPos(i % 5 - 2, Y + i / 5, i / 5);
                if (i / 5 == 1) {
                    level.setBlockAndUpdate(pos.below(), Blocks.OAK_SLAB.defaultBlockState()
                            .setValue(net.minecraft.world.level.block.SlabBlock.TYPE, net.minecraft.world.level.block.state.properties.SlabType.TOP));
                }
                level.setBlockAndUpdate(pos, ModBlocks.PLUSHES.get(all[i]).defaultBlockState().setValue(PlushBlock.ROTATION, 8));
            }
        });
        cam("0.5 -58.4 -2.9 0 24");
        ctx.waitTicks(20);
        shot("44_plushies");
        cam("-1.0 -59.3 -1.2 0 18");
        ctx.waitTicks(5);
        shot("45_plushies_close");
    }

    private void dyes() {
        clear();
        server.runOnServer(s -> {
            ServerLevel level = s.overworld();
            DyeColor[] colors = {DyeColor.RED, DyeColor.ORANGE, DyeColor.YELLOW, DyeColor.LIME, DyeColor.LIGHT_BLUE, DyeColor.PURPLE,
                    DyeColor.PINK, DyeColor.WHITE};
            for (int i = 0; i < colors.length; i++) {
                level.setBlockAndUpdate(new BlockPos(i - 4, Y, 0), ModBlocks.PET_BED.defaultBlockState().setValue(Dyeing.COLOR, colors[i]));
                level.setBlockAndUpdate(new BlockPos(i - 4, Y, 2), ModBlocks.PET_BASKET.defaultBlockState().setValue(Dyeing.COLOR, colors[colors.length - 1 - i]));
                level.setBlockAndUpdate(new BlockPos(i - 4, Y, 4), ModBlocks.EGG_LAMP.defaultBlockState().setValue(Dyeing.COLOR, colors[i]));
            }
        });
        cam("0 -57.4 -3.4 0 32");
        ctx.waitTicks(20);
        shot("46_dyed");
    }

    /** Pets with the new things: toy in the mouth at the toy box, cuddling a plush, asleep by its own plush, a treat in the air. */
    private void inUse() {
        clear();
        BlockPos box = new BlockPos(-3, Y, 1), plush = new BlockPos(0, Y, 1), bed = new BlockPos(3, Y, 1), dispenser = new BlockPos(-1, Y, 4);
        server.runOnServer(s -> {
            ServerLevel level = s.overworld();
            ServerPlayer p = player(s);
            level.setBlockAndUpdate(box, ModBlocks.TOY_BOX.defaultBlockState().setValue(ToyBoxBlock.OPEN, true));
            ((ToyBoxBlockEntity) level.getBlockEntity(box)).setItem(0, new ItemStack(ModItems.SQUEAKY_BALL));
            TamaPet kitten = spawn(level, p, PetSpecies.VOID_KITTEN, box.getX() + 0.5, box.getZ() - 0.6, 200, false);
            kitten.setCarried(new ItemStack(ModItems.SQUEAKY_BALL));
            kitten.playAction(net.kasax.tamagotchi.pet.PetAction.PLAY);
            level.setBlockAndUpdate(plush, ModBlocks.PLUSHES.get(PetSpecies.HEX_TOAD).defaultBlockState().setValue(PlushBlock.ROTATION, 12));
            TamaPet toad = spawn(level, p, PetSpecies.HEX_TOAD, plush.getX() - 0.35, plush.getZ() + 0.5, 270, false);
            toad.setInSittingPose(true);
            toad.playAction(net.kasax.tamagotchi.pet.PetAction.PETTED);
            level.setBlockAndUpdate(bed, ModBlocks.PET_BED.defaultBlockState().setValue(Dyeing.COLOR, DyeColor.LIGHT_BLUE));
            level.setBlockAndUpdate(bed.east(), ModBlocks.PLUSHES.get(PetSpecies.FROST_PENGUIN).defaultBlockState().setValue(PlushBlock.ROTATION, 6));
            spawn(level, p, PetSpecies.FROST_PENGUIN, bed.getX() + 0.5, bed.getZ() + 0.5, 200, false).setSleeping(true);
            level.setBlockAndUpdate(dispenser, ModBlocks.TREAT_DISPENSER.defaultBlockState());
            TamaPet pup = spawn(level, p, PetSpecies.EMBER_PUP, dispenser.getX() + 2.5, dispenser.getZ() - 1.5, 140, false);
            // a treat frozen mid-flight between the dispenser and the pup
            ItemEntity treat = new ItemEntity(level, dispenser.getX() + 1.5, Y + 1.6, dispenser.getZ() - 0.4, new ItemStack(ModItems.EMBER_JERKY), 0, 0, 0);
            treat.setNoGravity(true);
            treat.setPickUpDelay(32767);
            level.addFreshEntity(treat);
            pup.lookAt(net.minecraft.commands.arguments.EntityAnchorArgument.Anchor.EYES, treat.position());
        });
        cam("0.5 -58.1 -3.4 0 26");
        ctx.waitTicks(12);
        shot("47_in_use");
        cam("-2.6 -59.1 -1.6 0 22");
        ctx.waitTicks(2);
        shot("47b_toy_box_play");
        cam("1.6 -59.0 -1.5 0 22");
        ctx.waitTicks(2);
        shot("47c_cuddle_and_sleep");
    }

    /** The new items in hand and in the creative tab. */
    private void items() {
        clear();
        hud(true);
        cmd("gamemode survival @p");
        server.runOnServer(s -> {
            ServerPlayer p = player(s);
            p.getInventory().clearContent();
            p.getInventory().setItem(0, new ItemStack(ModBlocks.PLUSHES.get(PetSpecies.SCULK_WISP)));
            p.getInventory().setItem(1, new ItemStack(ModBlocks.PLUSHES.get(PetSpecies.MIMIC)));
            p.getInventory().setItem(2, new ItemStack(ModBlocks.EGG_LAMP));
            p.getInventory().setItem(3, new ItemStack(ModBlocks.PET_PORTRAIT));
            p.getInventory().setItem(4, new ItemStack(ModBlocks.TOY_BOX));
            p.getInventory().setItem(5, new ItemStack(ModBlocks.TREAT_DISPENSER));
            p.getInventory().setItem(6, new ItemStack(ModBlocks.PET_INCUBATOR));
            p.getInventory().setItem(7, new ItemStack(ModBlocks.PET_FLAP));
            ItemStack blueBed = new ItemStack(ModBlocks.PET_BED);
            blueBed.set(DataComponents.BLOCK_STATE, BlockItemStateProperties.EMPTY.with(Dyeing.COLOR, DyeColor.BLUE));
            p.getInventory().setItem(8, blueBed);
            p.getInventory().setSelectedSlot(0);
        });
        cam("0.5 -59 -2.5 0 10");
        ctx.waitTicks(20);
        shot("48_items_hotbar");
        cmd("gamemode creative @p");
        ctx.waitTicks(10);
        ctx.runOnClient(mc -> {
            CreativeModeInventoryScreen inv = new CreativeModeInventoryScreen(mc.player, mc.player.connection.enabledFeatures(), false);
            mc.gui.setScreen(inv);
            inv.setSelectedTab(BuiltInRegistries.CREATIVE_MODE_TAB.getValueOrThrow(ModTab.KEY));
        });
        ctx.waitTicks(10);
        shot("49_creative_tab");
        ctx.runOnClient(mc -> mc.gui.setScreen(null));
        hud(false);
        ctx.waitTicks(5);
    }

    // ------------------------------------------------------------------ functional checks

    private void checks() {
        clear();
        flap();
        dispenser();
        incubator();
        toyBox();
        plushSleep();
        portraitAndDyes();
    }

    /** A wall with a pet flap: the pet walks through to its owner, a cow can't find a way, and the player bumps into it. */
    private void flap() {
        BlockPos flap = new BlockPos(0, Y, 0);
        server.runOnServer(s -> {
            ServerLevel level = s.overworld();
            ServerPlayer p = player(s);
            for (int x = -8; x <= 8; x++) {
                for (int y = Y; y <= Y + 3; y++) {
                    level.setBlockAndUpdate(new BlockPos(x, y, 0), Blocks.STONE_BRICKS.defaultBlockState());
                }
            }
            level.setBlockAndUpdate(flap, ModBlocks.PET_FLAP.defaultBlockState());
            p.teleportTo(0.5, Y, 6.5);
            TamaPet pet = spawn(level, p, PetSpecies.VOID_KITTEN, 0.5, -4.5, 0, true);
            pet.getNavigation().moveTo(0.5, Y, 5.5, 1.0);
            Cow cow = EntityTypes.COW.create(level, EntitySpawnReason.COMMAND);
            cow.snapTo(2.5, Y, -4.5, 0, 0);
            level.addFreshEntity(cow);
        });
        ctx.waitTicks(10);
        boolean[] cowBlocked = {false};
        boolean[] playerBlocked = {false};
        server.runOnServer(s -> {
            ServerLevel level = s.overworld();
            Cow cow = level.getEntitiesOfClass(Cow.class, new AABB(flap).inflate(10)).get(0);
            Path path = cow.getNavigation().createPath(new BlockPos(0, Y, 5), 0);
            cowBlocked[0] = path == null || !path.canReach() || path.getEndNode().z < 1;
            AABB inFlap = new AABB(flap).deflate(0.2);
            playerBlocked[0] = !level.noCollision(player(s), inFlap);
            TamaPet pet = level.getEntitiesOfClass(TamaPet.class, new AABB(flap).inflate(10)).get(0);
            pet.getNavigation().moveTo(0.5, Y, 5.5, 1.0);
        });
        boolean through = false;
        boolean opened = false;
        for (int i = 0; i < 20 && !through; i++) {
            ctx.waitTicks(10);
            boolean[] r = {false, false};
            server.runOnServer(s -> {
                ServerLevel level = s.overworld();
                TamaPet pet = level.getEntitiesOfClass(TamaPet.class, new AABB(flap).inflate(10)).get(0);
                r[0] = pet.getZ() > 1.5;
                r[1] = level.getBlockState(flap).getValue(PetFlapBlock.OPEN);
                if (!r[0] && pet.getNavigation().isDone()) {
                    pet.getNavigation().moveTo(0.5, Y, 5.5, 1.0);
                }
            });
            through = r[0];
            opened |= r[1];
        }
        check("a pet walks through the pet flap", through);
        check("the flap swings open for the pet", opened);
        check("a cow finds no path through the flap", cowBlocked[0]);
        check("the player bumps into the flap", playerBlocked[0]);
        clear();
        cmd("fill -8 " + Y + " 0 8 " + (Y + 3) + " 0 air");
    }

    /** Three fish crackers, a hungry penguin, a redstone pulse: one treat flies over and gets eaten. */
    private void dispenser() {
        BlockPos pos = new BlockPos(0, Y, 0);
        float[] before = {0};
        server.runOnServer(s -> {
            ServerLevel level = s.overworld();
            ServerPlayer p = player(s);
            p.teleportTo(0.5, Y, -6.5);
            level.setBlockAndUpdate(pos, ModBlocks.TREAT_DISPENSER.defaultBlockState());
            ((TreatDispenserBlockEntity) level.getBlockEntity(pos)).setItem(4, new ItemStack(ModItems.FISH_CRACKERS, 3));
            TamaPet pet = spawn(level, p, PetSpecies.FROST_PENGUIN, 4.5, 2.5, 0, true);
            pet.setOrderedToSit(true);
            pet.needs().add(PetNeeds.Need.HUNGER, -60);
            before[0] = pet.needs().hunger;
            level.setBlockAndUpdate(pos.west(), Blocks.REDSTONE_BLOCK.defaultBlockState());
        });
        ctx.waitTicks(60);
        int[] left = {0};
        float[] after = {0};
        server.runOnServer(s -> {
            ServerLevel level = s.overworld();
            left[0] = ((TreatDispenserBlockEntity) level.getBlockEntity(pos)).getItem(4).getCount();
            after[0] = level.getEntitiesOfClass(TamaPet.class, new AABB(pos).inflate(10)).get(0).needs().hunger;
        });
        check("the treat dispenser shoots one treat on a redstone pulse (" + left[0] + " left)", left[0] == 2);
        check("the pet catches and eats it (hunger " + (int) before[0] + " -> " + (int) after[0] + ")", after[0] > before[0] + 20);
        clear();
    }

    /** An egg in the incubator hatches after 30 s with full health. */
    private void incubator() {
        BlockPos pos = new BlockPos(0, Y, 0);
        server.runOnServer(s -> {
            ServerLevel level = s.overworld();
            ServerPlayer p = player(s);
            level.setBlockAndUpdate(pos, ModBlocks.PET_INCUBATOR.defaultBlockState());
            ItemStack egg = eggOf(level, p, PetSpecies.EMBER_PUP);
            click(p, level, pos, egg);
        });
        boolean[] lit = {false};
        server.runOnServer(s -> lit[0] = s.overworld().getBlockState(pos).getValue(PetIncubatorBlock.LIT));
        ctx.waitTicks(PetIncubatorBlockEntity.HATCH_TICKS - 40);   // the test ticks client and server together: no /tick sprint
        boolean hatched = false;
        float[] health = {0, 0};
        for (int i = 0; i < 12 && !hatched; i++) {
            ctx.waitTicks(10);
            boolean[] h = {false};
            server.runOnServer(s -> {
                List<TamaPet> pets = s.overworld().getEntitiesOfClass(TamaPet.class, new AABB(pos).inflate(4));
                if (!pets.isEmpty()) {
                    h[0] = true;
                    health[0] = pets.get(0).getHealth();
                    health[1] = pets.get(0).getMaxHealth();
                }
            });
            hatched = h[0];
        }
        boolean[] empty = {false};
        server.runOnServer(s -> {
            ServerLevel level = s.overworld();
            empty[0] = ((PetIncubatorBlockEntity) level.getBlockEntity(pos)).getEgg().isEmpty() && !level.getBlockState(pos).getValue(PetIncubatorBlock.LIT);
        });
        check("the incubator takes the egg and glows", lit[0]);
        check("the pet hatches from the incubator", hatched);
        check("it hatches at full health (" + health[0] + " / " + health[1] + ")", hatched && health[0] >= health[1]);
        check("the incubator is empty and dark again", empty[0]);
        clear();
    }

    /** A bored pet next to a toy box with a ball inside opens it and plays. */
    private void toyBox() {
        BlockPos pos = new BlockPos(0, Y, 0);
        float[] before = {0};
        server.runOnServer(s -> {
            ServerLevel level = s.overworld();
            ServerPlayer p = player(s);
            p.teleportTo(0.5, Y, -5.5);
            level.setBlockAndUpdate(pos, ModBlocks.TOY_BOX.defaultBlockState());
            ((ToyBoxBlockEntity) level.getBlockEntity(pos)).setItem(0, new ItemStack(ModItems.SQUEAKY_BALL));
            TamaPet pet = spawn(level, p, PetSpecies.EMBER_PUP, 2.5, 2.5, 0, true);
            pet.needs().add(PetNeeds.Need.FUN, -70);
            pet.needs().add(PetNeeds.Need.HUNGER, 100);
            pet.needs().add(PetNeeds.Need.HYGIENE, 100);
            pet.needs().add(PetNeeds.Need.ENERGY, 100);
            before[0] = pet.needs().fun;
        });
        boolean open = false;
        boolean ballInMouth = false;
        for (int i = 0; i < 60 && !(open && ballInMouth); i++) {
            ctx.waitTicks(10);
            boolean[] r = {false, false};
            server.runOnServer(s -> {
                ServerLevel level = s.overworld();
                r[0] = level.getBlockState(pos).getValue(ToyBoxBlock.OPEN);
                List<TamaPet> pets = level.getEntitiesOfClass(TamaPet.class, new AABB(pos).inflate(10));
                r[1] = !pets.isEmpty() && pets.get(0).getCarried().is(ModItems.SQUEAKY_BALL);
            });
            open |= r[0];
            ballInMouth |= r[1];
        }
        ctx.waitTicks(140);
        float[] after = {0};
        boolean[] closed = {false};
        boolean[] kept = {false};
        server.runOnServer(s -> {
            ServerLevel level = s.overworld();
            after[0] = level.getEntitiesOfClass(TamaPet.class, new AABB(pos).inflate(10)).get(0).needs().fun;
            closed[0] = !level.getBlockState(pos).getValue(ToyBoxBlock.OPEN);
            kept[0] = ((ToyBoxBlockEntity) level.getBlockEntity(pos)).getItem(0).is(ModItems.SQUEAKY_BALL);
        });
        check("a bored pet opens the toy box", open);
        check("it plays with the ball from the box", ballInMouth);
        check("playing is fun (" + (int) before[0] + " -> " + (int) after[0] + ")", after[0] > before[0] + 10);
        check("the lid closes again and the ball stays in the box", closed[0] && kept[0]);
        clear();
    }

    /** Two sleeping penguins, one next to a penguin plush: that one rests faster. Plus a squeeze. */
    private void plushSleep() {
        float[] start = {0, 0};
        server.runOnServer(s -> {
            ServerLevel level = s.overworld();
            ServerPlayer p = player(s);
            level.setBlockAndUpdate(new BlockPos(-6, Y, 0), ModBlocks.PLUSHES.get(PetSpecies.FROST_PENGUIN).defaultBlockState());
            TamaPet a = spawn(level, p, PetSpecies.FROST_PENGUIN, -4.5, 0.5, 0, false);
            TamaPet b = spawn(level, p, PetSpecies.FROST_PENGUIN, 6.5, 0.5, 0, false);
            for (TamaPet t : List.of(a, b)) {
                t.needs().add(PetNeeds.Need.ENERGY, -80);
                t.setSleeping(true);
                t.setNoAi(false);
                t.setOrderedToSit(true);
            }
            start[0] = a.needs().energy;
            start[1] = b.needs().energy;
            a.addTag("plush_side");
        });
        ctx.waitTicks(260);
        float[] end = {0, 0};
        boolean[] squeezed = {false};
        server.runOnServer(s -> {
            ServerLevel level = s.overworld();
            for (TamaPet t : level.getEntitiesOfClass(TamaPet.class, new AABB(0, Y, 0, 0, Y, 0).inflate(12))) {
                end[t.entityTags().contains("plush_side") ? 0 : 1] = t.needs().energy;
            }
            BlockPos plush = new BlockPos(-6, Y, 0);
            click(player(s), level, plush, ItemStack.EMPTY);
            squeezed[0] = level.getBlockState(plush).getBlock() instanceof PlushBlock;
        });
        float gainPlush = end[0] - start[0], gainAlone = end[1] - start[1];
        check(String.format("sleeping next to its own plush rests faster (+%.1f vs +%.1f)", gainPlush, gainAlone), gainPlush > gainAlone * 1.3F);
        check("a plush can be squeezed and stays put", squeezed[0]);
        clear();
    }

    /** The portrait paints the nearest pet, then the next; dyes recolour; colours survive breaking; the lamp switches. */
    private void portraitAndDyes() {
        BlockPos portrait = new BlockPos(0, Y + 1, 0), bed = new BlockPos(3, Y, 0), lamp = new BlockPos(-3, Y, 0);
        String[] painted = {"", ""};
        boolean[] backdrop = {false};
        DyeColor[] bedColor = {null};
        DyeColor[] dropColor = {null};
        int[] light = {-1, -1};
        server.runOnServer(s -> {
            ServerLevel level = s.overworld();
            ServerPlayer p = player(s);
            p.teleportTo(0.5, Y, -2.5);
            level.setBlockAndUpdate(portrait, ModBlocks.PET_PORTRAIT.defaultBlockState());
            TamaPet near = spawn(level, p, PetSpecies.MIMIC, 1.5, -1.5, 0, false);
            near.setCustomName(net.minecraft.network.chat.Component.literal("Chompy"));
            TamaPet far = spawn(level, p, PetSpecies.SCULK_WISP, 6.5, -4.5, 0, false);
            far.setCustomName(net.minecraft.network.chat.Component.literal("Echo"));
            click(p, level, portrait, ItemStack.EMPTY);
            painted[0] = ((PetPortraitBlockEntity) level.getBlockEntity(portrait)).name();
            click(p, level, portrait, ItemStack.EMPTY);
            painted[1] = ((PetPortraitBlockEntity) level.getBlockEntity(portrait)).name();
            click(p, level, portrait, new ItemStack(Items.DYE.pick(DyeColor.LIME)));
            backdrop[0] = level.getBlockState(portrait).getValue(Dyeing.BACKDROP) == DyeColor.LIME;

            level.setBlockAndUpdate(bed, ModBlocks.PET_BED.defaultBlockState());
            click(p, level, bed, new ItemStack(Items.DYE.pick(DyeColor.BLUE)));
            bedColor[0] = level.getBlockState(bed).getValue(Dyeing.COLOR);
            level.destroyBlock(bed, true, p);
            for (ItemEntity it : level.getEntitiesOfClass(ItemEntity.class, new AABB(bed).inflate(2))) {
                if (it.getItem().is(ModBlocks.PET_BED.asItem())) {
                    BlockItemStateProperties props = it.getItem().getOrDefault(DataComponents.BLOCK_STATE, BlockItemStateProperties.EMPTY);
                    dropColor[0] = props.get(Dyeing.COLOR);
                }
            }
            level.setBlockAndUpdate(lamp, ModBlocks.EGG_LAMP.defaultBlockState());
            light[0] = level.getBlockState(lamp).getLightEmission();
            click(p, level, lamp, ItemStack.EMPTY);
            light[1] = level.getBlockState(lamp).getLightEmission();
        });
        check("the portrait paints the nearest pet (" + painted[0] + ")", painted[0].equals("Chompy"));
        check("a second click paints the next pet (" + painted[1] + ")", painted[1].equals("Echo"));
        check("a dye changes the portrait backdrop", backdrop[0]);
        check("a dye changes the bed colour (" + bedColor[0] + ")", bedColor[0] == DyeColor.BLUE);
        check("a broken bed keeps its colour (" + dropColor[0] + ")", dropColor[0] == DyeColor.BLUE);
        check("the egg lamp glows and switches off (" + light[0] + " -> " + light[1] + ")", light[0] == 14 && light[1] == 0);
        clear();
    }
}
