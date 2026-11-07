package net.kasax.tamagotchi.test.mixin;

import net.minecraft.client.KeyboardHandler;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.gen.Invoker;

/** Typed characters for the tests, as GLFW's char callback delivers them. */
@Mixin(KeyboardHandler.class)
public interface KeyboardHandlerAccessor {
    @Invoker("charTyped")
    void tamatest$charTyped(long window, int codepoint, int mods);
}
