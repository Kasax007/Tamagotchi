package net.kasax.tamagotchi.compat;

import java.util.LinkedHashMap;
import java.util.Map;
import net.kasax.tamagotchi.pet.PetSpecies;
import net.kasax.tamagotchi.registry.ModItems;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.ItemStack;

/** Information pages for recipe viewers (JEI, REI): how to get the things that have no recipe, or need explaining. */
public final class CompatInfo {
    private CompatInfo() {
    }

    public static Map<ItemStack, Component> pages() {
        Map<ItemStack, Component> map = new LinkedHashMap<>();
        map.put(new ItemStack(ModItems.TAMAGOTCHI_HEART), Component.translatable("info.tamagotchi.tamagotchi_heart"));
        map.put(new ItemStack(ModItems.TAMACON), Component.translatable("info.tamagotchi.tamacon"));
        map.put(new ItemStack(ModItems.TAMA_PAGER), Component.translatable("info.tamagotchi.tama_pager"));
        map.put(new ItemStack(ModItems.TAMA_EGG), Component.translatable("info.tamagotchi.tama_egg"));
        for (PetSpecies s : PetSpecies.values()) {
            map.put(new ItemStack(ModItems.SPAWN_EGGS.get(s)), Component.translatable("info.tamagotchi.pet." + s.id()));
        }
        return map;
    }
}
