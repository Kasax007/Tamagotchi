package net.kasax.tamacraft.registry;

import net.fabricmc.fabric.api.menu.v1.ExtendedMenuType;
import net.kasax.tamacraft.Tamacraft;
import net.kasax.tamacraft.menu.PetMenu;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;

public final class ModMenus {
    public static final ExtendedMenuType<PetMenu, PetMenu.Data> PET_MENU = new ExtendedMenuType<>(PetMenu::new, PetMenu.Data.CODEC);

    private ModMenus() {
    }

    public static void initialize() {
        Registry.register(BuiltInRegistries.MENU, Tamacraft.id("pet"), PET_MENU);
    }
}
