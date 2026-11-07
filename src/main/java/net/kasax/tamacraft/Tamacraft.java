package net.kasax.tamacraft;

import net.fabricmc.api.ModInitializer;
import net.kasax.tamacraft.registry.ModBlocks;
import net.kasax.tamacraft.registry.ModEntities;
import net.kasax.tamacraft.registry.ModItems;
import net.kasax.tamacraft.registry.ModMenus;
import net.kasax.tamacraft.registry.ModParticles;
import net.kasax.tamacraft.registry.ModSounds;
import net.kasax.tamacraft.registry.ModTab;
import net.minecraft.resources.Identifier;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/** Ten collectible pets to find, tame and look after. */
public class Tamacraft implements ModInitializer {
    public static final String MOD_ID = "tamacraft";
    public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

    public static Identifier id(String path) {
        return Identifier.fromNamespaceAndPath(MOD_ID, path);
    }

    @Override
    public void onInitialize() {
        ModSounds.initialize();
        ModParticles.initialize();
        ModEntities.initialize();
        ModBlocks.initialize();
        ModItems.initialize();
        ModMenus.initialize();
        ModTab.initialize();
        net.kasax.tamacraft.world.OreMarkers.initialize();
        LOGGER.info("Tamacraft ready: {} pets", net.kasax.tamacraft.pet.PetSpecies.values().length);
    }
}
