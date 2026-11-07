package net.kasax.tamacraft.registry;

import net.fabricmc.fabric.api.itemgroup.v1.FabricItemGroup;
import net.kasax.tamacraft.Tamacraft;
import net.kasax.tamacraft.pet.PetSpecies;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

/** The mod's own creative tab: tools, toys, food, furniture and all spawn eggs. */
public final class ModTab {
    public static final ResourceKey<CreativeModeTab> KEY = ResourceKey.create(Registries.CREATIVE_MODE_TAB, Tamacraft.id("tamacraft"));

    private ModTab() {
    }

    public static void initialize() {
        Registry.register(BuiltInRegistries.CREATIVE_MODE_TAB, KEY, FabricItemGroup.builder()
                .title(Component.translatable("itemGroup.tamacraft"))
                .icon(() -> new ItemStack(ModItems.TAMACRAFT_HEART))
                .displayItems((params, output) -> {
                    for (Item item : ModItems.TAB_ORDER) {
                        output.accept(item);
                    }
                    for (Item item : ModBlocks.BLOCK_ITEMS) {
                        output.accept(item);
                    }
                    for (PetSpecies s : PetSpecies.values()) {
                        output.accept(ModItems.SPAWN_EGGS.get(s));
                    }
                })
                .build());
    }
}
