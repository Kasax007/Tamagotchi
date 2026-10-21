package net.kasax.tamagotchi.registry;

import net.fabricmc.fabric.api.menu.v1.ExtendedMenuType;
import net.kasax.tamagotchi.Tamagotchi;
import net.kasax.tamagotchi.menu.PetMenu;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;

public final class ModMenus {
    public static final ExtendedMenuType<PetMenu, PetMenu.Data> PET_MENU = new ExtendedMenuType<>(PetMenu::new, PetMenu.Data.CODEC);

    private ModMenus() {
    }

    public static void initialize() {
        Registry.register(BuiltInRegistries.MENU, Tamagotchi.id("pet"), PET_MENU);
    }
}
