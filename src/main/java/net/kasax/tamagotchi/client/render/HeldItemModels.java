package net.kasax.tamagotchi.client.render;

import java.util.Map;
import net.fabricmc.api.EnvType;
import net.fabricmc.api.Environment;
import net.fabricmc.fabric.api.client.model.loading.v1.ModelLoadingPlugin;
import net.kasax.tamagotchi.Tamagotchi;
import net.kasax.tamagotchi.registry.ModItems;
import net.minecraft.client.Minecraft;
import net.minecraft.client.resources.model.BakedModel;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;

/**
 * The Tama Pager and the Laser Pointer are flat icons in the inventory and little 3D devices in the hand, on the ground
 * and in item frames (26.x: a display_context select in the item model; 1.21.1: an extra model swapped in by
 * {@link net.kasax.tamagotchi.mixin.client.ItemRendererMixin}, like vanilla does for the trident and spyglass).
 */
@Environment(EnvType.CLIENT)
public final class HeldItemModels {
    private static Map<Item, ResourceLocation> models;

    private HeldItemModels() {
    }

    public static void register() {
        models = Map.of(ModItems.TAMA_PAGER, Tamagotchi.id("item/tama_pager_3d"), ModItems.LASER_POINTER, Tamagotchi.id("item/laser_pointer_3d"));
        ModelLoadingPlugin.register(ctx -> ctx.addModels(models.values()));
    }

    /** The model to draw {@code stack} with in {@code context}: the 3D one everywhere but in the inventory. */
    public static BakedModel swap(ItemStack stack, ItemDisplayContext context, BakedModel model) {
        if (models == null || context == ItemDisplayContext.GUI) {
            return model;
        }
        ResourceLocation id = models.get(stack.getItem());
        return id == null ? model : Minecraft.getInstance().getModelManager().getModel(id);
    }
}
