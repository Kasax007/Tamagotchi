package net.kasax.tamagotchi.item;

import net.kasax.tamagotchi.registry.ModSounds;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

/** Throw it - your pets fetch it and bring it back. */
public class SqueakyBallItem extends TooltipItem {
    public SqueakyBallItem(Item.Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResult use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        level.playSound(null, player.blockPosition(), ModSounds.TOY_SQUEAK, SoundSource.PLAYERS, 0.8F, 1.1F);
        if (level instanceof ServerLevel server) {
            Vec3 eye = player.getEyePosition();
            ItemEntity ball = new ItemEntity(server, eye.x, eye.y - 0.2, eye.z, stack.copyWithCount(1));
            Vec3 v = player.getViewVector(1.0F).scale(0.9).add(0, 0.18, 0);
            ball.setDeltaMovement(v);
            ball.setPickUpDelay(30);
            ball.setThrower(player);
            server.addFreshEntity(ball);
            stack.consume(1, player);
            player.getCooldowns().addCooldown(stack, 10);
        }
        return InteractionResult.SUCCESS;
    }
}
