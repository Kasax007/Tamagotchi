package net.kasax.tamagotchi.block;

import net.kasax.tamagotchi.pet.PetSpecies;
import net.kasax.tamagotchi.registry.ModParticles;
import net.kasax.tamagotchi.registry.ModSounds;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.level.block.state.properties.RotationSegment;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;
import org.jspecify.annotations.Nullable;

/**
 * A plush toy of one of the pets (drawn by PlushRenderer from the pet's own model). Squeeze it with a click; a pet
 * that sleeps next to a plush of its own kind rests faster, and lonely pets come and cuddle it.
 */
public class PlushBlock extends BaseEntityBlock {
    public static final IntegerProperty ROTATION = BlockStateProperties.ROTATION_16;
    private static final VoxelShape SHAPE = Block.box(4, 0, 4, 12, 10, 12);
    private final PetSpecies species;

    public PlushBlock(PetSpecies species, Properties properties) {
        super(properties);
        this.species = species;
        registerDefaultState(this.stateDefinition.any().setValue(ROTATION, 0));
    }

    public PetSpecies species() {
        return this.species;
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(ROTATION);
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext ctx) {
        return defaultBlockState().setValue(ROTATION, RotationSegment.convertToSegment(ctx.getRotation() + 180));
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return SHAPE;
    }

    @Override
    protected RenderShape getRenderShape(BlockState state) {
        return RenderShape.INVISIBLE;
    }

    @Override
    public @Nullable BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new PlushBlockEntity(pos, state);
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (level instanceof ServerLevel server) {
            squeeze(server, pos);
        }
        return InteractionResult.SUCCESS;
    }

    /** Squeak, squish and a heart; used by players and by cuddling pets. */
    public static void squeeze(ServerLevel level, BlockPos pos) {
        level.blockEvent(pos, level.getBlockState(pos).getBlock(), PlushBlockEntity.EVENT_SQUISH, 0);
        level.playSound(null, pos, ModSounds.TOY_SQUEAK, SoundSource.BLOCKS, 0.7F, 1.1F + level.getRandom().nextFloat() * 0.3F);
        level.sendParticles(ModParticles.HEART, pos.getX() + 0.5, pos.getY() + 0.8, pos.getZ() + 0.5, 1, 0.1, 0.05, 0.1, 0);
    }

    @Override
    protected BlockState rotate(BlockState state, Rotation rotation) {
        return state.setValue(ROTATION, rotation.rotate(state.getValue(ROTATION), 16));
    }

    @Override
    protected BlockState mirror(BlockState state, Mirror mirror) {
        return state.setValue(ROTATION, mirror.mirror(state.getValue(ROTATION), 16));
    }
}
