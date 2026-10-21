package net.kasax.tamagotchi.client;

import java.util.EnumMap;
import java.util.Map;
import java.util.function.Supplier;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.api.EnvType;
import net.fabricmc.api.Environment;
import net.fabricmc.fabric.api.client.rendering.v1.BlockEntityRendererRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.EntityRendererRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.ModelLayerRegistry;
import net.kasax.tamagotchi.Tamagotchi;
import net.kasax.tamagotchi.client.model.PetModels;
import net.kasax.tamagotchi.client.particle.PetParticles;
import net.kasax.tamagotchi.client.render.PetRenderer;
import net.kasax.tamagotchi.client.render.RunningWheelRenderer;
import net.kasax.tamagotchi.client.screen.PetScreen;
import net.kasax.tamagotchi.pet.PetSpecies;
import net.kasax.tamagotchi.registry.ModBlocks;
import net.kasax.tamagotchi.registry.ModEntities;
import net.kasax.tamagotchi.registry.ModMenus;
import net.minecraft.client.gui.screens.MenuScreens;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.model.geom.builders.LayerDefinition;

/** Client wiring: model layers, renderers, particles and the pet screen. */
@Environment(EnvType.CLIENT)
public class TamagotchiClient implements ClientModInitializer {
    public static final Map<PetSpecies, ModelLayerLocation> LAYERS = new EnumMap<>(PetSpecies.class);

    private static Supplier<LayerDefinition> layer(PetSpecies s) {
        return switch (s) {
            case DESERT_DRAGON -> PetModels::createDesertDragon;
            case JUNGLE_DRAGON -> PetModels::createJungleDragon;
            case TIDE_DRAGON -> PetModels::createTideDragon;
            case FROST_PENGUIN -> PetModels::createFrostPenguin;
            case EMBER_PUP -> PetModels::createEmberPup;
            case SCULK_WISP -> PetModels::createSculkWisp;
            case VOID_KITTEN -> PetModels::createVoidKitten;
            case PEBBLE_GOLEM -> PetModels::createPebbleGolem;
            case HEX_TOAD -> PetModels::createHexToad;
            case MIMIC -> PetModels::createMimic;
        };
    }

    @Override
    public void onInitializeClient() {
        for (PetSpecies s : PetSpecies.values()) {
            ModelLayerLocation loc = new ModelLayerLocation(Tamagotchi.id(s.id()), "main");
            LAYERS.put(s, loc);
            Supplier<LayerDefinition> def = layer(s);
            ModelLayerRegistry.registerModelLayer(loc, def::get);
            EntityRendererRegistry.register(ModEntities.type(s), ctx -> new PetRenderer(ctx, s, loc));
        }
        ModelLayerRegistry.registerModelLayer(RunningWheelRenderer.LAYER, RunningWheelRenderer::createLayer);
        BlockEntityRendererRegistry.register(ModBlocks.RUNNING_WHEEL_BE, RunningWheelRenderer::new);
        PetParticles.register();
        MenuScreens.register(ModMenus.PET_MENU, PetScreen::new);
        net.kasax.tamagotchi.item.TamaconItem.openScreen = () -> net.minecraft.client.Minecraft.getInstance().gui.setScreen(
                new net.kasax.tamagotchi.client.screen.TamaconScreen());
    }
}
