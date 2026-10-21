package net.kasax.tamagotchi.item;

import java.util.Comparator;
import java.util.List;
import net.kasax.tamagotchi.pet.TamaPet;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.Level;

/**
 * The handheld virtual-pet device: right-click your pet (or the air for the nearest one within 64
 * blocks) to open its screen. While carried it beeps when a pet needs care (see {@link TamaPet}).
 */
public class TamaPagerItem extends TooltipItem {
    public TamaPagerItem(Item.Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResult use(Level level, Player player, InteractionHand hand) {
        if (!(player instanceof ServerPlayer sp)) {
            return InteractionResult.SUCCESS;
        }
        List<TamaPet> pets = level.getEntitiesOfClass(TamaPet.class, player.getBoundingBox().inflate(64), p -> p.isOwnedBy(player));
        TamaPet nearest = pets.stream().min(Comparator.comparingDouble(p -> p.distanceToSqr(player))).orElse(null);
        if (nearest == null) {
            sp.sendOverlayMessage(Component.translatable("message.tamagotchi.no_pet"));
            return InteractionResult.FAIL;
        }
        nearest.openPetScreen(sp);
        return InteractionResult.SUCCESS_SERVER;
    }
}
