package net.kasax.tamacraft.test;

import java.util.ArrayList;
import java.util.List;
import net.kasax.tamacraft.Tamacraft;
import net.kasax.tamacraft.menu.PetMenu;
import net.kasax.tamacraft.pet.PetNeeds;
import net.kasax.tamacraft.pet.PetSpecies;
import net.kasax.tamacraft.pet.TamaPet;
import net.kasax.tamacraft.registry.ModEntities;
import net.kasax.tamacraft.registry.ModItems;
import net.kasax.tamacraft.registry.ModMenus;
import io.netty.buffer.Unpooled;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import java.util.function.Consumer;
import net.minecraft.core.Holder;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.Registries;
import net.minecraft.gametest.framework.FunctionGameTestInstance;
import net.minecraft.gametest.framework.TestData;
import net.minecraft.gametest.framework.TestEnvironmentDefinition;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.neoforged.neoforge.event.RegisterGameTestsEvent;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.EntityBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;

/**
 * Server game tests (./gradlew runGameTestServer): every block and pet exists and works in a world, and the core of
 * the client self-test's functional checks (taming, backpack, pet screen, pager, feeding, snacks, fainting).
 */
public final class ServerTests {
    private static final Identifier FLOOR = id("floor");

    /** Test ids live in the test mod's namespace (only the shipped mod uses tamacraft:...). */
    private static Identifier id(String path) {
        return Identifier.fromNamespaceAndPath("tamacraft_gametest", path);
    }
    /** name, max ticks, test */
    private record Test(String name, int maxTicks, Consumer<GameTestHelper> function) {
    }

    private static final List<Test> TESTS = List.of(new Test("every_block_places", 100, ServerTests::everyBlockPlaces),
            new Test("every_pet_spawns_and_ticks", 200, ServerTests::everyPetSpawnsAndTicks),
            new Test("heart_tames_pet", 100, ServerTests::heartTamesPet),
            new Test("backpack_screen_and_pager", 100, ServerTests::backpackScreenAndPager),
            new Test("kibble_feeds_pet", 100, ServerTests::kibbleFeedsPet),
            new Test("snacks_for_hurt_owner", 200, ServerTests::snacksForHurtOwner),
            new Test("faints_into_egg", 100, ServerTests::faintsIntoEgg));

    /** The test functions (built-in registry, filled with the mod's entries on the first RegisterEvent). */
    public static void registerFunctions() {
        for (Test t : TESTS) {
            Registry.register(net.minecraft.core.registries.BuiltInRegistries.TEST_FUNCTION, id(t.name()), t.function());
        }
    }

    /** The test instances (a data-pack registry since 1.21.5), all on the floor template in an empty environment. */
    public static void registerTests(RegisterGameTestsEvent event) {
        Holder<TestEnvironmentDefinition<?>> env = event.registerEnvironment(id("default"));
        for (Test t : TESTS) {
            event.registerTest(id(t.name()), new FunctionGameTestInstance(
                    ResourceKey.create(Registries.TEST_FUNCTION, id(t.name())),
                    new TestData<>(env, FLOOR, t.maxTicks(), 0, true)));
        }
    }

    private ServerTests() {
    }

    private static List<Block> modBlocks() {
        List<Block> blocks = new ArrayList<>();
        for (Block b : BuiltInRegistries.BLOCK) {
            if (BuiltInRegistries.BLOCK.getKey(b).getNamespace().equals(Tamacraft.MOD_ID)) {
                blocks.add(b);
            }
        }
        return blocks;
    }

    static void everyBlockPlaces(GameTestHelper helper) {
        List<Block> blocks = modBlocks();
        helper.assertTrue(blocks.size() >= 25, "expected the mod's blocks, found " + blocks.size());
        for (int i = 0; i < blocks.size(); i++) {
            BlockPos pos = new BlockPos(i % 9, 1 + (i / 81) * 2, (i / 9) % 9);
            BlockState state = blocks.get(i).defaultBlockState();
            helper.setBlock(pos, state);
            helper.assertBlockState(pos, s -> s.is(state.getBlock()), s -> Component.literal("not placed: " + state));
            if (state.getBlock() instanceof EntityBlock) {
                helper.assertTrue(helper.getBlockEntity(pos, net.minecraft.world.level.block.entity.BlockEntity.class) != null, "no block entity at " + state);
            }
        }
        helper.runAfterDelay(20, () -> {
            for (int i = 0; i < blocks.size(); i++) {
                BlockPos pos = new BlockPos(i % 9, 1 + (i / 81) * 2, (i / 9) % 9);
                Block block = blocks.get(i);
                helper.assertBlockState(pos, s -> s.is(block), s -> Component.literal("gone after ticking: " + block));
            }
            helper.succeed();
        });
    }

    static void everyPetSpawnsAndTicks(GameTestHelper helper) {
        List<TamaPet> pets = new ArrayList<>();
        int i = 0;
        for (PetSpecies s : PetSpecies.values()) {
            pets.add(helper.spawn(ModEntities.type(s), new BlockPos(1 + (i % 4) * 2, 1, 1 + (i / 4) * 3)));
            i++;
        }
        helper.runAfterDelay(100, () -> {
            for (TamaPet pet : pets) {
                helper.assertTrue(pet.isAlive(), pet.species().id() + " died");
                helper.assertTrue(pet.species() == ModEntities.speciesOf(pet.getType()), "wrong species for " + pet.getType());
            }
            helper.succeed();
        });
    }

