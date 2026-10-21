package net.kasax.tamagotchi.item;

import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import net.kasax.tamagotchi.registry.ModParticles;
import net.kasax.tamagotchi.registry.ModSounds;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.ItemUseAnimation;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/** Hold right-click: a red dot appears where you point, and your pets chase and pounce on it. */
public class LaserPointerItem extends TooltipItem {
    private record Dot(Vec3 pos, long time, ResourceKey<Level> dimension) {
    }

    private static final Map<UUID, Dot> DOTS = new ConcurrentHashMap<>();

    public LaserPointerItem(Item.Properties properties) {
        super(properties);
    }

    /** The owner's laser dot if it was updated in the last few ticks. */
    public static @Nullable Vec3 activeDot(Level level, UUID owner) {
        Dot d = DOTS.get(owner);
        if (d == null || d.dimension != level.dimension() || level.getGameTime() - d.time > 4) {
            return null;
        }
        return d.pos;
    }

    @Override
    public InteractionResult use(Level level, Player player, InteractionHand hand) {
        player.startUsingItem(hand);
        // one click when the laser switches on, no repeats while it is held
        level.playSound(null, player.blockPosition(), ModSounds.TOY_LASER, SoundSource.PLAYERS, 0.3F, 1.0F);
        return InteractionResult.CONSUME;
    }

    @Override
    public int getUseDuration(ItemStack stack, LivingEntity user) {
        return 72000;
    }

    @Override
    public ItemUseAnimation getUseAnimation(ItemStack stack) {
        return ItemUseAnimation.NONE;
    }

    @Override
    public void onUseTick(Level level, LivingEntity user, ItemStack stack, int ticksRemaining) {
        if (!(level instanceof ServerLevel server)) {
            return;
        }
        Vec3 eye = user.getEyePosition();
        Vec3 end = eye.add(user.getViewVector(1.0F).scale(32));
        BlockHitResult hit = level.clip(new ClipContext(eye, end, ClipContext.Block.OUTLINE, ClipContext.Fluid.NONE, user));
        if (hit.getType() != HitResult.Type.BLOCK) {
            DOTS.remove(user.getUUID());
            return;
        }
        Vec3 p = hit.getLocation().add(Vec3.atLowerCornerOf(hit.getDirection().getUnitVec3i()).scale(0.04));
        DOTS.put(user.getUUID(), new Dot(p, level.getGameTime(), level.dimension()));
        server.sendParticles(ModParticles.LASER_DOT, p.x, p.y, p.z, 1, 0, 0, 0, 0);
    }

    @Override
    public boolean releaseUsing(ItemStack stack, Level level, LivingEntity entity, int remainingTime) {
        DOTS.remove(entity.getUUID());
        return true;
    }
}
