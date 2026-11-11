package net.kasax.tamacraft.registry;

import net.minecraft.world.inventory.MenuType;
import net.neoforged.neoforge.common.extensions.IMenuTypeExtension;
import net.kasax.tamacraft.Tamacraft;
import net.kasax.tamacraft.menu.PetMenu;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;

public final class ModMenus {
    /** The client learns which pet and how many slots from the {@link PetMenu.Data} sent with the menu. */
    public static final MenuType<PetMenu> PET_MENU = IMenuTypeExtension.create((id, inventory, buf) -> new PetMenu(id, inventory, PetMenu.Data.CODEC.decode(buf)));

    private ModMenus() {
    }

    public static void initialize() {
        Registry.register(BuiltInRegistries.MENU, Tamacraft.id("pet"), PET_MENU);
    }
}
