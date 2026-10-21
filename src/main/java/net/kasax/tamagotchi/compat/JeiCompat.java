package net.kasax.tamagotchi.compat;

import mezz.jei.api.IModPlugin;
import mezz.jei.api.JeiPlugin;
import mezz.jei.api.constants.VanillaTypes;
import mezz.jei.api.recipe.RecipeIngredientRole;
import mezz.jei.api.registration.IRecipeRegistration;
import mezz.jei.api.runtime.IJeiRuntime;
import net.kasax.tamagotchi.Tamagotchi;
import net.minecraft.resources.Identifier;
import net.minecraft.world.item.ItemStack;

/** JEI plugin (loaded only when JEI is installed): information pages. All recipes are vanilla crafting recipes. */
@JeiPlugin
public class JeiCompat implements IModPlugin {
    private static IJeiRuntime runtime;

    @Override
    public Identifier getPluginUid() {
        return Tamagotchi.id("jei");
    }

    @Override
    public void registerRecipes(IRecipeRegistration registration) {
        CompatInfo.pages().forEach((stack, text) -> registration.addItemStackInfo(stack, text));
    }

    @Override
    public void onRuntimeAvailable(IJeiRuntime jeiRuntime) {
        runtime = jeiRuntime;
    }

    /** Opens JEI's recipe view for an item (used by the screenshot test). */
    public static void showRecipes(ItemStack stack) {
        if (runtime != null) {
            runtime.getRecipesGui().show(runtime.getJeiHelpers().getFocusFactory().createFocus(RecipeIngredientRole.OUTPUT, VanillaTypes.ITEM_STACK, stack));
        }
    }
}
