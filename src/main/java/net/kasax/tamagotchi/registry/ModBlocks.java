package net.kasax.tamagotchi.registry;

import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.function.Function;
import net.fabricmc.fabric.api.object.builder.v1.block.entity.FabricBlockEntityTypeBuilder;
import net.kasax.tamagotchi.Tamagotchi;
import net.kasax.tamagotchi.block.BouncyMushroomBlock;
import net.kasax.tamagotchi.block.DyeablePetBedBlock;
import net.kasax.tamagotchi.block.EggLampBlock;
import net.kasax.tamagotchi.block.FoodBowlBlock;
import net.kasax.tamagotchi.block.PetBasketBlock;
import net.kasax.tamagotchi.block.PetBathBlock;
import net.kasax.tamagotchi.block.PetBedBlock;
import net.kasax.tamagotchi.block.PetFlapBlock;
import net.kasax.tamagotchi.block.PetHouseBlock;
import net.kasax.tamagotchi.block.PetIncubatorBlock;
import net.kasax.tamagotchi.block.PetIncubatorBlockEntity;
import net.kasax.tamagotchi.block.PetPortraitBlock;
import net.kasax.tamagotchi.block.PetPortraitBlockEntity;
import net.kasax.tamagotchi.block.PlushBlock;
import net.kasax.tamagotchi.block.PlushBlockEntity;
import net.kasax.tamagotchi.block.RunningWheelBlock;
import net.kasax.tamagotchi.block.RunningWheelBlockEntity;
import net.kasax.tamagotchi.block.ScratchingPostBlock;
import net.kasax.tamagotchi.block.ToyBoxBlock;
import net.kasax.tamagotchi.block.ToyBoxBlockEntity;
import net.kasax.tamagotchi.block.TreatDispenserBlock;
import net.kasax.tamagotchi.block.TreatDispenserBlockEntity;
import net.kasax.tamagotchi.pet.PetSpecies;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.MapColor;
import net.minecraft.world.level.material.PushReaction;

/** Pet furniture: beds, bowl, bath, playground, house, decoration, plushies and pet gadgets. */
public final class ModBlocks {
    public static final List<Item> BLOCK_ITEMS = new ArrayList<>();

