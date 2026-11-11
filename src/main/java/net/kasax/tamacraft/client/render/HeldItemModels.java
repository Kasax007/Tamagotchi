package net.kasax.tamacraft.client.render;

import java.util.Map;
import net.minecraft.client.resources.model.ModelResourceLocation;
import net.neoforged.neoforge.client.event.ModelEvent;
import net.kasax.tamacraft.Tamacraft;
import net.kasax.tamacraft.registry.ModItems;
import net.minecraft.client.Minecraft;
import net.minecraft.client.resources.model.BakedModel;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;

/**
 * The Tama Pager and the Laser Pointer are flat icons in the inventory and little 3D devices in the hand, on the ground
 * and in item frames (26.x: a display_context select in the item model; 1.21.1: an extra model swapped in by
 * {@link net.kasax.tamacraft.mixin.client.ItemRendererMixin}, like vanilla does for the trident and spyglass).
 */
public final class HeldItemModels {
    private static Map<Item, ResourceLocation> models;

    private HeldItemModels() {
    }

    public static void register() {
        models = Map.of(ModItems.TAMA_PAGER, Tamacraft.id("item/tama_pager_3d"), ModItems.LASER_POINTER, Tamacraft.id("item/laser_pointer_3d"));
    }

    /** The 3D models are extra models: NeoForge loads and bakes them next to the item models. */
    public static void registerModels(ModelEvent.RegisterAdditional event) {
        register();
        for (ResourceLocation id : models.values()) {
            event.register(ModelResourceLocation.standalone(id));
        }
    }

    /** The model to draw {@code stack} with in {@code context}: the 3D one everywhere but in the inventory. */
    public static BakedModel swap(ItemStack stack, ItemDisplayContext context, BakedModel model) {
        if (models == null || context == ItemDisplayContext.GUI) {
            return model;
        }
        ResourceLocation id = models.get(stack.getItem());
        return id == null ? model : Minecraft.getInstance().getModelManager().getModel(ModelResourceLocation.standalone(id));
    }
}
