package net.kasax.tamacraft.mixin.client;

import com.mojang.blaze3d.vertex.PoseStack;
import net.kasax.tamacraft.client.render.HeldItemModels;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.entity.ItemRenderer;
import net.minecraft.client.resources.model.BakedModel;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.ModifyVariable;

/** Flat inventory icon, 3D model elsewhere, for the pager and the laser pointer (see {@link HeldItemModels}). */
@Mixin(ItemRenderer.class)
public abstract class ItemRendererMixin {
    @ModifyVariable(method = "render(Lnet/minecraft/world/item/ItemStack;Lnet/minecraft/world/item/ItemDisplayContext;ZLcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/renderer/MultiBufferSource;IILnet/minecraft/client/resources/model/BakedModel;)V",
            at = @At("HEAD"), argsOnly = true)
    private BakedModel tamacraft$heldModel(BakedModel model, ItemStack stack, ItemDisplayContext context, boolean leftHand, PoseStack poseStack,
                                           MultiBufferSource buffers, int light, int overlay) {
        return HeldItemModels.swap(stack, context, model);
    }
}