    public static final Block PET_BED = reg("pet_bed", DyeablePetBedBlock::new,
            BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_RED).strength(0.4F).sound(SoundType.WOOL).noOcclusion());
    public static final Block PET_BASKET = reg("pet_basket", PetBasketBlock::new,
            BlockBehaviour.Properties.of().mapColor(MapColor.WOOD).strength(0.5F).sound(SoundType.BAMBOO_WOOD).noOcclusion());
    public static final Block DRAGON_NEST = reg("dragon_nest", p -> new PetBedBlock(p, Block.box(0, 0, 0, 16, 6, 16)),
            BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_YELLOW).strength(0.4F).sound(SoundType.GRASS).noOcclusion());
    public static final Block FOOD_BOWL = reg("food_bowl", FoodBowlBlock::new,
            BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_LIGHT_BLUE).strength(0.5F).sound(SoundType.DECORATED_POT).noOcclusion());
    public static final Block PET_BATH = reg("pet_bath", PetBathBlock::new,
            BlockBehaviour.Properties.of().mapColor(MapColor.WOOD).strength(1.0F).sound(SoundType.WOOD).noOcclusion());
    public static final Block BOUNCY_MUSHROOM = reg("bouncy_mushroom", BouncyMushroomBlock::new,
            BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_RED).strength(0.6F).sound(SoundType.SLIME_BLOCK)
                    .bounceRestitution(0.9F).noOcclusion());
    public static final Block RUNNING_WHEEL = reg("running_wheel", RunningWheelBlock::new,
            BlockBehaviour.Properties.of().mapColor(MapColor.WOOD).strength(1.0F).sound(SoundType.WOOD).noOcclusion());
    public static final Block SCRATCHING_POST = reg("scratching_post", ScratchingPostBlock::new,
            BlockBehaviour.Properties.of().mapColor(MapColor.WOOL).strength(0.8F).sound(SoundType.WOOL).noOcclusion());
    public static final Block PET_HOUSE = reg("pet_house", PetHouseBlock::new,
            BlockBehaviour.Properties.of().mapColor(MapColor.WOOD).strength(1.5F).sound(SoundType.WOOD).noOcclusion());

    public static final Block EGG_LAMP = reg("egg_lamp", EggLampBlock::new,
            BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_PINK).strength(0.3F).sound(SoundType.DECORATED_POT)
                    .lightLevel(st -> st.getValue(EggLampBlock.LIT) ? 14 : 0).noOcclusion());
    public static final Block PET_PORTRAIT = reg("pet_portrait", PetPortraitBlock::new,
            BlockBehaviour.Properties.of().mapColor(MapColor.WOOD).strength(0.5F).sound(SoundType.WOOD).noOcclusion());
    public static final Block TOY_BOX = reg("toy_box", ToyBoxBlock::new,
            BlockBehaviour.Properties.of().mapColor(MapColor.WOOD).strength(1.5F).sound(SoundType.WOOD).noOcclusion());
    public static final Block PET_FLAP = reg("pet_flap", PetFlapBlock::new,
            BlockBehaviour.Properties.of().mapColor(MapColor.WOOD).strength(1.0F).sound(SoundType.WOOD).noOcclusion());
    public static final Block TREAT_DISPENSER = reg("treat_dispenser", TreatDispenserBlock::new,
            BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_RED).strength(1.5F).sound(SoundType.COPPER).noOcclusion());
    public static final Block PET_INCUBATOR = reg("pet_incubator", PetIncubatorBlock::new,
            BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_ORANGE).strength(1.0F).sound(SoundType.COPPER)
                    .lightLevel(st -> st.getValue(PetIncubatorBlock.LIT) ? 9 : 0).noOcclusion());
    /** One plush toy per pet, e.g. tamagotchi:desert_dragon_plush. */
    public static final Map<PetSpecies, Block> PLUSHES = new EnumMap<>(PetSpecies.class);

    static {
        for (PetSpecies s : PetSpecies.values()) {
            PLUSHES.put(s, reg(s.id() + "_plush", p -> new PlushBlock(s, p),
                    BlockBehaviour.Properties.of().mapColor(MapColor.WOOL).strength(0.4F).sound(SoundType.WOOL)
                            .pushReaction(PushReaction.POPPED).noOcclusion()));
        }
    }

    public static final BlockEntityType<RunningWheelBlockEntity> RUNNING_WHEEL_BE =
            FabricBlockEntityTypeBuilder.create(RunningWheelBlockEntity::new, RUNNING_WHEEL).build();
    public static final BlockEntityType<PetPortraitBlockEntity> PET_PORTRAIT_BE =
            FabricBlockEntityTypeBuilder.create(PetPortraitBlockEntity::new, PET_PORTRAIT).build();
    public static final BlockEntityType<ToyBoxBlockEntity> TOY_BOX_BE =
            FabricBlockEntityTypeBuilder.create(ToyBoxBlockEntity::new, TOY_BOX).build();
    public static final BlockEntityType<TreatDispenserBlockEntity> TREAT_DISPENSER_BE =
            FabricBlockEntityTypeBuilder.create(TreatDispenserBlockEntity::new, TREAT_DISPENSER).build();
    public static final BlockEntityType<PetIncubatorBlockEntity> PET_INCUBATOR_BE =
            FabricBlockEntityTypeBuilder.create(PetIncubatorBlockEntity::new, PET_INCUBATOR).build();
    public static final BlockEntityType<PlushBlockEntity> PLUSH_BE =
            FabricBlockEntityTypeBuilder.create(PlushBlockEntity::new, PLUSHES.values().toArray(Block[]::new)).build();

    private ModBlocks() {
    }

    private static Block reg(String name, Function<BlockBehaviour.Properties, Block> factory, BlockBehaviour.Properties props) {
        ResourceKey<Block> key = ResourceKey.create(Registries.BLOCK, Tamagotchi.id(name));
        Block block = factory.apply(props.setId(key));
        Registry.register(BuiltInRegistries.BLOCK, key, block);
        ResourceKey<Item> itemKey = ResourceKey.create(Registries.ITEM, Tamagotchi.id(name));
        Item item = new BlockItem(block, new Item.Properties().setId(itemKey).useBlockDescriptionPrefix());
        Registry.register(BuiltInRegistries.ITEM, itemKey, item);
        BLOCK_ITEMS.add(item);
        return block;
    }

    public static void initialize() {
        Registry.register(BuiltInRegistries.BLOCK_ENTITY_TYPE, Tamagotchi.id("running_wheel"), RUNNING_WHEEL_BE);
        Registry.register(BuiltInRegistries.BLOCK_ENTITY_TYPE, Tamagotchi.id("pet_portrait"), PET_PORTRAIT_BE);
        Registry.register(BuiltInRegistries.BLOCK_ENTITY_TYPE, Tamagotchi.id("toy_box"), TOY_BOX_BE);
        Registry.register(BuiltInRegistries.BLOCK_ENTITY_TYPE, Tamagotchi.id("treat_dispenser"), TREAT_DISPENSER_BE);
        Registry.register(BuiltInRegistries.BLOCK_ENTITY_TYPE, Tamagotchi.id("pet_incubator"), PET_INCUBATOR_BE);
        Registry.register(BuiltInRegistries.BLOCK_ENTITY_TYPE, Tamagotchi.id("plush"), PLUSH_BE);
    }
}
