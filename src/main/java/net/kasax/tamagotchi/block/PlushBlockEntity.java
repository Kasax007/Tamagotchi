package net.kasax.tamagotchi.block;

import net.kasax.tamagotchi.pet.PetSpecies;
import net.kasax.tamagotchi.registry.ModBlocks;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;

/** Only exists so the plush can be drawn (and squished) by its renderer. */
public class PlushBlockEntity extends BlockEntity {
    public static final int EVENT_SQUISH = 1;
    /** Client: game time of the last squeeze. */
    public long squishedAt = Long.MIN_VALUE / 2;

    public PlushBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlocks.PLUSH_BE, pos, state);
    }

    public PetSpecies species() {
        return getBlockState().getBlock() instanceof PlushBlock p ? p.species() : PetSpecies.DESERT_DRAGON;
    }

    @Override
    public boolean triggerEvent(int id, int param) {
        if (id == EVENT_SQUISH) {
            if (this.level != null) {
                this.squishedAt = this.level.getGameTime();
            }
            return true;
        }
        return super.triggerEvent(id, param);
    }
}
