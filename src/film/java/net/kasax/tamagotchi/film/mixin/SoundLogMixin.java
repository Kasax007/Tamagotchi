package net.kasax.tamagotchi.film.mixin;

import net.kasax.tamagotchi.film.FilmSound;
import net.minecraft.client.resources.sounds.SoundInstance;
import net.minecraft.client.sounds.SoundEngine;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** Every sound the game starts, before the (missing) sound device is even asked: see {@link FilmSound}. */
@Mixin(SoundEngine.class)
public class SoundLogMixin {
    @Inject(method = "play", at = @At("HEAD"))
    private void film$log(SoundInstance instance, CallbackInfoReturnable<SoundEngine.PlayResult> cir) {
        FilmSound.log(instance);
    }
}
