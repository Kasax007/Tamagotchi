package net.kasax.tamacraft.registry;

import net.fabricmc.fabric.api.screenhandler.v1.ExtendedScreenHandlerType;
import net.kasax.tamacraft.Tamacraft;
import net.kasax.tamacraft.menu.PetMenu;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;

public final class ModMenus {
    public static final ExtendedScreenHandlerType<PetMenu, PetMenu.Data> PET_MENU = new ExtendedScreenHandlerType<>(PetMenu::new, PetMenu.Data.CODEC);

    private ModMenus() {
    }

    public static void initialize() {
        Registry.register(BuiltInRegistries.MENU, Tamacraft.id("pet"), PET_MENU);
    }
}
