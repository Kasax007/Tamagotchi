package net.kasax.tamacraft.client;

import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.Supplier;
import net.kasax.tamacraft.Tamacraft;
import net.kasax.tamacraft.block.Dyeing;
import net.kasax.tamacraft.client.model.PetModels;
import net.kasax.tamacraft.client.particle.PetParticles;
import net.kasax.tamacraft.client.render.IncubatorRenderer;
import net.kasax.tamacraft.client.render.PetPortraitRenderer;
import net.kasax.tamacraft.client.render.PetRenderer;
import net.kasax.tamacraft.client.render.PlushRenderer;
import net.kasax.tamacraft.client.render.PlushSpecialRenderer;
import net.kasax.tamacraft.client.render.PlushTag;
import net.kasax.tamacraft.client.render.RunningWheelRenderer;
import net.kasax.tamacraft.client.screen.PetScreen;
import net.kasax.tamacraft.pet.PetSpecies;
import net.kasax.tamacraft.registry.ModBlocks;
import net.kasax.tamacraft.registry.ModEntities;
import net.kasax.tamacraft.registry.ModMenus;
import net.minecraft.client.Minecraft;
import net.minecraft.client.color.block.BlockTintSource;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.world.item.DyeColor;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.EnumProperty;
import net.minecraft.world.level.block.state.properties.Property;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.client.event.EntityRenderersEvent;
import net.neoforged.neoforge.client.event.RegisterColorHandlersEvent;
import net.neoforged.neoforge.client.event.RegisterMenuScreensEvent;
import net.neoforged.neoforge.client.event.RegisterSpecialModelRendererEvent;

/** Client wiring: model layers, renderers, particles and the pet screen. */
@Mod(value = Tamacraft.MOD_ID, dist = Dist.CLIENT)
public class TamacraftClient {
    public static final Map<PetSpecies, ModelLayerLocation> LAYERS = new EnumMap<>(PetSpecies.class);

    static {
        for (PetSpecies s : PetSpecies.values()) {
            LAYERS.put(s, new ModelLayerLocation(Tamacraft.id(s.id()), "main"));
        }
    }

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

    public TamacraftClient(IEventBus modBus) {
        modBus.addListener(TamacraftClient::layers);
        modBus.addListener(TamacraftClient::renderers);
        modBus.addListener(TamacraftClient::specialModels);
        modBus.addListener(TamacraftClient::blockTints);
        modBus.addListener(PetParticles::register);
        modBus.addListener(TamacraftClient::screens);
        net.kasax.tamacraft.item.TamaconItem.openScreen = () -> Minecraft.getInstance().gui.setScreen(
                new net.kasax.tamacraft.client.screen.TamaconScreen());
    }

    private static void layers(EntityRenderersEvent.RegisterLayerDefinitions event) {
        for (PetSpecies s : PetSpecies.values()) {
            event.registerLayerDefinition(LAYERS.get(s), layer(s));
        }
        event.registerLayerDefinition(RunningWheelRenderer.LAYER, RunningWheelRenderer::createLayer);
        event.registerLayerDefinition(IncubatorRenderer.LAYER, IncubatorRenderer::createLayer);
        event.registerLayerDefinition(PlushTag.LAYER, PlushTag::createLayer);
    }

    private static void renderers(EntityRenderersEvent.RegisterRenderers event) {
        for (PetSpecies s : PetSpecies.values()) {
            ModelLayerLocation loc = LAYERS.get(s);
            event.registerEntityRenderer(ModEntities.type(s), ctx -> new PetRenderer(ctx, s, loc));
        }
        event.registerBlockEntityRenderer(ModBlocks.RUNNING_WHEEL_BE, RunningWheelRenderer::new);
        event.registerBlockEntityRenderer(ModBlocks.PET_INCUBATOR_BE, IncubatorRenderer::new);
        event.registerBlockEntityRenderer(ModBlocks.PLUSH_BE, PlushRenderer::new);
        event.registerBlockEntityRenderer(ModBlocks.PET_PORTRAIT_BE, PetPortraitRenderer::new);
    }

    /** The plush items: a special model renderer (item model type tamacraft:plush). */
    private static void specialModels(RegisterSpecialModelRendererEvent event) {
        event.register(Tamacraft.id("plush"), PlushSpecialRenderer.Unbaked.MAP_CODEC);
    }

    private static void blockTints(RegisterColorHandlersEvent.BlockTintSources event) {
        event.register(List.of(dyed(Dyeing.COLOR, Dyeing.FABRIC)), ModBlocks.PET_BED, ModBlocks.PET_BASKET);
        event.register(List.of(dyed(Dyeing.COLOR, Dyeing.LAMP)), ModBlocks.EGG_LAMP);
        event.register(List.of(dyed(Dyeing.BACKDROP, Dyeing.PASTEL)), ModBlocks.PET_PORTRAIT);
    }

    private static void screens(RegisterMenuScreensEvent event) {
        event.register(ModMenus.PET_MENU, PetScreen::new);
    }
}