    private static TamaPet tamedPet(GameTestHelper helper, ServerPlayer player, PetSpecies species) {
        TamaPet pet = helper.spawn(ModEntities.type(species), new BlockPos(4, 1, 4));
        player.snapTo(helper.absoluteVec(new net.minecraft.world.phys.Vec3(4.5, 1, 2.5)));
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(ModItems.TAMACRAFT_HEART));
        pet.mobInteract(player, InteractionHand.MAIN_HAND);
        return pet;
    }

    static void heartTamesPet(GameTestHelper helper) {
        ServerPlayer player = helper.makeMockServerPlayerInLevel();
        TamaPet pet = tamedPet(helper, player, PetSpecies.HEX_TOAD);
        helper.assertTrue(pet.isTame() && pet.isOwnedBy(player) && pet.hasCustomName(), "the heart did not tame the pet");
        helper.succeed();
    }

    static void backpackScreenAndPager(GameTestHelper helper) {
        ServerPlayer player = helper.makeMockServerPlayerInLevel();
        TamaPet pet = tamedPet(helper, player, PetSpecies.EMBER_PUP);
        player.setShiftKeyDown(true);
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.CHEST));
        pet.mobInteract(player, InteractionHand.MAIN_HAND);
        helper.assertTrue(pet.hasBackpack() && pet.storageSlots() == 27, "sneak + chest did not equip a backpack");
        pet.store(new ItemStack(Items.DIAMOND, 5));
        pet.store(new ItemStack(Items.APPLE, 3));
        // the pet screen: the mock player cannot receive NeoForge's open-screen payload (the client self-test opens the
        // real one), so check the menu the client builds from the data the server sends
        RegistryFriendlyByteBuf buf = new RegistryFriendlyByteBuf(Unpooled.buffer(), helper.getLevel().registryAccess());
        new PetMenu.Provider(pet).writeData(buf);
        PetMenu menu = ModMenus.PET_MENU.create(1, player.getInventory(), buf);
        helper.assertTrue(menu.stillValid(player), "the pet menu built from the screen data does not find the pet");
        helper.assertTrue(menu.slots.size() == 27 + 36, "the pet menu has " + menu.slots.size() + " slots");
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.SHEARS));
        pet.mobInteract(player, InteractionHand.MAIN_HAND);
        helper.assertFalse(pet.hasBackpack(), "sneak + shears did not take the backpack off");
        int spilled = helper.getLevel().getEntitiesOfClass(ItemEntity.class, pet.getBoundingBox().inflate(4)).size();
        helper.assertTrue(spilled >= 3, "the backpack spilled " + spilled + " item entities");
        player.setShiftKeyDown(false);
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(ModItems.TAMA_PAGER));
        pet.mobInteract(player, InteractionHand.MAIN_HAND);
        helper.assertTrue(pet.isOrderedToSit(), "the pager did not make the pet stay");
        pet.mobInteract(player, InteractionHand.MAIN_HAND);
        helper.assertFalse(pet.isOrderedToSit(), "the pager did not make the pet follow");
        helper.succeed();
    }

    static void kibbleFeedsPet(GameTestHelper helper) {
        ServerPlayer player = helper.makeMockServerPlayerInLevel();
        TamaPet pet = tamedPet(helper, player, PetSpecies.FROST_PENGUIN);
        pet.needs().add(PetNeeds.Need.HUNGER, -60);
        float before = pet.needs().get(PetNeeds.Need.HUNGER);
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(ModItems.PET_KIBBLE, 2));
        pet.mobInteract(player, InteractionHand.MAIN_HAND);
        float after = pet.needs().get(PetNeeds.Need.HUNGER);
        helper.assertTrue(after > before + 20, "kibble did not feed the pet: " + before + " -> " + after);
        helper.succeed();
    }

    static void snacksForHurtOwner(GameTestHelper helper) {
        ServerPlayer player = helper.makeMockServerPlayerInLevel();
        TamaPet pet = tamedPet(helper, player, PetSpecies.PEBBLE_GOLEM);
        player.setGameMode(net.minecraft.world.level.GameType.SURVIVAL);
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.GOLDEN_APPLE, 2));
        pet.mobInteract(player, InteractionHand.MAIN_HAND);
        helper.assertTrue(pet.snacks() == 0 && player.getMainHandItem().getCount() == 2, "golden apple taken without a backpack");
        pet.equipBackpack();
        pet.mobInteract(player, InteractionHand.MAIN_HAND);
        pet.mobInteract(player, InteractionHand.MAIN_HAND);
        helper.assertTrue(pet.snacks() == 2, "golden apples did not go into the backpack: " + pet.snacks());
        player.setHealth(4F);
        helper.succeedWhen(() -> helper.assertTrue(pet.snacks() == 1, "the hurt owner got no golden apple"));
    }

    static void faintsIntoEgg(GameTestHelper helper) {
        ServerPlayer player = helper.makeMockServerPlayerInLevel();
        TamaPet pet = tamedPet(helper, player, PetSpecies.VOID_KITTEN);
        pet.hurtServer(helper.getLevel(), helper.getLevel().damageSources().generic(), 1000F);
        helper.assertFalse(pet.isAlive(), "the pet did not faint");
        AABB box = new AABB(helper.absolutePos(BlockPos.ZERO)).inflate(12);
        int eggs = helper.getLevel().getEntitiesOfClass(ItemEntity.class, box, e -> e.getItem().is(ModItems.TAMA_EGG)).size();
        helper.assertTrue(eggs == 1, "expected one Tama Egg, found " + eggs);
        helper.succeed();
    }
}
