package net.kasax.tamacraft.compat;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import net.kasax.tamacraft.pet.PetSpecies;
import net.kasax.tamacraft.registry.ModBlocks;
import net.kasax.tamacraft.registry.ModItems;
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
        map.put(new ItemStack(ModItems.TAMACRAFT_HEART), Component.translatable("info.tamacraft.tamacraft_heart"));
        map.put(new ItemStack(ModItems.TAMACON), Component.translatable("info.tamacraft.tamacon"));
        map.put(new ItemStack(ModItems.TAMA_PAGER), Component.translatable("info.tamacraft.tama_pager"));
        map.put(new ItemStack(ModItems.TAMA_EGG), Component.translatable("info.tamacraft.tama_egg"));
        for (PetSpecies s : PetSpecies.values()) {
            map.put(new ItemStack(ModItems.SPAWN_EGGS.get(s)), Component.translatable("info.tamacraft.pet." + s.id()));
        }
        for (Block b : List.of(ModBlocks.TREAT_DISPENSER, ModBlocks.PET_INCUBATOR, ModBlocks.TOY_BOX, ModBlocks.PET_FLAP,
                ModBlocks.PET_PORTRAIT, ModBlocks.EGG_LAMP, ModBlocks.PET_BED, ModBlocks.PET_BASKET)) {
            map.put(new ItemStack(b), Component.translatable("info.tamacraft." + BuiltInRegistries.BLOCK.getKey(b).getPath()));
        }
        for (Block b : ModBlocks.PLUSHES.values()) {
            map.put(new ItemStack(b), Component.translatable("info.tamacraft.plush"));
        }
        return map;
    }
}
