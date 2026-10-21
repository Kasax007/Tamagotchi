package net.kasax.tamagotchi.block;

import net.kasax.tamagotchi.registry.ModItems;
import net.kasax.tamagotchi.registry.ModSounds;
import net.minecraft.core.BlockPos;
import net.minecraft.core.component.DataComponents;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/** Fill it with pet food (up to three portions); hungry pets come and eat from it by themselves. */
public class FoodBowlBlock extends Block {
    public static final IntegerProperty FILL = IntegerProperty.create("fill", 0, 3);
    private static final VoxelShape SHAPE = Block.box(3, 0, 3, 13, 5, 13);

    public FoodBowlBlock(Properties properties) {
        super(properties);
        registerDefaultState(this.stateDefinition.any().setValue(FILL, 0));
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(FILL);
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return SHAPE;
    }

    public static boolean isBowlFood(ItemStack stack) {
        return stack.is(ModItems.PET_KIBBLE) || stack.is(ModItems.FISH_CRACKERS) || stack.is(ModItems.DRAGON_FRUIT)
                || stack.is(ModItems.EMBER_JERKY) || stack.is(ModItems.ROCK_CANDY) || stack.is(ModItems.GLOW_GUMMY)
                || stack.is(ModItems.GOLDEN_BISCUIT) || stack.has(DataComponents.FOOD);
    }

    @Override
    protected InteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos, Player player, InteractionHand hand, BlockHitResult hit) {
        if (!isBowlFood(stack)) {
            return InteractionResult.TRY_WITH_EMPTY_HAND;
        }
        int fill = state.getValue(FILL);
        if (fill >= 3) {
            return InteractionResult.PASS;
        }
        if (!level.isClientSide()) {
            int add = stack.is(ModItems.PET_KIBBLE) ? 2 : 1;
            level.setBlockAndUpdate(pos, state.setValue(FILL, Math.min(3, fill + add)));
            stack.consume(1, player);
            level.playSound(null, pos, ModSounds.BLOCK_BOWL_FILL, SoundSource.BLOCKS, 0.8F, 1.0F);
        }
        return InteractionResult.SUCCESS;
    }

    public static void takePortion(ServerLevel level, BlockPos pos, BlockState state) {
        int fill = state.getValue(FILL);
        if (fill > 0) {
            level.setBlockAndUpdate(pos, state.setValue(FILL, fill - 1));
        }
    }

    @Override
    protected boolean hasAnalogOutputSignal(BlockState state) {
        return true;
    }

    @Override
    protected int getAnalogOutputSignal(BlockState state, Level level, BlockPos pos, net.minecraft.core.Direction direction) {
        return state.getValue(FILL) * 5;
    }
}
