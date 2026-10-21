package net.kasax.tamagotchi.block;

import net.minecraft.core.BlockPos;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/** Pet bed, basket and dragon nest: pets sleep here at night and when they are tired. */
public class PetBedBlock extends Block {
    private final VoxelShape shape;

    public PetBedBlock(Properties properties) {
        this(properties, Block.box(1, 0, 1, 15, 6, 15));
    }

    public PetBedBlock(Properties properties, VoxelShape shape) {
        super(properties);
        this.shape = shape;
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return this.shape;
    }
}
