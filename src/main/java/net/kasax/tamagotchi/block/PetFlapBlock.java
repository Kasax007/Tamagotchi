package net.kasax.tamagotchi.block;

import java.util.Map;
import net.kasax.tamagotchi.pet.TamaPet;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.InsideBlockEffectApplier;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.level.block.state.properties.EnumProperty;
import net.minecraft.world.level.pathfinder.PathComputationType;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.EntityCollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * A pet flap for a one-block hole in a wall: pets walk right through (it swings open), everyone else bumps into it.
 * Other mobs path around it like a wall; pets path through it (see {@link net.kasax.tamagotchi.pet.PetPathing}).
 */
public class PetFlapBlock extends Block {
    public static final EnumProperty<Direction> FACING = HorizontalDirectionalBlock.FACING;
    public static final BooleanProperty OPEN = BlockStateProperties.OPEN;
    private static final Map<Direction, VoxelShape> SHAPES = Shapes.rotateHorizontal(Block.box(0, 0, 7, 16, 16, 9));

    public PetFlapBlock(Properties properties) {
        super(properties);
        registerDefaultState(this.stateDefinition.any().setValue(FACING, Direction.NORTH).setValue(OPEN, false));
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(FACING, OPEN);
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext ctx) {
        return defaultBlockState().setValue(FACING, ctx.getHorizontalDirection().getOpposite());
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return SHAPES.get(state.getValue(FACING));
    }

    @Override
    protected VoxelShape getCollisionShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        if (context instanceof EntityCollisionContext ec && ec.getEntity() instanceof TamaPet) {
            return Shapes.empty();
        }
        return SHAPES.get(state.getValue(FACING));
    }

    @Override
    protected boolean isPathfindable(BlockState state, PathComputationType type) {
        return false;
    }

    @Override
    protected void entityInside(BlockState state, Level level, BlockPos pos, Entity entity, InsideBlockEffectApplier effects, boolean isPrecise) {
        if (!(level instanceof ServerLevel server) || !(entity instanceof TamaPet)) {
            return;
        }
        if (!state.getValue(OPEN)) {
            server.setBlock(pos, state.setValue(OPEN, true), Block.UPDATE_CLIENTS);
            server.playSound(null, pos, SoundEvents.WOODEN_TRAPDOOR_OPEN, SoundSource.BLOCKS, 0.5F, 1.5F);
        }
        server.scheduleTick(pos, this, 12);
    }

    @Override
    protected void tick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
        if (!state.getValue(OPEN)) {
            return;
        }
        if (!level.getEntitiesOfClass(TamaPet.class, new net.minecraft.world.phys.AABB(pos)).isEmpty()) {
            level.scheduleTick(pos, this, 12);
            return;
        }
        level.setBlock(pos, state.setValue(OPEN, false), Block.UPDATE_CLIENTS);
        level.playSound(null, pos, SoundEvents.WOODEN_TRAPDOOR_CLOSE, SoundSource.BLOCKS, 0.5F, 1.6F);
    }

    @Override
    protected BlockState rotate(BlockState state, Rotation rotation) {
        return state.setValue(FACING, rotation.rotate(state.getValue(FACING)));
    }

    @Override
    protected BlockState mirror(BlockState state, Mirror mirror) {
        return state.rotate(mirror.getRotation(state.getValue(FACING)));
    }
}
