package net.kasax.tamagotchi.compat;

import me.shedaniel.rei.api.client.plugins.REIClientPlugin;
import me.shedaniel.rei.api.client.registry.display.DisplayRegistry;
import me.shedaniel.rei.api.client.view.ViewSearchBuilder;
import me.shedaniel.rei.api.common.util.EntryStacks;
import me.shedaniel.rei.plugin.common.displays.DefaultInformationDisplay;
import net.minecraft.world.item.ItemStack;

/** REI plugin (loaded only when REI is installed): information pages. All recipes are vanilla crafting recipes. */
public class ReiCompat implements REIClientPlugin {
    @Override
    public void registerDisplays(DisplayRegistry registry) {
        CompatInfo.pages().forEach((stack, text) ->
                registry.add(DefaultInformationDisplay.createFromEntry(EntryStacks.of(stack), stack.getHoverName()).line(text)));
    }

    /** Opens REI's recipe view for an item (used by the screenshot test). */
    public static void showRecipes(ItemStack stack) {
        ViewSearchBuilder.builder().addRecipesFor(EntryStacks.of(stack)).open();
    }
}
