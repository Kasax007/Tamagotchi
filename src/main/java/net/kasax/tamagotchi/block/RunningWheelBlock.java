package net.kasax.tamagotchi.block;

import java.util.Map;
import net.kasax.tamagotchi.registry.ModSounds;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.level.block.state.properties.EnumProperty;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;
import org.jspecify.annotations.Nullable;

/**
 * A running wheel. While a pet runs in it the wheel spins (drawn by RunningWheelRenderer) and the
 * block gives a full redstone signal - functional decoration.
 */
public class RunningWheelBlock extends BaseEntityBlock {
    public static final EnumProperty<Direction> FACING = HorizontalDirectionalBlock.FACING;
    public static final BooleanProperty RUNNING = BooleanProperty.create("running");
    private static final Map<Direction, VoxelShape> SHAPES = Shapes.rotateHorizontal(Shapes.or(
            Block.box(1, 0, 1, 15, 1, 15),
            Block.box(2, 1, 14, 14, 14, 16)));

    public RunningWheelBlock(Properties properties) {
        super(properties);
        registerDefaultState(this.stateDefinition.any().setValue(FACING, Direction.NORTH).setValue(RUNNING, false));
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(FACING, RUNNING);
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext ctx) {
        return defaultBlockState().setValue(FACING, ctx.getHorizontalDirection().getOpposite());
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return Block.box(0, 0, 0, 16, 16, 16);
    }

    @Override
    protected VoxelShape getCollisionShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return SHAPES.get(state.getValue(FACING));
    }

    @Override
    protected RenderShape getRenderShape(BlockState state) {
        return RenderShape.MODEL;
    }

    @Override
    public @Nullable BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new RunningWheelBlockEntity(pos, state);
    }

    @Override
    protected boolean isSignalSource(BlockState state) {
        return true;
    }

    @Override
    protected int getSignal(BlockState state, BlockGetter level, BlockPos pos, Direction direction) {
        return state.getValue(RUNNING) ? 15 : 0;
    }

    /** Called every tick by a running pet; the wheel stops by itself shortly after the pet leaves. */
    public static void setRunning(ServerLevel level, BlockPos pos, boolean running) {
        BlockState st = level.getBlockState(pos);
        if (!(st.getBlock() instanceof RunningWheelBlock)) {
            return;
        }
        if (level.getBlockEntity(pos) instanceof RunningWheelBlockEntity be) {
            be.lastRun = running ? level.getGameTime() : 0;
        }
        if (st.getValue(RUNNING) != running) {
            level.setBlock(pos, st.setValue(RUNNING, running), Block.UPDATE_ALL);
            level.updateNeighborsAt(pos, st.getBlock());
            if (running) {
                level.scheduleTick(pos, st.getBlock(), 10);
            }
        }
        if (running && level.getGameTime() % 30 == 0) {
            level.playSound(null, pos, ModSounds.BLOCK_WHEEL, SoundSource.BLOCKS, 0.4F, 1.0F);
        }
    }

    @Override
    protected void tick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
        if (!state.getValue(RUNNING)) {
            return;
        }
        if (level.getBlockEntity(pos) instanceof RunningWheelBlockEntity be && level.getGameTime() - be.lastRun < 10) {
            level.scheduleTick(pos, this, 10);
            return;
        }
        level.setBlock(pos, state.setValue(RUNNING, false), Block.UPDATE_ALL);
        level.updateNeighborsAt(pos, this);
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
