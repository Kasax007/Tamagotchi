package net.kasax.tamagotchi.block;

import net.minecraft.core.BlockPos;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.DyeColor;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.phys.BlockHitResult;

/** The pet bed; dye it any of the sixteen colours. */
public class DyeablePetBedBlock extends PetBedBlock {
    public DyeablePetBedBlock(Properties properties) {
        super(properties);
        registerDefaultState(this.stateDefinition.any().setValue(Dyeing.COLOR, DyeColor.RED));
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(Dyeing.COLOR);
    }

    @Override
    protected InteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos, Player player, InteractionHand hand, BlockHitResult hit) {
        return Dyeing.apply(stack, state, level, pos, player, Dyeing.COLOR);
    }
}
