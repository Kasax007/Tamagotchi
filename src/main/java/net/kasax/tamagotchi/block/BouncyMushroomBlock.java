package net.kasax.tamagotchi.block;

import net.kasax.tamagotchi.registry.ModSounds;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/** A springy mushroom cap: pets (and players) bounce on it with a boing. */
public class BouncyMushroomBlock extends Block {
    public static final BooleanProperty SQUISHED = BooleanProperty.create("squished");
    private static final VoxelShape SHAPE = Block.box(0, 0, 0, 16, 10, 16);
    private static final VoxelShape SQUISHED_SHAPE = Block.box(0, 0, 0, 16, 8, 16);

    public BouncyMushroomBlock(Properties properties) {
        super(properties);
        registerDefaultState(this.stateDefinition.any().setValue(SQUISHED, false));
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(SQUISHED);
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return state.getValue(SQUISHED) ? SQUISHED_SHAPE : SHAPE;
    }

    @Override
    public void fallOn(Level level, BlockState state, BlockPos pos, Entity entity, double fallDistance) {
        // soft landing, no fall damage
    }

    @Override
    public void bounceOn(Level level, BlockState state, BlockPos pos, Entity entity, double fallDistance) {
        if (level instanceof ServerLevel server && fallDistance > 0.4) {
            squish(server, pos);
        }
    }

    public static void squish(ServerLevel level, BlockPos pos) {
        BlockState st = level.getBlockState(pos);
        if (st.getBlock() instanceof BouncyMushroomBlock && !st.getValue(SQUISHED)) {
            level.setBlock(pos, st.setValue(SQUISHED, true), Block.UPDATE_CLIENTS);
            level.scheduleTick(pos, st.getBlock(), 4);
            level.playSound(null, pos, ModSounds.BLOCK_BOUNCE, SoundSource.BLOCKS, 0.7F, 0.9F + level.getRandom().nextFloat() * 0.3F);
        }
    }

    @Override
    protected void tick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
        if (state.getValue(SQUISHED)) {
            level.setBlock(pos, state.setValue(SQUISHED, false), Block.UPDATE_CLIENTS);
        }
    }
}
