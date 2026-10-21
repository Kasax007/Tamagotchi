package net.kasax.tamagotchi.registry;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Function;
import net.fabricmc.fabric.api.object.builder.v1.block.entity.FabricBlockEntityTypeBuilder;
import net.kasax.tamagotchi.Tamagotchi;
import net.kasax.tamagotchi.block.BouncyMushroomBlock;
import net.kasax.tamagotchi.block.FoodBowlBlock;
import net.kasax.tamagotchi.block.PetBasketBlock;
import net.kasax.tamagotchi.block.PetBathBlock;
import net.kasax.tamagotchi.block.PetBedBlock;
import net.kasax.tamagotchi.block.PetHouseBlock;
import net.kasax.tamagotchi.block.RunningWheelBlock;
import net.kasax.tamagotchi.block.RunningWheelBlockEntity;
import net.kasax.tamagotchi.block.ScratchingPostBlock;
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

/** Pet furniture: beds, bowl, bath, playground and house. */
public final class ModBlocks {
    public static final List<Item> BLOCK_ITEMS = new ArrayList<>();

    public static final Block PET_BED = reg("pet_bed", PetBedBlock::new,
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

    public static final BlockEntityType<RunningWheelBlockEntity> RUNNING_WHEEL_BE =
            FabricBlockEntityTypeBuilder.create(RunningWheelBlockEntity::new, RUNNING_WHEEL).build();

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
    }
}
