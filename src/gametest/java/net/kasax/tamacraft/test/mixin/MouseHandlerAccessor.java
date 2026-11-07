package net.kasax.tamacraft.test.mixin;

import net.minecraft.client.MouseHandler;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.gen.Invoker;

/** Real mouse input for the tests: the same calls GLFW's callbacks make. */
@Mixin(MouseHandler.class)
public interface MouseHandlerAccessor {
    @Invoker("onMove")
    void tamatest$onMove(long window, double x, double y);

    @Invoker("onPress")
    void tamatest$onPress(long window, int button, int action, int mods);
}
