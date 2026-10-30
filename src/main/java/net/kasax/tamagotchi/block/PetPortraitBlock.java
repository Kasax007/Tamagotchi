package net.kasax.tamagotchi.block;

import java.util.Comparator;
import java.util.List;
import java.util.Map;
import net.kasax.tamagotchi.pet.TamaPet;
import net.kasax.tamagotchi.registry.ModParticles;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.DyeColor;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.EnumProperty;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;
import org.jspecify.annotations.Nullable;

/**
 * A framed portrait for the wall. Click it with an empty hand and it paints your nearest pet (click again for the
 * next one); click it with a dye to change the backdrop.
 */
public class PetPortraitBlock extends BaseEntityBlock {
    public static final EnumProperty<Direction> FACING = HorizontalDirectionalBlock.FACING;
    private static final Map<Direction, VoxelShape> SHAPES = Shapes.rotateHorizontal(Block.box(0, 0, 14, 16, 16, 16));

    public PetPortraitBlock(Properties properties) {
        super(properties);
        registerDefaultState(this.stateDefinition.any().setValue(FACING, Direction.NORTH).setValue(Dyeing.BACKDROP, DyeColor.PINK));
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(FACING, Dyeing.BACKDROP);
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext ctx) {
        Direction face = ctx.getClickedFace();
        return defaultBlockState().setValue(FACING, face.getAxis().isHorizontal() ? face : ctx.getHorizontalDirection().getOpposite());
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return SHAPES.get(state.getValue(FACING));
    }

    @Override
    protected RenderShape getRenderShape(BlockState state) {
        return RenderShape.MODEL;
    }

    @Override
    public @Nullable BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new PetPortraitBlockEntity(pos, state);
    }

    @Override
    protected InteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos, Player player, InteractionHand hand, BlockHitResult hit) {
        return Dyeing.apply(stack, state, level, pos, player, Dyeing.BACKDROP);
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (!(level instanceof ServerLevel server) || !(level.getBlockEntity(pos) instanceof PetPortraitBlockEntity be)) {
            return InteractionResult.SUCCESS;
        }
        List<TamaPet> mine = server.getEntitiesOfClass(TamaPet.class, new AABB(pos).inflate(24, 12, 24),
                p -> p.isAlive() && p.isTame() && p.isOwnedBy(player));
        if (mine.isEmpty()) {
            player.sendOverlayMessage(Component.translatable("message.tamagotchi.portrait_none"));
            return InteractionResult.SUCCESS;
        }
        mine.sort(Comparator.comparingDouble(p -> p.distanceToSqr(net.minecraft.world.phys.Vec3.atCenterOf(pos))));
        TamaPet pick = mine.get(0);
        if (pick.getUUID().equals(be.petId()) && mine.size() > 1) {
            pick = mine.get(1);
        }
        be.paint(pick);
        server.playSound(null, pos, SoundEvents.UI_CARTOGRAPHY_TABLE_TAKE_RESULT, SoundSource.BLOCKS, 0.8F, 1.2F);
        server.sendParticles(ModParticles.HEART, pos.getX() + 0.5, pos.getY() + 0.9, pos.getZ() + 0.5, 3, 0.25, 0.1, 0.25, 0);
        player.sendOverlayMessage(Component.translatable("message.tamagotchi.portrait", pick.getName()));
        return InteractionResult.SUCCESS;
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
