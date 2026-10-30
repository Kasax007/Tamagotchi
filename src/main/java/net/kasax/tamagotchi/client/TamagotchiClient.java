package net.kasax.tamagotchi.client;

import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.Supplier;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.api.EnvType;
import net.fabricmc.api.Environment;
import net.fabricmc.fabric.api.client.rendering.v1.BlockColorRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.BlockEntityRendererRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.EntityRendererRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.ModelLayerRegistry;
import net.kasax.tamagotchi.Tamagotchi;
import net.kasax.tamagotchi.block.Dyeing;
import net.kasax.tamagotchi.client.model.PetModels;
import net.kasax.tamagotchi.client.particle.PetParticles;
import net.kasax.tamagotchi.client.render.IncubatorRenderer;
import net.kasax.tamagotchi.client.render.PetPortraitRenderer;
import net.kasax.tamagotchi.client.render.PetRenderer;
import net.kasax.tamagotchi.client.render.PlushRenderer;
import net.kasax.tamagotchi.client.render.PlushSpecialRenderer;
import net.kasax.tamagotchi.client.render.PlushTag;
import net.kasax.tamagotchi.client.render.RunningWheelRenderer;
import net.kasax.tamagotchi.client.screen.PetScreen;
import net.kasax.tamagotchi.pet.PetSpecies;
import net.kasax.tamagotchi.registry.ModBlocks;
import net.kasax.tamagotchi.registry.ModEntities;
import net.kasax.tamagotchi.registry.ModMenus;
import net.minecraft.client.color.block.BlockTintSource;
import net.minecraft.client.gui.screens.MenuScreens;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.renderer.special.SpecialModelRenderers;
import net.minecraft.world.item.DyeColor;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.EnumProperty;
import net.minecraft.world.level.block.state.properties.Property;

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

    /** Tint index 0 of a dyeable block: the colour in its {@code prop}. */
    private static BlockTintSource dyed(EnumProperty<DyeColor> prop, float whiten) {
        return new BlockTintSource() {
            @Override
            public int color(BlockState state) {
                return Dyeing.tint(state.getValue(prop), whiten);
            }

            @Override
            public Set<Property<?>> relevantProperties() {
                return Set.of(prop);
            }
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
        ModelLayerRegistry.registerModelLayer(IncubatorRenderer.LAYER, IncubatorRenderer::createLayer);
        BlockEntityRendererRegistry.register(ModBlocks.PET_INCUBATOR_BE, IncubatorRenderer::new);
        ModelLayerRegistry.registerModelLayer(PlushTag.LAYER, PlushTag::createLayer);
        BlockEntityRendererRegistry.register(ModBlocks.PLUSH_BE, PlushRenderer::new);
        BlockEntityRendererRegistry.register(ModBlocks.PET_PORTRAIT_BE, PetPortraitRenderer::new);
        SpecialModelRenderers.ID_MAPPER.put(Tamagotchi.id("plush"), PlushSpecialRenderer.Unbaked.MAP_CODEC);
        BlockColorRegistry.register(List.of(dyed(Dyeing.COLOR, Dyeing.FABRIC)), ModBlocks.PET_BED, ModBlocks.PET_BASKET);
        BlockColorRegistry.register(List.of(dyed(Dyeing.COLOR, Dyeing.LAMP)), ModBlocks.EGG_LAMP);
        BlockColorRegistry.register(List.of(dyed(Dyeing.BACKDROP, Dyeing.PASTEL)), ModBlocks.PET_PORTRAIT);
        PetParticles.register();
        MenuScreens.register(ModMenus.PET_MENU, PetScreen::new);
        net.kasax.tamagotchi.item.TamaconItem.openScreen = () -> net.minecraft.client.Minecraft.getInstance().gui.setScreen(
                new net.kasax.tamagotchi.client.screen.TamaconScreen());
    }
}
