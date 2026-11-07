package net.kasax.tamagotchi.test.mixin;

import net.minecraft.client.gui.screens.inventory.CreativeModeInventoryScreen;
import net.minecraft.world.item.CreativeModeTab;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.gen.Invoker;

/** Opens a creative tab directly (26.x: CreativeModeInventoryScreen.setSelectedTab is public). */
@Mixin(CreativeModeInventoryScreen.class)
public interface CreativeScreenAccessor {
    @Invoker("selectTab")
    void tamatest$selectTab(CreativeModeTab tab);
}
