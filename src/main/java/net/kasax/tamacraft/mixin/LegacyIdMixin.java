package net.kasax.tamacraft.mixin;

import net.kasax.tamacraft.LegacyIds;
import net.kasax.tamacraft.Tamacraft;
import net.minecraft.resources.ResourceLocation;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * Old worlds keep working after the rename: an id in the old namespace {@code tamagotchi} becomes the same id in
 * {@code tamacraft} as soon as it is parsed or built (see {@link LegacyIds}). These three factories are where every
 * id from text, NBT, JSON, codecs and the network is made.
 */
@Mixin(ResourceLocation.class)
public abstract class LegacyIdMixin {
    @Inject(method = "createUntrusted", at = @At("HEAD"), cancellable = true)
    private static void tamacraft$oldId(String namespace, String path, CallbackInfoReturnable<ResourceLocation> cir) {
        if (LegacyIds.isOld(namespace)) {
            LegacyIds.used(namespace, path);
            cir.setReturnValue(ResourceLocation.fromNamespaceAndPath(Tamacraft.MOD_ID, LegacyIds.path(path)));
        }
    }

    @Inject(method = "tryBuild", at = @At("HEAD"), cancellable = true)
    private static void tamacraft$oldIdTry(String namespace, String path, CallbackInfoReturnable<ResourceLocation> cir) {
        if (LegacyIds.isOld(namespace)) {
            LegacyIds.used(namespace, path);
            cir.setReturnValue(ResourceLocation.tryBuild(Tamacraft.MOD_ID, LegacyIds.path(path)));
        }
    }

    @Inject(method = "tryBySeparator", at = @At("HEAD"), cancellable = true)
    private static void tamacraft$oldIdParse(String identifier, char separator, CallbackInfoReturnable<ResourceLocation> cir) {
        int at = identifier.indexOf(separator);
        if (at == LegacyIds.OLD_NAMESPACE.length() && identifier.startsWith(LegacyIds.OLD_NAMESPACE)) {
            String path = identifier.substring(at + 1);
            LegacyIds.used(LegacyIds.OLD_NAMESPACE, path);
            cir.setReturnValue(ResourceLocation.tryBuild(Tamacraft.MOD_ID, LegacyIds.path(path)));
        }
    }
}
