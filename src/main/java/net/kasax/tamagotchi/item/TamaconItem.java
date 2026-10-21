package net.kasax.tamagotchi.item;

import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.Level;

/** The Tamacon: the in-game guide to pets, care, items and furniture. Opens a client screen. */
public class TamaconItem extends TooltipItem {
    /** Set by the client entry point; the server never opens anything. */
    public static Runnable openScreen = () -> {
    };

    public TamaconItem(Item.Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResult use(Level level, Player player, InteractionHand hand) {
        if (level.isClientSide()) {
            openScreen.run();
        } else {
            level.playSound(null, player.blockPosition(), SoundEvents.BOOK_PAGE_TURN, player.getSoundSource(), 1.0F, 1.2F);
        }
        return InteractionResult.SUCCESS;
    }
}
