package net.kasax.tamagotchi.item;

import net.kasax.tamagotchi.pet.PetAction;
import net.kasax.tamagotchi.pet.PetNeeds;
import net.kasax.tamagotchi.pet.TamaPet;
import net.kasax.tamagotchi.registry.ModSounds;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.Level;

/** Wave it: every pet of yours nearby jumps and swipes at the feathers. */
public class FeatherWandItem extends TooltipItem {
    public FeatherWandItem(Item.Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResult use(Level level, Player player, InteractionHand hand) {
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
            player.getCooldowns().addCooldown(player.getItemInHand(hand), 16);
        }
        return InteractionResult.SUCCESS;
    }
}
