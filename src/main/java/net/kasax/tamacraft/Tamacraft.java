package net.kasax.tamacraft;

import net.kasax.tamacraft.registry.ModBlocks;
import net.kasax.tamacraft.registry.ModEntities;
import net.kasax.tamacraft.registry.ModItems;
import net.kasax.tamacraft.registry.ModMenus;
import net.kasax.tamacraft.registry.ModParticles;
import net.kasax.tamacraft.registry.ModSounds;
import net.kasax.tamacraft.registry.ModTab;
import net.minecraft.resources.ResourceLocation;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.registries.RegisterEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/** Ten collectible pets to find, tame and look after. */
@Mod(Tamacraft.MOD_ID)
public class Tamacraft {
    public static final String MOD_ID = "tamacraft";
    public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);
    private static boolean registered;

    public static ResourceLocation id(String path) {
        return ResourceLocation.fromNamespaceAndPath(MOD_ID, path);
    }

    public Tamacraft(IEventBus modBus) {
        // NeoForge opens every registry for the whole registration phase: the first RegisterEvent fills them all, in the
        // same order as the Fabric build (the registry classes register their entries themselves)
        modBus.addListener(RegisterEvent.class, event -> {
            if (!registered) {
                registered = true;
                onInitialize();
            }
        });
        modBus.addListener(ModEntities::registerAttributes);
    }

    private static void onInitialize() {
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
