package net.kasax.tamacraft.item;

import net.kasax.tamacraft.pet.PetAction;
import net.kasax.tamacraft.pet.PetNeeds;
import net.kasax.tamacraft.pet.TamaPet;
import net.kasax.tamacraft.registry.ModSounds;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

/** Wave it: every pet of yours nearby jumps and swipes at the feathers. */
public class FeatherWandItem extends TooltipItem {
    public FeatherWandItem(Item.Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        level.playSound(null, player.blockPosition(), ModSounds.TOY_FEATHER, SoundSource.PLAYERS, 0.8F, 0.9F + level.getRandom().nextFloat() * 0.3F);
        if (!level.isClientSide()) {
            for (TamaPet pet : level.getEntitiesOfClass(TamaPet.class, player.getBoundingBox().inflate(7), p -> p.isOwnedBy(player))) {
                if (pet.isSleeping() || pet.getTarget() != null) {
                    continue;
                }
                pet.getLookControl().setLookAt(player);
                pet.playAction(pet.getRandom().nextBoolean() ? PetAction.POUNCE : PetAction.PLAY);
                if (pet.onGround()) {
                    pet.setDeltaMovement(pet.getDeltaMovement().add(0, 0.32, 0));
                }
                pet.needs().add(PetNeeds.Need.FUN, 5);
                pet.needs().add(PetNeeds.Need.ENERGY, -0.5F);
            }
            player.getCooldowns().addCooldown(this, 16);
        }
        return InteractionResultHolder.sidedSuccess(player.getItemInHand(hand), level.isClientSide());
    }
}
