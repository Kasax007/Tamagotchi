package net.kasax.tamagotchi.client;

import java.util.EnumMap;
import java.util.Map;
import java.util.function.Supplier;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.api.EnvType;
import net.fabricmc.api.Environment;
import net.fabricmc.fabric.api.blockrenderlayer.v1.BlockRenderLayerMap;
import net.fabricmc.fabric.api.client.rendering.v1.BuiltinItemRendererRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.ColorProviderRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.EntityModelLayerRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.EntityRendererRegistry;
import net.kasax.tamagotchi.Tamagotchi;
import net.kasax.tamagotchi.block.Dyeing;
import net.kasax.tamagotchi.client.model.PetModels;
import net.kasax.tamagotchi.client.particle.PetParticles;
import net.kasax.tamagotchi.client.render.HeldItemModels;
import net.kasax.tamagotchi.client.render.IncubatorRenderer;
import net.kasax.tamagotchi.client.render.PetPortraitRenderer;
import net.kasax.tamagotchi.client.render.PetRenderer;
import net.kasax.tamagotchi.client.render.PlushItemRenderer;
import net.kasax.tamagotchi.client.render.PlushRenderer;
import net.kasax.tamagotchi.client.render.PlushTag;
import net.kasax.tamagotchi.client.render.RunningWheelRenderer;
import net.kasax.tamagotchi.client.screen.PetScreen;
import net.kasax.tamagotchi.pet.PetSpecies;
import net.kasax.tamagotchi.registry.ModBlocks;
import net.kasax.tamagotchi.registry.ModEntities;
import net.kasax.tamagotchi.registry.ModMenus;
import net.minecraft.client.gui.screens.MenuScreens;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderers;
import net.minecraft.core.component.DataComponents;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.DyeColor;
import net.minecraft.world.item.component.BlockItemStateProperties;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.EnumProperty;

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
    private static void dyed(EnumProperty<DyeColor> prop, float whiten, Block... blocks) {
        ColorProviderRegistry.BLOCK.register((state, level, pos, tintIndex) ->
                tintIndex == 0 && state.hasProperty(prop) ? Dyeing.tint(state.getValue(prop), whiten) : -1, blocks);
        // the item shows the colour the block had (the loot table copies it into the block_state component)
        ColorProviderRegistry.ITEM.register((stack, tintIndex) -> {
            if (tintIndex != 0 || !(stack.getItem() instanceof BlockItem item)) {
                return -1;
            }
            BlockState state = item.getBlock().defaultBlockState();
            BlockItemStateProperties props = stack.getOrDefault(DataComponents.BLOCK_STATE, BlockItemStateProperties.EMPTY);
            return Dyeing.tint(props.apply(state).getValue(prop), whiten);
        }, blocks);
    }

    @Override
    public void onInitializeClient() {
        for (PetSpecies s : PetSpecies.values()) {
            ModelLayerLocation loc = new ModelLayerLocation(Tamagotchi.id(s.id()), "main");
            LAYERS.put(s, loc);
            Supplier<LayerDefinition> def = layer(s);
            EntityModelLayerRegistry.registerModelLayer(loc, def::get);
            EntityRendererRegistry.register(ModEntities.type(s), ctx -> new PetRenderer(ctx, s, loc));
        }
        EntityModelLayerRegistry.registerModelLayer(RunningWheelRenderer.LAYER, RunningWheelRenderer::createLayer);
        BlockEntityRenderers.register(ModBlocks.RUNNING_WHEEL_BE, RunningWheelRenderer::new);
        EntityModelLayerRegistry.registerModelLayer(IncubatorRenderer.LAYER, IncubatorRenderer::createLayer);
        BlockEntityRenderers.register(ModBlocks.PET_INCUBATOR_BE, IncubatorRenderer::new);
        EntityModelLayerRegistry.registerModelLayer(PlushTag.LAYER, PlushTag::createLayer);
        BlockEntityRenderers.register(ModBlocks.PLUSH_BE, PlushRenderer::new);
        BlockEntityRenderers.register(ModBlocks.PET_PORTRAIT_BE, PetPortraitRenderer::new);
        PlushItemRenderer plushItems = new PlushItemRenderer();
        for (Block plush : ModBlocks.PLUSHES.values()) {
            BuiltinItemRendererRegistry.INSTANCE.register(plush, plushItems);
        }
        dyed(Dyeing.COLOR, Dyeing.FABRIC, ModBlocks.PET_BED, ModBlocks.PET_BASKET);
        dyed(Dyeing.COLOR, Dyeing.LAMP, ModBlocks.EGG_LAMP);
        dyed(Dyeing.BACKDROP, Dyeing.PASTEL, ModBlocks.PET_PORTRAIT);
        // 26.x picks the chunk layer from the textures; 1.21.1 needs it per block
        BlockRenderLayerMap.INSTANCE.putBlocks(RenderType.cutout(), ModBlocks.DRAGON_NEST, ModBlocks.EGG_LAMP, ModBlocks.FOOD_BOWL,
                ModBlocks.PET_INCUBATOR, ModBlocks.TREAT_DISPENSER);
        BlockRenderLayerMap.INSTANCE.putBlock(ModBlocks.PET_BATH, RenderType.translucent());
        HeldItemModels.register();
        PetParticles.register();
        MenuScreens.register(ModMenus.PET_MENU, PetScreen::new);
        net.kasax.tamagotchi.item.TamaconItem.openScreen = () -> net.minecraft.client.Minecraft.getInstance().setScreen(
                new net.kasax.tamagotchi.client.screen.TamaconScreen());
    }
}
