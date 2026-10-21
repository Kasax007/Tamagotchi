package net.kasax.tamagotchi;

import net.fabricmc.api.ModInitializer;
import net.kasax.tamagotchi.registry.ModBlocks;
import net.kasax.tamagotchi.registry.ModEntities;
import net.kasax.tamagotchi.registry.ModItems;
import net.kasax.tamagotchi.registry.ModMenus;
import net.kasax.tamagotchi.registry.ModParticles;
import net.kasax.tamagotchi.registry.ModSounds;
import net.kasax.tamagotchi.registry.ModTab;
import net.minecraft.resources.Identifier;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/** Ten collectible pets to find, tame and look after. */
public class Tamagotchi implements ModInitializer {
    public static final String MOD_ID = "tamagotchi";
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
        LOGGER.info("Tamagotchi ready: {} pets", net.kasax.tamagotchi.pet.PetSpecies.values().length);
    }
}
