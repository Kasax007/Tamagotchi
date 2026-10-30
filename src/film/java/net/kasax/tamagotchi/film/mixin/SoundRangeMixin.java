package net.kasax.tamagotchi.film.mixin;

import net.kasax.tamagotchi.film.FilmClock;
import net.minecraft.server.players.PlayerList;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.ModifyVariable;

/**
 * While a scene is filmed, every sound reaches the film player however far away it plays. The free camera is a
 * client-only stand, so the player's body is often more than the usual 16 blocks from what is filmed, and the server
 * never sent those sounds; the video tools work out the real loudness from where the camera was ({@code FilmSound}).
 */
@Mixin(PlayerList.class)
public class SoundRangeMixin {
    @ModifyVariable(method = "broadcast", at = @At("HEAD"), argsOnly = true, ordinal = 3)
    private double film$everywhere(double range) {
        return FilmClock.gated() ? Math.max(range, 512) : range;
    }
}
