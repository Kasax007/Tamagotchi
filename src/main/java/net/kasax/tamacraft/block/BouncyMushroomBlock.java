package net.kasax.tamacraft.block;

import net.kasax.tamacraft.registry.ModSounds;
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
import net.minecraft.world.phys.Vec3;
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
    public void fallOn(Level level, BlockState state, BlockPos pos, Entity entity, float fallDistance) {
        // soft landing, no fall damage; a real fall squishes the cap
        if (entity.isSuppressingBounce()) {
            super.fallOn(level, state, pos, entity, fallDistance);
        } else if (level instanceof ServerLevel server && fallDistance > 0.4) {
            squish(server, pos);
        }
    }

    @Override
    public void updateEntityAfterFallOn(BlockGetter level, Entity entity) {
        // springy: everyone bounces back up with most of their speed (sneaking players do not)
        Vec3 v = entity.getDeltaMovement();
        if (entity.isSuppressingBounce() || v.y >= 0.0) {
            super.updateEntityAfterFallOn(level, entity);
        } else {
            entity.setDeltaMovement(v.x, -v.y * 0.9, v.z);
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
