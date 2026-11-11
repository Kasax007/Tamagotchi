package net.kasax.tamacraft.client;

import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.function.Supplier;
import net.kasax.tamacraft.Tamacraft;
import net.kasax.tamacraft.block.Dyeing;
import net.kasax.tamacraft.client.model.PetModels;
import net.kasax.tamacraft.client.particle.PetParticles;
import net.kasax.tamacraft.client.render.HeldItemModels;
import net.kasax.tamacraft.client.render.IncubatorRenderer;
import net.kasax.tamacraft.client.render.PetPortraitRenderer;
import net.kasax.tamacraft.client.render.PetRenderer;
import net.kasax.tamacraft.client.render.PlushItemRenderer;
import net.kasax.tamacraft.client.render.PlushRenderer;
import net.kasax.tamacraft.client.render.PlushTag;
import net.kasax.tamacraft.client.render.RunningWheelRenderer;
import net.kasax.tamacraft.client.screen.PetScreen;
import net.kasax.tamacraft.pet.PetSpecies;
import net.kasax.tamacraft.registry.ModBlocks;
import net.kasax.tamacraft.registry.ModEntities;
import net.kasax.tamacraft.registry.ModMenus;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.renderer.BlockEntityWithoutLevelRenderer;
import net.minecraft.client.renderer.ItemBlockRenderTypes;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.core.component.DataComponents;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.DyeColor;
import net.minecraft.world.item.component.BlockItemStateProperties;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.EnumProperty;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.common.Mod;
import net.neoforged.fml.event.lifecycle.FMLClientSetupEvent;
import net.neoforged.neoforge.client.event.EntityRenderersEvent;
import net.neoforged.neoforge.client.event.RegisterColorHandlersEvent;
import net.neoforged.neoforge.client.event.RegisterMenuScreensEvent;
import net.neoforged.neoforge.client.extensions.common.IClientItemExtensions;
import net.neoforged.neoforge.client.extensions.common.RegisterClientExtensionsEvent;

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

    /** A dyeable block: tint index 0 is the colour in its {@code prop}. */
    private record Dyed(EnumProperty<DyeColor> prop, float whiten, List<Block> blocks) {
    }

    private static List<Dyed> dyed() {
        return List.of(new Dyed(Dyeing.COLOR, Dyeing.FABRIC, List.of(ModBlocks.PET_BED, ModBlocks.PET_BASKET)),
                new Dyed(Dyeing.COLOR, Dyeing.LAMP, List.of(ModBlocks.EGG_LAMP)),
                new Dyed(Dyeing.BACKDROP, Dyeing.PASTEL, List.of(ModBlocks.PET_PORTRAIT)));
    }

    public TamacraftClient(IEventBus modBus) {
        modBus.addListener(TamacraftClient::layers);
        modBus.addListener(TamacraftClient::renderers);
        modBus.addListener(TamacraftClient::blockColors);
        modBus.addListener(TamacraftClient::itemColors);
        modBus.addListener(TamacraftClient::itemExtensions);
        modBus.addListener(HeldItemModels::registerModels);
        modBus.addListener(PetParticles::register);
        modBus.addListener(TamacraftClient::screens);
        modBus.addListener(TamacraftClient::setup);
        net.kasax.tamacraft.item.TamaconItem.openScreen = () -> Minecraft.getInstance().setScreen(
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

    private static void blockColors(RegisterColorHandlersEvent.Block event) {
        for (Dyed d : dyed()) {
            event.register((state, level, pos, tintIndex) ->
                    tintIndex == 0 && state.hasProperty(d.prop()) ? Dyeing.tint(state.getValue(d.prop()), d.whiten()) : -1,
                    d.blocks().toArray(Block[]::new));
        }
    }

    private static void itemColors(RegisterColorHandlersEvent.Item event) {
        for (Dyed d : dyed()) {
            // the item shows the colour the block had (the loot table copies it into the block_state component)
            event.register((stack, tintIndex) -> {
                if (tintIndex != 0 || !(stack.getItem() instanceof BlockItem item)) {
                    return -1;
                }
                BlockState state = item.getBlock().defaultBlockState();
                BlockItemStateProperties props = stack.getOrDefault(DataComponents.BLOCK_STATE, BlockItemStateProperties.EMPTY);
                return Dyeing.tint(props.apply(state).getValue(d.prop()), d.whiten());
            }, d.blocks().toArray(Block[]::new));
        }
    }

    /** The plush items draw the little pet like the placed plush (item model parent builtin/entity). */
    private static void itemExtensions(RegisterClientExtensionsEvent event) {
        IClientItemExtensions plush = new IClientItemExtensions() {
            private PlushItemRenderer renderer;

            @Override
            public BlockEntityWithoutLevelRenderer getCustomRenderer() {
                if (this.renderer == null) {
                    this.renderer = new PlushItemRenderer();
                }
                return this.renderer;
            }
        };
        event.registerItem(plush, ModBlocks.PLUSHES.values().stream().map(Block::asItem).toArray(net.minecraft.world.item.Item[]::new));
    }

    private static void screens(RegisterMenuScreensEvent event) {
        event.register(ModMenus.PET_MENU, PetScreen::new);
    }

    @SuppressWarnings("deprecation")
    private static void setup(FMLClientSetupEvent event) {
        // 26.x picks the chunk layer from the textures; 1.21.1 needs it per block
        event.enqueueWork(() -> {
            for (Block b : new Block[]{ModBlocks.DRAGON_NEST, ModBlocks.EGG_LAMP, ModBlocks.FOOD_BOWL, ModBlocks.PET_INCUBATOR,
                    ModBlocks.TREAT_DISPENSER}) {
                ItemBlockRenderTypes.setRenderLayer(b, RenderType.cutout());
            }
            ItemBlockRenderTypes.setRenderLayer(ModBlocks.PET_BATH, RenderType.translucent());
        });
    }
}
