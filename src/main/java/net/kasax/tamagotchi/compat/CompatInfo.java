package net.kasax.tamagotchi.compat;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import net.kasax.tamagotchi.pet.PetSpecies;
import net.kasax.tamagotchi.registry.ModBlocks;
import net.kasax.tamagotchi.registry.ModItems;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Block;

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
        for (Block b : List.of(ModBlocks.TREAT_DISPENSER, ModBlocks.PET_INCUBATOR, ModBlocks.TOY_BOX, ModBlocks.PET_FLAP,
                ModBlocks.PET_PORTRAIT, ModBlocks.EGG_LAMP, ModBlocks.PET_BED, ModBlocks.PET_BASKET)) {
            map.put(new ItemStack(b), Component.translatable("info.tamagotchi." + BuiltInRegistries.BLOCK.getKey(b).getPath()));
        }
        for (Block b : ModBlocks.PLUSHES.values()) {
            map.put(new ItemStack(b), Component.translatable("info.tamagotchi.plush"));
        }
        return map;
    }
}
